"""Forskningsrapport, metodrapport (låst mall utdata/rapporter/MALL.md, version 4; Metodrapport, delvis prövad):
"Skrivmiljöer utan namn: grupper av runstenar utan ristare blir till 85 procent en och samma hand när metoden prövas på
ristare den inte sett" (sv + en). r/anonymous.R (grupperingen och valideringen) och de två låsta planerna 2026-10-29
(analysplaner/2026-10-29-okanda-ristare-oberoende.md, 2026-10-29-en-och-samma-mastare.md). Alla siffror asserteras.
    ../../../.venv/bin/python build_rapport_skrivmiljoer.py [--write | --update DOC]"""
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
TL_SV = "metoden byggdes 2026-10-11; prövningen på ristare som hölls utanför gjordes 2026-10-20; de två planerna för oberoende prov låstes och kördes 2026-10-29"
TL_EN = "the method was built 2026-10-11; the test on carvers held out was made 2026-10-20; the two plans for independent tests were locked and run 2026-10-29"
AN = json.load(open(os.path.join(ROOT, "data", "cache", "r", "corpus", FP, "anonymous.json"), encoding="utf-8"))
OK = json.load(open(os.path.join(ROOT, "utdata", "okanda_ristare", "okanda_ristare.json"), encoding="utf-8"))
MA = json.load(open(os.path.join(ROOT, "utdata", "okanda_ristare", "mastare_del12.json"), encoding="utf-8"))
METHODS = open(os.path.join(ROOT, "METHODS.md"), encoding="utf-8").read()
SHA = {k: open(os.path.join(ROOT, "analysplaner", f"{k}.sha256")).read().split()[0][:16]
       for k in ("2026-10-29-okanda-ristare-oberoende", "2026-10-29-en-och-samma-mastare")}
assert SHA["2026-10-29-okanda-ristare-oberoende"].startswith("a09033c8") and SHA["2026-10-29-en-och-samma-mastare"].startswith("591fd25d")
pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731


def pfmt(p, en=False):
    if p < 0.001:
        m, e = f"{p:.1e}".split("e")
        m = m if en else m.replace(".", ",")
        return f"p = {m} · 10{str(int(e)).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))}"
    s = f"{p:.3f}" if p < 0.1 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the method and its validation -----------------------------------------------------------------------------------
assert (AN["n_stones"], AN["n_known"], AN["n_unattributed"], AN["n_candidates"], AN["n_robust"]) == (1292, 441, 691, 8, 5)
CA = AN["calibration"]
assert (CA["link_km"], CA["lr_min"], round(CA["lr"], 1), pc(CA["precision"]), round(CA["max_spread_km"]), AN["robust_min"]) == (30, 12, 13.6, 71, 23, 0.65)
VA = AN["validation"]
assert (VA["n_groups"], pc(VA["purity"]), pc(VA["purity_geography"]), pc(VA["share_pure"])) == (15, 69, 43, 60)
HO, HN = VA["heldout"], VA["heldout_no_time"]
assert (pc(HO["purity"]), pc(HO["purity_geography"]), pc(HO["difference"]), pc(HO["difference_ci"][0]), pc(HO["difference_ci"][1])) == (85, 69, 16, 15, 17)
assert (HO["runs_above"], HO["runs"], HO["folds"], pc(HN["purity"]), pc(HN["purity_geography"])) == (30, 30, 3, 85, 68)
assert AN["coverage"]["n_carvers"] == 35 and AN["coverage"]["carvers_by_province"] == {"Ög": 1, "Sö": 8, "U": 25, "Vs": 1}
SHARE = AN["coverage"]["share_attributed"]
assert [pc(SHARE[p]) for p in ("U", "Sö", "Ög", "Sm", "Vg", "M")] == [70, 46, 5, 2, 1, 8]
assert "74 mot 61 %" in METHODS  # the transfer between Södermanland and Uppland (utdata/ristare/ristare_overforing.R)
G = AN["groups"]
assert len(G) == 16
CAND = [g for g in G if g["status"] == "candidate"]
assert [(g["name"], g["n"], g["provinces"]) for g in CAND] == [
    ("Konungsundsgruppen", 28, ["Ög"]), ("Vibygruppen", 14, ["Ög"]), ("Vetlandagruppen", 14, ["Sm"]), ("Kölabygruppen", 13, ["Vg"]),
    ("Sättnagruppen", 7, ["M"]), ("Leksbergsgruppen", 6, ["Vg"]), ("Husabygruppen", 6, ["Vg"]), ("Dalumsgruppen", 5, ["Vg"])]
