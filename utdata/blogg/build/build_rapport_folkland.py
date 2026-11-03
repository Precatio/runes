"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4; Fullt prövat fynd): "Upplands folkland skiljer
runstenarna åt mer än alla 999 slumpvisa indelningar av samma härader" (sv + en). Siffrorna låses mot
utdata/gamla_granser/monster.json (plan analysplaner/2026-11-02-gamla-granser-nya-monster.md, sha 054c87d5, avvikelse 1
f0a42169), monster_trappa.json (tilläggsplan e31f2fd1), monster_kanslighet.json, monster_drag.json och
utdata/granser/gransskannern.json (plan 7d22ff40).
    ../../../.venv/bin/python build_rapport_folkland.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

GG = os.path.join(ROOT, "utdata", "gamla_granser")
M = json.load(open(os.path.join(GG, "monster.json"), encoding="utf-8"))
TR = json.load(open(os.path.join(GG, "monster_trappa.json"), encoding="utf-8"))
KS = json.load(open(os.path.join(GG, "monster_kanslighet.json"), encoding="utf-8"))
DR = json.load(open(os.path.join(GG, "monster_drag.json"), encoding="utf-8"))
GS = json.load(open(os.path.join(ROOT, "utdata", "granser", "gransskannern.json"), encoding="utf-8"))
HL = json.load(open(os.path.join(ROOT, "web", "src", "lib", "historiska_land.json"), encoding="utf-8"))
APP_VERSION = json.load(open(os.path.join(ROOT, "web", "package.json")))["version"]
assert APP_VERSION == "3.0.0"
MALL_SHA = open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().split()[0]
assert MALL_SHA.startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 1
TODAY = "2026-11-03"  # rapportversionens datum, fast i byggaren
SHA = {f: open(os.path.join(ROOT, "analysplaner", f + ".sha256")).read().split()[0] for f in
       ("2026-11-02-gamla-granser-nya-monster", "2026-11-02-gamla-granser-nya-monster-avvikelse",
        "2026-11-02-folkland-slumpindelning-trappa", "2026-11-02-gransskannern", "2026-11-01-upplands-folkland")}
assert SHA["2026-11-02-gamla-granser-nya-monster"].startswith("054c87d5")
assert SHA["2026-11-02-gamla-granser-nya-monster-avvikelse"].startswith("f0a42169")
assert SHA["2026-11-02-folkland-slumpindelning-trappa"].startswith("e31f2fd1")
assert SHA["2026-11-02-gransskannern"].startswith("7d22ff40") and SHA["2026-11-01-upplands-folkland"].startswith("48346775")
TL_SV = ("kartlagret med de gamla landen byggdes och folklandsgränsen för *at* prövades under en låst plan 2026-11-01; "
         "häradernas folkland kontrollerades mot sexårsgärden 1314, gränsskannern kördes och slumpindelningsprovet "
         "låstes och kördes 2026-11-02; tilläggsplanen för känslighetsanalyserna låstes och kördes 2026-11-02")
TL_EN = ("the map layer of the old lands was built and the folkland border for *at* was tested under a locked plan "
         "2026-11-01; the hundreds' folklands were checked against the six-year tithe of 1314, the border scan was run and "
         "the random-partition test was locked and run 2026-11-02; the addendum plan for the sensitivity analyses was "
         "locked and run 2026-11-02")

d1 = lambda x: f"{x:.1f}".replace(".", ",")  # noqa: E731
r0 = lambda x: f"{x:.0f}"  # noqa: E731
pc = lambda k, n: round(100 * k / n)  # noqa: E731


def pf(p, en=False):
    s = f"{p:.3f}"
    return s if en else s.replace(".", ",")


# ---- the main test (step 1) -------------------------------------------------------------------------------------------
U, S = M["step1"]["uppland"], M["step1"]["smaland"]
assert U["units"] == 32 and U["stones"] == 841 and U["features"] == 25
assert U["sizes"] == {"attundaland": 9, "roden": 7, "tiundaland": 11, "fjadrundaland": 5}
A, HA, HB = U["alla"], U["A"], U["B"]
assert (round(A["chi2_real"]), round(A["chi2_median_random"]), round(A["chi2_p95_random"]), A["p"]) == (360, 183, 259, 0.001)
assert (round(HA["chi2_real"]), round(HA["chi2_median_random"]), HA["p"]) == (237, 129, 0.001)
assert (round(HB["chi2_real"]), round(HB["chi2_median_random"]), HB["p"]) == (217, 125, 0.001)
assert (A["k_real"], A["k_median_random"], round(A["p_k"], 3)) == (14, 8.0, 0.026)
assert U["holds"]
RATIO = A["chi2_real"] / A["chi2_median_random"]
assert round(RATIO, 1) == 2.0
assert S["units"] == 19 and S["stones"] == 103 and S["features"] == 14 and not S["holds"]
assert (round(S["alla"]["chi2_real"]), round(S["alla"]["chi2_median_random"]), round(S["alla"]["p"], 3)) == (199, 183, 0.145)
HOLM_U = min(1, 2 * min(A["p"], S["alla"]["p"]))  # two step-1 tests in the plan, Holm
assert HOLM_U == 0.002
# the addendum ladder
ST = TR["steps"]
assert TR["all_hold"] and list(ST) == ["pa_plats", "utan_fem_ristare", "daterade", "utan_forlorade"]
LAD = {k: (v["stones"], round(v["alla"]["chi2_real"]), round(v["alla"]["chi2_median_random"]), v["alla"]["p"]) for k, v in ST.items()}
assert LAD == {"pa_plats": (497, 241, 138, 0.002), "utan_fem_ristare": (534, 231, 136, 0.003),
               "daterade": (512, 270, 145, 0.002), "utan_forlorade": (704, 308, 171, 0.002)}
