"""Forskningsrapport (låst mall utdata/rapporter/MALL.md): "I västra Uppland skrevs ʀ med r fem gånger så ofta som i resten
av landet" (sv + en). Klustret ur den rumsliga skanningen (r/hotspots.R), känslighetsanalyserna (src/robustness.py,
METHODS 1v) och de explorativa räkningarna om ristaren Erik och tiden, allt på korpusens version e83202e01a5e6d27.
Figurerna ritas av utdata/rapporter/figurer/karta_r_for_R.R. Varje siffra asserteras mot filerna.
    ../../../.venv/bin/python build_rapport_r_for_R.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

import pandas as pd
from scipy import stats

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels, r_findings, robustness  # noqa: E402
from src import r_bridge as rb  # noqa: E402

FP = "e83202e01a5e6d27"
C = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
DONE = json.load(open(os.path.join(C, "done.json"), encoding="utf-8"))
assert DONE["fingerprint"] == FP and DONE["r_version"].startswith("R version 4.6.1")
APP_VERSION = json.load(open(os.path.join(ROOT, "web", "package.json")))["version"]
assert APP_VERSION == "3.0.0"
REPORT_VERSION = 1
TODAY = dt.date.today().isoformat()

pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731  (half up; the result files round to 3 decimals, 0.565 is 56.5 %)
d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731
d1 = lambda x: f"{x:.1f}".replace(".", ",")  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_n = lambda n: f"{n:,}"  # noqa: E731


def pfmt(p, en=False):
    if p < 0.001:
        return "p < 0.001" if en else "p < 0,001"
    s = f"{p:.3f}" if p < 0.01 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the scan (r/hotspots.R) -------------------------------------------------------------------------------------------
H = json.load(open(os.path.join(C, "hotspots.json"), encoding="utf-8"))
assert (H["n_stones"], H["k"], H["ubpop"], H["nsim"]) == (1097, 8, 0.1, 999)
N_TRAITS = len(H["patterns"])
assert N_TRAITS == 13
PAT = next(x for x in H["patterns"] if x["key"] == "r_for_R")
CL = PAT["clusters"][0]
assert (PAT["n"], PAT["cases"], PAT["n_hot"], PAT["n_cold"]) == (514, 87, 32, 0)
MO = PAT["moran"]
assert round(MO["i"], 3) == 0.183 and MO["p"] < 1e-20
assert (CL["center"], round(CL["radius_km"], 1), CL["n"], CL["cases"]) == ("U 1172", 30.4, 36, 24)
assert (pc(CL["rate_in"]), pc(CL["rate_out"]), d2(CL["rr"]), CL["p"], CL["q_bh"]) == (67, 13, "5,06", 0.001, 0.013)
HA, HB = CL["halves"]["A"], CL["halves"]["B"]
assert CL["halves"]["replicated"] and (pc(HA["rate_in"]), pc(HA["rate_out"]), pc(HB["rate_in"]), pc(HB["rate_out"])) == (85, 12, 57, 15)
assert HA["p"] < 1e-7 and HB["p"] < 1e-4 and round(HA["or"]) == 41 and d1(HB["or"]) == "7,3"
SIG_TRAITS = [(p["key"], p["clusters"][0]["q_bh"]) for p in H["patterns"] if p.get("clusters")]
assert [k for k, q in SIG_TRAITS if q < 0.05] == ["r_for_R"]  # the only trait whose cluster passes the adjustment
HOT_VG = [s["signum"] for s in PAT["stones"] if s["signum"].startswith("Vg")]
HOT_UVS = [s["signum"] for s in PAT["stones"] if not s["signum"].startswith("Vg")]
assert (len(HOT_VG), len(HOT_UVS)) == (9, 23) and HOT_VG == ["Vg 2", "Vg 3", "Vg 4", "Vg 6", "Vg 12", "Vg 13", "Vg 15", "Vg 16", "Vg 106"]
INSIDE = set(CL["stones"])
RD = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
assert RD["U 1172"]["place"].startswith("Holm") and RD["U 1172"]["parish"] == "Vittinge sn"
PAR = pd.Series([RD[s]["parish"] for s in INSIDE]).value_counts()
assert (PAR["Simtuna sn"], PAR["Vårfrukyrka sn"], PAR["Tillinge sn"]) == (5, 3, 3)

# ---- the stones (corpus.csv): trait known, not moved (as in the scan) -------------------------------------------------
d = pd.read_csv(os.path.join(C, "corpus.csv"), low_memory=False)
N_ALL = len(d)
assert N_ALL == 2321  # rows; the Swedish Viking-Age runestones (the people module counts 2 320 with a region)
k = d[d.pm_r_for_R.notna() & ((d.moved.isna()) | (d.moved == 0))].copy()
assert len(k) == 514 and int(k.pm_r_for_R.sum()) == 87
k["inside"] = k.signum.isin(INSIDE)
S = k["style"]
early, late = S.isin(["RAK", "Fp", "Pr1", "Pr2"]), S.isin(["Pr3", "Pr4", "Pr5"])
erik_all = k.carvers_all.fillna("").str.contains("Erik")
erik = (k.carver == "Erik") & (k.carvers_uncertain == 0)


def frac(x):
    return int(x.pm_r_for_R.sum()), len(x)


def fisher(a, b):
    return stats.fisher_exact([[a[0], a[1] - a[0]], [b[0], b[1] - b[0]]])


E_IN, E_OUT = frac(k[erik & k.inside]), frac(k[erik & ~k.inside])
assert (E_IN, E_OUT) == ((11, 11), (1, 1)) and list(k[erik & ~k.inside].signum) == ["U 774"]
assert set(k[erik]["style"]) == {"Fp"} and frac(k[erik_all]) == (15, 15)
UNC = sorted(k[erik_all & ~erik].signum, key=lambda x: int(x.split()[1]))
assert UNC == ["U 732", "U 755", "U 1151"]
EA_IN, EA_OUT = frac(k[early & k.inside]), frac(k[early & ~k.inside])
assert (EA_IN, EA_OUT) == ((15, 15), (34, 182)) and frac(k[early & k.inside & ~erik_all]) == (2, 2)
FP_U_OUT = frac(k[(S == "Fp") & ~k.inside & (k.province == "U")])
assert FP_U_OUT == (7, 9)
LA_IN, LA_U_OUT = frac(k[late & k.inside]), frac(k[late & ~k.inside & (k.province == "U")])
assert (LA_IN, LA_U_OUT) == ((7, 16), (12, 109))
P_LATE = fisher(LA_IN, LA_U_OUT)[1]
assert 0.002 < P_LATE < 0.004
NE_IN, ALL_OUT = frac(k[k.inside & ~erik_all]), frac(k[~k.inside])
assert (NE_IN, ALL_OUT) == ((11, 23), (63, 478))
P_NE = fisher(NE_IN, ALL_OUT)[1]
assert P_NE < 0.001
B = k[(k.carver == "Balle") & (k.carvers_uncertain == 0)]
B_IN, B_OUT = frac(B[B.inside]), frac(B[~B.inside])
P_B = fisher(B_IN, B_OUT)[1]
assert (B_IN, B_OUT) == ((3, 5), (5, 19)) and 0.25 < P_B < 0.35
BALL = k[k.carvers_all.fillna("").str.contains("Balle")]  # Balli with the uncertain attributions too
BA_IN, BA_OUT = frac(BALL[BALL.inside]), frac(BALL[~BALL.inside])
P_BA = fisher(BA_IN, BA_OUT)[1]
assert (BA_IN, BA_OUT) == ((5, 7), (6, 20)) and 0.08 < P_BA < 0.09
A = k[(k.carver == "Åsmund") & (k.carvers_uncertain == 0)]
A_IN, A_OUT = frac(A[A.inside]), frac(A[~A.inside])
assert (A_IN, A_OUT) == ((0, 3), (0, 10))
U_OUT, SO, VG = frac(k[(k.province == "U") & ~k.inside]), frac(k[k.province == "Sö"]), frac(k[k.province == "Vg"])
assert (U_OUT, SO, VG) == ((39, 244), (7, 80), (9, 41))
# Erik's signed stone is not counted: a gap breaks the word pairing (hand reading in the text)
assert pd.isna(d[d.signum == "U 1165"].pm_r_for_R.iloc[0]) and "airikr" in RD["U 1165"]["transliteration"] and "-ftir" in RD["U 1165"]["transliteration"]

# ---- the sensitivity analyses (src/robustness.py) ----------------------------------------------------------------------
ROB = json.load(open(os.path.join(C, "robustness.json"), encoding="utf-8"))
P = ROB["patterns"]["Geografi|hotspot_r_for_R_U"]
SPEC = ROB["specs"]["Geografi|hotspot_r_for_R_U"]
RU = P["rungs"]
assert (P["n"], P["k"], P["direction"]) == (514, 87, 1) and set(RU) == {"raw", "adjusted", "carver", "parish", "half_A", "half_B", "moved_rundata", "moved_runor"}
assert all(r["holds"] for r in RU.values()) and SPEC["selected"] and not SPEC["lopo"] and not SPEC["place"]
assert [round(RU[x]["or"], 1) for x in ("raw", "adjusted", "carver", "parish", "half_A", "half_B", "moved_runor")] == [13.2, 13.0, 16.7, 15.9, 10.0, 19.0, 10.5]
assert (RU["carver"]["groups"], RU["parish"]["groups"], RU["half_A"]["n"], RU["half_B"]["n"], RU["moved_runor"]["n"]) == (272, 280, 262, 252, 447)
assert max(r["p"] for r in RU.values()) < 0.001
EF, CK = P["effect"], P["check"]
assert (pc(EF["share_hi"]), pc(EF["share_lo"]), round(100 * EF["diff"]), [round(100 * x) for x in EF["diff_ci"]]) == (63, 13, 50, [32, 67])
assert CK["ok"] and min(CK["uniformity_p"], CK["dispersion_p"], CK["spatial_p"]) > 0.05 and P.get("coding") is None
ANN = robustness.annotate(r_findings.corpus_patterns(rb.JOB.result(FP)), robustness.load(FP))
ME = next(x for x in ANN if x["key"] == "hotspot_r_for_R_U")
SUMM = robustness.summary(ANN)
N_SHOWN, N_ALLRUNG = SUMM["n_fdr"], SUMM["all_rungs"]
assert ME["confirmed"] is True and ME["ladder"]["passed"] == ME["ladder"]["tested"] == 8 and 0.015 < ME["q_global"] < 0.025
assert (N_SHOWN, N_ALLRUNG) == (48, 15)
QG = d2(ME["q_global"])
QGe = f"{ME['q_global']:.2f}"

# ---- the figures (utdata/rapporter/figurer/karta_r_for_R.R) --------------------------------------------------------------
FIG = os.path.join(ROOT, "utdata", "rapporter", "figurer")
FIGS = {f"{v}_{lang}": blog_figures.freeze(open(os.path.join(FIG, f"karta_r_for_R{'' if v == 'riket' else '_zoom'}_{lang}.png"), "rb").read())
        for v in ("riket", "zoom") for lang in ("sv", "en")}

SLUG = "r-for-yr-runan-vastra-uppland"
title = "I västra Uppland skrevs ʀ med r fem gånger så ofta som i resten av landet"
title_en = "In western Uppland ʀ was written with r five times as often as in the rest of the country"
summary = ("Runstenar där ljudet ʀ skrivs med den vanliga r-runan samlas i västra Uppland: 67 procent av stenarna inom 30 kilometer "
           "från Holm i Vittinge mot 13 procent i resten av landet. Fyndet håller i båda halvorna av materialet och i alla "
           "känslighetsanalyser. Ristaren Erik skrev så på alla sina stenar, men klustret står kvar utan dem.")
summary_en = ("Runestones on which the sound ʀ is written with the ordinary r-rune cluster in western Uppland: 67 percent of the stones "
              "within 30 kilometres of Holm in Vittinge against 13 percent in the rest of the country. The finding holds in both "
              "halves of the material and in every sensitivity analysis. The carver Erik wrote so on all his stones, but the "
              "cluster remains without them.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/artiklar/{SLUG}")

body = f"""*Viktor Kvant, oberoende forskare. Rapportversion {REPORT_VERSION}, {TODAY}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, yr-runan, ʀ, r, Uppland, ristare, rumslig statistik. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** I runsvenskan fanns två r-ljud, r och ʀ, med var sin runa. Under 1000-talet skrivs ʀ allt oftare med den vanliga r-runan, och tidigare forskning har visat att detta varierar mellan landskap och ristare. Frågan här är om stavningen samlas geografiskt mer än slumpen ger, var, och om samlingen tål en fast serie känslighetsanalyser.
**Material.** {sp(PAT['n'])} vikingatida runstenar i de svenska landskapen där det går att avgöra hur ʀ är skrivet och som står kvar på sin ursprungliga plats, ur Samnordisk runtextdatabas (Rundata).
**Metod.** Rumslig autokorrelation (Morans I), lokala heta områden (Getis-Ord Gi∗) och Kulldorffs rumsliga scanstatistik med 999 Monte Carlo-simuleringar, justerat för de {N_TRAITS} stavnings- och innehållsdrag som skannades; intern replikering i två på förhand bestämda halvor av materialet; åtta känslighetsanalyser; justering för alla {N_SHOWN} samband som projektet redovisar.
**Resultat.** Inom {d1(CL['radius_km'])} kilometer från Holm i Vittinge socken har {CL['cases']} av {CL['n']} stenar r för ʀ ({pc(CL['rate_in'])} procent), mot {pc(CL['rate_out'])} procent i resten av landet; skanningens p = 0,001, justerat för de {N_TRAITS} dragen q = 0,013. Samma riktning i båda halvorna ({pc(HA['rate_in'])} mot {pc(HA['rate_out'])} och {pc(HB['rate_in'])} mot {pc(HB['rate_out'])} procent), alla känslighetsanalyser håller, och justerat för alla samband q = {QG}. Explorativt: ristaren Erik skrev r på alla sina {E_IN[1] + E_OUT[1]} säkert attribuerade stenar, men klustret står kvar utan dem ({NE_IN[0]} av {NE_IN[1]} stenar), och bland de senare stenarna i bygden är stavningen fyra gånger så vanlig som i övriga Uppland.
**Slutsats.** Västra Uppland är det område i Sverige där ʀ oftast skrevs med r. Stavningen följde ristaren snarare än platsen, och vi föreslår att klustret är en skrivtradition som började med Erik och fördes vidare. Tidigare forskning har läst Eriks r som uttal; det kan materialet ännu inte utesluta.