ROB = [g["name"] for g in CAND if g["robust"]]
assert ROB == ["Konungsundsgruppen", "Vetlandagruppen", "Kölabygruppen", "Leksbergsgruppen", "Husabygruppen"]

# ---- the independent tests (locked 2026-10-29) ------------------------------------------------------------------------
CO = OK["control"]["summary"]
assert (OK["control"]["n_carvers"], OK["B"], OK["radius_km"]) == (26, 9999, 30)
assert CO["rock"]["p"] < 1e-8 and CO["height"]["p"] < 1e-4 and CO["names"]["p"] < 1e-17
assert OK["holds"] == {"H1": True, "H2": False, "H3": True}
assert (round(OK["holm"]["H1"], 4), round(OK["holm"]["H3"], 3), round(OK["p"]["H2"], 2)) == (0.0023, 0.035, 0.32)
GR = {g.get("group") or g.get("name"): g for g in OK["candidates"]["groups"]} if all(("group" in g or "name" in g) for g in OK["candidates"]["groups"]) else None
KON = OK["candidates"]["groups"][0]
assert (KON["n"], pc(KON["rock"]["obs"]), pc(KON["rock"]["null_mean"]), KON["rock"]["p"]) == (28, 92, 77, 0.0001)
H5 = MA["part2"]
assert H5["verdict"] == "håller" and 0.004 < H5["H5"]["p"] < 0.005 and H5["control"]["p"] < 1e-12
SP = {c["group"]: c for c in H5["candidates"]}
assert (SP["Kölaby"]["p"], round(SP["Konungsund"]["p"], 3)) == (0.0001, 0.033)
P1 = MA["part1"]
assert (P1["Konungsund"]["span"], P1["Konungsund"]["verdict"], P1["Kölaby"]["verdict"], P1["Leksberg"]["verdict"]) == (32.5, "förenligt", "förenligt", "förenligt")

SLUG = "skrivmiljoer-utan-namn"
title = "Skrivmiljöer utan namn: grupper av runstenar utan ristare blir till 85 procent en och samma hand när metoden prövas på ristare den inte sett"
title_en = "Writing milieus without names: groups of runestones without a carver come out 85 percent one and the same hand when the method is tested on carvers it has not seen"
summary = ("Metodrapport. Runstenar utan ristare grupperas efter handens drag – stavning, skiljetecken, formler och runformer, inte "
           "plats och innehåll. Prövad på kända ristare som hölls utanför bestod en grupp till 85 procent av samma ristare, mot "
           "69 procent för lika många stenar som bara står nära varandra. Åtta möjliga skrivmiljöer utan namn finns, främst i "
           "Götaland, där metoden ännu inte är prövad.")
summary_en = ("Methods report. Runestones without a carver are grouped by the features of the hand – spelling, word dividers, "
              "formulas and rune forms, not place and content. Tested on known carvers held out, a group consisted 85 percent of "
              "the same carver, against 69 percent for as many stones that merely stand close together. Eight possible writing "
              "milieus without names exist, mainly in Götaland, where the method is not yet tested.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report (methods report), report version {REPORT_VERSION}; analysis in "
           f"Vitki {APP_VERSION}. https://vitkirunor.se/en/forskningsrapporter/{SLUG}")


def chart(sv):
    rows = [":::chart Andel av en grupp som är samma ristare, kända ristare" if sv else ":::chart Share of a group that is the same carver, known carvers"]
    st = (("Första valideringen", "Ristare som hölls utanför", "Utan de tidsberoende dragen") if sv else
          ("First validation", "Carvers held out", "Without the time-dependent traits"))
    me, ge = (("Grupperna", "Lika många närliggande stenar") if sv else ("The groups", "As many nearby stones"))
    f = (lambda x: f"{100 * x:.0f}")
    for lab, a, b in ((st[0], VA["purity"], VA["purity_geography"]), (st[1], HO["purity"], HO["purity_geography"]),
                      (st[2], HN["purity"], HN["purity_geography"])):
        rows += [f"# {lab}", f"+{me} | {f(a)} |", f"{ge} | {f(b)} |"]
    rows += ["Källa: Rundata; ristare med minst tre säkra stenar." if sv else "Source: Rundata; carvers with at least three secure stones.", ":::"]
    return "\n".join(rows)


