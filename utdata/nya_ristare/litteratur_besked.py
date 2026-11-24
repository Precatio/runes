"""Litteraturens besked per grupp (beskrivande), ur de GRANSKADE uttalandena (två granskare, båda bekräftade) och de
länkar som redan finns i Sveriges runinskrifter och Runor 2020 (facit 1).

Rättelse 2026-11-24 (granskning av rapportutkastet): ett uttalande om olika händer med fler än två stenar delades tidigare
upp i alla par, fast det oftast gäller en sten mot de andra (Stern 2013: U 855 är inte Arnfasts, men U 41, 43, 79 och 123
är det). Nu används uttalanden om olika händer bara när de gäller exakt två stenar, eller när granskarna anger att det är
en lista över olika namnbärare ("bärare"), där alla stenar verkligen är av olika ristare. Övriga räknas som tvetydiga.

    .venv/bin/python utdata/nya_ristare/litteratur_besked.py
Skriver utdata/nya_ristare/grupper_litteratur.json och litteratur_besked.json (sammanfattningen).
"""
import itertools
import json
import os
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CACHE = os.path.join(ROOT, "data", "cache", "hander")
SIG = re.compile(r"^(U|Sö|Ög|Vg|Sm|Öl|Vs|Nä|Gs|Hs|Ån|Vr|D|M|J|G|DR|N|Bo)\s*(\d+[A-Za-z]?)$")
THESES = {"kallstrom2007": "Källström 2007", "zilmer2005": "Zilmer 2005", "stern2013": "Stern 2013", "williams1990": "Williams 1990",
          "lagman1990": "Lagman 1990", "larsson2002": "Larsson 2002", "akerstrom2020": "Åkerström 2020",
          "pereswetoff2017": "Pereswetoff-Morath 2017"}


def norm(s):
    m = SIG.match((s or "").strip())
    return f"{m.group(1)} {m.group(2)}" if m else None


META = {x["id"].split("@")[0]: x.get("meta") or {} for x in json.load(open(os.path.join(CACHE, "lit_stallen.json"), encoding="utf-8"))}


def ref(src):
    kind, key = src.split(":", 1)
    if kind == "avhandling":
        return THESES.get(key, key)
    m = META.get(src, {})
    a = (m.get("authors") or ["?"])[0].split(",")[0]
    return f"{a} {m.get('year') or ''} ({'Fornvännen' if kind == 'fornvannen' else 'Futhark'})"


items = json.load(open(os.path.join(CACHE, "lit_granska.json"), encoding="utf-8"))
ver = {r["fil"]: r for r in json.load(open(os.path.join(CACHE, "lit_granskning.json"), encoding="utf-8")) if r}
same, diff, attr = defaultdict(set), defaultdict(set), defaultdict(set)
ambiguous = 0
for i, it in enumerate(items):
    r = ver.get(os.path.abspath(os.path.join(CACHE, "lit_granska", f"item_{i:03d}.txt")))
    vs = [v for v in (r or {}).get("granskare", []) if v]
    if not (len(vs) == 2 and all(v["bekraftad"] and v["styrka"] in ("säker", "trolig") for v in vs)):
        continue
    st = sorted({norm(s) for s in vs[0]["stenar"]} & {norm(s) for s in vs[1]["stenar"]} - {None})
    rel, src = it["claim"]["relation"], ref(it["källa"])
    if rel == "samma_hand":
        for a, b in itertools.combinations(st, 2):
            same[(a, b)].add(src)
    elif rel == "olika_hander":
        if len(st) == 2 or (len(st) > 2 and all("bärare" in v["skal"] for v in vs)):
            for a, b in itertools.combinations(st, 2):
                diff[(a, b)].add(src)
        elif len(st) > 2:
            ambiguous += 1
    else:
        for a in st:
            attr[a].add((it["claim"].get("ristare") or "").split()[0])

f1 = json.load(open(os.path.join(CACHE, "facit.json"), encoding="utf-8"))
known = defaultdict(set)
for l in f1["länkar"]:
    known[tuple(sorted((l["a"], l["b"])))].add(l["källa"])
mentioned = set()
for x in json.load(open(os.path.join(CACHE, "lit_stallen.json"), encoding="utf-8")):
    mentioned |= set(x["signa"])
for c in json.load(open(os.path.join(CACHE, "sri_kontexter.json"), encoding="utf-8")):
    mentioned.add(c["stone"])

G = json.load(open(os.path.join(HERE, "grupper.json"), encoding="utf-8"))
out = []
for g in G:
    st = sorted(g["stenar"])
    pairs = list(itertools.combinations(st, 2))
    k1 = [[a, b, sorted(known[(a, b)])] for a, b in pairs if (a, b) in known]
    sp = [[a, b, sorted(same[(a, b)])] for a, b in pairs if (a, b) in same]
    dp = [[a, b, sorted(diff[(a, b)])] for a, b in pairs if (a, b) in diff]
    names = Counter(n for s in st for n in {x for x in attr.get(s, ()) if x})
    shared = {n: k for n, k in names.items() if k >= 2}
    linked = bool(k1 or sp or shared)
    if linked and dp:
        v = "delvis motsagd"
    elif linked:
        v = "kopplad tidigare"
    elif dp:
        v = "motsagd"
    elif set(st) & mentioned:
        v = "ingen tidigare koppling"
    else:
        v = "ej omnämnd"
    out.append({"id": g["id"], "stenar": st, "typ": g["typ"], "underlag": g["underlag"], "besked": v,
                "sri_runor": k1, "samma_hand": sp, "olika_hander": dp, "gemensam_ristare": shared,
                "tillskrivningar": {s: sorted(attr[s]) for s in st if s in attr}})
json.dump(out, open(os.path.join(HERE, "grupper_litteratur.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
good = [x for x in out if x["typ"] == "okänd hand" and x["underlag"] == "gott"]
summary = {"alla": dict(Counter(x["besked"] for x in out)), "okänd_gott": dict(Counter(x["besked"] for x in good)),
           "okänd_gott_kopplad_sri_runor": sum(1 for x in good if x["sri_runor"]),
           "okänd_gott_kopplad_litteratur": sum(1 for x in good if not x["sri_runor"] and (x["samma_hand"] or x["gemensam_ristare"])),
           "olika_hander_par": len(diff), "olika_hander_tvetydiga_uttalanden": ambiguous}
json.dump(summary, open(os.path.join(HERE, "litteratur_besked.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False, indent=1))
for x in out:
    if "motsagd" in x["besked"]:
        print(x["id"], x["typ"], x["besked"], x["olika_hander"])
