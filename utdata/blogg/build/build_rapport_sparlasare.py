"""Forskningsrapport, metodrapport (låst mall utdata/rapporter/MALL.md, version 4; Metodrapport, delvis prövad):
"Skanningen som ledtråd: med 3D-spåren fyller språkmodellen i 60 procent av de dolda orden rätt i stället för 54, och
omflyttade spår gör det sämre" (sv + en). Spårläsaren (utdata/sparlasare/, led E–G) och känslighetskontrollen utan
Sö 113 (utan_so113.py). Alla siffror asserteras mot filerna.
    ../../../.venv/bin/python build_rapport_sparlasare.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

APP_VERSION = json.load(open(os.path.join(ROOT, "web", "package.json")))["version"]
assert APP_VERSION == "3.0.0"
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 1
TODAY = "2026-10-31"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = "spårläsaren byggdes och ställdes in på Sö 113 2026-10-17; det skarpa provet kördes 2026-10-17; provet på verkliga luckor kördes 2026-10-17; provet räknades om utan Sö 113 2026-10-31"
TL_EN = "the trace reader was built and tuned on Sö 113 2026-10-17; the sharp test was run 2026-10-17; the test on real gaps was run 2026-10-17; the test was recomputed without Sö 113 2026-10-31"
SD = os.path.join(ROOT, "utdata", "sparlasare")
F = json.load(open(os.path.join(SD, "led_f_summering.json"), encoding="utf-8"))
X = json.load(open(os.path.join(SD, "utan_so113.json"), encoding="utf-8"))
E = json.load(open(os.path.join(SD, "led_e_perm.json"), encoding="utf-8"))
G = {s["sig"]: s for s in json.load(open(os.path.join(SD, "led_g.json"), encoding="utf-8"))}
d1 = lambda x: f"{100 * x:.1f}".replace(".", ",")  # noqa: E731
e1 = lambda x: f"{100 * x:.1f}"  # noqa: E731
d3 = lambda x: f"{x:.3f}".replace(".", ",")  # noqa: E731


def pexp(p, en=False):
    m, e = f"{p:.1e}".split("e")
    m = m if en else m.replace(".", ",")
    return f"p = {m} · 10{str(int(e)).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))}"


def pf(p, en=False):
    if p < 0.001:
        return pexp(p, en)
    s = f"{p:.3f}" if p < 0.1 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the sharp test (led F) -------------------------------------------------------------------------------------------
A = F["all"]
assert (A["n"], A["stones"], len(F["stones"])) == (157, 17, 17) and "Sö 113" in F["stones"]
MN = A["means"]
assert [d1(MN[c]["word_ok"]) for c in ("utan", "skanner", "omflyttad")] == ["53,5", "59,9", "52,9"]
assert [f"{MN[c]['p_truth']:.3f}" for c in ("utan", "skanner", "omflyttad")] == ["0.379", "0.414", "0.365"]
SU, SO, OU = A["skanner_vs_utan"], A["skanner_vs_omflyttad"], A["omflyttad_vs_utan"]
assert 3.7e-6 < SU["p"] < 3.8e-6 and 2.0e-8 < SO["p"] < 2.1e-8 and 0.0087 < OU["p"] < 0.0089 and OU["mean_diff"] < 0
assert (SU["n_changed"], SU["n_plus"]) == (113, 74)
# the recomputation (same test) reproduces the summary exactly
XA, XU = X["alla"], X["utan_So_113"]
assert abs(XA["skanner_vs_utan"]["p"] - SU["p"]) < 1e-12 and XA["n"] == A["n"]
assert (XU["n"], XU["stones"]) == (145, 16)
assert [d1(XU["means"][c]["word_ok"]) for c in ("utan", "skanner", "omflyttad")] == ["57,2", "63,4", "55,2"]
assert 5.8e-6 < XU["skanner_vs_utan"]["p"] < 6.0e-6 and XU["skanner_vs_omflyttad"]["p"] < 2e-8

# ---- the earlier step on undamaged runes (led E) ----------------------------------------------------------------------
assert (E["n_shuffles"], E["p_value"], E["p_value_top1"]) == (200, 0.01, 0.015)
assert (f"{E['pooled_mean_p']:.3f}", f"{E['pooled_null'][0]:.3f}", d1(E["pooled_top1"]), d1(E["pooled_top1_null"][0])) == ("0.077", "0.066", "19,3", "13,8")

# ---- real gaps end to end (led G) -------------------------------------------------------------------------------------
assert len(G) == 5 and set(G) == {"Sö 162", "Sö 206", "Sö 211", "Sö 360", "Sö 45"}
assert (G["Sö 162"]["utan"][0]["word"], G["Sö 162"]["skanner"][0]["word"]) == ("stæin", "staf")
assert (G["Sö 206"]["utan"][1]["word"], G["Sö 206"]["skanner"][1]["word"], G["Sö 206"]["utan"][1]["rundata"]) == ("karl", "kumbl", "G[uðl]aug")
assert G["Sö 211"]["skanner"][0]["word"] == "stæin" and G["Sö 45"]["skanner"][0]["word"] == "gæiRfastr"
N_GAP_WORDS = sum(len(s["utan"]) for s in G.values())
assert N_GAP_WORDS == 7

SLUG = "skanningen-som-ledtrad"
title = "Skanningen som ledtråd: med 3D-spåren fyller språkmodellen i 60 procent av de dolda orden rätt i stället för 54, och omflyttade spår gör det sämre"
title_en = "The scan as a clue: with the 3D traces the language model fills in 60 percent of the hidden words correctly instead of 54, and shuffled traces make it worse"
summary = ("Metodrapport. En spårläsare läser i en 3D-skanning vilka runor en skadad runa kan vara, och en språkmodell väljer bland "
           "dem. När hela ord doldes på 17 skannade runstenar blev 59,9 procent rätt med spåren mot 53,5 procent utan dem, och "
           "samma spår slumpvis omflyttade gav 52,9 procent. Vid verkligt svåra skador kan spåren däremot leda fel.")
summary_en = ("Methods report. A trace reader reads from a 3D scan which runes a damaged rune can be, and a language model chooses "
              "among them. When whole words were hidden on 17 scanned runestones, 59.9 percent came out right with the traces "
              "against 53.5 percent without them, and the same traces shuffled gave 52.9 percent. At really severe damage, however, "
              "the traces can mislead.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report (methods report), report version {REPORT_VERSION}; analysis in "
           f"Vitki {APP_VERSION}. https://vitkirunor.se/en/forskningsrapporter/{SLUG}")


def chart(sv):
    f = d1 if sv else e1
    lab = (("Utan spår", "Med skanningens spår", "Spåren omflyttade") if sv else ("Without traces", "With the scan's traces", "Traces shuffled"))
    rows = [":::chart Dolda ord som fylldes i rätt, procent" if sv else ":::chart Hidden words filled in correctly, percent"]
    for g_sv, g_en, mm, n in (("Alla 17 stenar", "All 17 stones", MN, A["n"]), ("Utan Sö 113", "Without Sö 113", XU["means"], XU["n"])):
        rows.append(f"# {g_sv if sv else g_en}")
        for c, lb in zip(("utan", "skanner", "omflyttad"), lab):
            rows.append(f"{'+' if c == 'skanner' else ''}{lb} | {f(mm[c]['word_ok'])} | {n} {'ord' if sv else 'words'}")
    rows += ["Källa: Rundata; skanningar av Laila Kitzler Åhfeldt, Riksantikvarieämbetet (CC BY 4.0)." if sv else
             "Source: Rundata; scans by Laila Kitzler Åhfeldt, Swedish National Heritage Board (CC BY 4.0).", ":::"]
    return "\n".join(rows)


body = f"""*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, 3D-skanning, skadade runor, språkmodell, luckor, rekonstruktion, Södermanland. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Vad som inte är prövat.** Provet var inte låst i en plan, och spårläsarens inställningar togs fram på en av stenarna i provet. Provet döljer hela ord på hela runor; vid verkliga skador har spåren bara prövats på fem stenar, och där kan de leda fel.
**Bakgrund och syfte.** När runor är skadade läser runologen vad som finns kvar på stenen, och en språkmodell kan föreslå vad som stod där. Frågan här är om det som en 3D-skanning visar av de skadade runorna gör språkmodellens förslag bättre.
**Material.** 17 runstenar i Södermanland som Laila Kitzler Åhfeldt har skannat i 3D och publicerat öppet, med texten i Samnordisk runtextdatabas (Rundata); {A['n']} ord som gick att pröva.
**Metod.** En spårläsare läser i skanningens djupbild vilka av de sexton runorna varje upptäckt runa kan vara, med en sannolikhet för var och en. Varje helt ord på två till sex runor döljs, och en språkmodell som är tränad utan stenen fyller i det: utan spår, med spåren och med samma spår slumpvis omflyttade mellan stenens platser. Jämförelsen är parad, ord för ord.
**Resultat.** Med spåren blev {d1(MN['skanner']['word_ok'])} procent av orden rätt, mot {d1(MN['utan']['word_ok'])} procent utan dem, {pexp(SU['p'])}. Omflyttade spår gav {d1(MN['omflyttad']['word_ok'])} procent, sämre än inga spår alls. Utan stenen där inställningarna togs fram: {d1(XU['means']['skanner']['word_ok'])} mot {d1(XU['means']['utan']['word_ok'])} procent. På fem stenar med verkliga luckor fungerade kedjan, men vid de svåraste skadorna ledde spåren fel.
**Slutsats.** Det skanningen visar hjälper språkmodellen, och det hjälper för att det läser stenen, inte bara för att det minskar antalet möjliga runor. Vid svåra skador ska spåren visas för den som läser och vägas in först när den har bekräftat dem.

