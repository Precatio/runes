"""Spårläsaren, led E (2026-10-17): sannolikhetsvikter i stället för hårda trösklar. Led D visade att huggdjupet
skiljer äkta bistavar från brus, men en hård tröskel kastar information: en blobb på gränsen är varken säkert brus
eller säkert bistav. Här får varje blobb en vikt w ∈ (0,1) ur djupkvot (mot sin stav), avlånghet och längd. Mallkostnaden
räknar med vikterna – att avfärda en blobb som brus kostar w, inte 1 – och varje mallplats kostar ett litet pris (PRIOR)
så att runor med många bistavar (b, f, r) inte blir billiga soptunnor för brus. Kostnaderna blir 16-vägslikelihooder
P(runa) = softmax(−kostnad/TAU) med golv, precis den form sannolikhetsmodellens mjuka spår (restore allowed=) vill ha.
Utvärdering som förut: radordning + parning mot translittereringen, omkastad text som slumpkontroll; nu mäts medel-P för
facitrunan, topp-1 och topp-3. Blobbarna cachas per sten (den tunga djupbilden räknas en gång).
    cd aagaard-research && PYTHONPATH=. .venv/bin/python utdata/sparlasare/led_e.py ["Sö 113"] [--sweep]"""
import itertools
import json
import math
import os
import random
import sys

import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from led_a import align, rows_of, text_runes  # noqa: E402
from led_b import grooves_with_arrays, seg_dist, stave_of  # noqa: E402
from led_c import T  # noqa: E402

TAU = 0.25      # softmax temperature: how sharply cost differences become probability differences (swept on Sö 113)
PRIOR = 0.08    # cost per template slot: a rune with many branches must earn them
EPS = 0.10      # probability floor: no rune is ever impossible (weathering, detector faults)
D_MID = 0.55    # depth-ratio logistic midpoint (led D: hard 0.5–0.65 gave the first net signal)
D_SLOPE = 0.12


def blob_weight(depth_ratio: float, elong: float, length: float) -> float:
    """How likely this blob is a carved branch rather than weathering or a serif."""
    w_d = 1.0 / (1.0 + math.exp(-(depth_ratio - D_MID) / D_SLOPE))
    w_e = 0.5 + 0.5 * min(1.0, max(0.0, (elong - 1.6) / 2.4))
    w_l = 0.5 + 0.5 * min(1.0, max(0.0, (length - 3.0) / 4.0))
    return w_d * w_e * w_l


def weighted_blobs(runes: list[dict], lines: list[dict], arrays: dict) -> dict:
    """Like led C's all_blobs but no hard depth filter: every elongated blob outside the staves' widths and band
    lines, assigned to its nearest stave, with a weight from depth ratio, elongation and length."""
    mask, wide, hw_img, res = arrays["mask"], arrays["wide_area"], arrays["half_width"], arrays["res"]
    depth = arrays["depth"]
    hw = float(np.median(hw_img[mask])) if mask.any() else 3.0
    staves = {r["id"]: stave_of(r) for r in runes}
    pts_all = np.argwhere(mask & ~wide) * res
    keep = np.ones(len(pts_all), bool)
    for A, B in staves.values():
        keep &= seg_dist(pts_all, A, B) > hw + 0.6
    for s in lines:
        if s["kind"] == "ornament" or s.get("length_mm", 0) > 60:
            keep &= seg_dist(pts_all, np.array(s["p0_mm"]), np.array(s["p1_mm"])) > hw + 0.6
    img = np.zeros(mask.shape, bool)
    px = (pts_all[keep] / res).astype(int)
    img[px[:, 0], px[:, 1]] = True
    lab, n = ndimage.label(img, structure=np.ones((3, 3)))
    out = {r["id"]: [] for r in runes}
    for k in range(1, n + 1):
        pts = np.argwhere(lab == k) * res
        if len(pts) * res * res < 4.0:
            continue
        best_id, best_d = None, None
        for rid, (A, B) in staves.items():
            d = float(seg_dist(pts, A, B).min())
            if best_d is None or d < best_d:
                best_id, best_d = rid, d
        if best_d > hw + 3.5:
            continue
        A, B = staves[best_id]
        L = float(np.linalg.norm(B - A))
        u = (B - A) / max(L, 1e-9)
        nrm = np.array([-u[1], u[0]])
        C = pts - pts.mean(axis=0)
        w_, v_ = np.linalg.eigh(C.T @ C / len(pts))
        elong = w_[1] / max(w_[0], 1e-9)
        axis = v_[:, 1]
        t_ = C @ axis
        length = float(t_.max() - t_.min())
        if length < 3.0 or elong < 1.6:
            continue
        ang = float(np.degrees(np.arccos(min(1.0, abs(float(axis @ u))))))
        near = pts[np.argmin(seg_dist(pts, A, B))]
        t_attach = float(np.clip((near - A) @ u / max(L, 1e-9), -0.2, 1.2))
        if ang < 15 and not 0.05 < t_attach < 0.95:
            continue
        # the blob's depth against its stave's depth
        bpx = (pts / res).astype(int)
        blob_d = float(np.median(depth[bpx[:, 0], bpx[:, 1]]))
        spx = np.array([(A + t * u) / res for t in np.linspace(0, L, 25)]).astype(int)
        spx = spx[(spx[:, 0] >= 0) & (spx[:, 0] < depth.shape[0]) & (spx[:, 1] >= 0) & (spx[:, 1] < depth.shape[1])]
        stave_d = float(np.median(depth[spx[:, 0], spx[:, 1]])) if len(spx) else 0.0
        ratio = blob_d / stave_d if stave_d > 0 else 1.0
        tz = min(max(t_attach, 0.0), 1.0)
        out[best_id].append({"zone": "end" if min(tz, 1 - tz) < 0.35 else "mid",
                             "side": float(np.sign((pts.mean(axis=0) - A) @ nrm)) or 1.0,
                             "angle": ang, "length": length, "t": t_attach, "long": length > 0.55 * L,
                             "elong": float(elong), "ratio": float(ratio)})
    # two blobs on opposite sides at matching height and angle are one crossing stroke
    feats = {}
    for rid, bs in out.items():
        merged, used = [], set()
        for i, b in enumerate(bs):
            if i in used:
                continue
            j = next((j for j, c in enumerate(bs) if j > i and j not in used and c["side"] != b["side"]
                      and abs(c["t"] - b["t"]) < 0.3 and abs(c["angle"] - b["angle"]) < 30), None)
            if j is not None and b["zone"] == "mid":
                used |= {i, j}
                c = bs[j]
                merged.append({"cross": True, "zone": "mid", "side": 0, "long": False,
                               "w": max(blob_weight(b["ratio"], b["elong"], b["length"]),
                                        blob_weight(c["ratio"], c["elong"], c["length"]))})
            else:
                used.add(i)
                merged.append({"cross": False, "zone": b["zone"], "side": b["side"], "long": b["long"],
                               "w": blob_weight(b["ratio"], b["elong"], b["length"])})
        feats[rid] = merged
    return feats


