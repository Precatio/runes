"""Sannolikhetsmodellen i appen (inskriftssidans panel "Läsning och luckor"): för en vikingatida inskrift modellens
läsning ord för ord, ifyllning av förlorade runor – med det som syns av dem, om användaren anger det –, datering ur
språket och översättningsutkast på svenska och engelska. Bygger på src/runlm.py och src/rungloss.py; proven och
siffrorna finns i METHODS.md, avsnitt 8.1.

En inskrift läses alltid av en modell som inte är tränad på den. Inskrifterna delas i fem delar efter signum, och en
inskrift i del k läses av modellen som tränats på de fyra andra – annars skulle en lucka som Rundata har återställt
fyllas av en modell som redan läst återställningen. Modellerna byggs först när de behövs (omkring en halv minut
vardera) och resultaten sparas per inskrift i data/cache/textmodel/."""
import json
import os
import re
import threading
import zlib
from datetime import datetime, timezone

from src import runlm as rl
from src import rungloss as rg

VERSION = "textmodel-2"
K = 5
CACHE = os.path.join(rl.ROOT, "data", "cache", "textmodel", VERSION)
MAX_GAP = 4  # longer runs of lost runes are left open: the masking test covers 1–4 runes
FILL = dict(window=None, char_fills=15, context_cands=True, n_cands=100, by_word=True, near_km=10.0, lam_near=0.1)
MODEL = dict(aligned=True, lam_name=0.05, contexts=True, alpha=100.0, kappa_e=50.0, lm_beta=200.0)
EPOCH_LABEL = {"800": "800-talet", "900": "900-talet", "1000": "1000–1070", "1100": "1070–1150"}
# What the tests showed (METHODS.md 8.1), shown with the results so that a reader can judge them
VALIDATION = {"inside_word": 0.72, "whole_word": 0.56, "sure_right": 0.93, "rundata_sure": 0.96,
              "with_traces": 0.85, "dating_epoch": 0.58, "dating_near": 0.93}

_lock = threading.Lock()
_compute = threading.Lock()  # one reading at a time: the models' caches are shared
_bundles: dict = {}
_data: dict = {}


def fold_of(signum: str) -> int:
    return zlib.crc32(signum.encode("utf-8")) % K


def _records() -> dict:
    if "by" not in _data:
        recs = rl.load_rundata()
        cal = os.path.join(rl.ROOT, "data", "runlm_calibration.json")
        _data.update(recs=recs, by={r["signum"]: r for r in recs},
                     V=[r for r in recs if rl.viking(r) and r.get("transliteration") and r.get("normalization")],
                     da=rg.load_danish(recs), edda=rl.edda_tokens(),
                     T=json.load(open(cal))["dating_temperature"] if os.path.exists(cal) else None)
    return _data


def bundle(k: int) -> dict:
    """The model, glossaries and Old Norse forms learned from every inscription outside part k."""
    with _lock:
        if k in _bundles:
            return _bundles[k]
        d = _records()
        keep = lambda r: fold_of(r["signum"]) != k
        m = rl.Model([r for r in d["V"] if keep(r)], edda_tokens=d["edda"], **MODEL)
        rest = [r for r in d["recs"] if keep(r)]
        da_recs = [dict(r, translation_da=d["da"][r["signum"]]) for r in rest if r["signum"] in d["da"]]
        _bundles[k] = {
            "model": m, "en": rg.Glossary([r for r in rest if r.get("translation_en")]),
            "da": rg.Glossary(da_recs, field="translation_da", words=rg._danish, src="normalization_ows") if da_recs else None,
            "ows": rg.ows_map(rest)}
        return _bundles[k]


def text_groups(translit: str) -> tuple[list[str], list[int]]:
    """The carved groups with every lost rune ('-') written '?', and the groups followed by a break: text lost to an
    unknown extent ('...') or a sign that is not read, where the reading starts afresh."""
    groups, breaks = [], []
    for _, t in rl.sections(translit):
        for g in re.split(rl.DIV, rl.clean_translit(t)):
            g = rl.runekey(re.sub(r"\s+", "", g)).replace("-", "?")
            pieces = re.split(r"([^a-zþðæøåöäąR?]+)", g)
            for q, p in enumerate(pieces):
                if q % 2 == 1:  # a separator: a break after the group before it
                    if groups and p.strip():
                        breaks.append(len(groups) - 1)
                elif p:
                    groups.append(p)
        if groups:
            breaks.append(len(groups) - 1)  # a new section starts afresh
    return groups, sorted(set(breaks))


def _parts(groups, breaks):
    """The text without its open gaps: pieces of the groups and where the reading may break at no cost."""
    parts, sg, at = [], [], []
    for idx, grp in enumerate(groups):
        pieces = [p for p in grp.split("?") if p]
        for q, p in enumerate(pieces):
            parts.append(p)
            if q < len(pieces) - 1 or idx in breaks or (q == len(pieces) - 1 and grp.endswith("?")):
                sg.append(len(parts) - 1)
    return parts, sg


def _safe(signum: str) -> str:
    return re.sub(r"[^A-Za-z0-9ÅÄÖåäöÆØæø;_-]+", "_", signum)


