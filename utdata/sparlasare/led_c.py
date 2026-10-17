"""Spårläsaren, led C (2026-10-17): global blobbtilldelning och rikare runmallar. Led B läste bistavarna ur spårmasken
men lät en blobb mellan två runor räknas för båda, så rena stavar som i fick falska bistavar. Här tilldelas varje blobb
bara sin närmaste stav. Mallarna använder dessutom det som är känt utan att veta vad som är upp eller läsriktning:
korsande eller ej, ände eller mitt, samma eller motsatt sida (relativt, prövas under spegling), och om bistaven är lång
(som u:s båge) eller kort. En runa är möjlig om de funna bistavarna ryms i någon av dess mallar (saknade bistavar är
tillåtna – detektorn missar långt oftare än den hittar på). Blir mängden tom räknas den som "säger inget" (alla 16).
Samma parning och slumpkontroll som förut.
    cd aagaard-research && PYTHONPATH=. .venv/bin/python utdata/sparlasare/led_c.py ["Sö 113"]"""
import itertools
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
from led_a import FUT, align, rows_of, text_runes  # noqa: E402
from led_b import grooves_with_arrays, seg_dist, stave_of  # noqa: E402


def all_blobs(runes: list[dict], lines: list[dict], arrays: dict, depth_ratio: float = 0.0):
    """Every elongated groove blob outside the staves' own width and the band lines, assigned to its nearest stave:
    {rune id: [branch]} where a branch is {cross(later), zone, side ±1, angle°, length, t}."""
    mask, wide, hw_img, res = arrays["mask"], arrays["wide_area"], arrays["half_width"], arrays["res"]
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
        # the blob belongs to the stave it sits closest to, and only if it is attached to it
        best_id, best_d = None, None
        for rid, (A, B) in staves.items():
            d = float(seg_dist(pts, A, B).min())
            if best_d is None or d < best_d:
                best_id, best_d = rid, d
        if best_d > hw + 3.5:
            continue
        A, B = staves[best_id]
        if depth_ratio > 0:
            # a real branch is carved about as deep as its stave; weathering and serifs are shallow
            depth, res_ = arrays["depth"], arrays["res"]
            px = (pts / res_).astype(int)
            blob_d = float(np.median(depth[px[:, 0], px[:, 1]]))
            su = (B - A) / max(np.linalg.norm(B - A), 1e-9)
            spx = np.array([(A + t * su) / res_ for t in np.linspace(0, np.linalg.norm(B - A), 25)]).astype(int)
            spx = spx[(spx[:, 0] >= 0) & (spx[:, 0] < depth.shape[0]) & (spx[:, 1] >= 0) & (spx[:, 1] < depth.shape[1])]
            stave_d = float(np.median(depth[spx[:, 0], spx[:, 1]])) if len(spx) else 0.0
            if stave_d > 0 and blob_d < depth_ratio * stave_d:
                continue
        L = float(np.linalg.norm(B - A))
        u = (B - A) / max(L, 1e-9)
        nrm = np.array([-u[1], u[0]])
        C = pts - pts.mean(axis=0)
        w_, v_ = np.linalg.eigh(C.T @ C / len(pts))
        elong = w_[1] / max(w_[0], 1e-9)
        axis = v_[:, 1]
        t_ = C @ axis
        length = float(t_.max() - t_.min())
        if length < 3.5 or elong < 2.0:
            continue
        ang = float(np.degrees(np.arccos(min(1.0, abs(float(axis @ u))))))
        near = pts[np.argmin(seg_dist(pts, A, B))]
        t_attach = float(np.clip((near - A) @ u / max(L, 1e-9), -0.2, 1.2))
        if ang < 15 and not 0.05 < t_attach < 0.95:
            continue
        tz = min(max(t_attach, 0.0), 1.0)
        out[best_id].append({"zone": "end" if min(tz, 1 - tz) < 0.35 else "mid",
                             "side": float(np.sign((pts.mean(axis=0) - A) @ nrm)) or 1.0,
                             "angle": ang, "length": length, "t": t_attach, "long": length > 0.55 * L})
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
                merged.append({"cross": True, "zone": "mid", "side": 0, "long": False})
            else:
                used.add(i)
                merged.append({"cross": False, "zone": b["zone"], "side": b["side"], "long": b["long"]})
        feats[rid] = merged
    return feats