def load_features(signum: str) -> dict:
    """Cached: {"runes": the detected runes, "feats": {id: [weighted blobs]}}. The heavy array run happens once."""
    path = os.path.join(HERE, signum.replace(" ", "_") + "_feats_e.json")
    if os.path.exists(path):
        d = json.load(open(path))
        d["feats"] = {int(k) if k.lstrip("-").isdigit() else k: v for k, v in d["feats"].items()}
        return d
    g = grooves_with_arrays(signum)
    runes = [r for r in g["runes"] if r.get("strokes_detail")]
    feats = weighted_blobs(runes, g["stroke_lines"], g["arrays"])
    out = {"signum": signum, "runes": runes, "feats": feats}
    json.dump(out, open(path, "w"))
    return out


def template_cost(obs: list[dict], template: list[tuple], prior: float) -> float:
    """The cheapest weighted way to lay the observed blobs into the template's slots. Discarding a blob as noise
    costs its weight w; using it costs w times the fit penalties; a missed slot costs 0.25; and every slot in the
    template costs `prior`, so a big template pays for its capacity."""
    best = None
    for polarity in (1, -1):
        for perm in itertools.permutations(range(len(template))) if len(template) <= 4 else [tuple(range(len(template)))]:
            cost, used, side_of = 0.0, set(), {}
            for o in sorted(obs, key=lambda b: -b["w"]):
                slot = None
                for ti in perm:
                    if ti in used:
                        continue
                    cross, zone, grp, long_ = template[ti]
                    if o["cross"] != cross:
                        continue
                    c = 0.0
                    if not o["cross"]:
                        if o["zone"] == "mid" and zone == "end":
                            c += 0.3
                        if o["long"] and not long_:
                            c += 0.5
                        want = side_of.get(grp)
                        if want is not None and want != o["side"] * polarity:
                            c += 0.6
                    slot = (c, ti, o)
                    break
                if slot is None or slot[0] >= 1.0:
                    cost += o["w"] * 1.0  # cheaper to call it noise
                else:
                    c, ti, o2 = slot
                    cost += o2["w"] * c
                    used.add(ti)
                    if not o2["cross"]:
                        cross, zone, grp, long_ = template[ti]
                        side_of.setdefault(grp, o2["side"] * polarity)
            cost += 0.25 * (len(template) - len(used))
            if best is None or cost < best:
                best = cost
    return (best if best is not None else 99.0) + prior * len(template)


