"""Länkmodellen (src/linking.py): länkar mellan runstenar som delar namn, prövade mot en nollmodell, släktgrupper,
händelser och gårdsnamn. Skriver data/links.json, som appen läser (Fynd per sten, Statistik (R)).

Slumpfelet redovisas på två sätt: q_lo–q_hi per länk (nollkörningarna dragna om, src/linking.fdr) och samma körning
med andra frön (--seeds), så att det syns om antalet säkra länkar och Jarlabankeprövningen beror på slumpen.
    .venv/bin/python -m scripts.link_entities [--null 2000] [--seeds 1,2,3]"""
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.rundata import store  # noqa: E402
from src import linking as L  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "links.json")
JARLABANKE = ("U 127", "U 164", "U 165", "U 212", "U 261")
SEED = 2026


def _interval(v) -> list[float] | None:
    v = [x for x in v if x is not None]
    return [round(float(x), 4) for x in np.percentile(v, [2.5, 97.5])] if v else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--null", type=int, default=L.N_NULL)
    ap.add_argument("--seeds", default="1,2,3", help="fler frön för känslighetsprövningen ('' hoppar över den)")
    a = ap.parse_args()
    s = store()
    st = L.stones(s.inscriptions)
    w = L.weights(st)
    sex = L.name_sex(st)
    obs = L.links(st, w)
    stats = {}
    null = L.null_scores(st, w, a.null, seed=SEED, stats=stats)
    qb = L.fdr(obs, null, seed=SEED)
    strict = [dict(x) for x in obs]
    stats_d = {}
    null_d = L.null_scores(st, w, a.null, seed=SEED, level="district", stats=stats_d)
    L.fdr(strict, null_d, seed=SEED)
    q_strict = {(x["a"], x["b"]): x for x in strict}
    display = {p["key"]: p["name"] for x in st.values() for p in x["persons"]}
    for x in obs:
        x["names"] = [display.get(k, k) if not k.startswith("plats:") else k[6:] for k in x["shared"]]
        y = q_strict[(x["a"], x["b"])]
        x["q_district"], x["q_district_lo"], x["q_district_hi"] = y["q"], y["q_lo"], y["q_hi"]
        x["rundata_linked"] = L.rundata_linked(st[x["a"]], st[x["b"]])
        x["contradictions"] = L.contradictions(x, st, sex)
        d = L.km(st[x["a"]], st[x["b"]])
        x["km"] = None if d is None else round(d, 1)
    cut = L.FDR_CUT
    # the Monte Carlo spread of the headline numbers, from the bootstrap draws (in obs order, before sorting)
    ok = np.array([not x["contradictions"] for x in obs])
    jar_i = [i for i, x in enumerate(obs) if x["a"] in JARLABANKE and x["b"] in JARLABANKE]
    boot_sure = [int(((row < cut) & ok).sum()) for row in qb]
    boot_jar = [float(row[jar_i].max()) for row in qb] if jar_i else []
    obs.sort(key=lambda x: (x["q"], -x["score"]))
    # a link whose stones contradict each other (two fathers, dead then alive) is no family link, whatever its strength
    consistent = [x for x in obs if not x["contradictions"]]
    groups = L.groups(consistent, st)
    jar = [x for x in obs if x["a"] in JARLABANKE and x["b"] in JARLABANKE]
    pp = L.parsten_pairs(st)
    noted = L.rundata_noted_pairs(st)
    sure = [x for x in consistent if x["q"] < cut]
    found = {(x["a"], x["b"]) for x in sure}
    # what the missed pairs share: no readable name at all, one name (too little for a link) or two or more (too weak)
    shared_pp = [len(L._tokens(st[p]) & L._tokens(st[q])) for p, q in pp if (p, q) not in found]
    events, farms = defaultdict(list), defaultdict(list)
    for sg, x in st.items():
        for e in x["events"]:
            events[e].append(sg)
        for p in set(x["places"]):
            farms[p].append(sg)
    contradicted = [x for x in obs if x["q"] < cut and x["contradictions"]]
    near = [x["km"] for x in sure if x["km"] is not None]
    jar_q = max((x["q"] for x in jar), default=None)
    jar_hi = max((x["q_hi"] for x in jar), default=None)
    seeds = []
    for sd in [int(v) for v in a.seeds.split(",") if v.strip()]:
        other = [dict(x) for x in obs]
        nl = L.null_scores(st, w, a.null, seed=sd)
        L.fdr(other, nl, n_boot=1, seed=sd)
        seeds.append({"seed": sd, "null_mean": round(float(np.mean([len(z) for z in nl])), 2),
                      "n_sure": sum(1 for x in other if x["q"] < cut and not x["contradictions"]),
                      "jarlabanke_q_max": max((x["q"] for x in other if x["a"] in JARLABANKE and x["b"] in JARLABANKE),
                                              default=None)})
    out = {
        "computed_at": datetime.now(timezone.utc).isoformat(), "n_stones": len(st), "n_null": a.null, "seed": SEED,
        "n_boot": L.N_BOOT, "fdr_cut": cut, "common_max": L.COMMON, "time_gap": L.TIME_GAP,
        "n_links": len(obs), "n_pairs_all": L.all_pairs(st),
        "null_mean": round(float(np.mean([len(z) for z in null])), 2),
        "null_mean_district": round(float(np.mean([len(z) for z in null_d])), 2),
        "null_unrepaired": stats.get("unrepaired", 0) + stats_d.get("unrepaired", 0),
        "n_sure": len(sure), "n_sure_district": sum(1 for x in consistent if x["q_district"] < cut),
        # sure whatever the Monte Carlo noise (q_hi under the cut), and how many sit at the cut (interval across it)
        "n_sure_robust": sum(1 for x in sure if x["q_hi"] < cut),
        "n_at_cut": sum(1 for x in consistent if x["q_lo"] < cut <= x["q_hi"]),
        "n_sure_interval": _interval(boot_sure),
        "seeds": seeds,
        "n_contradicted": len(contradicted),
        "km_median_sure": float(np.median(near)) if near else None,
        "share_sure_within_10km": (sum(1 for d in near if d <= 10) / len(near)) if near else None,
        "validation": {"jarlabanke": {"stones": list(JARLABANKE), "pairs": len(jar), "q_max": jar_q, "q_max_hi": jar_hi,
                                      "q_max_interval": _interval(boot_jar),
                                      "passed": jar_q is not None and jar_q < cut,
                                      "stable": jar_hi is not None and jar_hi < cut},
                       "parsten": {"n": len(pp), "found": len(pp & found), "pairs": sorted(map(list, pp)),
                                   "missed_shared_none": sum(1 for v in shared_pp if v == 0),
                                   "missed_shared_one": sum(1 for v in shared_pp if v == 1),
                                   "missed_shared_two_plus": sum(1 for v in shared_pp if v >= 2)},
                       "rundata_noted": {"n": len(noted), "found": len(noted & found),
                                         "linked_sure": sum(1 for x in sure if x["rundata_linked"])}},
        "links": obs, "groups": groups,
        "events": {k: sorted(v) for k, v in sorted(events.items(), key=lambda kv: -len(kv[1]))},
        "farms": {k: sorted(v) for k, v in farms.items() if len(v) >= 2},
        "persons": {sg: [{k: p[k] for k in ("name", "role", "rel")} for p in x["persons"]] for sg, x in st.items() if x["persons"]},
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"{len(st)} stenar, {len(obs)} länkar av {out['n_pairs_all']} par (nollmodell {out['null_mean']:.1f} i landskapet, "
          f"{out['null_mean_district']:.1f} i häradet; {out['null_unrepaired']} dubbletter kvar), {len(sure)} med q < {cut} "
          f"(slumpintervall {out['n_sure_interval']}, {out['n_sure_robust']} säkra, {out['n_at_cut']} vid gränsen; "
          f"{out['n_sure_district']} med den strängare), {len(contradicted)} avfärdade av motsägelser, {len(groups)} släktgrupper; "
          f"Jarlabanke q max {jar_q} (övre {jar_hi}); parstenar {len(pp & found)} av {len(pp)} "
          f"(missade: inget delat namn {out['validation']['parsten']['missed_shared_none']}, ett "
          f"{out['validation']['parsten']['missed_shared_one']}, två+ {out['validation']['parsten']['missed_shared_two_plus']}); Rundata-noterade {len(noted & found)} av {len(noted)}; "
          f"median {out['km_median_sure']} km; frön {seeds}")


if __name__ == "__main__":
    main()
