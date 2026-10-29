"""Mästarmodellen, steg 2 och del 1–2 i analysplaner/2026-10-29-en-och-samma-mastare.md: tidsspann, bergart, namn och
ovanliga stavningar för kalibreringsgrupperna och kandidaterna (percentiler mot trakten, 199 dragningar), H5 (ovanliga
stavningar, 9 999 dragningar, positiv kontroll) och tidsjämförelsen med de kända ristarna.
    .venv/bin/python utdata/okanda_ristare/mastare_drag.py      Skriver mastare_drag.csv och mastare_del12.json."""
import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np
from pyproj import Transformer
from scipy import sparse
from scipy.stats import chi2

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import entities, geology, stone_dimensions  # noqa: E402

FP = "3f58e9339191761e"
RADIUS_KM = 30
B_MODEL, B_TEST = 199, 9999
MIN_DATA = 4
MIN_LEMMA, RARE_SHARE = 5, 0.10
SEED = 20261029
ROCK = re.compile(r"\b(gråsten|granit\w*|gnejs\w*|sandsten\w*|kalksten\w*|porfyr\w*|diorit\w*|gabbro|diabas|"
                  r"kvartsit\w*|hälleflinta|leptit|skiffer|amfibolit|ryolit|migmatit|marmor)", re.I)

corpus = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
rows = [r for r in csv.DictReader(open(os.path.join(corpus, "corpus.csv"), encoding="utf-8")) if r["lat"] and r["lon"]]
sig = [r["signum"] for r in rows]
idx = {x: i for i, x in enumerate(sig)}
N = len(rows)
T = Transformer.from_crs(4326, 3006, always_xy=True)
xy = np.array(T.transform([float(r["lon"]) for r in rows], [float(r["lat"]) for r in rows])).T / 1000
style = np.array([r["style"] or "" for r in rows])
mid = np.array([(float(r["style_from"]) + float(r["style_to"])) / 2 if r["style_from"] and r["style_to"] else np.nan
                for r in rows])
prov = [r["province"] for r in rows]

# --- the traits, as pair matrices over all stones ---
kmr = {}
for r in json.load(open(os.path.join(ROOT, "data", "raa", "kmr_runstenar.json"), encoding="utf-8"))["records"]:
    if len(r["signa"]) == 1:
        kmr[r["signa"][0]] = " ".join(r["fields"].get("Beskrivning", []))
fams = sorted(geology.FAMILIES)


def rock(i: int) -> int:
    f = geology.families(rows[i]["material"] or "")
    if not f:
        m = ROCK.search(kmr.get(sig[i], ""))
        f = geology.families(m.group(1)) if m else set()
    return sum(1 << fams.index(x) for x in f)


RM = np.array([rock(i) for i in range(N)])
HAS_R = RM > 0
R_SHARE = np.where(HAS_R[:, None] & HAS_R[None, :], ((RM[:, None] & RM[None, :]) > 0).astype(float), np.nan)

dims = stone_dimensions.load().get("stones") or {}
H = np.array([math.log(dims[s]["height_m"]) if (dims.get(s) or {}).get("status") == "ok" and not dims[s].get("fragment")
              and dims[s].get("height_m") else np.nan for s in sig])
H_DIFF = np.abs(H[:, None] - H[None, :])

st = store()


def incidence(sets: list[set]) -> np.ndarray:
    vocab = {v: j for j, v in enumerate(sorted({x for s in sets for x in s}))}
    m = sparse.lil_matrix((N, max(1, len(vocab))), dtype=np.int32)
    for i, s in enumerate(sets):
        for v in s:
            m[i, vocab[v]] = 1
    m = m.tocsr()
    return ((m @ m.T).toarray() > 0).astype(float)


names = []
for s in sig:
    rec = st.get(s)
    names.append({p["key"] for p in entities.extract(rec)["persons"] if not p.get("uncertain") and p.get("key")} if rec else set())
N_SHARE = incidence(names)

# rare spellings: lemma on >= 5 stones in the province, the spelling on at most 10 % of them
spell = [dict(p.split("=", 1) for p in r["pairs"].split("|") if "=" in p) if r["pairs"] else {} for r in rows]
lemma_n, form_n = defaultdict(Counter), defaultdict(Counter)
for i, sp in enumerate(spell):
    for lem, form in sp.items():
        lemma_n[prov[i]][lem] += 1
        form_n[prov[i]][(lem, form)] += 1
