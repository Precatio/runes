"""När korset kom till gudarnas platser: runstenarna i kultplatssocknarna (låst plan
analysplaner/2026-11-17-korset-och-kultplatserna.md, sha256 90e7af35). Kultplatsnamnen ur tillägg 1
(resultat_tillagg1.json), runstenarna ur Rundata, socknarna ur ISOF; proven K1–K3.
    .venv/bin/python utdata/asatro/korset.py"""
import collections
import hashlib
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import analys as main_plan  # noqa: E402
from src import nordic, question  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-17-korset-och-kultplatserna.md")
SHA = hashlib.sha256(open(PLAN, "rb").read()).hexdigest()
assert SHA.startswith("90e7af35"), SHA
SAMI = {"Áhkká", "Nammásj", "Unna Sájvva", "Tarradalen"}
PROV = {"U": "Uppland", "Sö": "Södermanland", "Ög": "Östergötland", "Öl": "Öland", "Vg": "Västergötland", "Sm": "Småland",
        "G": "Gotland", "Vs": "Västmanland", "Gs": "Gästrikland", "Nä": "Närke", "Hs": "Hälsingland", "M": "Medelpad",
        "Bo": "Bohuslän", "Vr": "Värmland", "D": "Dalarna", "J": "Jämtland"}
NOTES = ["Socknar utan runstenar har ingen halva i Pröva en egen frågas indelning; de delas växelvis A/B i namnordning "
         "inom landskapet (planen säger bara 'samma halvor')."]


def key(name):
    return main_plan.norm(name)


