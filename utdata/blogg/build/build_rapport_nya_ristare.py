"""Forskningsrapport, metodrapport (låst mall utdata/rapporter/MALL.md, version 4; Metodrapport, fullt prövad):
"Grupper av runstenar med samma hand, också utan namn" (sv + en). Planerna analysplaner/2026-11-23-nya-ristare-program.md
(f5ce4fe7), …-slutprov-1.md (081bf667), …-slutprov-2-litteraturen.md (706be174) och 2026-11-24-nya-ristare-3d.md
(ffb9b051); resultaten i utdata/nya_ristare/. Alla siffror asserteras mot filerna.
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
APP_VERSION = "3.0.0"
REPORT_VERSION = 1
TODAY = "2026-11-24"
D = os.path.join(ROOT, "utdata", "nya_ristare")
J = lambda f: json.load(open(os.path.join(D, f), encoding="utf-8"))  # noqa: E731
PLANS = {"program": ("2026-11-23-nya-ristare-program.md", "f5ce4fe7"), "s1": ("2026-11-23-nya-ristare-slutprov-1.md", "081bf667"),
         "s2": ("2026-11-23-nya-ristare-slutprov-2-litteraturen.md", "706be174"), "3d": ("2026-11-24-nya-ristare-3d.md", "ffb9b051")}
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
assert (S2["olika_händer_par_inom_30km"], S2["av_dem_i_samma_grupp"]) == (14, 1)
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
LV = Counter(x["besked"] for x in LIT.values())
assert (LV["stöds i litteraturen"], LV["ny"], LV["motsagd"], LV["ej omnämnd"]) == (57, 155, 1, 15)
LVU = Counter(LIT[g["id"]]["besked"] for g in GOOD_UNK)
assert (LVU["ny"], LVU["stöds i litteraturen"], LVU["ej omnämnd"]) == (69, 7, 1)
assert LIT["G131"]["samma_hand"][0][:2] == ["Ög 231", "Ög 232"] and "Källström 2020 (Fornvännen)" in LIT["G131"]["samma_hand"][0][2]
assert LIT["G074"]["besked"] == "motsagd" and LIT["G074"]["olika_hander"][0][:2] == ["U 43", "U 79"]
G052 = next(g for g in GRP if g["id"] == "G052")
assert G052["stenar"] == ["Sö 131", "Sö 134", "Sö 137", "Sö 319", "Sö 367", "Sö 46"]
DEL = json.load(open(os.path.join(D, "delning.json"), encoding="utf-8"))
assert len(DEL["grupper"]) == 118 and Counter(g["del"] for g in DEL["grupper"]) == {"U": 59, "P": 59}
LOG = open(os.path.join(D, "provdelen_logg.md"), encoding="utf-8").read()
assert len([l for l in LOG.splitlines() if l.startswith("- ")]) == 1  # provdelen öppnad en gång
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
title = ("Runstenar med samma hand, också utan namn: 42 procent av runologernas stenpar i samma grupp mot 7 procent för "
         "grannstenar, i ett låst slutprov")
title_en = ("Runestones by the same hand, also without a name: 42 percent of the runologists' stone pairs in the same group "
            "against 7 percent for neighbouring stones, in a locked final test")
summary = ("Metodrapport. En inlärd modell för samma hand bildar grupper av runstenar som kan vara gjorda av samma ristare, "
           "också där ingen namngiven ristare passar. I ett låst slutprov mot runologernas egna uttalanden, som hölls undan "
           "tills metoden var bestämd, hamnade 42 procent av deras stenpar i samma grupp mot 7 procent för grannstenar på "
           "samma avstånd. Ett andra prov mot uttalanden i Fornvännen, Futhark och åtta avhandlingar gav 46 mot 7 procent.")
summary_en = ("Methods report. A learned model of the same hand forms groups of runestones that may have been made by the same "
              "carver, also where no named carver fits. In a locked final test against the runologists' own statements, held "
              "back until the method was fixed, 42 percent of their stone pairs ended up in the same group against 7 percent "
              "for neighbouring stones at the same distance. A second test against statements in Fornvännen, Futhark and "
              "eight theses gave 46 against 7 percent.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report (methods report), report version {REPORT_VERSION}; analysis in "
           f"Vitki {APP_VERSION}. https://vitkirunor.se/en/forskningsrapporter/{SLUG}")
TL_SV = ("planen för arbetet och delningen av runologernas grupper låstes 2026-11-23; modellen byggdes på utvecklingsdelen "
         "2026-11-23; slutprov 1 låstes och kördes 2026-11-23; planen för slutprov 2 låstes 2026-11-23; slutprov 2 och "
         "provet av huggtekniken kördes 2026-11-24")
TL_EN = ("the plan for the work and the split of the runologists' groups were locked 2026-11-23; the model was built on the "
         "development half 2026-11-23; final test 1 was locked and run 2026-11-23; the plan for final test 2 was locked "
         "2026-11-23; final test 2 and the test of the carving technique were run 2026-11-24")


def chart(sv):
    of = "av" if sv else "of"
    rows = [":::chart Runologernas stenpar i samma grupp, procent" if sv else ":::chart The runologists' stone pairs in the same group, percent"]
    for lab_sv, lab_en, r in (("Slutprov 1, alla grupper", "Final test 1, all groups", A),
                              ("Slutprov 1, händer utan namn", "Final test 1, hands without a name", O),
                              ("Slutprov 2, litteraturen", "Final test 2, the literature", T1)):
        rows += [f"# {lab_sv if sv else lab_en} ({r['grupper']} {'grupper' if sv else 'groups'})",
                 f"+{'Samma grupp' if sv else 'Same group'} | {d1(100 * r['medel_samma'], not sv)} | {r['bättre']} {'grupper bättre' if sv else 'groups better'}",
                 f"{'Grannstenar på samma avstånd' if sv else 'Neighbouring stones at the same distance'} | {d1(100 * r['medel_kontroll'], not sv)} | –"]
    rows += ["Källa: Rundata, Runor 2020, Sveriges runinskrifter och litteraturen; medel över grupperna. Diagram: Vitki."
             if sv else "Source: Rundata, Runor 2020, Sveriges runinskrifter and the literature; mean over the groups. Chart: Vitki.", ":::"]
    return "\n".join(rows)


body = f"""*Viktor Kvant, oberoende forskare. Metodrapport, fullt prövad. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, runristare, attribuering, samma hand, gradient boosting, klusteranalys, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Runologer har kopplat ihop många osignerade runstenar med varandra: ”samme ristare som …”. En statistisk modell som bara väljer bland namngivna ristare kan inte se en hand utan namn. Syftet var att pröva om en modell som lär sig vad som skiljer stenar av samma hand från stenar av olika händer kan bilda grupper av stenar som hör ihop, också där ingen namngiven ristare passar.
**Material.** 2 314 svenska vikingatida runstenar i Samnordisk runtextdatabas (Rundata) med koordinater, och alla 312 550 stenpar inom 30 km. Som jämförelse användes runologernas egna uttalanden om samma hand: i Sveriges runinskrifter och Runor 2020 (118 grupper), och i Fornvännen, Futhark och åtta avhandlingar (63 nya par).
**Metod.** En gradient boosting-modell tränades på par av stenar med känd ristare och gav varje stenpar en sannolikhet för samma hand. Stenarna slogs ihop till grupper med genomsnittlig länkning inom 30 km. Runologernas grupper delades slumpvis i en utvecklingsdel och en provdel. Metoden bestämdes helt på utvecklingsdelen, och provdelen öppnades en gång i ett låst slutprov. Ett andra låst prov gjordes mot litteraturen.
**Resultat.** I provdelen hamnade {pc(A['medel_samma'])} procent av runologernas stenpar i samma grupp, mot {pc(A['medel_kontroll'])} procent för grannstenar på samma avstånd ({A['grupper']} grupper, bättre i {A['bättre']} och sämre i {A['sämre']}, {pf(A['p'])}). För händer utan namn var det {pc(O['medel_samma'])} mot {d1(100 * O['medel_kontroll'])} procent ({O['grupper']} grupper, {pf(O['p'])}). Mot litteraturen var det {pc(T1['medel_samma'])} mot {pc(T1['medel_kontroll'])} procent ({T1['grupper']} grupper, {pf(T1['p'])}). Omkring {pc(G8['precision_namngivna'])} procent av paren i samma grupp har samma ristare, mätt på stenar med känd ristare. Huggtekniken i 3D-skanningar varken stödde eller fällde grupperna.
**Slutsats.** Metoden återskapar runologernas bedömningar av samma hand långt oftare än platsen ensam gör. Den ger {len(GRP)} grupper av minst tre stenar, och {len(GOOD_UNK)} av dem har gott underlag och ingen sten med känd ristare. Grupperna är prövbara hypoteser, inte nya ristare.

