"""Spårläsaren, led D (2026-10-17): kostnadsbaserad matchning i stället för boolesk. Led C gav skarpa mängder när
observationen var ren men dömde över hälften av runorna till "omöjligt" – brus och översegmentering gör att strikta
regler slår fel. Här får varje runmall en kostnad: en observerad bistav som inte ryms i mallen kostar 1,0 (troligen
brus eller vittring), en mallbistav som inte observerats kostar 0,25 (detektorn missar ofta), en ändobservation i en
mittplats 0,3, korsning mot icke-korsning går inte alls. Runans kostnad är den billigaste mallens, och mängden är alla
runor inom 0,75 av den bästa – aldrig tom. Det är samma tanke som i sannolikhetsmodellen: säg inte mer än provet tål.
    cd aagaard-research && PYTHONPATH=. .venv/bin/python utdata/sparlasare/led_d.py ["Sö 113"]"""
import itertools
import json
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from led_a import FUT, align, rows_of, text_runes  # noqa: E402
from led_b import grooves_with_arrays  # noqa: E402
from led_c import T, all_blobs  # noqa: E402

MARGIN = 0.75


def template_cost(obs: list[dict], template: list[tuple]) -> float:
    """The cheapest way to lay the observed branches into the template's slots."""
    best = None
    for polarity in (1, -1):
        for perm in itertools.permutations(range(len(template))) if len(template) <= 4 else [tuple(range(len(template)))]:
            cost, used, side_of = 0.0, set(), {}
            for o in obs:
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
                if slot is None:
                    cost += 1.0  # noise, weathering or a neighbour's stroke
                else:
                    c, ti, o2 = slot
                    cost += c
                    used.add(ti)
                    if not o2["cross"]:
                        cross, zone, grp, long_ = template[ti]
                        side_of.setdefault(grp, o2["side"] * polarity)
            cost += 0.25 * (len(template) - len(used))  # branches the detector missed
            if best is None or cost < best:
                best = cost
    return best if best is not None else 99.0


def rune_costs(obs: list[dict]) -> dict[str, float]:
    return {r: min(template_cost(obs, t) for t in alts) for r, alts in T.items()}


def candidate_set(obs: list[dict]) -> set[str]:
    c = rune_costs(obs)
    m = min(c.values())
    return {r for r, v in c.items() if v - m <= MARGIN}


def main(signum="Sö 113"):
    g = grooves_with_arrays(signum)
    runes = [r for r in g["runes"] if r.get("strokes_detail")]
    feats = all_blobs(runes, g["stroke_lines"], g["arrays"], depth_ratio=float(os.environ.get("DEPTH_RATIO", "0") or 0))
    sets_by_id = {r["id"]: candidate_set(feats[r["id"]]) for r in runes}
    nb = [len(feats[r["id"]]) for r in runes]
    text = text_runes(signum)
    rows = rows_of(runes)
    print(f"{signum}: {len(runes)} runor; texten {len(text)}; bistavar/runa {np.mean(nb):.2f}")

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
    right = sum(t in ss for _, t, ss in inf)
    print(f"informativa: {len(inf)}, rätt {right}")
    for i, t, ss in inf:
        print(f"   {i:3} facit {t} {'JA ' if t in ss else 'NEJ'} ({len(ss)}): {''.join(ss)}")
    json.dump({"signum": signum, "coverage": best["coverage"], "set_size": best["set_size"], "null": null,
               "branches_mean": float(np.mean(nb)), "informative": len(inf), "informative_right": right},
              open(os.path.join(HERE, "led_d.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*(sys.argv[1:] or ()))
