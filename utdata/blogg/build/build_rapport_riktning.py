"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4; Fullt prövat fynd): "Runstenarna vände texten mot
vägen – hälften av ristningarna inom 45 grader från vägen, mot en fjärdedel väntat" (sv + en). Den låsta planen
analysplaner/2026-10-29-ristningens-riktning.md (H1–H4) och tilläggsplanen för robusthetsstegen
analysplaner/2026-10-31-riktning-trappan.md. Alla siffror asserteras mot utdata/riktning/riktning.json och trappan.json;
rättelserna i rapportversion 3 (granskningen 2026-11-05: gon-tilläggen och de dubbla posterna) mot gon_kontroll.json.
    ../../../.venv/bin/python build_rapport_riktning.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "utdata", "rapporter", "figurer"))
from figur import FIG, bild  # noqa: E402

APP_VERSION = "3.0.0"  # the Vitki version the analysis was made in (tag v3.0.0 + the commits named in Data och kod), not the current one
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 3  # version 1: 2026-10-31 (först publicerad); version 2: 2026-11-01 (Figur 1); version 3: rättelser
FIRST_PUBLISHED = "2026-10-31"
TODAY = "2026-11-05"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = ("analysplanen låstes 2026-10-29; analysen kördes 2026-10-29; tilläggsplanen för känslighetsanalyserna låstes och "
         "kördes 2026-10-31; en granskning före arkiveringen fann två kodningsfel 2026-11-05; kontrollen med rättade "
         "riktningar kördes 2026-11-05")
TL_EN = ("the analysis plan was locked 2026-10-29; the analysis was run 2026-10-29; the addendum plan for the sensitivity "
         "analyses was locked and run 2026-10-31; a review before archiving found two coding errors 2026-11-05; the check "
         "with corrected directions was run 2026-11-05")
RD = os.path.join(ROOT, "utdata", "riktning")
R = json.load(open(os.path.join(RD, "riktning.json"), encoding="utf-8"))
TR = json.load(open(os.path.join(RD, "trappan.json"), encoding="utf-8"))
G = json.load(open(os.path.join(RD, "gon_kontroll.json"), encoding="utf-8"))
SHA = {k: open(os.path.join(ROOT, "analysplaner", f"{k}.sha256")).read().split()[0][:16]
       for k in ("2026-10-29-ristningens-riktning", "2026-10-31-riktning-trappan")}
assert SHA["2026-10-29-ristningens-riktning"].startswith("cd73b962") and SHA["2026-10-31-riktning-trappan"].startswith("4da9710d")

pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731
r0 = lambda x: int(x + 0.5)  # noqa: E731
d2 = lambda x: f"{x:.2f}".replace(".", ",").replace("-", "−")  # noqa: E731
e2 = lambda x: f"{x:.2f}".replace("-", "−")  # noqa: E731


def pfmt(p, en=False):
    if p < 0.001:
        s = f"{p:.4f}"
    elif p < 0.1:
        s = f"{p:.3f}"
    else:
        s = f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


# ---- the locked plan (H1–H4) ------------------------------------------------------------------------------------------
assert (R["n"], R["n_vag"], R["n_vag_text"], R["n_gard"]) == (219, 123, 69, 94)
A, HA, HB = R["resultat"]["alla"], R["resultat"]["A"], R["resultat"]["B"]
H1, H2, H3, H4 = A["H1"], A["H2"], A["H3"], A["H4"]
assert R["status"] == {"H1": "ingen skillnad påvisad", "H2": "håller", "H3": "ingen skillnad påvisad", "H4": "ingen skillnad påvisad"}
assert (d2(H2["medel_cos"]), d2(H2["vantat"]), pc(H2["andel_inom_45"]), H2["p"]) == ("0,37", "0,01", 50, 0.0001)
assert abs(R["holm"]["H2"] - 0.0004) < 1e-9
assert (HA["H2"]["n"], HB["H2"]["n"], d2(HA["H2"]["medel_cos"]), d2(HB["H2"]["medel_cos"])) == (71, 52, "0,45", "0,26")
assert HA["H2"]["p"] == 0.0001 and 0.018 < HB["H2"]["p"] < 0.019
assert 0.48 < H1["p"] < 0.49 and 0.30 < H3["p"] < 0.31 and 0.86 < H4["p"] < 0.87 and H4["n_bro"] == 9
assert (pfmt(HA["H1"]["p"]), pfmt(HB["H1"]["p"])) == ("p = 0,79", "p = 0,039")  # H1 i halvorna
assert (d2(H3["medel_cos"]), d2(H3["vantat"]), e2(H3["vantat"])) == ("0,01", "−0,02", "−0.02")
DESC = R["beskrivning"]
ST = DESC["streck"]
assert (ST["V"], ST["N"], ST["Ö"], ST["S"], pc(DESC["andel_soder"])) == (37, 26, 25, 25, 32)
assert sum(ST[k] for k in ("SÖ", "SSÖ", "S", "SSV", "SV")) == 70 and abs(DESC["andel_soder"] - 70 / 219) < 1e-12  # mellan SÖ och SV
# the plan's robustness tests (analysplanen: "gården inom 500 m; bara Uppland och Södermanland")
RB = R["robusthet"]
G500, US = RB["gard_500"], RB["U_So"]["H2"]
assert (G500["n"], d2(G500["medel_cos"]), d2(G500["vantat"]), pfmt(G500["p"])) == (52, "0,01", "−0,06", "p = 0,20")
assert (US["n"], d2(US["medel_cos"]), d2(US["vantat"]), pc(US["andel_inom_45"]), US["p"]) == (92, "0,35", "−0,02", 52, 0.0001)
assert RB["vag_bara_text"]["n"] == 69 and RB["vag_bara_registrerad"]["n"] == 80  # samma som stegen i 5.3

# ---- the addendum ladder ----------------------------------------------------------------------------------------------
assert TR["plan"] == "analysplaner/2026-10-31-riktning-trappan.md" and TR["all_hold"] is True and TR["lopo_holds"] is True
RU, LO = TR["rungs"], TR["lopo"]
assert set(RU) == {"huvud", "halva_A", "halva_B", "socken", "en_per_ristare", "utan_aterresta", "utan_flyttade_runor",
                   "dagens_flyttregel", "bara_text", "bara_registrerad"} and all(r["holds"] for r in RU.values())
assert abs(RU["huvud"]["medel_cos"] - H2["medel_cos"]) < 1e-9  # same measure as the plan's H2
assert (RU["en_per_ristare"]["n"], TR["n_carvers"], TR["n_parishes"], TR["n_reerected"], TR["n_reerected_alla_219"], TR["n_moved_runor"],
        TR["n_moved_now"]) == (93, 20, 76, 14, 29, 10, 0)
assert (RU["bara_text"]["n"], pc(RU["bara_text"]["andel_inom_45"]), RU["bara_registrerad"]["n"], pc(RU["bara_registrerad"]["andel_inom_45"])) == (69, 62, 80, 28)
assert abs(RU["bara_registrerad"]["andel_inom_45"] - 0.275) < 1e-12 and d2(RU["bara_registrerad"]["medel_cos"]) == "0,16"
assert 0.019 < RU["bara_registrerad"]["p"] < 0.020 and pfmt(RU["bara_registrerad"]["p"]) == "p = 0,020" and set(LO) == {"U", "Sö", "Ög"}
assert (LO["U"]["n"], pc(LO["U"]["andel_kvar"]), LO["Sö"]["n"], LO["Ög"]["n"]) == (62, 50, 92, 113)
assert (pfmt(HB["H2"]["p"]), pfmt(RU["halva_B"]["p"])) == ("p = 0,019", "p = 0,016")  # nya omblandningar i stegen

