"""De möjliga okända ristarna mot bergart, storlek och namn: H1–H3 och den positiva kontrollen enligt den låsta planen
analysplaner/2026-10-29-okanda-ristare-oberoende.md.
    .venv/bin/python utdata/okanda_ristare/analys.py      Skriver okanda_ristare.json."""
import json
import math
import os
import re
import sys
from collections import Counter

import numpy as np
from pyproj import Transformer
from scipy.stats import chi2

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
import csv  # noqa: E402

from api.rundata import store  # noqa: E402
from src import entities, geology, stone_dimensions  # noqa: E402

FP = "3f58e9339191761e"
RADIUS_KM = 30
B = 9999
MIN_DATA = 4
SEED = 20261029
CANDIDATES = (2, 5, 6, 12, 13)
ROCK = re.compile(r"\b(gråsten|granit\w*|gnejs\w*|sandsten\w*|kalksten\w*|porfyr\w*|diorit\w*|gabbro|diabas|"
                  r"kvartsit\w*|hälleflinta|leptit|skiffer|amfibolit|ryolit|migmatit|marmor)", re.I)

corpus = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
rows = [r for r in csv.DictReader(open(os.path.join(corpus, "corpus.csv"), encoding="utf-8")) if r["lat"] and r["lon"]]
anon = json.load(open(os.path.join(corpus, "anonymous.json"), encoding="utf-8"))
kmr, kmr_refs = {}, {}
for r in json.load(open(os.path.join(ROOT, "data", "raa", "kmr_runstenar.json"), encoding="utf-8"))["records"]:
    if len(r["signa"]) == 1:
        kmr[r["signa"][0]] = " ".join(r["fields"].get("Beskrivning", []))
        kmr_refs[r["signa"][0]] = r["fields"].get("Referens: skriftlig källa", [])
dims = stone_dimensions.load().get("stones") or {}
s = store()

T = Transformer.from_crs(4326, 3006, always_xy=True)
xy = np.array(T.transform([float(r["lon"]) for r in rows], [float(r["lat"]) for r in rows])).T / 1000
sig = [r["signum"] for r in rows]
idx = {x: i for i, x in enumerate(sig)}
style = [r["style"] or "" for r in rows]


def rock(signum: str, material: str) -> frozenset:
    fam = geology.families(material or "")
    if not fam:
        m = ROCK.search(kmr.get(signum, ""))
        fam = geology.families(m.group(1)) if m else set()
    return frozenset(fam)


def height(signum: str) -> float | None:
    d = dims.get(signum) or {}
    if d.get("status") != "ok" or d.get("fragment") or not d.get("height_m"):
        return None
    return math.log(d["height_m"])


def names(signum: str) -> frozenset:
    rec = s.get(signum)
    if not rec:
        return frozenset()
    return frozenset(p["key"] for p in entities.extract(rec)["persons"] if not p.get("uncertain") and p.get("key"))


ROCKS = [rock(r["signum"], r["material"]) for r in rows]
HEIGHT = np.array([np.nan if height(x) is None else height(x) for x in sig])
NAMES = [names(x) for x in sig]


def matrices(ix: np.ndarray):
    """Parmatriserna för stenarna ix: delad bergart, höjdskillnad, delat namn (NaN där uppgiften saknas)."""
    n = len(ix)
    rk = [ROCKS[i] for i in ix]
    nm = [NAMES[i] for i in ix]
    has_r = np.array([bool(x) for x in rk])
    mr = np.full((n, n), np.nan)
    mn = np.zeros((n, n))
    for a in range(n):
        for b in range(a + 1, n):
            if has_r[a] and has_r[b]:
                mr[a, b] = mr[b, a] = float(bool(rk[a] & rk[b]))
            mn[a, b] = mn[b, a] = float(bool(nm[a] & nm[b]))
    h = HEIGHT[ix]
    mh = np.abs(h[:, None] - h[None, :])
    return {"rock": mr, "height": mh, "names": mn}


def stat(m: np.ndarray, sub: np.ndarray) -> float:
    x = m[np.ix_(sub, sub)]
    iu = np.triu_indices(len(sub), 1)
    v = x[iu]
    v = v[~np.isnan(v)]
    k = (1 + math.isqrt(1 + 8 * len(v))) // 2 if len(v) else 0  # stones with data, from the number of pairs
    return float(v.mean()) if len(v) and k >= MIN_DATA else float("nan")


def n_with(kind: str, members: list[int]) -> int:
    if kind == "rock":
        return sum(bool(ROCKS[i]) for i in members)
    if kind == "height":
        return int(np.sum(~np.isnan(HEIGHT[members])))
    return len(members)