def rune_probs(obs: list[dict], tau: float = TAU, prior: float = PRIOR, eps: float = EPS) -> dict[str, float]:
    """P(rune | observed blobs) over the 16 runes: softmax of −cost/tau with a uniform floor."""
    costs = {r: min(template_cost(obs, t, prior) for t in alts) for r, alts in T.items()}
    m = min(costs.values())
    ex = {r: math.exp(-(c - m) / tau) for r, c in costs.items()}
    z = sum(ex.values())
    return {r: (1 - eps) * v / z + eps / 16 for r, v in ex.items()}


def evaluate(order, probs_by_id, txt, tau=TAU, margin=0.75):
    """Alignment via margin sets (as led D, for comparability), then probability metrics on the pairs."""
    dists = [probs_by_id[r["id"]] for r in order]
    sets = []
    for d in dists:
        mx = max(d.values())
        sets.append({r for r, p in d.items() if math.log(mx / p) * tau <= margin})
    cost, pairs = align(sets, txt)
    p_true = [dists[i][t] for i, t in pairs]
    ranks = [sorted(dists[i].values(), reverse=True).index(dists[i][t]) for i, t in pairs]
    return {"cost": cost, "pairs": pairs,
            "mean_p": float(np.mean(p_true)) if p_true else 0.0,
            "logscore": float(np.mean(np.log(p_true))) if p_true else -99.0,
            "top1": float(np.mean([r == 0 for r in ranks])) if ranks else 0.0,
            "top3": float(np.mean([r < 3 for r in ranks])) if ranks else 0.0}


def run(signum: str, tau=TAU, prior=PRIOR, quiet=False):
    data = load_features(signum)
    runes, feats = data["runes"], data["feats"]
    probs_by_id = {r["id"]: rune_probs(feats[r["id"]], tau, prior) for r in runes}
    text = text_runes(signum)
    rows = rows_of(runes)
    best = best_order = None
    for top_down in (True, False):
        for left_right in (True, False):
            order = [r for row in (rows if top_down else rows[::-1]) for r in (row if left_right else row[::-1])]
            e = evaluate(order, probs_by_id, text, tau)
            if best is None or e["cost"] < best["cost"]:
                best, best_order = e, order
    rng = random.Random(7)
    null = [evaluate(best_order, probs_by_id, "".join(rng.sample(text, len(text))), tau) for _ in range(20)]
    res = {"signum": signum, "n_runes": len(runes), "text_len": len(text), "tau": tau, "prior": prior,
           "mean_p": best["mean_p"], "logscore": best["logscore"], "top1": best["top1"], "top3": best["top3"],
           "null_mean_p": float(np.mean([e["mean_p"] for e in null])),
           "null_mean_p_sd": float(np.std([e["mean_p"] for e in null])),
           "null_top1": float(np.mean([e["top1"] for e in null])),
           "null_top3": float(np.mean([e["top3"] for e in null])),
           "null_logscore": float(np.mean([e["logscore"] for e in null]))}
    if not quiet:
        print(f"{signum}: {len(runes)} runor, texten {len(text)} (tau {tau}, prior {prior})")
        print(f"  medel-P(facit) {res['mean_p']:.3f}  mot omkastad {res['null_mean_p']:.3f} ± {res['null_mean_p_sd']:.3f}")
        print(f"  topp-1 {res['top1']:.2f} (slump {res['null_top1']:.2f});  topp-3 {res['top3']:.2f} (slump {res['null_top3']:.2f})")
        print(f"  logpoäng {res['logscore']:.3f} mot {res['null_logscore']:.3f} (uniform {math.log(1/16):.3f})")
        for i, t in best["pairs"]:
            d = probs_by_id[best_order[i]["id"]]
            top = sorted(d.items(), key=lambda kv: -kv[1])[:4]
            mark = "JA " if t == top[0][0] else ("ja " if t in {r for r, _ in top[:3]} else "nej")
            print(f"   {i:3} facit {t} {mark} " + "  ".join(f"{r} {p:.2f}" for r, p in top))
    return res


def sweep(signum="Sö 113"):
    print(f"svep på {signum}: medel-P(facit) − slump (och topp-1 − slump)")
    for tau in (0.3, 0.5, 0.8):
        line = []
        for prior in (0.0, 0.08, 0.12, 0.2):
            r = run(signum, tau, prior, quiet=True)
            line.append(f"prior {prior}: {r['mean_p'] - r['null_mean_p']:+.3f} ({r['top1'] - r['null_top1']:+.2f})")
        print(f"  tau {tau}:  " + "   ".join(line))


def main(*args):
    rest = [a for a in args if not a.startswith("--")]
    if "--sweep" in args:
        sweep(rest[0] if rest else "Sö 113")
        return
    signums = rest or ["Sö 113"]
    out = [run(s) for s in signums]
    json.dump(out, open(os.path.join(HERE, "led_e.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*(sys.argv[1:] or ()))