# sensitivity without granite (outside the plan)
assert (KS["features"], round(KS["alla"]["chi2_real"]), round(KS["alla"]["chi2_median_random"]), KS["alla"]["p"]) == (24, 318, 154, 0.001)
assert (KS["A"]["p"], KS["B"]["p"]) == (0.001, 0.002)
# which traits (descriptive)
FD = {f["feature"]: f for f in DR["features"]}
assert DR["n_stones"] == 841 and sum(1 for f in DR["features"] if f["p"] < 0.05) == 14
SH = lambda f, L: FD[f]["shares"][L]  # noqa: E731
assert [pc(*SH("pm_kors", L)) for L in ("attundaland", "tiundaland", "fjadrundaland", "roden")] == [61, 65, 35, 40]
assert [pc(*SH("prep_at", L)) for L in ("attundaland", "tiundaland", "fjadrundaland", "roden")] == [12, 32, 40, 23]
assert [pc(*SH("r_for_R", L)) for L in ("attundaland", "tiundaland", "fjadrundaland", "roden")] == [12, 19, 52, 15]
TOP = [f["feature"] for f in DR["features"][:5]]
assert TOP == ["pm_kors", "mat_granit", "prep_at", "monoftong", "r_for_R"]
# the border scan (follow-up, its own plan)
hold = [t for t in GS["tests"] if t.get("holds")]
assert len(hold) == 6 and all(t["a"] in ("attundaland", "tiundaland", "fjadrundaland", "roden") and
                              t["b"] in ("attundaland", "tiundaland", "fjadrundaland", "roden") for t in hold)
assert sorted(t["feature"] for t in hold) == ["flera_resare", "mat_granit", "pm_kors", "pm_kors", "prep_at", "r_for_R"]
# the 1314 check, as stated in the land layer
regs = {r["id"]: r for r in HL["epoch"]["regions"]}
assert "Sexårsgärden 1314 (SDHK 2593) räknar hit de åtta hundarena" in regs["attundaland"]["note"]
assert "Sexårsgärden 1314" in regs["tiundaland"]["note"] and "Gästrikland och Roden" in regs["tiundaland"]["note"]
assert "Sexårsgärden 1314" in regs["fjadrundaland"]["note"] and regs["roden"]["certainty"] == "omstridd"


# ---- runic examples: Rundata transliterations rendered with standard younger-futhark (long-branch) forms -------------
RECS = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
RMAP = {"a": "ᛅ", "b": "ᛒ", "e": "ᛂ", "f": "ᚠ", "g": "ᚵ", "h": "ᚼ", "i": "ᛁ", "k": "ᚴ", "l": "ᛚ", "m": "ᛘ", "n": "ᚾ",
        "o": "ᚬ", "r": "ᚱ", "R": "ᛦ", "s": "ᛋ", "t": "ᛏ", "u": "ᚢ", "y": "ᚤ", "þ": "ᚦ", " ": "᛫"}


def ex(signum, excerpt):
    t = " ".join(RECS[signum]["transliteration"].replace("'", " ").replace("÷", " ").replace("·", " ").split())
    assert excerpt in t, (signum, excerpt)
    return "".join(RMAP[c] for c in excerpt)


EX = {"u1177": ex("U 1177", "litu risa stin at tuba"), "u181": ex("U 181", "iftiR est faþur sin"),
      "u749": ex("U 749", "þair litu rasa stan"), "u974": ex("U 974", "þaiR")}
assert RECS["U 1177"]["carvers"][0]["name"] == RECS["U 181"]["carvers"][0]["name"] == RECS["U 974"]["carvers"][0]["name"] == "Öpir 1"
assert RECS["U 749"]["carvers"][0]["name"] == "Balle"
assert (RECS["U 1177"]["parish"], RECS["U 181"]["parish"], RECS["U 749"]["parish"], RECS["U 974"]["parish"]) == (
    "Harbo sn", "Össeby-Garns sn", "Husby-Sjutolfts sn", "Vaksala sn")

SLUG = "upplands-folkland-skiljer-runstenarna"
title = "Upplands folkland skiljer runstenarna åt mer än alla 999 slumpvisa indelningar av samma härader"
title_en = "Uppland's folklands separate the runestones more than all 999 random divisions of the same hundreds"
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki "
           f"{APP_VERSION}. https://vitkirunor.se/en/forskningsrapporter/{SLUG}")
summary = ("Gränserna mellan Upplands gamla folkland – Tiundaland, Attundaland, Fjädrundaland och kustlandet Roden – "
           "skiljer runstenarnas språk, sed och utförande ungefär dubbelt så mycket som en typisk slumpvis indelning av samma "
           "härader i lika stora block, och ingen av 999 slumpindelningar når upp till dem. Det håller i båda halvorna av "
           "materialet och i alla förregistrerade känslighetsanalyser. Smålands små land visar inget motsvarande.")
summary_en = ("The borders between Uppland's old folklands – Tiundaland, Attundaland, Fjädrundaland and the coastal land "
              "Roden – separate the language, custom and execution of the runestones about twice as much as a typical "
              "random division of the same hundreds into blocks of the same size, and none of 999 random divisions reaches "
              "them. It holds in both halves of the material and in every pre-registered sensitivity analysis. Småland's "
              "small lands show nothing similar.")


def chart(lang):
    sv = lang == "sv"
    N = {"attundaland": "Attundaland", "tiundaland": "Tiundaland", "fjadrundaland": "Fjädrundaland", "roden": "Roden"}
    rows = [":::chart Tre drag per folkland: kors, prepositionen at och r för ʀ" if sv else
            ":::chart Three features by folkland: cross, the preposition at and r for ʀ"]
    for f, lab in (("pm_kors", "Kors" if sv else "Cross"), ("prep_at", "at" if sv else "at"), ("r_for_R", "r för ʀ" if sv else "r for ʀ")):
        rows.append(f"# {lab}")
        for L in ("attundaland", "tiundaland", "fjadrundaland", "roden"):
            k, n = SH(f, L)
            rows.append(f"{N[L]} | {pc(k, n)} | {k} {'av' if sv else 'of'} {n}")
    rows.append("Källa: Samnordisk runtextdatabas; folkland efter häradernas indelning i sexårsgärden 1314 och Institutet för "
                "språk och folkminnens ortnamnsregister. Rå andelar av stenarna där draget går att avgöra. Procent." if sv else
                "Source: Scandinavian Runic-text Data Base; folkland after the hundreds in the six-year tithe of 1314 and the "
                "place-name register of the Institute for Language and Folklore. Raw shares of the stones where the feature can "
                "be decided. Percent.")
    return "\n".join(rows) + "\n:::"


body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, Uppland, folkland, hundare, härad, regional variation, permutationstest, logistisk regression. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Uppland var under medeltiden inget enat landskap utan bestod av tre folkland – Tiundaland, Attundaland och Fjädrundaland – och kustlandet Roden, med gemensam lag först 1296. Hur gamla folklanden är vet man inte: de nämns tidigast omkring 1120, och det har föreslagits att indelningen går tillbaka till slutet av 900-talet. Runstenarna restes just under 1000-talet. Om folklandens gränser redan då skilde människorna åt, borde stenarna skilja sig mer över dessa gränser än över vilka andra gränser som helst genom samma bygder. Det är frågan här.

