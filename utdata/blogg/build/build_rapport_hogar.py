"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4): "Runstenar står oftare vid stora gravhögar än vid små"
(sv + en). Prov H3 i den låsta planen analysplaner/2026-11-18-hogarna.md (089fcfb5) och den låsta tilläggsplanen för
känslighetsanalyserna analysplaner/2026-11-18-hogarna-trappan.md (53f11fa6). Alla siffror asserteras mot
utdata/hogar/resultat.json och utdata/hogar/resultat_trappan.json, planerna och källorna.
    ../../../.venv/bin/python build_rapport_hogar.py [--write | --update DOC]"""
import datetime as dt
import hashlib
import json
import math
import os
import re
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

# TILLBAKADRAGEN 2026-11-18: huvudfyndet höll inte med grupper av högar som enhet (plan 6870d6cd, utdata/hogar/resultat_grupper.json,
# robust = false). Byggaren får inte skriva eller uppdatera utkastet med det gamla påståendet förrän Viktor har beslutat
# om utkastet (radera, eller skriv om som negativ metodrapport).
_g = json.load(open(os.path.join(ROOT, "utdata", "hogar", "resultat_grupper.json"), encoding="utf-8"))
if not _g.get("robust", True):
    sys.exit("Rapporten är tillbakadragen (resultat_grupper.json: robust = false) – byggaren stoppar. Se mounds-study.")
from utdata.norge.citat import letters  # noqa: E402

APP_VERSION = json.load(open(os.path.join(ROOT, "web", "package.json"), encoding="utf-8"))["version"]
assert APP_VERSION == "3.1.0"
REPORT_VERSION = 1
TODAY = "2026-11-18"  # rapportversionens datum, fast i byggaren (mallen version 3)
SLUG = "runstenar-vid-stora-gravhogar"
TL_SV = ("registret hämtades 2026-11-02; analysplanen låstes 2026-11-18; tilläggsplanen med känslighetsanalyserna låstes "
         "2026-11-18")
TL_EN = ("the register was extracted 2026-11-02; the analysis plan was locked 2026-11-18; the addendum plan with the "
         "sensitivity analyses was locked 2026-11-18")

# ---- the plans
def sha(name):
    return hashlib.sha256(open(os.path.join(ROOT, "analysplaner", name), "rb").read()).hexdigest()


SHA1, SHA2 = sha("2026-11-18-hogarna.md"), sha("2026-11-18-hogarna-trappan.md")
assert SHA1.startswith("089fcfb5") and SHA2.startswith("53f11fa6")
PLAN1 = open(os.path.join(ROOT, "analysplaner", "2026-11-18-hogarna.md"), encoding="utf-8").read()
PLAN2 = open(os.path.join(ROOT, "analysplaner", "2026-11-18-hogarna-trappan.md"), encoding="utf-8").read()
assert "uttag 2026-11-02" in PLAN1 and "**H3. Runstenarna:** om det står en runsten inom 500 m." in PLAN1
assert "T1 har oddskvot > 1 i båda halvorna" in PLAN2 and "tredjedel av tätheten" in PLAN2

# ---- the results
R1 = json.load(open(os.path.join(ROOT, "utdata", "hogar", "resultat.json"), encoding="utf-8"))
R2 = json.load(open(os.path.join(ROOT, "utdata", "hogar", "resultat_trappan.json"), encoding="utf-8"))
assert R1["sha"] == "089fcfb5" and R2["sha"] == "53f11fa6"
H3 = R1["prov"]["H3_runsten"]
assert H3["haller"] and not R1["prov"]["H1_husby_tuna"]["haller"] and not R1["prov"]["H2_kultplats"]["haller"]
assert (R1["hogar"], R1["med_diameter"], R1["stora"], R1["mindre"]) == (17531, 11072, 2017, 9055)
assert R2["robust"] and all(R2["steg"].values())
assert R2["tathet_tredjedelar"] == [0.0, 0.0] and R2["landskap_none"] == 18
assert (R2["runstenar"], R2["pa_plats"], R2["kyrkor"]) == (2318, 1097, 444)
T = {k: R2[k] for k in ("T0", "T1", "T2", "T3", "T4")}
assert abs(T["T0"]["or"] - math.exp(H3["stat"])) < 1e-9  # T0 reproduces H3
HA, HF = R2["T1_halvor"], R2["T1_halvor_forsta_korningen"]
assert R2["T6"]["250"]["or"] > T["T1"]["or"] > R2["T6"]["1000"]["or"]  # "Effekten är störst nära högen"
assert all(HA[h]["or"] > 1 and HA[h]["p"] < 0.05 for h in "AB")
PLS = R2["per_landskap_pa_plats"]
LOPO = R2["T5"]
assert all(v["or"] > 1 for v in LOPO.values()) and all(v["or"] > 1 for v in R2["T6"].values())
assert all(v["p"] < 0.01 for v in LOPO.values())  # "med p < 0,01 i varje fall"


def c(v, d=2):
    return f"{v:.{d}f}".replace(".", ",")


def e(v, d=2):
    return f"{v:.{d}f}"


def pv(p, sv=True):
    s = "p < 0,001" if p < 0.001 else f"p = {p:.3f}".replace(".", ",")
    return s if sv else s.replace(",", ".")


def ci(x, sv=True):
    f = c if sv else e
    return f"{f(x['ci95'][0])}–{f(x['ci95'][1])}"


def pct(a, b):
    return 100 * a / b


# pooled shares (Simpson): large mounds look LESS often near a stone, because most of them lie in Skåne and Halland
POOL = (pct(T["T1"]["stora_med_sten"], T["T1"]["stora"]), pct(T["T1"]["mindre_med_sten"], T["T1"]["mindre"]))
assert (T["T1"]["stora_med_sten"], T["T1"]["mindre_med_sten"]) == (47, 356) and [round(v, 1) for v in POOL] == [2.3, 3.9]
SKHA = PLS["Skåne"]["stora"] + PLS["Halland"]["stora"]
assert SKHA == 1605 and PLS["Skåne"]["stora_med_sten"] + PLS["Halland"]["stora_med_sten"] + PLS["Skåne"]["mindre_med_sten"] + PLS["Halland"]["mindre_med_sten"] == 0
THREE = PLS["Uppland"]["stora_med_sten"] + PLS["Medelpad"]["stora_med_sten"] + PLS["Södermanland"]["stora_med_sten"]
assert (PLS["Uppland"]["stora_med_sten"], PLS["Medelpad"]["stora_med_sten"], PLS["Södermanland"]["stora_med_sten"], THREE) == (20, 10, 9, 39)
UP, SO, ME = PLS["Uppland"], PLS["Södermanland"], PLS["Medelpad"]
assert [round(100 * UP["andel_stora"]), round(100 * UP["andel_mindre"])] == [27, 14]
assert [round(100 * SO["andel_stora"]), round(100 * SO["andel_mindre"])] == [28, 10]
assert [round(100 * ME["andel_stora"]), round(100 * ME["andel_mindre"], 1)] == [16, 1.8]
# the old example stones stand in churchyards (moved); the examples used stand where they were raised
from src import r_bridge  # noqa: E402
RD = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
assert all(r_bridge.is_moved(RD[s]) for s in ("Vg 44", "Vg 45", "Ög 181"))
assert not any(r_bridge.is_moved(RD[s]) for s in ("Sö 137", "Sö 138", "Sö 202", "U Fv1975;169"))
assert "ok haug þenna" in RD["U 135"]["normalization"] and "ok haug gæra" in RD["U 269"]["normalization"]
# Rundata as described in METHODS.md (as in the earlier reports)
assert "version 2014 med RUNDATA.xls från 2018" in open(os.path.join(ROOT, "METHODS.md"), encoding="utf-8").read()

# ---- the literature, checked against the journals' text
SOK = sqlite3.connect("/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite")


def jcheck(key, page, *frags):
    text = letters(SOK.execute("select text from pages where key=? and page=?", (key, page)).fetchone()[0])
    for f in frags:
        assert letters(f) in text, (key, page, f)


jcheck("1991_litt", 38, "136", "Mats G. Larsson, Runstenar och utlandsfärder")
jcheck("1991_litt", 40, "138", "att storhögar förekommer betydligt oftare", "på bebyggelseenhet med utlandsfararstenar",
       "än i referensgruppens bebyggelseenhet", "väljer Larsson slumpmässigt ut en referens")
jcheck("1991_litt", 41, "139", "Per H. Ramqvist")
jcheck("1917_127", 17, "142", "kung Nordians hög", "vid Ås-Husby")

GLOSS_SV = "[https://vitkirunor.se/forskningsrapporter/begrepp](https://vitkirunor.se/forskningsrapporter/begrepp)"
GLOSS_EN = "[https://vitkirunor.se/en/forskningsrapporter/begrepp](https://vitkirunor.se/en/forskningsrapporter/begrepp)"
FAM_SV = "[https://vitkirunor.se/forskningsrapporter/familjegrupper-vid-gravfalten](https://vitkirunor.se/forskningsrapporter/familjegrupper-vid-gravfalten)"
FAM_EN = "[https://vitkirunor.se/en/forskningsrapporter/familjegrupper-vid-gravfalten](https://vitkirunor.se/en/forskningsrapporter/familjegrupper-vid-gravfalten)"
ART_SV = "[https://vitkirunor.se/artiklar/kullarna-vid-skogens-rand](https://vitkirunor.se/artiklar/kullarna-vid-skogens-rand)"
ART_EN = "[https://vitkirunor.se/en/artiklar/kullarna-vid-skogens-rand](https://vitkirunor.se/en/artiklar/kullarna-vid-skogens-rand)"
GITHUB = "[https://github.com/Precatio/runes](https://github.com/Precatio/runes)"
FAMR = json.load(open(os.path.join(ROOT, "utdata", "familjens_plats", "familjens_plats.json"), encoding="utf-8"))
assert {t["key"]: t for t in FAMR["tests"]}["y2_hog"]["status"] == "ingen skillnad påvisad"

title = "Runstenar står oftare vid stora gravhögar än vid små – oddsen tre gånger så stora, också bland stenar på sin plats"
title_en = "Runestones stand by large burial mounds more often than by small ones – three times the odds, also among stones in their original place"
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/forskningsrapporter/{SLUG}")
summary = ("Förregistrerad studie av 11 072 fristående gravhögar med känd storlek i Sverige. Inom samma landskap har en "
           "hög som är minst 20 meter bred ungefär tre gånger så stora odds att ha en runsten inom 500 meter som en mindre hög, "
           "också när bara stenar på sin ursprungliga plats räknas, när högar nära medeltida kyrkor tas bort och när stora och "
           "små högar jämförs inom samma socken. Mönstret bärs av Uppland, Medelpad och Södermanland.")
summary_en = ("Pre-registered study of 11,072 free-standing burial mounds of known size in Sweden. Within the same province, a "
              "mound at least 20 metres across has about three times the odds of a runestone within 500 metres compared with a "
              "smaller mound, also when only stones in their original place are counted, when mounds near medieval churches are "
              "removed and when large and small mounds are compared within the same parish. The pattern is carried by Uppland, "
              "Medelpad and Södermanland.")


def chart(sv):
    rows = [("Uppland", UP), ("Södermanland", SO), ("Medelpad", ME), ("Västergötland", PLS["Västergötland"]),
            ("Östergötland", PLS["Östergötland"])]
    out = [":::chart " + ("Figur 1. Gravhögar med en runsten på sin ursprungliga plats inom 500 meter" if sv else
                          "Figure 1. Burial mounds with a runestone in its original place within 500 metres")]
    for k, v in rows:
        out.append("# " + k)
        out.append(f"+{'Stor hög, minst 20 m' if sv else 'Large mound, at least 20 m'} | {100 * v['andel_stora']:.0f} | "
                   f"{v['stora_med_sten']} {'av' if sv else 'of'} {v['stora']}")
        out.append(f"{'Mindre hög' if sv else 'Smaller mound'} | {100 * v['andel_mindre']:.0f} | "
                   f"{v['mindre_med_sten']} {'av' if sv else 'of'} {v['mindre']}")
    out.append("Källa: Rundata (stenar på sin ursprungliga plats) och Riksantikvarieämbetets kulturmiljöregister. Procent. "
               "Diagram: Vitki, efter Rundata och Kulturmiljöregistret." if sv else
               "Source: Rundata (stones in their original place) and the Swedish National Heritage Board's Kulturmiljöregistret. "
               "Per cent. Chart: Vitki, after Rundata and Kulturmiljöregistret.")
    out.append(":::")
    return "\n".join(out)


def lopo(sv):
    f = c if sv else e
    items = sorted(LOPO.items(), key=lambda kv: kv[1]["or"])
    lo, hi = items[0], items[-1]
    return (lo[0], f(lo[1]["or"]), hi[0], f(hi[1]["or"]))


L_SV, L_EN = lopo(True), lopo(False)
assert L_SV[0] == "Medelpad" and L_SV[2] == "Uppland"

body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, gravhögar, storhögar, fornlämningar, landskap, Mantel–Haenszel, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Runstenar står ofta vid gravfält, och enskilda stenar står vid kända storhögar. Om runstenarna sökte sig till de stora högarna mer än till de små är inte mätt för hela landet. Studien jämför stora och små högar, med landskapet konstant.
**Material.** {R1['hogar']:,} fristående gravhögar i Riksantikvarieämbetets kulturmiljöregister, varav {R1['med_diameter']:,} med angiven diameter ({R1['stora']:,} minst 20 meter breda); {R2['runstenar']:,} svenska vikingatida runstenar med läge i Rundata, varav {R2['pa_plats']:,} på sin ursprungliga plats.
**Metod.** Mantel–Haenszels oddskvot för en runsten inom 500 meter, stor mot mindre hög, inom landskap; p ur omblandning av storleken inom landskapen. Ett förregistrerat huvudtest, därefter sex förregistrerade känslighetsanalyser där alla måste hålla.
**Resultat.** Med alla stenar är oddskvoten {c(T['T0']['or'])} (95 % {ci(T['T0'])}; {pv(H3['p'])}, Holm över planens tre test {pv(H3['p_holm'])}), i båda halvorna av materialet. Med bara stenar på sin plats {c(T['T1']['or'])} ({ci(T['T1'])}); utan högar inom 1 km från en medeltida kyrka {c(T['T2']['or'])}; stora mot små högar i samma socken {c(T['T3']['or'])}; med den lokala tätheten av runstenar och gravfält konstant {c(T['T4']['or'])}. Med vart och ett av landskapen utelämnat ligger oddskvoten mellan {L_SV[1]} och {L_SV[3]}. Underlaget är litet: {T['T1']['stora_med_sten']} stora högar har en sten på sin plats inom 500 meter, {THREE} av dem i Uppland, Medelpad och Södermanland.
**Slutsats.** I klartext: där det står runstenar har en stor gravhög ungefär tre gånger så stora odds att ha en runsten nära sig som en liten, och det beror inte på att stenar senare flyttades till kyrkor vid storhögarna. Studien visar läget, inte avsikten, och den kan inte säga om högarna var äldre än stenarna.

## 1. Inledning

Att runstenar ofta står vid gravfält är känt sedan länge. Gunnar Ekholm (1950) hävdade att de främst stod vid vägar och att gravfälten följde vägarna; Torun Zachrisson (1998) satte stenarna i samband med gård, gräns och gravfält; Lydia Klos (2009) har hävdat att de flesta restes vid gravfält. I en tidigare rapport visade vi att runstenar i grupp oftare än ensamma stenar står vid gravfält, men att närheten till en gravhög inte skilde dem åt ({FAM_SV}).

De stora högarna har en egen forskningshistoria. Sune Lindqvist (1917, s. 142) knöt storhögar som ”kung Nordians hög” vid Ås-Husby till kungsgårdarna. Mats G. Larsson (1990) fann, enligt Per H. Ramqvists recension, att storhögar förekommer betydligt oftare på de bebyggelseenheter som har stenar efter utlandsfarare än på bebyggelseenheter med andra runstenar i ett slumpvis valt jämförelseurval (Ramqvist 1991, s. 138). I den isländska traditionen låter Snorre Sturlasson i Ynglingasagan (kap. 8) Oden stifta att man skulle göra en hög efter förnäma män och resa bautastenar efter andra – en sen, lärd bild där hög och sten hör ihop.

Det som saknas är ett mått från högarnas sida, för hela landet: står runstenarna oftare vid de stora högarna än vid de små, i samma landskap och i samma socken, och håller det när de flyttade stenarna räknas bort? Det mäts här.

## 2. Förregistrering

Två planer låstes i projektets versionshantering innan något av proven räknades; kontrollsummor (SHA-256) nedan, filerna under Data och kod.

1. **Kullarna** (18 november 2026, `{SHA1[:8]}…`): tre test, Holm-korrigerade: storhögar nära Husby- och tunaorter (H1), nära kultplatsnamn (H2) och med en runsten inom 500 meter (H3). Hypotesen H3 ordagrant: ”om det står en runsten inom 500 m. Teststorhet: Mantel–Haenszel-oddskvoten stor mot mindre över landskapen; p ur samma omblandning.” Ett prov håller när Holm-justerat p < 0,05, riktningen är densamma i båda halvorna och med gränsen 15 och 30 meter. Inget annat än antalet högar, deras storlek och namn var sett före låsningen.
2. **Tilläggsplanen** (18 november 2026, `{SHA2[:8]}…`): sex känslighetsanalyser av H3, skrivna när H3:s resultat var känt men innan någon av dem räknades. Planen anger misstanken den skulle pröva: att stenar flyttats till kyrkor som byggts vid storhögar. Mönstret räknas som robust bara om alla steg håller (avsnitt 4.3).

H3 är det konfirmatoriska testet. Känslighetsanalyserna är förregistrerade men gjorda på samma material. H1 och H2 höll inte och redovisas i den populära artikeln, inte här.

## 3. Material

- **Högarna.** Riksantikvarieämbetets kulturmiljöregister, lämningstypen Hög, hämtat 2 november 2026: {R1['hogar']:,} fristående högar med läge. Högar som ingår i gravfält finns inte som egna poster och ingår inte. Diametern läses ur beskrivningen (”20 m diam”, ”20 m i diam”); {R1['med_diameter']:,} högar har en angiven diameter. **Stor hög:** minst 20 meter ({R1['stora']:,}); **mindre:** under 20 meter ({R1['mindre']:,}). Högar utan angiven diameter ingår inte.
- **Landskap.** Registrets län är inte landskap. Varje hög får landskapet för den socken (Institutet för språk och folkminnen) vars mittpunkt ligger närmast; {R2['landskap_none']} högar ligger närmast en socken utan landskap och bildar en egen grupp.
- **Runstenarna.** Samnordisk runtextdatabas (Rundata), version 2014 med RUNDATA.xls uppdaterad 2018: {R2['runstenar']:,} svenska vikingatida runstenar med koordinat. **På sin ursprungliga plats:** de {R2['pa_plats']:,} som inte räknas som flyttade – en sten räknas som flyttad när Rundatas placering säger det, när platsen är en kyrka, kyrkogård, ett slott eller ett museum, eller när placeringstexten nämner en annan plats än fyndplatsen.
- **Medeltida kyrkor:** {R2['kyrkor']} kyrkobyggnader uppförda före 1350 enligt Wikidata, långt ifrån alla. **Gravfält:** kulturmiljöregistrets gravfält.
- **Skåne och Halland.** Rundatas svenska material innehåller inga runstenar i Skåne och Halland (de förs till det danska), där {SKHA:,} av de {R1['stora']:,} stora högarna ligger. Där kan sambandet inte prövas; de högarna bidrar inte till oddskvoten.

## 4. Metod

Statistiska begrepp förklaras i ordlistan, {GLOSS_SV}.

**4.1 Testet.** För varje hög noteras om det står en runsten inom 500 meter. Mantel–Haenszels oddskvot väger samman fyrfältstabellerna (stor eller mindre hög, sten eller inte) inom varje landskap, så att landskap med många stenar och många små högar inte jämförs med landskap utan stenar. Ett 95-procentsintervall beräknas med Robins, Breslow och Greenlands (1986) metod. p-värdet är tvåsidigt: storleksetiketten blandas om mellan högarna inom varje landskap 10 000 gånger, med ett slumpfrö ur planens kontrollsumma.

**4.2 Halvorna.** Inom varje län delas socknarna växelvis i två halvor i namnordning; testet ska ge samma riktning i båda.

**4.3 Känslighetsanalyserna** (tilläggsplanen). T1: bara stenar på sin ursprungliga plats, också i båda halvorna. T2: som T1 utan högar inom 1 km från en medeltida kyrka. T3: som T1 men jämfört inom socken i stället för landskap. T4: som T1 inom grupper av landskap × lokal täthet av runstenar (1–5 km från högen, så att måttet inte innehåller utfallet) × gravfält inom 1 km. T5: T1 med vart och ett av de landskap som har minst 10 stora högar utelämnat. T6: T1 med radien 250 och 1 000 meter. Kraven: T1–T4 oddskvot över 1 och p < 0,05; T1 över 1 i båda halvorna med p < 0,05 i en halva med minst 50 stora högar; T5 över 1 med varje landskap utelämnat; T6 över 1. Alla krav ska uppfyllas, så ingen korrektion för flera test görs.

**4.4 Avvikelser från planerna.**
1. Huvudplanen nämnde formen ”20 m diam”; registret skriver oftast ”20 m i diam”. Den formen lades till innan något test räknades.
2. T4: tätheten skulle delas i tredjedelar, men de flesta högar har ingen runsten 1–5 km bort, så två av gränserna blev 0. Tätheten delades därför i ”inga” och ”några” stenar; regeln skrevs i koden före körningen men står inte i planen.
3. Halvorna i T1: den första körningen delade socknarna växelvis bland högarna med diameter, inte bland alla högar som planen föreskriver (”som förut”). Det rättades; båda redovisas i 5.3.
4. Efter den första körningen lades 95-procentsintervall och antal per landskap till som beskrivning. Testen kördes om med samma slumpfrö och gav samma oddskvoter och p-värden.

## 5. Resultat

**5.1 Huvudtestet.** Med alla runstenar med läge är oddskvoten {c(T['T0']['or'])} (95 % {ci(T['T0'])}; {pv(H3['p'])}; Holm över planens tre test {pv(H3['p_holm'])}). Båda halvorna: {c(math.exp(H3['halvor']['A']['stat']))} ({pv(H3['halvor']['A']['p'])}, {H3['halvor']['A']['stora']:,} stora högar) och {c(math.exp(H3['halvor']['B']['stat']))} ({pv(H3['halvor']['B']['p'])}, {H3['halvor']['B']['stora']:,}). Testet håller enligt planen.

{chart(True)}

I klartext: i Uppland står det en runsten på sin ursprungliga plats inom 500 meter från ungefär var fjärde stor hög ({UP['stora_med_sten']} av {UP['stora']}) men från ungefär var sjunde mindre ({UP['mindre_med_sten']} av {UP['mindre']:,}); i Södermanland var fjärde mot var tionde; i Medelpad var sjätte mot knappt var femtionde. Räknat över hela landet utan landskapen ser det ut tvärtom – {c(POOL[0], 1)} mot {c(POOL[1], 1)} procent – eftersom {SKHA:,} av de stora högarna ligger i Skåne och Halland, där materialet saknar runstenar. Därför jämförs högarna inom landskapen.

**5.2 Planens robusthetsprov.** Med gränsen 15 meter är oddskvoten {c(math.exp(H3['troskel_15_30']['15']))}, med 30 meter {c(math.exp(H3['troskel_15_30']['30']))}: samma riktning.

**5.3 Känslighetsanalyserna, steg för steg.**
- T1, bara stenar på sin ursprungliga plats: {c(T['T1']['or'])} (95 % {ci(T['T1'])}; {pv(T['T1']['p'])}). {T['T1']['stora_med_sten']} av {R1['stora']:,} stora och {T['T1']['mindre_med_sten']} av {R1['mindre']:,} mindre högar har en sådan sten inom 500 meter. Halvorna enligt planen: {c(HA['A']['or'])} ({pv(HA['A']['p'])}, {HA['A']['stora']:,} stora högar) och {c(HA['B']['or'])} ({pv(HA['B']['p'])}, {HA['B']['stora']:,}); i den första körningens halvor {c(HF['A']['or'])} ({pv(HF['A']['p'])}) och {c(HF['B']['or'])} ({pv(HF['B']['p'])}). Håller.
- T2, utan de {R2['T2']['borttagna_hogar']} högarna inom 1 km från en medeltida kyrka: {c(T['T2']['or'])} ({ci(T['T2'])}; {pv(T['T2']['p'])}). Håller.
- T3, inom socken: {c(T['T3']['or'])} ({ci(T['T3'])}; {pv(T['T3']['p'])}). Håller.
- T4, med lokal täthet och gravfält konstanta: {c(T['T4']['or'])} ({ci(T['T4'])}; {pv(T['T4']['p'])}). Håller.
- T5, ett landskap i taget utelämnat: oddskvoten ligger mellan {L_SV[1]} (utan {L_SV[0]}) och {L_SV[3]} (utan {L_SV[2]}), med p < 0,01 i varje fall. Utan Skåne är bara {round(100 * LOPO['Skåne']['kvar_av_stora'])} procent av de stora högarna kvar, men de bidrar ändå inte. Håller.
- T6, radien: {c(R2['T6']['250']['or'])} vid 250 meter och {c(R2['T6']['1000']['or'])} vid 1 000 meter. Effekten är störst nära högen. Håller.

**5.4 Exempel** (beskrivande). Stenarna vid Skalunda hög (Vg 44, Vg 45) och Ledbergs kulle (Ög 181) står på kyrkogårdar och räknas inte i T1–T6. Bland stenar på sin plats står U Fv1975;169 vid Tjärkullen, Borresta i Orkesta socken (35 meter); Sö 137 och Sö 138 vid Tingshögen i Ludgo (30 meter); och Sö 202 i Östa, Ytterselö, nära en 25 meter bred hög.

## 6. Diskussion

**Vad fyndet säger.** Runstenarna står inte bara vid gravfälten utan oftare vid de stora högarna än vid de små i samma bygd. Det är inte en följd av att stenar senare samlades vid kyrkor som byggts vid storhögar: de flyttade stenarna och högarna nära kyrkor är borttagna utan att mönstret ändras, och det håller inom samma socken.

**Mot tidigare forskning.** Fyndet går i samma riktning som Larssons (1990) iakttagelse att storhögar är vanligare vid stenar efter utlandsfarare, men mäter från andra hållet och för alla runstenar: det är storhögarna som oftare har en sten nära sig. Att grupper av stenar inte skilde sig från ensamma stenar i närheten till gravhögar ({FAM_SV}) är ingen motsägelse: där jämfördes stenar, här högar av olika storlek. Snorres bild av hög och bautasten som två former av minne passar med läget, men en text från 1200-talet kan inte styrka vad man tänkte på 1000-talet.

**Svagheter, i ordning efter vikt.**
1. **Litet antal.** {T['T1']['stora_med_sten']} stora högar har en sten på sin plats nära sig, {THREE} av dem i tre landskap. Mönstret håller med vart och ett av landskapen utelämnat, men inte prövat med Uppland, Medelpad och Södermanland utelämnade tillsammans – utan dem finns nästan inga fall kvar.
2. **Ingen datering.** Registret anger sällan när en hög byggdes. En stor hög vid en runsten kan vara samtida med stenen; stenarna U 135 (Broby) och U 269 (Harby) säger att de efterlevande gjorde en hög vid stenen. Studien kan därför inte skilja mellan att stenarna sökte sig till äldre högar och att samma familjer reste både hög och sten.
3. **Storleken ur texten.** Diametern finns för {round(100 * R1['med_diameter'] / R1['hogar'])} procent av högarna. Om storhögar oftare beskrivs med mått i bygder med runstenar påverkar det jämförelsen; det har inte prövats.
4. **Flyttade stenar och kyrkor.** Rundatas placering är inte fullständig, och Wikidatas medeltida kyrkor är långt ifrån alla. En kontroll mot Runor, Riksantikvarieämbetets runregister, har inte gjorts.

**Vad som skulle fälla fyndet.** Att mönstret försvann med flyttade stenar enligt Runor, att det saknades i danskt material (Skåne, Danmark) med samma metod, eller att daterade storhögar vid runstenar visade sig vara byggda långt efter stenarna.

## 7. Slutsats

Bland Sveriges fristående gravhögar har de stora ungefär tre gånger så stora odds som de små att ha en runsten nära sig, inom samma landskap och inom samma socken, och med bara stenar på sin ursprungliga plats. Mönstret bärs av Uppland, Medelpad och Södermanland.

## Data och kod

Analysen kördes i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([https://vitkirunor.se](https://vitkirunor.se)). Kod, analysplaner och resultatfiler finns öppet under GPL-3.0 i {GITHUB}.

- Analysplanerna: `analysplaner/2026-11-18-hogarna.md` och `analysplaner/2026-11-18-hogarna-trappan.md`.
- Skripten: `utdata/hogar/analys.py` (huvudtestet, `resultat.json`) och `utdata/hogar/trappan.py` (känslighetsanalyserna, `resultat_trappan.json`).
- Data: Rundata (`data/rundata.json`); kulturmiljöregistret, uttag 2026-11-02 (högarna i `downloads/hogar/hogar.csv` utanför versionshanteringen, gravfälten i `data/raa/lamningar.csv`); Wikidatas kyrkor och socknarna (Institutet för språk och folkminnen) som i projektets övriga analyser.
- Köra om, från projektmappen: `.venv/bin/python utdata/hogar/analys.py` och `.venv/bin/python utdata/hogar/trappan.py`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_hogar.py`, som läser varje siffra ur resultatfilerna och planerna och stannar om något inte stämmer.
- Den populära artikeln: {ART_SV}.

## Referenser

- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, s. 137–147.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Kvant, V. 2026. Runstenarna samlas i familjegrupper vid gravfälten. Forskningsrapport. {FAM_SV}
- Larsson, M. G. 1990. *Runstenar och utlandsfärder. Aspekter på det senvikingatida samhället med utgångspunkt i de fasta fornlämningarna*. Acta Archaeologica Lundensia, Series in 8°, 18. Lund.
- Lindqvist, S. 1917. Ottarshögen i Vendel. *Fornvännen* 12, s. 127–143.
- Mantel, N. & Haenszel, W. 1959. Statistical aspects of the analysis of data from retrospective studies of disease. *Journal of the National Cancer Institute* 22 (4), s. 719–748.
- Ramqvist, P. H. 1991. Recension av M. G. Larsson, *Runstenar och utlandsfärder*. *Fornvännen* 86, s. 136–139.
- Riksantikvarieämbetet. Kulturmiljöregistret (fornlämningar), uttag 2026-11-02.
- Robins, J., Breslow, N. & Greenland, S. 1986. Estimators of the Mantel–Haenszel variance consistent in both sparse data and large-strata limiting models. *Biometrics* 42 (2), s. 311–323.
- Samnordisk runtextdatabas (Rundata), version 2014 med RUNDATA.xls uppdaterad 2018. Institutionen för nordiska språk, Uppsala universitet. Open Database License 1.0 / Database Contents License 1.0.
- Snorre Sturlasson. *Ynglinga saga*, kap. 8. I: *Heimskringla*, utg. N. Linder & H. A. Haggson, 1869–1872.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholms universitet.

:::box Det viktigaste i korthet
- Runstenarna står oftare vid de stora gravhögarna än vid de små i samma bygd – oddsen är ungefär tre gånger så stora.
- Det beror inte på att stenar senare flyttades till kyrkor vid storhögarna; mönstret håller med bara stenar på sin plats och inom samma socken.
- Underlaget är litet och bärs av Uppland, Medelpad och Södermanland, och studien kan inte säga om högarna var äldre än stenarna.
:::"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. The English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, burial mounds, great mounds, ancient monuments, landscape, Mantel–Haenszel, pre-registration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** Runestones often stand by grave fields, and individual stones stand by well-known great mounds. Whether runestones sought out large mounds more than small ones has not been measured for the whole country. The study compares large and small mounds, holding the province constant.
**Material.** {R1['hogar']:,} free-standing burial mounds in the Swedish National Heritage Board's Kulturmiljöregistret, {R1['med_diameter']:,} of them with a stated diameter ({R1['stora']:,} at least 20 metres across); {R2['runstenar']:,} Swedish Viking-Age runestones with a position in Rundata, {R2['pa_plats']:,} of them in their original place.
**Method.** The Mantel–Haenszel odds ratio for a runestone within 500 metres, large against smaller mound, within provinces; p from permuting size within provinces. One pre-registered main test, then six pre-registered sensitivity analyses, all of which must hold.
**Results.** With all stones the odds ratio is {e(T['T0']['or'])} (95 % {ci(T['T0'], False)}; {pv(H3['p'], False)}, Holm over the plan's three tests {pv(H3['p_holm'], False)}), in both halves of the material. With only stones in their original place {e(T['T1']['or'])} ({ci(T['T1'], False)}); without mounds within 1 km of a medieval church {e(T['T2']['or'])}; large against small mounds in the same parish {e(T['T3']['or'])}; with the local density of runestones and grave fields held constant {e(T['T4']['or'])}. With each province left out in turn the odds ratio lies between {L_EN[1]} and {L_EN[3]}. The basis is small: {T['T1']['stora_med_sten']} large mounds have a stone in its original place within 500 metres, {THREE} of them in Uppland, Medelpad and Södermanland.
**Conclusion.** In plain words: where there are runestones, a large burial mound has about three times the odds of a small one of having a runestone near it, and this is not because stones were later moved to churches by the great mounds. The study shows the placement, not the intention, and it cannot say whether the mounds were older than the stones.

## 1. Introduction

That runestones often stand by grave fields has long been known. Gunnar Ekholm (1950) argued that they stood mainly by roads and that the grave fields followed the roads; Torun Zachrisson (1998) related the stones to farm, boundary and grave field; Lydia Klos (2009) has argued that most were raised at grave fields. In an earlier report we showed that runestones in groups stand by grave fields more often than lone stones, but that nearness to a burial mound did not set them apart ({FAM_EN}).

The large mounds have a research history of their own. Sune Lindqvist (1917, p. 142) tied great mounds such as ”King Nordian's mound” at Ås-Husby to the royal estates. Mats G. Larsson (1990) found, according to Per H. Ramqvist's review, that great mounds occur considerably more often on the settlement units that have stones for men who travelled abroad than on settlement units with other runestones in a randomly chosen reference sample (Ramqvist 1991, p. 138). In the Icelandic tradition Snorri Sturluson in Ynglinga saga (ch. 8) has Odin decree that a mound should be made for noble men and standing stones raised for others – a late, learned picture in which mound and stone belong together.

What is missing is a measure from the mounds' side, for the whole country: do runestones stand more often by the large mounds than by the small ones, in the same province and the same parish, and does it hold when the moved stones are left out? That is measured here.

## 2. Pre-registration

Two plans were committed to the project's version control before any of the tests was run; checksums (SHA-256) below, the files under Data and code.

1. **The mounds** (18 November 2026, `{SHA1[:8]}…`): three tests, Holm-corrected: great mounds near Husby and -tuna places (H1), near cult place names (H2) and with a runestone within 500 m (H3). Hypothesis H3 verbatim (translated): ”whether a runestone stands within 500 m. Test statistic: the Mantel–Haenszel odds ratio large against smaller across the provinces; p from the same permutation.” A test holds when the Holm-adjusted p < 0.05 and the direction is the same in both halves and with the limit at 15 and 30 metres. Nothing but the number of mounds, their size and names had been seen before the lock.
2. **The addendum** (18 November 2026, `{SHA2[:8]}…`): six sensitivity analyses of H3, written when H3's result was known but before any of them was run. The plan states the suspicion it was to test: that stones had been moved to churches built by great mounds. The pattern counts as robust only if every step holds (section 4.3).

H3 is the confirmatory test. The sensitivity analyses are pre-registered but run on the same material. H1 and H2 did not hold; they are reported in the popular article, not here.

## 3. Material

- **The mounds.** The Swedish National Heritage Board's Kulturmiljöregistret, monument type Hög (mound), extracted 2 November 2026: {R1['hogar']:,} free-standing mounds with a position. Mounds inside grave fields have no records of their own and are not included. The diameter is read from the description (”20 m diam”, ”20 m i diam”); {R1['med_diameter']:,} mounds have a stated diameter. **Large mound:** at least 20 metres ({R1['stora']:,}); **smaller:** under 20 metres ({R1['mindre']:,}). Mounds without a stated diameter are not included.
- **Province.** The register's counties are not provinces. Each mound gets the province of the parish (Institute for Language and Folklore) whose centre lies nearest; {R2['landskap_none']} mounds lie nearest a parish without a province and form a group of their own.
- **The runestones.** The Scandinavian Runic-text Database (Rundata), 2014 version with RUNDATA.xls updated 2018: {R2['runstenar']:,} Swedish Viking-Age runestones with coordinates. **In their original place:** the {R2['pa_plats']:,} not counted as moved – a stone counts as moved when Rundata's placement says so, when the place is a church, churchyard, manor or museum, or when the placement text names another place than the find place.
- **Medieval churches:** {R2['kyrkor']} church buildings erected before 1350 according to Wikidata, far from all. **Grave fields:** Kulturmiljöregistret's grave fields.
- **Skåne and Halland.** Rundata's Swedish material has no runestones in Skåne and Halland (they are counted as Danish), where {SKHA:,} of the {R1['stora']:,} large mounds lie. There the link cannot be tested; those mounds do not contribute to the odds ratio.

## 4. Method

Statistical terms are explained in the glossary, {GLOSS_EN}.

**4.1 The test.** For each mound it is noted whether a runestone stands within 500 metres. The Mantel–Haenszel odds ratio combines the two-by-two tables (large or smaller mound, stone or not) within each province, so that provinces with many stones and many small mounds are not compared with provinces without stones. A 95 % interval is computed with the method of Robins, Breslow and Greenland (1986). The p-value is two-sided: the size label is permuted among the mounds within each province 10,000 times, with a seed from the plan's checksum.

**4.2 The halves.** Within each county the parishes are split alternately into two halves in name order; the test must give the same direction in both.

**4.3 The sensitivity analyses** (the addendum). T1: only stones in their original place, also in both halves. T2: as T1 without mounds within 1 km of a medieval church. T3: as T1 but compared within parish instead of province. T4: as T1 within groups of province × local density of runestones (1–5 km from the mound, so that the measure does not contain the outcome) × grave field within 1 km. T5: T1 with each province with at least 10 large mounds left out in turn. T6: T1 with the radius at 250 and 1,000 metres. The requirements: T1–T4 odds ratio above 1 and p < 0.05; T1 above 1 in both halves with p < 0.05 in a half with at least 50 large mounds; T5 above 1 with every province left out; T6 above 1. All requirements must be met, so no correction for multiple tests is made.

**4.4 Deviations from the plans.**
1. The main plan named the form ”20 m diam”; the register usually writes ”20 m i diam”. That form was added before any test was run.
2. T4: density was to be split into thirds, but most mounds have no runestone 1–5 km away, so two of the cut points were 0. Density was therefore split into ”none” and ”some” stones; the rule was written in the code before the run but is not in the plan.
3. The halves in T1: the first run split the parishes alternately among the mounds with a diameter, not among all mounds as the plan prescribes (”as before”). This was corrected; both are reported in 5.3.
4. After the first run, 95 % intervals and counts per province were added as description. The tests were rerun with the same seed and gave the same odds ratios and p-values.

## 5. Results

**5.1 The main test.** With all runestones with a position the odds ratio is {e(T['T0']['or'])} (95 % {ci(T['T0'], False)}; {pv(H3['p'], False)}; Holm over the plan's three tests {pv(H3['p_holm'], False)}). Both halves: {e(math.exp(H3['halvor']['A']['stat']))} ({pv(H3['halvor']['A']['p'], False)}, {H3['halvor']['A']['stora']:,} large mounds) and {e(math.exp(H3['halvor']['B']['stat']))} ({pv(H3['halvor']['B']['p'], False)}, {H3['halvor']['B']['stora']:,}). The test holds according to the plan.

{chart(False)}

In plain words: in Uppland a runestone in its original place stands within 500 metres of about one large mound in four ({UP['stora_med_sten']} of {UP['stora']}) but of about one smaller mound in seven ({UP['mindre_med_sten']} of {UP['mindre']:,}); in Södermanland one in four against one in ten; in Medelpad one in six against fewer than one in fifty. Counted over the whole country without the provinces it looks the other way round – {e(POOL[0], 1)} against {e(POOL[1], 1)} per cent – because {SKHA:,} of the large mounds lie in Skåne and Halland, where the material has no runestones. That is why the mounds are compared within provinces.

**5.2 The plan's robustness checks.** With the limit at 15 metres the odds ratio is {e(math.exp(H3['troskel_15_30']['15']))}, at 30 metres {e(math.exp(H3['troskel_15_30']['30']))}: the same direction.

**5.3 The sensitivity analyses, step by step.**
- T1, only stones in their original place: {e(T['T1']['or'])} (95 % {ci(T['T1'], False)}; {pv(T['T1']['p'], False)}). {T['T1']['stora_med_sten']} of {R1['stora']:,} large and {T['T1']['mindre_med_sten']} of {R1['mindre']:,} smaller mounds have such a stone within 500 metres. The halves as planned: {e(HA['A']['or'])} ({pv(HA['A']['p'], False)}, {HA['A']['stora']:,} large mounds) and {e(HA['B']['or'])} ({pv(HA['B']['p'], False)}, {HA['B']['stora']:,}); in the first run's halves {e(HF['A']['or'])} ({pv(HF['A']['p'], False)}) and {e(HF['B']['or'])} ({pv(HF['B']['p'], False)}). Holds.
- T2, without the {R2['T2']['borttagna_hogar']} mounds within 1 km of a medieval church: {e(T['T2']['or'])} ({ci(T['T2'], False)}; {pv(T['T2']['p'], False)}). Holds.
- T3, within parish: {e(T['T3']['or'])} ({ci(T['T3'], False)}; {pv(T['T3']['p'], False)}). Holds.
- T4, with local density and grave fields held constant: {e(T['T4']['or'])} ({ci(T['T4'], False)}; {pv(T['T4']['p'], False)}). Holds.
- T5, one province left out at a time: the odds ratio lies between {L_EN[1]} (without {L_EN[0]}) and {L_EN[3]} (without {L_EN[2]}), with p < 0.01 in every case. Without Skåne only {round(100 * LOPO['Skåne']['kvar_av_stora'])} per cent of the large mounds remain, but they do not contribute anyway. Holds.
- T6, the radius: {e(R2['T6']['250']['or'])} at 250 metres and {e(R2['T6']['1000']['or'])} at 1,000 metres. The effect is largest close to the mound. Holds.

**5.4 Examples** (descriptive). The stones at Skalunda hög (Vg 44, Vg 45) and Ledbergs kulle (Ög 181) stand in churchyards and are not counted in T1–T6. Among stones in their original place, U Fv1975;169 stands by Tjärkullen, Borresta in Orkesta parish (35 metres); Sö 137 and Sö 138 by Tingshögen in Ludgo (30 metres); and Sö 202 at Östa, Ytterselö, near a mound 25 metres across.

## 6. Discussion

**What the finding says.** Runestones stand not only by grave fields but more often by the large mounds than by the small ones in the same district. This is not a consequence of stones later being gathered at churches built by great mounds: the moved stones and the mounds near churches have been removed without changing the pattern, and it holds within the same parish.

**Against earlier research.** The finding points the same way as Larsson's (1990) observation that great mounds are more common by stones for men who travelled abroad, but measures from the other side and for all runestones: it is the great mounds that more often have a stone near them. That groups of stones did not differ from lone stones in nearness to burial mounds ({FAM_EN}) is no contradiction: there stones were compared, here mounds of different size. Snorri's picture of mound and standing stone as two forms of memory fits the placement, but a text from the 1200s cannot show what people thought in the 1000s.

**Weaknesses, in order of weight.**
1. **Small numbers.** {T['T1']['stora_med_sten']} large mounds have a stone in its original place near them, {THREE} of them in three provinces. The pattern holds with each province left out, but it has not been tested with Uppland, Medelpad and Södermanland left out together – without them hardly any cases remain.
2. **No dating.** The register seldom says when a mound was built. A large mound by a runestone may be contemporary with the stone; the stones U 135 (Broby) and U 269 (Harby) say that the survivors made a mound by the stone. The study therefore cannot tell stones seeking out older mounds from the same families raising both mound and stone.
3. **Size from the text.** The diameter is given for {round(100 * R1['med_diameter'] / R1['hogar'])} per cent of the mounds. If great mounds are more often described with measurements in districts with runestones, that affects the comparison; it has not been tested.
4. **Moved stones and churches.** Rundata's placement is incomplete, and Wikidata's medieval churches are far from all. A check against Runor, the Heritage Board's runic register, has not been made.

**What would overturn the finding.** That the pattern disappeared with moved stones according to Runor, that it was absent in Danish material (Skåne, Denmark) with the same method, or that dated great mounds by runestones turned out to have been built long after the stones.

## 7. Conclusion

Among Sweden's free-standing burial mounds, the large ones have about three times the odds of the small ones of having a runestone near them, within the same province and within the same parish, and with only stones in their original place. The pattern is carried by Uppland, Medelpad and Södermanland.

## Data and code

The analysis was run in Vitki {APP_VERSION}, an open research tool for runestones ([https://vitkirunor.se](https://vitkirunor.se)). Code, analysis plans and result files are openly available under GPL-3.0 at {GITHUB}.

- The analysis plans: `analysplaner/2026-11-18-hogarna.md` and `analysplaner/2026-11-18-hogarna-trappan.md`.
- The scripts: `utdata/hogar/analys.py` (the main test, `resultat.json`) and `utdata/hogar/trappan.py` (the sensitivity analyses, `resultat_trappan.json`).
- Data: Rundata (`data/rundata.json`); Kulturmiljöregistret, extract of 2026-11-02 (the mounds in `downloads/hogar/hogar.csv` outside version control, the grave fields in `data/raa/lamningar.csv`); Wikidata's churches and the parishes (Institute for Language and Folklore) as in the project's other analyses.
- To rerun, from the project folder: `.venv/bin/python utdata/hogar/analys.py` and `.venv/bin/python utdata/hogar/trappan.py`.
- The report is built by `utdata/blogg/build/build_rapport_hogar.py`, which reads every number from the result files and the plans and stops if anything does not match.
- The popular article: {ART_EN}.

## References

- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, pp. 137–147.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Kvant, V. 2026. Runestones gather in family groups by the grave fields. Research report. {FAM_EN}
- Larsson, M. G. 1990. *Runstenar och utlandsfärder. Aspekter på det senvikingatida samhället med utgångspunkt i de fasta fornlämningarna*. Acta Archaeologica Lundensia, Series in 8°, 18. Lund.
- Lindqvist, S. 1917. Ottarshögen i Vendel. *Fornvännen* 12, pp. 127–143.
- Mantel, N. & Haenszel, W. 1959. Statistical aspects of the analysis of data from retrospective studies of disease. *Journal of the National Cancer Institute* 22 (4), pp. 719–748.
- Ramqvist, P. H. 1991. Review of M. G. Larsson, *Runstenar och utlandsfärder*. *Fornvännen* 86, pp. 136–139.
- Riksantikvarieämbetet (Swedish National Heritage Board). Kulturmiljöregistret (ancient monuments), extract 2026-11-02.
- Robins, J., Breslow, N. & Greenland, S. 1986. Estimators of the Mantel–Haenszel variance consistent in both sparse data and large-strata limiting models. *Biometrics* 42 (2), pp. 311–323.
- Scandinavian Runic-text Database (Rundata), 2014 version with RUNDATA.xls updated 2018. Department of Scandinavian Languages, Uppsala University. Open Database License 1.0 / Database Contents License 1.0.
- Snorri Sturluson. *Ynglinga saga*, ch. 8. In: *Heimskringla*, ed. N. Linder & H. A. Haggson, 1869–1872.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholm University.

:::box The essentials in brief
- Runestones stand more often by the large burial mounds than by the small ones in the same district – the odds are about three times as high.
- This is not because stones were later moved to churches by the great mounds; the pattern holds with only stones in their original place and within the same parish.
- The basis is small and carried by Uppland, Medelpad and Södermanland, and the study cannot say whether the mounds were older than the stones.
:::"""