# ---- version 3: the check after the review of 2026-11-05 (utdata/riktning/gon_kontroll.py) ------------------------------
GR, GU, LR, LU = G["rattad"], G["rattad_en_per_sten"], G["trappan_rattad"], G["trappan_rattad_en_per_sten"]
assert G["trappan_last_reproducerad"] is True and LR["all_hold"] is True and LU["all_hold"] is True
assert all(r["holds"] for r in LR["rungs"].values()) and all(r["holds"] for r in LU["rungs"].values())
assert (G["n_rattade_vagar"], G["n_rattade_ristningar"], G["n_rattade_vagar_bland_text"]) == (9, 6, 9)
assert {x["signum"] for x in G["rattade_vagar"]} == {"U 947", "U 949", "U 352", "U 1043", "U 1065", "U 859", "U 629", "U 233", "Ög 176"}
assert {x["signum"] for x in G["rattade_ristningar"]} == {"Sö 348", "U 34", "U 949", "U 30", "U 472", "U 474"}
assert [x["text"] for x in G["rattade_vagar"] if x["signum"] == "U 947"] == ["V 40cg S om landsväg"]
FV, FI = [x["fel_grader"] for x in G["rattade_vagar"]], [x["fel_grader"] for x in G["rattade_ristningar"]]
assert (r0(min(FV)), r0(max(FV)), r0(min(FI)), r0(max(FI))) == (50, 86, 9, 40)
assert (d2(G["last"]["alla"]["medel_cos"]), pc(G["last"]["alla"]["andel_inom_45"]), d2(G["last"]["bara_text"]["medel_cos"])) == ("0,37", 50, "0,49")
assert (d2(GR["alla"]["medel_cos"]), pc(GR["alla"]["andel_inom_45"]), d2(GR["bara_text"]["medel_cos"])) == ("0,39", 52, "0,53")
DUP = G["dubbletter"]
assert (len(DUP["stenar"]), DUP["n_stenar"], DUP["n_poster"], DUP["n_stenar_med_vag"], DUP["n_poster_med_vag"]) == (5, 214, 219, 120, 123)
assert (d2(GU["alla"]["medel_cos"]), pc(GU["alla"]["andel_inom_45"])) == ("0,37", 51)
assert LR["rungs"]["huvud"]["p"] == 0.0001 and LU["rungs"]["huvud"]["p"] == 0.0001
assert abs(LR["rungs"]["huvud"]["medel_cos"] - GR["alla"]["medel_cos"]) < 1e-12
PB = (pfmt(LR["rungs"]["halva_B"]["p"]), pfmt(LU["rungs"]["halva_B"]["p"]))
PR = (pfmt(LR["rungs"]["bara_registrerad"]["p"]), pfmt(LU["rungs"]["bara_registrerad"]["p"]))
assert PB == ("p = 0,003", "p = 0,007") and PR == ("p = 0,024", "p = 0,047")
assert (pfmt(GR["H1_rayleigh"]["p"]), pfmt(GR["H3_gard"]["p"])) == ("p = 0,46", "p = 0,29")
IN = G["indata"]
assert IN["kmr_runstenar"]["hamtad"] == "2026-10-29" and "K-samsök (CC0)" in IN["kmr_runstenar"]["kalla"]
assert (IN["lamningar_fardvagar"]["hamtad_filtid"], IN["lamningar_vagmarke"]["hamtad_filtid"], IN["lamningar_bytomt"]["hamtad_filtid"],
        IN["runor_2020"]["hamtad"]) == ("2026-10-12", "2026-10-29", "2026-10-29", "2026-10-16")
assert IN["korpus"]["huvud"] == "3f58e9339191761e" and IN["korpus"]["flyttregel_steget"] == "e83202e01a5e6d27"
assert IN["korpus"]["identiska"] is True and IN["korpus"]["huvud_skapad"] == "2026-10-28"  # the moved-rule step's corpus has the same rows as the main one
for f_ in ("scripts/fetch_kmr_runstenar.py", "scripts/fetch_raa_remains.py", "scripts/fetch_raa_extra.sh", "scripts/fetch_runor.py"):
    assert os.path.exists(os.path.join(ROOT, f_)), f_
COMMITS = {"74ca1ef": ("2026-10-29", "utdata/riktning/analys.py"), "d0f5a6b": ("2026-10-31", "utdata/riktning/trappa.py"),
           "4f80a63": ("2026-11-01", "utdata/blogg/build/build_rapport_riktning.py"), "07d2ec0": ("2026-10-27", "src/placement.py")}
for h_, (day_, file_) in COMMITS.items():
    assert git("show", "-s", "--format=%ad", "--date=short", h_) == day_ and file_ in git("show", "--name-only", "--format=", h_).split("\n"), h_
assert git("log", "-1", "--format=%ad", "--date=short", "v3.0.0") == "2026-10-20"
# figure 1: "toward" = the sector straight at the road, i.e. within 11.25 degrees (rapportfigurer.py, sector 0 of 16)
_st = pd.read_csv(os.path.join(RD, "stenar.csv"))
_st = _st[_st.vag.notna()]
assert int((((_st.riktning - _st.vag + 180) % 360 - 180).abs() <= 22.5 / 2).sum()) == FIG["vag"]["toward"] == 31

SLUG = "ristningen-vand-mot-vagen"
title = "Runstenarna vände texten mot vägen – hälften av ristningarna inom 45 grader från vägen, mot en fjärdedel väntat"
title_en = "The runestones turned their text towards the road – half of the inscriptions within 45 degrees of the road, against a quarter expected"
summary = ("Förregistrerad studie. Av de runstenar som står kvar på sin plats och där vi vet var vägen gick vänder hälften "
           "ristningen mot vägen, mot en fjärdedel om riktningen vore slumpvis. Fyndet håller i båda halvorna av "
           "materialet och i alla känslighetsanalyser, också när två kodningsfel rättas. Texten vändes mot den som gick "
           "förbi; vi fann inget tecken på att den vändes mot ett visst väderstreck eller mot gården.")
summary_en = ("Pre-registered study. Of the runestones that still stand in place and where we know where the road ran, half "
              "turn the inscription towards the road, against a quarter if the direction were random. The finding holds in "
              "both halves of the material and in every sensitivity analysis, also when two coding errors are corrected. The "
              "text was turned towards those passing by; we found no sign that it was turned towards a particular point of "
              "the compass or towards the farm.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/forskningsrapporter/{SLUG}")


def chart(sv):
    f = (lambda x: f"{100 * x:.1f}".replace(".", ",")) if sv else (lambda x: f"{100 * x:.1f}")
    rows = [":::chart Ristningen vänd inom 45 grader från vägen, procent" if sv else ":::chart Inscription turned within 45 degrees of the road, percent",
            f"+{'Alla stenar med väg' if sv else 'All stones with a road'} | {f(H2['andel_inom_45'])} | {H2['n']} {'stenar' if sv else 'stones'}",
            f"{'Väg ur registrets text' if sv else 'Road from the register text'} | {f(RU['bara_text']['andel_inom_45'])} | {RU['bara_text']['n']} {'stenar' if sv else 'stones'}",
            f"{'Registrerad färdväg inom 500 m' if sv else 'Registered route within 500 m'} | {f(RU['bara_registrerad']['andel_inom_45'])} | {RU['bara_registrerad']['n']} {'stenar' if sv else 'stones'}",
            f"{'Väntat om riktningen vore slumpvis' if sv else 'Expected if the direction were random'} | {f(0.25)} |",
            "Källa: Kulturmiljöregistret och Rundata; den låsta analysen. Diagram: Vitki." if sv else
            "Source: the Swedish register of ancient monuments and Rundata; the locked analysis. Chart: Vitki.", ":::"]
    return "\n".join(rows)


def rung_sv(k, label):
    r = RU[k]
    return f"- {label} ({r['n']} stenar): medel-cos {d2(r['medel_cos'])} mot {d2(r['vantat'])}, {pfmt(r['p'])}."


def rung_en(k, label):
    r = RU[k]
    return f"- {label} ({r['n']} stones): mean cos {e2(r['medel_cos'])} against {e2(r['vantat'])}, {pfmt(r['p'], True)}."


