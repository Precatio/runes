"""Statistik i R: export av korpusen, körning av R-skripten i r/ och cachning av resultaten.

Korpusanalyserna (geografi, klustring, textanalys och attribueringsmodell) körs en gång per version av
Rundata och R-skripten och sparas i data/cache/r/<fingeravtryck>/. Analysen av en enskild sten läser
de sparade resultaten och körs på några sekunder.

R anropas med `Rscript --vanilla r/<modul>.R <indata> <utmapp>`. Varje modul skriver result.json och
figurer (PNG) i utmappen. Samma skript och samma CSV ingår i reproducerbarhetspaketet, så att en forskare
kan köra om allt i R utan appen.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys
import threading
import time
import zipfile
from datetime import datetime, timezone

from src import research_gaps as gaps
from src import spawn
from src.inscription_types import CATEGORIES, categories
from src.language_profile import TRAITS, ai_counts, dotted_counts, o_counts, och_counts, prayer_form, r_counts, traits
from src.orthography import features
from src.pattern_map import PATTERNS as MAP_PATTERNS, pagan, stone_patterns
from src.styles import BY_CODE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R_DIR = os.path.join(ROOT, "r")
CACHE_DIR = os.environ.get("R_CACHE_DIR", os.path.join(ROOT, "data", "cache", "r"))
MODULES = ("geography", "clusters", "text", "attribution", "anonymous", "chronology", "dialect", "network", "change",
           "remains", "hotspots", "words", "messages")
STONE_MODULES = ("stone", "landscape")
MODULE_LABELS = {"geography": "Geografi", "clusters": "Klustring och MCA", "text": "Text och formler",
                 "attribution": "Attribueringsmodell", "anonymous": "Okända ristare",
                 "chronology": "Seriation och datering",
                 "dialect": "Stavning och dialekter", "network": "Formelnätverk", "change": "Förändring i tid och rum",
                 "remains": "Lämningar runt stenarna", "hotspots": "Hot spots och kluster", "words": "Ordförrådet",
                 "messages": "Budskapen"}
REQUIRED_PACKAGES = ("jsonlite", "dplyr", "tidyr", "stringr", "ggplot2", "sf", "leaflet", "htmlwidgets",
                     "tidytext", "cluster", "FactoMineR", "factoextra", "tidymodels", "ranger", "ragg",
                     "ca", "stringdist", "igraph", "tidygraph", "ggraph", "terra", "gdistance", "raster", "png", "mgcv",
                     # textanalysens specialister (2026-10-19, för Edda-/stilometrispåret; topicmodels kräver GSL)
                     "stylo", "quanteda", "topicmodels")

# Natural Earth 1:10 milj. (public domain): kustlinje, sjöar och vattendrag, med de europeiska tilläggen
WATER_LAYERS = {
    "coastline": "https://naciscdn.org/naturalearth/10m/physical/ne_10m_coastline.zip",
    "lakes": "https://naciscdn.org/naturalearth/10m/physical/ne_10m_lakes.zip",
    "lakes_europe": "https://naciscdn.org/naturalearth/10m/physical/ne_10m_lakes_europe.zip",
    "rivers": "https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.zip",
    "rivers_europe": "https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_europe.zip",
    "land": "https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip",
}

CSV_COLUMNS = (["signum", "province", "district", "place", "parish", "lat", "lon", "carver", "has_carver", "carvers_uncertain",
                "style", "material", "cross", "short_twig", "lost", "moved", "pagan", "n_words", "n_words_core", "carvers_all",
                "style_from", "style_to"]
               + [f"cat_{k}" for k in CATEGORIES] + [f"trait_{k}" for k in TRAITS]
               + [f"pm_{k}" for k, *_ in MAP_PATTERNS]
               + ["words", "pairs", "normalization", "signed", "ai_n", "ai_mono", "ai_sten_n", "ai_sten_mono",
                  "dot_n", "dot_cand", "dot_y_exp", "dot_y_obs", "dot_e_exp", "dot_e_obs", "dot_g_exp", "dot_g_obs",
                  "dot_d_exp", "dot_d_obs", "dot_y_u", "dot_y_i", "end_intact", "prayer_and", "prayer_sal",
                  "prayer_gudsmodir", "R_n", "R_r", "R_eftir_n", "R_eftir_r", "r_n", "r_R", "ai_mono_e", "ai_mono_i",
                  "o_n", "o_o", "aa_n", "aa_o", "dot_e_eftir_exp", "dot_e_eftir_obs", "och_n", "och_auk", "och_uk",
                  "och_ok", "och_ak"])


# ---- R installation ------------------------------------------------------------------------

def rscript() -> str | None:
    """Rscript att köra: RSCRIPT om den är satt (RSCRIPT='' betyder uttryckligen att R saknas, så att en körning
    utan R kan provas på en maskin som har R), annars Rscript i PATH eller en av de vanliga platserna."""
    env = os.environ.get("RSCRIPT")
    if env is not None:
        return env or None
    path = shutil.which("Rscript")
    if path:
        return path
    for p in ("/opt/homebrew/bin/Rscript", "/usr/local/bin/Rscript", "/usr/bin/Rscript"):
        if os.path.exists(p):
            return p
    return None


def enabled() -> bool:
    return os.environ.get("R_DISABLED", "") not in ("1", "true") and rscript() is not None


_status_cache: dict = {}


def _status_key(libpaths: list[str]) -> list:
    """Vad R-kontrollen beror på: Rscript och paketbiblioteken (ändras när paket installeras eller tas bort)."""
    paths = [rscript()] + list(libpaths)
    return [[p, os.path.getmtime(p) if p and os.path.exists(p) else None] for p in paths]


def status() -> dict:
    """Om R finns, vilken version och vilka paket som saknas.

    Kontrollen startar R och laddar alla paket (flera sekunder), så svaret sparas på disk och används så länge
    Rscript och paketbiblioteken är oförändrade (högst en vecka)."""
    if not enabled():
        return {"available": False, "version": None, "missing": list(REQUIRED_PACKAGES),
                "note": "R är inte installerat på servern (Rscript saknas)." if os.environ.get("R_DISABLED") is None
                else "R är avstängt på servern."}
    if _status_cache.get("t", 0) > time.time() - 3600:
        return _status_cache["v"]
    path = os.path.join(CACHE_DIR, "status.json")
    try:
        saved = json.load(open(path, encoding="utf-8"))
        if saved["t"] > time.time() - 7 * 86400 and saved["key"] == json.loads(json.dumps(_status_key(saved["libpaths"]))):
            _status_cache.update(t=time.time(), v=saved["v"])
            return saved["v"]
    except (OSError, ValueError, KeyError):
        pass
    code = ("pk <- c(%s); miss <- pk[!vapply(pk, requireNamespace, logical(1), quietly = TRUE)];"
            "cat(jsonlite::toJSON(list(version = R.version.string, missing = miss, libpaths = .libPaths()), auto_unbox = TRUE))"
            % ", ".join(f'"{p}"' for p in REQUIRED_PACKAGES))
    libpaths: list[str] = []
    try:
        out = spawn.run([rscript(), "--vanilla", "-e", code], capture_output=True, text=True, timeout=120)
        info = json.loads(out.stdout.strip().splitlines()[-1])
        missing = info["missing"] if isinstance(info["missing"], list) else [info["missing"]]
        libpaths = info["libpaths"] if isinstance(info.get("libpaths"), list) else [info.get("libpaths")]
        v = {"available": not missing, "version": info["version"], "missing": missing,
             "note": None if not missing else "Paket saknas i R. Kör: Rscript r/install.R"}
    except Exception as e:  # jsonlite missing or R broken
        v = {"available": False, "version": None, "missing": list(REQUIRED_PACKAGES),
             "note": f"R kunde inte startas eller saknar jsonlite: {str(e)[:200]}. Kör: Rscript r/install.R"}
    _status_cache.update(t=time.time(), v=v)
    if v["available"]:
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            json.dump({"t": time.time(), "libpaths": libpaths, "key": _status_key(libpaths), "v": v},
                      open(path, "w", encoding="utf-8"))
        except OSError:
            pass
    return v


# ---- corpus export -------------------------------------------------------------------------

def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _style_dates(r: dict) -> dict:
    """Gräslunds datering för stilgruppen (för kombinationer som "Pr3 - Pr4" hela spannet)."""
    if not gaps.has_style(r):
        return {"style_from": None, "style_to": None}
    groups = [BY_CODE[c] for c in re.findall(r"RAK|Fp|KB|Pr\d", r["style"]) if c in BY_CODE and BY_CODE[c]["from"]]
    if not groups:
        return {"style_from": None, "style_to": None}
    return {"style_from": min(g["from"] for g in groups), "style_to": max(g["to"] for g in groups)}


# Words of the bridge and prayer phrases ("gærði bro þessa fyrir and hans", "Guð hialpi and hans"): a bridge phrase makes
# a text longer by itself, so the length held constant when bridge stones are compared with others leaves them out
_PHRASE_WORDS = {w.lower() for w in {"bro", "bru", "brú", "brúar", "bryggju", "bryggja", "brygg", "bryggiu", "broð", "væg", "vægh", "veg",
                 "vegR", "vægR", "gærði", "gerði", "gærðu", "gerðu", "gera", "gæra", "gørva", "gærva", "fyrir", "and",
                 "ônd", "sál", "salu", "sálu", "sialu", "guð", "guðs", "hialpi", "hjalpi", "hiælpi", "hialpin", "hialp", "kristr", "krist",
                 "moðir", "móðir", "hans", "hennar", "þæira", "þeira"}}


# Rundata's placement of a stone that is no longer where it was raised: at or in a church, in a wall, a museum or a
# collection ("I vapenhuset.", "Inmurad i södra väggen.", "Sigtuna museum", "Nu vid Åkerby."). Used where the stone's
# surroundings matter (remains.R, hotspots.R, the pattern map), with the place (MOVED_PLACE, is_moved)
MOVED = re.compile(r"kyrk|vapenhus|torn|museum|museet|samling|hembygds|parken|\bpark\b|SHM|magasin|förråd|slott|"
                   r"Dagsnäs|skola|bibliotek|universitet|lapidarium|inmurad|vägg|gavel|koret|sakristi|stiglucka|bogård|"
                   r"kloster|prästgård|Skansen|Runverket|lasarett|bruk\b|privatperson|gravkor|porten|golvet|^Nu vid|"
                   r"Förvara|Befann sig", re.I)
# Rundata's place, when it names a church, a vicarage, a monastery, a castle, a school or a museum ("Frustuna kyrka",
# "Veta kyrkogård"): the placement is often empty for these stones, and they can not be told from stones raised there,
# so they are counted as moved too. A village named after the church (Kyrkby) is not.
MOVED_PLACE = re.compile(r"kyrka\b|kyrkan\b|kyrkogård|kyrkoruin|ödekyrk|kyrkohärbärge|kyrkhärbre|prästgård|\bkloster\b|"
                         r"klosterruin|\bslott\b|skolan\b|museum|museet|samling|lapidarium", re.I)


def is_moved(r: dict) -> bool:
    """Om stenen inte står där den restes, enligt Rundatas placering eller plats (MOVED, MOVED_PLACE), eller för att
    placeringstexten säger att den flyttats eller nämner en annan plats än fyndplatsen (src/placement.py, 2026-10-27)."""
    if MOVED.search(r.get("placement") or "") or MOVED_PLACE.search(r.get("place") or ""):
        return True
    from src.placement import placement_elsewhere
    return placement_elsewhere(r)


def core_words(normalization: str) -> int:
    """Antal ord i normaliseringen utan bro- och bönefrasernas ord (se _PHRASE_WORDS)."""
    words = [w.strip(".,:;!?\"'()[]").lower() for w in normalization.split()]
    return sum(1 for w in words if w and w not in _PHRASE_WORDS)


def corpus_rows(inscriptions: list[dict], names=frozenset()) -> list[dict]:
    """En rad per svensk vikingatida runsten: plats, ristare, stil, kategorier, språkdrag och ordformer."""
    rows = []
    for r in inscriptions:
        if not gaps.is_runestone(r):
            continue
        carvers = gaps.certain_carvers(r)
        f = features(r, names)
        words = f["words"]
        pairs = "|".join(f"{n}={w}" for n, w in f["variants"].items() if "=" not in n and "|" not in n)
        t = traits(r, names)
        cats = set(categories(r))
        rt = (r.get("rune_types") or "").lower()
        row = {
            "signum": r["signum"], "province": gaps.province(r), "place": r.get("place") or "",
            "district": r.get("district") or "", "parish": r.get("parish") or "", "lat": r.get("lat"), "lon": r.get("lon"),
            "carver": carvers[0] if len(carvers) == 1 else "",
            "has_carver": int(gaps.has_carver(r)),
            "carvers_uncertain": int(gaps.has_carver(r) and len(carvers) != 1),
            "style": r["style"] if gaps.has_style(r) else "",
            "material": r.get("material") or "",
            "cross": int(bool((r.get("cross_form") or "").strip())),
            "short_twig": int("kortkvist" in rt),
            "lost": int(r["flags"]["lost"]),
            "moved": int(is_moved(r)),
            "pagan": int(pagan(r)),
            "n_words": f["n_words"],
            "n_words_core": core_words(r.get("normalization") or ""),
            **_style_dates(r),
            "carvers_all": ";".join(c["name"] for c in r["carvers"] if c["kind"] in ("S", "A")),
            **{f"cat_{k}": int(k in cats) for k in CATEGORIES},
            **{f"trait_{k}": t.get(k, "") for k in TRAITS},
            # The pattern map's patterns (src/pattern_map.py: 1, 0 or empty), so that R scans the same patterns as the map
            **{f"pm_{k}": "" if v is None else v for k, v in stone_patterns(r, names).items()},
            "words": " ".join(words),
            "pairs": pairs,
            "normalization": _clean_text(r.get("normalization")),
            # A certain carver who signed the stone (the strongest kind of attribution)
            "signed": int(any(c["kind"] == "S" and not c["uncertain"] for c in r["carvers"])),
            **ai_counts(r),
            **dotted_counts(r),
            **prayer_form(r),
            **r_counts(r),
            **o_counts(r),
            **och_counts(r),
        }
        rows.append(row)
    return rows


def write_csv(rows: list[dict], path: str):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for row in rows:
            w.writerow({k: ("" if row.get(k) is None else row[k]) for k in CSV_COLUMNS})


def csv_bytes(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    w.writeheader()
    for row in rows:
        w.writerow({k: ("" if row.get(k) is None else row[k]) for k in CSV_COLUMNS})
    return buf.getvalue().encode("utf-8")


def _scripts_hash(names: list[str]) -> str:
    h = hashlib.sha256()
    for name in sorted(names):
        path = os.path.join(R_DIR, name)
        h.update(name.encode())
        if os.path.exists(path):
            with open(path, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


# Modules that read other modules' results (in corpus_dir)
DEPENDS = {"attribution": ("geography", "text"), "anonymous": ("geography", "text", "attribution"),
           "chronology": ("text",)}
# The files each module writes, so that an unchanged module's results can be reused from an earlier run
MODULE_FILES = {"geography": ("geography*", "geografi_*", "ristare_karta*"), "clusters": ("clusters*", "kluster_*"),
                "text": ("text*",), "attribution": ("attribution*", "modell_*"), "anonymous": ("anonymous*", "okanda_*"),
                "chronology": ("chronology*", "seriation_*"), "dialect": ("dialect*", "dialekt_*"),
                "network": ("network*", "natverk_*"), "change": ("change*", "forandring_*"),
                "remains": ("remains*", "lamningar_*", "landskap_genomsokning*"), "hotspots": ("hotspots*", "hotspot_*"),
                "messages": ("messages*", "budskap_*")}

# Kulturmiljöregistret's remains (scripts/fetch_raa_remains.py) and the place names and medieval churches
# (scripts/fetch_place_names.py), read by remains.R; not part of the repository
REMAINS = os.path.join(ROOT, "data", "raa", "lamningar.csv")
CULT_NAMES = os.path.join(ROOT, "data", "ortnamn", "kultnamn.csv")
PLACES = os.path.join(ROOT, "data", "ortnamn", "platser.csv")
CHURCHES = os.path.join(ROOT, "data", "ortnamn", "kyrkor.csv")


def _remains_hash() -> str:
    h = hashlib.sha256()
    for path in (REMAINS, CULT_NAMES, PLACES, CHURCHES):
        if os.path.exists(path):
            with open(path, "rb") as fh:
                h.update(fh.read())
        else:
            h.update(b"none")
    return h.hexdigest()[:16]


def _messages_hash() -> str:
    """The message rules (src/messages.py) and their hand-coded check (data/messages_check.json, which messages.R reads):
    the messages module is recomputed when either changes."""
    h = hashlib.sha256()
    for path in (os.path.join(ROOT, "src", "messages.py"), os.path.join(ROOT, "data", "messages_check.json")):
        if os.path.exists(path):
            with open(path, "rb") as fh:
                h.update(fh.read())
        else:
            h.update(b"none")
    return h.hexdigest()[:16]


def write_messages(path: str):
    """The messages of each runestone (src/messages.py) for r/messages.R, beside the corpus."""
    from api.rundata import store
    from src import messages
    rows = messages.rows(store().inscriptions)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})


def _if_exists(path: str) -> str | None:
    return path if os.path.exists(path) else None


def module_hashes(csv_data: bytes) -> dict[str, str]:
    """En version per modul: korpusen, common.R, modulens skript och versionerna av de moduler den läser. En modul
    med samma version som i en tidigare körning behöver inte räknas om."""
    base = hashlib.sha256(csv_data).hexdigest() + _scripts_hash(["common.R"])
    out: dict[str, str] = {}
    for m in MODULES:  # run order, so upstream versions exist
        key = (base + _scripts_hash([f"{m}.R"]) + "".join(out[u] for u in DEPENDS.get(m, ()))
               + (_remains_hash() if m == "remains" else "") + (_messages_hash() if m == "messages" else ""))
        out[m] = hashlib.sha256(key.encode()).hexdigest()[:16]
    return out


def _reusable(module: str, version: str, exclude: str) -> str | None:
    """Katalogen för en tidigare fullständig körning där modulen hade samma version och lyckades."""
    root = os.path.join(CACHE_DIR, "corpus")
    best = None
    for name in os.listdir(root) if os.path.isdir(root) else []:
        d = os.path.join(root, name)
        p = os.path.join(d, "done.json")
        if name == exclude or not os.path.exists(p):
            continue
        try:
            done = json.load(open(p, encoding="utf-8"))
        except ValueError:
            continue
        if (done.get("module_hashes") or {}).get(module) == version and module not in (done.get("errors") or {}):
            if best is None or os.path.getmtime(p) > os.path.getmtime(os.path.join(best, "done.json")):
                best = d
    return best


def _copy_module(module: str, src: str, dst: str):
    import glob
    for pattern in MODULE_FILES.get(module, (f"{module}*",)):
        for path in glob.glob(os.path.join(src, pattern)):
            target = os.path.join(dst, os.path.basename(path))
            if os.path.isdir(path):
                shutil.copytree(path, target, dirs_exist_ok=True)
            else:
                shutil.copy2(path, target)


def fingerprint(data: bytes) -> str:
    """Korpusens version: data och korpusmodulernas skript (inte sten- och landskapsskripten)."""
    scripts = ["common.R"] + [f"{m}.R" for m in MODULES]
    return hashlib.sha256(data + _scripts_hash(scripts).encode() + _remains_hash().encode()
                          + _messages_hash().encode()).hexdigest()[:16]


# ---- water data ----------------------------------------------------------------------------

def ensure_water() -> str | None:
    """Hämtar Natural Earths vattenlager en gång (för avstånd till vatten). None om det inte går."""
    import requests

    folder = os.path.join(CACHE_DIR, "naturalearth")
    os.makedirs(folder, exist_ok=True)
    ok = True
    for key, url in WATER_LAYERS.items():
        target = os.path.join(folder, key)
        if os.path.isdir(target) and any(n.endswith(".shp") for n in os.listdir(target)):
            continue
        try:
            resp = requests.get(url, timeout=120, headers={"User-Agent": "Vitki/1.0"})
            resp.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                z.extractall(target)
        except Exception:
            ok = False
    return folder if ok or any(os.path.isdir(os.path.join(folder, k)) for k in WATER_LAYERS) else None


# ---- running R -----------------------------------------------------------------------------

class RError(RuntimeError):
    pass


# An R process takes up to about 1 GB: at most R_MAX_PROCS of them at a time from this process (the corpus job runs in
# a process of its own), and one run per result folder, so that two identical requests share one run
_slots = threading.BoundedSemaphore(max(1, int(os.environ.get("R_MAX_PROCS", "2"))))
_dir_locks: dict[str, threading.Lock] = {}
_dir_guard = threading.Lock()


def _dir_lock(out_dir: str) -> threading.Lock:
    with _dir_guard:
        return _dir_locks.setdefault(os.path.abspath(out_dir), threading.Lock())


def _cached_run(path: str, module: str, params: dict, out_dir: str, timeout: int) -> dict:
    """The module's result in `path`, run first if it is missing; a second caller waits for the first one's run (and
    never reads the file while R is still writing it)."""
    with _dir_lock(out_dir):
        if not os.path.exists(path):
            run_module(module, params, out_dir, timeout=timeout)
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)


def run_module(module: str, params: dict, out_dir: str, timeout: int = 3600) -> dict:
    with _slots:
        return _run_module(module, params, out_dir, timeout)


def _run_module(module: str, params: dict, out_dir: str, timeout: int) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    params_path = os.path.join(out_dir, f"{module}_params.json")
    with open(params_path, "w", encoding="utf-8") as fh:
        json.dump(params, fh, ensure_ascii=False)
    proc = spawn.run([rscript(), "--vanilla", os.path.join(R_DIR, f"{module}.R"), params_path, out_dir],
                     capture_output=True, text=True, timeout=timeout, cwd=ROOT,  # src/spawn.py: no fork
                          env={**os.environ, "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"})
    log = (proc.stdout or "") + (proc.stderr or "")
    with open(os.path.join(out_dir, f"{module}.log"), "w", encoding="utf-8") as fh:
        fh.write(log)
    result_path = os.path.join(out_dir, f"{module}.json")
    if proc.returncode != 0 or not os.path.exists(result_path):
        tail = "\n".join(line for line in log.strip().splitlines()[-8:])
        if proc.returncode < 0:  # killed by a signal before R could write anything
            why = ("avbröts av operativsystemet (signal 9), oftast av minnesbrist" if proc.returncode == -9 else
                   f"kraschade (signal {-proc.returncode}); kör modulen med Rscript för att se var")
            tail = f"R {why}." + (f"\n{tail}" if tail else "")
        elif not tail:
            tail = f"R avslutades med kod {proc.returncode} utan felmeddelande."
        raise RError(f"R-modulen {module} misslyckades: {tail[-800:]}")
    with open(result_path, encoding="utf-8") as fh:
        return json.load(fh)


class CorpusJob:
    """Korpusanalyserna körs i en egen process (python -m src.r_bridge <fingeravtryck>) som skriver sitt läge i
    state.json, så att jobbet överlever omstarter av servern och syns från alla serverprocesser."""

    def directory(self, fp: str) -> str:
        return os.path.join(CACHE_DIR, "corpus", fp)

    def ready(self, fp: str) -> bool:
        return os.path.exists(os.path.join(self.directory(fp), "done.json"))

    def done(self, fp: str) -> dict | None:
        """Only done.json (when it was computed, the modules' errors), without the modules' results."""
        if not self.ready(fp):
            return None
        try:
            with open(os.path.join(self.directory(fp), "done.json"), encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):  # a file being written right now
            return None

    def module(self, fp: str, module: str) -> dict | None:
        """One module's result, or None when it is missing."""
        p = os.path.join(self.directory(fp), f"{module}.json")
        if not os.path.exists(p):
            return None
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)

    def result(self, fp: str) -> dict | None:
        out = self.done(fp)
        if out is None:
            return None
        try:
            for m in MODULES:
                out[m] = self.module(fp, m)
        except ValueError:  # a file being written right now
            return None
        return out

    def state_of(self, fp: str) -> dict:
        p = os.path.join(self.directory(fp), "state.json")
        st = {"running": False, "module": None, "error": None, "fingerprint": fp, "done_modules": []}
        if os.path.exists(p):
            try:
                st.update(json.load(open(p, encoding="utf-8")))
            except ValueError:
                pass
        if st.get("running") and not _alive(st.get("pid")):
            st.update(running=False, error=st.get("error") or "Körningen avbröts.")
        return st

    def start(self, fp: str, csv_data: bytes) -> bool:
        if self.ready(fp) or self.state_of(fp).get("running"):
            return False
        d = self.directory(fp)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "corpus.csv"), "wb") as fh:
            fh.write(csv_data)
        _write_state(d, running=True, module=None, error=None, done_modules=[], pid=None,
                     started=datetime.now(timezone.utc).isoformat())
        # posix_spawn in a session of its own (src/spawn.py): a fork of the server, with its gRPC and numpy threads, can
        # crash before the job starts, and the job is to outlive restarts of the server
        pid = spawn.detached([sys.executable, "-m", "src.r_bridge", fp], ROOT, os.path.join(d, "job.log"))
        _write_state(d, pid=pid)
        return True