## 1. Inledning

Runsvenskan hade två r-ljud. Det ena, r, är det vanliga. Det andra, ʀ, går tillbaka på ett äldre *z* och står bland annat i ändelser som *æftiʀ* ’efter’, *þæiʀ* ’de’ och *stæinaʀ* ’stenar’. Det hade en egen runa, yr-runan ᛦ. Med tiden föll ljuden samman, och i de senare vikingatida inskrifterna skrivs ʀ allt oftare med den vanliga r-runan.

Patrik Larsson (2002) har i sin avhandling om yr-runan gått igenom hur äldre ʀ betecknas i alla nordiska runinskrifter. Han visar att andelen skrivningar med r-runa efter vokal är betydligt högre i Uppland, Västergötland och på Gotland (18–28 procent) än i andra landskap med många belägg (avsnitt 7.2.2), och att den uppländska gruppen i stilen Fp till stor del består av inskrifter av ristaren Erik, som konsekvent skriver r-runa för ʀ (avsnitt 7.2.3). Per Stille (1999, s. 206) har i sin studie av ristarna i Fjädrundaland iakttagit detsamma om Erik och dragit slutsatsen att r och ʀ hade fallit samman i hans språk. Larsson för Erik till de ristare som inte tycks ha haft kvar någon skillnad mellan ljuden (avsnitt 7.2.1) och argumenterar för att den ökande användningen av r-runan i stort speglar en pågående språkförändring, inte en ortografisk reform (avsnitt 7.3).

