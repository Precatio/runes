"""Vad prisas på runstenarna? Varje vikingatida runsten (src/inscription_types._is_runestone: period V, objekt
'runsten', fragment medräknade, hela Norden) söks igenom i Rundatas fornvästnordiska normalisering
(normalization_ows, samma språkform som Eddans texter) efter uttryck som säger något om en människas egenskaper,
förmågor eller gärningar. Kategorierna och mönstren står nedan och är satta före räkningen; varje träff skrivs ut i
sitt sammanhang (dygder_runstenar_kwic.txt) så att den kan granskas.

Räknas per sten (en sten med två 'góðan' räknas en gång per kategori). Utdata: dygder_runstenar.json.
    .venv/bin/python utdata/dygder/dygder_runstenar.py
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src.inscription_types import _is_runestone  # noqa: E402

HERE = os.path.dirname(__file__)

# Egenskaper som tillskrivs en människa. Mönstren gäller normalization_ows (ǫ skrivs ô); \b = ordgräns.
EGENSKAPER = {
    # det allmänna omdömet: 'góðr' (god), oftast i 'góðan dreng/þegn' eller 'fôður góðan'
    "god": r"\bgóð(an|r|a|ir|rar|um)?\b(?!\s+(?:matar))",
    # samhällsidealen: drengr (den pålitlige, hedervärde mannen; även unga män i följe) och þegn (fri jordägare/man)
    "drengr": r"\bdreng(r|s|i|ir|ja|jar)?\b|\bdrengila\b",
    "þegn": r"\bþegn(s|a|ar)?\b",
    # givmildhet och gästfrihet
    "givmild": r"\bmild(an|r|i|astr)\b|\bmatar\s+góð\w*|\bgóð\w*\s+matar\b|\bmildr?\s+matar\b|\bmildastr\s+matar\b",
    # ordet: vältalighet, att kunna ge råd, vishet
    # ('ráði sá kunni' är INTE med: det är ristarformeln 'tyde den som kan')
    "ord_och_rad": r"\borða\b|\bmáls\s*risinn\b|\bmálsrisinn\b|\bmálspak\w*|\bráðspak\w*"
                   r"|\bvitran\b|\bspak(r|a|an)\b|\bfróð(an|r)\b",
    # skicklighet i ett hantverk eller en färdighet
    "skicklig": r"\bslœgjastr\b|\bhônnurst\b|\bkunni\s+vel\b|\bhagr\b",
    # mod och krigarideal som EGENSKAP (djärv, käck, stark); stupad i strid räknas under gärningar
    "modig": r"\bdjarf(r|an|s)?\b|\bfrœkn(an|ar)?\b|\bþróttar\s+þegn\b|\bhraust\w*|\bfló\s+eigi\b|\beigi\s+fló\b",
    # snjallr: 'duktig, skicklig, käck' – tvetydigt mellan förmåga och mod, därför för sig
    "duktig": r"\b(hug)?snjall(an|ir|ara|a|astir|r)?\b",
    # det bästa och främsta
    "framst": r"\bbeztr?\b|\bbezt(an|ra|i|a)\b|\bfyrstr\b|\bœztr\b",
    # trohet och omsorg om de sina
    "trohet": r"\bholl(an|r)\b|\btrúfast\w*|\bheldu\s+sína\s+húskarla\s+ve",
    # heder: utan skam, inte en niding ('óníðingr', 'óneiss'), en duglig man ('hæfr')
    "heder": r"\bóníðing\w*|\bóneis\w*|\bhæf(an|r)\b|\balgóð\w*",
    # kvinnans husfru-ideal
    "husfru": r"\bhúsfreyj\w*|\bhúsfrú\w*|\bhýfreyj\w*",
}

GARNINGAR = {
    # resor, krig och handel
    "resa_osterut": r"\bGrikk\w*|\bGôrð\w*|\bGarð\w*|\bSerk\w*|\baustr\w*|\bEistland\w*|\bVirland\w*|\bSemgal\w*|\bSeimgal\w*",
    "resa_vasterut": r"\bEngland\w*|\bvestr\w*|\bLundún\w*|\bBaðum\b|\bÍrland\w*",
    "strid": r"\bfell\b|\borrost\w*|\bbarð(i|ist|ust|a)\b|\bí\s+liði\b|\bliðs\s+forungi\b|\bvíking\w*|\bherferð\w*|\bdrepinn\b|\bvígi\b",
    "handel_och_skepp": r"\bgulli\s+skip?ti\b|\bkaupm\w*|\bskipari\w*|\bstýrimann\w*|\bknerri\b|\bsiglt?\b|\bsigldi\b",
    # gärningar för andra och för minnet
    "bro_och_vag": r"\bbrú\w*|\bbro\b|\bvegr?\b|\bvegi\b|\bryðja\b|\bryðr\b",
    "gard_och_arv": r"\bbónd(a|i)?\s+beztr\b|\bbjó\b|\bbú\w*\b|\bátti\b|\barf\w*|\beignað\w*|\bóðal\w*",
    "kristen_bon": r"\bGuð\b|\bKrist\w*|\bsál\w*|\bônd\b|\bGuðs\b|\bMaría\b|\bMichael\b|\bMikjáll\w*",
    "minnet_varar": r"\bæ\s+mun\b|\buppi\s+vera\b|\blengi\s+mun\b|\bmunu\s+minni\b|\bmeðan\s+mannkind\b|\bmeð\s+steinn\s+lifir\b",
}

CAT = {**{k: re.compile(v, re.I) for k, v in EGENSKAPER.items()},
       **{k: re.compile(v, re.I) for k, v in GARNINGAR.items()}}
# names are marked with a quote in normalization_ows ("Góði, "Dreng): never count a name as a quality
NAMN = re.compile(r'"\S+')


# träffar som granskats och inte är egenskaper hos en människa
UNDANTAG = {("framst", "U 719"),  # 'þann heim bezta kristnum' = paradiset
            ("framst", "Sö 176"),  # 'bôrn sex, bezt' – oklart vad som avses
            ("givmild", "U 971")}  # 'Mildi(?)' osäker läsning, troligen namn/bön


def text(r):
    t = re.sub(r"[\[\]\(\)?]", "", r.get("normalization_ows") or "")  # [g]ó[ð]r → góðr
    return NAMN.sub(" ", t)


def land(r):
    p = r["signum"].split(" ")[0]
    return "Danmark" if p in ("DR",) else "Norge" if p in ("N",) else "Sverige" if p in (
        "U", "Sö", "Ög", "Vg", "Sm", "Öl", "Gs", "Hs", "M", "J", "Nä", "Vs", "D", "Bo", "Hälsingland", "G", "Vr", "Lp",
        "Ds", "Hr") else "övrigt"


rs = [r for r in store().inscriptions if _is_runestone(r)]
per_sten = {}
kwic = defaultdict(list)
for r in rs:
    t = text(r)
    hits = set()
    for k, rx in CAT.items():
        if (k, r["signum"]) in UNDANTAG:
            continue
        for m in rx.finditer(t):
            hits.add(k)
            kwic[k].append(f'{r["signum"]}: …{t[max(0, m.start() - 50):m.end() + 50].strip()}…')
    per_sten[r["signum"]] = hits

n = len(rs)
egen = [s for s, h in per_sten.items() if h & set(EGENSKAPER)]
ut = {
    "n_runstenar": n,
    "n_med_egenskap": len(egen),
    "egenskaper": {k: sum(1 for h in per_sten.values() if k in h) for k in EGENSKAPER},
    "garningar": {k: sum(1 for h in per_sten.values() if k in h) for k in GARNINGAR},
    "per_land": {},
}
by_land = defaultdict(list)
for r in rs:
    by_land[land(r)].append(per_sten[r["signum"]])
for L, hs in by_land.items():
    ut["per_land"][L] = {"n": len(hs), **{k: sum(1 for h in hs if k in h) for k in CAT}}

json.dump(ut, open(os.path.join(HERE, "dygder_runstenar.json"), "w"), ensure_ascii=False, indent=1)
with open(os.path.join(HERE, "dygder_runstenar_kwic.txt"), "w", encoding="utf-8") as f:
    for k in CAT:
        f.write(f"\n===== {k} ({len(kwic[k])} träffar)\n")
        f.write("\n".join(kwic[k]) + "\n")
print(json.dumps({k: ut[k] for k in ("n_runstenar", "n_med_egenskap", "egenskaper", "garningar")}, ensure_ascii=False, indent=1))