## 1. Inledning

Ristarna bakom de flesta runstenar är okända. Jan Axelson (1993) förtecknade de signerade och attribuerade inskrifterna i Mellansverige, Per Stille (1999) attribuerade stenarna i Fjädrundaland, och Magnus Källström (2007) har studerat ristarna och deras skriftmiljöer i hela Norden. Runologerna har också kopplat ihop osignerade stenar med varandra utan att ge ristaren ett namn, i Sveriges runinskrifter och i Runor (Riksantikvarieämbetet 2020). Claiborne Thompson (1975) visade hur stavningen skiljer ristare åt, och Laila Kitzler Åhfeldt (2002, 2020) har skilt ristare åt med huggspårens form i laserskanningar.

En statistisk modell som väljer bland de namngivna ristarna kan inte se en hand utan namn. När en sådan modell prövades mot runologernas grupper ”samma som gjort X” i Runor 2020 gav den samma ristare inom grupperna ungefär lika ofta som för grannstenar på samma avstånd (Kvant 2026a). Ett mått på hur lika två inskrifter är i stavning och språkdrag, utöver vad grannar på samma avstånd är, kände däremot igen runologernas par. Men grupper som byggdes av det måttet blev bygder, inte händer.

Vi har inte funnit någon metod som bildar grupper av runstenar med samma hand över hela materialet och som har prövats mot runologernas bedömningar med en del av dem undanhållen. Syftet här är att redovisa en sådan metod och två låsta prov av den.

## 2. Förregistrering

Arbetet följde fyra planer som låstes i projektets versionshantering innan det de gällde räknades:
- **Planen för arbetet** (2026-11-23, SHA-256 `{SHA['program'][:16]}…`). Den bestämde hur jämförelsematerialet byggs, att det delas i en utvecklingsdel och en provdel med grupperna som enheter, och att provdelen bara används i låsta slutprov, högst tre gånger innan ett nytt material byggs.
- **Slutprov 1** (2026-11-23, `{SHA['s1'][:16]}…`), låst innan provdelen öppnades. Den bestämde metoden, gränsen τ = 0,8, måttet och utfallet: provet håller om ett ensidigt Wilcoxon-test över grupperna ger p under 0,05 och andelen i samma grupp är större än kontrollens.
- **Slutprov 2** (2026-11-23, `{SHA['s2'][:16]}…`): samma metod och samma mått mot nya par ur litteraturen, låst innan paren jämfördes med grupperna. Före låsningen hade en beskrivande räkning setts: hur många grupper som hade minst ett par i den ogranskade läsningen. Provmåttet hade inte setts.
- **Huggtekniken** (2026-11-24, `{SHA['3d'][:16]}…`): om stenar i samma grupp liknar varandra i fyra huggspårsmått mer än stenar av samma bergart.

Slutprov 1 och 2 är de konfirmatoriska proven, huggtekniken är en uppföljning. Jämförelserna mellan modellvarianter (5.3) är utvecklingsarbete på utvecklingsdelen och inte prov.