Det som saknas i den litteraturen är ett mått på om stavningen samlas geografiskt mer än slumpen ger, oberoende av landskapsgränser, och om en sådan samling står kvar när stenarnas ålder och ristarnas egna vanor hålls konstanta. Syftet med den här studien är att mäta det, och att pröva vad mätningen säger om den förklaring tidigare forskning har gett. Uttalet prövas inte direkt, men avsnitt 6 tar ställning till vad mönstret säger om det.

## 2. Förregistrering: vad som var bestämt i förväg och vad som är explorativt

Ingen analysplan låstes för den här frågan innan resultaten var kända. Fyndet är alltså inte förregistrerat, och det ska läsas som upptäckt i en systematisk genomsökning.

Genomsökningen var en allmän metod som tillämpades på en gång på {N_TRAITS} drag i runstenarnas stavning och innehåll, bland dem r för ʀ. Metoden, gränserna (cirklar som rymmer högst en tiondel av stenarna, 999 simuleringar, justering över dragen) och indelningen av materialet i två halvor bestämdes i programkoden innan genomsökningen kördes, och de var desamma för alla drag. Ingen hypotes om r för ʀ eller om västra Uppland fanns före genomsökningen.

Fyra saker gör att fyndet ändå inte beror på att vi valde det:

1. Scanstatistikens p-värde räknar med alla cirklar som prövades; det är sannolikheten att det mest extrema området skulle vara så extremt om stavningen vore jämnt fördelad.
2. p-värdena justeras för de {N_TRAITS} dragen som skannades, och därtill för alla {N_SHOWN} samband som projektet redovisar.
3. Halvorna bestämdes oberoende av mönstren, och klustret ska hålla i var halva för sig.
4. Samma känslighetsanalyser som för alla andra samband.

Analyserna i avsnitt 5.1–5.3 är de som metoden föreskriver för varje drag. Avsnitt 5.4 om ristaren Erik och om tiden är explorativt: det räknades efter att klustret var känt och redovisas beskrivande, med p-värden som inte är justerade för att frågorna valdes i efterhand.

## 3. Material

- **Källa.** Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk vid Uppsala universitet: translitterering, normalisering, landskap, socken, plats, ristare och stilgruppering för varje inskrift. Materialet frystes för analysen den 29 oktober 2026.
- **Stenarna.** Vikingatida runstenar i de svenska landskapen. Bara runstenar; andra föremål med runor ingår inte. Skåne och Blekinge, som var danska under vikingatiden, förs i Rundata till Danmark och ingår inte. Av stenarna har {sp(H['n_stones'])} känt läge och står kvar på sin ursprungliga plats; stenar som enligt Rundata eller Riksantikvarieämbetets register Runor (2020) har flyttats räknas inte, eftersom deras plats inte säger var de ristades.
- **Draget.** För varje sten tas de ord vars normaliserade form slutar på ʀ och vars huggna form slutar på r- eller ʀ-runan. Stenen räknas som *r för ʀ* om minst en sådan ändelse är huggen med r-runan, och som *ʀ-runa* om alla är huggna med yr-runan. Draget kan avgöras på {sp(PAT['n'])} av stenarna; {PAT['cases']} av dem ({pc(PAT['cases'] / PAT['n'])} procent) har r för ʀ. Måttet bygger på Rundatas normalisering, som sätter ʀ efter ordets historia, och på translitteringen av vad ristaren högg. Det har inte kontrollerats mot en egen handläsning.
- **Ristaren.** Den ristare Rundata anger, med uppgift om attributionen är säker. Attributionerna bygger på utgåvorna i Sveriges runinskrifter och på Axelson (1993). Erik har tolv säkert attribuerade stenar där draget kan avgöras och tre osäkert attribuerade ({', '.join(UNC)}). Hans enda signerade sten, U 1165 vid Rotbrunna, räknas inte, eftersom en lucka i texten gör att orden inte kan paras ihop med normaliseringen; den har r-runa i båda de ord där ʀ väntas (*-ftir* och namnet *airikr*).
- **Datering** efter stenens ornamentikstil (Gräslund 2006). I avsnitt 5.4 räknas RAK, Fp, Pr1 och Pr2 som tidiga och Pr3–Pr5 som sena.

## 4. Metod

**4.1 Genomsökningen.** Tre mått, alla i R (R {DONE['r_version'].split()[2]}) med stenarnas läge i SWEREF 99 TM:

- *Morans I* (Moran 1950) med de {H['k']} närmaste stenarna som grannar: samlas draget alls geografiskt?
- *Getis-Ord Gi∗* (Getis & Ord 1992) för varje sten: ligger stenen i ett område där draget är vanligare bland grannarna än i landet? De lokala p-värdena justeras med Benjamini–Hochberg över stenarna.
- *Kulldorffs rumsliga scanstatistik* (Kulldorff 1997): alla cirklar runt varje sten som rymmer högst en tiondel av stenarna prövas, med landets andel som förväntat värde. Den cirkel där draget är mest överrepresenterat är klustret, och dess p-värde kommer från {H['nsim']} simuleringar där draget fördelas slumpvis över stenarna. Det minsta möjliga p-värdet är då 0,001. Klustrens p-värden justeras med Benjamini–Hochberg över de {N_TRAITS} dragen.

**4.2 Replikering i halvorna.** Materialet delades en gång, för alla projektets analyser, i två halvor socken för socken (hela socknar växelvis inom varje landskap). Andelen med draget inom och utanför klustret jämförs i var halva för sig med Fishers exakta test.

**4.3 Känslighetsanalyser.** Klustret prövas som jämförelse mellan stenar inom och utanför det, med logistisk regression: rå modell; modellen justerad för dateringsperiod; ristaren som slumpeffekt, så att en flitig ristares vanor inte räknas som en bygds; socknen som slumpeffekt; var halva för sig; och utan flyttade stenar, dels enligt Rundata, dels också enligt Runor 2020:s uppgift om ursprunglig plats. Två analyser som görs för andra samband görs inte här: modellen utan ett landskap i taget, eftersom klustret ligger inom ett landskap, och stenens läge som rumslig yta, eftersom jämförelsen själv är geografisk. Känslighetsanalyserna prövar klustret som det hittades, inte valet av det; för valet står scanstatistikens p-värde och halvorna. När p-värdena justeras för alla {N_SHOWN} samband som projektet redovisar används därför det största av känslighetsanalysernas p och scanstatistikens eget. Modellens antaganden prövas med simulerade residualer (DHARMa; Hartig 2022).

**4.4 Explorativa räkningar.** Andelen med draget inom och utanför klustret, uppdelat på ristare och dateringsperiod, jämförs med Fishers exakta test. De p-värdena är inte justerade.

**4.5 Avvikelser och tidigare versioner.** Ingen plan fanns, så inga avvikelser kan redovisas. En populär artikel om samma mönster publicerades den 13 oktober 2026 på en tidigare version av materialet. Efter en rättelse av vilka stenar som räknas som flyttade har klustret fått ett annat centrum (Holm i Vittinge i stället för Grop-Norrby i Vårfrukyrka) och en annan radie (30 i stället för 22 kilometer). Siffrorna i den här rapporten gäller.