assert FIG["vag"]["n"] == 123 and FIG["vag"]["toward"] == 31 and round(FIG["vag"]["expected"]) == 8
FIG_SV = bild("vag", "sv", "Figur 1. Till vänster måttet: vinkeln v mellan hållet ristningen vetter åt och riktningen till vägen. Till höger de 123 stenarna: 31 vetter åt samma väderstreck som vägen (inom 11,25 grader), mot omkring 8 om riktningen vore slumpvis. Illustration och diagram: Vitki, ur Riksantikvarieämbetets kulturmiljöregister och Rundata.")
FIG_EN = bild("vag", "en", "Figure 1. Left, the measure: the angle v between the direction the inscription faces and the direction to the road. Right, the 123 stones: 31 face the same compass point as the road (within 11.25 degrees), against about 8 if the direction were random. Illustration and chart: Vitki, from the Swedish register of ancient monuments and Rundata.")

LOG_SV = f"""## Ändringslogg

- **Version 1, {FIRST_PUBLISHED}.** Första publicerade versionen.
- **Version 2, 2026-11-01.** Figur 1 tillagd: en skiss av måttet och ett rosdiagram över hur ristningarna vetter i förhållande till vägen. Inga siffror, tolkningar eller slutsatser är ändrade.
- **Version {REPORT_VERSION}, {TODAY}.** Rättelser efter en granskning inför den permanenta arkiveringen i Zenodo; felen rättas öppet i en ny version, inte i tysthet. (1) Två kodningsfel i hur registrets text lästes redovisas i 4.5 med en kontroll i efterhand: gon-tillägg i nio vägriktningar och sex ristningsriktningar lästes som ett enda väderstreck, och fem stenar med två poster i registret räknades två gånger. Rättat blir sambandet något starkare och alla känslighetsanalyser håller; den låsta analysens siffror står kvar oförändrade, och sammanfattningen och materialavsnittet säger detta. (2) Nollresultaten för väderstrecket, gården och bro- och vägstenarna beskrivs som att ingen skillnad kunde påvisas, inte som fakta; svagheterna har fått en punkt om bytomternas ålder, och svagheten om vägens ålder säger nu att sambandet med registrerade äldre färdvägar är svagt. (3) Tidigare forskning: Ekholm (1950) har redan beskrivit stenar som är vända mot vägen och en återresning som vände en sten; invändningen mot Klos tillskrivs nu Mats G. Larsson (2010), som har lagts till bland referenserna; sidorna för Ekholm och McLeod är angivna; en referens som inte citerades i texten är struken. (4) Planens två robusthetsprov som inte redovisades (gården inom 500 meter, bara Uppland och Södermanland) står i 5.2. (5) Form: andelen som vetter mot söder beskrivs som det den räknar (mellan sydost och sydväst), 5.3 säger att känslighetsanalyserna drog nya omblandningar, Figur 1:s bildtext säger vad samma väderstreck betyder, minustecken, diagrammets upphov, och under Data och kod korpusversionerna, commits, hämtningsskripten och hämtningsdatumen för registret."""
LOG_EN = f"""## Change log

- **Version 1, {FIRST_PUBLISHED}.** First published version.
- **Version 2, 2026-11-01.** Figure 1 added: a sketch of the measure and a rose diagram of how the inscriptions face relative to the road. No numbers, interpretations or conclusions have changed.
- **Version {REPORT_VERSION}, {TODAY}.** Corrections after a review before permanent archiving in Zenodo; errors are corrected openly in a new version, not silently. (1) Two coding errors in how the register text was read are reported in 4.5 with a check made afterwards: gon qualifiers in nine road bearings and six inscription bearings were read as a single compass point, and five stones with two records in the register were counted twice. Corrected, the association is slightly stronger and every sensitivity analysis holds; the locked analysis's numbers stand unchanged, and the abstract and the material section say so. (2) The null results for the compass, the farm and the bridge and road stones are described as no difference detected, not as facts; the weaknesses have a point on the age of the farm sites, and the weakness on the age of the road now says that the association with registered older routes is weak. (3) Earlier research: Ekholm (1950) had already described stones turned towards the road and a re-erection that turned a stone; the objection to Klos is now attributed to Mats G. Larsson (2010), added to the references; the pages for Ekholm and McLeod are given; a reference not cited in the text is removed. (4) The plan's two robustness tests that were not reported (the farm within 500 metres, only Uppland and Södermanland) are in 5.2. (5) Form: the share facing south is described as what it counts (between south-east and south-west), 5.3 says that the sensitivity analyses drew new shuffles, the caption of Figure 1 says what the same compass point means, minus signs, the chart's maker, and under Data and code the corpus versions, commits, fetch scripts and fetch dates for the register."""

LR_B, LU_B = LR["rungs"]["halva_B"]["p"], LU["rungs"]["halva_B"]["p"]
LR_R, LU_R = LR["rungs"]["bara_registrerad"]["p"], LU["rungs"]["bara_registrerad"]["p"]

body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY} (först publicerad {FIRST_PUBLISHED}). Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, vägar, placering, ristningens riktning, cirkulär statistik, Kulturmiljöregistret, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Var runstenarna restes har diskuterats länge, och vägarna är ett av svaren: stenar vid vägar syntes. Enstaka stenar har beskrivits som vända mot vägen, men ingen har mätt i hela materialet åt vilket håll ristningen vändes. Frågan här är om texten vändes mot vägen, mot gården eller mot ett visst väderstreck.
**Material.** {R['n']} poster i Kulturmiljöregistret om {DUP['n_stenar']} svenska vikingatida runstenar som står kvar på sin plats och där registret anger åt vilket håll ristningen vetter. För {R['n_vag']} av posterna finns en väg att mäta mot, för {R['n_gard']} en bytomt.
**Metod.** Förregistrerad studie med fyra test och Holm-korrigering. Måttet är cosinus för vinkeln mellan ristningens riktning och riktningen till vägen, jämfört med 9 999 omblandningar av riktningarna inom landskapet. Intern replikering i två halvor och tio känslighetsanalyser enligt en låst tilläggsplan.
**Resultat.** Hälften av stenarna, {pc(H2['andel_inom_45'])} procent, vänder ristningen inom 45 grader från vägen, mot en fjärdedel om riktningen vore slumpvis. Medel-cos {d2(H2['medel_cos'])} mot {d2(H2['vantat'])} väntat, {pfmt(H2['p'])}, Holm-korrigerat p = 0,0004. Det håller i båda halvorna och i alla känslighetsanalyser, också utan Uppland, socken för socken, med en sten per ristare och utan återresta stenar. Två kodningsfel som hittades efter publiceringen ändrar inte detta; rättade blir sambandet något starkare (medel-cos {d2(GR['alla']['medel_cos'])}, {pc(GR['alla']['andel_inom_45'])} procent inom 45 grader; avsnitt 4.5). Riktningarna skiljer sig inte påvisbart från en jämn spridning, och vi fann inget tecken på att ristningen vändes mot gården (bytomterna är kända först från 1600–1700-talens kartor).
**Slutsats.** Texten vändes mot den som gick förbi på vägen. Den största svagheten är att vägen i registret ofta är dagens väg; med bara registrerade äldre färdvägar och vägmärken är sambandet svagt ({pc(RU['bara_registrerad']['andel_inom_45'])} procent inom 45 grader mot 25 väntat) men går åt samma håll.

## 1. Inledning

Gunnar Ekholm (1950) frågade var runstenarna restes och svarade att de uppländska stenarna i stor utsträckning står vid forntidens vägar och vattenleder, och att också stenarna vid gravfälten ofta förklaras av den väg som gick förbi gravfältet. Han noterade att enskilda stenar är vända mot vägen, vid Bollsta i Vaksala (s. 138) och på Särsta mark i Knivsta (s. 139), och att en återresning kan vända en sten: en sten på Ängby mark vid Knivsta har framsidan mot järnvägen sedan den restes på nytt på 1860-talet (s. 140). Torun Zachrisson (1998) har satt stenarna i samband med gård, gräns och gravfält, och Lydia Klos (2009) har hävdat att de flesta restes vid gravfält. Mats G. Larsson (2010) har invänt att gravfälten därmed blir starkt överbetonade på andra lägens bekostnad, och att Klos ställer betydligt strängare krav än tidigare forskning på vad som räknas som en forntida väg (se också McLeod 2014). Johan Bollaert (2016) jämförde stenar längs tre vikingatida vägar med andra stenar i samma trakter och fann att stenarna vid vägarna oftare har påfallande ornamentik och oftare ingår i monument med flera stenar, vilket stöder att de restes för att synas.