# --- templates: each rune as alternative branch lists of (cross, zone, side group 'A'/'B', long?). Side groups are
# relative (mirroring is unknown); 'end'/'mid' are inexact so an 'end' observation may fit a 'mid' slot, and a long
# branch may have been read short, but never the other way around.
T = {
    "i": [[]],
    "s": [[], [(False, "end", "A", False)]],  # short-twig s: a short stave, sometimes with a foot
    "u": [[(False, "end", "A", True)], [(False, "end", "A", False), (False, "end", "A", False)]],
    "k": [[(False, "end", "A", False)], [(False, "mid", "A", False)]],
    "l": [[(False, "end", "A", False)]],
    "t": [[(False, "end", "A", False)], [(False, "end", "A", False), (False, "end", "B", False)]],
    "m": [[(False, "end", "A", False), (False, "end", "B", False)]],
    "R": [[(False, "end", "A", False), (False, "end", "B", False)]],
    "f": [[(False, "end", "A", False), (False, "mid", "A", False)],
          [(False, "end", "A", False), (False, "end", "A", False)],
          [(False, "end", "A", False), (False, "mid", "A", False), (False, "mid", "A", False)]],
    "r": [[(False, "end", "A", False), (False, "mid", "A", False)],
          [(False, "end", "A", False), (False, "mid", "A", False), (False, "mid", "A", False)]],
    "b": [[(False, "end", "A", False), (False, "mid", "A", False)],
          [(False, "end", "A", False), (False, "mid", "A", False), (False, "mid", "A", False), (False, "end", "A", False)]],
    "þ": [[(False, "mid", "A", False)], [(False, "mid", "A", False), (False, "mid", "A", False)]],
    "n": [[(True, "mid", "A", False)]],
    "a": [[(True, "mid", "A", False)]],
    "h": [[(True, "mid", "A", False)]],
    "o": [[(True, "mid", "A", False)], [(True, "mid", "A", False), (True, "mid", "A", False)]],
}


def fits(obs: list[dict], template: list[tuple]) -> bool:
    """Do the observed branches fit inside the template? Each observation must take an unused slot: crossing must
    match, an 'end' observation may sit in a 'mid' slot and vice versa only mid→mid, a long observation needs a long
    slot, and the side groups must be mappable (A/B to left/right one way or the other)."""
    if len(obs) > len(template):
        return False
    for polarity in (1, -1):
        for perm in itertools.permutations(range(len(template)), len(obs)):
            ok = True
            side_of = {}
            for o, ti in zip(obs, perm):
                cross, zone, grp, long_ = template[ti]
                if o["cross"] != cross:
                    ok = False
                    break
                if not o["cross"]:
                    if o["zone"] == "mid" and zone == "end":
                        ok = False
                        break
                    if o["long"] and not long_:
                        ok = False
                        break
                    want = side_of.setdefault(grp, o["side"] * polarity)
                    if want != o["side"] * polarity:
                        ok = False
                        break
            if ok and len({g for g in side_of} ) <= 2 and (len(side_of) < 2 or len({v for v in side_of.values()}) == len(side_of)):
                return True
    return False


def candidate_set(obs: list[dict]) -> set[str]:
    s = {r for r, alts in T.items() if any(fits(obs, t) for t in alts)}
    return s or set(FUT)  # an impossible combination says nothing, not everything


def main(signum="Sö 113"):
    g = grooves_with_arrays(signum)
    runes = [r for r in g["runes"] if r.get("strokes_detail")]
    feats = all_blobs(runes, g["stroke_lines"], g["arrays"])
    nb = [len(feats[r["id"]]) for r in runes]
    text = text_runes(signum)
    rows = rows_of(runes)
    sets_by_id = {r["id"]: candidate_set(feats[r["id"]]) for r in runes}
    empty = sum(1 for r in runes if not {c for c, alts in T.items() if any(fits(feats[r["id"]], t) for t in alts)})
    print(f"{signum}: {len(runes)} runor; texten {len(text)}; bistavar/runa {np.mean(nb):.2f}; utan {sum(x == 0 for x in nb)}; omöjliga {empty}")

    def evaluate(order, txt):
        sets = [sets_by_id[r["id"]] for r in order]
        cost, pairs = align(sets, txt)
        cov = [t in sets[i] for i, t in pairs]
        return {"cost": cost, "pairs": pairs, "sets": sets, "coverage": float(np.mean(cov)) if cov else 0.0,
                "set_size": float(np.mean([len(sets[i]) for i, _ in pairs])) if pairs else 16.0}

    best = best_lab = best_order = None
    for top_down in (True, False):
        for left_right in (True, False):
            order = [r for row in (rows if top_down else rows[::-1]) for r in (row if left_right else row[::-1])]
            e = evaluate(order, text)
            lab = f"{'uppifrån' if top_down else 'nerifrån'}, {'v→h' if left_right else 'h→v'}"
            print(f"  {lab:18} kostnad {e['cost']:.1f}  täckning {e['coverage']:.2f}  mängd {e['set_size']:.1f}")
            if best is None or e["cost"] < best["cost"]:
                best, best_lab, best_order = e, lab, order
    rng = random.Random(7)
    null = [evaluate(best_order, "".join(rng.sample(text, len(text))))["coverage"] for _ in range(20)]
    inf = [(i, t, sorted(best["sets"][i])) for i, t in best["pairs"] if len(best["sets"][i]) < 16]
    print(f"\nbäst: {best_lab}. Täckning {best['coverage']:.2f} (mängd {best['set_size']:.1f}); omkastad {np.mean(null):.2f} ± {np.std(null):.2f}")
    print(f"informativa: {len(inf)}, rätt {sum(t in ss for _, t, ss in inf)}")
    for i, t, ss in inf:
        print(f"   {i:3} facit {t} {'JA ' if t in ss else 'NEJ'} ({len(ss)}): {''.join(ss)}")
    json.dump({"signum": signum, "coverage": best["coverage"], "set_size": best["set_size"], "null": null,
               "branches_mean": float(np.mean(nb)), "informative": len(inf),
               "informative_right": sum(t in ss for _, t, ss in inf)},
              open(os.path.join(HERE, "led_c.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*(sys.argv[1:] or ()))