def _alive(pid) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def _write_state(d: str, **kw):
    p = os.path.join(d, "state.json")
    st = {}
    if os.path.exists(p):
        try:
            st = json.load(open(p, encoding="utf-8"))
        except ValueError:
            st = {}
    st.update(kw)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(st, fh, ensure_ascii=False)
    os.replace(tmp, p)


def run_corpus(fp: str):
    """Kör alla korpusmoduler (anropas i den egna processen)."""
    d = JOB.directory(fp)
    _write_state(d, pid=os.getpid(), running=True)
    errors, done = {}, []
    try:
        water = ensure_water()
        write_messages(os.path.join(d, "messages.csv"))
        from src import pattern_map, places
        params = {"corpus": os.path.join(d, "corpus.csv"), "water_dir": water, "corpus_dir": d, "seed": 2026,
                  "messages": os.path.join(d, "messages.csv"),
                  "tile_dir": os.path.join(CACHE_DIR, "terrain"), "remains": _if_exists(REMAINS),
                  "cult_names": _if_exists(CULT_NAMES), "places": _if_exists(PLACES), "churches": _if_exists(CHURCHES),
                  # The names of the map's patterns and kinds of place, for the figures' labels (hotspots.R, remains.R)
                  "pattern_labels": {k: label for k, label, *_ in pattern_map.PATTERNS},
                  "kind_labels": {k: label for k, label, *_ in places.KINDS}}
        with open(os.path.join(d, "corpus.csv"), "rb") as fh:
            versions = module_hashes(fh.read())
        reused = []
        for m in MODULES:
            _write_state(d, module=m)
            src = _reusable(m, versions[m], os.path.basename(d))
            if src:  # unchanged since an earlier run: copy its results instead of recomputing
                _copy_module(m, src, d)
                reused.append(m)
                done.append(m)
                _write_state(d, done_modules=done)
                continue
            try:
                run_module(m, params, d)
                done.append(m)
                _write_state(d, done_modules=done)
            except Exception as e:  # a failing module is reported, the others still run
                errors[m] = str(e)
        session = ""
        try:
            session = spawn.run([rscript(), "--vanilla", "-e", "sessionInfo()"], capture_output=True,
                                     text=True, timeout=120).stdout
        except Exception:
            pass
        with open(os.path.join(d, "sessionInfo.txt"), "w", encoding="utf-8") as fh:
            fh.write(session)
        tmp = os.path.join(d, "done.json.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"fingerprint": fp, "computed_at": datetime.now(timezone.utc).isoformat(),
                       "errors": errors, "water": bool(water), "r_version": status().get("version"),
                       "module_hashes": versions, "reused": reused},
                      fh, ensure_ascii=False)
        os.replace(tmp, os.path.join(d, "done.json"))  # atomic: readers never see a half-written file
        _write_state(d, running=False, module=None, error="; ".join(errors.values()) or None)
    except Exception as e:
        _write_state(d, running=False, module=None, error=str(e))