Det som saknas är ett mått i hela materialet på hur själva ristningen vändes. Ekholms iakttagelser gäller enstaka stenar, och en sten kan stå vid en väg men vända texten åt ett annat håll. Syftet här är att pröva om ristningen vändes mot vägen, mot gården eller mot ett visst väderstreck, med de uppgifter om ristningens riktning som Kulturmiljöregistret har för en del stenar.

## 2. Förregistrering: hypotes och plan

Hypoteserna, måtten och tolkningsreglerna skrevs ned i en analysplan den 29 oktober 2026, innan någon riktning hade räknats. Planen har kontrollsumman SHA-256 `{SHA['2026-10-29-ristningens-riktning']}…` (se Data och kod). Före låsningen var bara antalet poster känt: 456 poster i registret anger en riktning, 369 gäller en enda sten med en riktning, 219 av dem står kvar på sin plats, och 88 av de 369 nämner en väg med väderstreck.

Planen prövar fyra hypoteser med Holm-korrigering: H1 att riktningarna inte är jämnt fördelade över kompassen, H2 att ristningen vänds mot vägen, H3 att den vänds mot gården och H4 att bro- och vägstenar vänds mer mot vägen än andra. En hypotes *håller* när Holm-p är under 0,05 och riktningen är densamma med p under 0,05 i båda halvorna.

Planen innehöll inte projektets fasta känslighetsanalyser, som är byggda för samband mellan två drag och inte för riktningar. Motsvarande steg för riktningar bestämdes därför i en tilläggsplan den 31 oktober 2026 (SHA-256 `{SHA['2026-10-31-riktning-trappan']}…`), innan de räknades. Två av stegen, halvorna och vägens källa, fanns redan i huvudplanen. En kontroll av återresta stenar gjordes efter huvudkörningen den 29 oktober med en annan ordlista; i tilläggsplanen låstes ordlistan innan steget räknades.

## 3. Material

- **Stenarna.** Svenska vikingatida runstenar i Samnordisk runtextdatabas (Rundata) som står kvar på sin plats och har känt läge, och vars post i Riksantikvarieämbetets Kulturmiljöregister gäller just den stenen och anger en enda riktning med orden ”vetter mot” och ett av sexton väderstreck: {R['n']} poster, som gäller {DUP['n_stenar']} stenar (fem stenar har två poster var och räknades två gånger i den låsta analysen; se 4.5). Bara runstenar.
- **Vägen.** I första hand registrets egen uppgift om stenens läge i förhållande till en väg (”5 m Ö om väg”; vägen ligger då åt motsatt håll): {R['n_vag_text']} stenar. Annars närmaste registrerade färdväg eller vägmärke inom 500 meter. Sammanlagt {R['n_vag']} stenar med väg. Vägarna kommer bara ur Riksantikvarieämbetets register.
- **Gården.** Närmaste registrerade bytomt eller gårdstomt inom en kilometer: {R['n_gard']} stenar.
- **Riktningarna** räknas som bäringar från stenen, med norr som 0 grader och väderstrecken i steg om 22,5 grader.
- **Halvorna** är projektets fasta indelning socken för socken.

## 4. Metod

**4.1 Måttet.** För varje sten räknas cosinus för vinkeln mellan ristningens riktning och riktningen till vägen: 1 när ristningen vetter rakt mot vägen, 0 när den vetter åt sidan och −1 när den vetter bort. Medelvärdet över stenarna jämförs med 9 999 omblandningar där ristningarnas riktningar fördelas om mellan stenarna inom samma landskap, så att landskapets allmänna riktningsmönster behålls. Testet är ensidigt. Andelen stenar inom 45 grader från vägen redovisas också; om riktningen vore slumpvis vore den en fjärdedel.

**4.2 De andra hypoteserna.** H1 prövas med Rayleighs test för jämn fördelning (Mardia & Jupp 2000). H3 prövas som H2 mot riktningen till gården. H4 jämför medel-cos mot vägen mellan bro- och vägstenar och övriga, med omblandning av etiketten inom landskapet, tvåsidigt.

**4.3 Korrigering och replikering.** Holm-korrigering (Holm 1979) över de fyra testen. Varje hypotes prövas också i var halva för sig.

**4.4 Känslighetsanalyserna** enligt tilläggsplanen: halvorna; utan ett landskap i taget (landskap med minst tio stenar med väg; signifikans krävs bara där minst två tredjedelar av stenarna är kvar); socknen som enhet, med ett värde per socken; en sten per säker ristare; utan återresta stenar; utan stenar som Riksantikvarieämbetets register Runor (2020) anger som flyttade; med regeln för flyttade stenar efter rättelsen den 27 oktober 2026 (se Data och kod); bara vägar ur registrets text; och bara registrerade färdvägar och vägmärken. Ett steg håller när medel-cos ligger över det väntade och p är under 0,05.

**4.5 Avvikelser från planen.** Analysen följde planen, men en granskning före arkiveringen (5 november 2026) fann två kodningsfel i hur registrets text lästes. Siffrorna i resultatdelen är den låsta analysens och har inte ändrats; felen och en kontroll i efterhand redovisas här.

- **Gon-tillägg.** Nio vägriktningar och sex ristningsriktningar med gon-tillägg (”V 40cg S”, alltså 40 gon eller 36 grader från väster mot söder; en gon är en fyrahundradel av ett varv) lästes som bara ett väderstreck. Det gäller {G['n_rattade_vagar']} av de {R['n_vag_text']} vägarna ur registrets text, med fel på {r0(min(FV))}–{r0(max(FV))} grader, och {G['n_rattade_ristningar']} av de {R['n']} ristningsriktningarna, med fel på {r0(min(FI))}–{r0(max(FI))} grader. Rättade blir sambandet något starkare: medel-cos {d2(GR['alla']['medel_cos'])} i stället för {d2(G['last']['alla']['medel_cos'])} och {pc(GR['alla']['andel_inom_45'])} procent inom 45 grader i stället för {pc(G['last']['alla']['andel_inom_45'])}; med bara vägar ur registrets text {d2(GR['bara_text']['medel_cos'])} i stället för {d2(G['last']['bara_text']['medel_cos'])}.
- **Dubbla poster.** Fem stenar har två poster var i registret och räknades två gånger; de {DUP['n_poster']} posterna gäller {DUP['n_stenar']} stenar, och de {DUP['n_poster_med_vag']} med väg gäller {DUP['n_stenar_med_vag']}. Räknas varje sten en gång, med rättade riktningar, blir medel-cos {d2(GU['alla']['medel_cos'])} och {pc(GU['alla']['andel_inom_45'])} procent inom 45 grader.
- **Kontrollen.** Med de rättade riktningarna gjordes huvudtestet och alla känslighetsanalyser om med samma kod och samma omblandningar som under planerna; med de gamla riktningarna ger koden exakt de publicerade siffrorna. Alla steg håller, både med de {DUP['n_poster']} posterna och med varje sten räknad en gång. Huvudtestet ger {pfmt(LR['rungs']['huvud']['p'])}, halva B {pfmt(LR_B)} respektive {pfmt(LU_B).replace('p = ', '')}, och det svagaste steget, bara registrerade färdvägar och vägmärken, {pfmt(LR_R)} respektive {pfmt(LU_R).replace('p = ', '')}. H1 och H3 ändras inte i sak (Rayleighs test {pfmt(GR['H1_rayleigh']['p'])}; mot gården {pfmt(GR['H3_gard']['p'])}).

## 5. Resultat

**5.1 Mot vägen (H2).** Av de {H2['n']} stenarna med väg vänder {pc(H2['andel_inom_45'])} procent ristningen inom 45 grader från vägen. Medel-cos är {d2(H2['medel_cos'])} mot {d2(H2['vantat'])} väntat, {pfmt(H2['p'])}, det lägsta värde 9 999 omblandningar kan ge, och Holm-korrigerat p = 0,0004. Halva A: {HA['H2']['n']} stenar, medel-cos {d2(HA['H2']['medel_cos'])}, {pfmt(HA['H2']['p'])}. Halva B: {HB['H2']['n']} stenar, medel-cos {d2(HB['H2']['medel_cos'])}, {pfmt(HB['H2']['p'])}. H2 *håller* enligt planens regel. I klartext: av de stenar där vi vet var vägen gick vänder hälften texten mot vägen, inom 45 grader åt vardera hållet; om riktningen vore slumpvis skulle en fjärdedel göra det.