def analyze(signum: str, allowed: dict | None = None) -> dict:
    """The model's reading of an inscription. allowed: {gap number: for each lost rune of the gap the runes its
    visible remains allow ('' or None: nothing visible)}; without it the result is cached."""
    d = _records()
    r = d["by"].get(signum)
    if r is None:
        raise KeyError(signum)
    base = {"signum": signum, "version": VERSION, "validation": VALIDATION}
    if not (rl.viking(r) and r.get("transliteration")):
        return {**base, "available": False,
                "reason": "Modellen är byggd för vikingatida inskrifter med en translitterering i Rundata."}
    path = os.path.join(CACHE, _safe(signum) + ".json")
    if not allowed and os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except ValueError:
            pass
    groups, breaks = text_groups(r["transliteration"])
    if sum(len(g.replace("?", "")) for g in groups) < 4:
        return {**base, "available": False, "reason": "För få läsbara runor för att läsa texten."}
    b = bundle(fold_of(signum))
    with _compute:
        out = _read(r, groups, breaks, b, allowed, base, d)
    if not allowed:
        os.makedirs(CACHE, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False)
        os.replace(tmp, path)
    return out


def _read(r, groups, breaks, b, allowed, base, d):
    m = b["model"]
    site = (float(r["lat"]), float(r["lon"])) if r.get("lat") is not None and r.get("lon") is not None else None
    every = [(gi, x.start(), x.end()) for gi, g in enumerate(groups) for x in re.finditer(r"\?+", g)]
    fillable = [gp for gp in every if gp[2] - gp[1] <= MAX_GAP]
    traces = {fillable[int(n)]: [s or None for s in v] for n, v in (allowed or {}).items()
              if str(n).isdigit() and int(n) < len(fillable) and len(v) == fillable[int(n)][2] - fillable[int(n)][1]}
    details: dict = {}
    combos, gaps, words = (rl.restore_all(m, groups, signs=breaks, only=fillable, site=site, allowed=traces,
                                          details=details, **FILL) if fillable else ([], [], {}))
    best = combos[0][0] if combos else ()
    filled = list(groups)
    for (gi, a, e), f in sorted(zip(gaps, best), key=lambda x: (-x[0][0], -x[0][1])):
        filled[gi] = filled[gi][:a] + f + filled[gi][e:]
    parts, sg = _parts(filled, breaks)
    _, read, _, text, _, ll = rl.decode_epochs(m, parts, sg)
    # where the filled runes stand in the read text, and where the text breaks
    spans = []
    for (gi, a, e), f in zip(gaps, best):
        at = sum(len(x.replace("?", "")) for x in filled[:gi]) + len(filled[gi][:a].replace("?", ""))
        spans.append((at, at + len(f)))
    ends, pos = set(), 0
    for i, p in enumerate(parts):
        pos += len(p)
        if i in sg:
            ends.add(pos)
    def p_filled(i, j, w):
        """A word with filled runes is as probable as that word in its gaps (the reading itself takes the filling as
        given): the smallest probability of the word over the gaps it covers."""
        qs = [sum(q for w_, q in words.get(n, {}).items() if w_ != "<unk>" and rl.same_word(w_, w)) if w != "<unk>"
              else words.get(n, {}).get("<unk>", 0.0)
              for n, (a_, e_) in enumerate(spans) if i < e_ and a_ < j]
        return min(qs) if qs else None

    reading = []
    for i, j, w, p in read:
        filled = any(i < e_ and a_ < j for a_, e_ in spans)
        pf = p_filled(i, j, w) if filled else None
        reading.append({"runes": text[i:j], "word": w.lstrip("§"), "name": w.startswith("§"), "unknown": w == "<unk>",
                        "p": round(pf if pf is not None else p, 4), "filled": filled, "break_after": j in ends})
    prior = {e: (m.epoch_prior[e] or 1) for e in rl.EPOCHS}
    dating = rl.epoch_posterior(ll, prior, d["T"] or 1.0)
    vocab = [w for _, _, w, _ in read]
    out = {
        **base, "available": True, "computed_at": datetime.now(timezone.utc).isoformat(),
        "groups": groups, "reading": reading,
        "gaps": [{"number": n, "group": gi, "start": a, "end": e, "carved": groups[gi], "n": e - a,
                  "best": best[n] if n < len(best) else None,
                  "fills": [{"fill": f, "p": round(p, 4), "word": (w or "").lstrip("§") or None}
                            for f, p, w in details.get(n, [])[:8]],
                  "words": [{"word": w.lstrip("§"), "p": round(p, 4)} for w, p in list(words.get(n, {}).items())[:6]],
                  "traces": traces.get((gi, a, e))}
                 for n, (gi, a, e) in enumerate(gaps)],
        "open_gaps": [{"group": gi, "start": a, "end": e, "n": e - a} for gi, a, e in every if e - a > MAX_GAP],
        "dating": {"epochs": [{"epoch": e, "label": EPOCH_LABEL[e], "p": round(dating[e], 4)} for e in rl.EPOCHS],
                   "calibrated": bool(d["T"]), "rundata": r.get("dating") or ""},
        "translation": {"sv": rg.swedish(vocab, b["en"], b["da"], b["ows"]), "en": b["en"].translate(vocab)},
    }
    return out