## 1. Inledning

Många runinskrifter har skadade eller förlorade runor. Runologen läser det som finns kvar på stenen, och utgåvorna anger säkra, osäkra och förlorade runor. På senare år har språkmodeller använts för att föreslå vad som stått i skadade inskrifter; den mest kända är Ithaca för grekiska inskrifter (Assael m.fl. 2022). Laila Kitzler Åhfeldt har skannat ett stort antal runstenar i 3D för att studera huggtekniken (Kitzler Åhfeldt 2002; 2015) och publicerat skanningarna öppet (Kitzler Åhfeldt 2024).

Det som saknas är ett sätt att låta det som skanningen visar av en skadad runa styra vad en språkmodell föreslår, och ett prov på om det hjälper. Syftet här är att redovisa en spårläsare som gör det och att pröva den på dolda ord på skannade stenar.

## 2. Förregistrering: vad som var bestämt i förväg och vad som inte var det

Provet var inte låst i en plan. Spårläsaren byggdes i steg den 17 oktober 2026. Dess två inställningar, hur skarpt sannolikheterna fördelas och vad en extra del av en runa kostar, prövades fram på Sö 113 ensam och validerades sedan på Sö 134 och Sö 207, som inte hade använts. Det skarpa provet bestämdes därefter i koden, med tre villkor och samma mått för alla stenar, och kördes en gång. Sö 113 ingår bland de 17 stenarna; den 31 oktober räknades provet om utan Sö 113, med samma test. Provet på verkliga luckor kördes samma dag som det skarpa provet.

