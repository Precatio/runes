"""Skånes vikingatida runstenar i Rundata 3.1: vad de säger, vilka ord och formler som bär dem, och hur de står mot
Danmarks och de svenska landskapens stenar. Beskrivande underlag till artikeln om Skåne (build_skane.py); inga tester.
Skriver utdata/skane/skane.json.
    PYTHONPATH=. .venv/bin/python utdata/skane/skane_stenar.py"""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402

ins = store().inscriptions


def region(r):
    s = r["signum"].split()[0]
    if s == "DR":
        d = (r.get("district") or "") + " " + (r.get("municipality") or "")
        for name in ("Skåne", "Halland", "Blekinge", "Bornholm"):
            if name in d:
                return name
        return "Danmark"  # Jylland, Fyn, Sjælland, Lolland-Falster, Slesvig
    return {"Vg": "Västergötland", "Ög": "Östergötland", "Sm": "Småland", "Öl": "Öland", "U": "Uppland", "Sö": "Södermanland"}.get(s)


def is_vik_runestone(r):
    return (r.get("period") or "") == "V" and "runsten" in (r.get("object") or "").lower()


stones = [r for r in ins if is_vik_runestone(r) and region(r)]
groups = {}
for r in stones:
    groups.setdefault(region(r), []).append(r)
sk = groups["Skåne"]
norm = lambda r: (r.get("normalization") or "").replace("ð", "þ").replace("Ð", "Þ")  # noqa: E731  Danish and Swedish normalisation agree on þ then
T = {
    "ræisti/satti själv": r"\b(res[þt][iu]|ræist[iu]|ræisþ[iu]|satt[iu]|setti|sattu|ristu|raistu)\b",
    "lät (let) göra": r"\blet[u]?\b",
    "dræng": r"dræng|drængiaR|drængs",
    "þegn": r"þ[æe]gn|þiagn",
    "felagi": r"felag",
    "harþa goþan": r"har[þð]a go[þð]an|harþa go[þð]a",
    "goþan/goþr": r"\bgo[þð]a?n?\b|\bgoþr\b|\bgoþa\b",
    "Guð": r"\bGu[þð]\b|\bKrist",
    "bortom bygden": r"\b[wv][æe]str\b|\baustr\b|\bnor\b|Grikk|Englandi|Lundun|Gotland|wikingu|Sweþiuþu|Upsal",
    "drottin/hemþegn": r"drottin|drotin|hemþæg|heimþeg|himþigi",
    "bonda": r"\bbonda\b|\bboanda\b|\bbomanna\b|\blandmænnr\b",
    "kumbl": r"kumbl",
}


def share(rs, pat):
    n = sum(bool(re.search(pat, norm(r), re.I)) for r in rs)
    return {"n": n, "share": n / len(rs) if rs else None}


regions = ["Skåne", "Danmark", "Bornholm", "Västergötland", "Småland", "Östergötland", "Södermanland", "Uppland"]
cmp = {name: {reg: share(groups[reg], pat) for reg in regions} for name, pat in T.items()}
cmp["RAK"] = {reg: {"n": sum(r.get("style") == "RAK" for r in groups[reg]), "share": sum(r.get("style") == "RAK" for r in groups[reg]) / len(groups[reg])} for reg in regions}
cmp["kors"] = {reg: {"n": sum(bool(r.get("cross_form")) for r in groups[reg]), "share": sum(bool(r.get("cross_form")) for r in groups[reg]) / len(groups[reg])} for reg in regions}
dating = {reg: dict(Counter((r.get("dating") or "?").replace("V ", "", 1) for r in groups[reg]).most_common()) for reg in ("Skåne", "Danmark")}
efter = lambda d: d.startswith("V efter-Jelling") or d.startswith("V kristen efter-Jelling")  # noqa: E731
listed = lambda pat: sorted((r["signum"] for r in sk if re.search(pat, norm(r), re.I)), key=lambda s: (len(s), s))  # noqa: E731
out = {
    "n": {reg: len(groups[reg]) for reg in regions},
    "skane": [{"signum": r["signum"], "place": r["place"], "harad": (r.get("district") or "").split(",")[0], "dating": r.get("dating"),
               "style": r.get("style"), "cross": bool(r.get("cross_form")), "lost": r["flags"]["lost"], "lat": r.get("lat"), "lon": r.get("lon"),
               "normalization": r.get("normalization"), "translation_en": r.get("translation_en")} for r in sk],
    "harader": dict(Counter((r.get("district") or "").split(",")[0] for r in sk).most_common()),
    "dating": dating,
    "efter_jelling": {"Skåne": sum(efter(r.get("dating") or "") for r in sk), "Danmark": sum(efter(r.get("dating") or "") for r in groups["Danmark"])},
    "lost": sum(r["flags"]["lost"] for r in sk),
    "compare": cmp,
    "lists": {k: listed(p) for k, p in T.items()},
    "no_king_no_denmark": {"kunung": listed(r"kunung|konung"), "danmark": listed(r"[Dd]anm")},
}
json.dump(out, open(os.path.join(ROOT, "utdata", "skane", "skane.json"), "w"), ensure_ascii=False, indent=1)
print("stenar:", out["n"], "| Skåne förlorade:", out["lost"], "| efter-Jelling:", out["efter_jelling"])
print("härader:", out["harader"])
for name in list(T) + ["RAK", "kors"]:
    print(f"{name:20}", " | ".join(f"{reg[:5]} {100 * cmp[name][reg]['share']:3.0f} % ({cmp[name][reg]['n']})" for reg in regions))
for k, v in out["lists"].items():
    print(f"  {k}: {v}")
print("kung/Danmark:", out["no_king_no_denmark"])