## 5. Resultat

**5.1 Klustret.** Draget samlas tydligt geografiskt: Morans I = {d2(MO['i'])} (p < 0,001). Det mest extrema området har sin mitt i U 1172 vid Holm i Vittinge socken och en radie på {d1(CL['radius_km'])} kilometer. Där har {CL['cases']} av {CL['n']} stenar r för ʀ ({pc(CL['rate_in'])} procent), mot {pc(CL['rate_out'])} procent av stenarna i resten av landet: {d2(CL['rr'])} gånger så vanligt. Scanstatistikens p = 0,001, det lägsta värdet {H['nsim']} simuleringar kan ge; justerat för de {N_TRAITS} dragen q = 0,013. Av de {N_TRAITS} dragen är det det enda vars kluster klarar justeringen. Klustrets stenar ligger i {len(PAR)} socknar, flest i Simtuna ({PAR['Simtuna sn']}), Vårfrukyrka, Tillinge, Nysätra, Fröslunda och Jumkil (3 vardera). I halva A har {pc(HA['rate_in'])} procent av stenarna inom klustret draget mot {pc(HA['rate_out'])} utanför (oddskvot {round(HA['or'])}, {pfmt(HA['p'])}); i halva B {pc(HB['rate_in'])} mot {pc(HB['rate_out'])} procent (oddskvot {d1(HB['or'])}, {pfmt(HB['p'])}).

![Figur 1. ʀ skrivet med r-runan: stenarna och klustret]({FIGS['riket_sv']})
Figur 1. Varje punkt är en runsten där draget kan avgöras; rost: r för ʀ minst en gång, grå: bara yr-runan. Ringen är klustret. Källa: Rundata; kustlinjer och sjöar: Natural Earth.

![Figur 2. Klustret i västra Uppland]({FIGS['zoom_sv']})
Figur 2. Klustret i närbild. Svart ring runt en punkt: en av ristaren Eriks säkert attribuerade stenar. Källa: Rundata; kustlinjer och sjöar: Natural Earth.

**5.2 Känslighetsanalyserna** ({sp(P['n'])} stenar, {P['k']} med draget). Alla {ME['ladder']['tested']} håller:

- Rå modell: oddskvot {d1(RU['raw']['or'])} ({d1(RU['raw']['ci'][0])}–{d1(RU['raw']['ci'][1])}), {pfmt(RU['raw']['p'])}.
- Justerad för dateringsperiod: {d1(RU['adjusted']['or'])} ({d1(RU['adjusted']['ci'][0])}–{d1(RU['adjusted']['ci'][1])}), {pfmt(RU['adjusted']['p'])}.
- Ristaren som slumpeffekt ({RU['carver']['groups']} ristare och sockengrupper): {d1(RU['carver']['or'])} ({d1(RU['carver']['ci'][0])}–{d1(RU['carver']['ci'][1])}), {pfmt(RU['carver']['p'])}. Klustret är alltså inte bara en enda ristares vana.
- Socknen som slumpeffekt ({RU['parish']['groups']} socknar): {d1(RU['parish']['or'])} ({d1(RU['parish']['ci'][0])}–{d1(RU['parish']['ci'][1])}), {pfmt(RU['parish']['p'])}.
- Halva A ({RU['half_A']['n']} stenar): {d1(RU['half_A']['or'])}, {pfmt(RU['half_A']['p'])}. Halva B ({RU['half_B']['n']} stenar): {d1(RU['half_B']['or'])}, {pfmt(RU['half_B']['p'])}.
- Utan flyttade stenar enligt Rundata: {d1(RU['moved_rundata']['or'])}, {pfmt(RU['moved_rundata']['p'])}. Också utan stenar som Runor 2020 anger som flyttade ({RU['moved_runor']['n']} stenar kvar): {d1(RU['moved_runor']['or'])} ({d1(RU['moved_runor']['ci'][0])}–{d1(RU['moved_runor']['ci'][1])}), {pfmt(RU['moved_runor']['p'])}.
- Skillnaden i procentenheter i den justerade modellen: {pc(EF['share_hi'])} mot {pc(EF['share_lo'])} procent, {round(100 * EF['diff'])} enheter (troligen mellan {round(100 * EF['diff_ci'][0])} och {round(100 * EF['diff_ci'][1])}).
- Modellens antaganden: residualernas fördelning p = {d2(CK['uniformity_p'])}, överspridning p = {d2(CK['dispersion_p'])}, kvarvarande rumsligt mönster p = {d2(CK['spatial_p'])}. Inget avvikande.
- Justerat för alla {N_SHOWN} samband som projektet redovisar: q = {QG}. Sambandet är ett av {N_ALLRUNG} som håller i alla känslighetsanalyser.

**5.3 De heta stenarna.** Getis-Ord Gi∗ pekar ut {PAT['n_hot']} stenar i heta områden och inga i kalla. {len(HOT_UVS)} av dem ligger i och omkring klustret i Uppland och Västmanland. De övriga {len(HOT_VG)} ligger i Västergötland ({', '.join(HOT_VG)}), en andra grupp som är för liten för att scanstatistiken ska pröva den som eget kluster. Larsson (2002, kapitel 7) har noterat samma västgötska inskrifter, där prepositionen *æftiʀ* skrivs med r-runa. I övriga Uppland, utanför klustret, har {U_OUT[0]} av {U_OUT[1]} stenar draget ({pc(U_OUT[0] / U_OUT[1])} procent), i Södermanland {SO[0]} av {SO[1]} och i Västergötland {VG[0]} av {VG[1]}.

**5.4 Explorativt: ristaren Erik och tiden.**

- **Erik.** Alla Eriks {E_IN[1] + E_OUT[1]} säkert attribuerade stenar där draget kan avgöras har r för ʀ: {E_IN[1]} inom klustret och en utanför (U 774). Också de tre osäkert attribuerade har det. Alla är i stilen Fp.
- **De tidiga stenarna.** Inom klustret har alla {EA_IN[1]} tidiga stenar r för ʀ, och {EA_IN[1] - 2} av dem är attribuerade till Erik. Utanför klustret har {EA_OUT[0]} av {EA_OUT[1]} tidiga stenar draget ({pc(EA_OUT[0] / EA_OUT[1])} procent). I Uppland utanför klustret har {FP_U_OUT[0]} av {FP_U_OUT[1]} stenar i stilen Fp det.
- **Klustret utan Erik.** Utan alla stenar som attribuerats till Erik har {NE_IN[0]} av {NE_IN[1]} stenar inom klustret draget ({pc(NE_IN[0] / NE_IN[1])} procent), mot {ALL_OUT[0]} av {ALL_OUT[1]} utanför ({pc(ALL_OUT[0] / ALL_OUT[1])} procent), {pfmt(P_NE)}.
- **De senare stenarna.** Bland stenarna i stilgrupperna Pr3–Pr5 har {LA_IN[0]} av {LA_IN[1]} inom klustret draget ({pc(LA_IN[0] / LA_IN[1])} procent), mot {LA_U_OUT[0]} av {LA_U_OUT[1]} i övriga Uppland ({pc(LA_U_OUT[0] / LA_U_OUT[1])} procent), {pfmt(P_LATE)}.
- **Balle**, som ristade i bygden en generation efter Erik, har r för ʀ på {B_IN[0]} av {B_IN[1]} stenar inom klustret och {B_OUT[0]} av {B_OUT[1]} utanför ({pfmt(P_B)}); räknas också de osäkert attribuerade stenarna med blir det {BA_IN[0]} av {BA_IN[1]} mot {BA_OUT[0]} av {BA_OUT[1]} ({pfmt(P_BA)}). Skillnaden går åt det håll ett bygdemål förutsäger, men stenarna är för få för att den ska vara säker.
- **Åsmund**, som ristade på många håll i Uppland, skrev yr-runan på alla sina {A_IN[1] + A_OUT[1]} säkert attribuerade stenar där draget kan avgöras, också de {A_IN[1]} som står inom klustret.

