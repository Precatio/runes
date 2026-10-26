"""Artikelns siffror uppdelade efter vad inskriften står på (2026-10-17, Viktors regel: runstenar först, andra föremål
redovisas för sig). Runstenar = Rundatas föremål "runsten", också fragment och försvunna stenar; andra stenar = gravhällar,
berghällar, block m.m.; lösa föremål = metall, ben, horn, trä m.m. Läsprovet (kalib_klass.json), maskeringsprovet
(maskklass_f*.json), de verkliga luckorna med den korsvaliderade kalibreringen (klass_alla.json) och nattkörningen
(sammanstallning.json, med utgivarnas status som i batch_status.py). Skriver runstenar.json.
    PYTHONPATH=. .venv/bin/python utdata/modellartikel/runstenar.py"""
import json
import os
import re
import sys
import zlib
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
import scripts.runlm_gap_calibrate as C  # noqa: E402
import scripts.runlm_gaps as G  # noqa: E402
from scripts.luckprov import status_of  # noqa: E402
from src import runlm as rl  # noqa: E402
from src.textmodel import gap_class, name_keys  # noqa: E402

F = os.path.join(ROOT, "utdata", "runlm_forfining")
recs = rl.load_rundata()
by = {r["signum"]: r for r in recs}
KINDS = ("runsten", "annan sten", "lösa föremål")


def kind(sig):
    r = by[sig]
    if "runsten" in (r.get("object") or "").lower():
        return "runsten"
    return "annan sten" if r.get("material_type") == "sten" else "lösa föremål"


out = {}
V = [r for r in recs if rl.viking(r) and r.get("transliteration") and r.get("normalization")]
out["viking"] = dict(Counter(kind(r["signum"]) for r in V))

# --- the reading test
kk = json.load(open(os.path.join(F, "kalib_tm14_egend.json")))  # textmodel-15: the carver's own divider rate
rd = defaultdict(lambda: {"inscriptions": set(), "words": 0, "same": 0, "span": 0})
for sig, same, span in kk["per_word"]:
    g = rd[kind(sig)]
    g["inscriptions"].add(sig); g["words"] += 1; g["same"] += bool(same); g["span"] += bool(span)
out["reading"] = {k: {"inscriptions": len(g["inscriptions"]), "words": g["words"], "same": g["same"] / g["words"], "span": g["span"] / g["words"]}
                  for k, g in rd.items()}

# --- the masking test
mk = defaultdict(lambda: [0, 0])
for f in range(5):
    for x in json.load(open(os.path.join(F, f"mask4_f{f}.json")))["rows"]:
        g = mk[(kind(x["sig"]), x["kind"])]
        g[0] += 1; g[1] += bool(x["word_ok"])
out["masking"] = {f"{k}|{t}": {"n": n, "right": r / n} for (k, t), (n, r) in mk.items()}


# --- the real gaps the editors filled, with the cross-validated calibration (as kalibrering.json, split by kind)
def interpreted(sig):
    n = re.sub(r"<[^>]*>", " ", by[sig].get("normalization") or "") if sig in by else ""
    return sum(1 for _, p in rl.sections(n) for w in rl.norm_words(p) if not w.startswith("...")) >= 2