**Material.** {U['stones']} vikingatida runstenar i Uppland med känt läge, fördelade på {U['units']} härader och skeppslag med deras folkland enligt sexårsgärden 1314; {U['features']} drag i språk, formler, familj, ristning och bergart.

**Metod.** För varje drag mättes hur mycket blocktillhörigheten förklarar, med tiden konstant (logistisk regression, kvottest), och summan över dragen jämfördes med samma summa för 999 slumpvisa indelningar av samma härader i fyra sammanhängande block av samma storlek. Planen låstes före körningen.

**Resultat.** De verkliga folklanden ger summan {r0(A['chi2_real'])}; slumpindelningarna ger i median {r0(A['chi2_median_random'])}, och den högsta tjugondelen börjar vid {r0(A['chi2_p95_random'])}. Ingen slumpindelning når upp till folklanden (p = {pf(A['p'])}, provets lägsta möjliga värde; Holm-korrigerat {pf(HOLM_U)}). Det gäller i båda halvorna av materialet (p = {pf(HA['p'])} och {pf(HB['p'])}) och i alla fyra förregistrerade känslighetsanalyser (p mellan {pf(LAD['pa_plats'][3])} och {pf(LAD['utan_fem_ristare'][3])}). Smålands små land skiljer sig inte mer än slumpblock (p = {pf(S['alla']['p'])}).

**Slutsats.** Folklandens gränser skiljer runstenarna åt ungefär dubbelt så mycket som en typisk slumpgräns genom samma bygder. Indelningen, eller något som föregick den, fanns sannolikt redan när stenarna restes. Vad som skilde – språk, sed eller verkstäder – avgör provet inte.

## 1. Inledning

Att runstenarna i Uppland varierar inom landskapet är känt. Palm (1992) visade att prepositionen *at* är vanligare i Tiundaland än i Attundaland och drog sina undersökningsområden efter folklandens gränser. Larsson (2002) visade att r-runan för ʀ är vanligare i vissa landskap och härader, men menade att geografin i sig inte förklarar variationen inom Uppland. Stille (1999) undersökte runristarna i ett enda folkland, Fjädrundaland. Om folklandens ålder har Mats G. Larsson (1993) föreslagit att både ledungen och folklandsindelningen organiserades av Erik Segersäll under senare delen av 900-talet; folklanden nämns tidigast i en latinsk text från omkring 1120, och två av dem i en redogörelse som kan gå tillbaka till mitten av 1000-talet.

Det som saknas är ett prov av gränserna själva. Att två områden skiljer sig säger ännu inget om gränsen mellan dem: grannbygder liknar varandra, och nästan vilken uppdelning av ett landskap som helst ger skillnader mellan delarna. Frågan blir därför om folklandens gränser skiljer stenarna mer än andra gränser, dragna genom samma bygder, gör. Det prövas här med ett omblandningsprov (permutationstest) där de verkliga folklanden jämförs med slumpvisa indelningar av samma härader.

## 2. Förregistrering

Planen (*Nya mönster med den vikingatida indelningen*, steg 1) låstes 2 november 2026 med SHA-256 {SHA['2026-11-02-gamla-granser-nya-monster'][:16]}…, innan provet kördes. Hypotesen ordagrant: ”Om folklanden bara vore godtyckliga block av grannbygder skulle vilka block som helst skilja lika mycket”. Utfallsregeln: folklanden är särskilda om deras summa ligger över 95:e percentilen av slumpindelningarna (p = (1 + antal ≥ verklig) / 1000 < 0,05), och samma rangtal redovisas i båda halvorna. Samma prov för Smålands små land var förregistrerat som sekundärt.

En avvikelse låstes innan något resultat hade räknats ut (SHA-256 {SHA['2026-11-02-gamla-granser-nya-monster-avvikelse'][:16]}…): grannregeln behövde vidgas, se 4.4. Känslighetsanalyserna låstes i en egen tilläggsplan efter huvudprovet men innan de kördes (SHA-256 {SHA['2026-11-02-folkland-slumpindelning-trappa'][:16]}…).

Sett före låsningen: att *at* skiljer skarpt vid gränsen mellan Tiundaland och Attundaland (en egen låst plan dagen före, SHA-256 {SHA['2026-11-01-upplands-folkland'][:16]}…), och att gränsskannern (egen plan, SHA-256 {SHA['2026-11-02-gransskannern'][:16]}…) hittat skarpa gränser, alla mellan folklanden. Huvudprovet är därför inte en blind upptäckt: det prövar om ett mönster som syntes vid enskilda gränser gäller indelningen som helhet, mot en uttalad nollhypotes. Konfirmatoriskt: steg 1 för Uppland. Sekundärt: steg 1 för Småland. Uppföljning med egen låst plan: känslighetsanalyserna. Explorativt: provet utan bergarten och vilka drag som bär skillnaden.

## 3. Material

Runstenarna kommer ur Samnordisk runtextdatabas (Rundata, utgåvan 2014 uppdaterad 2018), fryst för analysen den 4 oktober 2026, med de drag som projektet kodat för alla vikingatida runstenar i svenska landskap. Urvalet: vikingatida runstenar i Uppland vars socken går att knyta till ett härad i Institutet för språk och folkminnens ortnamnsregister (samma socknamn inom 25 km, annars närmaste socken inom 15 km) och vars härad hör till ett folkland: {U['stones']} stenar i {U['units']} härader och skeppslag. Fördelningen: Attundaland {U['sizes']['attundaland']} härader och {DR['regions']['attundaland']} stenar, Tiundaland {U['sizes']['tiundaland']} och {DR['regions']['tiundaland']}, Fjädrundaland {U['sizes']['fjadrundaland']} och {DR['regions']['fjadrundaland']}, Roden {U['sizes']['roden']} och {DR['regions']['roden']}.

Häradernas folkland följer sexårsgärden 1314 (SDHK 2593), som räknar upp Attundalands åtta hundaren och Fjädrundalands fem på samma sätt som här; Tiundaland omfattar där också Gästrikland och Roden. Roden behandlas här som ett eget block. Dess omfattning och ställning är omstridd redan i det medeltida materialet (Dahlbäck m.fl. 1972), och det är en av fyndets svagheter (avsnitt 6).

