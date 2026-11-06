"""Spårläsaren blind (analysplaner/2026-11-06-sparlasare-blind.md, låst 2026-11-06): led F med parningen skanning ↔ text tagen
ur forskarens Runa för runa-klick i stället för ur en DP-parning som ser det dolda ordet.

Vägrar köra med färre än MIN_STONES facit som får användas: version 2 med kopplade runor, i utdata/facit/, inte
utvecklingsstenarna Sö 113 och Sö 128, och stenen måste klara led F:s ordkontroll (gold). Kör en sten i taget (den
tunga analysen tar några minuter och mycket minne).

    PYTHONPATH=. .venv/bin/python scripts/sparlasare_blind.py            # kontrollerar underlaget och kör
    PYTHONPATH=. .venv/bin/python scripts/sparlasare_blind.py --check    # bara kontrollen
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import sys

import numpy as np
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACIT_DIR = os.path.join(ROOT, "utdata", "facit")
OUT = os.path.join(ROOT, "utdata", "sparlasare", "blind")
PLAN = os.path.join(ROOT, "analysplaner", "2026-11-06-sparlasare-blind.md")
DEV = {"Sö 113", "Sö 128"}
MIN_STONES = 8
MIN_WORDS = 50
REACH = 1.5       # as web/src/lib/mesh.ts MARK_REACH
TRACE_EPS = 0.2   # as led F
SEED = 23         # as led F


def _led_f():
    sys.path.insert(0, os.path.join(ROOT, "utdata", "sparlasare"))
    import led_f  # noqa: E402
    return led_f


def eligible_facits(folder: str = FACIT_DIR) -> tuple[list[dict], list[str]]:
    """(the facits the test may use, one per stone, and why the others were left out)."""
    from src import rune_links
    from src.runlm import load_rundata, viking
    led_f = _led_f()
    recs = {r["signum"]: r for r in load_rundata() if viking(r) and r.get("transliteration") and r.get("normalization")}
    chosen: dict[str, dict] = {}
    notes = []
    for path in sorted(glob.glob(os.path.join(folder, "*.json"))):
        try:
            f = rune_links.read_facit(json.load(open(path, encoding="utf-8")))
        except (ValueError, json.JSONDecodeError) as e:
            notes.append(f"{os.path.basename(path)}: inte ett facit ({e})")
            continue
        sig = f.get("signum") or ""
        rec, part = rune_links.rundata_record(sig)
        sig = rec["signum"] if rec else sig
        why = (None if f["version"] >= 2 and f["rune_links"] else "inga kopplade runor (version 1)")
        why = why or ("utvecklingssten" if sig in DEV else None)
        why = why or (None if sig in recs and led_f.gold(recs[sig]) is not None else
                      "klarar inte led F:s ordkontroll (förlorade eller osäkra runor, eller ej vikingatida)")
        if why:
            notes.append(f"{os.path.basename(path)} ({sig}): {why}")
            continue
        f["_path"], f["_signum"] = path, sig
        if sig not in chosen or (f.get("created") or "") < (chosen[sig].get("created") or ""):
            chosen[sig] = f
    return list(chosen.values()), notes


def pair_links(link_xy: np.ndarray, rune_xy: np.ndarray, reach_factor: float = REACH) -> dict[int, int]:
    """{link index: detected rune index} for mutual nearest neighbours in the stone plane within reach_factor × the
    median distance between consecutive clicks. Sees neither the text nor the trace sets."""
    L, R = np.asarray(link_xy, float).reshape(-1, 2), np.asarray(rune_xy, float).reshape(-1, 2)
    if len(L) == 0 or len(R) == 0:
        return {}
    gaps = np.linalg.norm(np.diff(L, axis=0), axis=1)
    reach = reach_factor * float(np.median(gaps)) if len(gaps) else float("inf")
    d_lr, j_lr = cKDTree(R).query(L)
    _, j_rl = cKDTree(L).query(R)
    return {int(k): int(j) for k, (d, j) in enumerate(zip(d_lr, j_lr, strict=True)) if d <= reach and j_rl[j] == k}


def rune_centres(runes: list[dict], frame: dict) -> np.ndarray:
    """Each detected rune's centre in the stone plane (a, b in mm): the mean of its strokes' end points, which are
    (row, col) · grid in the analysis' grid; frame is the analysis' own image_frame (a0_mm, b0_mm)."""
    a0, b0 = float(frame["a0_mm"]), float(frame["b0_mm"])
    out = []
    for r in runes:
        pts = np.array([p for s in r["strokes_detail"] for p in (s["p0_mm"], s["p1_mm"])], float)
        row, col = pts[:, 0].mean(), pts[:, 1].mean()
        out.append((a0 + col, b0 + row))
    return np.array(out, float).reshape(-1, 2)


def scan_sets(facit: dict) -> tuple[dict[int, set], dict]:
    """{text position: expanded trace set} through the human links, and the pairing's quality."""
    from scripts.evaluate_rune_detection import find_scan, load_like_app, sha256
    from src import rune_links
    from src import trace_reader as tr
    from src.auto_grooves import analyze_grooves
    path = find_scan(facit.get("mesh") or {})
    want = (facit.get("mesh") or {}).get("sha256")
    if want and sha256(path) != want:
        raise ValueError(f"{path}: kontrollsumman stämmer inte med facitet.")
    par = facit["parameters"]
    g = analyze_grooves(load_like_app(path), par["normal"], up=par.get("up"), resolution_mm=0.6, keep_arrays=True,
                        sha256=want)
    runes = [r for r in g["runes"] if r.get("strokes_detail")]
    feats = tr.weighted_blobs(runes, g["stroke_lines"], g["arrays"])
    frame = g["image_frame"]
    f = rune_links._affine(frame)
    tokens = rune_links.token_by_index(facit)
    single = [ln for ln in facit["rune_links"]
              if len(ln["tokens"]) == 1 and (tokens.get(ln["tokens"][0]) or {}).get("pos") is not None]
    L = []
    for ln in single:
        if ln.get("point_mm") is not None:
            p = np.asarray(ln["point_mm"], float)
            L.append((float(p @ f["u"]), float(p @ f["v"])))
        else:
            L.append(rune_links.pixel_to_plane(frame, *ln["image_xy"]))
    pairs = pair_links(np.array(L), rune_centres(runes, frame))
    sets = {}
    for k, j in pairs.items():
        probs = tr.rune_probs(feats[runes[j]["id"]])
        if probs is None:  # the bind-rune guard: no proposal
            continue
        sets[tokens[single[k]["tokens"][0]]["pos"]] = tr.expand(tr.margin_set(probs))
    return sets, {"n_links": len(facit["rune_links"]), "n_single": len(single), "n_detected": len(runes),
                  "n_paired": len(pairs), "n_traced": len(sets)}


