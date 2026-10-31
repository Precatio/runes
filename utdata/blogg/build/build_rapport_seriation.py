"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4; Delvis prövat fynd): "Språk och innehåll ordnar
Upplands runstenar i samma följd som stilkronologin – rangkorrelation 0,54 utan ornamentiken" (sv + en). Seriationen
(r/chronology.R, inte förregistrerad) och den låsta planen för halvorna och Södermanland
(analysplaner/2026-10-31-seriation-halvor-sodermanland.md). Alla siffror asserteras mot filerna.
    ../../../.venv/bin/python build_rapport_seriation.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

FP = "e83202e01a5e6d27"
APP_VERSION = json.load(open(os.path.join(ROOT, "web", "package.json")))["version"]
assert APP_VERSION == "3.0.0"
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 1
TODAY = "2026-10-31"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = "seriationen gjordes första gången 2026-10-05; materialet frystes 2026-10-29; planen för halvorna och Södermanland låstes och kördes 2026-10-31"
TL_EN = "the seriation was first made 2026-10-05; the material was frozen 2026-10-29; the plan for the halves and Södermanland was locked and run 2026-10-31"
CH = json.load(open(os.path.join(ROOT, "data", "cache", "r", "corpus", FP, "chronology.json"), encoding="utf-8"))
RP = json.load(open(os.path.join(ROOT, "utdata", "seriation", "replikering.json"), encoding="utf-8"))
PLAN_SHA = open(os.path.join(ROOT, "analysplaner", "2026-10-31-seriation-halvor-sodermanland.sha256")).read().split()[0]
assert PLAN_SHA.startswith("454cacf9")

d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731


def pexp(p, en=False):
    m, e = f"{p:.1e}".split("e")
    m = m if en else m.replace(".", ",")
    return f"{m} · 10{str(int(e)).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))}"


# ---- the seriation in Uppland -----------------------------------------------------------------------------------------
assert (CH["region"], CH["n_stones"], CH["n_dated"], CH["n_attributes"]) == ("U", 818, 501, 65)
V = CH["validation"]
assert (d2(V["rho"]), d2(V["partial_rho"]), d2(V["lat_rho"]), V["mae_years"], V["mae_loo_years"], V["mae_naive_years"]) == ("0,54", "0,54", "0,09", 21, 21, 25)
VR = V["robustness"]
assert [d2(VR[k]["rho"]) for k in ("no_cross", "no_anchor", "no_changing", "strict", "within_district", "within_carver")] == \
    ["0,55", "0,54", "0,54", "0,53", "0,51", "0,25"]
assert (VR["within_district"]["groups"], VR["within_carver"]["groups"], VR["within_carver"]["n"]) == (23, 13, 251)
PS = {s["style"]: s for s in CH["per_style"]}
ORDER = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
assert [PS[s]["n"] for s in ORDER] == [32, 43, 30, 61, 100, 199, 36]
assert [d2(PS[s]["mean_score"]) for s in ORDER] == ["-0,79", "-0,89", "-0,46", "-0,18", "-0,01", "0,51", "0,80"]

# ---- the locked plan: halves and Södermanland -------------------------------------------------------------------------
assert RP["plan"] == "analysplaner/2026-10-31-seriation-halvor-sodermanland.md" and RP["corpus"] == FP
U, HA, HB, SO = RP["uppland"], RP["half_A"], RP["half_B"], RP["sodermanland"]
assert abs(U["rho"] - V["rho"]) < 0.001 and U["n_dated"] == 501  # the code check reproduced the known value
assert (HA["n_dated"], HB["n_dated"], d2(HA["rho"]), d2(HB["rho"]), d2(HA["partial_rho"]), d2(HB["partial_rho"])) == (264, 236, "0,51", "0,54", "0,51", "0,53")
assert HA["p_holm"] < 1e-17 and HB["p_holm"] < 1e-17 and RP["halves_hold"] is True
assert (SO["n_stones"], SO["n_dated"], SO["n_attributes"], d2(SO["rho"]), d2(SO["partial_rho"]), d2(SO["within_district"])) == (270, 151, 44, "0,32", "0,29", "0,24")
assert 6e-5 < SO["p_holm"] < 7e-5 and RP["sodermanland_status"] == "replikerat" and RP["sodermanland_geografi"] is True
assert (d2(HA["within_district"]), d2(HB["within_district"]), HA["n_districts"], HB["n_districts"], SO["n_districts"]) == ("0,46", "0,52", 14, 16, 11)