JOB = CorpusJob()


def wait_for(fp: str, timeout: float) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if JOB.ready(fp):
            return True
        if not JOB.state_of(fp)["running"]:
            return JOB.ready(fp)
        time.sleep(2)
    return JOB.ready(fp)


def stone(fp: str, signum: str, candidates: list[str], lang: str = "sv") -> dict:
    """R-analysen av en sten mot den sparade korpusanalysen (cachad per sten, kandidater och språk)."""
    d = JOB.directory(fp)
    key = hashlib.sha256(json.dumps([signum, sorted(candidates), lang, _scripts_hash(["common.R", "stone.R"])],
                                    ensure_ascii=False).encode()).hexdigest()[:12]
    out_dir = os.path.join(d, "stones", key)
    res = _cached_run(os.path.join(out_dir, "stone.json"), "stone",
                      {"corpus": os.path.join(d, "corpus.csv"), "corpus_dir": d, "signum": signum, "lang": lang,
                       "candidates": candidates, "water_dir": os.path.join(CACHE_DIR, "naturalearth")},
                      out_dir, timeout=600)
    res["figure_dir"] = out_dir
    return res


def question(fp: str, rows: list[dict], kind: str) -> dict:
    """Kontrollerna i R för Pröva en egen fråga (r/question.R): ristaren som slumpeffekt och platsen som yta. Cachade
    per korpusversion, underlag och skript, så att samma fråga räknas en gång."""
    cols = ["signum", "y", "x", "province", "epoch", "hand", "xk", "yk", "moved"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r[k]) for k in cols})
    data = buf.getvalue().encode("utf-8")
    key = hashlib.sha256(data + kind.encode() + _scripts_hash(["question.R"]).encode()).hexdigest()[:12]
    out_dir = os.path.join(CACHE_DIR, "question", fp, key)
    path = os.path.join(out_dir, "question.json")
    with _dir_lock(out_dir):  # one run per question, as in _cached_run
        if not os.path.exists(path):
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, "data.csv"), "wb") as fh:
                fh.write(data)
            run_module("question", {"data": os.path.join(out_dir, "data.csv"), "kind": kind}, out_dir, timeout=180)
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)