## 3. Material

- **Skanningarna.** Laila Kitzler Åhfeldt, Riksantikvarieämbetet, skannade runstenarna i Södermanland med en ATOS-skanner i projektet Runristandets dynamik och publicerade dem på Zenodo under CC BY 4.0 (Kitzler Åhfeldt 2024). Av dem användes de {A['stones']} stenar där Rundata har en ordtext som kan paras mot de upptäckta runorna. Bara runstenar.
- **Texterna.** Translitterering och normalisering ur Samnordisk runtextdatabas (Rundata).
- **Orden.** Varje helt ord på två till sex runor: 197 ordplatser, varav {A['n']} där alla tre villkoren gav ett resultat.
- **Verkliga luckor.** Fem stenar ur samma serie med luckor som Rundata markerar: {', '.join(sorted(G))}.

## 4. Metod

**4.1 Spårläsaren.** I skanningens djupbild hittas runornas stavar. Delar av huggspåret utanför stavarna, kvistar och bågar, får en vikt efter hur djupa, långsträckta och långa de är, eftersom vittring och märken i ytan ger grunda och korta spår. Varje upptäckt runa jämförs med formen för var och en av de sexton runorna, med en kostnad för delar som saknas eller är för många, och kostnaderna görs om till en sannolikhet per runa.