SLUG = "seriationen-foljer-stilkronologin"
title = "Språk och innehåll ordnar Upplands runstenar i samma följd som stilkronologin – rangkorrelation 0,54 utan ornamentiken"
title_en = "Language and content order the runestones of Uppland in the same sequence as the stylistic chronology – rank correlation 0.54 without the ornament"
summary = ("Delvis prövat fynd. Ordnas Upplands runstenar bara efter språk, formler och innehåll hamnar de i ungefär samma följd "
           "som i Gräslunds stilkronologi, som bygger på ornamentiken. Det håller lika starkt i båda halvorna av materialet. "
           "I Södermanland finns samma samband, men svagare och delvis geografiskt. Inom en och samma ristare är det svagt.")
summary_en = ("Partially tested finding. If the runestones of Uppland are ordered only by language, formulas and content, they fall "
              "in roughly the same sequence as in Gräslund's stylistic chronology, which rests on the ornament. It holds equally "
              "strongly in both halves of the material. In Södermanland the same association is found, but weaker and partly "
              "geographical. Within one and the same carver it is weak.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/forskningsrapporter/{SLUG}")


def chart(sv):
    rows = [":::chart Seriationens rangkorrelation med stilkronologin" if sv else ":::chart The seriation's rank correlation with the stylistic chronology"]
    f = d2 if sv else (lambda x: f"{x:.2f}")
    st = "daterade stenar" if sv else "dated stones"
    for lab_sv, lab_en, r in (("Uppland, hela", "Uppland, all", U), ("Uppland, halva A", "Uppland, half A", HA),
                              ("Uppland, halva B", "Uppland, half B", HB), ("Södermanland", "Södermanland", SO)):
        rows.append(f"{'+' if r is not SO else ''}{lab_sv if sv else lab_en} | {f(r['rho'])} | {r['n_dated']} {st}")
    rows.append(f"{'Uppland, inom ristare' if sv else 'Uppland, within carvers'} | {f(VR['within_carver']['rho'])} | {VR['within_carver']['n']} {st}")
    rows += ["Källa: Rundata. Spearmans rho mot stilgruppens mittår (Gräslund 2006)." if sv else
             "Source: Rundata. Spearman's rho against the style group's midpoint (Gräslund 2006).", ":::"]
    return "\n".join(rows)


