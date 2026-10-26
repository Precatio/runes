"""Summering av led F över alla stenar: läser led_f_<sten>.json, poolar orden och svarar på huvudfrågan –
höjer skannerspåren facits sannolikhet i riktig luckfyllnad? Parade Wilcoxontest (per ord): skanner mot utan
(ensidigt), skanner mot omflyttad (ensidigt), omflyttad mot utan (tvåsidigt – omflyttade mängder ska inte hjälpa).
Dessutom samma tabell för enbart stenar med pålitlig parning (täckningen minst två standardavvikelser över den
omkastade textens), eftersom böjda slingor kan kasta om radordningen och då hamnar spåren på fel positioner –
ett provbänksproblem, inte ett produktionsproblem: i panelen är luckans plats känd.
    .venv/bin/python utdata/sparlasare/led_f_summering.py"""
import glob
import json
import os

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
CONDS = ("utan", "skanner", "omflyttad")


def table(rows, label):
    both = [x for x in rows if all(x.get(c) for c in CONDS)]
    if not both:
        print(f"{label}: inga ord")
        return None
    print(f"\n{label} ({len(both)} ord på {len({x['sig'] for x in both})} stenar):")
    for c in CONDS:
        print(f"  {c:10} ord rätt {np.mean([x[c]['word_ok'] for x in both]):.3f}  fyllnad rätt "
              f"{np.mean([x[c]['right'] for x in both]):.3f}  medel-P(facit) {np.mean([x[c]['p_truth'] for x in both]):.3f}")
    out = {"n": len(both), "stones": len({x["sig"] for x in both}),
           "means": {c: {"word_ok": float(np.mean([x[c]["word_ok"] for x in both])),
                         "right": float(np.mean([x[c]["right"] for x in both])),
                         "p_truth": float(np.mean([x[c]["p_truth"] for x in both]))} for c in CONDS}}
    for a, b, alt in (("skanner", "utan", "greater"), ("skanner", "omflyttad", "greater"), ("omflyttad", "utan", "two-sided")):
        d = [x[a]["p_truth"] - x[b]["p_truth"] for x in both]
        nz = [v for v in d if abs(v) > 1e-9]
        if nz:
            w = stats.wilcoxon(nz, alternative=alt)
            print(f"  {a} − {b}: medel {np.mean(d):+.4f}, {sum(v > 0 for v in nz)} av {len(nz)} ändrade åt plus, "
                  f"Wilcoxon p = {w.pvalue:.4f} ({alt})")
            out[f"{a}_vs_{b}"] = {"mean_diff": float(np.mean(d)), "n_changed": len(nz),
                                  "n_plus": int(sum(v > 0 for v in nz)), "p": float(w.pvalue), "alt": alt}
    return out


def main():
    rows, stones = [], {}
    for path in sorted(glob.glob(os.path.join(HERE, "led_f_*.json"))):
        if path.endswith("summering.json"):
            continue
        d = json.load(open(path))
        if not isinstance(d, dict) or "rows" not in d:
            continue
        rows.extend(d["rows"])
        stones.update(d["stones"])
    print("parningskvalitet per sten (täckning mot omkastad text):")
    good = set()
    for s, q in sorted(stones.items()):
        z = (q["coverage"] - q["null"]) / max(q["null_sd"], 1e-9)
        ok = z >= 2.0
        if ok:
            good.add(s)
        print(f"  {s:14} {q['n_paired']:3} par av {q['n_detected']:3} upptäckta; täckning {q['coverage']:.2f} "
              f"mot {q['null']:.2f} ± {q['null_sd']:.2f}  ({z:+.1f} sd){'  PÅLITLIG' if ok else ''}")
    all_t = table(rows, "alla stenar")
    good_t = table([x for x in rows if x["sig"] in good], "stenar med pålitlig parning")
    json.dump({"stones": stones, "reliable": sorted(good), "all": all_t, "reliable_only": good_t},
              open(os.path.join(HERE, "led_f_summering.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
