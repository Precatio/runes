"""Gudarna på kartan: ortnamnen med gudanamn i Svenskt ortnamnslexikon (låst plan
analysplaner/2026-11-17-gudarna-pa-kartan.md, sha256 e120282a). Läser de två kodarnas graderingar (utanför git, eftersom
de citerar SOL), knyter namnen till ISOF:s socknar och kör del A och proven B1–B2.
    .venv/bin/python utdata/asatro/analys.py"""
import collections
import csv
import hashlib
import json
import math
import os
import random
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLAN = os.path.join(ROOT, "analysplaner", "2026-11-17-gudarna-pa-kartan.md")
SHA = hashlib.sha256(open(PLAN, "rb").read()).hexdigest()
assert SHA.startswith("e120282a"), SHA
DL = "/Volumes/2TB/Antigrvity/Runes/downloads/asatro"
ISOF = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof"
OUT = os.path.dirname(os.path.abspath(__file__))
STRICT = {"avvisad": 0, "osäker": 1, "säker": 2}
TESTED = ("Tor", "Oden", "Frö")
REGION = {**{p: "Mälarlanden" for p in ("Uppland", "Södermanland", "Västmanland", "Närke")},
          **{p: "Västra Götaland" for p in ("Västergötland", "Dalsland")},
          **{p: "Östra Götaland" for p in ("Östergötland", "Småland", "Öland")},
          "Gotland": "Gotland",
          **{p: "Danska riket" for p in ("Skåne", "Blekinge", "Halland")},
          **{p: "Norska riket" for p in ("Bohuslän", "Jämtland", "Härjedalen")},
          **{p: "Norr" for p in ("Värmland", "Dalarna", "Gästrikland", "Hälsingland", "Medelpad", "Ångermanland",
                                 "Västerbotten", "Norrbotten", "Lappland")}}


def final_grades():
    """The stricter of the two coders' grades for each (id, god); the disagreements."""
    one = {(r["id"], r["gud"]): r for r in csv.DictReader(open(os.path.join(DL, "kodare1.csv"), encoding="utf-8"))}
    two = {(r["id"], r["gud"]): r["grad"].strip() for r in csv.DictReader(open(os.path.join(DL, "kodare2.csv"), encoding="utf-8"))}
    rows, disagree = [], []
    for k, r in one.items():
        if r["grad"] in ("ej ortnamn", "dubblett"):
            continue
        g2 = two[k]
        assert g2 in STRICT, (k, g2)
        g = min(r["grad"], g2, key=STRICT.get)
        if g2 != r["grad"]:
            disagree.append({"namn": r["namn"], "gud": r["gud"], "kodare1": r["grad"], "kodare2": g2, "slutlig": g})
        rows.append({"id": int(r["id"]), "namn": r["namn"], "gud": r["gud"], "grad": g})
    return rows, disagree


def parishes():
    prov = {p["id"]: p["name"] for p in json.load(open(os.path.join(ISOF, "provinces.json"), encoding="utf-8"))}
    out = collections.defaultdict(list)
    for p in json.load(open(os.path.join(ISOF, "parishes.json"), encoding="utf-8")):
        if p.get("latitude") is None:
            continue
        out[prov.get(p["province_id"])].append(p)
    return out


def norm(s):
    return re.sub(r"\s+(sn|socken|landsförsamling|stadsförsamling|fg)$", "", s.strip().lower())


def locate(entry, P):
    """The parish of a SOL entry (plan: "Läge"): a parish entry is its own parish; another entry the parish its head
    names; a härad named after a parish counts as that parish (the text names it). None without a parish."""
    head = entry["head"]
    land = next((p for p in REGION if re.search(r"\b" + re.escape(p) + r"\b", head)), None)
    if land is None:
        return None, None, "inget landskap"
    cands = P.get(land, [])
    kind = head.split(",")[0].strip()
    names = []
    if re.search(r"(^|, |samt |och )sn\b", head.split(".")[0]):
        names.append(entry["name"])
        m = re.search(r"\(([^)]*?) sn\)|\(([^)]*?) socken\)", head)
        if m:
            names.insert(0, m.group(1) or m.group(2))
    m = re.search(r"([A-ZÅÄÖ][\wåäöé\- ]+?) sn\b", head)
    if m:
        names.append(m.group(1))
    if kind.startswith("hd") and entry["name"].endswith("härad"):
        base = entry["name"].replace(" härad", "")
        if re.search(r"\b" + re.escape(base.replace("åkers", "åker")) + r"\b", entry["text"]):
            names.append(base)
    for nm in [ALIAS.get(x, x) for x in names]:
        for p in cands:
            # ISOF writes the parish in the genitive (Torsåkers sn); SOL's head sometimes does too (Askers sn)
            if norm(p["name"]) in (norm(nm), norm(nm) + "s") or norm(p["name"]) + "s" == norm(nm):
                return p, land, None
    return None, land, "ingen socken"


# SOL's spelling of a parish where ISOF spells it otherwise (reported in the result)
ALIAS = {"Åsheda": "Åseda"}