def landscape(fp: str, signum: str, uplift_m: float | None = None, lang: str = "sv") -> dict:
    """Landskapsanalysen av en sten (höjdmodell, strand, sikt, vägar); cachad per sten, landhöjning och språk."""
    d = JOB.directory(fp)
    key = hashlib.sha256(json.dumps([signum, uplift_m, lang, _scripts_hash(["common.R", "landscape.R"])],
                                    ensure_ascii=False).encode()).hexdigest()[:12]
    out_dir = os.path.join(d, "landscape", key)
    params = {"corpus": os.path.join(d, "corpus.csv"), "signum": signum, "lang": lang,
              "water_dir": os.path.join(CACHE_DIR, "naturalearth"), "tile_dir": os.path.join(CACHE_DIR, "terrain")}
    if uplift_m is not None:
        params["uplift_m"] = uplift_m
    res = _cached_run(os.path.join(out_dir, "landscape.json"), "landscape", params, out_dir, timeout=900)
    res["figure_dir"] = out_dir
    return res


def oof_rows(fp: str) -> list[dict]:
    """Korsvaliderade sannolikheter för stenar med säker ristare: förstaval och sannolikheten för rätt ristare."""
    p = os.path.join(JOB.directory(fp), "attribution_oof.csv")
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            probs = {k[len(".pred_"):]: float(v) for k, v in row.items() if k.startswith(".pred_")}
            top = max(probs, key=probs.get)
            # The highest probability the model gave a wrong carver: the null distribution for its suggestions
            wrong = max((v for k, v in probs.items() if k != row["carver"]), default=0.0)
            out.append({"signum": row["signum"], "carver": row["carver"], "top": top, "p": round(probs[top], 3),
                        "p_truth": round(probs.get(row["carver"], 0.0), 3), "p_wrong_max": round(wrong, 4)})
    return out