{chart(True)}

{FIG_SV}

**5.2 Väderstrecket, gården och broarna (H1, H3, H4).** Riktningarna skiljer sig inte påvisbart från en jämn spridning över kompassen: Rayleighs test {pfmt(H1['p'])} (i halva A {pfmt(HA['H1']['p'])}, i halva B {pfmt(HB['H1']['p'])}). Väster är vanligast ({ST['V']} stenar), sedan norr ({ST['N']}), öster ({ST['Ö']}) och söder ({ST['S']}); {pc(DESC['andel_soder'])} procent vetter åt något håll mellan sydost och sydväst. Mot gården: medel-cos {d2(H3['medel_cos'])} mot {d2(H3['vantat'])}, {pfmt(H3['p'])}; vi fann alltså inget tecken på att ristningen vändes mot gården, men bytomterna är kända först från 1600- och 1700-talens kartor. Bro- och vägstenarna ({H4['n_bro']} med väg) skiljer sig inte påvisbart från andra stenar, {pfmt(H4['p'])}, men med nio stenar säger provet lite. Ingen av de tre hypoteserna håller.

**Planens robusthetsprov.** Med gården inom 500 meter i stället för en kilometer ({G500['n']} stenar): medel-cos {d2(G500['medel_cos'])} mot {d2(G500['vantat'])}, {pfmt(G500['p'])}. Med bara Uppland och Södermanland ({US['n']} stenar med väg): medel-cos {d2(US['medel_cos'])} mot {d2(US['vantat'])}, {pfmt(US['p'])}, {pc(US['andel_inom_45'])} procent inom 45 grader. Planens två andra prov, bara vägar ur registrets text och bara registrerade färdvägar och vägmärken, står bland känslighetsanalyserna i 5.3.

**5.3 Känslighetsanalyserna.** Alla håller:

{rung_sv('halva_A', 'Halva A')}
{rung_sv('halva_B', 'Halva B')}
- Utan ett landskap i taget: utan Uppland ({LO['U']['n']} stenar kvar, hälften, så bara riktningen krävs) medel-cos {d2(LO['U']['medel_cos'])}, {pfmt(LO['U']['p'])}; utan Södermanland ({LO['Sö']['n']}) {d2(LO['Sö']['medel_cos'])}, {pfmt(LO['Sö']['p'])}; utan Östergötland ({LO['Ög']['n']}) {d2(LO['Ög']['medel_cos'])}, {pfmt(LO['Ög']['p'])}.
{rung_sv('socken', f"Socknen som enhet, {TR['n_parishes']} socknar")}
{rung_sv('en_per_ristare', f"En sten per säker ristare, {TR['n_carvers']} ristare")}
{rung_sv('utan_aterresta', f"Utan återresta stenar, {TR['n_reerected']} bort")}
{rung_sv('utan_flyttade_runor', f"Utan stenar som Runor anger som flyttade, {TR['n_moved_runor']} bort")}
- Med regeln för flyttade stenar efter rättelsen den 27 oktober 2026 räknas ingen av de {H2['n']} som flyttad, eftersom huvudanalysen redan bygger på den regeln; resultatet är detsamma som huvudtestet.
{rung_sv('bara_text', f"Bara vägar ur registrets text, {pc(RU['bara_text']['andel_inom_45'])} procent inom 45 grader")}
{rung_sv('bara_registrerad', f"Bara registrerade färdvägar och vägmärken, {pc(RU['bara_registrerad']['andel_inom_45'])} procent inom 45 grader")}

Känslighetsanalyserna drog nya omblandningar, så p-värdena skiljer sig något från huvudtestets: halva B har {pfmt(RU['halva_B']['p'])} här och {pfmt(HB['H2']['p'])} i 5.1. Ordlistan för återresta stenar i tilläggsplanen träffar {TR['n_reerected_alla_219']} av alla {R['n']} stenar; kontrollen efter huvudkörningen, med en bredare ordlista, träffade 58. Båda ger samma resultat.

## 6. Diskussion

**Vad fyndet säger.** De som reste runstenarna vände texten mot vägen. Det gäller i hela materialet, i var halva, utan Uppland, socken för socken och med en sten per ristare, så det beror inte på några få platser eller verkstäder. Det gäller också utan de stenar som har rests upp på nytt, som annars kunde ha vänts mot dagens väg, och när kodningsfelen i 4.5 rättas. Vi fann inget tecken på att ristningen vändes mot ett visst väderstreck eller mot gården, men de proven är svagare än provet mot vägen, och att ett samband inte syns är inte detsamma som att det saknas.

**Mot tidigare forskning.** Resultatet ger ett mått i hela materialet åt det Ekholm (1950) såg vid enstaka stenar och åt tanken att stenarna vid vägarna restes för att synas (Bollaert 2016). Det står inte emot att många stenar restes vid gravfält (Klos 2009): en sten kan stå vid ett gravfält och vända texten mot vägen förbi det, så som Ekholm (1950, s. 138) beskrev stenen vid Bollsta. Vattenlederna mäts inte här; McLeod (2014) visar att U 170 vänder texten mot en forntida vik och har vägen bakom sig.

**Svagheter, i ordning efter vikt.**

1. **Vägen är ofta dagens väg.** Registrets text anger vägen vid inventeringen. Sambandet är starkast med vägar ur registrets text ({pc(RU['bara_text']['andel_inom_45'])} procent inom 45 grader) och svagt med registrerade äldre färdvägar och vägmärken ({pc(RU['bara_registrerad']['andel_inom_45'])} procent mot 25 väntat, {pfmt(RU['bara_registrerad']['p'])}). Har vägar dragits om förbi stenarna, eller stenar ställts upp mot en nyare väg, kan sambandet med dagens väg vara starkare än med vikingatidens.
2. **Urvalet.** Bara {DUP['n_stenar']} stenar på sin plats har en enda riktning i registret, och vi vet inte vad som styrde vilka stenar som fick en sådan uppgift.
3. **Återresningar.** Ordsökningen fångar inte alla stenar som har rests upp på nytt, och en återresning kan vända en sten (Ekholm 1950, s. 140). Resultatet är dock starkare utan de stenar den hittar, inte svagare.
4. **Gården.** Bytomterna är kända först från 1600- och 1700-talens kartor, och vikingatidens gårdar kan ha legat någon annanstans. Att vi inte fann något samband med gården säger därför mindre än sambandet med vägen.
5. **Upplösningen.** Riktningarna anges i sexton väderstreck, alltså i steg om 22,5 grader.

**Vad som skulle fälla fyndet.** Att sambandet försvann när vägarna mättes på de äldsta lantmäterikartorna, eller att en ny inventering av fler stenars riktning gav en jämn fördelning mot vägen.

## 7. Slutsats

