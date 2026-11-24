"""Sammanställer arbetsflödets läsning av litteraturen (data/cache/hander/lit_lasning.json): kontrollen, facit 2 och
litteraturbeskedet per grupp.

    .venv/bin/python utdata/nya_ristare/litteratur_sammanstall.py
Skriver data/cache/hander/lit_facit2.json (utanför git) och utdata/nya_ristare/{lit_kontroll.json, grupper_litteratur.json}.
"""
import itertools
import json
import os
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CACHE = os.path.join(ROOT, "data", "cache", "hander")
RD = {r["signum"] for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
SIGRX = re.compile(r"^(U|Sö|Ög|Vg|Sm|Öl|Vs|Nä|Gs|Hs|Ån|Vr|D|M|J|G|DR|N|Bo)\s*(\d+[A-Za-z]?)$")


def norm(s):
    m = SIGRX.match((s or "").strip())
    return f"{m.group(1)} {m.group(2)}" if m else None


def strong(c):
    return c["vem"] == "författaren" and c["styrka"] in ("säker", "trolig")


def items(claims, keep=strong):
    """Mängden (stalle, relation, stenpar eller sten→ristare) för jämförelser."""
    out = set()
    for c in claims:
        if not keep(c):
            continue
        st = sorted({norm(s) for s in c["stenar"]} - {None})
        if c["relation"] in ("samma_hand", "olika_hander"):
            for a, b in itertools.combinations(st, 2):
                out.add((c["stalle"], c["relation"], a, b))
        else:
            for a in st:
                out.add((c["stalle"], "ristare", a, (c.get("ristare") or "").split()[0].lower()))
    return out


W = json.load(open(os.path.join(CACHE, "lit_lasning.json"), encoding="utf-8"))
main = [c for r in W["lasning"] for c in r["claims"]]
ctrl = [c for r in W["kontroll"] for c in r["claims"]]
ctrl_ids = set()
for r in W["kontroll"]:
    for l in open(r["fil"], encoding="utf-8"):
        if l.startswith("=== STÄLLE "):
            ctrl_ids.add(l.split()[2])
A = {x for x in items(main) if x[0] in ctrl_ids}
B = items(ctrl)
per = defaultdict(lambda: [set(), set()])
for x in A:
    per[x[0]][0].add(x[1:])
for x in B:
    per[x[0]][1].add(x[1:])
same_places = sum(1 for i in ctrl_ids if per[i][0] == per[i][1])
kontroll = {"ställen": len(ctrl_ids), "lika_ställen": same_places, "procent": round(100 * same_places / len(ctrl_ids), 1),
            "uttalanden_läsare": len(A), "uttalanden_kontroll": len(B), "gemensamma": len(A & B),
            "precision_mot_kontroll": round(len(A & B) / max(len(A), 1), 3), "täckning_mot_kontroll": round(len(A & B) / max(len(B), 1), 3)}
json.dump(kontroll, open(os.path.join(HERE, "lit_kontroll.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("kontroll:", kontroll)

# facit 2: par där författaren själv säger samma hand (säker/trolig); olika händer; tillskrivningar
same, diff, attr = defaultdict(list), defaultdict(list), defaultdict(list)
for c in main:
    st = sorted({norm(s) for s in c["stenar"]} - {None})
    st = [s for s in st if s in RD]
    src = c["stalle"].split("@")[0]
    if c["relation"] == "samma_hand" and strong(c):
        for a, b in itertools.combinations(st, 2):
            same[(a, b)].append(src)
    elif c["relation"] == "olika_hander" and strong(c):
        for a, b in itertools.combinations(st, 2):
            diff[(a, b)].append(src)
    elif c["relation"] in ("tillskrivning", "signerad") and c.get("ristare") and (strong(c) or c["relation"] == "signerad"):
        for a in st:
            attr[a].append((c["ristare"], src, c["relation"]))
f1 = json.load(open(os.path.join(CACHE, "facit.json"), encoding="utf-8"))
old = {tuple(sorted((l["a"], l["b"]))) for l in f1["länkar"]}
new_pairs = {k: v for k, v in same.items() if k not in old}
json.dump({"samma_hand": [{"a": a, "b": b, "källor": sorted(set(v))} for (a, b), v in sorted(same.items())],
           "nya_par": [{"a": a, "b": b, "källor": sorted(set(v))} for (a, b), v in sorted(new_pairs.items())],
           "olika_hander": [{"a": a, "b": b, "källor": sorted(set(v))} for (a, b), v in sorted(diff.items())],
           "tillskrivningar": {s: v for s, v in sorted(attr.items())}},
          open(os.path.join(CACHE, "lit_facit2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"samma hand: {len(same)} par ({len(new_pairs)} nya mot facit 1); olika händer: {len(diff)}; tillskrivna stenar: {len(attr)}")

# besked per grupp
G = json.load(open(os.path.join(HERE, "grupper.json"), encoding="utf-8"))
mentioned = set()
S = json.load(open(os.path.join(CACHE, "lit_stallen.json"), encoding="utf-8"))
for x in S:
    mentioned |= set(x["signa"])
out = []
for g in G:
    st = g["stenar"]
    pairs = list(itertools.combinations(sorted(st), 2))
    sp = [(a, b, sorted(set(same[(a, b)]))) for a, b in pairs if (a, b) in same]
    dp = [(a, b, sorted(set(diff[(a, b)]))) for a, b in pairs if (a, b) in diff]
    names = Counter()
    for s in st:
        for n in {x[0].split()[0] for x in attr.get(s, [])}:
            names[n] += 1
    shared = {n: k for n, k in names.items() if k >= 2}
    if sp or shared:
        verdict = "delvis motsagd" if dp else "stöds i litteraturen"
    elif dp:
        verdict = "motsagd"
    elif set(st) & mentioned:
        verdict = "ny (stenarna nämns, inte som samma hand)"
    else:
        verdict = "ej omnämnd"
    out.append({"id": g["id"], "typ": g["typ"], "underlag": g["underlag"], "stenar": st, "besked": verdict,
                "samma_hand_par": [[a, b, s] for a, b, s in sp], "olika_hander_par": [[a, b, s] for a, b, s in dp],
                "gemensam_ristare_i_litteraturen": shared,
                "tillskrivningar": {s: sorted({x[0] for x in attr[s]}) for s in st if s in attr}})
json.dump(out, open(os.path.join(HERE, "grupper_litteratur.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(Counter(x["besked"] for x in out))
print("okänd hand + gott underlag:", Counter(x["besked"] for x in out if x["typ"] == "okänd hand" and x["underlag"] == "gott"))