**4.2 Språkmodellen.** Projektets modell för runtext föreslår ord och väger dem efter hur vanliga de är i runtexterna och i sitt sammanhang. Den är tränad utan stenen som prövas. Spåren läggs in mjukt: en runa som skanningen inte stöder blir mindre sannolik, inte omöjlig.

**4.3 Provet.** Varje helt ord på två till sex runor döljs och fylls i under tre villkor: utan spår, med spårläsarens sannolikheter för ordets runor, och med samma uppsättningar slumpvis omflyttade mellan stenens platser. Det sista villkoret prövar om spåren hjälper för att de läser stenen, eller bara för att de minskar antalet möjliga runor. Måtten är andelen ord som blev rätt och sannolikheten för det rätta ordet, jämförda ord för ord med Wilcoxons test för parade värden.

**4.4 Avvikelser.** Ingen plan fanns, så inga avvikelser kan redovisas. Omräkningen utan Sö 113 gjordes efter provet.

## 5. Resultat

**5.1 Det skarpa provet.** {A['n']} ord på {A['stones']} stenar. Rätt ord: {d1(MN['utan']['word_ok'])} procent utan spår, {d1(MN['skanner']['word_ok'])} procent med spåren och {d1(MN['omflyttad']['word_ok'])} procent med spåren omflyttade. Sannolikheten för det rätta ordet: {d3(MN['utan']['p_truth'])} utan, {d3(MN['skanner']['p_truth'])} med och {d3(MN['omflyttad']['p_truth'])} med omflyttade spår. Spåren gav högre sannolikhet än inga spår, {pexp(SU['p'])}, och högre än omflyttade spår, {pexp(SO['p'])}. Omflyttade spår gav lägre sannolikhet än inga spår, {pf(OU['p'])}: fel ledtrådar skadar. I klartext: med skanningens hjälp blev ungefär sex dolda ord av tio rätt i stället för drygt fem, och när ledtrådarna kastades om blev det sämre än utan dem.

{chart(True)}

**5.2 Utan Sö 113.** Utan stenen där inställningarna togs fram: {XU['n']} ord på {XU['stones']} stenar, {d1(XU['means']['utan']['word_ok'])} procent rätt utan spår, {d1(XU['means']['skanner']['word_ok'])} med och {d1(XU['means']['omflyttad']['word_ok'])} med omflyttade; spåren mot inga spår {pexp(XU['skanner_vs_utan']['p'])}, mot omflyttade {pexp(XU['skanner_vs_omflyttad']['p'])}.

**5.3 Det tidigare steget, på oskadade runor.** Innan språkmodellen kopplades in prövades spårläsaren ensam på de upptäckta runorna på Sö 113, Sö 134 och Sö 207: sannolikheten för den rätta runan var i medel {d3(E['pooled_mean_p'])} mot {d3(E['pooled_null'][0])} när texten blandades om ({E['n_shuffles']} omblandningar, {pf(E['p_value'])}), och den rätta runan kom först i {d1(E['pooled_top1'])} procent mot {d1(E['pooled_top1_null'][0])} ({pf(E['p_value_top1'])}). Spåren ensamma säger lite; tillsammans med språket säger de mer.