De {U['features']} dragen är de som projektet förregistrerade för folklandsstudien och som har minst tio stenar med och tio utan draget: korset, kristna formler och böner, hednisk markör, resa och död borta, beröm, bro och väg, vem som reste stenen (kvinna, flera resare) och efter vem (barn, förälder, syskon, make), *drengr* och *þegn*, ristarsignatur, prepositionen *at*, ordet *þennsa*, stungna runor, monoftongstavning, r för ʀ, o-runan, ordet *kumbl* (för få fall) och bergarten granit. Tiden hålls konstant med fem skikt efter stilgruppens mittår (före 1010, 1010–1040, 1040–1070, efter 1070, odaterad). Dragen är kodade ur Rundatas translitterationer, normaliseringar och översättningar med samma regler som i projektets tidigare rapporter; någon ny handkontroll av kodningen gjordes inte för den här studien.

## 4. Metod

**4.1 Modellen.** För varje drag skattas en logistisk regression med tidsskiktet och blocktillhörigheten, och blocktermens kvottest ger ett χ²-värde: hur mycket bättre stenarnas drag förutsägs när man vet vilket block de står i. Måttet är summan av χ² över alla {U['features']} drag. Andramåttet är antalet drag med p < 0,05.

**4.2 Slumpindelningarna och halvorna.** 999 slumpindelningar byggs av samma {U['units']} härader i fyra block med lika många härader som de verkliga folklanden ({U['sizes']['attundaland']}, {U['sizes']['tiundaland']}, {U['sizes']['fjadrundaland']} och {U['sizes']['roden']}). Varje block växer från en slumpvald starthärad till slumpvald granne tills det har sin storlek; en indelning som inte går att fullborda görs om. Blocken är alltså lika sammanhängande som riktiga land, och nollhypotesen tar hänsyn till att grannbygder liknar varandra. p-värdet är (1 + antal slumpindelningar med minst lika stor summa) / 1 000. Halvorna: socknarna i Uppland delas varannan efter medeldatering, och provet görs om i varje halva med samma 999 indelningar.

**4.3 Känslighetsanalyserna.** Samma prov på fyra urval enligt tilläggsplanen: bara stenar på sin ursprungliga plats; utan alla stenar av de fem flitigaste ristarna (Öpir, Fot, Balle, Åsmund, Gunnar, säkra och osäkra attribueringar); bara daterade stenar; utan förlorade stenar. Varje steg håller om p < 0,05.

**4.4 Avvikelser från planen.** (1) Grannregeln i planen, två härader är grannar om någon av deras socknar ligger inom 10 km, lämnade Värmdö skeppslag och Våla härad utan grannar, så att inga sammanhängande indelningar kunde byggas. Före något resultat ändrades regeln till 20 km, och en härad utan grannar får sin närmaste härad som granne (låst avvikelse). (2) Provet utan bergarten granit gjordes efter huvudresultatet och ligger utanför planen; det redovisas som explorativt. (3) Vilka drag som bär skillnaden räknades efter resultatet och är beskrivande. Inga andra avvikelser.

## 5. Resultat

**5.1 Huvudprovet.** De verkliga folklanden ger summan {r0(A['chi2_real'])}. De 999 slumpindelningarna ger i median {r0(A['chi2_median_random'])}, och 95:e percentilen ligger vid {r0(A['chi2_p95_random'])}. Ingen slumpindelning når folklanden: p = {pf(A['p'])}, provets lägsta möjliga värde, och Holm-korrigerat över planens två prov {pf(HOLM_U)}. Antalet drag som skiljer är {A['k_real']} mot i median {A['k_median_random']:.0f} (p = {pf(A['p_k'])}). I halvorna: {r0(HA['chi2_real'])} mot median {r0(HA['chi2_median_random'])} (p = {pf(HA['p'])}) och {r0(HB['chi2_real'])} mot {r0(HB['chi2_median_random'])} (p = {pf(HB['p'])}).

I klartext: folklandens gränser skiljer runstenarnas språk, sed och utförande ungefär dubbelt så mycket som en typisk slumpgräns dragen genom samma härader, och av 999 slumpvisa sätt att dela Uppland i fyra lika stora, sammanhängande delar kom inget upp i samma nivå som de verkliga folklanden.

Smålands små land, det sekundära provet: {S['units']} härader, {S['stones']} stenar och {S['features']} drag; summan {r0(S['alla']['chi2_real'])} mot median {r0(S['alla']['chi2_median_random'])} (p = {pf(S['alla']['p'])}). De små landen skiljer inte stenarna mer än slumpblock gör.

{chart('sv')}

**5.2 Vilka drag (beskrivande).** De fem drag som bidrar mest är korset, bergarten granit, prepositionen *at*, monoftongstavningen och r för ʀ. Korset står på sex av tio stenar i Attundaland och Tiundaland men på en av tre i Fjädrundaland och fyra av tio i Roden; *at* står på var åttonde sten i Attundaland mot fyra av tio i Fjädrundaland; r för ʀ på hälften av stenarna i Fjädrundaland mot en av åtta i Attundaland.

Så ser skillnaden ut på stenarna. Samma ristare, Öpir, skrev *at* i Tiundaland men *æftiR* i Attundaland, och samma ord, *þæiR* ’de’, stavas med r-runan i Fjädrundaland men med yr-runan i Tiundaland (runorna återges med den yngre futharkens vanliga former efter Rundatas translitteration, inte med stenarnas exakta former):
- Tiundaland, U 1177 i Harbo, ristad av Öpir: {EX['u1177']} – *litu risa stin at tuba*, ’lät resa stenen efter Tobbe’.
- Attundaland, U 181 i Össeby-Garn, ristad av Öpir: {EX['u181']} – *iftiR est faþur sin*, ’efter Äst, sin fader’.
- Fjädrundaland, U 749 i Husby-Sjutolft, attribuerad till Balle: {EX['u749']} – *þair litu rasa stan*, ’de lät resa stenen’, med ʀ i *þæiR* skrivet med r-runan ᚱ.
- Tiundaland, U 974 i Vaksala, attribuerad till Öpir: {EX['u974']} – *þaiR*, samma ord med yr-runan ᛦ.

