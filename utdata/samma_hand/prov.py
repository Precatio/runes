"""Ser ristarmodellen samma hand som runologerna? (analysplaner/2026-11-08-samma-hand-runor.md, sha 32257107)
Runor 2020:s "samma som gjort X" mot ristarmodellen K0 (korpus 510ebfb3), med grannstenar på samma avstånd som kontroll.
Skriver resultat.json och resultat.md.
    .venv/bin/python utdata/samma_hand/prov.py"""
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
C = os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229")
NDRAW = 999
rng = np.random.default_rng(2026)
SAME = re.compile(r"^(Samma som|Samma ristare som|Troligen samma|Antagligen samma|Förmodligen samma|Eventuellt samma)", re.I)
PREFIX = re.compile(r"^(U|Sö|Ög|Vg|Sm|Öl|G|Vs|Nä|Gs|Hs|M|D|Vr|Ån|J|Bo|DR|N|Sk|Bl|Hl)$")

corp = pd.read_csv(os.path.join(C, "corpus.csv"), low_memory=False)
corp = corp[corp.lat.notna()]
certain = {r.signum: r.carver for r in corp.itertuples() if isinstance(r.carver, str) and not r.carvers_uncertain}
xy = dict(zip(corp.signum, zip(*Transformer.from_crs(4326, 3006, always_xy=True).transform(corp.lon.values, corp.lat.values))))

# the model's top suggestion: out of fold for stones with a carver, else the prediction
att = json.load(open(os.path.join(C, "attribution.json"), encoding="utf-8"))
top, pcal = {}, {}
for p in att["predictions"]:
    top[p["signum"]] = p["top"]
    pcal[p["signum"]] = p.get("p_cal")
oof = pd.read_csv(os.path.join(C, "attribution_oof.csv"))
pc = [c for c in oof.columns if c.startswith(".pred_")]
oofm = oof.groupby("signum")[pc].mean()
for sig, row in oofm.iterrows():
    if sig not in top:
        top[sig] = row.idxmax()[len(".pred_"):]
        pcal[sig] = None
have = {s for s in top if s in xy}


def referenced(text: str, own_prefix: str) -> list[str]:
    """The signa named in a note: 'Samma som gjort U 1015, 1017-1024' → U 1015, U 1017 … U 1024."""
    # the stones follow "gjort" ("Samma som gjort U 1027"); a note without it names them after its last "som"
    m = re.search(r"gjort\s+(.*)$", text) or re.search(r".*\bsom\s+(.*)$", text)
    if not m:
        return []
    body = re.sub(r"ATA\s*[\d/]+", "", m.group(1)).replace(" och ", ",").rstrip(". ")
    out, prefix = [], own_prefix
    for part in [p.strip() for p in body.split(",") if p.strip()]:
        toks = part.split()
        if len(toks) >= 2 and PREFIX.match(toks[0]):
            prefix, part = toks[0], " ".join(toks[1:])
        part = part.strip()
        rg = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if rg:
            out += [f"{prefix} {k}" for k in range(int(rg.group(1)), int(rg.group(2)) + 1)]
        elif re.fullmatch(r"\d+[A-Za-z]?|Fv\d{4};\d+[A-Za-z]?", part):
            out.append(f"{prefix} {part}")
    return out


links, notes = [], {}
for f in glob.glob(os.path.join(ROOT, "data", "cache", "runor", "*.json")):
    d = json.load(open(f, encoding="utf-8"))
    sig = f"{d['signum1']} {d['signum2']}".strip()
    for cv in d.get("carver") or []:
        n = (cv.get("name") or "").strip()
        if SAME.match(n):
            notes.setdefault(sig, []).append(n)
            for o in referenced(n, d["signum1"]):
                links.append((sig, o, bool(cv.get("certainty"))))


def groups(use_links):
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b, _ in use_links:
        if a in have and b in have and a != b:
            parent[find(a)] = find(b)
    g = {}
    for s in parent:
        g.setdefault(find(s), set()).add(s)
    return [sorted(v) for v in g.values() if len(v) >= 2]