def main():
    t1 = json.load(open(os.path.join(HERE, "resultat_tillagg1.json"), encoding="utf-8"))
    P = main_plan.parishes()
    # The cult parishes: (landskap, parish key) -> best grade
    cult = {}
    for x in t1["namn"]:
        if x["kategori"] != "kultplats" or not x.get("socken") or x["namn"] in SAMI:
            continue
        k = (x["landskap"], key(x["socken"]))
        if cult.get(k) != "säker":
            cult[k] = x["grad"]
    # The parishes of each province, by key
    parishes = {land: {key(p["name"]): p["name"] for p in ps} for land, ps in P.items()}
    # The runestones and their parishes
    from api.rundata import store
    from api.routers.orthography import model as orth
    from src import r_bridge
    D = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
    se = [r for r in D if nordic.is_runestone(r) and nordic.land_of(r) == "sverige"]
    assert len(se) == 2321
    rows = r_bridge.corpus_rows(store().inscriptions, orth().names)
    half = question.halves(rows)
    stones, unmatched = [], 0
    for r in se:
        land = PROV.get(r["signum"].split()[0])
        pk = key(r.get("parish") or "")
        names = parishes.get(land, {})
        hit = pk if pk in names else (pk[:-1] if pk.endswith("s") and pk[:-1] in names else
                                      (pk + "s" if pk + "s" in names else None))
        if not land or hit is None:
            unmatched += 1
            continue
        ft = nordic.features(r)
        pat = nordic.patterns(r, ft) if ft is not None else {}
        stones.append({"signum": r["signum"], "land": land, "parish": hit, "cult": (land, hit) in cult,
                       "cult_sure": cult.get((land, hit)) == "säker", "half": half.get(r["signum"]),
                       "text": ft is not None, "kristen": pat.get("kristen"), "bon": pat.get("bon"),
                       "hednisk": pat.get("hednisk"), "bin": nordic.bin_of(nordic.year_of(r))})
    per_land = collections.Counter(s["land"] for s in stones)
    cult_per_land = collections.Counter(l for (l, _) in cult)
    lands = sorted(l for l in per_land if per_land[l] >= 30 and cult_per_land[l] >= 3)
    res = {"sha": SHA[:8], "noter": NOTES, "stenar_matchade": len(stones), "stenar_omatchade": unmatched,
           "provlandskap": lands, "kultsocknar": {l: cult_per_land[l] for l in lands},
           "socknar": {l: len(parishes[l]) for l in lands}}

    # ---- the halves of the parishes (K1): the stones' halves; parishes without stones alternately
    phalf = {}
    for s in stones:
        if s["half"]:
            phalf.setdefault((s["land"], s["parish"]), s["half"])
    for l in lands:
        rest = sorted(k for k in parishes[l] if (l, k) not in phalf)
        for i, k in enumerate(rest):
            phalf[(l, k)] = "A" if i % 2 == 0 else "B"

    def k1(sure_only=False, which=None):
        """Observed stones in the cult parishes / expected at the province's mean, over the test provinces."""
        cnt = collections.Counter((s["land"], s["parish"]) for s in stones)
        units = [(l, k) for l in lands for k in parishes[l] if which is None or phalf[(l, k)] == which]
        lab = {u: (cult.get(u) == "säker" if sure_only else u in cult) for u in units}
        def stat(lab):
            obs = exp = 0.0
            for l in lands:
                us = [u for u in units if u[0] == l]
                if not us:
                    continue
                mean = sum(cnt[u] for u in us) / len(us)
                for u in us:
                    if lab[u]:
                        obs += cnt[u]
                        exp += mean
            return obs / exp if exp else None
        obs = stat(lab)
        rng = random.Random(int(SHA[:8], 16))
        by = collections.defaultdict(list)
        for u in units:
            by[u[0]].append(u)
        ge = 0
        n = 10000
        lo_hi = []
        for _ in range(n):
            new = {}
            for l, us in by.items():
                v = [lab[u] for u in us]
                rng.shuffle(v)
                new.update(zip(us, v))
            s_ = stat(new)
            lo_hi.append(s_)
            ge += abs(s_ - 1) >= abs(obs - 1) - 1e-12  # two-sided around 1 (no difference)
        k_cult = sum(cnt[u] for u in units if lab[u])
        n_cult = sum(lab[u] for u in units)
        return {"kvot": obs, "p": (ge + 1) / (n + 1), "stenar_i_kultsocknar": k_cult, "kultsocknar": n_cult,
                "socknar": len(units), "stenar": sum(cnt[u] for u in units)}

    def mh(outcome, strata_key, sub, sure_only=False):
        st = collections.defaultdict(lambda: [0, 0, 0, 0])
        tot = [0, 0, 0, 0]
        for s in sub:
            y = s[outcome]
            if y is None:
                continue
            c = s["cult_sure"] if sure_only else s["cult"]
            i = (0 if y else 1) if c else (2 if y else 3)
            st[strata_key(s)][i] += 1
            tot[i] += 1
        or_, p, used = nordic.mantel_haenszel([tuple(v) for v in st.values()])
        return {"kult_ja": tot[0], "kult_n": tot[0] + tot[1], "ovr_ja": tot[2], "ovr_n": tot[2] + tot[3],
                "or_mh": or_, "p": p, "skikt": used}

    base = [s for s in stones if s["land"] in lands]
    k2_rows = [{**s, "y": None if not s["text"] or s["bin"] is None else s["kristen"]} for s in base]
    k3_rows = [{**s, "y": None if s["bin"] is None else int(s["bin"] == "sen")} for s in base]
    K1 = k1()
    K2 = mh("y", lambda s: (s["land"], s["bin"]), k2_rows)
    K3 = mh("y", lambda s: s["land"], k3_rows)
    ps = [K1["p"], K2["p"], K3["p"]]
    order = sorted(range(3), key=lambda i: ps[i])
    adj, run = [0.0] * 3, 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (3 - rank) * ps[i]))
        adj[i] = run
    K1["p_holm"], K2["p_holm"], K3["p_holm"] = adj
    # halves and secure-only
    K1["halvor"] = {h: k1(which=h) for h in ("A", "B")}
    K1["saker"] = k1(sure_only=True)
    up = lambda x: x["kvot"] > 1  # noqa: E731
    K1["haller"] = bool(K1["p_holm"] < 0.05 and all(up(K1["halvor"][h]) == up(K1) and K1["halvor"][h]["p"] < 0.05
                                                     for h in "AB") and up(K1["saker"]) == up(K1))
    for K, rows_, sk in ((K2, k2_rows, lambda s: (s["land"], s["bin"])), (K3, k3_rows, lambda s: s["land"])):
        K["halvor"] = {h: mh("y", sk, [s for s in rows_ if s["half"] == h]) for h in ("A", "B")}
        K["saker"] = mh("y", sk, rows_, sure_only=True)
        dirn = (K["or_mh"] or 1) > 1
        def ok(x):
            if x["or_mh"] is None or (x["or_mh"] > 1) != dirn:
                return False
            return x["kult_ja"] + x["ovr_ja"] < 10 or (x["p"] is not None and x["p"] < 0.05)
        K["haller"] = bool(K["p_holm"] < 0.05 and all(ok(K["halvor"][h]) for h in "AB")
                           and K["saker"]["or_mh"] is not None and (K["saker"]["or_mh"] > 1) == dirn)
    res["K1"], res["K2"], res["K3"] = K1, K2, K3
    # descriptive: prayer, the pagan stones, the cult parishes with most stones
    res["bon"] = mh("y", lambda s: (s["land"], s["bin"]),
                    [{**s, "y": None if not s["text"] or s["bin"] is None else s["bon"]} for s in base])
    res["hedniska"] = [{"signum": s["signum"], "socken": parishes[s["land"]][s["parish"]], "kultsocken": s["cult"]}
                       for s in stones if s["hednisk"]]
    cnt = collections.Counter((s["land"], s["parish"]) for s in stones if s["cult"])
    res["flest"] = [{"socken": parishes[l][k], "landskap": l, "stenar": n} for (l, k), n in cnt.most_common(12)]
    json.dump(res, open(os.path.join(HERE, "resultat_korset.json"), "w"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: res[k] for k in ("stenar_matchade", "stenar_omatchade", "provlandskap", "kultsocknar", "socknar")},
                     ensure_ascii=False))
    for k in ("K1", "K2", "K3"):
        print(k, json.dumps({a: b for a, b in res[k].items() if a not in ("halvor", "saker")}, ensure_ascii=False, default=float))
        print("   halvor", json.dumps(res[k]["halvor"], ensure_ascii=False, default=float)[:400])
        print("   säker", json.dumps(res[k]["saker"], ensure_ascii=False, default=float)[:300])
    print("bön", res["bon"]); print("hedniska", res["hedniska"]); print("flest", res["flest"])


if __name__ == "__main__":
    main()