**5.3 Känslighetsanalyserna steg för steg.**
- Bara stenar på sin ursprungliga plats ({LAD['pa_plats'][0]} stenar): {LAD['pa_plats'][1]} mot median {LAD['pa_plats'][2]}, p = {pf(LAD['pa_plats'][3])} – håller.
- Utan de fem flitigaste ristarnas stenar ({LAD['utan_fem_ristare'][0]}): {LAD['utan_fem_ristare'][1]} mot {LAD['utan_fem_ristare'][2]}, p = {pf(LAD['utan_fem_ristare'][3])} – håller.
- Bara daterade stenar ({LAD['daterade'][0]}): {LAD['daterade'][1]} mot {LAD['daterade'][2]}, p = {pf(LAD['daterade'][3])} – håller.
- Utan förlorade stenar ({LAD['utan_forlorade'][0]}): {LAD['utan_forlorade'][1]} mot {LAD['utan_forlorade'][2]}, p = {pf(LAD['utan_forlorade'][3])} – håller.
- Explorativt, utan bergarten granit ({KS['features']} drag): {r0(KS['alla']['chi2_real'])} mot {r0(KS['alla']['chi2_median_random'])}, p = {pf(KS['alla']['p'])}; i halvorna p = {pf(KS['A']['p'])} och {pf(KS['B']['p'])}. Skillnaden beror alltså inte på berggrunden.

**5.4 Uppföljning: gränserna en och en.** Gränsskannern (egen låst plan) prövade varje par av angränsande regioner med minst 40 stenar – i praktiken folklanden sinsemellan och mot Södermanland – och frågade om skillnaden är skarp vid själva gränsen. Sex drag är skarpa vid en gräns och håller i båda halvorna, och alla sex går mellan Upplands folkland: *at* och bergarten granit mellan Tiundaland och Attundaland, korset, flera resare och r för ʀ mellan Tiundaland och Fjädrundaland, och korset mellan Attundaland och Roden. Gränsen mot Södermanland, den enda andra som kunde prövas, håller inte på samma sätt.

## 6. Diskussion

Resultatet säger att folklandens gränser inte är vilka gränser som helst: de skiljer stenarna åt mer än sammanhängande slumpblock av samma storlek, i båda halvorna av materialet och i alla förregistrerade känslighetsanalyser. Eftersom stenarna i huvudsak är från 1000-talet och folklanden är kända först från omkring 1120, talar det för att indelningen – eller de bygdegemenskaper den byggde på – fanns redan när stenarna restes. Det stämmer med Larssons (1993) förslag om en organisation från slutet av 900-talet, men provet kan inte skilja en administrativ indelning från äldre bygder som indelningen sedan följde.

Mot tidigare forskning: Palm (1992) såg redan skillnaden i *at* mellan Tiundaland och Attundaland, och Larsson (2002) skillnaden i r för ʀ. Det nya är att gränserna prövas som helhet, mot en nollhypotes som tar hänsyn till att grannbygder liknar varandra, och att de håller. Larssons (2002) bedömning att geografin i sig inte förklarar variationen inom Uppland får därmed en nyans: folklanden förklarar mer än geografin i allmänhet.

Svagheterna i ordning efter vikt: (1) Indelningen är känd från 1300-talet. Häradernas folkland bygger på sexårsgärden 1314 och häradernas gränser på senare register; hundarena kan ha sett annorlunda ut på 1000-talet. (2) Roden är omstritt och behandlas här som ett eget block. (3) Dragen hänger ihop – kors och kristna formler, flera resare och relationerna – och summan av χ² räknar sådana drag flera gånger; nollfördelningen bygger dock på samma drag, så provet är giltigt, men måttet är inte ett antal oberoende skillnader. (4) Slumpblocken har lika många härader som folklanden, inte lika många stenar. (5) Ristarna: utan de fem flitigaste håller provet, men mindre verkstäder kan ändå bära delar av skillnaden; provet skiljer inte land från verkstad. (6) Smålands negativa resultat kan bero på för få stenar. (7) Peterson (1996) om dialektgränser i runinskrifterna har vi inte kunnat läsa.

Fyndet faller om andra sammanhängande indelningar av Uppland som följer naturliga gränser, till exempel vattendrag eller skogsbälten, skiljer stenarna lika mycket som folklanden; eller om ett oberoende material, som gravskicket eller ortnamnen, inte visar samma gränser.

## 7. Slutsats

Upplands folkland skiljer runstenarna åt ungefär dubbelt så mycket som en typisk slumpvis indelning av samma bygder, och ingen av 999 slumpindelningar når upp till dem. Indelningen, eller de bygder den byggde på, fanns sannolikt redan på 1000-talet.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts fram till den 3 november 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Planerna: `analysplaner/2026-11-02-gamla-granser-nya-monster.md`, avvikelsen `analysplaner/2026-11-02-gamla-granser-nya-monster-avvikelse.md`, tilläggsplanen `analysplaner/2026-11-02-folkland-slumpindelning-trappa.md`, med kontrollsummor bredvid.
- Huvudprovet: `utdata/gamla_granser/monster.py` → `monster.json`; känslighetsanalyserna `monster_trappa.py` → `monster_trappa.json`; provet utan granit `monster_kanslighet.py`; dragen `monster_drag.py`. Gränsskannern: `utdata/granser/gransskannern.py`.
- Regionerna: `src/regions.py`, `scripts/assign_historiska_land.py` (ISOF:s ortnamnsregister som första källa), kontrollen mot sexårsgärden `utdata/geografi/sexarsgard_1314.py`; dragen ur `utdata/upptackt_v3/drag.csv`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_folkland.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer. Mallen: `utdata/rapporter/MALL.md`, version 4.
- I Vitki syns folklanden på kartan (gränslagret Små land) och i statistiken efter de gamla gränserna. Populärt berättat i serien [De gamla landen](/artiklar/de-gamla-landen-sotholm).

## Referenser

- Dahlbäck, G., Jansson, B. & Westin, G. T. 1972. *Det medeltida Sverige* 1. Uppland 1. Norra Roden. Stockholm: Kungl. Vitterhets Historie och Antikvitets Akademien.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Larsson, M. G. 1993. Kung Eriks nyordning? Spår efter samhällsorganisation i vikingatidens Uppland. *Uppland* 1993, s. 105–134.
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter.* Runrön 17. Uppsala.
- Palm, R. 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna.* Runrön 7. Uppsala.
- Peterson, L. 1996. [Om dialektgeografi i runinskrifterna], i *Mål i sikte*, s. 239–252. (Inte läst.)
- Phipson, B. & Smyth, G. K. 2010. Permutation p-values should never be zero. *Statistical Applications in Genetics and Molecular Biology* 9 (1), artikel 39.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering.* Runrön 13. Uppsala.
- Svenskt diplomatariums huvudkartotek (SDHK) 2593, sexårsgärden 1314. Riksarkivet.