rare = [{f"{lem}={form}" for lem, form in sp.items()
         if lemma_n[prov[i]][lem] >= MIN_LEMMA and form_n[prov[i]][(lem, form)] / lemma_n[prov[i]][lem] <= RARE_SHARE}
        for i, sp in enumerate(spell)]
HAS_SP = np.array([bool(sp) for sp in spell])
RARE_SHARE_M = np.where(HAS_SP[:, None] & HAS_SP[None, :], incidence(rare), np.nan)
MATS = {"rock": R_SHARE, "height": H_DIFF, "names": N_SHARE, "rare": RARE_SHARE_M}
LOWER_IS_SIMILAR = {"height"}


def stat(M: np.ndarray, sub: np.ndarray) -> float:
    x = M[np.ix_(sub, sub)][np.triu_indices(len(sub), 1)]
    x = x[~np.isnan(x)]
    k = (1 + math.isqrt(1 + 8 * len(x))) // 2 if len(x) else 0
    return float(x.mean()) if len(x) and k >= MIN_DATA else float("nan")


def draws(members: list[int], B: int, rng) -> tuple[np.ndarray, list[np.ndarray]]:
    """B slumpmängder ur trakten (30 km), med samma fördelning på stilgrupp som gruppen."""
    centre = xy[members].mean(axis=0)
    dist = np.hypot(*(xy - centre).T)
    mset = set(members)
    pool = np.array([i for i in np.where(dist <= RADIUS_KM)[0] if i not in mset])
    need = Counter(style[i] for i in members)
    by = {s_: pool[style[pool] == s_] for s_ in need}
    out = []
    for _ in range(B):
        pick = []
        for s_, k in need.items():
            c = by[s_]
            if len(c) >= k:
                pick.extend(rng.choice(c, size=k, replace=False))
            else:
                pick.extend(c)
        short = len(members) - len(pick)
        if short:  # too few of a style group: random stones from the rest of the area, as the plan says
            rest = np.setdiff1d(pool, np.array(pick, dtype=int))
            pick.extend(rng.choice(rest, size=min(short, len(rest)), replace=False))
        out.append(np.array(pick, dtype=int))
    return pool, out


def compare(members: list[int], B: int, rng, kinds=("rock", "height", "names", "rare")) -> dict:
    _, ds = draws(members, B, rng)
    g = np.array(members)
    res = {}
    for k in kinds:
        o = stat(MATS[k], g)
        v = np.array([stat(MATS[k], x) for x in ds])
        v = v[~np.isnan(v)]
        if math.isnan(o) or not len(v):
            res[k] = {"tested": False}
            continue
        sim = -v if k in LOWER_IS_SIMILAR else v
        so = -o if k in LOWER_IS_SIMILAR else o
        pct = (np.sum(sim < so) + 0.5 * np.sum(sim == so)) / len(sim)  # share of draws less alike than the group
        p = (1 + np.sum(sim >= so)) / (1 + len(sim))
        res[k] = {"tested": True, "obs": o, "null_mean": float(v.mean()), "pct": float(pct), "p": float(p)}
    return res


def span(members) -> float:
    m = mid[members]
    m = m[~np.isnan(m)]
    return float(m.max() - m.min()) if len(m) >= MIN_DATA else float("nan")


rng = np.random.default_rng(SEED)
grp = list(csv.DictReader(open(os.path.join(OUT, "mastare_grupper.csv"), encoding="utf-8")))
mem = defaultdict(list)
for m in csv.DictReader(open(os.path.join(OUT, "mastare_medlemmar.csv"), encoding="utf-8")):
    mem[m["group"]].append(idx[m["signum"]])

# --- step 2: the traits for every group (199 draws) ---
feat = []
for n_, g in enumerate(grp):
    ms = mem[g["group"]]
    c = compare(ms, B_MODEL, rng)
    feat.append({"group": g["group"], "span": span(ms),
                 **{f"pct_{k}": (c[k]["pct"] if c[k]["tested"] else "") for k in ("rock", "names", "rare")}})
    if n_ % 100 == 0:
        print("grupp", n_, flush=True)