known = lambda x: bool(x["word"]) and x["word"] != "<unk>"  # noqa: E731
agree = lambda x: bool(x["agrees"]) or rl.same_word(x["word"].lstrip("§"), x["rundata"])  # noqa: E731
rest = [x for x in json.load(open(os.path.join(F, "klass3_alla.json")))["rows"] if interpreted(x["sig"]) and x["status"] == "återställt"]
val = [x for x in rest if known(x)]
top, names = C.top_words(recs), name_keys(recs)
# textmodel-15: the calibration the app uses (scripts/runlm_gap_calibrate.py, restored + documented + masked gaps,
# at the documented level), cross-validated: each restored gap gets its percentage from a fit without its stone
X = np.array([C.features(x["p"], gap_class(x["word"], top, names, True), len(x["fill"]), 4, False) for x in val])
y = np.array([1.0 if agree(x) else 0.0 for x in val])
fold = np.array([zlib.crc32(x["sig"].encode()) % 5 for x in val])
X1, y1, s1, _ = C.documented_rows(os.path.join(F, "dok_egend"), top, names, 4, whole=True)
X2, y2, s2, _, _ = C.masked_rows(os.path.join(F, "mask3"), top, names, by, 4)
f1 = np.array([zlib.crc32(s_.encode()) % 5 for s_ in s1])
f2 = np.array([zlib.crc32(s_.encode()) % 5 for s_ in s2])
src = lambda n, a, b: np.hstack([np.full((n, 1), a), np.full((n, 1), b)])  # noqa: E731
XA = np.vstack([np.hstack([X, src(len(X), 0, 0)]), np.hstack([X1, src(len(X1), 0, 1)]), np.hstack([X2, src(len(X2), 1, 0)])])
yA, fA = np.concatenate([y, y1, y2]), np.concatenate([fold, f1, f2])
q = np.zeros(len(y))
for k in range(5):
    w = C.fit(XA[fA != k], yA[fA != k])
    q[fold == k] = 1 / (1 + np.exp(-(np.hstack([X[fold == k], src(int((fold == k).sum()), 0, 1)]) @ w)))
ks = np.array([kind(x["sig"]) for x in val])
acls = [gap_class(re.sub(r"[\[\]\"(){}.,?…]", "", x["rundata"]), top, names) for x in val]
gaps = {}
for k in KINDS:
    m = ks == k
    bins = []
    for lo, hi in ((0, .5), (.5, .8), (.8, .95), (.95, 1.01)):
        b = m & (q >= lo) & (q < hi)
        bins.append({"lo": lo, "hi": hi, "n": int(b.sum()), "said": float(q[b].mean()) if b.any() else None, "right": float(y[b].mean()) if b.any() else None})
    cls = {c: {"n": int(sum(1 for i in range(len(val)) if m[i] and acls[i] == c)),
               "right": float(np.mean([y[i] for i in range(len(val)) if m[i] and acls[i] == c])) if any(m[i] and acls[i] == c for i in range(len(val))) else None}
           for c in (0, 1, 2)}
    gaps[k] = {"restored": sum(1 for x in rest if kind(x["sig"]) == k), "stones": len({x["sig"] for x in rest if kind(x["sig"]) == k}),
               "known": int(m.sum()), "right": float(y[m].mean()), "bins": bins, "by_class": cls}
out["gaps"] = gaps
out["documented"] = json.load(open(os.path.join(F, "dok_bins.json")))  # utdata/runlm_forfining/dok_bins.py

# --- the night run over all inscriptions with gaps, and what the editors did with each gap
S = json.load(open(os.path.join(ROOT, "utdata", "textmodel_batch", "sammanstallning.json")))
rec = {r["signum"]: r for r in G.SW}
idx = defaultdict(list)
for sig, r in rec.items():
    for groups, gap, w_, tok in G.gaps_of(r):
        idx[(sig, groups[gap[0]])].append((gap[1], gap[2], tok))


def band(x):
    if not x["word"] or x["word"] == "<unk>":
        return "inget förslag"
    p = x["p"]
    return "≥95" if p >= 0.95 else "80–95" if p >= 0.8 else "50–80" if p >= 0.5 else "<50"


batch = {}
for k in KINDS:
    rows = [x for x in S["rows"] if kind(x["signum"]) == k]
    st = defaultdict(Counter)
    for x in rows:
        m_ = [t for a, b, t in idx.get((x["signum"], x["carved"]), []) if a < x["end"] and x["start"] < b]
        s_ = status_of(m_[0]) if m_ else ("utanför provet" if x["signum"] in rec else "ej svensk")
        st[s_][band(x)] += 1
    batch[k] = {"inscriptions": len({x["signum"] for x in rows}), "gaps": len(rows), "too_few": sum(1 for s in S["missing"] if kind(s) == k),
                "bands": dict(Counter(map(band, rows))), "boundaries": sum(x["boundary"] for x in rows),
                "status": {s_: dict(c) for s_, c in st.items()}}
out["batch"] = batch
json.dump(out, open(os.path.join(HERE, "runstenar.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "gaps"}, ensure_ascii=False, indent=1)[:3500])
print(json.dumps(out["gaps"]["runsten"], ensure_ascii=False, indent=1))