## 6. Diskussion

**Vad fyndet säger.** Västra Uppland är det område i Sverige där ʀ oftast skrevs med r-runan, och det är inte en följd av att stenarna där är tidiga eller av att en enda ristare ristade många av dem: klustret står kvar med dateringsperiod och ristare konstanta, i var halva för sig och utan flyttade stenar. I den tidiga generationen bärs det nästan helt av Erik. Att det står kvar utan hans stenar, och att de senare stenarna i bygden skriver r fyra gånger så ofta som i övriga Uppland, visar att stavningen inte försvann med honom.

**Mot tidigare forskning.** Resultatet bekräftar och preciserar Larssons (2002) iakttagelse att Uppland och Västergötland skiljer ut sig. Inom Uppland pekar det ut ett bestämt område, och det återfinner hans västgötska grupp utan att ha letat efter den. Det bekräftar också Stilles (1999) iakttagelse om Erik.

**Där vi går emot tidigare forskning.** Stille läser Eriks r som tecken på att r och ʀ hade fallit samman i hans tal, och Larsson menar att r-runans frammarsch i stort speglar en språkförändring, inte en ortografisk reform (avsnitt 7.3). Larssons huvudskäl är att ristarna samtidigt betecknar palatalisering och använder s-runan för ʀ, vilket rimligen följer uttalet. Det är ett argument om runskriften i stort. Det visar att många ristare skrev efter örat, men inte att varje ristare gjorde det, och det förklarar inte varför en enda bygd skiljer sig så skarpt från resten av landet.

För västra Uppland föreslår vi en annan förklaring: att r för ʀ där var en skrivtradition som började med Erik och fördes vidare av ristarna i bygden. Tre iakttagelser stöder den.

1. Erik skrev r utan ett enda undantag, på alla femton stenar, också på den utanför bygden. Larsson tar, med Lena Peterson, ristarnas vacklan mellan runorna som tecken på en ljudförändring som pågår (avsnitt 7.3). Erik vacklar inte alls; han skriver som efter en regel.
2. Åsmund skrev yr-runa på alla sina tretton stenar, också de tre inom klustret. Det talar emot att platsen eller beställarna avgjorde stavningen. Den följde ristaren.
3. Stavningen lever kvar i samma bygd efter Erik, fyra gånger så vanlig bland de senare stenarna som i övriga Uppland, och klustret står kvar när ristaren hålls konstant.

Hypotesen är inte bevisad, och Stilles och Larssons förklaring är inte utesluten. Talen är små: Erik har en sten utanför bygden och Åsmund tre inom den. Talade Erik och ristarna efter honom själva ett mål där ljuden fallit samman, ger det samma mönster som en skrivtradition. Balle pekar dessutom åt andra hållet: han skrev r oftare inom klustret än utanför ({B_IN[0]} av {B_IN[1]} mot {B_OUT[0]} av {B_OUT[1]}, {pfmt(P_B)}; med de osäkert attribuerade stenarna {BA_IN[0]} av {BA_IN[1]} mot {BA_OUT[0]} av {BA_OUT[1]}, {pfmt(P_BA)}). Det som skiljer förklaringarna åt är om de senare r-stenarna i bygden står i Eriks tradition – samma ornamentik, samma formler, samma stavning i övrigt – eller bara i samma bygd. Det är nästa prov.

**Svagheter, i ordning efter vikt.**

1. **Fyndet är upptäckt, inte förregistrerat.** Klustrets gräns är vald av datan. Scanstatistiken, justeringen och halvorna tar hänsyn till det, men radien och centrum ska läsas som ungefärliga.
2. **Erik bär den tidiga delen.** Tretton av femton tidiga stenar i klustret är attribuerade till honom, och attributionerna bygger på stil; flera av dem har ifrågasatts (Larsson 2002, avsnitt 7.2.3). Klustret står kvar utan honom, men med mindre marginal.
3. **Draget avgörs på få ord per sten.** Många stenar har bara en eller två ändelser med ʀ, oftast i *æftiʀ*. Ett enda r räcker för att stenen räknas som r för ʀ.
4. **Måttet är inte handkontrollerat.** Det bygger på Rundatas translitterering och normalisering. En felläst yr-runa eller en normalisering som sätter ʀ där andra forskare inte gör det skulle flytta enskilda stenar.

**Vad som skulle fälla fyndet.** En handläsning som visar att r-formerna inom klustret oftare är osäkra läsningar än utanför, eller nya fynd i bygden med yr-runa.

## 7. Slutsats