def stone_rows(fp: str, name: str) -> list[dict]:
    p = os.path.join(JOB.directory(fp), name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k, v in r.items():
            if k == "signum":
                continue
            if v in ("TRUE", "FALSE"):
                r[k] = v == "TRUE"
            else:
                try:
                    r[k] = float(v) if "." in v else int(v)
                except (TypeError, ValueError):
                    pass
    return rows


def figure(directory: str, name: str) -> bytes | None:
    if not re.fullmatch(r"[\w\-]+\.png", name):
        return None
    p = os.path.join(directory, name)
    return open(p, "rb").read() if os.path.exists(p) else None


def package(fp: str, signum: str | None = None, candidates: list[str] | None = None) -> bytes:
    """Reproducerbarhetspaket: R-skripten, korpusens CSV, parametrar, resultat och sessionInfo."""
    d = JOB.directory(fp)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(R_DIR)):
            if name.endswith(".R") or name == "README.md":
                z.write(os.path.join(R_DIR, name), f"r/{name}")
        z.write(os.path.join(d, "corpus.csv"), "data/corpus.csv")
        if os.path.exists(os.path.join(d, "messages.csv")):  # an input of messages.R, not only a result
            z.write(os.path.join(d, "messages.csv"), "data/messages.csv")
        from src import pattern_map, places  # the figures' labels (hotspots.R, remains.R), as run_corpus gives them
        z.writestr("data/etiketter.json", json.dumps(
            {"pattern_labels": {k: label for k, label, *_ in pattern_map.PATTERNS},
             "kind_labels": {k: label for k, label, *_ in places.KINDS}}, ensure_ascii=False, indent=1))
        for name in sorted(os.listdir(d)):
            if name.endswith((".json", ".png", ".csv", ".html")) and name != "corpus.csv" and "_params" not in name:
                z.write(os.path.join(d, name), f"resultat/korpus/{name}")
        if os.path.exists(os.path.join(d, "sessionInfo.txt")):
            z.write(os.path.join(d, "sessionInfo.txt"), "resultat/sessionInfo.txt")
        if signum:
            res = stone(fp, signum, candidates or [])
            for name in sorted(os.listdir(res["figure_dir"])):
                if name.endswith((".json", ".png")) and "_params" not in name:
                    z.write(os.path.join(res["figure_dir"], name), f"resultat/sten/{name}")
        z.writestr("KOR_OM.R", _rerun_script(signum, candidates or []))
        z.writestr("LASMIG.txt", _readme(signum))
    return buf.getvalue()


