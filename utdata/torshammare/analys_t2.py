"""T2 kultplatssocknarna – tillägg 1 (analysplaner/2026-11-21-torshammare-tillagg-1-kultplatser.md, låst 5b64d88).
Skriver data/cache/torshammare/socknar.csv (till analys_t2.R) och utdata/torshammare/t2_beskrivning.json.
    .venv/bin/python utdata/torshammare/analys_t2.py && Rscript utdata/torshammare/analys_t2.R"""
import csv
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analys as a  # noqa: E402

DRAG = os.path.join(a.ROOT, "utdata", "asatro", "landskap_drag.csv")


def keys(name):
    f = a.fold(name)
    return {f, f[:-1] if f.endswith("s") and len(f) > 3 else f}


def main():
    bort = {ln.strip() for ln in open(os.path.join(HERE, "grind_bort.txt"), encoding="utf-8")
            if ln.strip() and not ln.startswith("#")}
    hs = [h for h in a.hammers() if h["Föremålsnummer"] not in bort]
    expo = [r for n in ("Kam", "Spänne") for r in a.rows(os.path.join(a.SRC, "exponering", f"{n}.csv"))
            if "Vikingatid" in r["Tidsperiod"]]
    drag = list(csv.DictReader(open(DRAG, encoding="utf-8")))
    cult_lands = {l for l, n in Counter(d["land"] for d in drag if d["cult"] == "1").items() if n >= 3}
    idx = {}
    for d in drag:
        for k in keys(d["name"]):
            idx.setdefault((k, d["land"]), []).append(d["id"])
    unmatched = Counter()

    def where(r):
        soc, land = r["Fyndplats, Socken"], r["Fyndplats, Landskap"].strip()
        ids = set()
        for k in keys(soc):
            ids.update(idx.get((k, land), []))
        if len(ids) == 1:
            return ids.pop()
        unmatched[(land, soc.split("|")[0].strip())] += 1
        return None

    H, Hr, Hh, E = Counter(), Counter(), Counter(), Counter()
    for h in hs:
        i = where(h)
        if i:
            H[i] += 1
            (Hr if a.kind(h) == "ring" else Hh)[i] += 1
    n_hammer_unmatched = sum(unmatched.values())
    for r in expo:
        i = where(r)
        if i:
            E[i] += 1
    hr = a.Harad()
    out = []
    for d in drag:
        if d["land"] == "Gotland" or d["land"] not in cult_lands or E[d["id"]] < 3:
            continue
        out.append({"id": d["id"], "socken": d["name"], "landskap": d["land"], "harad": hr.of(d["name"], d["land"]) or f"?{d['land']}",
                    "kult": d["cult"], "kult_saker": d["cult_saker"], "gravfalt": d["gravfalt"], "hog": d["hog"],
                    "exponering": E[d["id"]], "hammare": H[d["id"]], "ringar": Hr[d["id"]], "hangen": Hh[d["id"]],
                    "adelso": int(a.fold(d["name"]) == "adelsö")})
    os.makedirs(a.CACHE, exist_ok=True)
    with open(os.path.join(a.CACHE, "socknar.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    cult_ids = {d["id"]: d for d in drag if d["cult"] == "1"}
    res = {"socknar_i_modellen": len(out), "kultsocknar_i_modellen": sum(o["kult"] == "1" for o in out),
           "saker_i_modellen": sum(o["kult_saker"] == "1" for o in out), "hammare_i_modellen": sum(o["hammare"] for o in out),
           "harad_okant": sum(o["harad"].startswith("?") for o in out),
           "hammarposter_okopplade": n_hammer_unmatched, "landskap": sorted(cult_lands - {"Gotland"}),
           "hammare_i_kultsocknar_alla": [{"socken": cult_ids[i]["name"], "landskap": cult_ids[i]["land"], "säker": cult_ids[i]["cult_saker"] == "1",
                                           "poster": n, "ringar": Hr[i], "hängen": Hh[i], "exponering": E[i]}
                                          for i, n in H.most_common() if i in cult_ids]}
    json.dump(res, open(os.path.join(HERE, "t2_beskrivning.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