ALL = sorted(have)
P = np.array([xy[s] for s in ALL])
TOP = np.array([top[s] for s in ALL])
IDX = {s: i for i, s in enumerate(ALL)}


def agreement(grp, tol):
    pairs = [(a, b) for i, a in enumerate(grp) for b in grp[i + 1:]]
    obs = np.mean([top[a] == top[b] for a, b in pairs])
    gset = {IDX[s] for s in grp}
    ctrl_draws, missing = [], 0
    cand = []
    for a, b in pairs:
        for s, t in ((a, b), (b, a)):
            d = float(np.hypot(*(np.array(xy[s]) - np.array(xy[t]))))
            dd = np.hypot(*(P - np.array(xy[s])).T)
            lo, hi = min(d * (1 - tol), d - 1000), max(d * (1 + tol), d + 1000)
            ok = np.where((dd >= lo) & (dd <= hi))[0]
            ok = np.array([k for k in ok if k not in gset])
            if len(ok):
                cand.append((top[s], ok))
            else:
                missing += 1
    for _ in range(NDRAW):
        ctrl_draws.append(np.mean([TOP[rng.choice(ok)] == t for t, ok in cand]) if cand else np.nan)
    return float(obs), float(np.nanmean(ctrl_draws)), len(pairs), missing


def run(use_links, tol, only_unnamed):
    out = []
    for g in groups(use_links):
        unnamed = any(s not in certain for s in g)
        if only_unnamed and not unnamed:
            continue
        obs, ctrl, npairs, miss = agreement(g, tol)
        out.append({"stones": g, "obs": obs, "ctrl": ctrl, "pairs": npairs, "no_control": miss, "unnamed": unnamed,
                    "model": {s: top[s] for s in g}, "p_cal": {s: pcal.get(s) for s in g},
                    "rundata": {s: certain.get(s) for s in g}, "runor": {s: notes.get(s) for s in g if s in notes}})
    diff = [x["obs"] - x["ctrl"] for x in out if not np.isnan(x["ctrl"])]
    w = wilcoxon(diff, alternative="greater") if len(diff) >= 5 and any(diff) else None
    return out, {"groups": len(out), "median_diff": float(np.median(diff)) if diff else None,
                 "mean_obs": float(np.mean([x["obs"] for x in out])) if out else None,
                 "mean_ctrl": float(np.nanmean([x["ctrl"] for x in out])) if out else None,
                 "better": int(sum(d > 0 for d in diff)), "worse": int(sum(d < 0 for d in diff)),
                 "p": float(w.pvalue) if w else None}


grp_main, H1 = run(links, 0.25, True)
H1["holds"] = H1["p"] is not None and H1["p"] < 0.05 and H1["median_diff"] > 0
sens = {"all_groups": run(links, 0.25, False)[1], "certain_notes_only": run([l for l in links if l[2]], 0.25, True)[1],
        "control_10pct": run(links, 0.10, True)[1]}
opir = sum(1 for g in grp_main for s in g["stones"] if g["model"][s] == "Öpir 1")
nst = sum(len(g["stones"]) for g in grp_main)
res = {"plan": "analysplaner/2026-11-08-samma-hand-runor.md", "plan_sha": "32257107", "corpus": "510ebfb3",
       "runor_notes": sum(len(v) for v in notes.values()), "links": len(links), "H1": H1, "sensitivity": sens,
       "opir_share_in_groups": opir / nst if nst else None, "groups": grp_main}
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"H1": H1, "sensitivity": sens, "opir_share": res["opir_share_in_groups"]}, ensure_ascii=False, indent=1))
for g in sorted(grp_main, key=lambda x: -len(x["stones"])):
    print(f"{len(g['stones']):2} stenar  samst {g['obs']:.2f} kontroll {g['ctrl']:.2f}  | " + ", ".join(
        f"{s}:{g['model'][s]}{'*' if g['rundata'][s] else ''}" for s in g["stones"]))
