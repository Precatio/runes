"""Spårläsaren, led B (2026-10-17): bistavarna läses på maskenivå. Led A visade att skelettet tappar bistavarna – de
äts av korsningszonen eller växer aldrig ut ur det breda stavspåret – så här går vi tillbaka till själva spårmasken:
pixlar som ligger i spår men utanför stavarnas egen bredd och utanför slinglinjerna. Sammanhängande blobbar som sitter
fast i en stav och är avlånga blir bistavar, med läge (ände/mitt), sida och korsning. Sedan samma mängder, parning och
slumpkontroll som i led A.
    PYTHONPATH=. .venv/bin/python utdata/sparlasare/led_b.py ["Sö 113"]"""
import json
import os
import random
import sys

import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from led_a import FUT, SHAPES, align, consistent, rows_of, text_runes  # noqa: E402


def grooves_with_arrays(signum: str) -> dict:
    import trimesh
    from src.auto_grooves import analyze_grooves
    ref = json.load(open(os.path.join(ROOT, "utdata", "Rak", "referenser_g4", signum.replace(" ", "_") + ".json")))
    scan = next(p for p in (os.path.join(ROOT, "skanningar", ref["file"]), os.path.join(ROOT, ref["file"]))
                if os.path.exists(p))
    return analyze_grooves(trimesh.load(scan, process=False), ref["parameters"]["normal"],
                           up=ref["parameters"].get("up"), resolution_mm=0.6, keep_arrays=True)


def stave_of(rune: dict):
    st = max(rune["strokes_detail"], key=lambda s: s["length_mm"])
    return np.array(st["p0_mm"]), np.array(st["p1_mm"])