def cand_list(sv):
    pv = {"Ög": "Östergötland", "Sm": "Småland", "Vg": "Västergötland", "M": "Medelpad"}
    return "; ".join(f"{g['name'] if sv else g['name'].replace('gruppen', ' group')} ({g['n']} {'stenar' if sv else 'stones'}, {pv[g['provinces'][0]]})" for g in CAND)


body = f"""*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, runristare, skrivmiljöer, attribuering, klustring, Gowers avstånd, validering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Vad som inte är prövat.** Gränserna valdes efter den första valideringen, och prövningen på ristare som hölls utanför var inte låst i en plan. Metoden är kalibrerad på ristarna i Uppland och Södermanland, och att den fungerar i Östergötland, Västergötland, Småland och Medelpad, där de möjliga okända ristarna finns, är inte prövat.
**Bakgrund och syfte.** Många runstenar saknar ristare, särskilt i Götaland. Frågan här är om stenar utan ristare kan grupperas efter handens drag så att en grupp blir en och samma ristare, och hur ofta det lyckas.
**Material.** {AN['n_stones']} svenska vikingatida runstenar med minst fem läsbara ord i Samnordisk runtextdatabas (Rundata): {AN['n_known']} med säker ristare och {AN['n_unattributed']} utan.
**Metod.** Stenarna jämförs i stilgrupp, kors, kortkvistrunor, språkdrag, skiljetecken, bindrunor, formler och runpar, men inte i plats och innehåll (Gowers avstånd). Stenar som liknar varandra lika mycket som en ristares stenar länkas och grupperas. Metoden prövas på kända ristare som hölls utanför, och grupperna prövas mot drag som inte ingår i likheten: bergart, storlek, namn och ovanliga stavningar.
**Resultat.** På ristare som hölls utanför bestod en grupp i medel till {pc(HO['purity'])} procent av samma ristare, mot {pc(HO['purity_geography'])} procent för lika många närliggande stenar, och grupperna var bättre i alla {HO['runs']} upprepningar. Bland stenarna utan ristare blev det {len(G)} grupper, varav {len(CAND)} möjliga skrivmiljöer utan känd ristare. De delar bergart (Holm-korrigerat p = 0,002), namn (0,035) och ovanliga stavningar ({pfmt(H5['H5']['p'])}) oftare än stenar ur samma trakt, men inte storlek.
**Slutsats.** Metoden hittar händer bland kända ristare och föreslår åtta skrivmiljöer utan namn, med Konungsund i Östergötland och Kölaby i Västergötland som de starkaste. Förslagen är hypoteser för en runologisk granskning, inte attribueringar.

## 1. Inledning

Runologer har länge grupperat osignerade stenar efter stil, runformer och stavning för att finna ristarna bakom dem (Axelson 1993; Stille 1999). Magnus Källström (2007) har talat om skriftmiljöer: bygder där ristare och beställare delade sätt att skriva. Laila Kitzler Åhfeldt (2002) har skilt ristare åt efter huggspåren. I Uppland har de flesta stenar en ristare i Rundata, men i Götaland bara en liten del, och där är frågan vilka händer som ligger bakom de många stenarna utan namn.

Syftet här är att redovisa en metod som grupperar stenar utan ristare efter handens drag och att visa hur ofta en sådan grupp blir en och samma ristare när metoden prövas på ristare den inte har sett. Inom konsthistorien får en okänd mästare ett arbetsnamn efter ett typverk; här får en grupp ett namn efter typstenens socken.

## 2. Förregistrering: vad som var bestämt i förväg och vad som inte var det

Metoden byggdes den 11 oktober 2026. Gränsen för att länka två stenar och den största tillåtna spridningen valdes efter den första valideringen på kända ristare, så den valideringen är något för optimistisk. Den 20 oktober prövades metoden på ristare som hölls utanför: gränserna togs fram på två tredjedelar av ristarna och prövades på den sista. Den prövningen var inte låst i en plan, men den gjordes på ristare som gränserna inte hade sett.

Den 29 oktober 2026 låstes två planer innan de kördes. Den första prövar grupperna mot drag som inte ingår i likheten: bergart, höjd och personnamn (SHA-256 `{SHA['2026-10-29-okanda-ristare-oberoende']}…`). Den andra prövar om gruppernas tidsspann ryms i en ristares livsgärning och om de delar ovanliga stavningar (SHA-256 `{SHA['2026-10-29-en-och-samma-mastare']}…`). Båda har en positiv kontroll på kända ristare.

## 3. Material

- **Stenarna.** {AN['n_stones']} svenska vikingatida runstenar i Samnordisk runtextdatabas (Rundata) med minst fem läsbara ord. {AN['n_known']} har en säker ristare och {AN['n_unattributed']} har ingen. Bara runstenar.
- **De kända ristarna.** {AN['coverage']['n_carvers']} ristare med minst tre säkra stenar: 25 i Uppland, 8 i Södermanland, en i Östergötland och en i Västmanland.
- **Täckningen.** I Uppland har {pc(SHARE['U'])} procent av stenarna en ristare i Rundata, i Södermanland {pc(SHARE['Sö'])}, men i Östergötland {pc(SHARE['Ög'])}, Småland {pc(SHARE['Sm'])}, Västergötland {pc(SHARE['Vg'])} och Medelpad {pc(SHARE['M'])} procent.
- **Handens drag.** Stilgrupp, kors, kortkvistrunor, språkdrag, skiljetecken, bindrunor, formler och de vanligaste runparen. Plats och innehåll ingår inte, så att en grupp inte bara blir en bygd eller ett slags budskap.
- **De oberoende dragen.** Bergart och höjd ur Rundata, personnamnen i texten, och ovanliga stavningar av vanliga ord.

## 4. Metod

**4.1 Likheten.** Gowers avstånd (Gower 1971) mellan varje par av stenar i handens drag.

**4.2 Gränsen.** Gränsen för att länka två stenar bestäms på par av stenar med känd ristare inom {CA['link_km']} km: par under gränsen ska vara minst {CA['lr_min']} gånger vanligare bland samma ristares par än bland olika ristares (i dag {str(round(CA['lr'], 1)).replace('.', ',')}). Av länkade par med känd ristare är då {pc(CA['precision'])} procent samma ristare.

**4.3 Grupperna.** Stenar utan ristare länkas när de ligger inom {CA['link_km']} km och under gränsen, och grupperas med Louvain-metoden (Blondel m.fl. 2008). En grupp redovisas när den har minst fyra stenar och inte är mer utspridd än 90 procent av de kända ristarna ({round(CA['max_spread_km'])} km). En grupp som liknar en känd ristare i närheten räknas som den ristarens, inte som en okänd.

**4.4 Valideringen.** Samma förfarande på stenar med känd ristare, som om ristaren vore okänd: hur stor del av en grupp är samma ristare, jämfört med lika många närliggande stenar? I prövningen på ristare som hölls utanför delas ristarna slumpvis i tre delar; gränserna tas fram på två och grupper bildas på den tredje, trettio gånger. En grupp räknas som robust när minst {pc(AN['robust_min'])} procent av den återkommer utan de drag som beror på tiden.

**4.5 De oberoende proven.** För varje grupp jämförs andelen par som delar bergart och namn, och skillnaden i höjd, med 9 999 slumpvisa mängder av stenar ur samma trakt ({OK['radius_km']} km) med samma fördelning på stilgrupper, Holm-korrigerat över de tre testen. Samma sak för ovanliga stavningar. Positiv kontroll: samma prov på {OK['control']['n_carvers']} kända ristare.

**4.6 Avvikelser.** Inga från de låsta planerna.

## 5. Resultat

**5.1 Valideringen på kända ristare.** I den första valideringen bestod en grupp i medel till {pc(VA['purity'])} procent av samma ristare, mot {pc(VA['purity_geography'])} procent för lika många närliggande stenar, och {pc(VA['share_pure'])} procent av grupperna var till minst tre fjärdedelar en ristare.

**5.2 Ristare som hölls utanför.** Med gränserna framtagna på andra ristare bestod en grupp i medel till {pc(HO['purity'])} procent av samma ristare, mot {pc(HO['purity_geography'])} procent för närliggande stenar: en skillnad på {pc(HO['difference'])} procentenheter (osäkerhet {pc(HO['difference_ci'][0])}–{pc(HO['difference_ci'][1])}), till gruppernas fördel i alla {HO['runs']} upprepningar. Utan de drag som beror på tiden: {pc(HN['purity'])} mot {pc(HN['purity_geography'])} procent. I klartext: när metoden får stenar av ristare den aldrig har sett, och samlar dem i grupper, är ungefär fem stenar av sex i en grupp av samma hand; stenar som bara står nära varandra är det i ungefär sju fall av tio.

{chart(True)}

**5.3 Grupperna bland stenarna utan ristare.** Det blev {len(G)} grupper. {len(G) - len(CAND)} liknar en känd ristare i närheten, nästan alla i Uppland och Södermanland. {len(CAND)} gör det inte och är möjliga skrivmiljöer utan namn: {cand_list(True)}. Fem av dem är robusta utan de tidsberoende dragen: {', '.join(ROB)}.

**5.4 De oberoende proven.** Den positiva kontrollen visar att provet ser en ristare: kända ristares stenar delar bergart ({pfmt(CO['rock']['p'])}), liknar varandra i höjd ({pfmt(CO['height']['p'])}) och delar personnamn ({pfmt(CO['names']['p'])}) oftare än traktens stenar. För de möjliga skrivmiljöerna:

- **Bergart – håller**, Holm-korrigerat p = 0,002. Bärs av Konungsundsgruppen ({pc(KON['rock']['obs'])} procent av paren delar bergart mot {pc(KON['rock']['null_mean'])} i trakten) och Kölabygruppen.
- **Höjd – faller**, p = 0,32; bara tre grupper har mått.
- **Namn – håller**, Holm-korrigerat p = 0,035, framför allt i Kölabygruppen. Kända ristare delar också namn, eftersom en ristare ofta gjorde flera stenar åt samma släkt, så delade namn skiljer inte en ristare från en släkts beställningar.
- **Ovanliga stavningar – håller**, {pfmt(H5['H5']['p'])}, burna av Kölaby ({pfmt(SP['Kölaby']['p'])}) och Konungsund ({pfmt(SP['Konungsund']['p'])}).
- **Tiden.** Spannet mellan gruppens äldsta och yngsta stilgrupp är {str(P1['Konungsund']['span']).replace('.', ',')} år för Konungsund, Kölaby och Leksberg, vilket ryms i en ristares livsgärning.

## 6. Diskussion

**Vad metoden klarar.** På ristare som den inte har sett samlar metoden stenar som till fem sjättedelar är av samma hand, klart bättre än närheten ensam. Grupperna av stenar utan ristare delar dessutom bergart och ovanliga stavningar, drag som grupperingen inte använder, och i den positiva kontrollen är det just så en ristares stenar beter sig. Konungsundsgruppen i Östergötland och Kölabygruppen i Västergötland är de starkaste förslagen till okända ristare.

**Mot tidigare forskning.** Metoden gör systematiskt det som runologer gör när de attribuerar efter stil och stavning (Axelson 1993; Stille 1999), och dess grupper motsvarar det Källström (2007) kallar skriftmiljöer. Den ersätter inte granskningen av stenarna, men den pekar ut var en granskning lönar sig.

**Svagheter, i ordning efter vikt.**

1. **Inte prövad där kandidaterna finns.** Gränsen är kalibrerad på ristarna i Uppland och Södermanland. I Götaland och Medelpad finns nästan inga kända ristare att pröva mot. Flyttad mellan Södermanland och Uppland gav gränsen inget säkert resultat (74 mot 61 procent).
2. **Gränserna valdes efter valideringen.** Den första valideringen är därför för optimistisk; prövningen på ristare som hölls utanför ger det ärligare måttet.
3. **Ristare eller skriftmiljö.** En grupp kan vara en ristare, en verkstad eller en bygds sätt att skriva. Delade namn kan vara en släkts beställningar.
4. **Rundatas attribueringar.** De kända ristarna, som metoden kalibreras på, är till stor del själva attribuerade efter stil och stavning.

**Var metoden inte ska användas.** Som attribuering: en grupp är en hypotes om en hand. Inte heller för enskilda stenar utanför en grupp.

**Vad som skulle fälla metoden.** Att grupperna föll isär när stenarna granskades på plats, eller att huggspårsanalyser visade flera händer i grupper som metoden ser som en.

## 7. Slutsats

En metod som grupperar runstenar efter handens drag samlar, prövad på ristare den inte sett, stenar som till {pc(HO['purity'])} procent är av samma ristare. Den föreslår {len(CAND)} skrivmiljöer utan namn, främst i Götaland, och de starkaste delar också bergart och stavningar. Nästa steg är en runologisk granskning av Konungsunds- och Kölabygrupperna och huggspårsanalyser av deras stenar.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 31 oktober 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod, analysplanerna och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Grupperingen och valideringen: `r/anonymous.R` (resultat `anonymous.json` under materialets version `{FP}`); prövningen på ristare som hölls utanför `utdata/ristare/ristare_heldout.R`.
- De oberoende proven: planerna `analysplaner/2026-10-29-okanda-ristare-oberoende.md` och `analysplaner/2026-10-29-en-och-samma-mastare.md`; koden och resultaten i `utdata/okanda_ristare/`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_skrivmiljoer.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer.
- I Vitki visas grupperna under Statistik, Skrivmiljöer, och stenarna i Forskningsluckor. Populär framställning: [Ristarna som aldrig blev ihågkomna](/artiklar/ristarna-som-aldrig-blev-ihagkomna).

## Referenser

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Blondel, V. D., Guillaume, J.-L., Lambiotte, R. & Lefebvre, E. 2008. Fast unfolding of communities in large networks. *Journal of Statistical Mechanics*, P10008.
- Gower, J. C. 1971. A general coefficient of similarity and some of its properties. *Biometrics* 27 (4), s. 857–871.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Archaeology B:9. Stockholm: Stockholms universitet.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholms universitet.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Institutionen för nordiska språk, Uppsala universitet.

:::box Det viktigaste i korthet
- Stenar utan ristare kan samlas efter hur de är skrivna, och prövat på kända ristare blir fem av sex stenar i en grupp samma hand.
- Åtta sådana skrivmiljöer utan namn finns, främst i Östergötland och Västergötland, där nästan inga ristare är kända.
- De är förslag till runologerna om var det lönar sig att leta efter en okänd ristare, inte attribueringar.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Methods report, partially tested. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, rune carvers, writing milieus, attribution, clustering, Gower distance, validation. Competing interests: none. Funding: none.*

## Abstract

**What has not been tested.** The limits were chosen after the first validation, and the test on carvers held out was not locked in a plan. The method is calibrated on the carvers of Uppland and Södermanland, and that it works in Östergötland, Västergötland, Småland and Medelpad, where the possible unknown carvers are, has not been tested.
**Background and aim.** Many runestones lack a carver, especially in Götaland. The question here is whether stones without a carver can be grouped by the features of the hand so that a group becomes one and the same carver, and how often that succeeds.
**Material.** {AN['n_stones']:,} Swedish Viking-Age runestones with at least five legible words in the Scandinavian Runic-text Database (Rundata): {AN['n_known']} with a secure carver and {AN['n_unattributed']} without.
**Method.** The stones are compared in style group, cross, short-twig runes, language traits, word dividers, bind-runes, formulas and rune pairs, but not in place and content (Gower distance). Stones as alike as a carver's stones are linked and grouped. The method is tested on known carvers held out, and the groups are tested against traits not in the similarity: rock type, size, names and unusual spellings.
**Results.** On carvers held out, a group consisted on average {pc(HO['purity'])} percent of the same carver, against {pc(HO['purity_geography'])} percent for as many nearby stones, and the groups were better in all {HO['runs']} repetitions. Among the stones without a carver there were {len(G)} groups, {len(CAND)} of them possible writing milieus without a known carver. They share rock type (Holm-corrected p = 0.002), names (0.035) and unusual spellings ({pfmt(H5['H5']['p'], True)}) more often than stones from the same district, but not size.
**Conclusion.** The method finds hands among known carvers and suggests eight writing milieus without names, with Konungsund in Östergötland and Kölaby in Västergötland as the strongest. The suggestions are hypotheses for a runological examination, not attributions.

## 1. Introduction

Runologists have long grouped unsigned stones by style, rune forms and spelling to find the carvers behind them (Axelson 1993; Stille 1999). Magnus Källström (2007) has spoken of writing milieus: districts where carvers and sponsors shared ways of writing. Laila Kitzler Åhfeldt (2002) has told carvers apart by their grooves. In Uppland most stones have a carver in Rundata, but in Götaland only a small part, and there the question is which hands lie behind the many stones without names.

The aim here is to report a method that groups stones without a carver by the features of the hand and to show how often such a group becomes one and the same carver when the method is tested on carvers it has not seen. In art history an unknown master is given a working name after a type work; here a group is named after the parish of its type stone.

## 2. Pre-registration: what was fixed in advance and what was not

The method was built on 11 October 2026. The limit for linking two stones and the largest spread allowed were chosen after the first validation on known carvers, so that validation is somewhat too optimistic. On 20 October the method was tested on carvers held out: the limits were derived on two thirds of the carvers and tested on the last. That test was not locked in a plan, but it was made on carvers the limits had not seen.

On 29 October 2026 two plans were locked before they were run. The first tests the groups against traits not in the similarity: rock type, height and personal names (SHA-256 `{SHA['2026-10-29-okanda-ristare-oberoende']}…`). The second tests whether the groups' time spans fit within a carver's working life and whether they share unusual spellings (SHA-256 `{SHA['2026-10-29-en-och-samma-mastare']}…`). Both have a positive control on known carvers.

## 3. Material

- **The stones.** {AN['n_stones']:,} Swedish Viking-Age runestones in the Scandinavian Runic-text Database (Rundata) with at least five legible words. {AN['n_known']} have a secure carver and {AN['n_unattributed']} have none. Runestones only.
- **The known carvers.** {AN['coverage']['n_carvers']} carvers with at least three secure stones: 25 in Uppland, 8 in Södermanland, one in Östergötland and one in Västmanland.
- **The coverage.** In Uppland {pc(SHARE['U'])} percent of the stones have a carver in Rundata, in Södermanland {pc(SHARE['Sö'])}, but in Östergötland {pc(SHARE['Ög'])}, Småland {pc(SHARE['Sm'])}, Västergötland {pc(SHARE['Vg'])} and Medelpad {pc(SHARE['M'])} percent.
- **The features of the hand.** Style group, cross, short-twig runes, language traits, word dividers, bind-runes, formulas and the most common rune pairs. Place and content are not included, so that a group does not merely become a district or a kind of message.
- **The independent traits.** Rock type and height from Rundata, the personal names in the text, and unusual spellings of common words.

## 4. Method

**4.1 The similarity.** Gower distance (Gower 1971) between every pair of stones in the features of the hand.

**4.2 The limit.** The limit for linking two stones is fixed on pairs of stones with a known carver within {CA['link_km']} km: pairs below the limit must be at least {CA['lr_min']} times more common among the same carver's pairs than among different carvers' (today {round(CA['lr'], 1)}). Of linked pairs with a known carver, {pc(CA['precision'])} percent are then the same carver.

**4.3 The groups.** Stones without a carver are linked when they lie within {CA['link_km']} km and below the limit, and grouped with the Louvain method (Blondel et al. 2008). A group is reported when it has at least four stones and is not more spread out than 90 percent of the known carvers ({round(CA['max_spread_km'])} km). A group resembling a known carver nearby counts as that carver's, not as an unknown.

**4.4 The validation.** The same procedure on stones with a known carver, as if the carver were unknown: how large a part of a group is the same carver, compared with as many nearby stones? In the test on carvers held out, the carvers are divided at random into three parts; the limits are derived on two and groups formed on the third, thirty times. A group counts as robust when at least {pc(AN['robust_min'])} percent of it recurs without the traits that depend on time.

**4.5 The independent tests.** For each group the share of pairs sharing rock type and names, and the difference in height, are compared with 9,999 random sets of stones from the same district ({OK['radius_km']} km) with the same distribution of style groups, Holm-corrected over the three tests. The same for unusual spellings. Positive control: the same test on {OK['control']['n_carvers']} known carvers.

**4.6 Deviations.** None from the locked plans.

## 5. Results

**5.1 The validation on known carvers.** In the first validation a group consisted on average {pc(VA['purity'])} percent of the same carver, against {pc(VA['purity_geography'])} percent for as many nearby stones, and {pc(VA['share_pure'])} percent of the groups were at least three quarters one carver.

**5.2 Carvers held out.** With the limits derived on other carvers, a group consisted on average {pc(HO['purity'])} percent of the same carver, against {pc(HO['purity_geography'])} percent for nearby stones: a difference of {pc(HO['difference'])} percentage points (uncertainty {pc(HO['difference_ci'][0])}–{pc(HO['difference_ci'][1])}), in the groups' favour in all {HO['runs']} repetitions. Without the traits that depend on time: {pc(HN['purity'])} against {pc(HN['purity_geography'])} percent. In plain words: when the method gets stones by carvers it has never seen and gathers them into groups, about five stones in six in a group are by the same hand; stones that merely stand close together are so in about seven cases out of ten.

{chart(False)}

**5.3 The groups among the stones without a carver.** There were {len(G)} groups. {len(G) - len(CAND)} resemble a known carver nearby, almost all in Uppland and Södermanland. {len(CAND)} do not and are possible writing milieus without names: {cand_list(False)}. Five of them are robust without the time-dependent traits: {', '.join(x.replace('gruppen', ' group') for x in ROB)}.

**5.4 The independent tests.** The positive control shows that the test sees a carver: known carvers' stones share rock type ({pfmt(CO['rock']['p'], True)}), resemble each other in height ({pfmt(CO['height']['p'], True)}) and share personal names ({pfmt(CO['names']['p'], True)}) more often than the district's stones. For the possible writing milieus:

- **Rock type – holds**, Holm-corrected p = 0.002. Carried by the Konungsund group ({pc(KON['rock']['obs'])} percent of the pairs share rock type against {pc(KON['rock']['null_mean'])} in the district) and the Kölaby group.
- **Height – fails**, p = 0.32; only three groups have measurements.
- **Names – holds**, Holm-corrected p = 0.035, above all in the Kölaby group. Known carvers share names too, since a carver often made several stones for the same family, so shared names do not tell a carver from a family's commissions.
- **Unusual spellings – holds**, {pfmt(H5['H5']['p'], True)}, carried by Kölaby ({pfmt(SP['Kölaby']['p'], True)}) and Konungsund ({pfmt(SP['Konungsund']['p'], True)}).
- **Time.** The span between the group's oldest and youngest style group is {P1['Konungsund']['span']} years for Konungsund, Kölaby and Leksberg, which fits within a carver's working life.

## 6. Discussion

**What the method can do.** On carvers it has not seen, the method gathers stones that are five sixths by the same hand, clearly better than proximity alone. The groups of stones without a carver also share rock type and unusual spellings, traits the grouping does not use, and in the positive control that is just how a carver's stones behave. The Konungsund group in Östergötland and the Kölaby group in Västergötland are the strongest suggestions of unknown carvers.

**Against earlier research.** The method does systematically what runologists do when they attribute by style and spelling (Axelson 1993; Stille 1999), and its groups correspond to what Källström (2007) calls writing milieus. It does not replace examination of the stones, but it points out where an examination pays.

**Weaknesses, in order of weight.**

1. **Not tested where the candidates are.** The limit is calibrated on the carvers of Uppland and Södermanland. In Götaland and Medelpad there are almost no known carvers to test against. Moved between Södermanland and Uppland the limit gave no clear result (74 against 61 percent).
2. **The limits were chosen after the validation.** The first validation is therefore too optimistic; the test on carvers held out gives the more honest measure.
3. **Carver or writing milieu.** A group may be a carver, a workshop or a district's way of writing. Shared names may be a family's commissions.
4. **Rundata's attributions.** The known carvers on which the method is calibrated are themselves largely attributed by style and spelling.

**Where the method should not be used.** As attribution: a group is a hypothesis about a hand. Nor for single stones outside a group.

**What would overturn the method.** If the groups fell apart when the stones were examined on site, or if groove analyses showed several hands in groups the method sees as one.

## 7. Conclusion

A method that groups runestones by the features of the hand gathers, tested on carvers it has not seen, stones that are {pc(HO['purity'])} percent by the same carver. It suggests {len(CAND)} writing milieus without names, mainly in Götaland, and the strongest also share rock type and spellings. The next step is a runological examination of the Konungsund and Kölaby groups and groove analyses of their stones.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 31 October 2026. No release with a DOI exists yet; when one is made, the report will refer to it. All code, the analysis plans and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The grouping and the validation: `r/anonymous.R` (results `anonymous.json` under the material's version `{FP}`); the test on carvers held out `utdata/ristare/ristare_heldout.R`.
- The independent tests: the plans `analysplaner/2026-10-29-okanda-ristare-oberoende.md` and `analysplaner/2026-10-29-en-och-samma-mastare.md`; the code and results in `utdata/okanda_ristare/`.
- The report is built by `utdata/blogg/build/build_rapport_skrivmiljoer.py`, which reads every number from the result files and stops if anything disagrees.
- In Vitki the groups are shown under Statistics, Writing milieus, and the stones in Research gaps. Popular account: [The carvers who were never remembered](/en/artiklar/ristarna-som-aldrig-blev-ihagkomna).

## References

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Blondel, V. D., Guillaume, J.-L., Lambiotte, R. & Lefebvre, E. 2008. Fast unfolding of communities in large networks. *Journal of Statistical Mechanics*, P10008.
- Gower, J. C. 1971. A general coefficient of similarity and some of its properties. *Biometrics* 27 (4), pp. 857–871.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Archaeology B:9. Stockholm: Stockholm University.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholm University.
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Department of Scandinavian Languages, Uppsala University.

:::box The essentials
- Stones without a carver can be gathered by how they are written, and tested on known carvers five of six stones in a group are the same hand.
- Eight such writing milieus without names exist, mainly in Östergötland and Västergötland, where almost no carvers are known.
- They are suggestions to runologists about where it pays to look for an unknown carver, not attributions.
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
       "body_en": body_en, "labels": ["Rapport", "Ristare"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_skrivmiljoer.json")
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
                 "topic": "Rapport|skrivmiljoer", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
