"""Forskningsrapport, metodrapport (låst mall utdata/rapporter/MALL.md, version 4; Metodrapport, fullt prövad):
"Grupper av runstenar med samma hand, också utan namn" (sv + en). Planerna analysplaner/2026-11-23-nya-ristare-program.md
(f5ce4fe7), …-slutprov-1.md (081bf667), …-slutprov-2-litteraturen.md (706be174) och 2026-11-24-nya-ristare-3d.md
(ffb9b051); resultaten i utdata/nya_ristare/. Uppföljningen 2026-11-24-nya-ristare-ornamentik.md (bec4b16b, slutprov 3,
provdelens andra öppning) nämns i slutsatsen. Alla siffror asserteras mot filerna.
    ../../../.venv/bin/python build_rapport_nya_ristare.py [--write | --update DOC]"""
import datetime as dt
import hashlib
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
FP = "510ebfb3acc9a229"
APP_VERSION = "3.1.0"
REPORT_VERSION = 1
TODAY = "2026-11-25"
D = os.path.join(ROOT, "utdata", "nya_ristare")
J = lambda f: json.load(open(os.path.join(D, f), encoding="utf-8"))  # noqa: E731
PLANS = {"program": ("2026-11-23-nya-ristare-program.md", "f5ce4fe7"), "s1": ("2026-11-23-nya-ristare-slutprov-1.md", "081bf667"),
         "s2": ("2026-11-23-nya-ristare-slutprov-2-litteraturen.md", "706be174"), "3d": ("2026-11-24-nya-ristare-3d.md", "ffb9b051"),
         "orn": ("2026-11-24-nya-ristare-ornamentik.md", "bec4b16b")}
SHA = {}
for k, (f, pre) in PLANS.items():
    h = hashlib.sha256(open(os.path.join(ROOT, "analysplaner", f), "rb").read()).hexdigest()
    assert h.startswith(pre), (f, h)
    SHA[k] = h

# ---- siffrorna -------------------------------------------------------------------------------------------------------
S1, U1 = J("slutprov_P.json"), J("slutprov_U.json")
A, O = S1["alla"], S1["onämnda"]
assert (A["grupper"], A["bättre"], A["sämre"], round(A["medel_samma"], 2), round(A["medel_kontroll"], 3)) == (42, 23, 8, 0.42, 0.066)
assert (O["grupper"], O["bättre"], O["sämre"], round(O["medel_samma"], 2), round(O["medel_kontroll"], 3)) == (15, 11, 3, 0.69, 0.075)
assert 2.0e-5 < A["p"] < 2.2e-5 and 0.0016 < O["p"] < 0.0018
S2 = J("slutprov2.json")
T1, T2 = S2["T1"], S2["T2"]
assert (S2["facit2_par"], S2["facit2_grupper"], T1["grupper"], T1["bättre"], T1["sämre"]) == (63, 30, 25, 17, 5) and T1["håller"]
assert (round(T1["medel_samma"], 2), round(T1["medel_kontroll"], 3), round(T1["p"], 4)) == (0.46, 0.066, 0.0004)
assert (T2["grupper"], T2["bättre"], T2["sämre"], round(T2["medel_samma"], 2), round(T2["p"], 3)) == (7, 4, 1, 0.26, 0.062)
GR = S2["granskning"]
assert (GR["samma_hand|bekräftad"], GR["samma_hand|ej"], GR["olika_hander|bekräftad"], GR["olika_hander|ej"],
        GR["tillskrivning|bekräftad"], GR["tillskrivning|ej"]) == (74, 19, 38, 4, 131, 37)
GU = {r["tau"]: r for r in J("gruppering_utveckling.json")}
G8 = GU[0.8]
assert (round(G8["precision_namngivna"], 2), round(G8["facit_samma_grupp"], 2), round(G8["grannar_samma_grupp"], 3)) == (0.77, 0.34, 0.029)
assert (round(GU[0.9]["precision_namngivna"], 2), round(GU[0.7]["precision_namngivna"], 2)) == (0.85, 0.69)
PM = J("parmodell_utveckling.json")
M0, M1 = PM["M0 text (överskott)"], PM["M1 alla belägg"]
assert (round(M0["median_percentil"], 2), round(M1["median_percentil"], 2), M1["grupper"], M0["grupper"]) == (0.83, 0.94, 27, 17)
assert round(M1["onämnda"]["median_percentil"], 2) == 0.95 and M1["onämnda"]["grupper"] == 8
K1, KL = J("kontroll_facit.json"), J("lit_kontroll.json")
assert (K1["lika"], K1["stickprov"]) == (30, 40) and (KL["lika_ställen"], KL["ställen"]) == (220, 250)
H3 = J("huggteknik.json")
assert (H3["stenar"], round(H3["H3D"]["p"], 2), H3["H3D"]["håller"]) == (36, 0.24, False)
H3G = {g["grupp"]: g for g in H3["grupper"]}
assert round(H3G["G052"]["p"], 2) == 0.62 and round(H3G["G055"]["p"], 2) == 0.04 and round(H3G["G105"]["p"], 2) == 0.03
GRP = J("grupper.json")
assert len(GRP) == 228 and sum(len(g["stenar"]) for g in GRP) == 1103
TYP = Counter(g["typ"].split()[0] for g in GRP)
assert (TYP["okänd"], TYP["med"], TYP["blandad"]) == (95, 91, 42)
GOOD_UNK = [g for g in GRP if g["typ"] == "okänd hand" and g["underlag"] == "gott"]
assert len(GOOD_UNK) == 77 and sum(1 for g in GRP if g["underlag"] == "svagt") == 23
LIT = {x["id"]: x for x in J("grupper_litteratur.json")}
LB = J("litteratur_besked.json")
LV = Counter(x["besked"] for x in LIT.values())
assert (LV["kopplad tidigare"], LV["ingen tidigare koppling"], LV["ej omnämnd"], LV.get("motsagd", 0) + LV.get("delvis motsagd", 0)) == (75, 138, 15, 0)
LVU = Counter(LIT[g["id"]]["besked"] for g in GOOD_UNK)
assert (LVU["kopplad tidigare"], LVU["ingen tidigare koppling"], LVU["ej omnämnd"]) == (15, 61, 1)
assert (LB["okänd_gott_kopplad_sri_runor"], LB["okänd_gott_kopplad_litteratur"], LB["olika_hander_tvetydiga_uttalanden"]) == (11, 4, 4)
assert LIT["G131"]["samma_hand"][0][:2] == ["Ög 231", "Ög 232"] and "Källström 2020 (Fornvännen)" in LIT["G131"]["samma_hand"][0][2]
EX = J("rapport_extra.json")
assert (EX["slutprov1_alla_sammanslaget"]["samma"], EX["slutprov1_alla_sammanslaget"]["par"]) == (59, 147)
assert (EX["slutprov2_T1_sammanslaget"]["samma"], EX["slutprov2_T1_sammanslaget"]["par"]) == (22, 61)
assert (EX["provdelens_grupper"], EX["provdelens_grupper_med_par"]) == (59, 42)
PU, PS = EX["slutprov1_per_landskap"]["U"], EX["slutprov1_per_landskap"]["Sö"]
assert (PU["grupper"], round(100 * PU["samma"]), round(100 * PU["kontroll"], 1), PS["grupper"], round(100 * PS["samma"]), round(100 * PS["kontroll"], 1)) == (31, 39, 5.4, 7, 49, 10.7)
CB = {(c["från"], c["till"]): c for c in EX["kalibrering"]}
assert (round(100 * CB[(0.8, 0.9)]["andel_samma"]), round(100 * CB[(0.9, 1.0)]["andel_samma"]), round(100 * EX["grundnivå_samma_ristare"])) == (46, 73, 13)
assert (round(100 * CB[(0, 0.2)]["andel_samma"]), round(100 * CB[(0.4, 0.6)]["andel_samma"])) == (4, 15)
HO = EX["holm"]
assert HO["S1"] < 0.001 and HO["T1"] < 0.01 and HO["S2"] < 0.01 and HO["T2"] > 0.05 and HO["H3D"] > 0.05
assert (EX["stabilitet"]["lika_med_1"], EX["stabilitet"]["grupper"]) == (73, 228)
assert round(G8["täckning_namngivna"], 3) == 0.088
assert (S2["olika_händer_par_inom_30km"], S2["av_dem_i_samma_grupp"]) == (9, 0)
G052 = next(g for g in GRP if g["id"] == "G052")
assert G052["stenar"] == ["Sö 131", "Sö 134", "Sö 137", "Sö 319", "Sö 367", "Sö 46"]
DEL = json.load(open(os.path.join(D, "delning.json"), encoding="utf-8"))
assert len(DEL["grupper"]) == 118 and Counter(g["del"] for g in DEL["grupper"]) == {"U": 59, "P": 59}
LOG = open(os.path.join(D, "provdelen_logg.md"), encoding="utf-8").read()
LOGR = [l for l in LOG.splitlines() if l.startswith("- ")]
assert len(LOGR) == 2 and "slutprov 1" in LOGR[0] and "slutprov 3" in LOGR[1]  # provdelen öppnad två gånger: S1, sedan ornamentiken
S3 = json.load(open(os.path.join(D, "ornamentik", "slutprov3.json"), encoding="utf-8"))
assert S3["plan"] == PLANS["orn"][0] and not S3["O1"]["håller"] and S3["O2"]["håller"]  # ornamentiken förbättrar inte grupperna
assert (S3["O1"]["grupper"], S3["O1"]["bättre"], S3["O1"]["sämre"], round(S3["O1"]["p"], 2)) == (25, 2, 4, 0.78)
assert (S3["beskrivande"]["grupper_M1"], S3["beskrivande"]["grupper_utan_säker_M1"]) == (len(GRP), 95)  # appen behåller M1
HG = json.load(open(os.path.join(ROOT, "data", "cache", "r", "corpus", FP, "hand_groups.json"), encoding="utf-8")) \
    if os.path.exists(os.path.join(ROOT, "data", "cache", "r", "corpus", FP, "hand_groups.json")) else None