**5.4 Verkliga luckor.** På de fem stenarna med verkliga luckor ({N_GAP_WORDS} ord med förlorade runor) fungerade kedjan från skanning till förslag. Där stavarna är hela behöll spåren de rätta orden, som *stæin* på Sö 211 och *gæiRfastr* på Sö 45. Men där skadan var svår ledde spåren fel: på Sö 162 drog de *stæin* mot *staf*, och på Sö 206 drog de förslaget för ett skadat namn från *karl* till *kumbl*. Spårläsaren är prövad på oskadade runor, och vittring vid en skada ger just de falska kvistar som den då läser.

## 6. Diskussion

**Vad metoden klarar.** Skanningens spår gör språkmodellens förslag bättre, och det är spåren själva som hjälper: samma uppsättningar på fel plats gör förslagen sämre. Det är ett första prov på att 3D-skanning och språkmodell kan läsa en inskrift tillsammans, där skanningen visar vad som går att se och modellen vad som går att säga.

**Mot tidigare forskning.** Ithaca använder bara texten (Assael m.fl. 2022). Här läggs det som går att se på stenen till, i form av sannolikheter som modellen väger in. Skanningarna gjordes för att studera huggteknik (Kitzler Åhfeldt 2015) och visar sig också vara en källa för läsningen.

**Svagheter, i ordning efter vikt.**

1. **Dolda ord är inte skadade ord.** Provet döljer ord vars runor är hela på stenen. Vid verkliga skador har spåren bara prövats på fem stenar, och där kan de leda fel.
2. **Ingen låst plan.** Provets villkor bestämdes före körningen, men utan en plan med kontrollsumma. Inställningarna togs fram på Sö 113, som ingår i provet; utan den håller resultatet.
3. **En skanningsserie.** Alla stenar kommer ur samma serie i Södermanland, med samma skanner. Andra skannrar och andra stenar kan ge andra spår.
4. **Måttet för rätt ord.** Ett ord räknas som rätt när det är samma ord eller böjning; regeln räknar ibland närliggande former som samma, vilket gäller alla tre villkoren lika.

**Var metoden inte ska användas.** Ensam, vid svåra skador. Där ska spåren visas för den som läser stenen och vägas in först när läsaren har bekräftat dem; så gör Vitki i dag.

**Vad som skulle fälla metoden.** Att spåren inte gav någon förbättring på stenar ur andra skanningsserier, eller att de oftare ledde fel än rätt vid verkliga skador i ett större material.

## 7. Slutsats

