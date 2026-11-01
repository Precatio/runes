"""Maltstenen mot besvärjelser (låst plan analysplaner/2026-11-01-malt-besvarjelser.md, sha 44d8fa9f).
Del A: formen i avsnitt om 24 runor, minnesstenar mot besvärjelser (logistisk regression, AUC), tillämpad på Malt.
Del B: liknar Malts grupper de ord tolkningarna läser in (dvärg, Billing, Tyr, ut) mer än andra runstenars grupper, och
hur ofta når 50 slumpvisa kontrollord samma nivå? Inga läsningar av Malt. Skriver besvarjelser.json.
    PYTHONPATH=. .venv/bin/python utdata/Malt/besvarjelser.py"""
import ast
import json
import os
import random
import re
import sys
import zlib

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from src import runlm as rl  # noqa: E402
import scripts.runlm_sprakprov as S  # noqa: E402
from runrad_dubblering import stretches  # noqa: E402

# malt_stream, stream and the constants from upprepning.py (which runs its analysis on import)
_src = open(os.path.join(HERE, "upprepning.py")).read()
_ns = {"re": re, "rl": rl}
for node in ast.parse(_src).body:
    if (isinstance(node, ast.FunctionDef) and node.name in ("malt_stream", "stream", "n_runes")) or \
            (isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") in ("BEST",)):
        exec(compile(ast.Module([node], []), "upprepning.py", "exec"), _ns)
malt_stream, old_stream, n_runes, BEST = _ns["malt_stream"], _ns["stream"], _ns["n_runes"], _ns["BEST"]

MALT = "DR NOR1988;5"
W = 24
OBJ = re.compile(r"amulett|bleck", re.I)
NOTE = re.compile(r"besvärj|magisk|trollformel|amulett", re.I)
LEX = re.compile(r"þurs|galdr|agla|sárþvara|sarþvara|gyrill|þistil|dværg|dverg|\bværki\b", re.I)
VOW = set("aeiouyæø")
rows = rl.load_rundata()
by = {r["signum"]: r for r in rows}


def period(r):
    return "V" if rl.viking(r) else "M" if (r.get("period") or "").startswith("M") else "övr"


def is_charm(r):
    return rl.object_kind(r) != "runsten" and bool(OBJ.search(r.get("object") or "") or NOTE.search(r.get("other") or "")
                                                   or LEX.search(r.get("normalization") or ""))


def windows(st):
    """Consecutive 24-rune windows inside unbroken stretches: lists of (rune, group id)."""
    out = []
    for s in st:
        seq = [(ch, gi) for gi, g in enumerate(s) for ch in g]
        for i in range(0, len(seq) - W + 1, W):
            out.append(seq[i:i + W])
    return out


def bits(lm, t):
    """S.bits_per_rune with each rune's surprise capped at 20 bits: runes the model never saw (Latin letters on medieval
    amulets) otherwise give infinity. Deviation from the plan, decided after the first run stopped on it."""
    O = S.ORDER
    ss = ["<s>"] * (O - 1) + list(t) + ["</s>"]
    return sum(min(20.0, -lm.logscore(ss[i], ss[i - O + 1:i])) for i in range(O - 1, len(ss))) / (len(ss) - O + 1)


def feats(win, lm):
    t = "".join(c for c, _ in win)
    gids = [g for _, g in win]
    grams = [t[i:i + 3] for i in range(len(t) - 2)]
    rep = sum(grams.count(x) >= 2 for x in grams) / len(grams)
    inner = [g for g in set(gids) if g != gids[0] and g != gids[-1]]
    short = sum(1 for g in inner if gids.count(g) <= 2) / len(inner) if inner else 0.0
    return [bits(lm, t), S.coincidence(t), sum(c in VOW for c in t) / len(t), rep,
            float(bool(re.search(r"(.)\1\1", t))), sum(a != b for a, b in zip(gids, gids[1:])) / len(t), short]


NAMES = ["bitar_per_runa", "koincidens", "vokaler", "upprepning3", "trippelruna", "skiljetecken", "korta_grupper"]

# ---- the sets ---------------------------------------------------------------------------------------------------------
mem, charm_v, charm_m = [], [], []
for r in rows:
    if r["signum"] == MALT:
        continue
    st = stretches(r.get("transliteration"))
    if n_runes(st) < W:
        continue
    p = period(r)
    if p == "V" and rl.object_kind(r) == "runsten":
        mem.append((r["signum"], st))
    elif is_charm(r) and p in ("V", "M"):
        (charm_v if p == "V" else charm_m).append((r["signum"], st))
res = {"plan": "analysplaner/2026-11-01-malt-besvarjelser.md", "plan_sha": "44d8fa9f",
       "n": {"memorial": len(mem), "charm_viking": len(charm_v), "charm_medieval": len(charm_m)},
       "charm_viking": [s for s, _ in charm_v]}

# language model: 5 folds over the runestones; full model for everything else
fold = {s: zlib.crc32(s.encode()) % 5 for s, _ in mem}
segs = {s: ["".join(x) for x in st] for s, st in mem}
lm_fold = [S.train([g for s, gs in segs.items() if fold[s] != k for g in gs]) for k in range(5)]
lm_all = S.train([g for gs in segs.values() for g in gs])


def table(items, lm_of):
    X, grp = [], []
    for s, st in items:
        for w in windows(st):
            X.append(feats(w, lm_of(s)))
            grp.append(s)
    return np.array(X), grp


Xm, gm = table(mem, lambda s: lm_fold[fold[s]])
Xv, gv = table(charm_v, lambda s: lm_all)
Xmed, gmed = table(charm_m, lambda s: lm_all)
Xmalt = np.array([feats(w, lm_all) for w in windows(malt_stream(BEST))])
assert len(Xmalt) == 5


def model(Xa, ga, Xb, gb, cols, malt_rows=None):
    X = np.vstack([Xa[:, cols], Xb[:, cols]])
    y = np.r_[np.zeros(len(Xa)), np.ones(len(Xb))]
    g = np.array(ga + gb)
    pred = np.zeros(len(y))
    for tr, te in GroupKFold(5).split(X, y, g):
        sc = StandardScaler().fit(X[tr])
        m = LogisticRegression(class_weight="balanced", max_iter=2000).fit(sc.transform(X[tr]), y[tr])
        pred[te] = m.predict_proba(sc.transform(X[te]))[:, 1]
    sc = StandardScaler().fit(X)
    m = LogisticRegression(class_weight="balanced", max_iter=2000).fit(sc.transform(X), y)
    pm = m.predict_proba(sc.transform(Xmalt[:, cols]))[:, 1]
    auc = roc_auc_score(y, pred)
    return {"auc": float(auc), "n_windows": [int(len(Xa)), int(len(Xb))], "malt_windows": [float(x) for x in pm],
            "malt_mean": float(pm.mean()), "coef": dict(zip([NAMES[c] for c in cols], [float(x) for x in m.coef_[0]])),
            "verdict": ("ingen slutsats (AUC < 0,75)" if auc < 0.75 else
                        "liknar besvärjelser" if pm.mean() > 0.5 else "liknar minnesstenar")}


ALL = list(range(7))
NO_LM = list(range(1, 7))
res["A"] = {"main": model(Xm, gm, Xv, gv, ALL), "medieval": model(Xm, gm, Xmed, gmed, ALL),
            "no_lm": model(Xm, gm, Xv, gv, NO_LM)}
dk = [i for i, s in enumerate(gm) if s.startswith("DR")]
res["A"]["danish_memorial"] = model(Xm[dk], [gm[i] for i in dk], Xv, gv, ALL)
# descriptive: feature means and distances
sc = StandardScaler().fit(np.vstack([Xm, Xv]))
Z = lambda X: sc.transform(X).mean(0)  # noqa: E731
ref = {"malt": Xmalt, "memorial": Xm, "charm_viking": Xv, "charm_medieval": Xmed}
for s in ("DR EM85;371B", "DR EM85;151B", "DR 239"):
    st = stretches(by[s]["transliteration"])
    ws = windows(st)
    if ws:
        ref[s] = np.array([feats(w, lm_fold[fold[s]] if s in fold else lm_all) for w in ws])
res["A"]["means"] = {k: dict(zip(NAMES, [float(x) for x in v.mean(0)])) for k, v in ref.items()}
res["A"]["dist_from_malt"] = {k: float(np.linalg.norm(Z(v) - Z(Xmalt))) for k, v in ref.items() if k != "malt"}

# ---- Del B ------------------------------------------------------------------------------------------------------------
forms = set()
for r in rows:
    for _, p in rl.sections(r.get("normalization") or ""):
        for w in rl.norm_words(p):
            w = w.lower().strip('"').strip()
            if re.fullmatch(r"[a-zþðæøǫáéíóúýœ]+", w):
                forms.add(w)
TARGET = {"dvärg": [f for f in forms if f.startswith(("dværg", "dverg"))],
          "Billing": [f for f in forms if f.startswith(("billing", "billi"))],
          "Tyr": [f for f in forms if f in ("týr", "tyr")],
          "ut": [f for f in forms if f in ("út", "ut")]}
rng = random.Random(2026)
pool = sorted(f for f in forms if 3 <= len(f) <= 8 and not any(f in v for v in TARGET.values()))
CONTROL = rng.sample(pool, 50)


def groups(st):
    return [g for s in st for g in s]


comp = []
for r in rows:
    if r["signum"] == MALT or not rl.viking(r) or rl.object_kind(r) != "runsten":
        continue
    st = old_stream(r.get("transliteration"))
    if 91 <= n_runes(st) <= 204:
        comp.append(groups(st))
assert len(comp) == 163
malt_g = groups(malt_stream(BEST))


def Sval(gs, fs):
    return max((rl.similarity(g, f) for g in gs for f in fs), default=0.0)


def test(fs):
    xs = np.array([Sval(gs, fs) for gs in comp])
    m = Sval(malt_g, fs)
    best = max(((g, f) for g in malt_g for f in fs), key=lambda x: rl.similarity(*x)) if fs else None
    return {"forms": sorted(fs)[:20], "n_forms": len(fs), "malt": m, "p95": float(np.percentile(xs, 95)),
            "percentile": float((xs < m).mean()), "above_p95": bool(m > np.percentile(xs, 95)), "best_pair": best}


res["B"] = {"targets": {k: test(v) for k, v in TARGET.items()}}
ctl = {w: test([w]) for w in CONTROL}
res["B"]["controls_above"] = sum(v["above_p95"] for v in ctl.values())
res["B"]["controls"] = {w: {k: v[k] for k in ("malt", "p95", "above_p95", "best_pair")} for w, v in ctl.items()}
res["B"]["discriminates"] = res["B"]["controls_above"] <= 10
json.dump(res, open(os.path.join(HERE, "besvarjelser.json"), "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({"n": res["n"], "charm_viking": res["charm_viking"]}, ensure_ascii=False))
for k in ("main", "medieval", "no_lm", "danish_memorial"):
    a = res["A"][k]
    print(k, "AUC", round(a["auc"], 3), "fönster", a["n_windows"], "Malt", [round(x, 2) for x in a["malt_windows"]], "medel", round(a["malt_mean"], 3), "→", a["verdict"])
print("koef", {k: round(v, 2) for k, v in res["A"]["main"]["coef"].items()})
for k, v in res["A"]["means"].items():
    print("medel", k, {a: round(b, 3) for a, b in v.items()})
print("avstånd", {k: round(v, 2) for k, v in res["A"]["dist_from_malt"].items()})
for k, v in res["B"]["targets"].items():
    print("B", k, v["n_forms"], v["forms"][:8], "Malt", round(v["malt"], 3), "p95", round(v["p95"], 3), "pct", round(v["percentile"], 3), v["above_p95"], v["best_pair"])
print("kontrollord över gränsen:", res["B"]["controls_above"], "av 50 →", "skiljer" if res["B"]["discriminates"] else "skiljer inte")