with open(os.path.join(OUT, "mastare_drag.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(feat[0]))
    w.writeheader()
    w.writerows(feat)

# --- part 1: time ---
carv = defaultdict(list)
for i, r in enumerate(rows):
    if r["carver"]:
        carv[r["carver"]].append(i)
carver_spans = [(len([i for i in ms if not np.isnan(mid[i])]), span(ms)) for ms in carv.values()]
cands = [g for g in grp if g["kind"] == "kandidat"]
NAME = {"2": "Konungsund", "5": "Vetlanda", "6": "Kölaby", "12": "Leksberg", "13": "Husaby"}


def coverage(members) -> float | None:
    centre = xy[members].mean(axis=0)
    dist = np.hypot(*(xy - centre).T)
    styles = {style[i] for i in members if style[i]}
    same = [i for i in np.where(dist <= RADIUS_KM)[0] if style[i] in styles]
    return len(set(same) & set(members)) / len(same) if same else None


part1 = {}
for g in cands:
    ms = mem[g["group"]]
    k = int(np.sum(~np.isnan(mid[ms])))
    s_ = span(ms)
    ref = [sp for n, sp in carver_spans if n >= k and not math.isnan(sp)]
    if math.isnan(s_) or not ref:
        part1[NAME[g["candidate"]]] = {"n_styled": k, "verdict": "går inte att bedöma"}
        continue
    p90 = float(np.percentile(ref, 90))
    part1[NAME[g["candidate"]]] = {
        "n_styled": k, "span": s_, "styles": dict(Counter(style[i] or "ingen" for i in ms)),
        "n_ref_carvers": len(ref), "ref_p90": p90, "percentile": float(np.mean(np.array(ref) <= s_)),
        "verdict": "förenligt" if s_ <= p90 else "längre än de flesta ristares", "coverage": coverage(ms)}
ctrl_cov = [c for c in (coverage(ms) for name, ms in carv.items()
                        if len(ms) >= 5 and prov[ms[0]] in ("U", "Sö")) if c is not None]
part1["_kända_ristare_U_Sö"] = {"coverage_median": float(np.median(ctrl_cov)),
                                "coverage_p90": float(np.percentile(ctrl_cov, 90)), "n": len(ctrl_cov)}

# --- part 2: H5 rare spellings (9 999 draws), positive control first ---
rng2 = np.random.default_rng(SEED + 1)
control = []
for name, ms in sorted(carv.items()):
    ms = [i for i in ms if prov[i] in ("U", "Sö")]
    if len(ms) < 5:
        continue
    control.append({"carver": name, **compare(ms, B_TEST, rng2, kinds=("rare",))["rare"]})


def fisher(ps):
    ps = [p for p in ps if p is not None]
    return {"k": len(ps), "p": float(chi2.sf(-2 * sum(math.log(p) for p in ps), 2 * len(ps)))} if ps else {"k": 0, "p": None}


ctrl = fisher([c["p"] for c in control if c.get("tested")])
cand_res = []
for g in cands:
    ms = mem[g["group"]]
    r = compare(ms, B_TEST, rng2, kinds=("rare",))["rare"]
    shared = Counter(x for i in ms for x in rare[i])
    cand_res.append({"group": NAME[g["candidate"]], **r, "n_with_spellings": int(np.sum(HAS_SP[ms])),
                     "shared_rare": {k: v for k, v in shared.most_common() if v >= 2}})
h5 = fisher([c["p"] for c in cand_res if c.get("tested")])
part2 = {"control": {"n": len(control), **ctrl,
                     "share_p05": float(np.mean([c["p"] < 0.05 for c in control if c.get("tested")]))},
         "candidates": cand_res, "H5": h5,
         "verdict": ("inte informativt" if (ctrl["p"] or 1) >= 0.05 else
                     "håller" if (h5["p"] or 1) < 0.05 else "faller")}
json.dump({"part1": part1, "part2": part2}, open(os.path.join(OUT, "mastare_del12.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=float)
print(json.dumps({"part1": part1, "H5": h5, "control": part2["control"], "verdict": part2["verdict"]},
                 ensure_ascii=False, default=float))