if HG:
    assert {frozenset(g["stones"]) for g in HG["groups"]} == {frozenset(g["stenar"]) for g in GRP}  # appen visar de prövade grupperna
    STAB = sorted(g["stability"] for g in HG["groups"])
    assert round(STAB[len(STAB) // 2], 2) == 0.67
    assert sum(1 for g in HG["groups"] if g["type"] == "okänd hand" and g["evidence"] == "gott" and g["stability"] >= 0.8) == 39

pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731
d1 = lambda x, en=False: f"{x:.1f}" if en else f"{x:.1f}".replace(".", ",")  # noqa: E731


def pexp(p, en=False):
    m, e = f"{p:.1e}".split("e")
    m = m if en else m.replace(".", ",")
    return f"{m} · 10{str(int(e)).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))}"


def pf(p, en=False):
    if p < 0.001:
        return f"p = {pexp(p, en)}"
    s = f"{p:.4f}" if p < 0.001 else (f"{p:.3f}" if p < 0.01 else f"{p:.2f}")
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


SLUG = "stenar-med-samma-hand"
title = "Runstenar med samma hand"
title_en = "Runestones by the same hand"
summary = ("Metodrapport. En inlärd modell för samma hand bildar grupper av runstenar som kan vara gjorda av samma ristare, "
           "också där ingen namngiven ristare passar. I ett låst slutprov mot runologernas egna uttalanden, som hölls undan tills "
           "metoden var bestämd, hamnade i genomsnitt 42 procent av deras stenpar i samma grupp mot 7 procent för grannstenar på "
           "samma avstånd. Ett andra prov mot uttalanden i Fornvännen, Futhark och åtta avhandlingar gav 46 mot 7 procent.")
summary_en = ("Methods report. A learned model of the same hand forms groups of runestones that may have been made by the same "
              "carver, also where no named carver fits. In a locked final test against the runologists' own statements, held back "
              "until the method was fixed, on average 42 percent of their stone pairs ended up in the same group against 7 percent "
              "for neighbouring stones at the same distance. A second test against statements in Fornvännen, Futhark and eight "
              "theses gave 46 against 7 percent.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report (methods report), report version {REPORT_VERSION}; analysis in "
           f"Vitki {APP_VERSION}. https://vitkirunor.se/en/forskningsrapporter/{SLUG}")
TL_SV = ("planen för arbetet och delningen av runologernas grupper låstes 2026-11-23; modellen byggdes på utvecklingsdelen "
         "2026-11-23; slutprov 1 låstes och kördes 2026-11-23; litteraturen lästes och planen för slutprov 2 låstes 2026-11-23; "
         "uttalandena i litteraturen granskades och slutprov 2 och provet av huggtekniken kördes 2026-11-24; ornamentiken "
         "prövades i ett senare låst prov 2026-11-25")
TL_EN = ("the plan for the work and the split of the runologists' groups were locked 2026-11-23; the model was built on the "
         "development half 2026-11-23; final test 1 was locked and run 2026-11-23; the literature was read and the plan for final "
         "test 2 was locked 2026-11-23; the statements in the literature were reviewed and final test 2 and the test of the carving "
         "technique were run 2026-11-24; the ornament was tried in a later locked test 2026-11-25")
THESES_SV = ("Källström (2007), Zilmer (2005), Stern (2013), Williams (1990), Lagman (1990), Larsson (2002), Åkerström (2020) och "
             "Pereswetoff-Morath (2017)")
THESES_EN = ("Källström (2007), Zilmer (2005), Stern (2013), Williams (1990), Lagman (1990), Larsson (2002), Åkerström (2020) and "
             "Pereswetoff-Morath (2017)")
EXS = EX["slutprov1_alla_sammanslaget"]
EX2 = EX["slutprov2_T1_sammanslaget"]


def chart(sv):
    rows = [":::chart Runologernas stenpar i samma grupp, procent (medel per grupp)" if sv
            else ":::chart The runologists' stone pairs in the same group, percent (mean per group)"]
    for lab_sv, lab_en, r in (("Slutprov 1, alla grupper", "Final test 1, all groups", A),
                              ("Slutprov 1, händer utan namn", "Final test 1, hands without a name", O),
                              ("Slutprov 2, litteraturen", "Final test 2, the literature", T1)):
        rows += [f"# {lab_sv if sv else lab_en} ({r['grupper']} {'grupper' if sv else 'groups'})",
                 f"+{'Samma grupp' if sv else 'Same group'} | {d1(100 * r['medel_samma'], not sv)} | {r['bättre']} {'grupper bättre' if sv else 'groups better'}",
                 f"{'Grannstenar på samma avstånd' if sv else 'Neighbouring stones at the same distance'} | {d1(100 * r['medel_kontroll'], not sv)} | –"]
    rows += ["Källa: Rundata, Runor 2020, Sveriges runinskrifter och litteraturen. Diagram: Vitki."
             if sv else "Source: Rundata, Runor 2020, Sveriges runinskrifter and the literature. Chart: Vitki.", ":::"]
    return "\n".join(rows)


body = f"""*Viktor Kvant, oberoende forskare. Metodrapport, fullt prövad. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, runristare, attribuering, samma hand, gradient boosting, klusteranalys, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Runologer har kopplat ihop många osignerade runstenar med varandra: ”samme ristare som …”. En statistisk modell som bara väljer bland namngivna ristare kan inte se en hand utan namn. Syftet var att pröva om en modell som lär sig vad som skiljer stenar av samma hand från stenar av olika händer kan bilda grupper av stenar som hör ihop, också där ingen namngiven ristare passar.
**Material.** 2 314 svenska vikingatida runstenar i Samnordisk runtextdatabas (Rundata) med koordinater, och alla 312 550 stenpar inom 30 km. Som jämförelse användes runologernas egna uttalanden om samma hand: i Sveriges runinskrifter och Runor 2020 (118 grupper), och i Fornvännen, Futhark och åtta avhandlingar (63 nya par).
**Metod.** En gradient boosting-modell tränades på par av stenar med känd ristare och gav varje stenpar ett värde för samma hand. Stenarna slogs ihop till grupper med genomsnittlig länkning inom 30 km. Runologernas grupper delades slumpvis i en utvecklingsdel och en provdel. Metoden bestämdes på utvecklingsdelen, och provdelen öppnades en gång i ett låst slutprov. Ett andra låst prov gjordes mot litteraturen.
**Resultat.** I provdelen hamnade i genomsnitt {pc(A['medel_samma'])} procent av runologernas stenpar per grupp i samma grupp, mot {pc(A['medel_kontroll'])} procent för grannstenar på samma avstånd ({A['grupper']} grupper, bättre i {A['bättre']} och sämre i {A['sämre']}, {pf(A['p'])}; sammanslaget {EXS['samma']} av {EXS['par']} par). För händer utan namn var det {pc(O['medel_samma'])} mot {d1(100 * O['medel_kontroll'])} procent ({O['grupper']} grupper, {pf(O['p'])}). Mot litteraturen var det {pc(T1['medel_samma'])} mot {pc(T1['medel_kontroll'])} procent ({T1['grupper']} grupper, {pf(T1['p'])}). Omkring {pc(G8['precision_namngivna'])} procent av paren i samma grupp har samma ristare, mätt på stenar med känd ristare, men bara {d1(100 * G8['täckning_namngivna'])} procent av alla par med samma ristare inom 30 km hamnar i samma grupp.
**Vad som inte visades.** Mot litteraturen höll provet inte för händer utan namn ({T2['grupper']} grupper, {pf(T2['p'])}), och huggtekniken i 3D-skanningar visade inte att stenarna i samma grupp liknar varandra ({pf(H3['H3D']['p'])}, 18 stenar).
**Slutsats.** Metoden återfinner runologernas stenpar långt oftare än platsen ensam gör. Den ger {len(GRP)} grupper av minst tre stenar, och {len(GOOD_UNK)} av dem har gott underlag och ingen sten med känd ristare. Grupperna är prövbara hypoteser, inte nya ristare.

## 1. Inledning

Ristarna bakom de flesta runstenar är okända. Axelson (1993) förtecknade de signerade och attribuerade inskrifterna i Mellansverige, Stille (1999) attribuerade stenarna i Fjädrundaland och Källström (2007) studerade ristarnas skriftmiljöer i Norden. Runologerna har också kopplat ihop osignerade stenar med varandra utan att ge ristaren ett namn, i Sveriges runinskrifter och i Runor (Riksantikvarieämbetet 2020). Claiborne Thompson (1975) visade hur stavningen skiljer ristare åt, och Laila Kitzler Åhfeldt (2002, 2020) har skilt ristare åt med huggspårens form i laserskanningar.

En modell som väljer bland de namngivna ristarna kan inte se en hand utan namn. Prövad mot runologernas grupper ”samma som gjort X” i Runor 2020 gav en sådan modell samma ristare ungefär lika ofta som för grannstenar på samma avstånd (Kvant 2026). Ett mått på textlikhet utöver grannarna kände igen runologernas par, men grupper byggda av det blev bygder, inte händer (opublicerade försök, se Data och kod). En del av förklaringen var ett fel som upptäcktes i detta arbete: de kategoriska språkdragen, till exempel skiljetecknets typ, hade aldrig kommit med i måttet.

I projektets genomgång av Fornvännen, Futhark och avhandlingarna hösten 2026 fann vi ingen metod som bildar grupper av runstenar med samma hand över hela materialet och som har prövats mot runologernas bedömningar med en del av dem undanhållen. Syftet här är att redovisa en sådan metod och två låsta prov av den.

## 2. Förregistrering

Arbetet följde fyra planer som låstes i projektets versionshantering innan det de gällde räknades:
- **Planen för arbetet** (2026-11-23, SHA-256 `{SHA['program'][:16]}…`): hur jämförelsematerialet byggs och delas i en utvecklingsdel och en provdel (grupperna som enheter), och att provdelen bara används i låsta slutprov.
- **Slutprov 1** (2026-11-23, `{SHA['s1'][:16]}…`), låst innan provdelen öppnades. Den bestämde metoden, gränsen τ = 0,8, måttet och beslutsregeln, ordagrant: ”S1 (huvudprov, alla grupper): ensidigt Wilcoxon-test över grupperna. Håller om p < 0,05 och medelandelen i samma grupp är större än kontrollens.” S2 gällde på samma sätt bara grupper med händer utan namn.
- **Slutprov 2** (2026-11-23, `{SHA['s2'][:16]}…`): samma metod och mått mot nya par ur litteraturen (T1 alla grupper; T2 händer utan namn, avgörbart med minst 5 grupper med skillnad). Före låsningen hade en räkning på den ogranskade läsningen setts: 72 av 228 grupper hade minst ett par eller en gemensam ristare i litteraturen. Det avslöjar delvis provets täljare, men provmåttet hade inte setts.
- **Huggtekniken** (2026-11-24, `{SHA['3d'][:16]}…`): om stenar i samma grupp liknar varandra i fyra huggspårsmått mer än stenar av samma bergart.

Slutprov 1 och 2 är de konfirmatoriska proven, huggtekniken är en uppföljning. Jämförelserna mellan modellvarianter (5.3) är utvecklingsarbete och inte prov.

## 3. Material

- **Stenarna.** Samnordisk runtextdatabas (Rundata) 3.1, fryst för analysen. 2 314 svenska vikingatida runstenar med koordinater, utom Bohuslän. Avstånden räknades i SWEREF 99 TM.
- **Paren.** Alla 312 550 stenpar inom 30 km.
- **Beläggen per par** (andelen par där belägget finns): textlikhet i stavning, skiljetecken, språkdrag och formler utöver grannar på samma avstånd (46 %); de kategoriska språkdragen, lika eller olika, som skiljetecknets typ (54 %) och *eftir* eller *at* (45 %); stilgrupp (22 %); korsets form enligt Lagers (2002) typologi i Runor 2020 (23 %); ord om ornamentik (9 %) och runformer (12 %) i Sveriges runinskrifter; gemensamma namn, bergart, kortkvistrunor och avståndet.
- **Träningsparen.** 41 192 par av stenar med säker ristare i Rundata, varav 5 400 med samma ristare.
- **Runologernas grupper.**
  - *Källorna:* de 225 ställen i textbanden av Sveriges runinskrifter där utgivaren säger ”samme ristare”, ”samma hand” eller ”samme mästare”, och Runor 2020:s ”samma som gjort X”. Bara länkar som utgivaren själv står för, säkra eller troliga, togs med; möjliga länkar räknades inte.
  - *Kontrolläsningen:* ställena lästes av Anthropics språkmodell Claude (Claude Opus) i två instanser, en för varje halva. En tredje läsare kontrolläste 40 slumpvis valda ställen och stämde i {K1['lika']} ({pc(K1['lika'] / K1['stickprov'])} procent), under det förutbestämda kravet 85 procent.
  - *Omläsningen:* alla ställen lästes om, som planen föreskrev, med en striktare regel (bara signum som står i texten). Läsningarna stämde i 194 av 225 ställen (86 procent), vilket inte är en ny kontroll. De 62 omstridda paren avgjordes av samma språkmodell mot texten, med skriftlig motivering för 31.
  - *Resultatet:* 409 länkar i 118 grupper, varav 84 är par. De delades slumpvis (frö 20261123) i 59 grupper för utveckling och 59 för prov.
- **Litteraturen** (för slutprov 2).
  - *Underlaget:* 2 490 ställen där en ristare eller ”samma hand” nämns nära ett signum, i Fornvännen, Futhark och åtta avhandlingar: {THESES_SV}.
  - *Läsningen:* 28 instanser av samma språkmodell. En blind kontrolläsning av 250 ställen gav {KL['lika_ställen']} identiska ({pc(KL['lika_ställen'] / KL['ställen'])} procent, många utan uttalande), men på uttalandenivå bara {KL['gemensamma']} gemensamma: {pc(KL['precision_mot_kontroll'])} procent av läsarnas och {pc(KL['täckning_mot_kontroll'])} procent av kontrollens.
  - *Granskningen:* varje uttalande om samma hand, olika händer eller en tillskrivning prövades därför av två oberoende granskare som skulle försöka motbevisa det. Det behölls bara om båda bekräftade: {GR['samma_hand|bekräftad']} av {GR['samma_hand|bekräftad'] + GR['samma_hand|ej']} om samma hand och {GR['olika_hander|bekräftad']} av {GR['olika_hander|bekräftad'] + GR['olika_hander|ej']} om olika händer.
  - *Resultatet:* {S2['facit2_par']} par som inte redan fanns bland runologernas grupper, i {S2['facit2_grupper']} grupper.

## 4. Metod

### 4.1 Modellen för samma hand
- **Klassificeraren:** gradient boosting (många små beslutsträd som läggs till ett i taget och rättar de föregåendes fel) på beläggen och avståndet; saknade belägg lämnas tomma.
- **Träningen:** par av stenar med säker ristare, med ristarna delade slumpvis i fem delar. Ett par av sådana stenar får sitt värde från en modell som inte har sett någon av deras ristares stenar i någon av delarna; för par med olika ristare gäller det minst den ena av dem. Övriga par får medel över de fem modellerna.
- **Undantaget:** par inom runologernas grupper och par som rör provdelens stenar ingick aldrig i träningen.
- **Värdet:** modellen ger ett värde mellan 0 och 1 som rangordnar paren. Det är inte en kalibrerad sannolikhet (5.3).

### 4.2 Grupperna
- **Sammanslagningen:** genomsnittlig länkning. De två grupper med högst medelvärde över alla par mellan dem slås ihop först, men bara om alla deras stenar ligger inom 30 km från varandra. Medelvärdet i stället för den starkaste länken hindrar grupperna från att kedja ihop sig till bygder.
- **Gränsen:** sammanslagningen stannar när inget medelvärde mellan två grupper når τ = 0,8. Gränsen valdes på utvecklingsdelen som den högsta precisionen på par av stenar med känd ristare ({pc(G8['precision_namngivna'])} procent) som samtidigt gav tydlig täckning av utvecklingsdelens par ({pc(G8['facit_samma_grupp'])} mot {d1(100 * G8['grannar_samma_grupp'])} procent för grannar).

### 4.3 Provet
- **Måttet:** per grupp av runologer andelen par inom 30 km i samma grupp, mot andelen stenar på samma avstånd (± 25 procent, minst ± 1 km) från var och en av parets stenar, utanför runologernas grupp, som ligger i samma grupp som den stenen.
- **Testet:** ensidigt Wilcoxon-test (ett rangtest utan antagande om normalfördelning) över grupperna, så att en stor grupp inte väger mer än en liten.
- **Bortfallet:** av provdelens {EX['provdelens_grupper']} grupper har {EX['provdelens_grupper_med_par']} minst ett par inom 30 km bland stenarna med koordinater. Resten kan inte prövas.

### 4.4 Avvikelser från planerna
- **Omläsningen** av Sveriges runinskrifter gjordes med en striktare regel än den första läsningen, en regel som infördes efter att oenigheterna setts. De omstridda paren avgjordes av samma språkmodell, inte av en människa.
- **Kontrollen** tar stenar på samma avstånd från var och en av de två stenarna i ett par. Planens text säger ”från a”.
- **Gränsen τ** valdes med precisionen på alla par av stenar med känd ristare, också provdelens stenar med känd ristare i Rundata. Provdelens uttalanden om samma hand och provdelens grupper med händer utan namn ingick inte.
- **Ett kodfel i den beskrivande räkningen av olika händer** (inte i proven): ett uttalande om att en sten har en annan hand än flera andra delades upp i alla par, så att Stern (2013) fick säga att U 43 och U 79 har olika händer, fast hon tillskriver båda Arnfast. Rättat; nu används bara uttalanden om två stenar och listor över namnbärare (fyra uttalanden är tvetydiga).
- **Runhöjd och stenhöjd** prövades på utvecklingsdelen, gav inget lyft och togs inte med.
- **Märkningen ”svagt underlag”** (23 grupper, mest fragment från samma fyndplats som hålls ihop av platsen) lades till efter att grupperna setts. Den ingår inte i proven.
- **I övrigt** inga avvikelser.

## 5. Resultat

### 5.1 Slutprov 1
- **Alla grupper:** i provdelen hamnade i genomsnitt {pc(A['medel_samma'])} procent av runologernas stenpar per grupp i samma grupp, mot {pc(A['medel_kontroll'])} procent för grannstenar på samma avstånd. Det gällde {A['grupper']} grupper, bättre i {A['bättre']} och sämre i {A['sämre']}, {pf(A['p'])}. Sammanslaget över paren var det {EXS['samma']} av {EXS['par']} ({pc(EXS['andel'])} procent).
- **Grupper med händer utan namn**, där ingen sten har en känd ristare: {pc(O['medel_samma'])} mot {d1(100 * O['medel_kontroll'])} procent ({O['grupper']} grupper, bättre i {O['bättre']}, sämre i {O['sämre']}, {pf(O['p'])}).
- **Båda proven höll.** På utvecklingsdelen hade samma mått gett {pc(U1['alla']['medel_samma'])} mot {pc(U1['alla']['medel_kontroll'])} procent.
- **Holm-korrigering** (en justering för att flera prov gjordes) över rapportens fem förregistrerade prov ändrar inte utfallen.

{chart(True)}

I klartext: när runologerna säger att två stenar är gjorda av samma hand hamnar de i samma grupp ungefär två gånger av fem, medan en sten på samma avstånd hamnar där ungefär en gång av femton. För händer utan namn i provdelen är det ungefär två gånger av tre.

### 5.2 Per landskap
Uppland: {PU['grupper']} grupper, {pc(PU['samma'])} procent mot {d1(100 * PU['kontroll'])}. Södermanland: {PS['grupper']} grupper, {pc(PS['samma'])} procent mot {d1(100 * PS['kontroll'])}. Östergötland, Västmanland och Öland har en eller två grupper var. Per ristare går det inte att redovisa, eftersom de flesta grupperna saknar namn.

### 5.3 Värdena, precisionen och utvecklingsarbetet
- **Kalibreringen:** värdet är inte en sannolikhet. Bland par av stenar med känd ristare hade {pc(CB[(0, 0.2)]['andel_samma'])} procent samma ristare under 0,2, {pc(CB[(0.4, 0.6)]['andel_samma'])} procent vid 0,4–0,6, {pc(CB[(0.8, 0.9)]['andel_samma'])} vid 0,8–0,9 och {pc(CB[(0.9, 1.0)]['andel_samma'])} över 0,9 (grundnivå {pc(EX['grundnivå_samma_ristare'])} procent). Ordningen stämmer, nivåerna inte.
- **Precisionen i grupperna** på par av stenar med känd ristare var {pc(GU[0.9]['precision_namngivna'])} procent vid τ = 0,9, {pc(G8['precision_namngivna'])} procent vid 0,8 och {pc(GU[0.7]['precision_namngivna'])} procent vid 0,7. Täckningen är låg: vid 0,8 hamnar {d1(100 * G8['täckning_namngivna'])} procent av alla par med samma ristare inom 30 km i samma grupp. Grupperna är alltså få och snäva.
- **Modellvarianterna på utvecklingsdelen:** runologernas partner hamnade i median över {pc(M1['median_percentil'])} procent av stenarna på samma avstånd med alla belägg, mot {pc(M0['median_percentil'])} procent med bara stavning och språkdrag. De kategoriska språkdragen stod för en stor del av lyftet. Gemensamma namn tillförde inget.
- **Stabiliteten:** i två omträningar med andra slumpvisa delningar stannade i median {pc(EX['stabilitet']['median'])} procent av en grupps par ihop. {EX['stabilitet']['lika_med_1']} av {EX['stabilitet']['grupper']} grupper stannade helt ihop i båda.

### 5.4 Slutprov 2: litteraturen
- **De nya paren ur litteraturen:** i genomsnitt {pc(T1['medel_samma'])} procent hamnade i samma grupp, mot {pc(T1['medel_kontroll'])} procent för grannstenar ({T1['grupper']} grupper, bättre i {T1['bättre']}, sämre i {T1['sämre']}, {pf(T1['p'])}; sammanslaget {EX2['samma']} av {EX2['par']} par). T1 höll.
- **Bara händer utan namn (T2):** {pc(T2['medel_samma'])} mot {d1(100 * T2['medel_kontroll'])} procent i {T2['grupper']} grupper, varav {T2['bättre'] + T2['sämre']} med skillnad ({pf(T2['p'])}). T2 höll inte.
- **Olika händer:** av {S2['olika_händer_par_inom_30km']} stenpar inom 30 km som en forskare säger har olika händer lade modellen {S2['av_dem_i_samma_grupp']} i samma grupp.

### 5.5 Uppföljning: huggtekniken
- **Det förregistrerade provet höll inte** ({pf(H3['H3D']['p'])}). Sex grupper har minst två stenar bland Kitzler Åhfeldts öppna 3D-skanningar av runstenar i Södermanland, sammanlagt 18 stenar. Mätt i fyra huggspårsmått (spårets vinkel, djup, bredd och bottenradie) och jämfört med stenar av samma bergart var stenarna i samma grupp inte tydligt mer lika. Med 18 stenar har provet liten styrka.
- **Gruppen Sö 46, 131, 134, 137, 319 och 367** var inte lik i huggtekniken ({pf(H3G['G052']['p'])}) och är en av de mindre stabila. Kitzler Åhfeldts (2017) första huggteknikgrupp av tidiga stenar i Södermanland (Sö 131, 137, 166, 367, Fv1973;189) möter den delvis: Sö 166 ligger här i Traens grupp, och Sö 319 räknar hon till en annan grupp. Av hennes andra grupp ligger inget par i samma grupp.

### 5.6 Grupperna och litteraturen
- **Totalt** blev det {len(GRP)} grupper av minst tre stenar:
  - {TYP['okänd']} utan någon sten med känd ristare, varav {len(GOOD_UNK)} med gott underlag;
  - {TYP['med']} där alla stenar med känd ristare har samma ristare;
  - {TYP['blandad']} blandade.
- **Tidigare kopplingar:** av de {len(GOOD_UNK)} grupperna med okänd hand och gott underlag har {LVU['kopplad tidigare']} redan minst ett par som någon har kopplat ihop:
  - {LB['okänd_gott_kopplad_sri_runor']} i Sveriges runinskrifter eller Runor 2020;
  - {LB['okänd_gott_kopplad_litteratur']} bara i den övriga litteraturen, till exempel Ög 231 och 232 (Källström 2020).
- **Inga tidigare kopplingar:** i {LVU['ingen tidigare koppling']} grupper finns ingen koppling i de genomgångna källorna, och i en nämns stenarna inte alls. Ingen grupp motsägs av ett granskat uttalande.

## 6. Diskussion

Metoden återfinner runologernas stenpar, också för händer utan namn, långt oftare än platsen ensam gör, på bedömningar som hölls undan och mot ett andra material ur litteraturen. Precisionen är hög men täckningen låg: metoden pekar ut några par som hör ihop, inte en ristares hela verk.

Svagheter, i ordning efter vikt:
1. **Jämförelsematerialet är runologernas bedömningar, inte sanningen.** De bygger delvis på samma slags drag som modellen använder: stavning, stil, plats och, i Sveriges runinskrifter, samma beskrivningar av ornamentik och runformer som modellen läser. Provet visar att metoden återskapar deras bedömningar, inte att bedömningarna är rätt. Också träningen bygger på Rundatas attribueringar, som i Mellansverige till stor del följer Axelson (1993), som själv vägde in stavning och stil.
2. **Det andra provet är inte helt oberoende:** författarna står i samma tradition, 18 av de 25 grupperna i T1 innehåller stenar med känd ristare vars attribueringar ingick i träningen, och det renaste delprovet, händer utan namn, höll inte.
3. **Läsningen gjordes av en språkmodell.** Kontrolläsningen av Sveriges runinskrifter nådde aldrig kravet. Omläsningen följde en regel som infördes efter att oenigheterna setts, och de omstridda paren avgjordes av samma modell. I litteraturen delade läsare och kontroll bara {pc(KL['precision_mot_kontroll'])} procent av läsarnas uttalanden. Varje använt uttalande granskades av två granskare, men ett fel som båda gör slinker igenom, och kodfelet med Sterns uttalande (4.4) visar hur lätt ett uttalande kan förvrängas.
4. **Gruppgränserna är känsliga.** Stabiliteten bygger på bara två omträningar, och i median stannar två tredjedelar av en grupps par ihop. Det som är prövat är metoden, inte varje grupps exakta gräns.
5. **Fragment och kort text** grupperas på stil, kors och plats; grupper av fragment från samma fyndplats är märkta och säger lite om handen.
6. **Ingen ornamentik i detalj, inga runformer ur bild och ingen huggteknik** ingår i modellen.
7. **Runologernas egna bedömningar går isär.** U 1007 och U 1008 samt U 60 och U 124 är par som runologerna kallar samma hand, men som andra forskare säger har olika händer.

**Var metoden inte ska användas:** som tillskrivning, för fragment, för stenar mer än 30 km från varandra, och i landskap med få stenar och få kända ristare.

**Vad som skulle fälla metoden:** ett nytt material av runologiska bedömningar där grupperna inte gör bättre än grannstenar, eller grupper som en granskning av ornamentik och runformer på stenarna själva visar är blandade händer.

## 7. Slutsats

En modell som lär sig vad som skiljer samma hand från olika händer, och som väger samman stavning, språkdrag, stil, kors och plats, bildar grupper av runstenar som runologerna själva håller för samma hand långt oftare än grannstenar på samma avstånd. Det gäller i två låsta prov, och för händer utan namn i det första. Grupperna är få och snäva hypoteser att pröva med ornamentik, runformer och huggteknik på stenarna, inte nya ristare. En senare låst prövning, som öppnade provdelen en andra gång, visade att ornamentik kodad ur planscherna i Sveriges runinskrifter inte gjorde grupperna bättre, så de grupper som prövas här behålls.

## Data och kod

- Analysen är gjord på Rundata-korpusen med versionsnyckeln {FP}, i Vitki {APP_VERSION}. Kod och planer: https://github.com/Precatio/runes (CC BY 4.0).
- Planerna: `analysplaner/2026-11-23-nya-ristare-program.md`, `…-slutprov-1.md`, `…-slutprov-2-litteraturen.md`, `analysplaner/2026-11-24-nya-ristare-3d.md`.
- Skripten i `utdata/nya_ristare/`:
  - facit.py, belagg.py, parmodell.py, gruppering.py och slutprov.py (metoden och slutprov 1);
  - litteratur_stallen.py och slutprov2.py (slutprov 2);
  - litteratur_besked.py (besked per grupp);
  - huggteknik.py (huggtekniken);
  - rapport_extra.py (sammanslagna andelar, landskap, kalibrering, Holm, stabilitet).

  Resultatet står i `utdata/nya_ristare/resultat.md`. Grupperna i Vitki byggs av `src/hand_groups.py` med samma metod (METHODS.md 14l).
- Projektets tidigare försök med textlikheten: `utdata/nya_hander/`, `utdata/tata_karnor/`, `utdata/oppen_modell/`, `utdata/stenar_som_hor_ihop/`.
- Kodläget:
  - planen för arbetet i commit `6c6cab4`;
  - slutprov 1 i `69c148d` och `3698ddc`;
  - slutprov 2 i `d59c94f` och `f2c9083`;
  - huggtekniken i `91509e7` och `9a18ecf`;
  - den senare prövningen av ornamentiken (`analysplaner/2026-11-24-nya-ristare-ornamentik.md`, `utdata/nya_ristare/ornamentik/`, resultat.md avsnitt 10) i `f002f81`;
  - rättelserna efter granskningen av rapporten i den commit som lägger till denna text.
- 3D-skanningarna: skannade av Laila Kitzler Åhfeldt, Riksantikvarieämbetet, i projektet Runristandets dynamik (2009–2014), publicerade på Zenodo 2024, https://doi.org/10.5281/zenodo.11951255, CC BY 4.0. Huggspårsmåtten är beräknade i Vitki.
- Grupperna visas i Vitki under Ristarna och i stenprofilen i Stenöversikten (https://vitkirunor.se).
- Texterna ur Sveriges runinskrifter, Fornvännen, Futhark och avhandlingarna ligger inte i repot. Bara signum och källhänvisningar finns där.

## Referenser

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Jansson, S. B. F. 1958. Runstensfynd i kyrkmurar. *Fornvännen* 53, s. 241–257.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Scientific Archaeology B:9. Stockholm: Stockholms universitet.
- Kitzler Åhfeldt, L. 2017. *Runristare och mobilitet i Södermanland*. Stockholm: Riksantikvarieämbetet.
- Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland / Runestones in Södermanland* [Dataset]. Riksantikvarieämbetet. https://doi.org/10.5281/zenodo.11951255
- Kitzler Åhfeldt, L. 2020. Provenancing rune carvers on Bornholm through 3D-scanning and multivariate statistics of the carving technique. *European Journal of Archaeology* 23 (1), s. 82–104.
- Kvant, V. 2026. Statistiska ristarförslag ur runtexterna: 82 procent rätt bland de säkra förslagen i ett låst blindprov, mot 44 procent för närmaste ristare. Metodrapport, rapportversion 4. https://vitkirunor.se/forskningsrapporter/ristarforslag-blindprov
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholms universitet.
- Källström, M. 2020. Ett runristat gravmonument från Östra Stenby kyrka i Östergötland? *Fornvännen* 115 (2020:3), s. 181 ff.
- Lagman, S. 1990. *De stungna runorna. Användning och ljudvärde i runsvenska steninskrifter*. Runrön 4. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Lager, L. 2002. *Den synliga tron. Runstenskors som en spegling av kristnandet i Sverige*. Occasional Papers in Archaeology 31. Uppsala: Uppsala universitet.
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter*. Runrön 17. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Pereswetoff-Morath, S. 2017. *Vikingatida runbleck. Läsningar och tolkningar*. Uppsala: Uppsala universitet.
- Riksantikvarieämbetet. 2020. *Runor*. Databas över runinskrifter i Sverige. https://app.raa.se/open/runor
- Samnordisk runtextdatabas (Rundata) 3.1. Institutionen för nordiska språk, Uppsala universitet.
- Stern, M. 2013. *Runestone Images and Visual Communication in Viking Age Scandinavia*. Diss. University of Nottingham.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Thompson, C. W. 1975. *Studies in Upplandic Runography*. Austin: University of Texas Press.
- Williams, H. 1990. *Åsrunan. Användning och ljudvärde i runsvenska steninskrifter*. Runrön 3. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Zilmer, K. 2005. *”He drowned in Holmr's sea – his cargo-ship drifted to the sea-bottom, only three came out alive.” Records and representations of Baltic traffic in the Viking Age and the Early Middle Ages in early Nordic sources*. Dissertationes philologiae scandinavicae Universitatis Tartuensis 1. Tartu: Tartu universitet.
- Åkerström, H. 2020. *Visuella textkonventioner i den tidiga vikingatidens runristningar*. Runrön 23. Uppsala: Institutionen för nordiska språk, Uppsala universitet.

:::box Det viktigaste i korthet
- En modell som lär sig vad som skiljer samma hand från olika händer kan peka ut grupper av runstenar som hör ihop, också där ingen namngiven ristare passar.
- Den hittar runologernas egna stenpar långt oftare än grannstenar på samma avstånd, i två prov som var låsta i förväg.
- Grupperna är få och snäva: de flesta av en ristares stenar hamnar inte i samma grupp.
- I fyra av fem grupper utan känd ristare har ingen av de källor vi gått igenom kopplat ihop stenarna. De är hypoteser att pröva på stenarna själva, inte nya ristare.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Methods report, fully tested. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, rune carvers, attribution, same hand, gradient boosting, cluster analysis, preregistration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** Runologists have linked many unsigned runestones to each other: "the same carver as …". A statistical model that only chooses among named carvers cannot see a hand without a name. The aim was to test whether a model that learns what separates stones by the same hand from stones by different hands can form groups of stones that belong together, also where no named carver fits.
**Material.** 2,314 Swedish Viking Age runestones in the Scandinavian Runic-text Database (Rundata) with coordinates, and all 312,550 stone pairs within 30 km. As the comparison, the runologists' own statements about the same hand were used: in Sveriges runinskrifter and Runor 2020 (118 groups), and in Fornvännen, Futhark and eight theses (63 new pairs).
**Method.** A gradient boosting model was trained on pairs of stones with a known carver and gave each stone pair a value for the same hand. The stones were joined into groups by average linkage within 30 km. The runologists' groups were split at random into a development half and a test half. The method was fixed on the development half, and the test half was opened once in a locked final test. A second locked test was made against the literature.
**Results.** In the test half, on average {pc(A['medel_samma'])} percent of the runologists' stone pairs per group ended up in the same group, against {pc(A['medel_kontroll'])} percent for neighbouring stones at the same distance ({A['grupper']} groups, better in {A['bättre']} and worse in {A['sämre']}, {pf(A['p'], True)}; pooled {EXS['samma']} of {EXS['par']} pairs). For hands without a name it was {pc(O['medel_samma'])} against {d1(100 * O['medel_kontroll'], True)} percent ({O['grupper']} groups, {pf(O['p'], True)}). Against the literature it was {pc(T1['medel_samma'])} against {pc(T1['medel_kontroll'])} percent ({T1['grupper']} groups, {pf(T1['p'], True)}). About {pc(G8['precision_namngivna'])} percent of the pairs in the same group have the same carver, measured on stones with a known carver, but only {d1(100 * G8['täckning_namngivna'], True)} percent of all same-carver pairs within 30 km end up in the same group.
**What was not shown.** Against the literature the test did not hold for hands without a name ({T2['grupper']} groups, {pf(T2['p'], True)}), and the carving technique in 3D scans did not show that the stones in the same group are alike ({pf(H3['H3D']['p'], True)}, 18 stones).
**Conclusion.** The method recovers the runologists' stone pairs far more often than place alone does. It gives {len(GRP)} groups of at least three stones, and {len(GOOD_UNK)} of them have good evidence and no stone with a known carver. The groups are testable hypotheses, not new carvers.

## 1. Introduction

The carvers behind most runestones are unknown. Axelson (1993) listed the signed and attributed inscriptions in central Sweden, Stille (1999) attributed the stones of Fjädrundaland and Källström (2007) studied the carvers' writing environments in Scandinavia. The runologists have also linked unsigned stones to each other without naming the carver, in Sveriges runinskrifter and in Runor (Swedish National Heritage Board 2020). Claiborne Thompson (1975) showed how spelling separates carvers, and Laila Kitzler Åhfeldt (2002, 2020) has separated carvers by the shape of the grooves in laser scans.

A model choosing among the named carvers cannot see a hand without a name. Tested against the runologists' groups "same as made X" in Runor 2020, such a model gave the same carver about as often as for neighbouring stones at the same distance (Kvant 2026). A measure of text likeness beyond the neighbours recognised the runologists' pairs, but groups built from it became districts, not hands (unpublished attempts, see Data and code). Part of the explanation was an error found in this work: the categorical language traits, for example the type of word divider, had never entered the measure.

In the project's review of Fornvännen, Futhark and the theses in autumn 2026 we found no method that forms groups of runestones by the same hand across the whole material and that has been tested against the runologists' judgements with part of them held back. The aim here is to report such a method and two locked tests of it.

## 2. Preregistration

The work followed four plans, locked in the project's version control before what they concerned was computed:
- **The plan for the work** (2026-11-23, SHA-256 `{SHA['program'][:16]}…`): how the comparison material is built and split into a development half and a test half (groups as units), and that the test half is used only in locked final tests.
- **Final test 1** (2026-11-23, `{SHA['s1'][:16]}…`), locked before the test half was opened. It fixed the method, the threshold τ = 0.8, the measure and the decision rule, verbatim: "S1 (main test, all groups): one-sided Wilcoxon test over the groups. Holds if p < 0.05 and the mean share in the same group is larger than the control's." S2 applied in the same way to groups with hands without a name only.
- **Final test 2** (2026-11-23, `{SHA['s2'][:16]}…`): the same method and measure against new pairs from the literature (T1 all groups; T2 hands without a name, determinate with at least 5 groups with a difference). Before the lock a count on the unreviewed reading had been seen: 72 of 228 groups had at least one pair or a shared carver in the literature. That partly reveals the test's numerator, but the test measure had not been seen.
- **The carving technique** (2026-11-24, `{SHA['3d'][:16]}…`): whether stones in the same group are more alike in four groove measures than stones of the same rock type.

Final tests 1 and 2 are the confirmatory tests; the carving technique is a follow-up. The comparisons between model variants (5.3) are development work and not tests.

## 3. Material

- **The stones.** Scandinavian Runic-text Database (Rundata) 3.1, frozen for the analysis. 2,314 Swedish Viking Age runestones with coordinates, except Bohuslän. Distances were computed in SWEREF 99 TM.
- **The pairs.** All 312,550 stone pairs within 30 km.
- **The evidence per pair** (share of pairs where it exists): text likeness in spelling, word dividers, language traits and formulas beyond neighbours at the same distance (46 %); the categorical language traits, alike or not, such as the type of word divider (54 %) and *eftir* or *at* (45 %); style group (22 %); the shape of the cross after Lager's (2002) typology in Runor 2020 (23 %); words about the ornament (9 %) and rune forms (12 %) in Sveriges runinskrifter; shared names, rock type, short-twig runes and the distance.
- **The training pairs.** 41,192 pairs of stones with a certain carver in Rundata, of which 5,400 with the same carver.
- **The runologists' groups.**
  - *The sources:* the 225 places in the text volumes of Sveriges runinskrifter where the editor says "the same carver", "the same hand" or "the same master", and Runor 2020's "same as made X". Only links the editor stands behind, certain or probable, were included; possible links were not counted.
  - *The check reading:* the places were read by Anthropic's language model Claude (Claude Opus) in two instances, one for each half. A third reader checked 40 places chosen at random and agreed in {K1['lika']} ({pc(K1['lika'] / K1['stickprov'])} percent), below the requirement of 85 percent fixed in advance.
  - *The re-reading:* all places were read again, as the plan prescribed, with a stricter rule (only signa written in the text). The readings agreed in 194 of 225 places (86 percent), which is not a new check. The 62 disputed pairs were decided by the same language model against the text, with a written reason for 31.
  - *The result:* 409 links in 118 groups, of which 84 are pairs. They were split at random (seed 20261123) into 59 groups for development and 59 for testing.
- **The literature** (for final test 2).
  - *The material:* 2,490 places where a carver or "the same hand" is mentioned near a signum, in Fornvännen, Futhark and eight theses: {THESES_EN}.
  - *The reading:* 28 instances of the same language model. A blind check of 250 places gave {KL['lika_ställen']} identical ({pc(KL['lika_ställen'] / KL['ställen'])} percent, many without a statement), but at statement level only {KL['gemensamma']} shared: {pc(KL['precision_mot_kontroll'])} percent of the readers' and {pc(KL['täckning_mot_kontroll'])} percent of the check's.
  - *The review:* every statement about the same hand, different hands or an attribution was therefore tried by two independent reviewers who were to try to refute it. It was kept only if both confirmed it: {GR['samma_hand|bekräftad']} of {GR['samma_hand|bekräftad'] + GR['samma_hand|ej']} about the same hand and {GR['olika_hander|bekräftad']} of {GR['olika_hander|bekräftad'] + GR['olika_hander|ej']} about different hands.
  - *The result:* {S2['facit2_par']} pairs not already among the runologists' groups, in {S2['facit2_grupper']} groups.

## 4. Method

### 4.1 The model of the same hand
- **The classifier:** gradient boosting (many small decision trees added one at a time, each correcting the earlier ones' errors) on the evidence and the distance; missing evidence is left empty.
- **The training:** pairs of stones with a certain carver, with the carvers split at random into five parts. A pair of such stones gets its value from a model that has not seen any stones by their carver in any of the parts; for pairs with different carvers this holds for at least one of them. Other pairs get the mean over the five models.
- **The exclusion:** pairs within the runologists' groups and pairs touching the test half's stones never entered the training.
- **The value:** the model gives a value between 0 and 1 that ranks the pairs. It is not a calibrated probability (5.3).

### 4.2 The groups
- **The joining:** average linkage. The two groups with the highest mean value over all pairs between them are joined first, but only if all their stones lie within 30 km of each other. The mean instead of the strongest link keeps the groups from chaining into districts.
- **The threshold:** the joining stops when no mean value between two groups reaches τ = 0.8. The threshold was chosen on the development half as the highest precision on pairs of stones with a known carver ({pc(G8['precision_namngivna'])} percent) that also gave a clear coverage of the development half's pairs ({pc(G8['facit_samma_grupp'])} against {d1(100 * G8['grannar_samma_grupp'], True)} percent for neighbours).

### 4.3 The test
- **The measure:** per group of the runologists, the share of pairs within 30 km in the same group, against the share of stones at the same distance (± 25 percent, at least ± 1 km) from each of the pair's stones, outside the runologists' group, that lie in the same group as that stone.
- **The test:** one-sided Wilcoxon test (a rank test without assuming a normal distribution) over the groups, so that a large group does not weigh more than a small one.
- **The loss:** of the test half's {EX['provdelens_grupper']} groups, {EX['provdelens_grupper_med_par']} have at least one pair within 30 km among the stones with coordinates. The rest cannot be tested.

### 4.4 Deviations from the plans
- **The re-reading** of Sveriges runinskrifter used a stricter rule than the first reading, a rule introduced after the disagreements had been seen. The disputed pairs were decided by the same language model, not by a person.
- **The control** takes stones at the same distance from each of the two stones of a pair. The plan's text says "from a".
- **The threshold τ** was chosen with the precision on all pairs of stones with a known carver, including the test half's stones with a known carver in Rundata. The test half's same-hand statements and the test half's groups with hands without a name were not included.
- **A code error in the descriptive count of different hands** (not in the tests): a statement that one stone has a different hand from several others was split into all pairs, so that Stern (2013) was made to say that U 43 and U 79 have different hands, although she attributes both to Arnfastr. Corrected; now only statements about two stones and lists of name bearers are used (four statements are ambiguous).
- **Rune height and stone height** were tried on the development half, gave no lift and were not included.
- **The label "weak evidence"** (23 groups, mostly fragments from the same find place held together by the place) was added after the groups had been seen. It is not part of the tests.
- **Otherwise** no deviations.

## 5. Results

### 5.1 Final test 1
- **All groups:** in the test half, on average {pc(A['medel_samma'])} percent of the runologists' stone pairs per group ended up in the same group, against {pc(A['medel_kontroll'])} percent for neighbouring stones at the same distance. This covered {A['grupper']} groups, better in {A['bättre']} and worse in {A['sämre']}, {pf(A['p'], True)}. Pooled over the pairs it was {EXS['samma']} of {EXS['par']} ({pc(EXS['andel'])} percent).
- **Groups with hands without a name**, where no stone has a known carver: {pc(O['medel_samma'])} against {d1(100 * O['medel_kontroll'], True)} percent ({O['grupper']} groups, better in {O['bättre']}, worse in {O['sämre']}, {pf(O['p'], True)}).
- **Both tests held.** On the development half the same measure had given {pc(U1['alla']['medel_samma'])} against {pc(U1['alla']['medel_kontroll'])} percent.
- **Holm correction** (an adjustment for making several tests) over the report's five preregistered tests does not change the outcomes.

{chart(False)}

In plain words: when the runologists say two stones were made by the same hand, they end up in the same group about two times in five, while a stone at the same distance ends up there about one time in fifteen. For hands without a name in the test half it is about two times in three.

### 5.2 By province
Uppland: {PU['grupper']} groups, {pc(PU['samma'])} percent against {d1(100 * PU['kontroll'], True)}. Södermanland: {PS['grupper']} groups, {pc(PS['samma'])} percent against {d1(100 * PS['kontroll'], True)}. Östergötland, Västmanland and Öland have one or two groups each. By carver it cannot be reported, since most groups have no name.

### 5.3 The values, the precision and the development work
- **The calibration:** the value is not a probability. Among pairs of stones with a known carver, {pc(CB[(0, 0.2)]['andel_samma'])} percent had the same carver below 0.2, {pc(CB[(0.4, 0.6)]['andel_samma'])} percent at 0.4–0.6, {pc(CB[(0.8, 0.9)]['andel_samma'])} at 0.8–0.9 and {pc(CB[(0.9, 1.0)]['andel_samma'])} above 0.9 (base rate {pc(EX['grundnivå_samma_ristare'])} percent). The order holds, the levels do not.
- **The precision in the groups** on pairs of stones with a known carver was {pc(GU[0.9]['precision_namngivna'])} percent at τ = 0.9, {pc(G8['precision_namngivna'])} percent at 0.8 and {pc(GU[0.7]['precision_namngivna'])} percent at 0.7. The coverage is low: at 0.8, {d1(100 * G8['täckning_namngivna'], True)} percent of all same-carver pairs within 30 km end up in the same group. The groups are thus few and narrow.
- **The model variants on the development half:** the runologists' partner ranked in median above {pc(M1['median_percentil'])} percent of the stones at the same distance with all evidence, against {pc(M0['median_percentil'])} percent with spelling and language traits only. The categorical language traits accounted for much of the lift. Shared names added nothing.
- **The stability:** in two retrainings with other random splits, in median {pc(EX['stabilitet']['median'])} percent of a group's pairs stayed together. {EX['stabilitet']['lika_med_1']} of {EX['stabilitet']['grupper']} groups stayed wholly together in both.

### 5.4 Final test 2: the literature
- **The new pairs from the literature:** on average {pc(T1['medel_samma'])} percent ended up in the same group, against {pc(T1['medel_kontroll'])} percent for neighbouring stones ({T1['grupper']} groups, better in {T1['bättre']}, worse in {T1['sämre']}, {pf(T1['p'], True)}; pooled {EX2['samma']} of {EX2['par']} pairs). T1 held.
- **Hands without a name only (T2):** {pc(T2['medel_samma'])} against {d1(100 * T2['medel_kontroll'], True)} percent in {T2['grupper']} groups, of which {T2['bättre'] + T2['sämre']} with a difference ({pf(T2['p'], True)}). T2 did not hold.
- **Different hands:** of {S2['olika_händer_par_inom_30km']} stone pairs within 30 km that a researcher says have different hands, the model put {S2['av_dem_i_samma_grupp']} in the same group.

### 5.5 Follow-up: the carving technique
- **The preregistered test did not hold** ({pf(H3['H3D']['p'], True)}). Six groups have at least two stones among Kitzler Åhfeldt's open 3D scans of runestones in Södermanland, 18 stones in all. Measured in four groove measures (the groove's angle, depth, width and bottom radius) and compared with stones of the same rock type, the stones in the same group were not clearly more alike. With 18 stones the test has little power.
- **The group Sö 46, 131, 134, 137, 319 and 367** was not alike in carving technique ({pf(H3G['G052']['p'], True)}) and is one of the less stable. Kitzler Åhfeldt's (2017) first carving-technique group of early stones in Södermanland (Sö 131, 137, 166, 367, Fv1973;189) partly meets it: Sö 166 lies here in Traen's group, and she counts Sö 319 to another group. Of her second group, no pair lies in the same group.

### 5.6 The groups and the literature
- **In all** there were {len(GRP)} groups of at least three stones:
  - {TYP['okänd']} without any stone with a known carver, of which {len(GOOD_UNK)} with good evidence;
  - {TYP['med']} where all stones with a known carver have the same carver;
  - {TYP['blandad']} mixed.
- **Earlier links:** of the {len(GOOD_UNK)} unknown-hand groups with good evidence, {LVU['kopplad tidigare']} already have at least one pair that someone has linked:
  - {LB['okänd_gott_kopplad_sri_runor']} in Sveriges runinskrifter or Runor 2020;
  - {LB['okänd_gott_kopplad_litteratur']} only in the other literature, for example Ög 231 and 232 (Källström 2020).
- **No earlier links:** in {LVU['ingen tidigare koppling']} groups no link exists in the searched sources, and in one the stones are not mentioned at all. No group is contradicted by a reviewed statement.

## 6. Discussion

The method recovers the runologists' stone pairs, also for hands without a name, far more often than place alone does, on judgements held back and against a second material from the literature. The precision is high but the coverage low: the method points out some pairs that belong together, not a carver's whole work.

Weaknesses, in order of importance:
1. **The comparison material is the runologists' judgements, not the truth.** They rest partly on the same kind of features the model uses: spelling, style, place and, in Sveriges runinskrifter, the same descriptions of ornament and rune forms that the model reads. The test shows that the method reproduces their judgements, not that the judgements are right. The training also rests on Rundata's attributions, which in central Sweden largely follow Axelson (1993), who himself weighed spelling and style.
2. **The second test is not wholly independent:** the authors belong to the same tradition, 18 of the 25 groups in T1 contain stones with a known carver whose attributions entered the training, and the cleanest part, hands without a name, did not hold.
3. **The reading was done by a language model.** The check reading of Sveriges runinskrifter never reached the requirement. The re-reading followed a rule introduced after the disagreements had been seen, and the disputed pairs were decided by the same model. In the literature the readers and the check shared only {pc(KL['precision_mot_kontroll'])} percent of the readers' statements. Every statement used was reviewed by two reviewers, but an error both make slips through, and the code error with Stern's statement (4.4) shows how easily a statement can be distorted.
4. **The group boundaries are sensitive.** The stability rests on only two retrainings, and in median two thirds of a group's pairs stay together. What has been tested is the method, not each group's exact boundary.
5. **Fragments and short texts** are grouped on style, cross and place; groups of fragments from one find place are labelled and say little about the hand.
6. **No detailed ornament, no rune forms from images and no carving technique** are part of the model.
7. **The runologists' own judgements disagree.** U 1007 and U 1008, and U 60 and U 124, are pairs the runologists call the same hand, but which other researchers say have different hands.

**Where the method should not be used:** as an attribution, for fragments, for stones more than 30 km apart, and in provinces with few stones and few known carvers.

**What would refute the method:** a new material of runological judgements where the groups do no better than neighbouring stones, or groups that an examination of the ornament and rune forms on the stones themselves shows to be mixed hands.

## 7. Conclusion

A model that learns what separates the same hand from different hands, and that weighs together spelling, language traits, style, cross and place, forms groups of runestones that the runologists themselves hold to be the same hand far more often than neighbouring stones at the same distance. This holds in two locked tests, and for hands without a name in the first. The groups are few and narrow hypotheses to be tested with ornament, rune forms and carving technique on the stones, not new carvers. A later locked test, which opened the test half a second time, showed that ornament coded from the plates of Sveriges runinskrifter did not make the groups better, so the groups tested here are kept.

## Data and code

- The analysis was made on the Rundata corpus with the version key {FP}, in Vitki {APP_VERSION}. Code and plans: https://github.com/Precatio/runes (CC BY 4.0).
- The plans: `analysplaner/2026-11-23-nya-ristare-program.md`, `…-slutprov-1.md`, `…-slutprov-2-litteraturen.md`, `analysplaner/2026-11-24-nya-ristare-3d.md`.
- The scripts in `utdata/nya_ristare/`:
  - facit.py, belagg.py, parmodell.py, gruppering.py and slutprov.py (the method and final test 1);
  - litteratur_stallen.py and slutprov2.py (final test 2);
  - litteratur_besked.py (the verdict per group);
  - huggteknik.py (the carving technique);
  - rapport_extra.py (pooled shares, provinces, calibration, Holm, stability).

  The result is in `utdata/nya_ristare/resultat.md`. The groups in Vitki are built by `src/hand_groups.py` with the same method (METHODS.md 14l).
- The project's earlier attempts with the text likeness: `utdata/nya_hander/`, `utdata/tata_karnor/`, `utdata/oppen_modell/`, `utdata/stenar_som_hor_ihop/`.
- The code state:
  - the plan for the work in commit `6c6cab4`;
  - final test 1 in `69c148d` and `3698ddc`;
  - final test 2 in `d59c94f` and `f2c9083`;
  - the carving technique in `91509e7` and `9a18ecf`;
  - the later test of the ornament (`analysplaner/2026-11-24-nya-ristare-ornamentik.md`, `utdata/nya_ristare/ornamentik/`, resultat.md section 10) in `f002f81`;
  - the corrections after the review of the report in the commit that adds this text.
- The 3D scans: scanned by Laila Kitzler Åhfeldt, Swedish National Heritage Board, in the project Runristandets dynamik (2009–2014), published on Zenodo 2024, https://doi.org/10.5281/zenodo.11951255, CC BY 4.0. The groove measures were computed in Vitki.
- The groups are shown in Vitki under The carvers and in the stone profile in the Stone overview (https://vitkirunor.se).
- The texts from Sveriges runinskrifter, Fornvännen, Futhark and the theses are not in the repository. Only signa and source references are there.

## References

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter* [Central Swedish rune carvers]. Runrön 5. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Jansson, S. B. F. 1958. Runstensfynd i kyrkmurar [Runestone finds in church walls]. *Fornvännen* 53, pp. 241–257.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Scientific Archaeology B:9. Stockholm: Stockholm University.
- Kitzler Åhfeldt, L. 2017. *Runristare och mobilitet i Södermanland* [Rune carvers and mobility in Södermanland]. Stockholm: Swedish National Heritage Board.
- Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland / Runestones in Södermanland* [Dataset]. Swedish National Heritage Board. https://doi.org/10.5281/zenodo.11951255
- Kitzler Åhfeldt, L. 2020. Provenancing rune carvers on Bornholm through 3D-scanning and multivariate statistics of the carving technique. *European Journal of Archaeology* 23 (1), pp. 82–104.
- Kvant, V. 2026. Statistical carver suggestions from the runic texts: 82 percent right among the confident suggestions in a locked blind test, against 44 percent for the nearest carver. Methods report, report version 4. https://vitkirunor.se/en/forskningsrapporter/ristarforslag-blindprov
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden* [Masters and memorials]. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholm University.
- Källström, M. 2020. Ett runristat gravmonument från Östra Stenby kyrka i Östergötland? [A rune-inscribed grave monument from Östra Stenby church in Östergötland?]. *Fornvännen* 115 (2020:3), pp. 181 ff.
- Lagman, S. 1990. *De stungna runorna. Användning och ljudvärde i runsvenska steninskrifter* [The dotted runes]. Runrön 4. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Lager, L. 2002. *Den synliga tron. Runstenskors som en spegling av kristnandet i Sverige* [The visible faith]. Occasional Papers in Archaeology 31. Uppsala: Uppsala University.
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter* [The yr rune]. Runrön 17. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Pereswetoff-Morath, S. 2017. *Vikingatida runbleck. Läsningar och tolkningar* [Viking Age runic plates]. Uppsala: Uppsala University.
- Scandinavian Runic-text Database (Rundata) 3.1. Department of Scandinavian Languages, Uppsala University.
- Stern, M. 2013. *Runestone Images and Visual Communication in Viking Age Scandinavia*. PhD thesis, University of Nottingham.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering* [Runestones and rune carvers in Viking Age Fjädrundaland]. Runrön 13. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Swedish National Heritage Board (Riksantikvarieämbetet). 2020. *Runor*. Database of runic inscriptions in Sweden. https://app.raa.se/open/runor
- Thompson, C. W. 1975. *Studies in Upplandic Runography*. Austin: University of Texas Press.
- Williams, H. 1990. *Åsrunan. Användning och ljudvärde i runsvenska steninskrifter* [The ás rune]. Runrön 3. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Zilmer, K. 2005. *"He drowned in Holmr's sea – his cargo-ship drifted to the sea-bottom, only three came out alive." Records and representations of Baltic traffic in the Viking Age and the Early Middle Ages in early Nordic sources*. Dissertationes philologiae scandinavicae Universitatis Tartuensis 1. Tartu: University of Tartu.
- Åkerström, H. 2020. *Visuella textkonventioner i den tidiga vikingatidens runristningar* [Visual text conventions in early Viking Age runic inscriptions]. Runrön 23. Uppsala: Department of Scandinavian Languages, Uppsala University.

:::box The essentials
- A model that learns what separates the same hand from different hands can point out groups of runestones that belong together, also where no named carver fits.
- It finds the runologists' own stone pairs far more often than neighbouring stones at the same distance, in two tests locked in advance.
- The groups are few and narrow: most of a carver's stones do not end up in the same group.
- In four of five groups without a known carver, none of the sources we have searched has linked the stones. They are hypotheses to be tested on the stones themselves, not new carvers.
:::
"""

# ---- kontroller (mallen) -----------------------------------------------------------------------------------------------
assert "I klartext" in body and "In plain words" in body_en
assert round(LVU["ingen tidigare koppling"] / len(GOOD_UNK), 2) == 0.79  # "fyra av fem"
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS|\bAI\b"
for b in (body, body_en):
    assert not re.search(r"^\s*\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
    assert FP not in head
    assert "](/" not in b
    assert "3.0.0" not in b and "U 43 och U 79 har olika händer\n" not in b
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Metodrapport, fullt prövad. Rapportversion 1, 2026-11-25. Tidslinje: ")
assert body_en.split("\n", 1)[0].startswith("*Viktor Kvant, independent researcher. Methods report, fully tested. Report version 1, 2026-11-25. Timeline: ")
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
SEC = lambda b: [re.match(r"[\d.]*", h).group(0) for h in re.findall(r"^##+ (.+)$", b, re.M)]  # noqa: E731
assert SEC(body) == SEC(body_en), (SEC(body), SEC(body_en))
assert len(re.findall(r"^\s*- ", body, re.M)) == len(re.findall(r"^\s*- ", body_en, re.M))
assert len(re.findall(r"^\s*\d+\. ", body, re.M)) == len(re.findall(r"^\s*\d+\. ", body_en, re.M))
# mallens längd gäller löptexten: utan huvudraden och diagrammet, fram till Data och kod
prose = re.sub(r":::chart.*?\n:::", "", body.split("## Data")[0].split("\n", 1)[1], flags=re.S)
words = len(prose.split())
assert 1500 <= words <= 3000, words

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Ristare", "Sannolikhetsmodellen"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_nya_ristare.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", words, "före Data och kod;", len(body_en.split()), "words")

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
                 "topic": "Rapport|samma hand", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