Runstenarna vände sin text mot vägen: hälften av ristningarna vetter inom 45 grader från vägen, mot en fjärdedel om riktningen vore slumpvis, och sambandet tål varje känslighetsanalys, också när kodningsfelen rättas. Ristarna skrev för den som gick förbi. Nästa steg är att mäta vägarna på 1600- och 1700-talens kartor.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION} (git-taggen v3.0.0, 2026-10-20), ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen. Kodläget: huvudanalysen i commit 74ca1ef (2026-10-29), känslighetsanalyserna i d0f5a6b (2026-10-31) och rapportversion 2 i 4f80a63 (2026-11-01); kontrollen i 4.5 tillkom med rapportversion {REPORT_VERSION}. All kod, analysplanerna och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Korpusen: Rundata, fryst för analysen som korpus `{IN['korpus']['huvud']}` ({IN['korpus']['huvud_skapad']}), med regeln för flyttade stenar efter rättelsen den 27 oktober 2026 (commit 07d2ec0). Steget med den regeln i 5.3 läser korpus `{IN['korpus']['flyttregel_steget']}`, som har samma rader.
- Analysplanerna: `analysplaner/2026-10-29-ristningens-riktning.md` och `analysplaner/2026-10-31-riktning-trappan.md`, med kontrollsummorna i `.sha256`-filerna bredvid.
- Analysen: `utdata/riktning/analys.py` (resultat `riktning.json`, stenarna i `stenar.csv`); känslighetsanalyserna `utdata/riktning/trappa.py` (`trappan.json`).
- Kontrollen i 4.5: `utdata/riktning/gon_kontroll.py` (`gon_kontroll.json`) läser gon-tilläggen, räknar varje sten en gång och gör om alla känslighetsanalyser; med de gamla riktningarna ger den exakt `trappan.json`.
- Registret: Riksantikvarieämbetets kulturmiljöregister via K-samsök (CC0); vägarna kommer bara därifrån. Filerna i `data/raa/` versionshanteras inte utan hämtas med `scripts/fetch_kmr_runstenar.py` (runstenarnas poster, hämtade {IN['kmr_runstenar']['hamtad']}), `scripts/fetch_raa_remains.py` (färdvägar, {IN['lamningar_fardvagar']['hamtad_filtid']}) och `scripts/fetch_raa_extra.sh` (vägmärken och bytomter, {IN['lamningar_vagmarke']['hamtad_filtid']}); Runor med `scripts/fetch_runor.py` ({IN['runor_2020']['hamtad']}). Kontrollsummorna för de hämtade filerna står i `gon_kontroll.json`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_riktning.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer.

## Referenser

- Bollaert, J. 2016. *Runstenar längs vägen. En undersökning av samband mellan runstenarnas placering och utformning*. Masteruppsats. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, s. 137–147.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Larsson, M. G. 2010. Recension av L. Klos, *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. *Futhark. International Journal of Runic Studies* 1, s. 249–253.
- Mardia, K. V. & Jupp, P. E. 2000. *Directional Statistics*. Chichester: Wiley.
- McLeod, S. 2014. The rediscovery of U 170: runestones, churchyards, and burial grounds in Sweden. *Journal of the North Atlantic* 25, s. 1–8. doi:10.3721/037.006.2503
- Riksantikvarieämbetet. Kulturmiljöregistret, via K-samsök. CC0. Hämtat {IN['lamningar_fardvagar']['hamtad_filtid']} och {IN['kmr_runstenar']['hamtad']}.
- Riksantikvarieämbetet. 2020. *Runor*. Runinskrifter i Sverige, databas. Hämtat {IN['runor_2020']['hamtad']}.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholms universitet.

:::box Det viktigaste i korthet
- Runstenarna vände sin text mot vägen. Vi såg inget tecken på att väderstrecket eller gården styrde hur de vändes.
- Ristarna skrev för den som gick förbi: stenen var ett budskap till vägfarande, inte bara ett minne vid hemmet.
- Det tål varje kontroll vi har, men vägen i registret är ofta dagens väg, så nästa prov är de gamla kartorna.
:::

{LOG_SV}
"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY} (first published {FIRST_PUBLISHED}). Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, roads, placement, orientation of the inscription, circular statistics, Swedish register of ancient monuments, pre-registration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** Where the runestones were raised has long been discussed, and the roads are one of the answers: stones by roads were seen. Single stones have been described as turned towards the road, but nobody has measured across the whole material which way the inscription was turned. The question here is whether the text was turned towards the road, towards the farm or towards a particular point of the compass.
**Material.** {R['n']} records in the Swedish register of ancient monuments on {DUP['n_stenar']} Swedish Viking-Age runestones that still stand in place and for which the register gives the direction the inscription faces. For {R['n_vag']} of the records there is a road to measure against, for {R['n_gard']} a farm site.
**Method.** A pre-registered study with four tests and Holm correction. The measure is the cosine of the angle between the inscription's direction and the direction to the road, compared with 9,999 shuffles of the directions within the province. Internal replication in two halves and ten sensitivity analyses under a locked addendum plan.
**Results.** Half of the stones, {pc(H2['andel_inom_45'])} percent, turn the inscription within 45 degrees of the road, against a quarter if the direction were random. Mean cos {e2(H2['medel_cos'])} against {e2(H2['vantat'])} expected, {pfmt(H2['p'], True)}, Holm-corrected p = 0.0004. It holds in both halves and in every sensitivity analysis, also without Uppland, parish by parish, with one stone per carver and without re-erected stones. Two coding errors found after publication do not change this; corrected, the association is slightly stronger (mean cos {e2(GR['alla']['medel_cos'])}, {pc(GR['alla']['andel_inom_45'])} percent within 45 degrees; section 4.5). The directions do not differ detectably from an even spread, and we found no sign that the inscription was turned towards the farm (farm sites are known only from 17th–18th-century maps).
**Conclusion.** The text was turned towards those passing by on the road. The main weakness is that the road in the register is often today's road; with only registered older routes and road markers the association is weak ({pc(RU['bara_registrerad']['andel_inom_45'])} percent within 45 degrees against 25 expected) but goes the same way.

## 1. Introduction

Gunnar Ekholm (1950) asked where the runestones were raised and answered that the stones of Uppland largely stand by the roads and waterways of the past, and that the stones at grave fields, too, are often explained by the road that passed the grave field. He noted that single stones are turned towards the road, at Bollsta in Vaksala (p. 138) and on Särsta land in Knivsta (p. 139), and that a re-erection can turn a stone: a stone on Ängby land near Knivsta has faced the railway since it was raised again in the 1860s (p. 140). Torun Zachrisson (1998) has related the stones to farm, boundary and grave field, and Lydia Klos (2009) has argued that most were raised at grave fields. Mats G. Larsson (2010) has objected that the grave fields are thereby strongly overstated at the expense of other locations, and that Klos sets far stricter requirements than earlier research for what counts as an ancient road (see also McLeod 2014). Johan Bollaert (2016) compared stones along three Viking-Age roads with other stones in the same districts and found that the stones by the roads more often have striking ornament and more often belong to monuments of several stones, which supports that they were raised to be seen.

What is missing is a measure across the whole material of how the inscription itself was turned. Ekholm's observations concern single stones, and a stone may stand by a road but turn its text another way. The aim here is to test whether the inscription was turned towards the road, towards the farm or towards a particular point of the compass, with the information on the inscription's direction that the register gives for some stones.

## 2. Pre-registration: hypothesis and plan

The hypotheses, measures and rules of interpretation were written down in an analysis plan on 29 October 2026, before any direction had been computed. The plan has the SHA-256 checksum `{SHA['2026-10-29-ristningens-riktning']}…` (see Data and code). Before locking only the number of records was known: 456 records in the register give a direction, 369 concern a single stone with one direction, 219 of these stand in place, and 88 of the 369 mention a road with a compass point.

The plan tests four hypotheses with Holm correction: H1 that the directions are not evenly spread over the compass, H2 that the inscription is turned towards the road, H3 that it is turned towards the farm and H4 that bridge and road stones are turned towards the road more than others. A hypothesis *holds* when Holm p is below 0.05 and the direction is the same with p below 0.05 in both halves.

The plan did not contain the project's fixed sensitivity analyses, which are built for associations between two traits and not for directions. The corresponding steps for directions were therefore fixed in an addendum plan on 31 October 2026 (SHA-256 `{SHA['2026-10-31-riktning-trappan']}…`), before they were computed. Two of the steps, the halves and the source of the road, were already in the main plan. A check of re-erected stones was made after the main run on 29 October with a different word list; in the addendum plan the word list was locked before the step was computed.

## 3. Material

- **The stones.** Swedish Viking-Age runestones in the Scandinavian Runic-text Database (Rundata) that still stand in place and have a known location, and whose record in the Swedish National Heritage Board's register of ancient monuments concerns just that stone and gives one direction with the words "faces" and one of sixteen compass points: {R['n']} records, which concern {DUP['n_stenar']} stones (five stones have two records each and were counted twice in the locked analysis; see 4.5). Runestones only.
- **The road.** First the register's own statement of the stone's position relative to a road ("5 m E of road"; the road then lies in the opposite direction): {R['n_vag_text']} stones. Otherwise the nearest registered route or road marker within 500 metres. {R['n_vag']} stones with a road in all. The roads come from the National Heritage Board's register only.
- **The farm.** The nearest registered village or farm site within one kilometre: {R['n_gard']} stones.
- **The directions** are computed as bearings from the stone, with north as 0 degrees and the compass points in steps of 22.5 degrees.
- **The halves** are the project's fixed division parish by parish.