:::box Det viktigaste i korthet
- Upplands folkland var inte bara medeltida skatte- och lagområden; deras gränser syns redan i 1000-talets runstenar.
- Gränserna skiljer stenarna mer än vilka grannblock som helst – det är gränserna själva, inte bara att närliggande bygder liknar varandra.
- Skillnaderna gäller både språket (*at*, r för ʀ) och seden (korset, vem som reste stenen).
- Provet visar att gränserna fanns, inte varför; Smålands små land visar inget motsvarande.
:::"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was done in Vitki {APP_VERSION}. Licence CC BY 4.0. The English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, Uppland, folkland, hundred, regional variation, permutation test, logistic regression. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** In the Middle Ages Uppland was not one province but three folklands – Tiundaland, Attundaland and Fjädrundaland – and the coastal land Roden, with a common law only from 1296. How old the folklands are is not known: they are first mentioned around 1120, and it has been suggested that the division goes back to the late tenth century. The runestones were raised precisely in the eleventh century. If the folkland borders already separated people then, the stones should differ more across those borders than across any other borders through the same districts. That is the question here.

**Material.** {U['stones']} Viking-age runestones in Uppland with known location, in {U['units']} hundreds and ship districts with their folkland according to the six-year tithe of 1314; {U['features']} features of language, formulas, family, carving and stone.

**Method.** For each feature we measured how much block membership explains, with time held constant (logistic regression, likelihood-ratio test), and the sum over the features was compared with the same sum for 999 random divisions of the same hundreds into four contiguous blocks of the same size. The plan was locked before the run.

**Results.** The real folklands give a sum of {r0(A['chi2_real'])}; the random divisions give a median of {r0(A['chi2_median_random'])}, and the top twentieth begins at {r0(A['chi2_p95_random'])}. No random division reaches the folklands (p = {pf(A['p'], True)}, the lowest value the test can give; Holm-corrected {pf(HOLM_U, True)}). This holds in both halves of the material (p = {pf(HA['p'], True)} and {pf(HB['p'], True)}) and in all four pre-registered sensitivity analyses (p between {pf(LAD['pa_plats'][3], True)} and {pf(LAD['utan_fem_ristare'][3], True)}). Småland's small lands differ no more than random blocks (p = {pf(S['alla']['p'], True)}).

**Conclusion.** The folkland borders separate the runestones about twice as much as a typical random border through the same districts. The division, or something that preceded it, probably existed already when the stones were raised. What set them apart – language, custom or workshops – the test does not decide.

## 1. Introduction

That Uppland's runestones vary within the province is known. Palm (1992) showed that the preposition *at* is more common in Tiundaland than in Attundaland and drew his study areas along the folkland borders. Larsson (2002) showed that the r-rune for ʀ is more common in certain provinces and hundreds, but held that geography as such does not explain the variation within Uppland. Stille (1999) studied the carvers of a single folkland, Fjädrundaland. On the age of the folklands, Mats G. Larsson (1993) has suggested that both the levy and the folkland division were organised by Erik the Victorious in the later tenth century; the folklands are first named in a Latin text of about 1120, and two of them in an account that may go back to the mid-eleventh century.

What is missing is a test of the borders themselves. That two areas differ says nothing yet about the border between them: neighbouring districts resemble each other, and almost any division of a province produces differences between its parts. The question is therefore whether the folkland borders separate the stones more than other borders, drawn through the same districts, do. It is tested here with a permutation test in which the real folklands are compared with random divisions of the same hundreds.

## 2. Pre-registration

The plan (*New patterns with the Viking-age division*, step 1) was locked on 2 November 2026 with SHA-256 {SHA['2026-11-02-gamla-granser-nya-monster'][:16]}…, before the test was run. The hypothesis, translated: "If the folklands were merely arbitrary blocks of neighbouring districts, any blocks would differ as much". The decision rule: the folklands are special if their sum lies above the 95th percentile of the random divisions (p = (1 + number ≥ real) / 1000 < 0.05), and the same rank is reported in both halves. The same test for Småland's small lands was pre-registered as secondary.

One deviation was locked before any result had been computed (SHA-256 {SHA['2026-11-02-gamla-granser-nya-monster-avvikelse'][:16]}…): the neighbour rule had to be widened, see 4.4. The sensitivity analyses were locked in a separate addendum after the main test but before they were run (SHA-256 {SHA['2026-11-02-folkland-slumpindelning-trappa'][:16]}…).

Seen before locking: that *at* changes sharply at the border between Tiundaland and Attundaland (its own locked plan the day before, SHA-256 {SHA['2026-11-01-upplands-folkland'][:16]}…), and that a border scan (its own plan, SHA-256 {SHA['2026-11-02-gransskannern'][:16]}…) had found sharp borders, all between the folklands. The main test is therefore not a blind discovery: it tests whether a pattern seen at single borders holds for the division as a whole, against an explicit null hypothesis. Confirmatory: step 1 for Uppland. Secondary: step 1 for Småland. Follow-up under its own locked plan: the sensitivity analyses. Exploratory: the test without the rock type and which features carry the difference.

## 3. Material

The runestones come from the Scandinavian Runic-text Data Base (Rundata, 2014 edition updated 2018), frozen for the analysis on 4 October 2026, with the features the project has coded for all Viking-age runestones in Swedish provinces. The selection: Viking-age runestones in Uppland whose parish can be linked to a hundred in the place-name register of the Institute for Language and Folklore (the same parish name within 25 km, otherwise the nearest parish within 15 km) and whose hundred belongs to a folkland: {U['stones']} stones in {U['units']} hundreds and ship districts. The distribution: Attundaland {U['sizes']['attundaland']} hundreds and {DR['regions']['attundaland']} stones, Tiundaland {U['sizes']['tiundaland']} and {DR['regions']['tiundaland']}, Fjädrundaland {U['sizes']['fjadrundaland']} and {DR['regions']['fjadrundaland']}, Roden {U['sizes']['roden']} and {DR['regions']['roden']}.

The folkland of each hundred follows the six-year tithe of 1314 (SDHK 2593), which lists Attundaland's eight hundreds and Fjädrundaland's five as here; Tiundaland there also includes Gästrikland and Roden. Roden is treated here as a block of its own. Its extent and status are disputed already in the medieval material (Dahlbäck et al. 1972), and this is one of the weaknesses of the finding (section 6).