body = f"""*Viktor Kvant, oberoende forskare. Delvis prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, seriation, korrespondensanalys, stilkronologi, datering, Uppland, Södermanland. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Vad som inte är prövat.** Seriationen i Uppland var inte förregistrerad, och den har ingen fast serie känslighetsanalyser som projektets samband mellan två drag; halvorna och en replikering i Södermanland prövades under en plan som låstes före körningen.
**Bakgrund och syfte.** Upplands runstenar dateras relativt efter ornamentiken, enligt Anne-Sofie Gräslunds stilkronologi. Frågan här är om stenarna hamnar i samma följd när de ordnas efter något helt annat: språket, formlerna och innehållet.
**Material.** {CH['n_stones']} runstenar i Uppland med minst fyra av {CH['n_attributes']} drag, varav {CH['n_dated']} med stilgrupp; för replikeringen {SO['n_stones']} stenar i Södermanland, varav {SO['n_dated']} med stilgrupp. Ur Samnordisk runtextdatabas (Rundata).
**Metod.** Korrespondensanalys av en tabell över stenar och drag, utan stilgruppen; stenarnas läge på första axeln jämförs med stilgruppens mittår (Spearmans rangkorrelation). Halvorna och Södermanland med samma metod, Holm-korrigerat.
**Resultat.** I Uppland rho = {d2(V['rho'])}, {d2(V['partial_rho'])} med latituden konstant. Halva A {d2(HA['rho'])}, halva B {d2(HB['rho'])}, båda Holm-korrigerat p under 10⁻¹⁷. Södermanland {d2(SO['rho'])}, Holm-korrigerat p = {pexp(SO['p_holm'])}, men {d2(SO['partial_rho'])} med latituden konstant. Inom härad {d2(VR['within_district']['rho'])}, inom samma ristare bara {d2(VR['within_carver']['rho'])}.
**Slutsats.** Språk och innehåll bär samma tidsföljd som ornamentiken i Uppland, och det är ett stöd för stilkronologin som är oberoende av den. Följden går till stor del mellan ristare snarare än inom dem, och den räcker inte för att datera enskilda stenar.

## 1. Inledning

Upplands vikingatida runstenar dateras relativt efter ornamentiken, i Anne-Sofie Gräslunds stilgrupper från RAK och Fp till Pr1–Pr5 (Gräslund 2006). Kronologin bygger på hur runormen och djurhuvudena är formade, inte på språket eller vad texten säger. Om språk och innehåll förändrades under samma tid borde stenarna hamna i ungefär samma följd när de ordnas efter dem, och det vore ett stöd för kronologin som inte bygger på samma iakttagelser. Ger två slags iakttagelser som inte har med varandra att göra samma ordning, är det svårt att förklara på annat sätt än att båda följer tiden.

Seriation med korrespondensanalys är en vanlig metod för relativ datering i arkeologin (Greenacre 2007). Syftet här är att pröva om språk, formler och innehåll ger samma följd som stilkronologin, om det håller i två halvor av materialet och om det gäller också utanför Uppland, där kronologin inte byggdes.

## 2. Förregistrering: vad som var bestämt i förväg och vad som är explorativt

Seriationen i Uppland gjordes första gången den 5 oktober 2026 som en del av projektets genomgång, utan låst plan, och dess värde var känt när resten av studien planerades. Den är alltså inte förregistrerad. Varianterna utan kors, utan utlandsfärder, utan de drag som förändras över tid och inom härad och ristare (5.2) räknades samtidigt och är explorativa.

Den 31 oktober 2026 låstes en plan för två prövningar innan de kördes (kontrollsumma SHA-256 `{PLAN_SHA[:16]}…`): seriationen i var halva av Upplands stenar för sig, och samma seriation på Södermanlands stenar, som inte hade seriationsprövats för sig. Halvorna håller när Holm-p är under 0,05 och rho minst 0,3 i båda. Södermanland är *replikerat* med samma gränser; är korrelationen med latituden konstant under 0,3 sägs att sambandet kan vara geografiskt. En provkörning återgav Upplands kända värde exakt innan prövningarna kördes.

## 3. Material

- **Källa.** Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk vid Uppsala universitet. Materialet frystes för analysen den 29 oktober 2026. Bara runstenar.
- **Dragen.** Språkdrag (stavning av vissa ljud och ord), fem formler (resarformel, monument, ordföljd, ristarsignatur, bön), kors, kortkvistrunor och innehållskategorier, som närvaro eller frånvaro per sten. Drag som finns på färre än 15 stenar räknas inte, och stenar med färre än fyra drag räknas inte. Stilgruppen ingår inte.
- **Tiden** är stilgruppens mittår enligt Gräslund (2006).
- **Uppland:** {CH['n_stones']} stenar och {CH['n_attributes']} drag, {CH['n_dated']} stenar med stilgrupp. **Södermanland:** {SO['n_stones']} stenar och {SO['n_attributes']} drag, {SO['n_dated']} med stilgrupp.
- **Halvorna** är projektets fasta indelning socken för socken.

## 4. Metod

**4.1 Seriationen.** Korrespondensanalys (paketet ca; Nenadić & Greenacre 2007) av tabellen med stenar och drag. Analysen placerar stenar som har samma drag nära varandra, och drag som brukar finnas på samma stenar nära varandra; den första axeln är den riktning i materialet som skiljer stenarna mest. Stenarnas läge på den första axeln jämförs med stilgruppens mittår med Spearmans rangkorrelation. Axelns tecken är godtyckligt och vänds så att korrelationen blir positiv.

**4.2 Geografin.** Eftersom språkdrag också skiljer sig mellan norr och söder redovisas den partiella korrelationen med latituden konstant.

**4.3 Halvorna och Södermanland.** Samma metod, oförändrad, på var halva och på Södermanland, Holm-korrigerat över de tre testen.

**4.4 Varianterna (explorativa).** Seriationen utan kors, utan utlandsfärder, utan de drag vars förändring över tid mäts för sig (stungna runor, monoftongen, åsrunan) och utan allt detta, samt korrelationen inom härad och inom ristare med minst fem daterade stenar.

**4.5 Avvikelser.** Inga från planen.

## 5. Resultat

**5.1 Uppland och halvorna.** I Uppland är rho = {d2(V['rho'])} (okorrigerat p = {pexp(V['p'])}) och {d2(V['partial_rho'])} med latituden konstant; latituden själv korrelerar bara {d2(V['lat_rho'])} med axeln. Halva A: {HA['n_dated']} daterade stenar, rho {d2(HA['rho'])}, med latituden konstant {d2(HA['partial_rho'])}. Halva B: {HB['n_dated']} daterade stenar, rho {d2(HB['rho'])}, med latituden konstant {d2(HB['partial_rho'])}. Båda Holm-korrigerat p under 10⁻¹⁷: halvorna *håller*. Stilgrupperna i medel längs axeln: RAK {d2(PS['RAK']['mean_score'])}, Fp {d2(PS['Fp']['mean_score'])}, Pr1 {d2(PS['Pr1']['mean_score'])}, Pr2 {d2(PS['Pr2']['mean_score'])}, Pr3 {d2(PS['Pr3']['mean_score'])}, Pr4 {d2(PS['Pr4']['mean_score'])}, Pr5 {d2(PS['Pr5']['mean_score'])}: följden är stilkronologins, utom att RAK och Fp byter plats. I klartext: ordnar man stenarna bara efter vad och hur det står skrivet hamnar de i ungefär samma ordning som när man ordnar dem efter ornamentiken; sambandet är måttligt starkt och lika starkt i båda halvorna.

{chart(True)}

**5.2 Varianterna (explorativa).** Utan kors {d2(VR['no_cross']['rho'])}, utan utlandsfärder {d2(VR['no_anchor']['rho'])}, utan de drag som förändras över tid {d2(VR['no_changing']['rho'])}, utan allt detta {d2(VR['strict']['rho'])}. Inom härad ({VR['within_district']['groups']} härader) {d2(VR['within_district']['rho'])}; inom ristare ({VR['within_carver']['groups']} ristare med minst fem daterade stenar, {VR['within_carver']['n']} stenar) bara {d2(VR['within_carver']['rho'])}.

**5.3 Södermanland (replikering).** {SO['n_dated']} daterade stenar: rho {d2(SO['rho'])}, Holm-korrigerat p = {pexp(SO['p_holm'])}; *replikerat* enligt planens regel. Med latituden konstant {d2(SO['partial_rho'])}, under planens gräns 0,3, så sambandet kan delvis vara geografiskt. Inom härad {d2(SO['within_district'])} ({SO['n_districts']} härader).

**5.4 Dateringen av enskilda stenar.** Används axeln för att skatta årtal blir medelfelet {V['mae_loo_years']} år när varje sten skattas utan sig själv, mot {V['mae_naive_years']} år för att gissa medelåret: seriationen ordnar stenarna, men den daterar inte en enskild sten mycket bättre än en gissning.

## 6. Diskussion

**Vad fyndet säger.** Språket, formlerna och innehållet förändrades i samma följd som ornamentiken i Uppland, och det håller lika starkt i två halvor av materialet. Eftersom ornamentiken inte ingår är det ett stöd för Gräslunds relativa kronologi som bygger på andra iakttagelser än hennes egna. Det står sig också utan korsen, som är en del av bilden, utan Ingvars- och Englandsstenarna, som annars kunde förankra tiden, och utan de stavningsdrag vars förändring mäts för sig.

**Mot tidigare forskning.** Stilkronologin är den grund de flesta dateringar av svenska runstenar vilar på (Gräslund 2006). Resultatet säger att den inte bara är en ordning av ornament: språk och innehåll följer samma tid. I Södermanland, där kronologin tillämpas men inte byggdes, finns samma följd men ungefär hälften så stark.

**Svagheter, i ordning efter vikt.**

1. **Följden går mellan ristare.** Inom en och samma ristare är korrelationen bara {d2(VR['within_carver']['rho'])}. Ornament och språk följer båda ristaren, och ristarna verkade vid olika tider; en del av överensstämmelsen kan därför vara att seriationen ordnar ristare. Inom härad står den sig ({d2(VR['within_district']['rho'])}), så det är inte en ordning av bygder.
2. **Inte förregistrerad.** Seriationen i Uppland var känd när planen för halvorna och Södermanland låstes. Halvorna och Södermanland är därför det egentliga provet.
3. **Södermanland kan vara geografi.** Med latituden konstant är korrelationen {d2(SO['partial_rho'])}, under planens gräns.
4. **Inte en datering.** Medelfelet för årtal är bara något bättre än att gissa medelåret.

**Vad som skulle fälla fyndet.** Att korrelationen försvann inom ristare också i ett större material med fler ristare som verkade länge, eller att en datering oberoende av både ornament och språk gav en annan följd.

## 7. Slutsats

Ordnade efter språk, formler och innehåll hamnar Upplands runstenar i samma följd som i stilkronologin, rho {d2(V['rho'])}, och det håller i båda halvorna. Det är ett oberoende stöd för den relativa kronologin, men ordningen går till stor del mellan ristare, och i Södermanland är den svagare och delvis geografisk. Nästa steg är att pröva seriationen inom ristare som verkade under lång tid, och i Östergötland och Västergötland när dateringen där blir säkrare.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 31 oktober 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod, analysplanen och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Seriationen: `r/chronology.R` (resultat `chronology.json` under materialets version `{FP}`).
- Planen för halvorna och Södermanland: `analysplaner/2026-10-31-seriation-halvor-sodermanland.md`; koden `utdata/seriation/replikering.R`, resultaten `replikering.json` och `replikering_resultat.md`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_seriation.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer.
- I Vitki visas seriationen under Statistik, Datering.

## Referenser

- Greenacre, M. 2007. *Correspondence Analysis in Practice*. 2 uppl. Boca Raton: Chapman & Hall/CRC.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Nenadić, O. & Greenacre, M. 2007. Correspondence analysis in R, with two- and three-dimensional graphics: the ca package. *Journal of Statistical Software* 20 (3).
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.

:::box Det viktigaste i korthet
- Det som står på stenarna förändrades i samma takt som ornamentiken: två oberoende klockor som visar ungefär samma tid.
- Det ger stilkronologin ett stöd som inte bygger på ornamenten själva.
- Klockorna går mest mellan ristarna, inte inom dem, och de räcker inte för att datera en enskild sten.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Partially tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, seriation, correspondence analysis, stylistic chronology, dating, Uppland, Södermanland. Competing interests: none. Funding: none.*

## Abstract

**What has not been tested.** The seriation in Uppland was not pre-registered, and it has no fixed series of sensitivity analyses like the project's associations between two traits; the halves and a replication in Södermanland were tested under a plan locked before the run.
**Background and aim.** The runestones of Uppland are dated relatively by their ornament, following Anne-Sofie Gräslund's stylistic chronology. The question here is whether the stones fall in the same sequence when ordered by something entirely different: the language, the formulas and the content.
**Material.** {CH['n_stones']} runestones in Uppland with at least four of {CH['n_attributes']} traits, {CH['n_dated']} of them with a style group; for the replication {SO['n_stones']} stones in Södermanland, {SO['n_dated']} with a style group. From the Scandinavian Runic-text Database (Rundata).
**Method.** Correspondence analysis of a table of stones and traits, without the style group; the stones' position on the first axis is compared with the style group's midpoint (Spearman's rank correlation). The halves and Södermanland with the same method, Holm-corrected.
**Results.** In Uppland rho = {V['rho']:.2f}, {V['partial_rho']:.2f} with latitude held constant. Half A {HA['rho']:.2f}, half B {HB['rho']:.2f}, both Holm-corrected p below 10⁻¹⁷. Södermanland {SO['rho']:.2f}, Holm-corrected p = {pexp(SO['p_holm'], True)}, but {SO['partial_rho']:.2f} with latitude held constant. Within hundreds {VR['within_district']['rho']:.2f}, within one and the same carver only {VR['within_carver']['rho']:.2f}.
**Conclusion.** Language and content carry the same temporal sequence as the ornament in Uppland, and that is support for the stylistic chronology independent of it. The sequence runs largely between carvers rather than within them, and it is not enough to date individual stones.

## 1. Introduction

The Viking-Age runestones of Uppland are dated relatively by their ornament, in Anne-Sofie Gräslund's style groups from RAK and Fp to Pr1–Pr5 (Gräslund 2006). The chronology rests on how the rune animal and the animal heads are shaped, not on the language or on what the text says. If language and content changed over the same time, the stones should fall in roughly the same sequence when ordered by them, and that would be support for the chronology not resting on the same observations. If two kinds of observation that have nothing to do with each other give the same order, it is hard to explain otherwise than that both follow time.

Seriation by correspondence analysis is a common method of relative dating in archaeology (Greenacre 2007). The aim here is to test whether language, formulas and content give the same sequence as the stylistic chronology, whether it holds in two halves of the material and whether it applies also outside Uppland, where the chronology was not built.

## 2. Pre-registration: what was fixed in advance and what is exploratory

The seriation in Uppland was first made on 5 October 2026 as part of the project's survey, without a locked plan, and its value was known when the rest of the study was planned. It is therefore not pre-registered. The variants without crosses, without journeys abroad, without the traits that change over time and within hundreds and carvers (5.2) were computed at the same time and are exploratory.

On 31 October 2026 a plan for two tests was locked before they were run (SHA-256 checksum `{PLAN_SHA[:16]}…`): the seriation in each half of the stones of Uppland on its own, and the same seriation on the stones of Södermanland, which had not been seriated on their own. The halves hold when Holm p is below 0.05 and rho at least 0.3 in both. Södermanland is *replicated* by the same limits; if the correlation with latitude held constant is below 0.3, the association is said to be possibly geographical. A trial run reproduced Uppland's known value exactly before the tests were run.

## 3. Material

- **Source.** The Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University. The material was frozen for the analysis on 29 October 2026. Runestones only.
- **The traits.** Language traits (the spelling of certain sounds and words), five formulas (sponsor formula, monument, word order, carver's signature, prayer), cross, short-twig runes and content categories, as presence or absence per stone. Traits found on fewer than 15 stones are not counted, nor stones with fewer than four traits. The style group is not included.
- **Time** is the style group's midpoint after Gräslund (2006).
- **Uppland:** {CH['n_stones']} stones and {CH['n_attributes']} traits, {CH['n_dated']} stones with a style group. **Södermanland:** {SO['n_stones']} stones and {SO['n_attributes']} traits, {SO['n_dated']} with a style group.
- **The halves** are the project's fixed division parish by parish.

## 4. Method

**4.1 The seriation.** Correspondence analysis (the package ca; Nenadić & Greenacre 2007) of the table of stones and traits. The analysis places stones that have the same traits close together, and traits that tend to occur on the same stones close together; the first axis is the direction in the material that separates the stones most. The stones' position on the first axis is compared with the style group's midpoint by Spearman's rank correlation. The sign of the axis is arbitrary and is turned so that the correlation is positive.

**4.2 The geography.** Since language traits also differ between north and south, the partial correlation with latitude held constant is reported.

**4.3 The halves and Södermanland.** The same method, unchanged, on each half and on Södermanland, Holm-corrected over the three tests.

**4.4 The variants (exploratory).** The seriation without crosses, without journeys abroad, without the traits whose change over time is measured separately (dotted runes, the monophthong, the ós-rune) and without all of these, and the correlation within hundreds and within carvers with at least five dated stones.

**4.5 Deviations.** None from the plan.

## 5. Results

**5.1 Uppland and the halves.** In Uppland rho = {V['rho']:.2f} (uncorrected p = {pexp(V['p'], True)}) and {V['partial_rho']:.2f} with latitude held constant; latitude itself correlates only {V['lat_rho']:.2f} with the axis. Half A: {HA['n_dated']} dated stones, rho {HA['rho']:.2f}, with latitude held constant {HA['partial_rho']:.2f}. Half B: {HB['n_dated']} dated stones, rho {HB['rho']:.2f}, with latitude held constant {HB['partial_rho']:.2f}. Both Holm-corrected p below 10⁻¹⁷: the halves *hold*. The style groups on average along the axis: RAK {PS['RAK']['mean_score']:.2f}, Fp {PS['Fp']['mean_score']:.2f}, Pr1 {PS['Pr1']['mean_score']:.2f}, Pr2 {PS['Pr2']['mean_score']:.2f}, Pr3 {PS['Pr3']['mean_score']:.2f}, Pr4 {PS['Pr4']['mean_score']:.2f}, Pr5 {PS['Pr5']['mean_score']:.2f}: the sequence is that of the stylistic chronology, except that RAK and Fp change places. In plain words: if one orders the stones only by what is written and how, they fall in roughly the same order as when one orders them by the ornament; the association is moderately strong and equally strong in both halves.

{chart(False)}

**5.2 The variants (exploratory).** Without crosses {VR['no_cross']['rho']:.2f}, without journeys abroad {VR['no_anchor']['rho']:.2f}, without the traits that change over time {VR['no_changing']['rho']:.2f}, without all of these {VR['strict']['rho']:.2f}. Within hundreds ({VR['within_district']['groups']} hundreds) {VR['within_district']['rho']:.2f}; within carvers ({VR['within_carver']['groups']} carvers with at least five dated stones, {VR['within_carver']['n']} stones) only {VR['within_carver']['rho']:.2f}.

**5.3 Södermanland (replication).** {SO['n_dated']} dated stones: rho {SO['rho']:.2f}, Holm-corrected p = {pexp(SO['p_holm'], True)}; *replicated* by the plan's rule. With latitude held constant {SO['partial_rho']:.2f}, below the plan's limit of 0.3, so the association may be partly geographical. Within hundreds {SO['within_district']:.2f} ({SO['n_districts']} hundreds).

**5.4 Dating individual stones.** If the axis is used to estimate years, the mean error is {V['mae_loo_years']} years when each stone is estimated without itself, against {V['mae_naive_years']} years for guessing the mean year: the seriation orders the stones, but it does not date a single stone much better than a guess.

## 6. Discussion

**What the finding says.** Language, formulas and content changed in the same sequence as the ornament in Uppland, and it holds equally strongly in two halves of the material. Since the ornament is not included, it is support for Gräslund's relative chronology resting on other observations than her own. It also holds without the crosses, which are part of the picture, without the Ingvar and England stones, which could otherwise anchor the time, and without the spelling traits whose change is measured separately.

**Against earlier research.** The stylistic chronology is the basis on which most datings of Swedish runestones rest (Gräslund 2006). The result says that it is not only an ordering of ornament: language and content follow the same time. In Södermanland, where the chronology is applied but was not built, the same sequence is found but about half as strong.

**Weaknesses, in order of weight.**

1. **The sequence runs between carvers.** Within one and the same carver the correlation is only {VR['within_carver']['rho']:.2f}. Ornament and language both follow the carver, and the carvers worked at different times; part of the agreement may therefore be that the seriation orders carvers. Within hundreds it holds ({VR['within_district']['rho']:.2f}), so it is not an ordering of districts.
2. **Not pre-registered.** The seriation in Uppland was known when the plan for the halves and Södermanland was locked. The halves and Södermanland are therefore the actual test.
3. **Södermanland may be geography.** With latitude held constant the correlation is {SO['partial_rho']:.2f}, below the plan's limit.
4. **Not a dating.** The mean error for years is only somewhat better than guessing the mean year.

**What would overturn the finding.** If the correlation disappeared within carvers also in a larger material with more carvers who worked long, or if a dating independent of both ornament and language gave another sequence.

## 7. Conclusion

Ordered by language, formulas and content, the runestones of Uppland fall in the same sequence as in the stylistic chronology, rho {V['rho']:.2f}, and it holds in both halves. That is independent support for the relative chronology, but the order runs largely between carvers, and in Södermanland it is weaker and partly geographical. The next step is to test the seriation within carvers who worked over a long time, and in Östergötland and Västergötland when the dating there becomes more secure.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 31 October 2026. No release with a DOI exists yet; when one is made, the report will refer to it. All code, the analysis plan and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The seriation: `r/chronology.R` (results `chronology.json` under the material's version `{FP}`).
- The plan for the halves and Södermanland: `analysplaner/2026-10-31-seriation-halvor-sodermanland.md`; the code `utdata/seriation/replikering.R`, the results `replikering.json` and `replikering_resultat.md`.
- The report is built by `utdata/blogg/build/build_rapport_seriation.py`, which reads every number from the result files and stops if anything disagrees.
- In Vitki the seriation is shown under Statistics, Dating.

## References

- Greenacre, M. 2007. *Correspondence Analysis in Practice*. 2nd ed. Boca Raton: Chapman & Hall/CRC.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Nenadić, O. & Greenacre, M. 2007. Correspondence analysis in R, with two- and three-dimensional graphics: the ca package. *Journal of Statistical Software* 20 (3).
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.

:::box The essentials
- What is written on the stones changed at the same pace as the ornament: two independent clocks showing roughly the same time.
- That gives the stylistic chronology support that does not rest on the ornaments themselves.
- The clocks run mostly between the carvers, not within them, and they are not enough to date a single stone.
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
assert "## Sammanfattning\n\n**Vad som inte är prövat.**" in body  # mallen v2: status först för allt utom nivå 1
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Delvis prövat fynd. Rapportversion 1, 2026-10-31. Tidslinje: ")

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Datering och stil", "Språk och stavning"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_seriation.json")
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
                 "topic": "Rapport|seriation", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