## 4. Method

**4.1 The measure.** For each stone the cosine of the angle between the inscription's direction and the direction to the road is computed: 1 when the inscription faces the road straight on, 0 when it faces sideways and −1 when it faces away. The mean over the stones is compared with 9,999 shuffles in which the inscriptions' directions are redistributed among the stones within the same province, so that each province's general pattern of directions is kept. The test is one-sided. The share of stones within 45 degrees of the road is also reported; if the direction were random it would be a quarter.

**4.2 The other hypotheses.** H1 is tested with Rayleigh's test of uniformity (Mardia & Jupp 2000). H3 is tested like H2 against the direction to the farm. H4 compares the mean cos towards the road between bridge and road stones and the others, with the label shuffled within the province, two-sided.

**4.3 Correction and replication.** Holm correction (Holm 1979) over the four tests. Each hypothesis is also tested in each half on its own.

**4.4 The sensitivity analyses** under the addendum plan: the halves; without one province at a time (provinces with at least ten stones with a road; significance required only where at least two thirds of the stones remain); the parish as the unit, with one value per parish; one stone per secure carver; without re-erected stones; without stones the National Heritage Board's register Runor (2020) gives as moved; with the rule for moved stones after the correction of 27 October 2026 (see Data and code); only roads from the register text; and only registered routes and road markers. A step holds when the mean cos lies above the expected value and p is below 0.05.

**4.5 Deviations from the plan.** The analysis followed the plan, but a review before archiving (5 November 2026) found two coding errors in how the register text was read. The numbers in the results section are those of the locked analysis and have not been changed; the errors and a check made afterwards are reported here.