def _rerun_script(signum: str | None, candidates: list[str]) -> str:
    # Every corpus module, in the order the app runs them (later modules read the earlier ones' results in om/), with
    # the same parameters as run_corpus; the remains and place names are optional files the user adds under data/
    modules = ", ".join(f'"{m}"' for m in MODULES)
    lines = [
        "# Kör om analyserna från projektets rotmapp i paketet: Rscript KOR_OM.R",
        "# Paketen installeras med: Rscript r/install.R",
        'dir.create("om", showWarnings = FALSE)',
        'opt <- function(f) if (file.exists(f)) normalizePath(f) else NULL',
        'lab <- if (file.exists("data/etiketter.json")) jsonlite::fromJSON("data/etiketter.json", simplifyVector = FALSE) else list()',
        'params <- list(corpus = normalizePath("data/corpus.csv"), corpus_dir = normalizePath("om"),',
        '               water_dir = if (dir.exists("naturalearth")) normalizePath("naturalearth") else NULL, seed = 2026,',
        '               messages = opt("data/messages.csv"), remains = opt("data/lamningar.csv"),',
        '               cult_names = opt("data/kultnamn.csv"), places = opt("data/platser.csv"),',
        '               churches = opt("data/kyrkor.csv"), pattern_labels = lab$pattern_labels, kind_labels = lab$kind_labels)',
        'p <- file.path("om", "params.json"); jsonlite::write_json(params, p, auto_unbox = TRUE, null = "null")',
        f'for (m in c({modules}))',
        '  system2("Rscript", c("--vanilla", file.path("r", paste0(m, ".R")), p, "om"))',
    ]
    if signum:
        cand = ", ".join(f'"{c}"' for c in candidates)
        lines += [
            f'sp <- list(corpus = params$corpus, corpus_dir = params$corpus_dir, signum = "{signum}",',
            f'           candidates = c({cand}), water_dir = params$water_dir)',
            'dir.create(file.path("om", "sten"), showWarnings = FALSE)',
            'p2 <- file.path("om", "sten", "params.json"); jsonlite::write_json(sp, p2, auto_unbox = TRUE, null = "null")',
            'system2("Rscript", c("--vanilla", file.path("r", "stone.R"), p2, file.path("om", "sten")))',
        ]
    return "\n".join(lines) + "\n"