def seg_dist(P: np.ndarray, A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Distance from each point in P (n×2, mm) to the segment AB."""
    u = B - A
    L2 = float(u @ u) or 1e-9
    t = np.clip((P - A) @ u / L2, 0.0, 1.0)
    proj = A + t[:, None] * u
    return np.linalg.norm(P - proj, axis=1)


def branch_blobs(r: dict, runes: list[dict], lines: list[dict], arrays: dict):
    """The rune's branches read from the groove mask: elongated blobs outside every stave's own width and outside
    the band lines, attached to this rune's stave. Returns [(crossing, zone)]."""
    mask, wide, hw_img, res = arrays["mask"], arrays["wide_area"], arrays["half_width"], arrays["res"]
    A, B = stave_of(r)
    L = float(np.linalg.norm(B - A))
    u = (B - A) / max(L, 1e-9)
    nrm = np.array([-u[1], u[0]])
    hw = float(np.median(hw_img[mask])) if mask.any() else 3.0
    # the corridor around this stave where branches can live
    lo = np.minimum(A, B) - 0.8 * L
    hi = np.maximum(A, B) + 0.8 * L
    r0, c0 = (max(0, int(lo[0] / res)), max(0, int(lo[1] / res)))
    r1, c1 = (min(mask.shape[0], int(hi[0] / res) + 1), min(mask.shape[1], int(hi[1] / res) + 1))
    sub = (mask & ~wide)[r0:r1, c0:c1]
    if not sub.any():
        return []
    yy, xx = np.mgrid[r0:r1, c0:c1]
    P = np.stack([yy.ravel() * res, xx.ravel() * res], axis=1)
    keep = sub.ravel().copy()
    # outside every stave's own width (all runes), and outside the band and ornament lines
    for other in runes:
        A2, B2 = stave_of(other)
        keep &= seg_dist(P, A2, B2) > hw + 0.6
    for s in lines:
        if s["kind"] in ("ornament",) or s.get("length_mm", 0) > 60:
            keep &= seg_dist(P, np.array(s["p0_mm"]), np.array(s["p1_mm"])) > hw + 0.6
    resid = keep.reshape(sub.shape)
    lab, n = ndimage.label(resid, structure=np.ones((3, 3)))
    out = []
    for k in range(1, n + 1):
        pts = np.argwhere(lab == k) * res + [r0 * res, c0 * res]
        if len(pts) * res * res < 4.0:  # under 4 mm²
            continue
        d_stave = seg_dist(pts, A, B)
        if d_stave.min() > hw + 3.5:
            continue  # not attached to this stave
        C = pts - pts.mean(axis=0)
        w_, v_ = np.linalg.eigh(C.T @ C / len(pts))
        elong = w_[1] / max(w_[0], 1e-9)
        axis = v_[:, 1]
        t_ = C @ axis
        length = float(t_.max() - t_.min())
        if length < 3.5 or elong < 2.0:
            continue
        ang = np.degrees(np.arccos(min(1.0, abs(float(axis @ u)))))
        near = pts[np.argmin(d_stave)]
        t_attach = float(np.clip((near - A) @ u / max(L, 1e-9), -0.2, 1.2))
        if ang < 15 and not 0.05 < t_attach < 0.95:
            continue  # in line with the stave beyond its end: part of the stave's groove
        side = float(np.sign((pts.mean(axis=0) - A) @ nrm))
        tz = min(max(t_attach, 0.0), 1.0)
        tz = min(tz, 1 - tz)
        out.append({"zone": "end" if tz < 0.35 else "mid", "side": side, "angle": ang,
                    "t": t_attach, "length": length})
    # two blobs on opposite sides at matching height and angle are one crossing stroke
    branches, used = [], set()
    for i, b in enumerate(out):
        if i in used:
            continue
        j = next((j for j, c in enumerate(out) if j > i and j not in used and c["side"] != b["side"]
                  and abs(c["t"] - b["t"]) < 0.3 and abs(c["angle"] - b["angle"]) < 30), None)
        if j is not None and b["zone"] == "mid":
            used |= {i, j}
            branches.append((True, "mid"))
        else:
            used.add(i)
            branches.append((False, b["zone"]))
    return branches


def main(signum="Sö 113"):
    g = grooves_with_arrays(signum)
    runes = [r for r in g["runes"] if r.get("strokes_detail")]
    lines = g["stroke_lines"]
    arrays = g["arrays"]
    feats = {r["id"]: branch_blobs(r, runes, lines, arrays) for r in runes}
    nb = [len(v) for v in feats.values()]
    text = text_runes(signum)
    rows = rows_of(runes)
    print(f"{signum}: {len(runes)} runor i {len(rows)} rader {[len(r) for r in rows]}; texten har {len(text)} runor")
    print(f"bistavar per runa (maskenivå): medel {np.mean(nb):.2f}; utan bistav {sum(x == 0 for x in nb)} av {len(nb)}")

    def sets_for(order):
        return [{c for c in FUT if consistent(feats[r["id"]], c)} for r in order]

    def evaluate(order, txt):
        sets = sets_for(order)
        cost, pairs = align(sets, txt)
        cov = [t in sets[i] for i, t in pairs]
        return {"cost": cost, "pairs": pairs, "sets": sets, "coverage": float(np.mean(cov)) if cov else 0.0,
                "set_size": float(np.mean([len(sets[i]) for i, _ in pairs])) if pairs else 16.0}

    best = best_lab = best_order = None
    for top_down in (True, False):
        for left_right in (True, False):
            order = [r for row in (rows if top_down else rows[::-1]) for r in (row if left_right else row[::-1])]
            e = evaluate(order, text)
            lab = f"rader {'uppifrån' if top_down else 'nerifrån'}, {'v→h' if left_right else 'h→v'}"
            print(f"  {lab:24} kostnad {e['cost']:.1f}  täckning {e['coverage']:.2f}  mängd {e['set_size']:.1f}")
            if best is None or e["cost"] < best["cost"]:
                best, best_lab, best_order = e, lab, order
    rng = random.Random(7)
    null = []
    for _ in range(20):
        sh = list(text)
        rng.shuffle(sh)
        null.append(evaluate(best_order, "".join(sh))["coverage"])
    print(f"\nbäst: {best_lab}. Täckning {best['coverage']:.2f} (mängd {best['set_size']:.1f}); "
          f"omkastad text {np.mean(null):.2f} ± {np.std(null):.2f}")
    inf = [(i, t, sorted(best["sets"][i])) for i, t in best["pairs"] if len(best["sets"][i]) < 16]
    print(f"informativa mängder: {len(inf)}; rätt i {sum(t in ss for _, t, ss in inf)}")
    for i, t, ss in inf:
        print(f"   runa {i:3} facit {t}  {'JA ' if t in ss else 'NEJ'} ({len(ss)}): {''.join(ss)}")
    json.dump({"signum": signum, "coverage": best["coverage"], "set_size": best["set_size"],
               "null": null, "n_branches_mean": float(np.mean(nb)),
               "informative": len(inf), "informative_right": sum(t in ss for _, t, ss in inf)},
              open(os.path.join(HERE, "led_b.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*(sys.argv[1:] or ()))