## 3. Material

- **Stenarna.** Samnordisk runtextdatabas (Rundata) 3.1, fryst för analysen. 2 314 svenska vikingatida runstenar med koordinater, utom Bohuslän. Avstånden räknades i SWEREF 99 TM.
- **Paren.** Alla 312 550 stenpar inom 30 km.
- **Beläggen per par**, med andelen av paren där belägget finns:
  - stavning, skiljetecken, bindrunor, språkdrag, formler och innehåll, som likhet utöver grannar på samma avstånd (46 %);
  - de kategoriska språkdragen, lika eller olika: skiljetecknets typ (54 %), prepositionen *eftir* eller *at* (45 %), stavningen av *eftir* och *þenna*, *ai* och *auk* med flera;
  - stilgrupp (22 %) och korsets form enligt Lagers typologi i Runor 2020 (23 %);
  - ord om ornamentik (9 %) och runformer (12 %) i Sveriges runinskrifters beskrivningar;
  - gemensamma namn, bergart, kortkvistrunor och avståndet.
- **Träningsparen.** 41 192 par av stenar med säker ristare i Rundata, varav 5 400 med samma ristare.
- **Runologernas grupper.**
  - *Källorna:* de 225 ställen i textbanden av Sveriges runinskrifter där utgivaren säger ”samme ristare”, ”samma hand” eller ”samme mästare”, och Runor 2020:s ”samma som gjort X”.
  - *Läsningen:* ställena lästes av Anthropics språkmodell Claude (Claude Opus) i två instanser, en för varje halva. En tredje läsare kontrolläste 40 slumpvis valda ställen och stämde i {K1['lika']} ({pc(K1['lika'] / K1['stickprov'])} procent), under det förutbestämda kravet 85 procent. Därför lästes alla ställen om med en striktare regel (bara signum som står i texten), och 62 omstridda par avgjordes för hand.
  - *Resultatet:* 409 länkar i 118 grupper, varav 84 par. De delades slumpvis (frö 20261123) i 59 grupper för utveckling och 59 för prov.
- **Litteraturen** (för slutprov 2).
  - *Underlaget:* 2 490 ställen i Fornvännen, Futhark och åtta avhandlingar där en ristare eller ”samma hand” nämns nära ett signum. De lästes av 28 instanser. En blind kontrolläsning av 250 ställen gav {KL['lika_ställen']} identiska ({pc(KL['lika_ställen'] / KL['ställen'])} procent).
  - *Granskningen:* varje uttalande om samma hand, olika händer eller en tillskrivning prövades av två oberoende granskare som skulle försöka motbevisa det. Det behölls bara om båda bekräftade: {GR['samma_hand|bekräftad']} av {GR['samma_hand|bekräftad'] + GR['samma_hand|ej']} om samma hand och {GR['olika_hander|bekräftad']} av {GR['olika_hander|bekräftad'] + GR['olika_hander|ej']} om olika händer.
  - *Resultatet:* {S2['facit2_par']} par som inte redan fanns bland runologernas grupper, i {S2['facit2_grupper']} grupper.

## 4. Metod

### 4.1 Modellen för samma hand
- **Klassificeraren:** gradient boosting (ett stort antal små beslutsträd som läggs till ett i taget, vart och ett rättande de föregåendes fel) på beläggen ovan och avståndet. Saknade belägg lämnas tomma.
- **Träningen:** par av stenar med säker ristare, med ristarna delade slumpvis i fem delar. Ett par av sådana stenar får sin sannolikhet från en modell som inte har sett deras ristare. Övriga par får medel över de fem modellerna.
- **Undantaget:** par inom runologernas grupper och par som rör provdelens stenar ingick aldrig i träningen.

### 4.2 Grupperna
- **Sammanslagningen:** genomsnittlig länkning. De två grupper med högst medelsannolikhet över alla par mellan dem slås ihop först, men bara om alla deras stenar ligger inom 30 km från varandra. Medelvärdet i stället för den starkaste länken hindrar grupperna från att kedja ihop sig till bygder.
- **Gränsen:** sammanslagningen stannar när ingen sannolikhet når τ = 0,8. Gränsen valdes på utvecklingsdelen som den högsta precisionen på par av stenar med känd ristare ({pc(G8['precision_namngivna'])} procent) som samtidigt gav tydlig täckning av utvecklingsdelens par ({pc(G8['facit_samma_grupp'])} mot {d1(100 * G8['grannar_samma_grupp'])} procent för grannar).

### 4.3 Provet
- **Andelen:** för varje grupp av runologer räknas andelen par inom 30 km som hamnar i samma grupp.
- **Kontrollen:** för varje par jämförs med stenar på samma avstånd från den ena stenen (± 25 procent, minst ± 1 km), utanför runologernas grupp, och andelen av dem i samma grupp som den stenen.
- **Testet:** skillnaden per grupp prövas med ett ensidigt Wilcoxon-test (ett rangtest som inte förutsätter normalfördelning) över grupperna, så att en stor grupp inte väger mer än en liten.

### 4.4 Avvikelser från planerna
- **Kontrolläsningen av Sveriges runinskrifter** nådde inte kravet (75 procent). Alla ställen lästes därför om, som planen föreskrev, och oenigheterna avgjordes för hand innan materialet användes.
- **Ett fel i tidigare arbete:** de kategoriska språkdragen hade blivit noll när likheten räknades i tidigare studier, eftersom de är text i materialet. De togs med som egna belägg här (lika eller olika).
- **Runhöjd och stenhöjd** prövades på utvecklingsdelen, gav inget lyft och togs inte med.
- **Märkningen ”svagt underlag”** (23 grupper, mest fragment från samma fyndplats som hålls ihop av platsen) lades till efter att grupperna setts. Den ingår inte i proven.
- **I övrigt** inga avvikelser.

## 5. Resultat

