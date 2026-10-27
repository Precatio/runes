"""Länkmodellen (src/linking.py): länkar mellan runstenar som delar namn, prövade mot en nollmodell, släktgrupper,
händelser och gårdsnamn. Skriver data/links.json, som appen läser (Fynd per sten, Statistik (R)).
    .venv/bin/python -m scripts.link_entities [--null 200]"""
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--null", type=int, default=L.N_NULL)
    a = ap.parse_args()
    s = store()
    st = L.stones(s.inscriptions)
    w = L.weights(st)
    obs = L.links(st, w)
    null = L.null_scores(st, w, a.null)
    L.fdr(obs, null)
    strict = [dict(x) for x in obs]
    null_d = L.null_scores(st, w, a.null, level="district")
    L.fdr(strict, null_d)
    q_strict = {(x["a"], x["b"]): x["q"] for x in strict}
    display = {p["key"]: p["name"] for x in st.values() for p in x["persons"]}
    for x in obs:
        x["names"] = [display.get(k, k) if not k.startswith("plats:") else k[6:] for k in x["shared"]]
        x["q_district"] = q_strict[(x["a"], x["b"])]
        x["contradictions"] = L.contradictions(x, st)
        d = L.km(st[x["a"]], st[x["b"]])
        x["km"] = None if d is None else round(d, 1)
    obs.sort(key=lambda x: (x["q"], -x["score"]))
    # a link whose stones contradict each other (two fathers, dead then alive) is no family link, whatever its strength
    consistent = [x for x in obs if not x["contradictions"]]
    groups = L.groups(consistent, st)
    jar = [x for x in obs if x["a"] in JARLABANKE and x["b"] in JARLABANKE]
    pp = L.parsten_pairs(st)
    found = {(x["a"], x["b"]) for x in consistent if x["q"] < L.FDR_CUT}
    events, farms = defaultdict(list), defaultdict(list)
    for sg, x in st.items():
        for e in x["events"]:
            events[e].append(sg)
        for p in set(x["places"]):
            farms[p].append(sg)
    sure = [x for x in consistent if x["q"] < L.FDR_CUT]
    contradicted = [x for x in obs if x["q"] < L.FDR_CUT and x["contradictions"]]
    near = [x["km"] for x in sure if x["km"] is not None]
    out = {
        "computed_at": datetime.now(timezone.utc).isoformat(), "n_stones": len(st), "n_null": a.null,
        "fdr_cut": L.FDR_CUT, "n_links": len(obs), "null_mean": float(np.mean([len(z) for z in null])),
        "null_mean_district": float(np.mean([len(z) for z in null_d])),
        "n_sure": len(sure), "n_sure_district": sum(1 for x in consistent if x["q_district"] < L.FDR_CUT),
        "n_contradicted": len(contradicted),
        "km_median_sure": float(np.median(near)) if near else None,
        "share_sure_within_10km": (sum(1 for d in near if d <= 10) / len(near)) if near else None,
        "validation": {"jarlabanke": {"stones": list(JARLABANKE), "pairs": len(jar),
                                      "q_max": max((x["q"] for x in jar), default=None)},
                       "parsten": {"n": len(pp), "found": len(pp & found), "pairs": sorted(map(list, pp))}},
        "links": obs, "groups": groups,
        "events": {k: sorted(v) for k, v in sorted(events.items(), key=lambda kv: -len(kv[1]))},
        "farms": {k: sorted(v) for k, v in farms.items() if len(v) >= 2},
        "persons": {sg: [{k: p[k] for k in ("name", "role", "rel")} for p in x["persons"]] for sg, x in st.items() if x["persons"]},
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"{len(st)} stenar, {len(obs)} länkar (nollmodell {out['null_mean']:.0f} i landskapet, "
          f"{out['null_mean_district']:.0f} i häradet), {len(sure)} med q < {L.FDR_CUT} "
          f"({out['n_sure_district']} med den strängare), {len(contradicted)} avfärdade av motsägelser, {len(groups)} släktgrupper; "
          f"Jarlabanke q max {out['validation']['jarlabanke']['q_max']}; parstenar {len(pp & found)} av {len(pp)}")


if __name__ == "__main__":
    main()