body = body.replace(f"{R1['hogar']:,}", f"{R1['hogar']:,}".replace(",", " "))
for n in (R1["med_diameter"], R1["stora"], R1["mindre"], R2["runstenar"], R2["pa_plats"], SKHA, UP["mindre"],
          H3["halvor"]["A"]["stora"], H3["halvor"]["B"]["stora"], HA["A"]["stora"], HA["B"]["stora"]):
    body = body.replace(f"{n:,}", f"{n:,}".replace(",", " "))

# ---- checks (the template)
assert "I klartext" in body and "In plain words" in body_en
assert "ungefär var fjärde stor hög" in body and "var sjätte mot knappt var femtionde" in body
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS|\bAI\b"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
    assert all(u.startswith("https://") for u in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", b)), b
    cap = [ln for ln in b.split(":::chart")[1].split("\n:::")[0].split("\n") if re.match(r"(Källa|Source):", ln)]
    assert len(cap) == 1 and cap[0].endswith(("Diagram: Vitki, efter Rundata och Kulturmiljöregistret.",
                                              "Chart: Vitki, after Rundata and Kulturmiljöregistret."))
    assert 1500 <= len(head.split()) <= 3000, len(head.split())
assert body.split("\n", 1)[0].startswith(f"*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: ")
assert body_en.split("\n", 1)[0].startswith(f"*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: ")
assert "## 2. Förregistrering" in body and "## 6. Diskussion" in body and "Det viktigaste i korthet" in body

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Geografi"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_hogar.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body.split("## Data")[0].split()), "före Data och kod;", len(body_en.split()), "words,",
      len(body_en.split("## Data")[0].split()), "before Data and code")

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
                 "topic": "Rapport|hogar", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