### 5.1 Slutprov 1
- **Alla grupper:** i provdelen hamnade {pc(A['medel_samma'])} procent av runologernas stenpar i samma grupp, mot {pc(A['medel_kontroll'])} procent för grannstenar på samma avstånd. Det gällde {A['grupper']} grupper, bättre i {A['bättre']} och sämre i {A['sämre']}, {pf(A['p'])}.
- **Grupper med händer utan namn**, där ingen sten har en känd ristare: {pc(O['medel_samma'])} mot {d1(100 * O['medel_kontroll'])} procent ({O['grupper']} grupper, bättre i {O['bättre']}, sämre i {O['sämre']}, {pf(O['p'])}).
- **Båda proven höll.** På utvecklingsdelen hade samma mått gett {pc(U1['alla']['medel_samma'])} mot {pc(U1['alla']['medel_kontroll'])} procent.

{chart(True)}

I klartext: när runologerna säger att två stenar är gjorda av samma hand hamnar de i samma grupp ungefär två gånger av fem, medan en sten på samma avstånd hamnar där ungefär en gång av femton. För händer utan namn är det ungefär två gånger av tre.

### 5.2 Slutprov 2: litteraturen
- **De nya paren ur litteraturen:** {pc(T1['medel_samma'])} procent hamnade i samma grupp, mot {pc(T1['medel_kontroll'])} procent för grannstenar ({T1['grupper']} grupper, bättre i {T1['bättre']}, sämre i {T1['sämre']}, {pf(T1['p'])}). Provet höll.
- **Bara händer utan namn:** {pc(T2['medel_samma'])} mot {d1(100 * T2['medel_kontroll'])} procent, men med bara {T2['grupper']} grupper ({pf(T2['p'])}). Det räcker inte för en slutsats.
- **Olika händer:** av {S2['olika_händer_par_inom_30km']} stenpar inom 30 km som en forskare säger har olika händer lade modellen {S2['av_dem_i_samma_grupp']} i samma grupp.

### 5.3 Precision och utvecklingsarbete
- **Precisionen på par av stenar med känd ristare**, mätt så att modellen inte sett deras ristare: {pc(GU[0.9]['precision_namngivna'])} procent vid τ = 0,9, {pc(G8['precision_namngivna'])} procent vid 0,8 och {pc(GU[0.7]['precision_namngivna'])} procent vid 0,7.

- **Modellvarianterna på utvecklingsdelen:** runologernas partner hamnade i median över {pc(M1['median_percentil'])} procent av stenarna på samma avstånd med alla belägg, mot {pc(M0['median_percentil'])} procent med bara stavning och språkdrag. De kategoriska språkdragen stod för en stor del av lyftet. Gemensamma namn tillförde inget.
- **Stabiliteten:** när modellen tränades om med andra slumpvisa delningar stannade i median två tredjedelar av en grupps par ihop.

### 5.4 Uppföljning: huggtekniken och grupperna
- **Huggtekniken:** sex grupper har minst två stenar bland Kitzler Åhfeldts skanningar i Södermanland, sammanlagt 18 stenar. Mätt i fyra huggspårsmått (spårets vinkel, djup, bredd och bottenradie) och jämfört med stenar av samma bergart var stenarna i samma grupp inte tydligt mer lika ({pf(H3['H3D']['p'])}).
- **Gruppen Sö 46, 131, 134, 137, 319 och 367** var inte särskilt lik i huggtekniken ({pf(H3G['G052']['p'])}). Den innehåller ändå tre av Kitzler Åhfeldts fem stenar i gruppen Rak 1 (Sö 131, 137, 367).
- **Totalt** blev det {len(GRP)} grupper av minst tre stenar:
  - {TYP['okänd']} utan någon sten med känd ristare, varav {len(GOOD_UNK)} med gott underlag;
  - {TYP['med']} där alla stenar med känd ristare har samma ristare;
  - {TYP['blandad']} blandade.
- **Mot litteraturen:** av de {len(GOOD_UNK)} grupperna med okänd hand och gott underlag har {LVU['stöds i litteraturen']} redan kopplats ihop av forskare, till exempel Ög 231 och 232 (Källström 2020) och Sö 84, 85, 362 och 363 (Jansson 1958). I {LVU['ny']} nämns stenarna i litteraturen, men inte som samma hand. En grupp motsägs: Stern (2013) säger att U 43 och U 79 har olika händer.

## 6. Diskussion

Metoden gör det som en modell som väljer bland namngivna ristare inte kunde: den känner igen runologernas händer, också de utan namn, långt oftare än platsen ensam gör, och den gör det på bedömningar som hölls undan tills metoden var bestämd, och på ett andra, oberoende material ur litteraturen.

Svagheter, i ordning efter vikt:
1. **Jämförelsematerialet är runologernas bedömningar, inte sanningen.** De bygger delvis på samma slags drag som modellen använder: stavning, stil och plats. Provet visar att metoden återskapar deras bedömningar, inte att bedömningarna är rätt. Också träningen bygger på Rundatas attribueringar, som i Mellansverige till stor del följer Axelson (1993), som själv vägde in stavning och stil.
2. **Läsningen gjordes av en språkmodell.** Utläsningen av Sveriges runinskrifter nådde inte kravet förrän efter en omläsning. Varje uttalande ur litteraturen granskades av två oberoende granskare, men ett fel som båda gör slinker igenom.
3. **Gruppgränserna är känsliga.** Med andra slumpvisa delningar av träningen stannar två tredjedelar av en grupps par ihop i median. Med en något annorlunda träning var bara en tredjedel av grupperna identiska. Det som är prövat är metoden, inte varje grupps exakta gräns.
4. **Fragment och kort text.** Stenar med lite text grupperas på stil, kors och plats, och fragment från samma fyndplats hålls ihop av avståndet. De är märkta, men en sådan grupp säger lite om handen.
5. **Ingen ornamentik i detalj, inga runformer ur bild och ingen huggteknik** ingår i modellen. Huggtekniken prövades bara som uppföljning, på få stenar, och huggspårsmåtten har tidigare följt bergarten mer än handen.

