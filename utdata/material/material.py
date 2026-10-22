"""Materialet och budskapet: vad som skrevs på sten, trä, ben och metall i Rundata 3.1 (alla inskrifter, alla länder), per
period (U urnordisk tid, V vikingatid, M medeltid), och vilka vikingatida stenar som själva säger att de ska stå kvar.
Beskrivande underlag till artikeln om valet av sten (build_material.py); inga tester. Skriver utdata/material/material.json.
    PYTHONPATH=. .venv/bin/python utdata/material/material.py"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402

ins = store().inscriptions
MATS = ("sten", "trä", "ben/horn", "metall")
mat = lambda r: (r.get("material_type") or "?")  # noqa: E731
per = lambda r: (r.get("period") or "?")  # noqa: E731
norm = lambda r: (r.get("normalization") or "").replace("ð", "þ").replace("Ð", "Þ")  # noqa: E731
readable = lambda r: bool(re.search(r"[a-zæøåäöþʀ]{2,}", (r.get("normalization") or ""), re.I))  # noqa: E731


def kind(r):
    """Vad texten gör, grovt: en klass per inskrift, i fast ordning (den första som passar)."""
    n, e, t = norm(r), (r.get("translation_en") or ""), norm(r) + " " + (r.get("translation_en") or "")
    if not readable(r):
        return "oläsligt"
    if re.search(r"\bfuþ[aąo]rk|<fuþ", t, re.I) or re.search(r"\bfuþ[aąo]r?k", (r.get("transliteration") or ""), re.I):
        return "futhark"
    if re.search(r"\bæft(iR)?\b|\bæft\b|in memory of", t, re.I) or re.search(r"\bat\b.*\b(faþur|moþur|broþur|sun|syni|bonda|dottur|systur)\b", n, re.I):
        return "minnesinskrift"
    if re.search(r"\balu\b|\blaukaz\b|\bþurs\b|\blaþu\b|\bagla\b|sator|amulet|charm|galdr|fever|against the", t, re.I):
        return "besvärjelse/skydd"
    if re.search(r"\bGuþ\b|\bKrist|\bMaria\b|\bAve\b|\bPater|\bDominus|\bamen\b|\bGod\b|Christ|\bMary\b|\bLord\b|\bsoul\b|\bsanct|\bhialpi\b", t, re.I):
        return "bön/religiös"
    if re.search(r"\b(a|á|æigir|owns|owner)\b", e + " " + n, re.I) and re.search(r"owns|owner|\bá\b", e + " " + n, re.I):
        return "namn/ägare"
    if re.search(r"\b(made|carved|cut|wrote|writes|painted)\b|\bgærþi\b|\brist[iu]\b|\bræist\b|\bfaþi\b|\bskrifaþi\b", e + " " + n, re.I):
        return "tillverkare/ristare"
    if len(n.split()) <= 3:
        return "namn/ägare"
    return "meddelande/annat"


tab, words = defaultdict(Counter), defaultdict(list)
for r in ins:
    if mat(r) in MATS and per(r) in ("U", "V", "M"):
        tab[(per(r), mat(r))][kind(r)] += 1
        if readable(r):
            words[(per(r), mat(r))].append(len(norm(r).split()))
summary = {}
for key in sorted(tab):
    n = sum(tab[key].values()); ws = sorted(words[key])
    summary[f"{key[0]}|{key[1]}"] = {"n": n, "median_words": ws[len(ws) // 2] if ws else None, "kinds": dict(tab[key].most_common())}
total = {p: Counter(mat(r) for r in ins if per(r) == p and mat(r) in MATS) for p in ("U", "V", "M")}

# Stones that say they will stand or last (Viking Age, every country)
STAND = re.compile(r"\b(standa|stændr|standr|stænda|stanti)\b|\bm[æe]þan\b|\baldri(gi)?\b|\blengi\b|\blængi\b|\blifiR\b|\bminnum\b", re.I)
stones = [r for r in ins if mat(r) == "sten" and per(r) == "V"]
stand = []
for r in stones:
    m = STAND.search(norm(r))
    if m and re.search(r"stæin|sten|stain|kumbl|mærki|runaR|runum|minnum|lifa|mæþan|meþan|verald", norm(r), re.I):
        seg = re.search(r"[^.;§]*" + re.escape(m.group(0)) + r"[^.;§]*", norm(r))
        stand.append({"signum": r["signum"], "place": r["place"], "text": (seg.group(0).strip() if seg else norm(r)[:120]),
                      "translation_en": r.get("translation_en"), "normalization": r.get("normalization")})
# Where the wood and bone come from
places = {f"{p}|{m}": dict(Counter((r.get("place") or "?").split(",")[0] for r in ins if per(r) == p and mat(r) == m).most_common(8))
          for p, m in (("V", "trä"), ("V", "ben/horn"), ("M", "trä"), ("M", "ben/horn"))}
examples = {s: next(({"signum": r["signum"], "object": r.get("object"), "place": r["place"], "normalization": r.get("normalization"),
                      "translation_en": r.get("translation_en"), "period": per(r), "material": mat(r)} for r in ins if r["signum"] == s), None)
            for s in ("DR AUD1997;264", "N A240", "U NOR2000;34A", "Sö Fv1981;197", "DR M109", "N B540", "N B333", "DR IK149,1", "DR 196",
                      "G 88", "DR 42", "Sm 16", "U 114", "DR 212", "U 729", "U 707", "Sö 206", "G 343", "DR 131", "Sö 137", "Ög 136", "U 838")}
u_dating = dict(Counter((r.get("dating") or "?") for r in ins if per(r) == "U" and mat(r) == "sten").most_common())
out = {"n_total": len(ins), "period": dict(Counter(per(r) for r in ins)), "material_by_period": {p: dict(c) for p, c in total.items()},
       "summary": summary, "stand": stand, "n_stand": len(stand), "n_v_stones": len(stones), "places": places, "examples": examples,
       "u_stone_dating": u_dating,
       "m_wood_objects": dict(Counter((r.get("object") or "?") for r in ins if per(r) == "M" and mat(r) == "trä").most_common(12))}
json.dump(out, open(os.path.join(ROOT, "utdata", "material", "material.json"), "w"), ensure_ascii=False, indent=1)
print("inskrifter:", len(ins), out["period"]); print("material per period:", out["material_by_period"])
for k, v in summary.items():
    print(f"{k:12} n {v['n']:5} median {v['median_words']:>3} | " + ", ".join(f"{a} {100 * b / v['n']:.0f} %" for a, b in list(v["kinds"].items())[:6]))
print("ståendeformler:", len(stand), "av", len(stones))
for x in stand:
    print("  ", x["signum"], "|", x["text"][:100])
print("platser:", places)