- **Gon qualifiers.** Nine road bearings and six inscription bearings with a gon qualifier ("V 40cg S", that is 40 gon or 36 degrees from west towards south; a gon is one four-hundredth of a full turn) were read as a single compass point. This concerns {G['n_rattade_vagar']} of the {R['n_vag_text']} roads from the register text, with errors of {r0(min(FV))}–{r0(max(FV))} degrees, and {G['n_rattade_ristningar']} of the {R['n']} inscription directions, with errors of {r0(min(FI))}–{r0(max(FI))} degrees. Corrected, the association is slightly stronger: mean cos {e2(GR['alla']['medel_cos'])} instead of {e2(G['last']['alla']['medel_cos'])} and {pc(GR['alla']['andel_inom_45'])} percent within 45 degrees instead of {pc(G['last']['alla']['andel_inom_45'])}; with only roads from the register text {e2(GR['bara_text']['medel_cos'])} instead of {e2(G['last']['bara_text']['medel_cos'])}.
- **Double records.** Five stones have two records each in the register and were counted twice; the {DUP['n_poster']} records concern {DUP['n_stenar']} stones, and the {DUP['n_poster_med_vag']} with a road concern {DUP['n_stenar_med_vag']}. Counting each stone once, with corrected directions, gives mean cos {e2(GU['alla']['medel_cos'])} and {pc(GU['alla']['andel_inom_45'])} percent within 45 degrees.
- **The check.** With the corrected directions the main test and every sensitivity analysis were rerun with the same code and the same shuffles as under the plans; with the old directions the code reproduces the published numbers exactly. Every step holds, both with the {DUP['n_poster']} records and with each stone counted once. The main test gives {pfmt(LR['rungs']['huvud']['p'], True)}, half B {pfmt(LR_B, True)} and {pfmt(LU_B, True).replace('p = ', '')} respectively, and the weakest step, only registered routes and road markers, {pfmt(LR_R, True)} and {pfmt(LU_R, True).replace('p = ', '')}. H1 and H3 do not change in substance (Rayleigh's test {pfmt(GR['H1_rayleigh']['p'], True)}; towards the farm {pfmt(GR['H3_gard']['p'], True)}).

## 5. Results

**5.1 Towards the road (H2).** Of the {H2['n']} stones with a road, {pc(H2['andel_inom_45'])} percent turn the inscription within 45 degrees of the road. The mean cos is {e2(H2['medel_cos'])} against {e2(H2['vantat'])} expected, {pfmt(H2['p'], True)}, the lowest value 9,999 shuffles can give, and Holm-corrected p = 0.0004. Half A: {HA['H2']['n']} stones, mean cos {e2(HA['H2']['medel_cos'])}, {pfmt(HA['H2']['p'], True)}. Half B: {HB['H2']['n']} stones, mean cos {e2(HB['H2']['medel_cos'])}, {pfmt(HB['H2']['p'], True)}. H2 *holds* by the plan's rule. In plain words: of the stones where we know where the road ran, half turn their text towards the road, within 45 degrees either way; if the direction were random, a quarter would.

{chart(False)}

{FIG_EN}

**5.2 The compass, the farm and the bridges (H1, H3, H4).** The directions do not differ detectably from an even spread over the compass: Rayleigh's test {pfmt(H1['p'], True)} (in half A {pfmt(HA['H1']['p'], True)}, in half B {pfmt(HB['H1']['p'], True)}). West is the most common ({ST['V']} stones), then north ({ST['N']}), east ({ST['Ö']}) and south ({ST['S']}); {pc(DESC['andel_soder'])} percent face somewhere between south-east and south-west. Towards the farm: mean cos {e2(H3['medel_cos'])} against {e2(H3['vantat'])}, {pfmt(H3['p'], True)}; so we found no sign that the inscription was turned towards the farm, but the farm sites are known only from the maps of the seventeenth and eighteenth centuries. The bridge and road stones ({H4['n_bro']} with a road) do not differ detectably from other stones, {pfmt(H4['p'], True)}, but with nine stones the test says little. None of the three hypotheses holds.

**The plan's robustness tests.** With the farm within 500 metres instead of one kilometre ({G500['n']} stones): mean cos {e2(G500['medel_cos'])} against {e2(G500['vantat'])}, {pfmt(G500['p'], True)}. With only Uppland and Södermanland ({US['n']} stones with a road): mean cos {e2(US['medel_cos'])} against {e2(US['vantat'])}, {pfmt(US['p'], True)}, {pc(US['andel_inom_45'])} percent within 45 degrees. The plan's two other tests, only roads from the register text and only registered routes and road markers, are among the sensitivity analyses in 5.3.

**5.3 The sensitivity analyses.** All hold:

{rung_en('halva_A', 'Half A')}
{rung_en('halva_B', 'Half B')}
- Without one province at a time: without Uppland ({LO['U']['n']} stones left, half, so only the direction is required) mean cos {e2(LO['U']['medel_cos'])}, {pfmt(LO['U']['p'], True)}; without Södermanland ({LO['Sö']['n']}) {e2(LO['Sö']['medel_cos'])}, {pfmt(LO['Sö']['p'], True)}; without Östergötland ({LO['Ög']['n']}) {e2(LO['Ög']['medel_cos'])}, {pfmt(LO['Ög']['p'], True)}.
{rung_en('socken', f"The parish as the unit, {TR['n_parishes']} parishes")}
{rung_en('en_per_ristare', f"One stone per secure carver, {TR['n_carvers']} carvers")}
{rung_en('utan_aterresta', f"Without re-erected stones, {TR['n_reerected']} removed")}
{rung_en('utan_flyttade_runor', f"Without stones Runor gives as moved, {TR['n_moved_runor']} removed")}
- With the rule for moved stones after the correction of 27 October 2026 none of the {H2['n']} counts as moved, since the main analysis is already built on that rule; the result is the same as the main test.
{rung_en('bara_text', f"Only roads from the register text, {pc(RU['bara_text']['andel_inom_45'])} percent within 45 degrees")}
{rung_en('bara_registrerad', f"Only registered routes and road markers, {pc(RU['bara_registrerad']['andel_inom_45'])} percent within 45 degrees")}

The sensitivity analyses drew new shuffles, so the p values differ slightly from those of the main test: half B has {pfmt(RU['halva_B']['p'], True)} here and {pfmt(HB['H2']['p'], True)} in 5.1. The addendum plan's word list for re-erected stones hits {TR['n_reerected_alla_219']} of all {R['n']} stones; the check after the main run, with a wider word list, hit 58. Both give the same result.

## 6. Discussion

**What the finding says.** Those who raised the runestones turned the text towards the road. It holds in the whole material, in each half, without Uppland, parish by parish and with one stone per carver, so it does not depend on a few places or workshops. It also holds without the stones that have been re-erected, which could otherwise have been turned towards today's road, and when the coding errors in 4.5 are corrected. We found no sign that the inscription was turned towards a particular point of the compass or towards the farm, but those tests are weaker than the test against the road, and an association that is not seen is not the same as one that is absent.

**Against earlier research.** The result gives a measure across the whole material to what Ekholm (1950) saw at single stones and to the idea that the stones by the roads were raised to be seen (Bollaert 2016). It does not contradict that many stones were raised at grave fields (Klos 2009): a stone can stand at a grave field and turn its text towards the road past it, as Ekholm (1950, p. 138) described the stone at Bollsta. The waterways are not measured here; McLeod (2014) shows that U 170 turns its text towards a former bay and has the road behind it.

**Weaknesses, in order of weight.**

1. **The road is often today's road.** The register text gives the road at the time of the survey. The association is strongest with roads from the register text ({pc(RU['bara_text']['andel_inom_45'])} percent within 45 degrees) and weak with registered older routes and road markers ({pc(RU['bara_registrerad']['andel_inom_45'])} percent against 25 expected, {pfmt(RU['bara_registrerad']['p'], True)}). If roads were later laid past the stones, or stones were reset to face a newer road, the association with today's road may be stronger than with the Viking-Age one.
2. **The selection.** Only {DUP['n_stenar']} stones in place have a single direction in the register, and we do not know what decided which stones received such a statement.
3. **Re-erections.** The word search does not catch every stone that has been re-erected, and a re-erection can turn a stone (Ekholm 1950, p. 140). The result is, however, stronger without the stones it finds, not weaker.
4. **The farm.** The farm sites are known only from the maps of the seventeenth and eighteenth centuries, and the Viking-Age farms may have lain elsewhere. That we found no association with the farm therefore says less than the association with the road.
5. **The resolution.** The directions are given in sixteen compass points, that is in steps of 22.5 degrees.

**What would overturn the finding.** If the association disappeared when the roads were measured on the oldest land-survey maps, or if a new survey of more stones' directions gave an even distribution relative to the road.

## 7. Conclusion

The runestones turned their text towards the road: half of the inscriptions face within 45 degrees of the road, against a quarter if the direction were random, and the association withstands every sensitivity analysis, also when the coding errors are corrected. The carvers wrote for those who passed by. The next step is to measure the roads on the maps of the seventeenth and eighteenth centuries.

## Data and code

The analysis was made in Vitki {APP_VERSION} (git tag v3.0.0, 2026-10-20), an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version. Code state: the main analysis in commit 74ca1ef (2026-10-29), the sensitivity analyses in d0f5a6b (2026-10-31) and report version 2 in 4f80a63 (2026-11-01); the check in 4.5 was added with report version {REPORT_VERSION}. All code, the analysis plans and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The corpus: Rundata, frozen for the analysis as corpus `{IN['korpus']['huvud']}` ({IN['korpus']['huvud_skapad']}), with the rule for moved stones after the correction of 27 October 2026 (commit 07d2ec0). The step with that rule in 5.3 reads corpus `{IN['korpus']['flyttregel_steget']}`, which has the same rows.
- The analysis plans: `analysplaner/2026-10-29-ristningens-riktning.md` and `analysplaner/2026-10-31-riktning-trappan.md`, with their checksums in the `.sha256` files beside them.
- The analysis: `utdata/riktning/analys.py` (results `riktning.json`, the stones in `stenar.csv`); the sensitivity analyses `utdata/riktning/trappa.py` (`trappan.json`).
- The check in 4.5: `utdata/riktning/gon_kontroll.py` (`gon_kontroll.json`) reads the gon qualifiers, counts each stone once and reruns every sensitivity analysis; with the old directions it reproduces `trappan.json` exactly.
- The register: the Swedish National Heritage Board's register of ancient monuments via K-samsök (CC0); the roads come from there only. The files in `data/raa/` are not under version control but are fetched with `scripts/fetch_kmr_runstenar.py` (the runestone records, fetched {IN['kmr_runstenar']['hamtad']}), `scripts/fetch_raa_remains.py` (routes, {IN['lamningar_fardvagar']['hamtad_filtid']}) and `scripts/fetch_raa_extra.sh` (road markers and farm sites, {IN['lamningar_vagmarke']['hamtad_filtid']}); Runor with `scripts/fetch_runor.py` ({IN['runor_2020']['hamtad']}). The checksums of the fetched files are in `gon_kontroll.json`.
- The report is built by `utdata/blogg/build/build_rapport_riktning.py`, which reads every number from the result files and stops if anything disagrees.

## References

- Bollaert, J. 2016. *Runstenar längs vägen. En undersökning av samband mellan runstenarnas placering och utformning*. Master's thesis. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, pp. 137–147.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Larsson, M. G. 2010. Review of L. Klos, *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. *Futhark. International Journal of Runic Studies* 1, pp. 249–253.
- Mardia, K. V. & Jupp, P. E. 2000. *Directional Statistics*. Chichester: Wiley.
- McLeod, S. 2014. The rediscovery of U 170: runestones, churchyards, and burial grounds in Sweden. *Journal of the North Atlantic* 25, pp. 1–8. doi:10.3721/037.006.2503
- Swedish National Heritage Board. The register of ancient monuments (Kulturmiljöregistret), via K-samsök. CC0. Retrieved {IN['lamningar_fardvagar']['hamtad_filtid']} and {IN['kmr_runstenar']['hamtad']}.
- Swedish National Heritage Board. 2020. *Runor*. Runic inscriptions in Sweden, database. Retrieved {IN['runor_2020']['hamtad']}.
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholm University.

:::box The essentials
- The runestones turned their text towards the road. We saw no sign that the compass or the farm decided how they were turned.
- The carvers wrote for those who passed by: the stone was a message to travellers, not only a memorial by the home.
- It withstands every check we have, but the road in the register is often today's road, so the next test is the old maps.
:::

{LOG_EN}
"""

JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
    assert not re.search(r"(?<![\w-])-\d", head), "minustecken, inte bindestreck"
    assert not re.search(r"\b(3f58e9339191761e|e83202e01a5e6d27|74ca1ef|d0f5a6b|4f80a63|07d2ec0)\b", head)  # versionsnycklar bara under Data och kod
    for ref in ("Bollaert", "Ekholm", "Holm", "Klos", "Larsson", "Mardia", "McLeod", "Zachrisson"):
        assert f"{ref}," in b.split("## Referenser" if b is body else "## References")[1] and ref in head, ref  # citerad och listad
    assert "Kvant, V. 2026" not in b and "137 ff" not in b and "dagens regel" not in b and "today's rule" not in b
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
assert "I klartext" in body and "In plain words" in body_en  # mallen version 4
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion 3, 2026-11-05 (först publicerad 2026-10-31). Tidslinje: ")
assert body_en.split("\n", 1)[0].startswith("*Viktor Kvant, independent researcher. Fully tested finding. Report version 3, 2026-11-05 (first published 2026-10-31). Timeline: ")
assert body.rstrip().endswith(LOG_SV) and body_en.rstrip().endswith(LOG_EN)  # ändringsloggen sist
assert body.count("\n## ") == body_en.count("\n## ") and body.count("\n- ") == body_en.count("\n- ")  # sv och en i takt

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Geografi"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_riktning.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body.split("## Data")[0].split()), "före Data och kod;", len(body_en.split()), "words")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p_ for p_ in blog._all() if p_.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Rapport|riktning", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
