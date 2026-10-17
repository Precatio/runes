"""Kalibrering av alla förslag i en lucka på en gång (2026-10-17, textmodel-17). Förut kalibrerades bara förstavalet
(gap_recal), och alternativen fick högst sin råa sannolikhet. Då kunde två nästan lika förslag byta plats beroende på
vilket som råkade stå först (Sö 206: Guðlaug 41 % rått, Gíslaug 29 %, efter kalibreringen 10 mot 29).

Här får varje förslag i luckan en poäng ur sin ordklass och sin råa sannolikhet, med samma lutning inom klassen, och
förstavalet en konstant per klass (det valdes för att det fick högst sannolikhet, och den sannolikheten är därför för hög):
    u_i = a_klass + b_klass · log p_i + r_klass · [i är förstavalet]
och "inget av förslagen" en poäng ur luckan som helhet:
    u_0 = c + d · log(förlorade runor) + e · helt ord + f · log(1 − största p) + källans konstant
P(förslag i) = exp(u_i) / (exp(u_0) + Σ exp(u_j)). Klasserna är formelord, andra ord, kända namn och namn som modellen
satt ihop (src/textmodel.gap_class). Inom en klass kan ordningen aldrig vända; mellan klasser kan den, när ett ord av en
klass där modellen ofta har fel står först. Varianterna prövades korsvaliderat (utdata/runlm_forfining/lista_varianter.py):
log(1 − största p) i stället för log(största p) och konstanten för förstavalet behövdes; en term för avståndet till
tvåan tillförde inget.
Skattas med största sannolikhet (scipy) på tre slags luckor: utgivarnas (scripts/runlm_gaps.py), dokumenterade
(scripts/runlm_documented_test.py, runor i [ ]) och maskerade (scripts/runlm_restore_test.py). Appen använder de
dokumenterade luckornas nivå. Korsvalidering med hela stenar utanför (crc32 mod 5), jämförd med dagens regel. Det svåra
maskeringsprovet (--hard) ingår inte och prövas för sig. Med --write skrivs koefficienterna till
data/runlm_calibration.json under gap_list.
    .venv/bin/python -m scripts.runlm_list_calibrate [--write]"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import zlib

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.runlm_gap_calibrate import CAL, top_words  # noqa: E402
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "utdata", "runlm_forfining")
KC = 4      # word classes
KMAX = 6    # candidates per gap
SOURCES = ("restored", "documented", "masked")
recs = {r["signum"]: r for r in rl.load_rundata()}
TOP, NAMES = top_words(recs.values()), tm.name_keys(recs.values())


def gap(cands, n_lost, whole, source, sig, kind):
    """One gap: cands [(word, raw p, right)], best first."""
    cands = [(w, p, ok) for w, p, ok in cands if w and w != "<unk>" and p > 0][:KMAX]
    return {"cands": cands, "lost": n_lost, "whole": whole, "source": source, "sig": sig, "kind": kind,
            "fold": zlib.crc32(sig.encode()) % 5}


def load(hard=False):
    gaps = []
    if not hard:
        def interpreted(sig):
            n = re.sub(r"<[^>]*>", " ", recs[sig].get("normalization") or "") if sig in recs else ""
            return sum(1 for _, p in rl.sections(n) for w in rl.norm_words(p) if not w.startswith("...")) >= 2
        for x in json.load(open(os.path.join(F, "klass3_alla.json")))["rows"]:
            if not (interpreted(x["sig"]) and x["status"] == "återställt" and x["word"] and x["word"] != "<unk>"):
                continue
            ok = lambda w: rl.same_word(w.lstrip("§"), x["rundata"])  # noqa: E731
            cands = [(x["word"], x["p"], bool(x["agrees"]) or ok(x["word"]))] + [(w, p, ok(w)) for w, p in x["alts"]]
            gaps.append(gap(cands, len(x["fill"]), False, "restored", x["sig"], rl.object_kind(recs[x["sig"]])))
        for k in range(5):
            for x in json.load(open(os.path.join(F, f"dok_alts_f{k}.json")))["rows"]:
                if x["gold_word"] and x.get("alts"):
                    gaps.append(gap([(w, p, ok) for (w, p), ok in zip(x["alts"], x["alts_ok"])], x["lost"], False,
                                    "documented", x["sig"], x["kind"]))
    for k in range(5):
        path = os.path.join(F, f"{'svart4' if hard else 'mask4'}_f{k}.json")
        if not os.path.exists(path):
            print("saknas:", os.path.relpath(path, ROOT))
            continue
        for x in json.load(open(path))["rows"]:
            if x.get("words"):
                gaps.append(gap([tuple(c) for c in x["words"]], x["n"], x["kind"] == "helt ord", "masked", x["sig"],
                                rl.object_kind(recs[x["sig"]])))
    return [g for g in gaps if g["cands"]]


def arrays(gaps):
    n = len(gaps)
    cls = np.zeros((n, KMAX), int)
    lp = np.zeros((n, KMAX))
    mask = np.zeros((n, KMAX), bool)
    right = np.zeros((n, KMAX), bool)
    z = np.zeros((n, 6))  # none: constant, log lost, whole, log(1 − max p), masked, documented
    for i, g in enumerate(gaps):
        for j, (w, p, ok) in enumerate(g["cands"]):
            cls[i, j] = tm.gap_class(w, TOP, NAMES, composed=True)
            lp[i, j] = math.log(max(p, 1e-9))
            mask[i, j] = True
            right[i, j] = bool(ok)
        z[i] = [1.0, math.log(max(1, g["lost"])), float(g["whole"]), math.log(max(1 - g["cands"][0][1], 1e-6)),
                float(g["source"] == "masked"), float(g["source"] == "documented")]
    return cls, lp, mask, right, z


NPAR = 3 * KC + 6  # class constants, class slopes, none (6), first-choice constants per class


def probs(theta, cls, lp, mask, z):
    """P(each candidate) and P(none) for every gap."""
    a, b, c, r = theta[:KC], theta[KC:2 * KC], theta[2 * KC:2 * KC + 6], theta[2 * KC + 6:]
    u = a[cls] + b[cls] * lp
    u[:, 0] += r[cls[:, 0]]
    u = np.where(mask, u, -np.inf)
    u0 = z @ c
    m = np.maximum(u.max(axis=1), u0)
    e = np.exp(u - m[:, None])
    e0 = np.exp(u0 - m)
    tot = e.sum(axis=1) + e0
    return e / tot[:, None], e0 / tot


def nll(theta, cls, lp, mask, right, z, l2=0.5):
    p, p0 = probs(theta, cls, lp, mask, z)
    any_right = right.any(axis=1)
    lik = np.where(any_right, (p * right).sum(axis=1), p0)
    return -np.sum(np.log(np.clip(lik, 1e-12, None))) + 0.05 * np.sum(theta ** 2)


def fit(gaps):
    A = arrays(gaps)
    x0 = np.zeros(NPAR)
    x0[KC:2 * KC] = 1.0
    res = minimize(nll, x0, args=A, method="L-BFGS-B")
    return res.x


def at_documented(z):
    """The app reads its gaps at the documented level."""
    z = z.copy()
    z[:, 4], z[:, 5] = 0.0, 1.0
    return z


def evaluate(gaps, P, label):
    """The chosen word (highest calibrated probability): how often right, ECE and the gaps at ≥ 95 %."""
    q = np.array([max(pp) for pp in P])
    y = np.array([float(g["cands"][int(np.argmax(pp))][2]) for g, pp in zip(gaps, P)])
    top = np.array([float(g["cands"][0][2]) for g in gaps])
    bins = ((0, .5), (.5, .8), (.8, .95), (.95, 1.01))
    ece = sum(abs(q[m].mean() - y[m].mean()) * m.sum() for lo, hi in bins for m in [(q >= lo) & (q < hi)] if m.any()) / len(y)
    sure = q >= 0.95
    return {"label": label, "n": len(gaps), "first_choice_right": float(top.mean()), "chosen_right": float(y.mean()),
            "ece": float(ece), "sure_n": int(sure.sum()), "sure_right": float(y[sure].mean()) if sure.any() else None,
            "bins": [(round(float(q[m].mean()), 3), round(float(y[m].mean()), 3), int(m.sum())) for lo, hi in bins
                     for m in [(q >= lo) & (q < hi)] if m.any()]}


def current_rule(g):
    """textmodel-16: the first choice by gap_recal, the others at most their raw probability."""
    G = tm._records()["G"]
    (w0, p0, _) = g["cands"][0]
    if p0 >= 1:
        return [p for _, p, _ in g["cands"]]
    c0 = tm.calibrate_gap(p0, w0, g["lost"], G, g["whole"])
    s = min(1.0, (1 - c0) / (1 - p0))
    return [c0] + [p * s for _, p, _ in g["cands"][1:]]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    gaps = load()
    hard = load(hard=True)
    folds = np.array([g["fold"] for g in gaps])
    A = arrays(gaps)
    cv = [None] * len(gaps)
    for k in range(5):
        th = fit([g for g, f in zip(gaps, folds) if f != k])
        idx = np.where(folds == k)[0]
        sub = [a[idx] for a in A]
        p, _ = probs(th, sub[0], sub[1], sub[2], at_documented(sub[4]))
        for i, row in zip(idx, p):
            cv[i] = row[:len(gaps[i]["cands"])]
    theta = fit(gaps)
    Ah = arrays(hard)
    ph, _ = probs(theta, Ah[0], Ah[1], Ah[2], at_documented(Ah[4]))
    hard_P = [row[:len(g["cands"])] for g, row in zip(hard, ph)]
    out = {"theta": [round(float(v), 5) for v in theta], "classes": KC, "kmax": KMAX, "n": len(gaps), "report": []}
    for src in SOURCES:
        for sub_label, sel in (("runstenar", lambda g: g["kind"] == "runsten"),):
            for wh in ((False, True) if src == "masked" else (False,)):
                ix = [i for i, g in enumerate(gaps) if g["source"] == src and sel(g) and g["whole"] == wh]
                gs = [gaps[i] for i in ix]
                lab = f"{src}{' helt ord' if wh else ''} | {sub_label}"
                new = evaluate(gs, [cv[i] for i in ix], lab + " | ny (KV)")
                old = evaluate(gs, [current_rule(g) for g in gs], lab + " | textmodel-16")
                out["report"] += [old, new]
    for wh in (False, True):
        ix = [i for i, g in enumerate(hard) if g["kind"] == "runsten" and g["whole"] == wh]
        gs = [hard[i] for i in ix]
        lab = f"svår maskering{' helt ord' if wh else ''} | runstenar (ingick inte)"
        out["report"] += [evaluate(gs, [current_rule(g) for g in gs], lab + " | textmodel-16"),
                          evaluate(gs, [hard_P[i] for i in ix], lab + " | ny")]
    for r in out["report"]:
        print(f"{r['label']:70} n {r['n']:4}  förstaval {r['first_choice_right']:.3f}  valt {r['chosen_right']:.3f}  "
              f"ECE {r['ece']:.3f}  ≥95 %: {r['sure_n']} rätt {r['sure_right'] if r['sure_right'] is None else round(r['sure_right'], 3)}")
    if "--write" in argv:
        cal = json.load(open(CAL)) if os.path.exists(CAL) else {}
        cal["gap_list"] = {**out, "top50": sorted(TOP), "note": "Alla förslag i en lucka kalibrerade tillsammans (scripts/runlm_list_calibrate.py), "
                                                               "på de dokumenterade luckornas nivå."}
        json.dump(cal, open(CAL, "w"), ensure_ascii=False, indent=1)
        print("skrivet till", CAL)
    return out


if __name__ == "__main__":
    main()