Med 3D-skanningens spår fyllde språkmodellen i {d1(MN['skanner']['word_ok'])} procent av de dolda orden rätt mot {d1(MN['utan']['word_ok'])} procent utan, och omflyttade spår gjorde det sämre. Skanningen och språket kan läsa en runsten tillsammans. Vid svåra skador måste en människa bekräfta vad skanningen ser innan det vägs in.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 31 oktober 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Spårläsaren och proven: `utdata/sparlasare/` (stegen `led_a.py`–`led_g.py`; det skarpa provet `led_f.py` med sammanställningen `led_f_summering.json`; omräkningen utan Sö 113 `utan_so113.py`; verkliga luckor `led_g.json`).
- Huggspåren: `src/auto_grooves.py`. Språkmodellen: `src/runlm.py` och `src/textmodel.py`.
- Skanningarna: Kitzler Åhfeldt 2024, doi:10.5281/zenodo.11951255.
- Rapporten byggs av `utdata/blogg/build/build_rapport_sparlasare.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer.
- I Vitki visas spåren i stenanalysen under ”Vad skannern ser”.

## Referenser

- Assael, Y., Sommerschield, T., Shillingford, B. m.fl. 2022. Restoring and attributing ancient texts using deep neural networks. *Nature* 603, s. 280–283.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Archaeology B:9. Stockholm: Stockholms universitet.
- Kitzler Åhfeldt, L. 2015. Rune Carvers and Local Mobility. *Viking and Medieval Scandinavia* 11, s. 143–182.
- Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland / Runestones in Södermanland* [datamängd]. Riksantikvarieämbetet. Zenodo. doi:10.5281/zenodo.11951255. CC BY 4.0.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.

:::box Det viktigaste i korthet
- Det en 3D-skanning visar av en runa hjälper en språkmodell att fylla i rätt ord, och fel ledtrådar gör det sämre.
- Skanningen och språket kan alltså läsa en runsten tillsammans: det ena visar vad som syns, det andra vad som går att säga.
- Vid svåra skador kan spåren leda fel, så en människa måste se och bekräfta dem först.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Methods report, partially tested. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, 3D scanning, damaged runes, language model, lacunae, restoration, Södermanland. Competing interests: none. Funding: none.*

## Abstract

**What has not been tested.** The test was not locked in a plan, and the trace reader's settings were derived on one of the stones in the test. The test hides whole words of whole runes; at real damage the traces have been tested on only five stones, and there they can mislead.
**Background and aim.** When runes are damaged the runologist reads what remains on the stone, and a language model can suggest what stood there. The question here is whether what a 3D scan shows of the damaged runes makes the language model's suggestions better.
**Material.** 17 runestones in Södermanland that Laila Kitzler Åhfeldt has scanned in 3D and published openly, with their text in the Scandinavian Runic-text Database (Rundata); {A['n']} words that could be tested.
**Method.** A trace reader reads in the scan's depth image which of the sixteen runes each detected rune can be, with a probability for each. Every whole word of two to six runes is hidden, and a language model trained without the stone fills it in: without traces, with the traces and with the same traces shuffled at random among the stone's positions. The comparison is paired, word by word.
**Results.** With the traces {e1(MN['skanner']['word_ok'])} percent of the words came out right, against {e1(MN['utan']['word_ok'])} percent without them, {pexp(SU['p'], True)}. Shuffled traces gave {e1(MN['omflyttad']['word_ok'])} percent, worse than no traces at all. Without the stone on which the settings were derived: {e1(XU['means']['skanner']['word_ok'])} against {e1(XU['means']['utan']['word_ok'])} percent. On five stones with real lacunae the chain worked, but at the most severe damage the traces misled.
**Conclusion.** What the scan shows helps the language model, and it helps because it reads the stone, not merely because it reduces the number of possible runes. At severe damage the traces should be shown to the reader and weighed in only once the reader has confirmed them.

## 1. Introduction

Many runic inscriptions have damaged or lost runes. The runologist reads what remains on the stone, and the editions mark certain, uncertain and lost runes. In recent years language models have been used to suggest what stood in damaged inscriptions; the best known is Ithaca for Greek inscriptions (Assael et al. 2022). Laila Kitzler Åhfeldt has scanned a large number of runestones in 3D to study carving technique (Kitzler Åhfeldt 2002; 2015) and published the scans openly (Kitzler Åhfeldt 2024).

What is missing is a way of letting what the scan shows of a damaged rune steer what a language model suggests, and a test of whether it helps. The aim here is to report a trace reader that does so and to test it on hidden words on scanned stones.

## 2. Pre-registration: what was fixed in advance and what was not

The test was not locked in a plan. The trace reader was built in steps on 17 October 2026. Its two settings, how sharply the probabilities are distributed and what an extra part of a rune costs, were tried out on Sö 113 alone and then validated on Sö 134 and Sö 207, which had not been used. The sharp test was then fixed in the code, with three conditions and the same measures for all stones, and run once. Sö 113 is among the 17 stones; on 31 October the test was recomputed without Sö 113, with the same test. The test on real lacunae was run the same day as the sharp test.

## 3. Material

- **The scans.** Laila Kitzler Åhfeldt, Swedish National Heritage Board, scanned the runestones of Södermanland with an ATOS scanner in the project Runristandets dynamik and published them on Zenodo under CC BY 4.0 (Kitzler Åhfeldt 2024). Of these, the {A['stones']} stones were used for which Rundata has a word text that can be paired with the detected runes. Runestones only.
- **The texts.** Transliteration and normalisation from the Scandinavian Runic-text Database (Rundata).
- **The words.** Every whole word of two to six runes: 197 word positions, {A['n']} of them where all three conditions gave a result.
- **Real lacunae.** Five stones from the same series with lacunae marked in Rundata: {', '.join(sorted(G))}.

## 4. Method

**4.1 The trace reader.** In the scan's depth image the runes' staves are found. Parts of the groove outside the staves, branches and bows, get a weight by how deep, elongated and long they are, since weathering and marks in the surface give shallow and short traces. Each detected rune is compared with the shape of each of the sixteen runes, with a cost for parts missing or too many, and the costs are turned into a probability per rune.

**4.2 The language model.** The project's model of runic text suggests words and weighs them by how common they are in the runic texts and in their context. It is trained without the stone being tested. The traces are put in softly: a rune the scan does not support becomes less probable, not impossible.

**4.3 The test.** Every whole word of two to six runes is hidden and filled in under three conditions: without traces, with the trace reader's probabilities for the word's runes, and with the same sets shuffled at random among the stone's positions. The last condition tests whether the traces help because they read the stone, or merely because they reduce the number of possible runes. The measures are the share of words that came out right and the probability of the right word, compared word by word with Wilcoxon's test for paired values.

**4.4 Deviations.** No plan existed, so no deviations can be reported. The recomputation without Sö 113 was made after the test.

## 5. Results

**5.1 The sharp test.** {A['n']} words on {A['stones']} stones. Right word: {e1(MN['utan']['word_ok'])} percent without traces, {e1(MN['skanner']['word_ok'])} percent with the traces and {e1(MN['omflyttad']['word_ok'])} percent with the traces shuffled. The probability of the right word: {MN['utan']['p_truth']:.3f} without, {MN['skanner']['p_truth']:.3f} with and {MN['omflyttad']['p_truth']:.3f} with shuffled traces. The traces gave a higher probability than no traces, {pexp(SU['p'], True)}, and higher than shuffled traces, {pexp(SO['p'], True)}. Shuffled traces gave a lower probability than no traces, {pf(OU['p'], True)}: wrong clues hurt. In plain words: with the scan's help about six hidden words in ten came out right instead of just over five, and when the clues were shuffled it was worse than without them.

{chart(False)}

**5.2 Without Sö 113.** Without the stone on which the settings were derived: {XU['n']} words on {XU['stones']} stones, {e1(XU['means']['utan']['word_ok'])} percent right without traces, {e1(XU['means']['skanner']['word_ok'])} with and {e1(XU['means']['omflyttad']['word_ok'])} with shuffled; the traces against no traces {pexp(XU['skanner_vs_utan']['p'], True)}, against shuffled {pexp(XU['skanner_vs_omflyttad']['p'], True)}.

**5.3 The earlier step, on undamaged runes.** Before the language model was connected, the trace reader was tested on its own on the detected runes of Sö 113, Sö 134 and Sö 207: the probability of the right rune was on average {E['pooled_mean_p']:.3f} against {E['pooled_null'][0]:.3f} when the text was shuffled ({E['n_shuffles']} shuffles, {pf(E['p_value'], True)}), and the right rune came first in {e1(E['pooled_top1'])} percent against {e1(E['pooled_top1_null'][0])} ({pf(E['p_value_top1'], True)}). The traces alone say little; together with the language they say more.

**5.4 Real lacunae.** On the five stones with real lacunae ({N_GAP_WORDS} words with lost runes) the chain from scan to suggestion worked. Where the staves are whole the traces kept the right words, such as *stæin* on Sö 211 and *gæiRfastr* on Sö 45. But where the damage was severe the traces misled: on Sö 162 they pulled *stæin* towards *staf*, and on Sö 206 they pulled the suggestion for a damaged name from *karl* to *kumbl*. The trace reader is tested on undamaged runes, and weathering at a lesion produces exactly the false branches it then reads.

## 6. Discussion

**What the method can do.** The scan's traces make the language model's suggestions better, and it is the traces themselves that help: the same sets in the wrong place make the suggestions worse. It is a first test that 3D scanning and a language model can read an inscription together, the scan showing what can be seen and the model what can be said.

**Against earlier research.** Ithaca uses only the text (Assael et al. 2022). Here what can be seen on the stone is added, as probabilities the model weighs in. The scans were made to study carving technique (Kitzler Åhfeldt 2015) and turn out to be a source for reading too.

**Weaknesses, in order of weight.**

1. **Hidden words are not damaged words.** The test hides words whose runes are whole on the stone. At real damage the traces have been tested on only five stones, and there they can mislead.
2. **No locked plan.** The test's conditions were fixed before the run, but without a plan with a checksum. The settings were derived on Sö 113, which is in the test; without it the result holds.
3. **One scanning series.** All stones come from the same series in Södermanland, with the same scanner. Other scanners and other stones may give other traces.
4. **The measure of a right word.** A word counts as right when it is the same word or inflection; the rule sometimes counts neighbouring forms as the same, which applies equally to all three conditions.

**Where the method should not be used.** On its own, at severe damage. There the traces should be shown to the reader of the stone and weighed in only once the reader has confirmed them; that is what Vitki does today.

**What would overturn the method.** If the traces gave no improvement on stones from other scanning series, or if they misled more often than they helped at real damage in a larger material.

## 7. Conclusion

With the 3D scan's traces the language model filled in {e1(MN['skanner']['word_ok'])} percent of the hidden words correctly against {e1(MN['utan']['word_ok'])} percent without, and shuffled traces made it worse. The scan and the language can read a runestone together. At severe damage a human must confirm what the scan sees before it is weighed in.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 31 October 2026. No release with a DOI exists yet; when one is made, the report will refer to it. All code and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The trace reader and the tests: `utdata/sparlasare/` (the steps `led_a.py`–`led_g.py`; the sharp test `led_f.py` with the summary `led_f_summering.json`; the recomputation without Sö 113 `utan_so113.py`; real lacunae `led_g.json`).
- The grooves: `src/auto_grooves.py`. The language model: `src/runlm.py` and `src/textmodel.py`.
- The scans: Kitzler Åhfeldt 2024, doi:10.5281/zenodo.11951255.
- The report is built by `utdata/blogg/build/build_rapport_sparlasare.py`, which reads every number from the result files and stops if anything disagrees.
- In Vitki the traces are shown in the stone analysis under "What the scanner sees".

## References

- Assael, Y., Sommerschield, T., Shillingford, B. et al. 2022. Restoring and attributing ancient texts using deep neural networks. *Nature* 603, pp. 280–283.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Archaeology B:9. Stockholm: Stockholm University.
- Kitzler Åhfeldt, L. 2015. Rune Carvers and Local Mobility. *Viking and Medieval Scandinavia* 11, pp. 143–182.
- Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland / Runestones in Södermanland* [dataset]. Swedish National Heritage Board. Zenodo. doi:10.5281/zenodo.11951255. CC BY 4.0.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.

:::box The essentials
- What a 3D scan shows of a rune helps a language model fill in the right word, and wrong clues make it worse.
- The scan and the language can thus read a runestone together: one shows what can be seen, the other what can be said.
- At severe damage the traces can mislead, so a human must see and confirm them first.
:::
"""

JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
assert "I klartext" in body and "In plain words" in body_en  # mallen version 4
assert "## Sammanfattning\n\n**Vad som inte är prövat.**" in body
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion 1, 2026-10-31. Tidslinje: ")

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Huggspår och 3D", "Sannolikhetsmodellen"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_sparlasare.json")
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
                 "topic": "Rapport|sparlasare", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