def chi2(table):
    rows = list(table)
    cols = sorted({c for r in rows for c in table[r]})
    n = sum(table[r][c] for r in rows for c in cols)
    rs = {r: sum(table[r].values()) for r in rows}
    cs = {c: sum(table[r][c] for r in rows) for c in cols}
    return sum((table[r][c] - rs[r] * cs[c] / n) ** 2 / (rs[r] * cs[c] / n) for r in rows for c in cols if rs[r] and cs[c])


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def stats(items):
    """(χ² of god × region, mean share of the three nearest neighbours with the same god)."""
    t = collections.defaultdict(collections.Counter)
    for x in items:
        t[x["gud"]][x["region"]] += 1
    same = []
    for i, x in enumerate(items):
        nn = sorted((km(x["pt"], y["pt"]), j) for j, y in enumerate(items) if j != i)[:3]
        same.append(sum(items[j]["gud"] == x["gud"] for _, j in nn) / 3)
    return chi2(t), sum(same) / len(same)


def perm_test(items, n=10000, seed=None):
    obs = stats(items)
    rng = random.Random(seed)
    labels = [x["gud"] for x in items]
    ge = [0, 0]
    null = [[], []]
    for _ in range(n):
        rng.shuffle(labels)
        s = stats([{**x, "gud": g} for x, g in zip(items, labels)])
        for k in (0, 1):
            null[k].append(s[k])
            ge[k] += s[k] >= obs[k] - 1e-12
    p = [(ge[k] + 1) / (n + 1) for k in (0, 1)]
    med = [sorted(null[k])[n // 2] for k in (0, 1)]
    return obs, p, med


def main():
    sol = json.load(open(os.path.join(DL, "isof_sol", "sol_entries.json"), encoding="utf-8"))
    rows, disagree = final_grades()
    P = parishes()
    named, dropped = [], []
    for r in rows:
        if r["grad"] == "avvisad":
            continue
        p, land, why = locate(sol[r["id"]], P)
        if p is None:
            dropped.append({"namn": r["namn"], "gud": r["gud"], "skäl": why})
            continue
        named.append({**r, "socken": p["name"], "landskap": land, "region": REGION[land],
                      "pt": (p["latitude"], p["longitude"]), "belagg": sol[r["id"]].get("year_first")})
    # A härad that counts as its parish counts once (plan): the same god in the same parish only once
    seen, uniq = set(), []
    for x in named:
        k = (x["gud"], x["socken"], x["landskap"])  # same-named parishes in different provinces are different places
        if k not in seen:
            seen.add(k)
            uniq.append(x)
    res = {"sha": SHA[:8], "traffar": len(rows), "oenighet": disagree, "utan_lage": dropped, "avvikelser": [
        "Stavningen Åsheda (SOL) matchas mot Åseda sn (ISOF); ISOF:s sockennamn står i genitiv och matchas så.",
        "Första körningen slog ihop socknar med samma namn i olika landskap (tre Torsåker, två Odensvi). Rättat innan "
        "resultatet användes; båda körningarna gav samma utfall: inget av proven håller."]}
    res["A_per_gud"] = {g: {"säker": sum(1 for x in uniq if x["gud"] == g and x["grad"] == "säker"),
                            "osäker": sum(1 for x in uniq if x["gud"] == g and x["grad"] == "osäker"),
                            "regioner": dict(collections.Counter(x["region"] for x in uniq if x["gud"] == g))}
                        for g in sorted({x["gud"] for x in uniq})}
    res["namn"] = [{k: x[k] for k in ("namn", "gud", "grad", "socken", "landskap", "region", "pt", "belagg")} for x in uniq]
    test = [x for x in uniq if x["gud"] in TESTED]
    seed = int(SHA[:8], 16)
    obs, p, med = perm_test(test, seed=seed)
    sure = [x for x in test if x["grad"] == "säker"]
    obs_s = stats(sure)
    holm = sorted(range(2), key=lambda i: p[i])
    adj, run = [0.0, 0.0], 0.0
    for rank, i in enumerate(holm):
        run = max(run, min(1.0, (2 - rank) * p[i]))
        adj[i] = run
    res["B"] = {"n": len(test), "n_saker": len(sure),
                "B1": {"chi2": obs[0], "p": p[0], "p_holm": adj[0], "median_null": med[0], "chi2_saker": obs_s[0],
                       "haller": bool(adj[0] < 0.05 and obs_s[0] > med[0])},
                "B2": {"samma_gud_bland_3_narmaste": obs[1], "p": p[1], "p_holm": adj[1], "median_null": med[1],
                       "varde_saker": obs_s[1], "haller": bool(adj[1] < 0.05 and obs_s[1] > med[1])},
                "tabell": {g: dict(collections.Counter(x["region"] for x in test if x["gud"] == g)) for g in TESTED}}
    json.dump(res, open(os.path.join(OUT, "resultat.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("traffar", "oenighet", "utan_lage", "A_per_gud", "B")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