**Var metoden inte ska användas.**
- Inte som en tillskrivning.
- Inte för fragment.
- Inte för stenar mer än 30 km från varandra.
- Inte i landskap med få stenar och få kända ristare, där träningen nästan saknar par.

**Vad som skulle fälla metoden:** ett nytt material av runologiska bedömningar där grupperna inte gör bättre än grannstenar, eller grupper som en granskning av ornamentik och runformer på stenarna själva visar är blandade händer.

## 7. Slutsats

En modell som lär sig vad som skiljer samma hand från olika händer, och som väger samman stavning, språkdrag, stil, kors och plats, bildar grupper av runstenar som runologerna själva håller för samma hand långt oftare än grannstenar på samma avstånd. Detta gäller i två låsta prov och för händer utan namn. Grupperna är hypoteser att pröva med ornamentik, runformer och huggteknik på stenarna, inte nya ristare.

## Data och kod

- Analysen är gjord på Rundata-korpusen med versionsnyckeln {FP}, i Vitki {APP_VERSION}. Kod och planer: https://github.com/Precatio/runes (CC BY 4.0).
- Planerna: `analysplaner/2026-11-23-nya-ristare-program.md`, `…-slutprov-1.md`, `…-slutprov-2-litteraturen.md`, `analysplaner/2026-11-24-nya-ristare-3d.md`.
- Skripten: `utdata/nya_ristare/` (facit.py, belagg.py, parmodell.py, gruppering.py, slutprov.py, litteratur_stallen.py, litteratur_sammanstall.py, slutprov2.py, huggteknik.py) och resultatet `utdata/nya_ristare/resultat.md`. Grupperna i Vitki byggs av `src/hand_groups.py` med samma metod (METHODS.md 14l).
- Kodläget: planen för arbetet i commit `6c6cab4`, slutprov 1 i `69c148d` och `3698ddc`, slutprov 2 i `d59c94f` och `f2c9083`, huggtekniken i `91509e7` och `9a18ecf`.
- Grupperna visas i Vitki under Ristarna och i stenprofilen i Stenöversikten (https://vitkirunor.se).
- Texterna ur Sveriges runinskrifter, Fornvännen, Futhark och avhandlingarna ligger inte i repot. Bara signum och källhänvisningar finns där.

## Referenser

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Jansson, S. B. F. 1958. Sörmländska runstensfynd. *Fornvännen* 53, s. 241–259.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Scientific Archaeology B:9. Stockholm: Stockholms universitet.
- Kitzler Åhfeldt, L. 2020. Provenancing rune carvers on Bornholm through 3D-scanning and multivariate statistics of the carving technique. *European Journal of Archaeology* 23 (1), s. 82–104.
- Kvant, V. 2026a. Statistiska ristarförslag ur runtexterna. Metodrapport, rapportversion 4. https://vitkirunor.se/forskningsrapporter/ristarforslag-blindprov
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholms universitet.
- Källström, M. 2020. Ett runristat gravmonument från Östra Stenby kyrka i Östergötland? *Fornvännen* 115.
- Riksantikvarieämbetet. 2020. *Runor*. Databas över runinskrifter i Sverige. https://app.raa.se/open/runor
- Samnordisk runtextdatabas (Rundata) 3.1. Institutionen för nordiska språk, Uppsala universitet.
- Stern, M. 2013. *Runestone Images and Visual Communication in Viking Age Scandinavia*. Diss. University of Nottingham.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Thompson, C. W. 1975. *Studies in Upplandic Runography*. Austin: University of Texas Press.

:::box Det viktigaste i korthet
- En modell som lär sig vad som skiljer samma hand från olika händer kan peka ut grupper av runstenar som hör ihop, också där ingen namngiven ristare passar.
- Den hittar runologernas egna grupper långt oftare än grannstenar på samma avstånd, i två prov som var låsta i förväg.
- Av de grupper som saknar känd ristare och har gott underlag har de flesta aldrig kopplats ihop i litteraturen.
- Grupperna är hypoteser att pröva på stenarna själva, inte nya ristare.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Methods report, fully tested. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, rune carvers, attribution, same hand, gradient boosting, cluster analysis, preregistration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** Runologists have linked many unsigned runestones to each other: "the same carver as …". A statistical model that only chooses among named carvers cannot see a hand without a name. The aim was to test whether a model that learns what separates stones by the same hand from stones by different hands can form groups of stones that belong together, also where no named carver fits.
**Material.** 2,314 Swedish Viking Age runestones in the Scandinavian Runic-text Database (Rundata) with coordinates, and all 312,550 stone pairs within 30 km. As the comparison, the runologists' own statements about the same hand were used: in Sveriges runinskrifter and Runor 2020 (118 groups), and in Fornvännen, Futhark and eight theses (63 new pairs).
**Method.** A gradient boosting model was trained on pairs of stones with a known carver and gave each stone pair a probability of the same hand. The stones were joined into groups by average linkage within 30 km. The runologists' groups were split at random into a development half and a test half. The method was fixed entirely on the development half, and the test half was opened once in a locked final test. A second locked test was made against the literature.
**Results.** In the test half, {pc(A['medel_samma'])} percent of the runologists' stone pairs ended up in the same group, against {pc(A['medel_kontroll'])} percent for neighbouring stones at the same distance ({A['grupper']} groups, better in {A['bättre']} and worse in {A['sämre']}, {pf(A['p'], True)}). For hands without a name it was {pc(O['medel_samma'])} against {d1(100 * O['medel_kontroll'], True)} percent ({O['grupper']} groups, {pf(O['p'], True)}). Against the literature it was {pc(T1['medel_samma'])} against {pc(T1['medel_kontroll'])} percent ({T1['grupper']} groups, {pf(T1['p'], True)}). About {pc(G8['precision_namngivna'])} percent of the pairs in the same group have the same carver, measured on stones with a known carver. The carving technique in 3D scans neither supported nor refuted the groups.
**Conclusion.** The method reproduces the runologists' judgements of the same hand far more often than place alone does. It gives {len(GRP)} groups of at least three stones, and {len(GOOD_UNK)} of them have good evidence and no stone with a known carver. The groups are testable hypotheses, not new carvers.

## 1. Introduction

The carvers behind most runestones are unknown. Jan Axelson (1993) listed the signed and attributed inscriptions in central Sweden, Per Stille (1999) attributed the stones of Fjädrundaland, and Magnus Källström (2007) has studied the carvers and their writing environments across Scandinavia. The runologists have also linked unsigned stones to each other without naming the carver, in Sveriges runinskrifter and in Runor (Swedish National Heritage Board 2020). Claiborne Thompson (1975) showed how spelling separates carvers, and Laila Kitzler Åhfeldt (2002, 2020) has separated carvers by the shape of the grooves in laser scans.

A statistical model that chooses among the named carvers cannot see a hand without a name. When such a model was tested against the runologists' groups "same as made X" in Runor 2020, it gave the same carver within the groups about as often as for neighbouring stones at the same distance (Kvant 2026a). A measure of how alike two inscriptions are in spelling and language traits, beyond what neighbours at the same distance are, did however recognise the runologists' pairs. But groups built from that measure became districts, not hands.

We have found no method that forms groups of runestones by the same hand across the whole material and that has been tested against the runologists' judgements with part of them held back. The aim here is to report such a method and two locked tests of it.

## 2. Preregistration

The work followed four plans, locked in the project's version control before what they concerned was computed:
- **The plan for the work** (2026-11-23, SHA-256 `{SHA['program'][:16]}…`). It decided how the comparison material is built, that it is split into a development half and a test half with the groups as units, and that the test half is used only in locked final tests, at most three times before a new material is built.
- **Final test 1** (2026-11-23, `{SHA['s1'][:16]}…`), locked before the test half was opened. It fixed the method, the threshold τ = 0.8, the measure and the outcome: the test holds if a one-sided Wilcoxon test over the groups gives p below 0.05 and the share in the same group is larger than the control's.
- **Final test 2** (2026-11-23, `{SHA['s2'][:16]}…`): the same method and measure against new pairs from the literature, locked before the pairs were compared with the groups. Before the lock a descriptive count had been seen: how many groups had at least one pair in the unreviewed reading. The test measure had not been seen.
- **The carving technique** (2026-11-24, `{SHA['3d'][:16]}…`): whether stones in the same group are more alike in four groove measures than stones of the same rock type.

Final tests 1 and 2 are the confirmatory tests; the carving technique is a follow-up. The comparisons between model variants (5.3) are development work on the development half and not tests.

## 3. Material

- **The stones.** Scandinavian Runic-text Database (Rundata) 3.1, frozen for the analysis. 2,314 Swedish Viking Age runestones with coordinates, except Bohuslän. Distances were computed in SWEREF 99 TM.
- **The pairs.** All 312,550 stone pairs within 30 km.
- **The evidence per pair**, with the share of pairs where the evidence exists:
  - spelling, word dividers, bind runes, language traits, formulas and content, as likeness beyond neighbours at the same distance (46 %);
  - the categorical language traits, alike or not: the type of word divider (54 %), the preposition *eftir* or *at* (45 %), the spelling of *eftir* and *þenna*, *ai* and *auk* and others;
  - style group (22 %) and the shape of the cross after Lager's typology in Runor 2020 (23 %);
  - words about the ornament (9 %) and rune forms (12 %) in the descriptions in Sveriges runinskrifter;
  - shared names, rock type, short-twig runes and the distance.
- **The training pairs.** 41,192 pairs of stones with a certain carver in Rundata, of which 5,400 with the same carver.
- **The runologists' groups.**
  - *The sources:* the 225 places in the text volumes of Sveriges runinskrifter where the editor says "the same carver", "the same hand" or "the same master", and Runor 2020's "same as made X".
  - *The reading:* the places were read by Anthropic's language model Claude (Claude Opus) in two instances, one for each half. A third reader checked 40 places chosen at random and agreed in {K1['lika']} ({pc(K1['lika'] / K1['stickprov'])} percent), below the requirement of 85 percent fixed in advance. Therefore all places were read again with a stricter rule (only signa written in the text), and 62 disputed pairs were decided by hand.
  - *The result:* 409 links in 118 groups, of which 84 pairs. They were split at random (seed 20261123) into 59 groups for development and 59 for testing.
- **The literature** (for final test 2).
  - *The material:* 2,490 places in Fornvännen, Futhark and eight theses where a carver or "the same hand" is mentioned near a signum. They were read by 28 instances. A blind check of 250 places gave {KL['lika_ställen']} identical ({pc(KL['lika_ställen'] / KL['ställen'])} percent).
  - *The review:* every statement about the same hand, different hands or an attribution was tried by two independent reviewers who were to try to refute it. It was kept only if both confirmed it: {GR['samma_hand|bekräftad']} of {GR['samma_hand|bekräftad'] + GR['samma_hand|ej']} about the same hand and {GR['olika_hander|bekräftad']} of {GR['olika_hander|bekräftad'] + GR['olika_hander|ej']} about different hands.
  - *The result:* {S2['facit2_par']} pairs not already among the runologists' groups, in {S2['facit2_grupper']} groups.

## 4. Method

### 4.1 The model of the same hand
- **The classifier:** gradient boosting (a large number of small decision trees added one at a time, each correcting the errors of the earlier ones) on the evidence above and the distance. Missing evidence is left empty.
- **The training:** pairs of stones with a certain carver, with the carvers split at random into five parts. A pair of such stones gets its probability from a model that has not seen their carver. Other pairs get the mean over the five models.
- **The exclusion:** pairs within the runologists' groups and pairs touching the test half's stones never entered the training.

### 4.2 The groups
- **The joining:** average linkage. The two groups with the highest mean probability over all pairs between them are joined first, but only if all their stones lie within 30 km of each other. The mean instead of the strongest link keeps the groups from chaining into districts.
- **The threshold:** the joining stops when no probability reaches τ = 0.8. The threshold was chosen on the development half as the highest precision on pairs of stones with a known carver ({pc(G8['precision_namngivna'])} percent) that also gave a clear coverage of the development half's pairs ({pc(G8['facit_samma_grupp'])} against {d1(100 * G8['grannar_samma_grupp'], True)} percent for neighbours).

### 4.3 The test
- **The share:** for each of the runologists' groups, the share of pairs within 30 km that end up in the same group.
- **The control:** each pair is compared with stones at the same distance from one of the stones (± 25 percent, at least ± 1 km), outside the runologists' group, and the share of them in the same group as that stone.
- **The test:** the difference per group is tested with a one-sided Wilcoxon test (a rank test that does not assume a normal distribution) over the groups, so that a large group does not weigh more than a small one.

### 4.4 Deviations from the plans
- **The check reading of Sveriges runinskrifter** did not reach the requirement (75 percent). All places were therefore read again, as the plan prescribed, and the disagreements were decided by hand before the material was used.
- **An error in earlier work:** the categorical language traits had become zero when the likeness was computed in earlier studies, because they are text in the material. They were included as their own evidence here (alike or not).
- **Rune height and stone height** were tried on the development half, gave no lift and were not included.
- **The label "weak evidence"** (23 groups, mostly fragments from the same find place held together by the place) was added after the groups had been seen. It is not part of the tests.
- **Otherwise** no deviations.

## 5. Results

### 5.1 Final test 1
- **All groups:** in the test half, {pc(A['medel_samma'])} percent of the runologists' stone pairs ended up in the same group, against {pc(A['medel_kontroll'])} percent for neighbouring stones at the same distance. This covered {A['grupper']} groups, better in {A['bättre']} and worse in {A['sämre']}, {pf(A['p'], True)}.
- **Groups with hands without a name**, where no stone has a known carver: {pc(O['medel_samma'])} against {d1(100 * O['medel_kontroll'], True)} percent ({O['grupper']} groups, better in {O['bättre']}, worse in {O['sämre']}, {pf(O['p'], True)}).
- **Both tests held.** On the development half the same measure had given {pc(U1['alla']['medel_samma'])} against {pc(U1['alla']['medel_kontroll'])} percent.

{chart(False)}

In plain words: when the runologists say two stones were made by the same hand, they end up in the same group about two times in five, while a stone at the same distance ends up there about one time in fifteen. For hands without a name it is about two times in three.

### 5.2 Final test 2: the literature
- **The new pairs from the literature:** {pc(T1['medel_samma'])} percent ended up in the same group, against {pc(T1['medel_kontroll'])} percent for neighbouring stones ({T1['grupper']} groups, better in {T1['bättre']}, worse in {T1['sämre']}, {pf(T1['p'], True)}). The test held.
- **Hands without a name only:** {pc(T2['medel_samma'])} against {d1(100 * T2['medel_kontroll'], True)} percent, but with only {T2['grupper']} groups ({pf(T2['p'], True)}). That is not enough for a conclusion.
- **Different hands:** of {S2['olika_händer_par_inom_30km']} stone pairs within 30 km that a researcher says have different hands, the model put {S2['av_dem_i_samma_grupp']} in the same group.

### 5.3 Precision and development work
- **The precision on pairs of stones with a known carver**, measured so that the model had not seen their carver: {pc(GU[0.9]['precision_namngivna'])} percent at τ = 0.9, {pc(G8['precision_namngivna'])} percent at 0.8 and {pc(GU[0.7]['precision_namngivna'])} percent at 0.7.

- **The model variants on the development half:** the runologists' partner ranked in median above {pc(M1['median_percentil'])} percent of the stones at the same distance with all evidence, against {pc(M0['median_percentil'])} percent with spelling and language traits only. The categorical language traits accounted for much of the lift. Shared names added nothing.
- **The stability:** when the model was retrained with other random splits, in median two thirds of a group's pairs stayed together.

### 5.4 Follow-up: the carving technique and the groups
- **The carving technique:** six groups have at least two stones among Kitzler Åhfeldt's scans in Södermanland, 18 stones in all. Measured in four groove measures (the groove's angle, depth, width and bottom radius) and compared with stones of the same rock type, the stones in the same group were not clearly more alike ({pf(H3['H3D']['p'], True)}).
- **The group Sö 46, 131, 134, 137, 319 and 367** was not particularly alike in carving technique ({pf(H3G['G052']['p'], True)}). It still contains three of Kitzler Åhfeldt's five stones in the group Rak 1 (Sö 131, 137, 367).
- **In all** there were {len(GRP)} groups of at least three stones:
  - {TYP['okänd']} without any stone with a known carver, of which {len(GOOD_UNK)} with good evidence;
  - {TYP['med']} where all stones with a known carver have the same carver;
  - {TYP['blandad']} mixed.