The {U['features']} features are those the project pre-registered for the folkland study that have at least ten stones with and ten without the feature: the cross, Christian formulas and prayers, a pagan marker, journey and death abroad, praise, bridge and road, who raised the stone (a woman, several raisers) and for whom (child, parent, sibling, spouse), *drengr* and *þegn*, the carver's signature, the preposition *at*, the word *þennsa*, dotted runes, monophthong spelling, r for ʀ, the o-rune, the word *kumbl* (too few cases) and the rock type granite. Time is held constant with five strata by the midpoint of the style group (before 1010, 1010–1040, 1040–1070, after 1070, undated). The features are coded from Rundata's transliterations, normalisations and translations with the same rules as in the project's earlier reports; no new hand check of the coding was made for this study.

## 4. Method

**4.1 The model.** For each feature a logistic regression with the time stratum and the block membership is estimated, and the likelihood-ratio test of the block term gives a χ² value: how much better the stones' features are predicted when one knows which block they stand in. The measure is the sum of χ² over all {U['features']} features. The second measure is the number of features with p < 0.05.

**4.2 The random divisions and the halves.** 999 random divisions are built from the same {U['units']} hundreds into four blocks with as many hundreds as the real folklands ({U['sizes']['attundaland']}, {U['sizes']['tiundaland']}, {U['sizes']['fjadrundaland']} and {U['sizes']['roden']}). Each block grows from a randomly chosen starting hundred to a randomly chosen neighbour until it has its size; a division that cannot be completed is redrawn. The blocks are thus as contiguous as real lands, and the null hypothesis takes into account that neighbouring districts resemble each other. The p-value is (1 + number of random divisions with at least as large a sum) / 1,000. The halves: Uppland's parishes are split alternately by mean dating, and the test is repeated in each half with the same 999 divisions.

**4.3 The sensitivity analyses.** The same test on four selections according to the addendum: only stones in their original place; without all stones by the five most prolific carvers (Öpir, Fot, Balle, Åsmund, Gunnar, certain and uncertain attributions); only dated stones; without lost stones. Each step holds if p < 0.05.

**4.4 Deviations from the plan.** (1) The plan's neighbour rule, two hundreds are neighbours if any of their parishes lie within 10 km, left the ship district of Värmdö and the hundred of Våla without neighbours, so that no contiguous divisions could be built. Before any result, the rule was changed to 20 km, and a hundred without neighbours gets its nearest hundred as neighbour (locked deviation). (2) The test without the rock type granite was run after the main result and lies outside the plan; it is reported as exploratory. (3) Which features carry the difference was computed after the result and is descriptive. No other deviations.

## 5. Results

**5.1 The main test.** The real folklands give a sum of {r0(A['chi2_real'])}. The 999 random divisions give a median of {r0(A['chi2_median_random'])}, and the 95th percentile lies at {r0(A['chi2_p95_random'])}. No random division reaches the folklands: p = {pf(A['p'], True)}, the lowest value the test can give, and Holm-corrected over the plan's two tests {pf(HOLM_U, True)}. The number of differing features is {A['k_real']} against a median of {A['k_median_random']:.0f} (p = {pf(A['p_k'], True)}). In the halves: {r0(HA['chi2_real'])} against a median of {r0(HA['chi2_median_random'])} (p = {pf(HA['p'], True)}) and {r0(HB['chi2_real'])} against {r0(HB['chi2_median_random'])} (p = {pf(HB['p'], True)}).

In plain words: the folkland borders separate the language, custom and execution of the runestones about twice as much as a typical random border drawn through the same hundreds, and of 999 random ways of dividing Uppland into four equally large, contiguous parts, none reached the level of the real folklands.

Småland's small lands, the secondary test: {S['units']} hundreds, {S['stones']} stones and {S['features']} features; the sum {r0(S['alla']['chi2_real'])} against a median of {r0(S['alla']['chi2_median_random'])} (p = {pf(S['alla']['p'], True)}). The small lands separate the stones no more than random blocks do.

{chart('en')}

**5.2 Which features (descriptive).** The five features that contribute most are the cross, the rock type granite, the preposition *at*, monophthong spelling and r for ʀ. The cross is on six stones in ten in Attundaland and Tiundaland but on one in three in Fjädrundaland and four in ten in Roden; *at* is on one stone in eight in Attundaland against four in ten in Fjädrundaland; r for ʀ on half the stones in Fjädrundaland against one in eight in Attundaland.

This is what the difference looks like on the stones. The same carver, Öpir, wrote *at* in Tiundaland but *æftiR* in Attundaland, and the same word, *þæiR* 'they', is spelled with the r-rune in Fjädrundaland but with the yr-rune in Tiundaland (the runes are rendered with the usual younger-futhark forms after Rundata's transliteration, not with the stones' exact forms):
- Tiundaland, U 1177 at Harbo, carved by Öpir: {EX['u1177']} – *litu risa stin at tuba*, 'had the stone raised in memory of Tobbe'.
- Attundaland, U 181 at Össeby-Garn, carved by Öpir: {EX['u181']} – *iftiR est faþur sin*, 'in memory of Äst, their father'.
- Fjädrundaland, U 749 at Husby-Sjutolft, attributed to Balle: {EX['u749']} – *þair litu rasa stan*, 'they had the stone raised', with the ʀ of *þæiR* written with the r-rune ᚱ.
- Tiundaland, U 974 at Vaksala, attributed to Öpir: {EX['u974']} – *þaiR*, the same word with the yr-rune ᛦ.

**5.3 The sensitivity analyses step by step.**
- Only stones in their original place ({LAD['pa_plats'][0]} stones): {LAD['pa_plats'][1]} against a median of {LAD['pa_plats'][2]}, p = {pf(LAD['pa_plats'][3], True)} – holds.
- Without the stones of the five most prolific carvers ({LAD['utan_fem_ristare'][0]}): {LAD['utan_fem_ristare'][1]} against {LAD['utan_fem_ristare'][2]}, p = {pf(LAD['utan_fem_ristare'][3], True)} – holds.
- Only dated stones ({LAD['daterade'][0]}): {LAD['daterade'][1]} against {LAD['daterade'][2]}, p = {pf(LAD['daterade'][3], True)} – holds.
- Without lost stones ({LAD['utan_forlorade'][0]}): {LAD['utan_forlorade'][1]} against {LAD['utan_forlorade'][2]}, p = {pf(LAD['utan_forlorade'][3], True)} – holds.
- Exploratory, without the rock type granite ({KS['features']} features): {r0(KS['alla']['chi2_real'])} against {r0(KS['alla']['chi2_median_random'])}, p = {pf(KS['alla']['p'], True)}; in the halves p = {pf(KS['A']['p'], True)} and {pf(KS['B']['p'], True)}. The difference is thus not down to the bedrock.