def _readme(signum: str | None) -> str:
    return (
        "Reproducerbarhetspaket – Vitki, statistik i R\n\n"
        "r/              R-skripten som appen kör (" + ", ".join(MODULE_LABELS[m][:1].lower() + MODULE_LABELS[m][1:] for m in MODULES)
        + (", stenen" if signum else "") + ")\n"
        "data/corpus.csv korpusen: svenska vikingatida runstenar ur Samnordisk runtextdatabas, med kategorier\n"
        "                och språkdrag som appen räknat fram (se METHODS.md)\n"
        "data/messages.csv budskapen per sten (indata till messages.R)\n"
        "data/etiketter.json mönstrens och platsernas namn för figurerna\n"
        "resultat/       appens resultat, figurer och sessionInfo() för den körning som gav dem\n"
        "KOR_OM.R        kör om alla " + str(len(MODULES)) + " korpusanalyser" + (" och stenens analys" if signum else "")
        + "; resultaten hamnar i om/\n\n"
        "Avstånd till vatten kräver Natural Earths lager (1:10 milj.) i mappen naturalearth/ med undermapparna\n"
        + ", ".join(WATER_LAYERS) + "; utan dem hoppas den delen över.\n"
        "Lämningarna runt stenarna (remains.R) kräver data/lamningar.csv (Riksantikvarieämbetets Kulturmiljöregister,\n"
        "hämtad med appens scripts/fetch_raa_remains.py) och, för ortnamnen och kyrkorna, data/kultnamn.csv,\n"
        "data/platser.csv och data/kyrkor.csv (scripts/fetch_place_names.py). De följer inte med paketet; utan dem\n"
        "skriver remains.R bara att lämningarna saknas, och lämningarnas resultat i resultat/korpus/ går inte att köra om.\n\n"
        "Källa: Samnordisk runtextdatabas, Institutionen för nordiska språk, Uppsala universitet (ODbL-1.0 / DbCL-1.0).\n"
        + (f"Stenen i paketet: {signum}.\n" if signum else "")
    )


if __name__ == "__main__":
    run_corpus(sys.argv[1])
