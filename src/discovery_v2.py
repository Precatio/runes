"""Upptäcktsmotorn, version 2: version 1:s drag (src/discovery.py) plus ord, material, ortnamnsmiljö och stengrupper,
enligt den låsta planen analysplaner/2026-10-29-upptacktsmotorn-v2.md. Skriver dragmatrisen, familjerna och de
familjepar som inte prövas (FORBID) för r/discovery_v2.R och r/discovery_lokal.R.
    .venv/bin/python -m src.discovery_v2 data/cache/r/corpus/<fp> utdata/upptackt_v2/drag.csv"""
from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter

import numpy as np
from scipy.spatial import cKDTree

from src import discovery, places

ROOT = discovery.ROOT
MIN_WORD_STONES = 30
N_WORDS = 60
CHURCH_PLACE = re.compile(r"kyrka\b|kyrkan\b|kyrkogård|kyrkoruin|ödekyrk", re.I)
CHURCH_PLACEMENT = re.compile(r"kyrk|vapenhus|\btorn|bogård|stiglucka|koret|sakristi|gravkor|inmurad", re.I)
MUSEUM = re.compile(r"museum|museet|samling|SHM|magasin|förråd|lapidarium|Skansen|Runverket|Förvara|privatperson", re.I)
OLD = re.compile(r"(?:sta|stad|by|inge|inga|vin|hem|lösa|tuna)$")
YOUNG = re.compile(r"(?:torp|torpet|ryd|hult|boda)$")
MATERIALS = ("granit", "sandsten", "kalksten", "gnejs")
WORD_BOUND = ("monoftong", "au", "o_runa", "r", "prep", "h", "nasal")
TEXT = ("ord", "familj", "resa", "arv", "kristen", "egen", "berom", "hednisk", "bro", "ting", "dod_kvinna", "ristare",
        "stungna") + WORD_BOUND
CONTENT = ("ord", "familj", "resa", "arv", "kristen", "egen", "berom", "hednisk", "bro", "ting", "dod_kvinna")
FORBID = sorted({tuple(sorted(("ord", f))) for f in TEXT} | {tuple(sorted((w, f))) for w in WORD_BOUND for f in CONTENT})


def tokens(norm: str) -> set[str]:
    """Ordformerna i en normalisering med r/words.R:s regler (namn, skadade ord och lösa fragment bort)."""
    out = set()
    for raw in (norm or "").split():
        if '"' in raw:
            continue
        t = re.sub(r"[\"\[\]()<>{}«»]", "", raw)
        t = re.sub(r"^[.,;:!?+·×=§|/\\'’]+|[.,;:!?+·×=§|/\\'’]+$", "", t)
        if not t or re.search(r"\.\.\.|[-?…]", t) or (len(t) == 1 and t.lower() not in ("a", "i", "ø")):
            continue
        t = t[0].lower() + t[1:]
        if re.fullmatch(r"[a-zåäöæøǫœęþðáéíóúýūōR]+", t):
            out.add(t)
    return out


def _xy(lat, lon):
    return places._xy(np.asarray(lat, float), np.asarray(lon, float))


def rows(corpus_dir: str) -> tuple[list[dict], dict]:
    base = discovery.rows(corpus_dir)
    corpus = discovery._read(os.path.join(corpus_dir, "corpus.csv"))
    recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
    fam = {k: ("familj" if v in ("resare", "relation") else v) for k, v in discovery.FAMILY.items()}

    # Ord
    toks = {r["signum"]: tokens(corpus[r["signum"]].get("normalization")) for r in base}
    cnt = Counter(w for ts in toks.values() for w in ts)
    words = [w for w, n in cnt.most_common() if MIN_WORD_STONES <= n <= len(base) / 2][:N_WORDS]
    for r in base:
        for w in words:
            r[f"ord_{w}"] = int(w in toks[r["signum"]])
    fam.update({f"ord_{w}": "ord" for w in words})

    # Material
    for r in base:
        m = (corpus[r["signum"]].get("material") or "").lower()
        for k in MATERIALS:
            r[f"mat_{k}"] = int(k in m) if m else None
    fam.update({f"mat_{k}": "material" for k in MATERIALS})

    # Plats: på sin plats, vid kyrkan (lokaliserad) och ortnamnsmiljö
    lat = np.array([discovery._num(corpus[r["signum"]].get("lat")) or np.nan for r in base])
    lon = np.array([discovery._num(corpus[r["signum"]].get("lon")) or np.nan for r in base])
    moved = np.array([corpus[r["signum"]].get("moved") == "1" for r in base])
    lost = np.array([corpus[r["signum"]].get("lost") == "1" for r in base])
    insitu = ~moved & ~lost & ~np.isnan(lat)
    for i, r in enumerate(base):
        rec = recs[r["signum"]]
        plc, pln = rec.get("placement") or "", rec.get("place") or ""
        church = bool(CHURCH_PLACEMENT.search(plc) or CHURCH_PLACE.search(pln)) and not MUSEUM.search(plc + " " + pln)
        r["lat"], r["lon"] = (None if np.isnan(lat[i]) else lat[i]), (None if np.isnan(lon[i]) else lon[i])
        r["pa_plats"] = int(insitu[i])
        r["lokal"] = int(insitu[i] or (church and not lost[i] and not np.isnan(lat[i])))
    # Ortnamnsmiljö och stengrupper räknas mot alla stenar på sin plats i korpusen (inte bara de med fyra ord)
    allc = [c for c in corpus.values() if c.get("moved") == "0" and c.get("lost") == "0" and c.get("lat")]
    axy = _xy([float(c["lat"]) for c in allc], [float(c["lon"]) for c in allc])
    atree = cKDTree(axy)
    sxy = _xy(lat[insitu], lon[insitu])
    pl = list(csv.DictReader(open(os.path.join(ROOT, "data", "ortnamn", "platser.csv"), encoding="utf-8")))
    pl = [p for p in pl if p["place"] in ("village", "hamlet", "farm", "isolated_dwelling", "locality")]

    def near(pts, radius):
        d, _ = cKDTree(_xy([float(p["lat"]) for p in pts], [float(p["lon"]) for p in pts])).query(sxy)
        return (d <= radius).astype(int)

    pp = places.places()
    env = {"nara_gammalt_namn": near([p for p in pl if OLD.search(p["name"].lower())], 1000),
           "nara_ungt_namn": near([p for p in pl if YOUNG.search(p["name"].lower())], 1000),
           "nara_kultnamn": near(pp["cult_a"] + pp["cult_b"], 2000),
           "nara_centralort": near(pp["central"], 5000)}
    grp = []
    for p in sxy:
        ds = np.linalg.norm(axy[atree.query_ball_point(p, 500)] - p, axis=1)
        grp.append(int(((ds > 25) & (ds <= 500)).any()))
    env["i_grupp"] = np.array(grp)
    idx = np.where(insitu)[0]
    for k, v in env.items():
        for r in base:
            r[k] = None
        for j, i in enumerate(idx):
            base[i][k] = int(v[j])
        fam[k] = "landskap"
    return base, fam


def write(corpus_dir: str, path: str) -> int:
    rs, fam = rows(corpus_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rs[0]))
        w.writeheader()
        for r in rs:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    stem = os.path.splitext(path)[0]
    json.dump(fam, open(stem + "_familjer.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump([list(p) for p in FORBID], open(stem + "_forbjudna.json", "w", encoding="utf-8"), ensure_ascii=False)
    return len(rs)


if __name__ == "__main__":
    import sys
    print(write(sys.argv[1], sys.argv[2]))