**5.4 Follow-up: the borders one by one.** A border scan (its own locked plan) tested every pair of neighbouring regions with at least 40 stones – in practice the folklands among themselves and against Södermanland – and asked whether the difference is sharp at the border itself. Six features are sharp at a border and hold in both halves, and all six run between Uppland's folklands: *at* and the rock type granite between Tiundaland and Attundaland, the cross, several raisers and r for ʀ between Tiundaland and Fjädrundaland, and the cross between Attundaland and Roden. The border with Södermanland, the only other one that could be tested, does not hold in the same way.

## 6. Discussion

The result says that the folkland borders are not just any borders: they separate the stones more than contiguous random blocks of the same size, in both halves of the material and in every pre-registered sensitivity analysis. Since the stones are mainly from the eleventh century and the folklands are known only from around 1120, this suggests that the division – or the district communities it was built on – existed already when the stones were raised. This agrees with Larsson's (1993) proposal of an organisation from the late tenth century, but the test cannot tell an administrative division from older districts that the division later followed.

Against earlier research: Palm (1992) already saw the difference in *at* between Tiundaland and Attundaland, and Larsson (2002) the difference in r for ʀ. What is new is that the borders are tested as a whole, against a null hypothesis that takes into account that neighbouring districts resemble each other, and that they hold. Larsson's (2002) judgement that geography as such does not explain the variation within Uppland thereby receives a nuance: the folklands explain more than geography in general.

The weaknesses in order of importance: (1) The division is known from the fourteenth century. The hundreds' folklands rest on the six-year tithe of 1314 and the hundreds' borders on later registers; the hundreds may have looked different in the eleventh century. (2) Roden is disputed and is treated here as a block of its own. (3) The features are related – the cross and Christian formulas, several raisers and the relations – and the sum of χ² counts such features more than once; the null distribution rests on the same features, so the test is valid, but the measure is not a count of independent differences. (4) The random blocks have as many hundreds as the folklands, not as many stones. (5) The carvers: without the five most prolific the test holds, but smaller workshops may still carry part of the difference; the test does not separate land from workshop. (6) Småland's negative result may be due to too few stones. (7) We have not been able to read Peterson (1996) on dialect borders in the runic inscriptions.

The finding falls if other contiguous divisions of Uppland that follow natural borders, such as watercourses or forest belts, separate the stones as much as the folklands; or if an independent material, such as burial customs or place names, does not show the same borders.

## 7. Conclusion

Uppland's folklands separate the runestones about twice as much as a typical random division of the same districts, and none of 999 random divisions reaches them. The division, or the districts it was built on, probably existed already in the eleventh century.

## Data and code

The analysis was done in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se)), with the changes made up to 3 November 2026. No release with a DOI exists yet; when it does, the report will refer to it. All code and result files are open on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The plans: `analysplaner/2026-11-02-gamla-granser-nya-monster.md`, the deviation `analysplaner/2026-11-02-gamla-granser-nya-monster-avvikelse.md`, the addendum `analysplaner/2026-11-02-folkland-slumpindelning-trappa.md`, with checksums beside them.
- The main test: `utdata/gamla_granser/monster.py` → `monster.json`; the sensitivity analyses `monster_trappa.py` → `monster_trappa.json`; the test without granite `monster_kanslighet.py`; the features `monster_drag.py`. The border scan: `utdata/granser/gransskannern.py`.
- The regions: `src/regions.py`, `scripts/assign_historiska_land.py` (the ISOF place-name register as first source), the check against the six-year tithe `utdata/geografi/sexarsgard_1314.py`; the features from `utdata/upptackt_v3/drag.csv`.
- The report is built by `utdata/blogg/build/build_rapport_folkland.py`, which reads every number from the result files and stops if anything does not match. The template: `utdata/rapporter/MALL.md`, version 4.
- In Vitki the folklands are shown on the map (the border layer Small lands) and in the statistics by the old borders. Told for a general audience in the series [De gamla landen](/en/artiklar/de-gamla-landen-sotholm).

## References

- Dahlbäck, G., Jansson, B. & Westin, G. T. 1972. *Det medeltida Sverige* 1. Uppland 1. Norra Roden. Stockholm: Kungl. Vitterhets Historie och Antikvitets Akademien.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Larsson, M. G. 1993. Kung Eriks nyordning? Spår efter samhällsorganisation i vikingatidens Uppland. *Uppland* 1993, pp. 105–134.
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter.* Runrön 17. Uppsala.
- Palm, R. 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna.* Runrön 7. Uppsala.
- Peterson, L. 1996. [On dialect geography in the runic inscriptions], in *Mål i sikte*, pp. 239–252. (Not read.)
- Phipson, B. & Smyth, G. K. 2010. Permutation p-values should never be zero. *Statistical Applications in Genetics and Molecular Biology* 9 (1), article 39.
- Scandinavian Runic-text Data Base (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering.* Runrön 13. Uppsala.
- Swedish Diplomatarium main catalogue (SDHK) 2593, the six-year tithe of 1314. Swedish National Archives.

:::box The essentials in brief
- Uppland's folklands were not only medieval tax and law districts; their borders show already in the runestones of the eleventh century.
- The borders separate the stones more than any neighbouring blocks – it is the borders themselves, not merely that nearby districts resemble each other.
- The differences concern both the language (*at*, r for ʀ) and the custom (the cross, who raised the stone).
- The test shows that the borders existed, not why; Småland's small lands show nothing similar.
:::"""

# the plain-words sentence rests on these numbers (mallen version 4)
assert round(RATIO) == 2 and A["p"] == 0.001
assert "I klartext" in body and "In plain words" in body_en
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion")
assert body_en.split("\n", 1)[0].startswith("*Viktor Kvant, independent researcher. Fully tested finding. Report version")

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Geografi", "Språk och stavning", "Tro och magi"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_folkland.json")
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
        assert not [p_ for p_ in blog._all() if p_.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Rapport|folkland", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