- **Against the literature:** of the {len(GOOD_UNK)} unknown-hand groups with good evidence, {LVU['stöds i litteraturen']} have already been linked by researchers, for example Ög 231 and 232 (Källström 2020) and Sö 84, 85, 362 and 363 (Jansson 1958). In {LVU['ny']} the stones are mentioned in the literature, but not as the same hand. One group is contradicted: Stern (2013) says that U 43 and U 79 have different hands.

## 6. Discussion

The method does what a model choosing among named carvers could not: it recognises the runologists' hands, also those without a name, far more often than place alone does, and it does so on judgements held back until the method was fixed, and on a second, independent material from the literature.

Weaknesses, in order of importance:
1. **The comparison material is the runologists' judgements, not the truth.** They rest partly on the same kind of features the model uses: spelling, style and place. The test shows that the method reproduces their judgements, not that the judgements are right. The training also rests on Rundata's attributions, which in central Sweden largely follow Axelson (1993), who himself weighed spelling and style.
2. **The reading was done by a language model.** The reading of Sveriges runinskrifter did not reach the requirement until after a second reading. Every statement from the literature was reviewed by two independent reviewers, but an error both make slips through.
3. **The group boundaries are sensitive.** With other random splits of the training, in median two thirds of a group's pairs stay together. With a somewhat different training only a third of the groups were identical. What has been tested is the method, not each group's exact boundary.
4. **Fragments and short texts.** Stones with little text are grouped on style, cross and place, and fragments from the same find place are held together by the distance. They are labelled, but such a group says little about the hand.
5. **No detailed ornament, no rune forms from images and no carving technique** are part of the model. The carving technique was only tested as a follow-up, on few stones, and the groove measures have earlier followed the rock type more than the hand.