def test(members: list[int], rng: np.random.Generator) -> dict:
    """Gruppen mot B slumpmängder ur trakten med samma fördelning på stilgrupp."""
    centre = xy[members].mean(axis=0)
    dist = np.hypot(*(xy - centre).T)
    mset = set(members)
    pool = [i for i in np.where(dist <= RADIUS_KM)[0] if i not in mset]
    ix = np.array(members + pool)
    M = matrices(ix)
    g = np.arange(len(members))
    pool_local = np.arange(len(members), len(ix))
    by_style: dict[str, list[int]] = {}
    for j in pool_local:
        by_style.setdefault(style[ix[j]], []).append(j)
    obs = {k: stat(M[k], g) for k in M}
    draws = {k: [] for k in M}
    for _ in range(B):
        used: set[int] = set()
        pick = []
        for i in members:
            cands = [j for j in by_style.get(style[i], []) if j not in used]
            if not cands:  # no stone of that style group left in the area: any stone from the area, as the plan says
                cands = [j for j in pool_local if j not in used]
            j = cands[rng.integers(len(cands))]
            used.add(j)
            pick.append(j)
        sub = np.array(pick)
        for k in M:
            draws[k].append(stat(M[k], sub))
    out = {"n": len(members), "n_pool": len(pool)}
    for k in M:
        d = np.array(draws[k])
        d = d[~np.isnan(d)]
        o = obs[k]
        if math.isnan(o) or not len(d):
            out[k] = {"n_data": n_with(k, members), "tested": False}
            continue
        extreme = np.sum(d <= o) if k == "height" else np.sum(d >= o)
        out[k] = {"n_data": n_with(k, members), "tested": True, "obs": o, "null_mean": float(d.mean()),
                  "p": float((1 + extreme) / (1 + len(d))), "n_null": int(len(d))}
    return out


def fisher(ps: list[float]) -> dict:
    ps = [p for p in ps if p is not None]
    if not ps:
        return {"k": 0, "p": None}
    x = -2 * sum(math.log(p) for p in ps)
    return {"k": len(ps), "p": float(chi2.sf(x, 2 * len(ps)))}


def summarize(results: list[dict]) -> dict:
    return {k: {**fisher([r[k]["p"] for r in results if r[k].get("tested")]),
                "share_p05": (sum(1 for r in results if r[k].get("tested") and r[k]["p"] < 0.05)
                              / max(1, sum(1 for r in results if r[k].get("tested"))))}
            for k in ("rock", "height", "names")}


rng = np.random.default_rng(SEED)
# Positive control: known carvers in Uppland and Södermanland with at least five certain stones
carv = Counter(r["carver"] for r in rows if r["carver"] and r["province"] in ("U", "Sö"))
control = []
for name, n in sorted(carv.items()):
    if n < 5:
        continue
    members = [i for i, r in enumerate(rows) if r["carver"] == name and r["province"] in ("U", "Sö")]
    control.append({"carver": name, **test(members, rng)})
    print("kontroll", name, n, flush=True)
ctrl = summarize(control)

cand = []
for g in anon["groups"]:
    if g["id"] not in CANDIDATES:
        continue
    st = [x if isinstance(x, str) else x.get("signum") for x in g["stones"]]
    members = [idx[x] for x in st if x in idx]
    res = test(members, rng)
    shared = Counter(n for i in members for n in NAMES[i])
    res.update({"id": g["id"], "parish": g["parish"], "type_stone": g["type_stone"], "stones": st,
                "rocks": dict(Counter("/".join(sorted(ROCKS[i])) or "okänd" for i in members)),
                "heights_m": [round(math.exp(HEIGHT[i]), 2) for i in members if not np.isnan(HEIGHT[i])],
                "shared_names": {k: v for k, v in shared.items() if v >= 2},
                "refs": {x: kmr_refs.get(x, []) for x in st}})
    cand.append(res)
    print("kandidat", g["parish"], flush=True)
cs = summarize(cand)

ps = {"H1": cs["rock"]["p"], "H2": cs["height"]["p"], "H3": cs["names"]["p"]}
valid = {k: v for k, v in ps.items() if v is not None}
order = sorted(valid, key=valid.get)
holm, running = {}, 0.0
for r, k in enumerate(order):
    running = max(running, min(1.0, valid[k] * (len(valid) - r)))
    holm[k] = running
informative = {"H1": (ctrl["rock"]["p"] or 1) < 0.05, "H2": (ctrl["height"]["p"] or 1) < 0.05,
               "H3": (ctrl["names"]["p"] or 1) < 0.05}
holds = {k: k in holm and holm[k] < 0.05 for k in ps}
if holds["H3"]:
    reading = "familjens beställningar möjliga"
elif (holds["H1"] and informative["H1"]) or (holds["H2"] and informative["H2"]):
    reading = "stöd för verkstad eller ristare"
else:
    reading = "ristare och lokal skrivsed går inte att skilja"
out = {"plan": "analysplaner/2026-10-29-okanda-ristare-oberoende.md", "fingerprint": FP, "B": B, "radius_km": RADIUS_KM,
       "control": {"n_carvers": len(control), "summary": ctrl, "carvers": control},
       "candidates": {"summary": cs, "groups": cand}, "p": ps, "holm": holm, "holds": holds,
       "informative": informative, "reading": reading}
json.dump(out, open(os.path.join(OUT, "okanda_ristare.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
          default=float)
print(json.dumps({k: out[k] for k in ("p", "holm", "holds", "informative", "reading")}, ensure_ascii=False))
print("kontroll", json.dumps(ctrl), "kandidater", json.dumps(cs))
