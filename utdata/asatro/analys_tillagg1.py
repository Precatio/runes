"""Gudarna på kartan, tillägg 1: kultplatserna, väsendena och tingen i Svenskt ortnamnslexikon (låst tillägg
analysplaner/2026-11-17-gudarna-pa-kartan-tillagg-1.md, sha256 f7b339ef). Två blinda kodares graderingar (utanför git)
slås ihop; landsdelen tas ur SOL:s huvudrad; proven C1–C2.
    .venv/bin/python utdata/asatro/analys_tillagg1.py"""
import collections
import csv
import hashlib
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analys as main_plan  # noqa: E402

ROOT = main_plan.ROOT
PLAN = os.path.join(ROOT, "analysplaner", "2026-11-17-gudarna-pa-kartan-tillagg-1.md")
SHA = hashlib.sha256(open(PLAN, "rb").read()).hexdigest()
assert SHA.startswith("f7b339ef"), SHA
DL, OUT = main_plan.DL, main_plan.OUT
STRICT = main_plan.STRICT
GROUPS = ("vi", "harg", "hov", "al", "lund", "åker", "övrigt")
NOTES = ["När kodarna är oeniga om efterledet räknas namnet till 'övrigt' (planen säger inget om det fallet).",
         "Ett gudanamn ur huvudplanen som kodarna också gav kultplats får den strängare av de två slutliga graderna."]


def region_of(head):
    land = next((p for p in main_plan.REGION if re.search(r"\b" + re.escape(p) + r"\b", head)), None)
    return land, (main_plan.REGION[land] if land else None)


def merged():
    A = {r["id"]: r for r in csv.DictReader(open(os.path.join(DL, "t1_kodareA.csv"), encoding="utf-8"))}
    B = {r["id"]: r for r in csv.DictReader(open(os.path.join(DL, "t1_kodareB.csv"), encoding="utf-8"))}
    ids = [r["id"] for r in csv.DictReader(open(os.path.join(DL, "t1_indata.csv"), encoding="utf-8"))]
    assert set(A) == set(B) == set(ids), "kodarna ska ha samma uppslag som indata"
    out, cat_dis, grade_dis = {}, 0, 0
    for i in ids:
        a, b = A[i], B[i]
        ka, kb = a["kategori"].strip(), b["kategori"].strip()
        ga, gb = a["grad"].strip(), b["grad"].strip()
        assert ka in ("kultplats", "väsen", "ting", "ingen") and kb in ("kultplats", "väsen", "ting", "ingen"), (i, ka, kb)
        if ka != kb:
            cat_dis += 1
            continue
        if ka == "ingen":
            continue
        g = min(ga, gb, key=STRICT.get)
        grade_dis += ga != gb
        if g == "avvisad":
            continue
        ea, eb = a.get("efterled", "").strip(), b.get("efterled", "").strip()
        out[int(i)] = {"namn": a["namn"], "kategori": ka, "grad": g,
                       "efterled": ea if ea == eb and ea in GROUPS else "övrigt",
                       "sen": "ja" if "ja" in (a.get("sen", "").strip(), b.get("sen", "").strip()) else "nej"}
    return out, cat_dis, grade_dis