Inom {d1(CL['radius_km'])} kilometer från Holm i Vittinge har {pc(CL['rate_in'])} procent av runstenarna r för ʀ, mot {pc(CL['rate_out'])} procent i resten av landet, och samlingen tål varje känslighetsanalys. Den börjar med ristaren Erik men står kvar utan honom och lever vidare bland de senare stenarna i bygden. Stavningen följde ristaren snarare än platsen, och vi föreslår att klustret är en skrivtradition. Att det i stället speglar ristarnas eget uttal, som Stille och Larsson menar, kan runstenarna ännu inte utesluta; provet är om de senare r-stenarna står i Eriks tradition eller bara i hans bygd.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 31 oktober 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod och alla resultatfiler finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Draget: `src/language_profile.py` (r för ʀ) och `src/pattern_map.py`.
- Genomsökningen: `r/hotspots.R`. Känslighetsanalyserna: `r/robustness.R` och `src/robustness.py` (metodbeskrivning i `METHODS.md`, avsnitt 1f och 1v). Resultaten sparas under materialets version `{FP}`.
- Figurerna: `utdata/rapporter/figurer/karta_r_for_R.R`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_r_for_R.py`, som räknar de explorativa siffrorna, läser resten ur resultatfilerna och stannar om något inte stämmer.
- I Vitki visas klustret under Statistik, Geografi, med känslighetsanalyserna steg för steg, och på Karta under Mönster. Populär framställning: [Erik skrev r – och bygden skrev efter](/artiklar/erik-skrev-r-och-bygden-skrev-efter), med äldre siffror.

## Referenser

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), s. 289–300.
- Getis, A. & Ord, J. K. 1992. The analysis of spatial association by use of distance statistics. *Geographical Analysis* 24 (3), s. 189–206.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R-paket.
- Kulldorff, M. 1997. A spatial scan statistic. *Communications in Statistics – Theory and Methods* 26 (6), s. 1481–1496.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter*. Runrön 17. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Moran, P. A. P. 1950. Notes on continuous stochastic phenomena. *Biometrika* 37 (1–2), s. 17–23.
- Riksantikvarieämbetet. *Runor* (runinskriftsregister), uttag 2020.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Institutionen för nordiska språk, Uppsala universitet.

:::box Det viktigaste i korthet
- I västra Uppland, kring Simtuna, Vårfrukyrka och Tillinge, skrevs det gamla ljudet ʀ med vanlig r-runa långt oftare än någon annanstans i Sverige.
- Ristaren Erik skrev så på varje sten, men bygden fortsatte efter honom – samlingen är inte en enda mans vana.
- Vår hypotes är att det var en skrivtradition som fördes vidare, inte ett uttal. Tidigare forskning har läst det som uttal, och stenarna kan ännu inte avgöra vem som har rätt.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Report version {REPORT_VERSION}, {TODAY}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, yr-rune, ʀ, r, Uppland, carvers, spatial statistics. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** Runic Swedish had two r-sounds, r and ʀ, each with its own rune. During the eleventh century ʀ is written ever more often with the ordinary r-rune, and earlier research has shown that this varies between provinces and carvers. The question here is whether the spelling clusters geographically more than chance would give, where, and whether the cluster withstands a fixed series of sensitivity analyses.
**Material.** {en_n(PAT['n'])} Viking-Age runestones in the Swedish provinces where it can be decided how ʀ is written and which stand at their original site, from the Scandinavian Runic-text Database (Rundata).
**Method.** Spatial autocorrelation (Moran's I), local hot spots (Getis-Ord Gi∗) and Kulldorff's spatial scan statistic with 999 Monte Carlo simulations, adjusted for the {N_TRAITS} spelling and content traits scanned; internal replication in two pre-defined halves of the material; eight sensitivity analyses; adjustment for all {N_SHOWN} associations the project reports.
**Results.** Within {CL['radius_km']:.1f} kilometres of Holm in Vittinge parish, {CL['cases']} of {CL['n']} stones have r for ʀ ({pc(CL['rate_in'])} percent), against {pc(CL['rate_out'])} percent in the rest of the country; scan p = 0.001, adjusted for the {N_TRAITS} traits q = 0.013. Same direction in both halves ({pc(HA['rate_in'])} against {pc(HA['rate_out'])} and {pc(HB['rate_in'])} against {pc(HB['rate_out'])} percent), every sensitivity analysis holds, and adjusted for all associations q = {QGe}. Exploratory: the carver Erik wrote r on all his {E_IN[1] + E_OUT[1]} securely attributed stones, but the cluster remains without them ({NE_IN[0]} of {NE_IN[1]} stones), and among the later stones of the district the spelling is four times as common as in the rest of Uppland.
**Conclusion.** Western Uppland is the area of Sweden where ʀ was most often written with r. The spelling followed the carver rather than the place, and we propose that the cluster is a writing tradition that began with Erik and was passed on. Earlier research has read Erik's r as pronunciation; the material cannot yet rule that out.

## 1. Introduction

Runic Swedish had two r-sounds. One, r, is the ordinary one. The other, ʀ, goes back to an older *z* and stands, among other places, in endings such as *æftiʀ* ’after’, *þæiʀ* ’they’ and *stæinaʀ* ’stones’. It had a rune of its own, the yr-rune ᛦ. In time the sounds merged, and in the later Viking-Age inscriptions ʀ is written ever more often with the ordinary r-rune.

Patrik Larsson (2002), in his dissertation on the yr-rune, went through how older ʀ is written in all Scandinavian runic inscriptions. He shows that the share of spellings with the r-rune after a vowel is markedly higher in Uppland, Västergötland and on Gotland (18–28 percent) than in other provinces with many instances (section 7.2.2), and that the Uppland group in the Fp style consists largely of inscriptions by the carver Erik, who consistently writes the r-rune for ʀ (section 7.2.3). Per Stille (1999, p. 206), in his study of the carvers of Fjädrundaland, observed the same of Erik and concluded that r and ʀ had merged in his speech. Larsson places Erik among the carvers who seem to have kept no distinction between the sounds (section 7.2.1) and argues that the growing use of the r-rune on the whole reflects an ongoing language change, not an orthographic reform (section 7.3).

What that literature lacks is a measure of whether the spelling clusters geographically more than chance would give, independently of provincial boundaries, and whether such a cluster remains when the age of the stones and the habits of individual carvers are held constant. The aim of this study is to measure that, and to test what the measurement says about the explanation earlier research has given. Pronunciation is not tested directly, but section 6 takes a position on what the pattern says about it.

## 2. Pre-registration: what was fixed in advance and what is exploratory

No analysis plan was locked for this question before the results were known. The finding is therefore not pre-registered, and it should be read as a discovery in a systematic search.

The search was a general method applied at once to {N_TRAITS} traits in the spelling and content of the runestones, r for ʀ among them. The method, its limits (circles holding at most a tenth of the stones, 999 simulations, adjustment across the traits) and the division of the material into two halves were fixed in the program code before the search was run, and they were the same for every trait. No hypothesis about r for ʀ or about western Uppland existed before the search.

Four things nonetheless keep the finding from being an artefact of our choosing it:

1. The scan statistic's p-value takes into account every circle that was tested; it is the probability that the most extreme area would be as extreme if the spelling were evenly distributed.
2. The p-values are adjusted for the {N_TRAITS} traits scanned, and in addition for all {N_SHOWN} associations the project reports.
3. The halves were set independently of the patterns, and the cluster must hold in each half on its own.
4. The same sensitivity analyses as for every other association.

The analyses in sections 5.1–5.3 are those the method prescribes for every trait. Section 5.4 on the carver Erik and on time is exploratory: it was computed after the cluster was known and is reported descriptively, with p-values that are not adjusted for the questions having been chosen afterwards.

## 3. Material

- **Source.** The Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University: transliteration, normalisation, province, parish, site, carver and style group for each inscription. The material was frozen for the analysis on 29 October 2026.
- **The stones.** Viking-Age runestones in the Swedish provinces. Runestones only; other objects with runes are not included. Skåne and Blekinge, Danish in the Viking Age, are counted as Denmark in Rundata and are not included. Of the stones, {en_n(H['n_stones'])} have a known location and stand at their original site; stones moved according to Rundata or to the Swedish National Heritage Board's register Runor (2020) are not counted, since their location does not say where they were carved.
- **The trait.** For each stone, the words whose normalised form ends in ʀ and whose carved form ends in the r- or the yr-rune are taken. The stone counts as *r for ʀ* if at least one such ending is carved with the r-rune, and as *ʀ-rune* if all are carved with the yr-rune. The trait can be decided on {en_n(PAT['n'])} of the stones; {PAT['cases']} of them ({pc(PAT['cases'] / PAT['n'])} percent) have r for ʀ. The measure rests on Rundata's normalisation, which places ʀ by the word's history, and on the transliteration of what the carver cut. It has not been checked against a reading of our own.
- **The carver.** The carver Rundata gives, with a note of whether the attribution is secure. The attributions rest on the editions in Sveriges runinskrifter and on Axelson (1993). Erik has twelve securely attributed stones where the trait can be decided and three uncertainly attributed ones ({', '.join(UNC)}). His only signed stone, U 1165 at Rotbrunna, is not counted, since a gap in the text keeps its words from being paired with the normalisation; it has the r-rune in both the words where ʀ is expected (*-ftir* and the name *airikr*).
- **Dating** by the stone's ornamental style (Gräslund 2006). In section 5.4, RAK, Fp, Pr1 and Pr2 count as early and Pr3–Pr5 as late.

## 4. Method

**4.1 The search.** Three measures, all in R (R {DONE['r_version'].split()[2]}) with the stones' locations in SWEREF 99 TM:

- *Moran's I* (Moran 1950) with the {H['k']} nearest stones as neighbours: does the trait cluster geographically at all?
- *Getis-Ord Gi∗* (Getis & Ord 1992) for each stone: does the stone lie in an area where the trait is more common among the neighbours than in the country? The local p-values are adjusted with Benjamini–Hochberg across the stones.
- *Kulldorff's spatial scan statistic* (Kulldorff 1997): every circle around every stone holding at most a tenth of the stones is tested, with the national share as the expected value. The circle where the trait is most over-represented is the cluster, and its p-value comes from {H['nsim']} simulations in which the trait is distributed at random over the stones. The smallest possible p-value is then 0.001. The clusters' p-values are adjusted with Benjamini–Hochberg across the {N_TRAITS} traits.

**4.2 Replication in the halves.** The material was divided once, for all the project's analyses, into two halves parish by parish (whole parishes dealt alternately within each province). The share with the trait within and outside the cluster is compared in each half on its own with Fisher's exact test.

**4.3 Sensitivity analyses.** The cluster is tested as a comparison between stones within and outside it, with logistic regression: the raw model; the model adjusted for dating period; the carver as a random effect, so that a prolific carver's habits are not counted as a district's; the parish as a random effect; each half on its own; and without moved stones, both according to Rundata and also according to Runor 2020's record of the original site. Two analyses made for other associations are not made here: the model without one province at a time, since the cluster lies within one province, and the stone's location as a spatial surface, since the comparison itself is geographic. The sensitivity analyses test the cluster as it was found, not the choice of it; for the choice, the scan statistic's p-value and the halves stand. When the p-values are adjusted for all {N_SHOWN} associations the project reports, the larger of the sensitivity analyses' p and the scan statistic's own is therefore used. The model's assumptions are checked with simulated residuals (DHARMa; Hartig 2022).

**4.4 Exploratory counts.** The share with the trait within and outside the cluster, split by carver and dating period, is compared with Fisher's exact test. Those p-values are not adjusted.

**4.5 Deviations and earlier versions.** No plan existed, so no deviations can be reported. A popular article on the same pattern was published on 13 October 2026 on an earlier version of the material. After a correction of which stones count as moved, the cluster has a different centre (Holm in Vittinge instead of Grop-Norrby in Vårfrukyrka) and a different radius (30 instead of 22 kilometres). The figures in this report apply.

## 5. Results

**5.1 The cluster.** The trait clusters clearly: Moran's I = {MO['i']:.2f} (p < 0.001). The most extreme area has its centre at U 1172 at Holm in Vittinge parish and a radius of {CL['radius_km']:.1f} kilometres. There {CL['cases']} of {CL['n']} stones have r for ʀ ({pc(CL['rate_in'])} percent), against {pc(CL['rate_out'])} percent of the stones in the rest of the country: {CL['rr']:.2f} times as common. Scan p = 0.001, the lowest value {H['nsim']} simulations can give; adjusted for the {N_TRAITS} traits q = 0.013. Of the {N_TRAITS} traits it is the only one whose cluster passes the adjustment. The cluster's stones lie in {len(PAR)} parishes, most in Simtuna ({PAR['Simtuna sn']}), Vårfrukyrka, Tillinge, Nysätra, Fröslunda and Jumkil (3 each). In half A, {pc(HA['rate_in'])} percent of the stones within the cluster have the trait against {pc(HA['rate_out'])} outside (odds ratio {round(HA['or'])}, {pfmt(HA['p'], True)}); in half B {pc(HB['rate_in'])} against {pc(HB['rate_out'])} percent (odds ratio {HB['or']:.1f}, {pfmt(HB['p'], True)}).

![Figure 1. ʀ written with the r-rune: the stones and the cluster]({FIGS['riket_en']})
Figure 1. Each point is a runestone where the trait can be decided; rust: r for ʀ at least once, grey: the yr-rune only. The ring is the cluster. Source: Rundata; coastlines and lakes: Natural Earth.

![Figure 2. The cluster in western Uppland]({FIGS['zoom_en']})
Figure 2. The cluster close up. Black ring around a point: one of the carver Erik's securely attributed stones. Source: Rundata; coastlines and lakes: Natural Earth.

**5.2 The sensitivity analyses** ({en_n(P['n'])} stones, {P['k']} with the trait). All {ME['ladder']['tested']} hold:

- Raw model: odds ratio {RU['raw']['or']:.1f} ({RU['raw']['ci'][0]:.1f}–{RU['raw']['ci'][1]:.1f}), {pfmt(RU['raw']['p'], True)}.
- Adjusted for dating period: {RU['adjusted']['or']:.1f} ({RU['adjusted']['ci'][0]:.1f}–{RU['adjusted']['ci'][1]:.1f}), {pfmt(RU['adjusted']['p'], True)}.
- Carver as a random effect ({RU['carver']['groups']} carvers and parish groups): {RU['carver']['or']:.1f} ({RU['carver']['ci'][0]:.1f}–{RU['carver']['ci'][1]:.1f}), {pfmt(RU['carver']['p'], True)}. The cluster is thus not merely one carver's habit.
- Parish as a random effect ({RU['parish']['groups']} parishes): {RU['parish']['or']:.1f} ({RU['parish']['ci'][0]:.1f}–{RU['parish']['ci'][1]:.1f}), {pfmt(RU['parish']['p'], True)}.
- Half A ({RU['half_A']['n']} stones): {RU['half_A']['or']:.1f}, {pfmt(RU['half_A']['p'], True)}. Half B ({RU['half_B']['n']} stones): {RU['half_B']['or']:.1f}, {pfmt(RU['half_B']['p'], True)}.
- Without moved stones according to Rundata: {RU['moved_rundata']['or']:.1f}, {pfmt(RU['moved_rundata']['p'], True)}. Also without stones that Runor 2020 records as moved ({RU['moved_runor']['n']} stones remain): {RU['moved_runor']['or']:.1f} ({RU['moved_runor']['ci'][0]:.1f}–{RU['moved_runor']['ci'][1]:.1f}), {pfmt(RU['moved_runor']['p'], True)}.
- The difference in percentage points in the adjusted model: {pc(EF['share_hi'])} against {pc(EF['share_lo'])} percent, {round(100 * EF['diff'])} points (probably between {round(100 * EF['diff_ci'][0])} and {round(100 * EF['diff_ci'][1])}).
- The model's assumptions: residual distribution p = {CK['uniformity_p']:.2f}, overdispersion p = {CK['dispersion_p']:.2f}, remaining spatial pattern p = {CK['spatial_p']:.2f}. Nothing amiss.
- Adjusted for all {N_SHOWN} associations the project reports: q = {QGe}. The association is one of {N_ALLRUNG} that hold in every sensitivity analysis.

**5.3 The hot stones.** Getis-Ord Gi∗ singles out {PAT['n_hot']} stones in hot areas and none in cold ones. {len(HOT_UVS)} of them lie in and around the cluster in Uppland and Västmanland. The other {len(HOT_VG)} lie in Västergötland ({', '.join(HOT_VG)}), a second group too small for the scan statistic to test as a cluster of its own. Larsson (2002, chapter 7) noted the same inscriptions in Västergötland, where the preposition *æftiʀ* is written with the r-rune. In the rest of Uppland, outside the cluster, {U_OUT[0]} of {U_OUT[1]} stones have the trait ({pc(U_OUT[0] / U_OUT[1])} percent), in Södermanland {SO[0]} of {SO[1]} and in Västergötland {VG[0]} of {VG[1]}.

**5.4 Exploratory: the carver Erik and time.**

- **Erik.** All Erik's {E_IN[1] + E_OUT[1]} securely attributed stones where the trait can be decided have r for ʀ: {E_IN[1]} within the cluster and one outside (U 774). The three uncertainly attributed ones have it too. All are in the Fp style.
- **The early stones.** Within the cluster all {EA_IN[1]} early stones have r for ʀ, and {EA_IN[1] - 2} of them are attributed to Erik. Outside the cluster {EA_OUT[0]} of {EA_OUT[1]} early stones have the trait ({pc(EA_OUT[0] / EA_OUT[1])} percent). In Uppland outside the cluster {FP_U_OUT[0]} of {FP_U_OUT[1]} stones in the Fp style have it.
- **The cluster without Erik.** Without every stone attributed to Erik, {NE_IN[0]} of {NE_IN[1]} stones within the cluster have the trait ({pc(NE_IN[0] / NE_IN[1])} percent), against {ALL_OUT[0]} of {ALL_OUT[1]} outside ({pc(ALL_OUT[0] / ALL_OUT[1])} percent), {pfmt(P_NE, True)}.
- **The later stones.** Among the stones in the style groups Pr3–Pr5, {LA_IN[0]} of {LA_IN[1]} within the cluster have the trait ({pc(LA_IN[0] / LA_IN[1])} percent), against {LA_U_OUT[0]} of {LA_U_OUT[1]} in the rest of Uppland ({pc(LA_U_OUT[0] / LA_U_OUT[1])} percent), {pfmt(P_LATE, True)}.
- **Balli**, who carved in the district a generation after Erik, has r for ʀ on {B_IN[0]} of {B_IN[1]} stones within the cluster and {B_OUT[0]} of {B_OUT[1]} outside ({pfmt(P_B, True)}); counting also the uncertainly attributed stones it is {BA_IN[0]} of {BA_IN[1]} against {BA_OUT[0]} of {BA_OUT[1]} ({pfmt(P_BA, True)}). The difference goes the way a local speech predicts, but the stones are too few for it to be certain.
- **Åsmund**, who carved in many parts of Uppland, wrote the yr-rune on all his {A_IN[1] + A_OUT[1]} securely attributed stones where the trait can be decided, including the {A_IN[1]} that stand within the cluster.

## 6. Discussion

**What the finding says.** Western Uppland is the area of Sweden where ʀ was most often written with the r-rune, and that is not because the stones there are early or because a single carver carved many of them: the cluster remains with dating period and carver constant, in each half and without moved stones. In the early generation it is carried almost wholly by Erik. That it remains without his stones, and that the later stones of the district write r four times as often as the rest of Uppland, shows that the spelling did not disappear with him.

**Against earlier research.** The result confirms and sharpens Larsson's (2002) observation that Uppland and Västergötland stand out. Within Uppland it singles out a definite area, and it recovers his group in Västergötland without having looked for it. It also confirms Stille's (1999) observation about Erik.

**Where we depart from earlier research.** Stille reads Erik's r as a sign that r and ʀ had merged in his speech, and Larsson holds that the advance of the r-rune on the whole reflects a language change, not an orthographic reform (section 7.3). Larsson's main reason is that the carvers at the same time mark palatalisation and use the s-rune for ʀ, which must reasonably follow pronunciation. That is an argument about runic writing at large. It shows that many carvers wrote by ear, but not that every carver did, and it does not explain why a single district differs so sharply from the rest of the country.

For western Uppland we propose another explanation: that r for ʀ there was a writing tradition that began with Erik and was passed on by the carvers of the district. Three observations support it.

1. Erik wrote r without a single exception, on all fifteen stones, including the one outside the district. Larsson, with Lena Peterson, takes the carvers' wavering between the runes as a sign of a sound change in progress (section 7.3). Erik does not waver at all; he writes as if by a rule.
2. Åsmund wrote the yr-rune on all his thirteen stones, including the three within the cluster. That speaks against the place or the patrons deciding the spelling. It followed the carver.
3. The spelling lives on in the same district after Erik, four times as common among the later stones as in the rest of Uppland, and the cluster remains when the carver is held constant.

The hypothesis is not proven, and Stille's and Larsson's explanation is not ruled out. The numbers are small: Erik has one stone outside the district and Åsmund three within it. If Erik and the carvers after him themselves spoke a variety in which the sounds had merged, that gives the same pattern as a writing tradition. Balli, moreover, points the other way: he wrote r more often within the cluster than outside it ({B_IN[0]} of {B_IN[1]} against {B_OUT[0]} of {B_OUT[1]}, {pfmt(P_B, True)}; with the uncertainly attributed stones {BA_IN[0]} of {BA_IN[1]} against {BA_OUT[0]} of {BA_OUT[1]}, {pfmt(P_BA, True)}). What separates the explanations is whether the later r-stones of the district stand in Erik's tradition – the same ornament, the same formulas, the same spelling otherwise – or merely in the same district. That is the next test.

**Weaknesses, in order of weight.**

1. **The finding is discovered, not pre-registered.** The cluster's boundary is chosen by the data. The scan statistic, the adjustment and the halves take that into account, but the radius and centre should be read as approximate.
2. **Erik carries the early part.** Thirteen of fifteen early stones in the cluster are attributed to him, and the attributions rest on style; several have been questioned (Larsson 2002, section 7.2.3). The cluster remains without him, but with a smaller margin.
3. **The trait is decided on few words per stone.** Many stones have only one or two endings with ʀ, most often in *æftiʀ*. A single r is enough for the stone to count as r for ʀ.
4. **The measure is not checked by hand.** It rests on Rundata's transliteration and normalisation. A misread yr-rune, or a normalisation placing ʀ where other scholars do not, would move individual stones.

**What would overturn the finding.** A hand reading showing that the r-forms within the cluster are more often uncertain readings than outside it, or new finds in the district with the yr-rune.

## 7. Conclusion

Within {CL['radius_km']:.1f} kilometres of Holm in Vittinge, {pc(CL['rate_in'])} percent of the runestones have r for ʀ, against {pc(CL['rate_out'])} percent in the rest of the country, and the cluster withstands every sensitivity analysis. It begins with the carver Erik but remains without him and lives on among the later stones of the district. The spelling followed the carver rather than the place, and we propose that the cluster is a writing tradition. That it instead reflects the carvers' own pronunciation, as Stille and Larsson hold, the runestones cannot yet rule out; the test is whether the later r-stones stand in Erik's tradition or merely in his district.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 31 October 2026. No release with a DOI exists yet; when one is made, the report will refer to it. All code and result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The trait: `src/language_profile.py` (r for ʀ) and `src/pattern_map.py`.
- The search: `r/hotspots.R`. The sensitivity analyses: `r/robustness.R` and `src/robustness.py` (method description in `METHODS.md`, sections 1f and 1v). The results are saved under the material's version `{FP}`.
- The figures: `utdata/rapporter/figurer/karta_r_for_R.R`.
- The report is built by `utdata/blogg/build/build_rapport_r_for_R.py`, which computes the exploratory figures, reads the rest from the result files and stops if anything disagrees.
- In Vitki the cluster is shown under Statistics, Geography, with the sensitivity analyses step by step, and on the Map under Patterns. Popular account: [Erik wrote r – and the district followed](/en/artiklar/erik-skrev-r-och-bygden-skrev-efter), with older figures.

## References

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), pp. 289–300.
- Getis, A. & Ord, J. K. 1992. The analysis of spatial association by use of distance statistics. *Geographical Analysis* 24 (3), pp. 189–206.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R package.
- Kulldorff, M. 1997. A spatial scan statistic. *Communications in Statistics – Theory and Methods* 26 (6), pp. 1481–1496.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter*. Runrön 17. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Moran, P. A. P. 1950. Notes on continuous stochastic phenomena. *Biometrika* 37 (1–2), pp. 17–23.
- Swedish National Heritage Board (Riksantikvarieämbetet). *Runor* (register of runic inscriptions), 2020 extract.
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Department of Scandinavian Languages, Uppsala University.

:::box The essentials
- In western Uppland, around Simtuna, Vårfrukyrka and Tillinge, the old sound ʀ was written with the ordinary r-rune far more often than anywhere else in Sweden.
- The carver Erik wrote so on every stone, but the district carried on after him – the cluster is not one man's habit.
- Our hypothesis is that it was a writing tradition that was passed on, not a pronunciation. Earlier research has read it as pronunciation, and the stones cannot yet decide who is right.
:::
"""

JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)  # the locked template: no internal names before Data och kod
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Språk och stavning", "Geografi", "Ristare"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_r_for_R.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body_en.split()), "words")

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
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Rapport|r_for_R", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
