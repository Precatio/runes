"""Näringar och hantverk per gammalt land och härad ur fornlämningsregistret (BESKRIVANDE underlag för serien De gamla
landen, inget prov): andelen av alla registrerade lämningar i enheten som är järnframställning, fångstgropar, åkrar, båt-
och hamnlämningar osv, jämfört med resten av landskapet och – eftersom registret inventerats länsvis – med resten av
landskapet inom samma län. Skriver naringar.json och naringar.md.
    PYTHONPATH=. .venv/bin/python utdata/landprofiler/naringar.py
Indata: /Volumes/2TB/tmp/landprofil/alla_pt.csv, alla_pg.csv, alla_ln.csv (ogr2ogr-uttag ur lamningar_sverige.gpkg)."""
import csv
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(10 ** 9)
src = open(os.path.join(HERE, "data.py")).read()
g = {"__name__": "naringar", "__file__": os.path.join(HERE, "data.py")}
exec(compile(src[:src.index("# ---- 1–3 the stones")], "data_head", "exec"), g)
nearest, unit_cols = g["nearest"], g["unit_cols"]

CAT = {
    "järnframställning": {"Blästbrukslämning", "Blästplats"},
    "fångstgropar": {"Fångstgrop", "Fångstgropssystem", "Fångstanläggning övrig", "Fångstgård"},
    "åker och röjning": {"Fossil åker", "Område med fossil åkermark", "Röjningsröse"},
    "hägnader": {"Hägnad", "Hägnadssystem"},
    "båtar och hamnar": {"Båtlänning", "Hamnanläggning", "Hamnområde"},
    "boplatser": {"Boplats", "Boplatsområde", "Boplatsgrop", "Boplatsvall", "Boplatslämning övrig"},
    "husgrunder (förhist./medeltid)": {"Husgrund, förhistorisk/medeltida"},
    "tomtningar": {"Tomtning"},
    "offer och kult": {"Offerkast", "Offerplats", "Källa med tradition", "Labyrint"},
    "hällristningar": {"Hällristning", "Bildristning"},
    "gravar": {"Gravfält", "Hög", "Stensättning", "Röse", "Grav markerad av sten/block", "Stenkrets/stenrad", "Flatmarksgrav"},
    "runristningar": {"Runristning"},
    "kolning (mest efter 1500)": {"Kolningsanläggning"},
    "fäbodar (mest efter 1500)": {"Fäbod"},
}
TYP2CAT = {t: c for c, ts in CAT.items() for t in ts}

rows, seen = [], set()
for f in ("alla_pt.csv", "alla_pg.csv", "alla_ln.csv"):
    for r in csv.DictReader(open("/Volumes/2TB/tmp/landprofil/" + f)):
        if r["uuid"] in seen or not r.get("X"):
            continue
        seen.add(r["uuid"])
        p = nearest((float(r["Y"]), float(r["X"])))
        if p is None:
            continue
        u = unit_cols(p)
        rows.append((u["province"], u["region"], u["harad"], u["county"], TYP2CAT.get(r["lamningstyp"])))
print("lämningar med socken i Svealand/Götaland:", len(rows))

SPLIT = {"U", "Sm", "G"}
tot = defaultdict(Counter)   # (level, unit) -> Counter(cat) ; "_all" total
for pv, reg, h, cty, c in rows:
    keys = [("landskap", pv), ("härad", h)] + ([("land", reg)] if pv in SPLIT and reg != pv else [])
    for k in keys:
        tot[k]["_all"] += 1
        if c:
            tot[k][c] += 1
    tot[("lan", pv, cty)]["_all"] += 1
    if c:
        tot[("lan", pv, cty)][c] += 1
    tot[("hlan", h, cty)]["_all"] += 1
    if c:
        tot[("hlan", h, cty)][c] += 1
    if pv in SPLIT and reg != pv:
        tot[("llan", reg, cty)]["_all"] += 1
        if c:
            tot[("llan", reg, cty)][c] += 1

unit_prov, unit_cty = {}, defaultdict(Counter)
for pv, reg, h, cty, c in rows:
    unit_prov[("härad", h)] = pv
    unit_cty[("härad", h)][cty] += 1
    if pv in SPLIT and reg != pv:
        unit_prov[("land", reg)] = pv
        unit_cty[("land", reg)][cty] += 1

out = []
for key, pv in unit_prov.items():
    n = tot[key]["_all"]
    if n < 200:
        continue
    cty = unit_cty[key].most_common(1)[0][0]
    rest = tot[("landskap", pv)]
    inlan = tot[("hlan" if key[0] == "härad" else "llan", key[1], cty)]
    lanrest = tot[("lan", pv, cty)]
    prof = {}
    for c in CAT:
        a, A = tot[key][c], n
        b, B = rest[c] - a, rest["_all"] - A
        ai, Ai = inlan[c], inlan["_all"]
        bi, Bi = lanrest[c] - ai, lanrest["_all"] - Ai
        prof[c] = {"n": a, "share": a / A, "share_rest": (b / B) if B else None,
                   "share_in_county": (ai / Ai) if Ai else None, "share_rest_county": (bi / Bi) if Bi else None}
    out.append({"level": key[0], "unit": key[1], "province": pv, "county": cty, "n": n, "profile": prof})
json.dump(out, open(os.path.join(HERE, "naringar.json"), "w"), ensure_ascii=False, indent=0)


def ratio(x, y):
    return x / y if (x is not None and y) else None


L = ["# Näringar och hantverk per land (beskrivande, fornlämningsregistret)", "",
     "Andel av alla registrerade lämningar i enheten; i parentes resten av landskapet. Kvot = enhetens andel delad med "
     "restens, inom samma län (registret är inventerat länsvis). Visar kategorier där kvoten inom länet är ≥ 2 eller ≤ 0,5 "
     "och enheten har minst 20 lämningar i kategorin. Beskrivande underlag, inte prövade fynd.", ""]
for o in sorted(out, key=lambda o: (o["level"] != "land", o["province"], o["unit"])):
    lines = []
    for c, p in o["profile"].items():
        r = ratio(p["share_in_county"], p["share_rest_county"])
        if r is not None and p["n"] >= 20 and (r >= 2 or r <= 0.5):
            lines.append(f"{c} {100 * p['share']:.1f} % ({100 * (p['share_rest'] or 0):.1f} %), kvot inom län {r:.1f}")
    if lines:
        L.append(f"- **{o['unit']}** ({o['level']}, {o['province']}, {o['n']} lämningar): " + "; ".join(lines))
open(os.path.join(HERE, "naringar.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L[:60]))