**Where the method should not be used.**
- Not as an attribution.
- Not for fragments.
- Not for stones more than 30 km apart.
- Not in provinces with few stones and few known carvers, where the training has almost no pairs.

**What would refute the method:** a new material of runological judgements where the groups do no better than neighbouring stones, or groups that an examination of the ornament and rune forms on the stones themselves shows to be mixed hands.

## 7. Conclusion

A model that learns what separates the same hand from different hands, and that weighs together spelling, language traits, style, cross and place, forms groups of runestones that the runologists themselves hold to be the same hand far more often than neighbouring stones at the same distance. This holds in two locked tests and for hands without a name. The groups are hypotheses to be tested with ornament, rune forms and carving technique on the stones, not new carvers.

## Data and code

- The analysis was made on the Rundata corpus with the version key {FP}, in Vitki {APP_VERSION}. Code and plans: https://github.com/Precatio/runes (CC BY 4.0).
- The plans: `analysplaner/2026-11-23-nya-ristare-program.md`, `…-slutprov-1.md`, `…-slutprov-2-litteraturen.md`, `analysplaner/2026-11-24-nya-ristare-3d.md`.
- The scripts: `utdata/nya_ristare/` (facit.py, belagg.py, parmodell.py, gruppering.py, slutprov.py, litteratur_stallen.py, litteratur_sammanstall.py, slutprov2.py, huggteknik.py) and the result `utdata/nya_ristare/resultat.md`. The groups in Vitki are built by `src/hand_groups.py` with the same method (METHODS.md 14l).
- The code state: the plan for the work in commit `6c6cab4`, final test 1 in `69c148d` and `3698ddc`, final test 2 in `d59c94f` and `f2c9083`, the carving technique in `91509e7` and `9a18ecf`.
- The groups are shown in Vitki under The carvers and in the stone profile in the Stone overview (https://vitkirunor.se).
- The texts from Sveriges runinskrifter, Fornvännen, Futhark and the theses are not in the repository. Only signa and source references are there.

## References

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter* [Central Swedish rune carvers]. Runrön 5. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Jansson, S. B. F. 1958. Sörmländska runstensfynd [Runestone finds in Södermanland]. *Fornvännen* 53, pp. 241–259.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Scientific Archaeology B:9. Stockholm: Stockholm University.
- Kitzler Åhfeldt, L. 2020. Provenancing rune carvers on Bornholm through 3D-scanning and multivariate statistics of the carving technique. *European Journal of Archaeology* 23 (1), pp. 82–104.
- Kvant, V. 2026a. Statistical carver suggestions from the runic texts. Methods report, report version 4. https://vitkirunor.se/en/forskningsrapporter/ristarforslag-blindprov
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden* [Masters and memorials]. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholm University.
- Källström, M. 2020. Ett runristat gravmonument från Östra Stenby kyrka i Östergötland? [A rune-inscribed grave monument from Östra Stenby church in Östergötland?]. *Fornvännen* 115.
- Scandinavian Runic-text Database (Rundata) 3.1. Department of Scandinavian Languages, Uppsala University.
- Stern, M. 2013. *Runestone Images and Visual Communication in Viking Age Scandinavia*. PhD thesis, University of Nottingham.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering* [Runestones and rune carvers in Viking Age Fjädrundaland]. Runrön 13. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Swedish National Heritage Board (Riksantikvarieämbetet). 2020. *Runor*. Database of runic inscriptions in Sweden. https://app.raa.se/open/runor
- Thompson, C. W. 1975. *Studies in Upplandic Runography*. Austin: University of Texas Press.

:::box The essentials
- A model that learns what separates the same hand from different hands can point out groups of runestones that belong together, also where no named carver fits.
- It finds the runologists' own groups far more often than neighbouring stones at the same distance, in two tests locked in advance.
- Of the groups without a known carver and with good evidence, most have never been linked in the literature.
- The groups are hypotheses to be tested on the stones themselves, not new carvers.
:::
"""

# ---- kontroller (mallen) -----------------------------------------------------------------------------------------------
assert "I klartext" in body and "In plain words" in body_en
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS|\bAI\b"
for b in (body, body_en):
    assert not re.search(r"^\s*\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
    assert FP not in head
    assert "](/" not in b
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Metodrapport, fullt prövad. Rapportversion 1, 2026-11-24. Tidslinje: ")
assert body_en.split("\n", 1)[0].startswith("*Viktor Kvant, independent researcher. Methods report, fully tested. Report version 1, 2026-11-24. Timeline: ")
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
SEC = lambda b: [re.match(r"[\d.]*", h).group(0) for h in re.findall(r"^##+ (.+)$", b, re.M)]  # noqa: E731
assert SEC(body) == SEC(body_en), (SEC(body), SEC(body_en))
assert len(re.findall(r"^\s*- ", body, re.M)) == len(re.findall(r"^\s*- ", body_en, re.M))
assert len(re.findall(r"^\s*\d+\. ", body, re.M)) == len(re.findall(r"^\s*\d+\. ", body_en, re.M))
words = len(body.split("## Data")[0].split())
assert 1500 <= words <= 3200, words

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