def perm_chi2(rows, key_a, key_b, n, seed):
    def tab(rs):
        t = collections.defaultdict(collections.Counter)
        for r in rs:
            t[r[key_a]][r[key_b]] += 1
        return main_plan.chi2(t)
    obs = tab(rows)
    rng = random.Random(seed)
    lab = [r[key_b] for r in rows]
    ge, null = 0, []
    for _ in range(n):
        rng.shuffle(lab)
        s = tab([{**r, key_b: v} for r, v in zip(rows, lab)])
        null.append(s)
        ge += s >= obs - 1e-12
    return obs, (ge + 1) / (n + 1), sorted(null)[n // 2]


def main():
    sol = json.load(open(os.path.join(DL, "isof_sol", "sol_entries.json"), encoding="utf-8"))
    coded, cat_dis, grade_dis = merged()
    # The gods of the main plan (final grades there) count as cult places
    gods, _ = main_plan.final_grades()
    for g in gods:
        if g["grad"] == "avvisad":
            continue
        if g["id"] in coded and coded[g["id"]]["kategori"] == "kultplats":
            coded[g["id"]]["grad"] = min(coded[g["id"]]["grad"], g["grad"], key=STRICT.get)
        elif g["id"] not in coded:
            coded[g["id"]] = {"namn": g["namn"], "kategori": "kultplats", "grad": g["grad"], "efterled": "övrigt", "sen": "nej"}
    entries = []
    for i, e in enumerate(sol):
        land, reg = region_of(e["head"])
        if reg is None:
            continue
        c = coded.get(i)
        entries.append({"id": i, "region": reg, "landskap": land,
                        "kult": "ja" if c and c["kategori"] == "kultplats" else "nej",
                        "kult_saker": "ja" if c and c["kategori"] == "kultplats" and c["grad"] == "säker" else "nej"})
    res = {"sha": SHA[:8], "noter": NOTES, "indata": 402, "oenig_kategori": cat_dis, "oenig_grad": grade_dis,
           "uppslag_med_landsdel": len(entries), "uppslag_utan_landsdel": len(sol) - len(entries)}
    reg_n = collections.Counter(x["region"] for x in entries)
    res["A"] = {}
    for kat in ("kultplats", "väsen", "ting"):
        items = [(i, c) for i, c in coded.items() if c["kategori"] == kat]
        per = collections.defaultdict(lambda: {"säker": 0, "osäker": 0})
        for i, c in items:
            _, reg = region_of(sol[i]["head"])
            per[reg or "utan landsdel"][c["grad"]] += 1
        res["A"][kat] = {"n": len(items), "per_landsdel": dict(per),
                         "andel_av_sol": {r: round((per[r]["säker"] + per[r]["osäker"]) / reg_n[r], 4) for r in reg_n}}
        if kat == "väsen":
            res["A"][kat]["sena"] = sum(1 for _, c in items if c["sen"] == "ja")
    res["A"]["efterled"] = dict(collections.Counter(c["efterled"] for c in coded.values() if c["kategori"] == "kultplats"))
    res["namn"] = []
    P = main_plan.parishes()
    for i, c in sorted(coded.items()):
        land, reg = region_of(sol[i]["head"])
        p, _, _ = main_plan.locate({**sol[i], "name": sol[i]["name"]}, P)
        res["namn"].append({**c, "landskap": land, "region": reg, "socken": p["name"] if p else None,
                            "pt": [p["latitude"], p["longitude"]] if p else None})
    seed = int(SHA[:8], 16)
    c1 = perm_chi2(entries, "region", "kult", 10000, seed)
    c1s = perm_chi2(entries, "region", "kult_saker", 2000, seed)[0]
    kult = [{"region": x["region"], "efterled": coded[x["id"]]["efterled"], "grad": coded[x["id"]]["grad"]}
            for x in entries if x["kult"] == "ja"]
    c2 = perm_chi2(kult, "region", "efterled", 10000, seed)
    c2s = perm_chi2([k for k in kult if k["grad"] == "säker"], "region", "efterled", 2000, seed)[0]
    ps = [c1[1], c2[1]]
    order = sorted(range(2), key=lambda i: ps[i])
    adj, run = [0.0, 0.0], 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (2 - rank) * ps[i]))
        adj[i] = run
    res["C1"] = {"chi2": c1[0], "p": c1[1], "p_holm": adj[0], "median_null": c1[2], "chi2_saker": c1s,
                 "haller": bool(adj[0] < 0.05 and c1s > c1[2]),
                 "andel_per_landsdel": {r: {"kult": sum(1 for x in entries if x["region"] == r and x["kult"] == "ja"),
                                            "n": reg_n[r]} for r in reg_n}}
    res["C2"] = {"n": len(kult), "chi2": c2[0], "p": c2[1], "p_holm": adj[1], "median_null": c2[2], "chi2_saker": c2s,
                 "haller": bool(adj[1] < 0.05 and c2s > c2[2]),
                 "tabell": {g: dict(collections.Counter(k["region"] for k in kult if k["efterled"] == g)) for g in GROUPS}}
    json.dump(res, open(os.path.join(OUT, "resultat_tillagg1.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "namn"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
