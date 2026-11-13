"""Underlag till "När restes stenen?" (Korpus nr 2, utlovat på s. 19 i nr 1). Beskrivande, inga prov.

Räknar på Rundatas svenska vikingatida runstenar (research_gaps.is_runestone):
- hur stenarna är daterade: säker stilgrupp (Gräslund), osäker eller ingen, utgivarnas tidsangivelser i dateringsfältet;
- stilgruppernas år (src/styles.py) och hur få olika värden skalan har;
- de fasta punkterna utanför stilen: Ingvarsstenarna (självkontrollens lista, utdata/varlden/sjalvkontroll) och stenar
  som nämner England, och vilka stilgrupper de har fått;
- vad som händer med ett mönster när dateringen är osäker: andelen stenar med bön ("hjälpe") i tidiga mot sena
  stilgrupper, och gränserna om alla stenar utan säker stilgrupp hade varit tidiga respektive sena.
    .venv/bin/python utdata/nar_restes/berakna.py
"""
import collections, json, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store
from src import research_gaps as rg
from src.styles import STYLE_GROUPS

I = [r for r in store().inscriptions if rg.is_runestone(r)]
N = len(I)
kod = lambda r: (r.get("style") or "").strip()
saker = [r for r in I if rg.has_style(r)]
osaker = [r for r in I if not rg.has_style(r) and kod(r) not in ("", "?")]
ingen = [r for r in I if kod(r) in ("", "?")]
per_grupp = collections.Counter(kod(r) for r in saker)
ar = {s["code"]: (s["from"], s["to"]) for s in STYLE_GROUPS}
TIDIG, SEN = {"RAK", "Fp", "Pr1", "Pr2"}, {"Pr3", "Pr4", "Pr5"}

utg = [r for r in I if rg.is_dated_by_year(r)]
utg_saker = sum(rg.has_style(r) for r in utg)
def sekel(d):
    d = d or ""
    if re.search(r"800", d): return "800-talet"
    if re.search(r"900", d): return "900-talet"
    if re.search(r"1100|1130", d): return "omkring 1100 eller senare"
    return "1000-talet"
utg_sekel = collections.Counter(sekel(r["dating"]) for r in utg)

sk = json.load(open(os.path.join(ROOT, "utdata", "varlden", "sjalvkontroll", "resultat.json"), encoding="utf-8"))
ingvar = set(sk["p1"]["ingvarsstenar"])
by = {r["signum"]: r for r in I}
ing_stil = collections.Counter(kod(by[s]) if rg.has_style(by[s]) else "ingen säker" for s in ingvar if s in by)
ENG = re.compile(r"\b(Æ|E)ngland", re.I)
england = [r for r in I if ENG.search(r.get("normalization") or "")]
eng_stil = collections.Counter(kod(r) if rg.has_style(r) else "ingen säker" for r in england)

BON = re.compile(r"hialp", re.I)
bon = lambda r: bool(BON.search(r.get("normalization") or ""))
def andel(rs): return (sum(map(bon, rs)), len(rs))
tid, sen = [r for r in saker if kod(r) in TIDIG], [r for r in saker if kod(r) in SEN]
odaterade = [r for r in I if not rg.has_style(r)]
b_t, b_s, b_o = andel(tid), andel(sen), andel(odaterade)
pc = lambda k, n: round(100 * k / n, 1) if n else None
gr = {"observerat": {"tidig": pc(*b_t), "sen": pc(*b_s)},
      "alla_odaterade_tidiga": {"tidig": pc(b_t[0] + b_o[0], b_t[1] + b_o[1]), "sen": pc(*b_s)},
      "alla_odaterade_sena": {"tidig": pc(*b_t), "sen": pc(b_s[0] + b_o[0], b_s[1] + b_o[1])}}

ut = {"runstenar": N, "saker_stilgrupp": len(saker), "osaker_stilgrupp": len(osaker), "ingen_stilgrupp": len(ingen),
      "andel_saker": pc(len(saker), N), "per_grupp": dict(per_grupp.most_common()), "grupp_ar": ar,
      "mittar_olika": sorted({(a + b) / 2 for a, b in ar.values() if a}),
      "utgivarens_tidsangivelse": len(utg), "varav_med_saker_stil": utg_saker, "utg_sekel": dict(utg_sekel),
      "ingvar": {"n": len(ingvar), "stil": dict(ing_stil.most_common())},
      "england": {"n": len(england), "signa": sorted(r["signum"] for r in england), "stil": dict(eng_stil.most_common())},
      "bon": {"tidig": b_t, "sen": b_s, "utan_saker_stil": b_o, "granser": gr}}
json.dump(ut, open(os.path.join(os.path.dirname(__file__), "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in ut.items() if k != "england"} | {"england": {k: v for k, v in ut["england"].items() if k != "signa"}}, ensure_ascii=False, indent=1))