def run_stone(facit: dict, V: list[dict], ET) -> tuple[list[dict], dict]:
    """Led F's loop for one stone with the human pairing (same model, words and conditions)."""
    led_f = _led_f()
    from src.runlm import Model, decode, normtok, restore, stone_divider_rate
    signum = facit["_signum"]
    r = next(x for x in V if x["signum"] == signum)
    groups, gw = led_f.gold(r)
    pos_sets, quality = scan_sets(facit)
    rng = random.Random(SEED)
    shuffled_positions = list(pos_sets)
    rng.shuffle(shuffled_positions)
    shuf = {p: pos_sets[q] for p, q in zip(sorted(pos_sets), shuffled_positions, strict=True)}
    m = Model([x for x in V if x["signum"] != signum], edda_tokens=ET, aligned=True, lam_name=0.05)
    rows = []
    for i, j, _runes, gword in [w for w in gw if 2 <= w[1] - w[0] <= 6]:
        loc = led_f.locate(groups, i, j)
        if loc is None:
            continue
        gi, g0, g1 = loc
        truth = groups[gi][g0:g1]
        masked = list(groups)
        masked[gi] = groups[gi][:g0] + "?" * (g1 - g0) + groups[gi][g1:]
        dr = stone_divider_rate(m, masked)
        conds = {"utan": (None, 0.0), "skanner": ([pos_sets.get(p) for p in range(i, j)], TRACE_EPS),
                 "omflyttad": ([shuf.get(p) for p in range(i, j)], TRACE_EPS)}
        row = {"sig": signum, "truth": truth, "word": gword, "n": j - i}
        for lab, (allowed, eps) in conds.items():
            if lab != "utan" and not any(allowed):
                row[lab] = None
                continue
            res = restore(m, masked, (gi, g0, g1), words={}, window=2, n_cands=60, div_rate=dr, allowed=allowed,
                          trace_eps=eps)
            fills = [fl for fl, _ in res]
            word_ok = False
            if fills:
                filled = list(groups)
                filled[gi] = groups[gi][:g0] + fills[0] + groups[gi][g1:]
                _, path, _, _ = decode(m, filled, d=dr)
                at = sum(len(x) for x in groups[:gi]) + g0
                w_ = next((w for a_, b_, w, _ in path if a_ <= at < b_), None)
                word_ok = bool(w_) and w_ != "<unk>" and m.lemma(w_) == m.lemma(normtok(gword))
            row[lab] = {"top": fills[0] if fills else None, "right": fills[:1] == [truth], "word_ok": word_ok,
                        "p_truth": float(dict(res).get(truth, 0.0)), "traced": sum(1 for a in (allowed or []) if a)}
        rows.append(row)
    return rows, quality


def decide(rows: list[dict]) -> dict:
    """The plan's decision rule (punkt 3) on the pooled words."""
    from scipy import stats
    both = [x for x in rows if all(x.get(c) for c in ("utan", "skanner", "omflyttad"))]
    out = {"n_words_traced": len(both), "stones": len({x["sig"] for x in both})}
    if len(both) < MIN_WORDS:
        return {**out, "verdict": "ej avgörbart (för få ord med spår)"}
    tests = {}
    for a, b, alt in (("skanner", "utan", "greater"), ("skanner", "omflyttad", "greater"), ("omflyttad", "utan", "two-sided")):
        d = [x[a]["p_truth"] - x[b]["p_truth"] for x in both]
        nz = [v for v in d if abs(v) > 1e-9]
        tests[f"{a}_vs_{b}"] = {"mean_diff": float(np.mean(d)), "n_changed": len(nz),
                                "p": float(stats.wilcoxon(nz, alternative=alt).pvalue) if nz else 1.0, "alt": alt}
    share = {c: float(np.mean([x[c]["word_ok"] for x in both])) for c in ("utan", "skanner", "omflyttad")}
    holds = (tests["skanner_vs_utan"]["p"] < 0.05 and tests["skanner_vs_omflyttad"]["p"] < 0.05
             and share["skanner"] > share["utan"])
    verdict = ("håller: spåren hjälper också när parningen är blind" if holds else
               "mängderna hjälper men läser inte stenen" if tests["skanner_vs_utan"]["p"] < 0.05 else
               "håller inte")
    return {**out, "tests": tests, "word_ok": share, "verdict": verdict}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="kontrollera bara underlaget")
    ap.add_argument("--facit", default=FACIT_DIR)
    a = ap.parse_args(argv)
    facits, notes = eligible_facits(a.facit)
    for n in notes:
        print("utelämnad:", n)
    print(f"{len(facits)} facit får användas: {', '.join(sorted(f['_signum'] for f in facits)) or '–'}")
    if len(facits) < MIN_STONES:
        raise SystemExit(f"Provet körs inte: {len(facits)} facit, planen kräver minst {MIN_STONES} "
                         f"(inte {', '.join(sorted(DEV))}; stenen ska klara led F:s ordkontroll).")
    if not os.path.exists(PLAN.replace(".md", ".sha256")):
        raise SystemExit("Provet körs inte: analysplanen är inte låst (analysplaner/2026-11-06-sparlasare-blind.sha256).")
    if a.check:
        return
    from src.runlm import edda_tokens, load_rundata, viking
    ET = edda_tokens()
    V = [r for r in load_rundata() if viking(r) and r.get("transliteration") and r.get("normalization")
         and r["signum"] != "DR NOR1988;5"]
    os.makedirs(OUT, exist_ok=True)
    rows, quality = [], {}
    for f in sorted(facits, key=lambda x: x["_signum"]):
        print(f["_signum"], "…", flush=True)
        r, q = run_stone(f, V, ET)
        rows += r
        quality[f["_signum"]] = {**q, "facit": os.path.basename(f["_path"])}
        json.dump({"rows": rows, "quality": quality}, open(os.path.join(OUT, "rader.json"), "w"), ensure_ascii=False, indent=1)
    res = {"plan": os.path.relpath(PLAN, ROOT), "quality": quality, **decide(rows)}
    json.dump(res, open(os.path.join(OUT, "resultat.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in res if k != "quality"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
