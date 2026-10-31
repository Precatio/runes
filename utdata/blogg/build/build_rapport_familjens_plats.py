"""Forskningsrapport (låst mall utdata/rapporter/MALL.md): "Runstenarna samlas i familjegrupper vid gravfälten" (sv + en).
Fyra förregistrerade studier (avståndet, grannstenarna, familjens plats, en generation; 2026-10-28/29) och den låsta
tilläggsplanen för robusthetstrappan (analysplaner/2026-10-31-familjens-plats-trappan.md). Alla siffror asserteras mot
resultatfilerna i utdata/avstand och utdata/familjens_plats.
    ../../../.venv/bin/python build_rapport_familjens_plats.py [--write | --update DOC]"""
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
REPORT_VERSION = 1
TODAY = "2026-10-31"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = "den första analysplanen låstes 2026-10-28; de följande planerna låstes 2026-10-29; materialet frystes 2026-10-29; tilläggsplanen och replikeringen låstes 2026-10-31"
TL_EN = "the first analysis plan was locked 2026-10-28; the following plans were locked 2026-10-29; the material was frozen 2026-10-29; the addendum and the replication were locked 2026-10-31"
FP = "3f58e9339191761e"
U = os.path.join(ROOT, "utdata")
J = lambda *p: json.load(open(os.path.join(U, *p), encoding="utf-8"))  # noqa: E731
AV, GR, GRT = J("avstand", "avstand.json"), J("avstand", "grannar.json"), J("avstand", "grannar_trappa.json")
REP = J("avstand", "replikering.json")
FPL, GEN, TRA = J("familjens_plats", "familjens_plats.json"), J("familjens_plats", "generation.json"), J("familjens_plats", "trappan.json")
SHA = {k: open(os.path.join(ROOT, "analysplaner", f"{k}.sha256" if k != "trappan" else "2026-10-31-familjens-plats-trappan.md.sha256")).read().split()[0][:16]
       for k in ("2026-10-28-avstand-mellan-stenar", "2026-10-28-avstand-mellan-stenar-tillagg", "2026-10-29-grannstenarna",
                 "2026-10-29-familjens-plats", "2026-10-29-en-generation", "trappan")}
SHA["replikering"] = open(os.path.join(ROOT, "analysplaner", "2026-10-31-avstand-replikering.md.sha256")).read().split()[0][:16]
assert SHA["replikering"] == "e1fb9abc5cf9ec88"
assert SHA["trappan"] == "ec4a17c59132e058" and SHA["2026-10-29-familjens-plats"] == "68361374fa670187"

d1 = lambda x: f"{x:.1f}".replace(".", ",")  # noqa: E731
d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731
pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731


def pfmt(p, en=False):
    if p < 0.001:
        return "p < 0.001" if en else "p < 0,001"
    s = f"{p:.3f}" if p < 0.01 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- 1. the spacing (DCLF) -------------------------------------------------------------------------------------------
AU, AS = AV["provinces"]["U"], AV["provinces"]["Sö"]
assert (AU["n_stones"], AU["n_sites"], AS["n_stones"], AS["n_sites"]) == (458, 420, 168, 149)
assert (AU["main"]["p"], AS["main"]["p"], AU["main"]["p_holm"], AS["main"]["p_holm"]) == (0.004, 0.003, 0.006, 0.006)
assert AU["main"]["direction"] == AS["main"]["direction"] == "klumpat"
assert all(h["p"] < 0.05 for h in list(AU["halves"].values()) + list(AS["halves"].values()))
assert max(list(AU["robustness"].values()) + list(AS["robustness"].values()), key=lambda r: r["p"])["p"] <= 0.005
NN_U, NN_S = AU["nearest_m"]["50%"], AS["nearest_m"]["50%"]
# the replication in Götaland (analysplaner/2026-10-31-avstand-replikering.md): the corrected method, unchanged, on stones
# that had been in no spacing analysis
assert REP["status"] == "replikerat" and (REP["main"]["n_stones"], REP["main"]["n"], REP["main"]["p"], REP["main"]["direction"]) == (167, 158, 0.004, "klumpat")
RH = REP["halves"]
assert (RH["vast"]["p"], RH["ost"]["p"], RH["vast"]["direction"], RH["ost"]["direction"]) == (0.023, 0.011, "klumpat", "klumpat")
RP = REP["provinces"]
assert {k: (v["p"], v["direction"], v["n_stones"]) for k, v in RP.items()} == {"Ög": (0.199, "klumpat", 59), "Vg": (0.003, "klumpat", 56), "Sm": (0.023, "klumpat", 52)}
assert (REP["sigma_m"], REP["floor"], REP["nsim"], REP["rinterval_m"]) == (AV["sigma_m"], AV["floor"], AV["nsim"], AV["rinterval_m"])
assert (round(NN_U / 100) / 10, round(NN_S / 100) / 10, round(AU["nearest_m"]["10%"], -1)) == (1.1, 1.4, 170)

# ---- 2. the shared names ---------------------------------------------------------------------------------------------
GN = GR["main"]["samma_namn"]
assert (round(GN["ratio"], 1), GN["near_pairs"], GN["far_pairs"], round(100 * GN["share_near"], 1), round(100 * GN["share_far"], 1)) == (7.9, 74, 4983, 17.6, 2.2)
assert 0.001 < GN["p_holm"] < 0.002 and GN["utslag"] == "håller" and GR["n_stones"] == 626
GC, GS = GR["main"]["samma_ristare"], GR["main"]["samma_stilgrupp"]
assert GC["utslag"] == GS["utslag"] == "antydan" and (round(GC["ratio"], 1), round(GS["ratio"], 1)) == (2.2, 1.6)
assert all(GR["main"][k]["utslag"] == "ingen skillnad påvisad" for k in ("bro", "resa", "kristen"))
BR = GRT["rungs"]
assert all(r["holds"] for r in BR.values()) and set(BR) == {"main", "half_A", "half_B", "only_U", "only_Sö", "no_same_carver", "moved_runor"}
assert [round(BR[k]["ratio"], 1) for k in ("half_A", "half_B", "only_U", "only_Sö", "no_same_carver", "moved_runor")] == [9.3, 5.8, 8.2, 5.8, 7.1, 9.6]
assert BR["only_Sö"]["p"] > 0.05 and BR["only_Sö"]["near_pairs"] == 11 and BR["only_U"]["p"] < 0.001

# ---- 3. the grave fields ---------------------------------------------------------------------------------------------
T1 = next(t for t in FPL["tests"] if t["key"] == "y1_gravfalt")
M1 = T1["main"]
assert (FPL["n_grupp"], FPL["n_ensam"], pc(M1["share_grupp"]), pc(M1["share_ensam"]), d2(M1["or"])) == (185, 472, 82, 55, "2,38")
assert M1["p"] < 0.001 and 0.003 < T1["p_holm"] < 0.004
OTHER = {t["key"]: t for t in FPL["tests"]}
assert all(OTHER[k]["p_holm"] > 0.3 for k in ("y2_hog", "y3_vag", "y4_grans", "y6_gammalt_namn", "y7_ungt_namn", "y8_kultnamn"))
assert d2(OTHER["y9_centralort"]["main"]["or"]) == "0,53" and 0.04 < OTHER["y9_centralort"]["p_holm"] < 0.05
assert pc(OTHER["y3_vag"]["main"]["share_grupp"]) == 26 and pc(OTHER["y3_vag"]["main"]["share_ensam"]) == 16
assert pc(OTHER["y4_grans"]["main"]["share_grupp"]) == 7 and pc(OTHER["y4_grans"]["main"]["share_ensam"]) == 6
RA = TRA["rungs"]
assert all(r["holds"] for r in RA.values()) and (TRA["n"], TRA["n_grupp"], TRA["n_ensam"]) == (657, 185, 472)
assert [d2(RA[k]["or"]) for k in ("raw", "adjusted", "carver", "parish", "place", "half_A", "half_B", "moved_runor")] == \
    ["3,59", "2,38", "2,49", "2,45", "2,45", "2,27", "2,53", "2,64"]
LOP = TRA["lopo"]
assert (LOP["U"]["share_left"] < 0.5, d2(LOP["U"]["or"]), LOP["U"]["p"] > 0.3) == (True, "1,44", True)
assert all(LOP[p]["or"] > 1 and LOP[p]["p"] < 0.01 for p in LOP if p != "U")

# ---- 4. one generation -----------------------------------------------------------------------------------------------
G = GEN["main"]
assert (G["groups"], G["stones"], d2(G["mean_styles"]), d2(G["expected"]), G["p"]) == (36, 84, "1,58", "1,93", 0.0001)
assert (pc(G["share_all_same"]), pc(G["share_all_same_expected"]), round(G["span_years"]), round(G["span_expected"])) == (47, 21, 20, 36)
assert G["provinces"] == {"U": 32, "Sö": 4} and GEN["status"] == "håller"
GH = GEN["halves"]
assert GH["A"]["p"] < 0.005 and GH["B"]["p"] < 0.005
GR_ = GEN["robustness"]
assert all(r["p"] < 0.05 for r in GR_.values())
NOC = next(r for k, r in GR_.items() if "ristare" in k or "carver" in k)
assert (NOC["groups"], d2(NOC["mean_styles"]), d2(NOC["expected"]), round(NOC["p"], 2)) == (28, "1,71", "1,96", 0.01)

SLUG = "familjegrupper-vid-gravfalten"
title = "Runstenarna samlas i familjegrupper vid gravfälten – grannstenar nämner samma personer åtta gånger oftare"
title_en = "Runestones gather in family groups by the grave fields – neighbouring stones name the same people eight times as often"
summary = ("Förregistrerad studie i fyra steg. Runstenar som står kvar på sin plats ligger närmare varandra än slumpen ger. Stenar "
           "inom 500 meter från varandra nämner samma personer åtta gånger så ofta som stenar längre bort, grupperna står vid "
           "gravfält oftare än ensamma stenar, och en grupp restes oftast inom en generation. Runstenen var familjens monument vid familjens gravfält.")
summary_en = ("Pre-registered study in four steps. Runestones that stand in place lie closer to one another than chance would give. "
              "Stones within 500 metres of each other name the same people eight times as often as stones further apart, the groups "
              "stand by grave fields more often than lone stones, and a group was usually raised within one generation. The runestone "
              "was the family's monument by the family's grave field.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/forskningsrapporter/{SLUG}")


def chart(sv):
    rows = [":::chart Grupper mot ensamma stenar och nära mot avlägsna stenpar" if sv else ":::chart Groups against lone stones, and near against distant pairs",
            "# " + ("Gravfält inom 500 m" if sv else "Grave field within 500 m"),
            f"+{'Sten i grupp' if sv else 'Stone in a group'} | {pc(M1['share_grupp'])} | {FPL['n_grupp']} {'stenar' if sv else 'stones'}",
            f"{'Ensam sten' if sv else 'Lone stone'} | {pc(M1['share_ensam'])} | {FPL['n_ensam']} {'stenar' if sv else 'stones'}",
            "# " + ("Samma personnamn" if sv else "The same personal name"),
            f"+{'Nära par, 25–500 m' if sv else 'Near pairs, 25–500 m'} | {d1(100 * GN['share_near']) if sv else f'{100 * GN['share_near']:.1f}'} | {GN['near_pairs']} {'par' if sv else 'pairs'}",
            f"{'Jämförelsepar, 2–10 km' if sv else 'Comparison pairs, 2–10 km'} | {d1(100 * GN['share_far']) if sv else f'{100 * GN['share_far']:.1f}'} | {GN['far_pairs']} {'par' if sv else 'pairs'}",
            ("Källa: Rundata; gravfält ur Riksantikvarieämbetets kulturmiljöregister. Råa andelar." if sv else
             "Source: Rundata; grave fields from the Swedish National Heritage Board's register. Raw shares."),
            ":::"]
    return "\n".join(rows)


body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, gravfält, familj, stengrupper, rumslig statistik, punktmönster, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Var runstenarna restes har diskuterats länge: vid gravfält, vid vägar och broar, vid gårdens gränser. Frågan här är om stenarna bildar grupper, vad stenarna i en grupp har gemensamt och var grupperna står – mätt på hela materialet, med tätheten i bygden konstant.
**Material.** Runstenar som står kvar på sin plats i Rundata: {AU['n_stones']} i Uppland och {AS['n_stones']} i Södermanland för mönstret och namnen, {REP['main']['n_stones']} i Östergötland, Västergötland och Småland för en replikering av mönstret, och {TRA['n']} i de svenska landskapen för gravfälten, med gravfält ur Riksantikvarieämbetets kulturmiljöregister.
**Metod.** Fyra förregistrerade studier: ett test av punktmönstret mot en bygd med varierande täthet (999 simuleringar), förregistrerat replikerat på nya stenar, en jämförelse av nära och avlägsna stenpar (9 999 omblandningar), en logistisk regression för gravfält i grupp mot ensam sten, och en omblandning av stilgrupper inom bygden. De två huvudtesten har gått en fast serie känslighetsanalyser enligt en låst tilläggsplan.
**Resultat.** Stenarna ligger närmare varandra än slumpen ger på 100–1 000 meter i Uppland och Södermanland, och samma test ger samma utslag på stenarna i Götaland ({pfmt(REP['main']['p'])}). Stenar inom 500 meter från varandra nämner samma person i {d1(100 * GN['share_near'])} procent av paren mot {d1(100 * GN['share_far'])} procent på 2–10 kilometers avstånd: {d1(GN['ratio'])} gånger så ofta. {pc(M1['share_grupp'])} procent av stenarna i grupp har ett gravfält inom 500 meter mot {pc(M1['share_ensam'])} procent av de ensamma; oddskvot {d2(M1['or'])}. En grupp har i medel {d2(G['mean_styles'])} olika stilgrupper mot {d2(G['expected'])} för lika många stenar ur samma bygd. Vägar, gränsmärken och maktens ortnamn skiljer inte grupperna från de ensamma stenarna.
**Slutsats.** Runstenarna står ofta i grupper som är familjens: samma människor, vid familjens gravfält, resta inom en generation. Fynden bärs i hög grad av Uppland.

## 1. Inledning

Gunnar Ekholm (1950) frågade var runstenarna restes och var skeptisk till tanken att ensamma stenar markerar bortodlade gravfält. Torun Zachrisson (1998) har i sin studie av Uppland och Gästrikland satt runstenarna i samband med gård, gräns och gravfält och föreslagit att stenar vid gårdens gränser skyddade gården. Lydia Klos (2009) har hävdat att de flesta runstenar ursprungligen restes vid gravfält, en slutsats som Shane McLeod (2014) menar överbetonar gravfälten på bekostnad av andra platser, som vägarna. Birgit Sawyer (2000) läste stenarna som uttryck för familj och arv, och grupper som Jarlabankes stenar i Täby och Vallentuna har länge setts som en släkts monument.

Det som saknas är ett mått på hela materialet: om stenarna faktiskt bildar grupper mer än slumpen ger när bygdens täthet hålls konstant, om stenarna i en grupp hör ihop genom människor eller genom vägar och broar, och om grupperna står på andra platser än de ensamma stenarna. Syftet med studien är att mäta det, i fyra steg som vart och ett förregistrerades innan det kördes.

## 2. Förregistrering: hypoteser och planer

Studien består av fyra förregistrerade steg och en tilläggsplan. Varje plan skrevs ned och tidsstämplades i projektets versionshantering innan analysen kördes; kontrollsummorna (SHA-256) står nedan och filerna under Data och kod.

1. **Avståndet** (28 oktober 2026, `{SHA['2026-10-28-avstand-mellan-stenar']}…`, tillägg `{SHA['2026-10-28-avstand-mellan-stenar-tillagg']}…`; replikering 31 oktober, `{SHA['replikering']}…`): står stenar som är kvar på sin plats närmare varandra än slumpen ger på 100–1 000 meter, med bygdens täthet konstant? Prövat i Uppland och Södermanland, och med samma metod på stenarna i Östergötland, Västergötland och Småland.
2. **Grannstenarna** (29 oktober, `{SHA['2026-10-29-grannstenarna']}…`): har nära stenpar (25–500 meter) oftare samma personnamn, samma ristare, samma stilgrupp eller samma budskap än stenpar på 2–10 kilometers avstånd? Sex test, Holm-korrigerade.
3. **Familjens plats** (29 oktober, `{SHA['2026-10-29-familjens-plats']}…`): står stenar i grupp (en annan sten 25–500 meter bort) oftare än ensamma stenar (närmaste sten över 1 kilometer bort) vid gravfält, gravhögar, vägar, gränsmärken, kyrkor och vissa ortnamn? Femton test, Holm-korrigerade.
4. **En generation** (29 oktober, `{SHA['2026-10-29-en-generation']}…`): har grupperna färre olika stilgrupper än lika många stenar dragna ur samma bygd?
5. **Tilläggsplanen** (31 oktober, `{SHA['trappan']}…`): samma fasta serie känslighetsanalyser som projektets alla andra samband går igenom, lagd på steg 2 (namnen) och steg 3 (gravfälten). Den skrevs efter att de fyra resultaten var kända men innan känslighetsanalyserna kördes, och den lägger inte till några nya utfall.

Två saker ska sägas om ordningen. Steg 4 formulerades efter en iakttagelse i steg 3: där var ett ensidigt test av *fler* stilgrupper än slumpen ställt, och utfallet gick kraftigt åt motsatt håll. Den nya planen prövade det motsatta med en striktare jämförelse (omblandning inom bygden i stället för inom landskapet), men på samma stenar. Steg 4 är alltså förregistrerat, men inte prövat på oberoende data. I steg 1 fick metoden rättas efter den första körningen i Uppland och Södermanland (se 4.6). Därför prövades den rättade metoden oförändrad, enligt en ny låst plan, på stenarna i Östergötland, Västergötland och Småland, som inte hade ingått i någon avståndsanalys. Det är den prövningen som bär steg 1.

## 3. Material

- **Källa.** Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk vid Uppsala universitet, i den version som frystes för analyserna den 28–29 oktober 2026. Gravfält, gravhögar, färdvägar och gränsmärken ur Riksantikvarieämbetets kulturmiljöregister; ortnamn ur projektets ortnamnstabell.
- **Stenarna.** Bara runstenar som enligt Rundata står kvar på sin ursprungliga plats och har känt läge; flyttade och försvunna stenar ingår inte, eftersom deras plats inte säger var de restes. Steg 1 och 2 gäller Uppland och Södermanland, där stenarna är flest ({AU['n_stones']} och {AS['n_stones']} stenar, {AU['n_sites']} och {AS['n_sites']} platser när stenar inom 25 meter räknas som en plats). Replikeringen av steg 1 gäller {REP['main']['n_stones']} stenar på plats i Östergötland ({RP['Ög']['n_stones']}), Västergötland ({RP['Vg']['n_stones']}) och Småland ({RP['Sm']['n_stones']}), de enda landskap utöver Uppland och Södermanland med tillräckligt många stenar kvar. Steg 3 gäller alla svenska landskap: {FPL['n_grupp']} stenar i grupp och {FPL['n_ensam']} ensamma.
- **Personnamnen** är resarnas och de dödas namn, lästa ur inskriften med projektets namnmodell. De 20 vanligaste namnen i hela materialet räknas inte, så att ett par inte delar namn bara för att namnet var vanligt.
- **Datering** efter stenens ornamentikstil (Gräslund 2006). En stilgrupp täcker 25–50 år.
- **Ristaren.** Den ristare Rundata anger, säker eller osäker.

## 4. Metod

**4.1 Punktmönstret.** Ripleys L-funktion för stenarnas platser, jämförd med ett inhomogent Poisson-mönster vars täthet är bygdens (kärnutjämning med 10 kilometers bandbredd och ett golv på 5 procent av medeltätheten), med ett DCLF-test över 100–1 000 meter mot 999 simuleringar (Baddeley m.fl. 2015). Uppland och Södermanland var för sig, Holm-korrigerade. Replikeringen använder exakt samma metod, med de tre götaländska landskapen som ett mönster; den räknas som lyckad om p är under 0,05, mönstret är klumpat och samma riktning gäller i båda halvorna.

**4.2 Grannstenarna.** För varje egenskap: andelen nära par som delar den, genom andelen jämförelsepar som delar den. p-värdet kommer från 9 999 omblandningar av stenarnas egenskaper inom landskapet, med platserna fasta.

**4.3 Gravfälten.** Logistisk regression: gravfält inom 500 meter ~ i grupp + landskap + dateringsperiod + lokal täthet av stenar, så att en tät bygd inte i sig räknas som ett gravfältsmönster.

**4.4 En generation.** För varje grupp med minst två stildaterade stenar: antalet olika stilgrupper, jämfört med lika många stenar dragna 9 999 gånger ur samma bygd (inom 10 kilometer, utom gruppens egen plats).

**4.5 Känslighetsanalyser** (tilläggsplanen). Gravfälten: rå modell; planens modell; ristaren som slumpeffekt (Bates m.fl. 2015); socknen som slumpeffekt; stenens läge som rumslig yta (Wood 2017); var halva för sig; utan ett landskap i taget; utan stenar som Riksantikvarieämbetets register Runor (2020) anger som flyttade. Namnen: huvudmåttet; var halva för sig; varje landskap för sig; utan par med samma säkra ristare; utan flyttade stenar enligt Runor. Halvorna är projektets fasta: hela socknar växelvis inom varje landskap. Ett steg håller när effekten går åt samma håll och p är under 0,05; när ett landskap tas bort, eller ett landskap prövas ensamt, krävs signifikans bara där minst två tredjedelar av materialet finns kvar.

**4.6 Avvikelser från planerna.** I steg 1 gav planens bandbredd på 2 kilometer stenar utan grannar en täthet nära noll, så att testet inte mätte något; en kalibrering på slumpmönster visade felet. Körningen redovisas som ogiltig, och ett tillägg med 10 kilometers bandbredd och ett golv låstes innan den nya körningen. Eftersom metoden rättades efter en körning på samma stenar prövades den sedan oförändrad på nya stenar (replikeringen); där gjordes bara en provkörning med 19 simuleringar för att hitta kodfel. I steg 3 slogs landskap med under tio stenar ihop. I övrigt inga avvikelser.

## 5. Resultat

**5.1 Stenarna bildar grupper.** Stenarna ligger närmare varandra än slumpen ger på 100–1 000 meter: Uppland {pfmt(AU['main']['p'])}, Södermanland {pfmt(AS['main']['p'])} (Holm-korrigerat 0,006 båda), i båda halvorna och med alla bandbredder och golv i robusthetsproven (p mellan 0,001 och 0,005). Medianavståndet till närmaste sten är {d1(NN_U / 1000)} kilometer i Uppland och {d1(NN_S / 1000)} i Södermanland, men var tionde sten har en granne inom ungefär 200 meter. Replikeringen på stenarna i Östergötland, Västergötland och Småland ger samma utslag: klumpat, {pfmt(REP['main']['p'])}, och i båda halvorna (väster {pfmt(RH['vast']['p'])}, öster {pfmt(RH['ost']['p'])}). Var för sig är Västergötland ({pfmt(RP['Vg']['p'])}) och Småland ({pfmt(RP['Sm']['p'])}) klumpade; Östergötland går åt samma håll men är för litet för att vara säkert ({pfmt(RP['Ög']['p'])}). En sten per gård, jämnt utspridda, får inget stöd.

**5.2 Grannstenarna nämner samma människor.** Av de nära paren där båda stenarna har namn delar {d1(100 * GN['share_near'])} procent ett personnamn ({GN['near_pairs']} par), mot {d1(100 * GN['share_far'])} procent av jämförelseparen ({GN['far_pairs']} par): {d1(GN['ratio'])} gånger så ofta, Holm-korrigerat {pfmt(GN['p_holm'])}. Samma ristare ({d1(GC['ratio'])} gånger) och samma stilgrupp ({d1(GS['ratio'])} gånger) är antydningar; broar, resor och kristna kännetecken gör grannarna inte mer lika. Känslighetsanalyserna håller alla:

- Halva A: kvot {d1(BR['half_A']['ratio'])} ({BR['half_A']['near_pairs']} nära par), {pfmt(BR['half_A']['p'])}. Halva B: {d1(BR['half_B']['ratio'])} ({BR['half_B']['near_pairs']}), {pfmt(BR['half_B']['p'])}.
- Bara Uppland: {d1(BR['only_U']['ratio'])} ({BR['only_U']['near_pairs']} nära par, {pc(BR['only_U']['share_of_pairs'])} procent av paren), {pfmt(BR['only_U']['p'])}. Bara Södermanland: {d1(BR['only_Sö']['ratio'])} ({BR['only_Sö']['near_pairs']} nära par), {pfmt(BR['only_Sö']['p'])} – samma riktning, men för få par för att vara säkert.
- Utan par där båda stenarna har samma säkra ristare: {d1(BR['no_same_carver']['ratio'])}, {pfmt(BR['no_same_carver']['p'])}.
- Utan stenar som Runor anger som flyttade: {d1(BR['moved_runor']['ratio'])}, {pfmt(BR['moved_runor']['p'])}.

**5.3 Grupperna står vid gravfälten.** {pc(M1['share_grupp'])} procent av stenarna i grupp har ett gravfält inom 500 meter, mot {pc(M1['share_ensam'])} procent av de ensamma. Med landskap, dateringsperiod och lokal täthet konstanta är oddskvoten {d2(M1['or'])} ({d2(M1['lo'])}–{d2(M1['hi'])}), {pfmt(M1['p'])}, Holm-korrigerat {pfmt(T1['p_holm'])}. Känslighetsanalyserna håller alla:

- Rå modell: oddskvot {d2(RA['raw']['or'])}. Ristaren som slumpeffekt ({RA['carver']['groups']} grupper): {d2(RA['carver']['or'])}, {pfmt(RA['carver']['p'])}. Socknen som slumpeffekt ({RA['parish']['groups']} socknar): {d2(RA['parish']['or'])}, {pfmt(RA['parish']['p'])}. Läget som rumslig yta: {d2(RA['place']['or'])}, {pfmt(RA['place']['p'])}.
- Halva A: {d2(RA['half_A']['or'])}, {pfmt(RA['half_A']['p'])}. Halva B: {d2(RA['half_B']['or'])}, {pfmt(RA['half_B']['p'])}.
- Utan flyttade stenar enligt Runor ({RA['moved_runor']['n']} stenar): {d2(RA['moved_runor']['or'])}, {pfmt(RA['moved_runor']['p'])}.
- Utan ett landskap i taget: oddskvoten ligger mellan {d2(min(LOP[p]['or'] for p in LOP if p != 'U'))} och {d2(max(LOP[p]['or'] for p in LOP if p != 'U'))} utan Östergötland, Småland, Södermanland och Västergötland. Utan Uppland, när bara {pc(LOP['U']['share_left'])} procent av stenarna är kvar, är den {d2(LOP['U']['or'])} och inte signifikant ({pfmt(LOP['U']['p'])}); riktningen håller, men skillnaden bärs i hög grad av Uppland.

Gravhögar, färdvägar och gränsmärken skiljer inte grupperna från de ensamma stenarna: färdväg inom 500 meter {pc(OTHER['y3_vag']['main']['share_grupp'])} mot {pc(OTHER['y3_vag']['main']['share_ensam'])} procent, gränsmärke {pc(OTHER['y4_grans']['main']['share_grupp'])} mot {pc(OTHER['y4_grans']['main']['share_ensam'])} procent, båda utan påvisad skillnad. Ortnamn på Husby och -tuna ligger tvärtom något *mer sällan* nära grupperna när tätheten hålls konstant (oddskvot {d2(OTHER['y9_centralort']['main']['or'])}, Holm {d2(OTHER['y9_centralort']['p_holm'])}, en antydan).

{chart(True)}

**5.4 En grupp restes inom en generation.** {G['groups']} grupper med {G['stones']} stildaterade stenar ({G['provinces']['U']} i Uppland, {G['provinces']['Sö']} i Södermanland) har i medel {d2(G['mean_styles'])} olika stilgrupper, mot {d2(G['expected'])} för lika många stenar ur samma bygd, {pfmt(G['p'])}; halva A {pfmt(GH['A']['p'])}, halva B {pfmt(GH['B']['p'])}. {pc(G['share_all_same'])} procent av grupperna har alla stenar i samma stilgrupp mot {pc(G['share_all_same_expected'])} procent väntat, och spannet mellan gruppens tidigaste och senaste sten är i medel {round(G['span_years'])} år mot {round(G['span_expected'])} år. Utan grupper där en och samma ristare gjort alla stenar ({NOC['groups']} grupper kvar) är det {d2(NOC['mean_styles'])} mot {d2(NOC['expected'])}, {pfmt(NOC['p'])}: svagare, men kvar. Exempel är Täby (U 135, 136, 137 och 140, alla i stilgrupp Pr2) och Skokloster (U 685, 686 och 689, alla Pr2); motexempel med tidsdjup finns, som Vårfrukyrka (Fp och Pr4).

**I klartext.** Runstenarna står närmare varandra än slumpen ger. Två stenar inom 500 meter från varandra nämner samma person ungefär åtta gånger så ofta som två stenar som står 2–10 kilometer isär. Stenar i en sådan grupp står vid ett gravfält i fyra fall av fem, de ensamma i drygt hälften av fallen, och stenarna i en grupp ligger närmare varandra i tid än stenar ur samma bygd: i medel tjugo år mellan den tidigaste och den senaste.

## 6. Diskussion

**Vad fynden säger.** Fyra mätningar pekar åt samma håll. Runstenar samlas i grupper på några hundra meter, stenarna i en grupp nämner samma människor, grupperna står vid gravfälten, och en grupp restes på kort tid. Den enklaste läsningen är att gruppen är familjens plats: en familj som under en generation reste flera stenar vid sitt gravfält, efter far, söner och bröder. Vägarna och broarna förklarar inte grupperna – grannstenar är inte oftare båda brostenar eller resestenar, och grupperna står inte oftare vid färdvägar än de ensamma stenarna.

**Mot tidigare forskning.** Fynden ger stöd åt Klos (2009) i att gravfältet var en huvudplats för runstenar, men preciserar det: det är framför allt *grupperna* som står vid gravfälten, medan drygt hälften av de ensamma stenarna också gör det. Zachrissons (1998) gränsstenar och de vägstenar som McLeod (2014) framhåller får inget stöd i jämförelsen grupp mot ensam – vilket inte utesluter att enskilda stenar stod vid gränser och vägar, men säger att det inte är det som skiljer familjens samlade plats från den ensamma stenen. Ekholms (1950) skepsis mot att ensamma stenar markerar bortodlade gravfält stämmer med att de ensamma stenarna mer sällan har ett gravfält nära. Att grupperna restes inom en generation har, så vitt vi har kunnat se, inte prövats statistiskt tidigare.

**Svagheter, i ordning efter vikt.**

1. **Uppland bär mycket.** {G['provinces']['U']} av {G['groups']} grupper i generationsprovet och {pc(BR['only_U']['share_of_pairs'])} procent av de nära paren i namnprovet ligger i Uppland, och utan Uppland är gravfältsskillnaden inte signifikant. Att stenarna klumpar sig gäller också i Götaland, men namnen, gravfälten och generationen gäller i första hand Uppland, där stenarna står kvar och är flest.
2. **Bara stenar på plats.** Omkring en tredjedel av runstenarna står kvar där de restes. Om flyttade stenar oftare kom från grupper eller från ensamma platser, påverkar det jämförelserna.
3. **Registret är inte fullständigt.** Ett gravfält som är bortodlat finns inte i registret. Det kan göra ensamma stenar ensamma i registret fast de en gång stod vid ett gravfält – Ekholms invändning åt andra hållet.
4. **Steg 4 vilar på samma stenar som iakttagelsen bakom det,** och stilgrupperna är 25–50 år breda. ”En generation” betyder här: kortare tid än slumpen ger i samma bygd.
5. **Namnen är lästa med regler,** och ett namn kan bäras av olika personer. Att de vanligaste namnen räknas bort minskar men tar inte bort den risken.

**Vad som skulle fälla fynden.** Att namnlikheten försvann när ristaren eller beställarens formel hölls konstant, att grupperna visade sig följa vägar när ett fullständigare vägregister användes, eller att generationsmönstret inte gick igen i ett annat landskap med många stenar på plats.

## 7. Slutsats

Runstenarna står ofta i grupper – i Uppland och Södermanland, och enligt en förregistrerad replikering också i Götaland – och grupperna är familjens: stenar inom 500 meter från varandra nämner samma människor åtta gånger så ofta som stenar längre bort, grupperna står vid gravfält oftare än ensamma stenar, och en grupp restes oftast inom en generation. Det gäller i första hand Uppland. Nästa steg är att se om samma familjer återkommer på flera platser, och vad som skiljer de ensamma stenarnas platser.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 31 oktober 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod, analysplanerna och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Analysplanerna: `analysplaner/2026-10-28-avstand-mellan-stenar.md` med tillägget, `analysplaner/2026-10-29-grannstenarna.md`, `analysplaner/2026-10-29-familjens-plats.md`, `analysplaner/2026-10-29-en-generation.md` och `analysplaner/2026-10-31-familjens-plats-trappan.md`, var och en med sin `.sha256`-fil.
- Avståndet: `utdata/avstand/avstand.R`; replikeringen `utdata/avstand/replikering.R` med planen `analysplaner/2026-10-31-avstand-replikering.md`. Grannstenarna: `utdata/avstand/grannar.py` och `utdata/avstand/grannar_trappa.py`.
- Familjens plats och generationen: `utdata/familjens_plats/data.py`, `utdata/familjens_plats/analys.R`, `utdata/familjens_plats/generation.py` och `utdata/familjens_plats/trappa.R`; resultat och avvikelser i `resultat.md`, `generation_resultat.md` och `trappan_resultat.md` i samma mappar.
- Materialets version: korpus `{FP}`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_familjens_plats.py`, som läser varje siffra ur resultatfilerna och stannar om något inte stämmer.

## Referenser

- Baddeley, A., Rubak, E. & Turner, R. 2015. *Spatial Point Patterns: Methodology and Applications with R*. Boca Raton: Chapman & Hall/CRC.
- Bates, D., Mächler, M., Bolker, B. & Walker, S. 2015. Fitting linear mixed-effects models using lme4. *Journal of Statistical Software* 67 (1), s. 1–48.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, s. 137 ff.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- McLeod, S. 2014. The rediscovery of U 170: runestones, churchyards, and burial grounds in Sweden. *Journal of the North Atlantic* 25. doi:10.3721/037.006.2503
- Riksantikvarieämbetet. Kulturmiljöregistret (fornlämningar); *Runor* (runinskriftsregister), uttag 2020.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2 uppl. Boca Raton: Chapman & Hall/CRC.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholms universitet.

:::box Det viktigaste i korthet
- Runstenarna står ofta i grupper, och stenarna i en grupp nämner samma människor – åtta gånger oftare än stenar längre bort.
- Grupperna står vid gravfälten och restes oftast inom en generation: familjens monument vid familjens gravplats, inte vägens eller gränsens.
- Mönstret är tydligast i Uppland, där stenarna står kvar; där är det också säkrast.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, grave fields, family, stone groups, spatial statistics, point patterns, pre-registration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** Where runestones were raised has long been discussed: by grave fields, by roads and bridges, at the farm's boundaries. The question here is whether the stones form groups, what the stones in a group have in common and where the groups stand – measured on the whole material, with the density of the settled land held constant.
**Material.** Runestones that stand in place according to Rundata: {AU['n_stones']} in Uppland and {AS['n_stones']} in Södermanland for the pattern and the names, {REP['main']['n_stones']} in Östergötland, Västergötland and Småland for a replication of the pattern, and {TRA['n']} in the Swedish provinces for the grave fields, with grave fields from the Swedish National Heritage Board's register.
**Method.** Four pre-registered studies: a test of the point pattern against settled land of varying density (999 simulations), replicated in a pre-registered test on new stones, a comparison of near and distant pairs of stones (9,999 permutations), a logistic regression for grave fields in a group against a lone stone, and a permutation of style groups within the district. The two main tests have passed a fixed series of sensitivity analyses under a locked addendum plan.
**Results.** The stones lie closer together than chance would give at 100–1,000 metres in Uppland and Södermanland, and the same test gives the same result on the stones of Götaland ({pfmt(REP['main']['p'], True)}). Stones within 500 metres of each other name the same person in {100 * GN['share_near']:.1f} percent of the pairs against {100 * GN['share_far']:.1f} percent at 2–10 kilometres: {GN['ratio']:.1f} times as often. {pc(M1['share_grupp'])} percent of the stones in a group have a grave field within 500 metres against {pc(M1['share_ensam'])} percent of the lone ones; odds ratio {M1['or']:.2f}. A group has on average {G['mean_styles']:.2f} different style groups against {G['expected']:.2f} for as many stones from the same district. Roads, boundary markers and the place names of power do not set the groups apart from the lone stones.
**Conclusion.** Runestones often stand in groups that belong to a family: the same people, by the family's grave field, raised within one generation. The findings are carried to a large degree by Uppland.

## 1. Introduction

Gunnar Ekholm (1950) asked where the runestones were raised and was sceptical of the idea that lone stones mark grave fields that have been ploughed away. Torun Zachrisson (1998), in her study of Uppland and Gästrikland, set the runestones in relation to farm, boundary and grave field and proposed that stones at a farm's boundaries protected the farm. Lydia Klos (2009) argued that most runestones were originally raised at grave fields, a conclusion that Shane McLeod (2014) holds overstates the grave fields at the expense of other places, such as roads. Birgit Sawyer (2000) read the stones as expressions of family and inheritance, and groups such as Jarlabanke's stones at Täby and Vallentuna have long been seen as a lineage's monuments.

What is missing is a measure on the whole material: whether the stones actually form groups beyond chance when the density of settlement is held constant, whether the stones of a group belong together through people or through roads and bridges, and whether the groups stand in other places than the lone stones. The aim of the study is to measure that, in four steps, each pre-registered before it was run.

## 2. Pre-registration: hypotheses and plans

The study consists of four pre-registered steps and an addendum plan. Each plan was written down and time-stamped in the project's version control before the analysis was run; the checksums (SHA-256) are given below and the files under Data and code.

1. **The spacing** (28 October 2026, `{SHA['2026-10-28-avstand-mellan-stenar']}…`, addendum `{SHA['2026-10-28-avstand-mellan-stenar-tillagg']}…`; replication 31 October, `{SHA['replikering']}…`): do stones still in place stand closer together than chance would give at 100–1,000 metres, with the density of settlement constant? Tested in Uppland and Södermanland, and with the same method on the stones of Östergötland, Västergötland and Småland.
2. **The neighbouring stones** (29 October, `{SHA['2026-10-29-grannstenarna']}…`): do near pairs of stones (25–500 metres) more often share a personal name, a carver, a style group or a message than pairs at 2–10 kilometres? Six tests, Holm-corrected.
3. **The family's place** (29 October, `{SHA['2026-10-29-familjens-plats']}…`): do stones in a group (another stone 25–500 metres away) more often than lone stones (nearest stone over 1 kilometre away) stand by grave fields, burial mounds, roads, boundary markers, churches and certain place names? Fifteen tests, Holm-corrected.
4. **One generation** (29 October, `{SHA['2026-10-29-en-generation']}…`): do the groups have fewer different style groups than as many stones drawn from the same district?
5. **The addendum plan** (31 October, `{SHA['trappan']}…`): the same fixed series of sensitivity analyses that every other association in the project passes, applied to step 2 (the names) and step 3 (the grave fields). It was written after the four results were known but before the sensitivity analyses were run, and it adds no new outcomes.

Two things must be said about the order. Step 4 was formulated after an observation in step 3: there a one-sided test of *more* style groups than chance had been set, and the result went strongly the other way. The new plan tested the opposite with a stricter comparison (permutation within the district instead of within the province), but on the same stones. Step 4 is thus pre-registered, but not tested on independent data. In step 1 the method had to be corrected after the first run in Uppland and Södermanland (see 4.6). The corrected method was therefore tested unchanged, under a new locked plan, on the stones of Östergötland, Västergötland and Småland, which had been in no spacing analysis. It is that test that carries step 1.

## 3. Material

- **Source.** The Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University, in the version frozen for the analyses on 28–29 October 2026. Grave fields, burial mounds, roads and boundary markers from the Swedish National Heritage Board's register; place names from the project's place-name table.
- **The stones.** Only runestones that according to Rundata stand at their original place and have a known location; moved and lost stones are not included, since their place does not say where they were raised. Steps 1 and 2 concern Uppland and Södermanland, where the stones are most numerous ({AU['n_stones']} and {AS['n_stones']} stones, {AU['n_sites']} and {AS['n_sites']} sites when stones within 25 metres count as one site). The replication of step 1 concerns {REP['main']['n_stones']} stones in place in Östergötland ({RP['Ög']['n_stones']}), Västergötland ({RP['Vg']['n_stones']}) and Småland ({RP['Sm']['n_stones']}), the only provinces besides Uppland and Södermanland with enough stones still in place. Step 3 concerns all Swedish provinces: {FPL['n_grupp']} stones in a group and {FPL['n_ensam']} lone ones.
- **The personal names** are the sponsors' and the dead's names, read from the inscription with the project's name model. The 20 most common names in the whole material are not counted, so that a pair does not share a name merely because the name was common.
- **Dating** by the stone's ornamental style (Gräslund 2006). A style group covers 25–50 years.
- **The carver.** The carver Rundata gives, secure or uncertain.

## 4. Method

**4.1 The point pattern.** Ripley's L-function for the stones' sites, compared with an inhomogeneous Poisson pattern whose intensity is that of the settled land (kernel smoothing with a 10-kilometre bandwidth and a floor of 5 percent of the mean intensity), with a DCLF test over 100–1,000 metres against 999 simulations (Baddeley et al. 2015). Uppland and Södermanland separately, Holm-corrected. The replication uses exactly the same method, with the three provinces of Götaland as one pattern; it counts as successful if p is below 0.05, the pattern is clustered and the same direction holds in both halves.

**4.2 The neighbouring stones.** For each trait: the share of near pairs that share it, divided by the share of comparison pairs that share it. The p-value comes from 9,999 permutations of the stones' traits within the province, with the sites fixed.

**4.3 The grave fields.** Logistic regression: grave field within 500 metres ~ in a group + province + dating period + local density of stones, so that a dense district does not in itself count as a grave-field pattern.

**4.4 One generation.** For each group with at least two style-dated stones: the number of different style groups, compared with as many stones drawn 9,999 times from the same district (within 10 kilometres, except the group's own site).

**4.5 Sensitivity analyses** (the addendum plan). Grave fields: raw model; the plan's model; the carver as a random effect (Bates et al. 2015); the parish as a random effect; the stone's location as a spatial surface (Wood 2017); each half on its own; without one province at a time; without stones that the National Heritage Board's register Runor (2020) records as moved. Names: the main measure; each half on its own; each province on its own; without pairs with the same secure carver; without stones moved according to Runor. The halves are the project's fixed ones: whole parishes dealt alternately within each province. A step holds when the effect goes the same way and p is below 0.05; when a province is removed, or a province is tested alone, significance is required only where at least two thirds of the material remains.

**4.6 Deviations from the plans.** In step 1 the plan's 2-kilometre bandwidth gave stones without neighbours an intensity near zero, so that the test measured nothing; a calibration on random patterns revealed the error. The run is reported as invalid, and an addendum with a 10-kilometre bandwidth and a floor was locked before the new run. Since the method was corrected after a run on the same stones, it was then tested unchanged on new stones (the replication); there only one test run with 19 simulations was made to find code errors. In step 3 provinces with fewer than ten stones were merged. Otherwise no deviations.

## 5. Results

**5.1 The stones form groups.** The stones lie closer together than chance would give at 100–1,000 metres: Uppland {pfmt(AU['main']['p'], True)}, Södermanland {pfmt(AS['main']['p'], True)} (Holm-corrected 0.006 both), in both halves and with every bandwidth and floor in the robustness checks (p between 0.001 and 0.005). The median distance to the nearest stone is {NN_U / 1000:.1f} kilometres in Uppland and {NN_S / 1000:.1f} in Södermanland, but one stone in ten has a neighbour within about 200 metres. The replication on the stones of Östergötland, Västergötland and Småland gives the same result: clustered, {pfmt(REP['main']['p'], True)}, and in both halves (west {pfmt(RH['vast']['p'], True)}, east {pfmt(RH['ost']['p'], True)}). On their own, Västergötland ({pfmt(RP['Vg']['p'], True)}) and Småland ({pfmt(RP['Sm']['p'], True)}) are clustered; Östergötland goes the same way but is too small to be sure ({pfmt(RP['Ög']['p'], True)}). One stone per farm, evenly spread, finds no support.

**5.2 Neighbouring stones name the same people.** Of the near pairs where both stones carry names, {100 * GN['share_near']:.1f} percent share a personal name ({GN['near_pairs']} pairs), against {100 * GN['share_far']:.1f} percent of the comparison pairs ({GN['far_pairs']} pairs): {GN['ratio']:.1f} times as often, Holm-corrected {pfmt(GN['p_holm'], True)}. The same carver ({GC['ratio']:.1f} times) and the same style group ({GS['ratio']:.1f} times) are indications; bridges, journeys and Christian features do not make neighbours more alike. The sensitivity analyses all hold:

- Half A: ratio {BR['half_A']['ratio']:.1f} ({BR['half_A']['near_pairs']} near pairs), {pfmt(BR['half_A']['p'], True)}. Half B: {BR['half_B']['ratio']:.1f} ({BR['half_B']['near_pairs']}), {pfmt(BR['half_B']['p'], True)}.
- Uppland only: {BR['only_U']['ratio']:.1f} ({BR['only_U']['near_pairs']} near pairs, {pc(BR['only_U']['share_of_pairs'])} percent of the pairs), {pfmt(BR['only_U']['p'], True)}. Södermanland only: {BR['only_Sö']['ratio']:.1f} ({BR['only_Sö']['near_pairs']} near pairs), {pfmt(BR['only_Sö']['p'], True)} – the same direction, but too few pairs to be sure.
- Without pairs in which both stones have the same secure carver: {BR['no_same_carver']['ratio']:.1f}, {pfmt(BR['no_same_carver']['p'], True)}.
- Without stones that Runor records as moved: {BR['moved_runor']['ratio']:.1f}, {pfmt(BR['moved_runor']['p'], True)}.

**5.3 The groups stand by the grave fields.** {pc(M1['share_grupp'])} percent of the stones in a group have a grave field within 500 metres, against {pc(M1['share_ensam'])} percent of the lone ones. With province, dating period and local density constant the odds ratio is {M1['or']:.2f} ({M1['lo']:.2f}–{M1['hi']:.2f}), {pfmt(M1['p'], True)}, Holm-corrected {pfmt(T1['p_holm'], True)}. The sensitivity analyses all hold:

- Raw model: odds ratio {RA['raw']['or']:.2f}. Carver as a random effect ({RA['carver']['groups']} groups): {RA['carver']['or']:.2f}, {pfmt(RA['carver']['p'], True)}. Parish as a random effect ({RA['parish']['groups']} parishes): {RA['parish']['or']:.2f}, {pfmt(RA['parish']['p'], True)}. Location as a spatial surface: {RA['place']['or']:.2f}, {pfmt(RA['place']['p'], True)}.
- Half A: {RA['half_A']['or']:.2f}, {pfmt(RA['half_A']['p'], True)}. Half B: {RA['half_B']['or']:.2f}, {pfmt(RA['half_B']['p'], True)}.
- Without stones moved according to Runor ({RA['moved_runor']['n']} stones): {RA['moved_runor']['or']:.2f}, {pfmt(RA['moved_runor']['p'], True)}.
- Without one province at a time: the odds ratio lies between {min(LOP[p]['or'] for p in LOP if p != 'U'):.2f} and {max(LOP[p]['or'] for p in LOP if p != 'U'):.2f} without Östergötland, Småland, Södermanland and Västergötland. Without Uppland, when only {pc(LOP['U']['share_left'])} percent of the stones remain, it is {LOP['U']['or']:.2f} and not significant ({pfmt(LOP['U']['p'], True)}); the direction holds, but the difference is carried to a large degree by Uppland.

Burial mounds, roads and boundary markers do not set the groups apart from the lone stones: road within 500 metres {pc(OTHER['y3_vag']['main']['share_grupp'])} against {pc(OTHER['y3_vag']['main']['share_ensam'])} percent, boundary marker {pc(OTHER['y4_grans']['main']['share_grupp'])} against {pc(OTHER['y4_grans']['main']['share_ensam'])} percent, both without a demonstrated difference. Place names in Husby and -tuna lie, on the contrary, somewhat *less often* near the groups when density is held constant (odds ratio {OTHER['y9_centralort']['main']['or']:.2f}, Holm {OTHER['y9_centralort']['p_holm']:.2f}, an indication).

{chart(False)}

**5.4 A group was raised within one generation.** {G['groups']} groups with {G['stones']} style-dated stones ({G['provinces']['U']} in Uppland, {G['provinces']['Sö']} in Södermanland) have on average {G['mean_styles']:.2f} different style groups, against {G['expected']:.2f} for as many stones from the same district, {pfmt(G['p'], True)}; half A {pfmt(GH['A']['p'], True)}, half B {pfmt(GH['B']['p'], True)}. {pc(G['share_all_same'])} percent of the groups have all their stones in the same style group against {pc(G['share_all_same_expected'])} percent expected, and the span between a group's earliest and latest stone is on average {round(G['span_years'])} years against {round(G['span_expected'])}. Without groups in which one and the same carver made every stone ({NOC['groups']} groups remain) it is {NOC['mean_styles']:.2f} against {NOC['expected']:.2f}, {pfmt(NOC['p'], True)}: weaker, but present. Examples are Täby (U 135, 136, 137 and 140, all in style group Pr2) and Skokloster (U 685, 686 and 689, all Pr2); counter-examples with time depth exist, such as Vårfrukyrka (Fp and Pr4).

**In plain words.** The runestones stand closer together than chance gives. Two stones within 500 metres of each other name the same person about eight times as often as two stones 2–10 kilometres apart. Stones in such a group stand by a grave field in four cases of five, lone stones in just over half, and the stones of a group lie closer together in time than stones from the same district: on average twenty years between the earliest and the latest.

## 6. Discussion

**What the findings say.** Four measurements point the same way. Runestones gather in groups of a few hundred metres, the stones of a group name the same people, the groups stand by the grave fields, and a group was raised within a short time. The simplest reading is that the group is the family's place: a family that within one generation raised several stones by its grave field, for a father, sons and brothers. The roads and bridges do not explain the groups – neighbouring stones are not more often both bridge stones or journey stones, and the groups do not stand by roads more often than the lone stones.

**Against earlier research.** The findings support Klos (2009) in that the grave field was a main place for runestones, but sharpen it: it is above all the *groups* that stand by the grave fields, while somewhat more than half of the lone stones do so too. Zachrisson's (1998) boundary stones and the road stones emphasised by McLeod (2014) find no support in the comparison of group against lone stone – which does not rule out that single stones stood at boundaries and roads, but says that this is not what sets the family's gathered place apart from the lone stone. Ekholm's (1950) scepticism that lone stones mark ploughed-out grave fields agrees with the lone stones less often having a grave field nearby. That the groups were raised within one generation has, as far as we have been able to see, not been tested statistically before.

**Weaknesses, in order of weight.**

1. **Uppland carries much.** {G['provinces']['U']} of {G['groups']} groups in the generation test and {pc(BR['only_U']['share_of_pairs'])} percent of the near pairs in the name test lie in Uppland, and without Uppland the grave-field difference is not significant. That the stones cluster holds also in Götaland, but the names, the grave fields and the generation apply first of all to Uppland, where the stones still stand and are most numerous.
2. **Only stones in place.** About a third of the runestones stand where they were raised. If moved stones more often came from groups or from lone places, that affects the comparisons.
3. **The register is not complete.** A grave field that has been ploughed away is not in the register. That can make lone stones lone in the register although they once stood by a grave field – Ekholm's objection the other way round.
4. **Step 4 rests on the same stones as the observation behind it,** and the style groups are 25–50 years wide. ”One generation” means here: a shorter time than chance gives in the same district.
5. **The names are read by rules,** and a name can be borne by different people. Removing the most common names reduces but does not remove that risk.

**What would overturn the findings.** That the name likeness disappeared when the carver or the sponsor's formula was held constant, that the groups turned out to follow roads when a more complete road register was used, or that the generation pattern did not recur in another province with many stones in place.

## 7. Conclusion

Runestones often stand in groups – in Uppland and Södermanland, and according to a pre-registered replication also in Götaland – and the groups belong to a family: stones within 500 metres of each other name the same people eight times as often as stones further apart, the groups stand by grave fields more often than lone stones, and a group was usually raised within one generation. It applies first of all to Uppland. The next step is to see whether the same families recur at several places, and what sets the lone stones' places apart.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 31 October 2026. No release with a DOI exists yet; when one is made, the report will refer to it. All code, the analysis plans and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The analysis plans: `analysplaner/2026-10-28-avstand-mellan-stenar.md` with its addendum, `analysplaner/2026-10-29-grannstenarna.md`, `analysplaner/2026-10-29-familjens-plats.md`, `analysplaner/2026-10-29-en-generation.md` and `analysplaner/2026-10-31-familjens-plats-trappan.md`, each with its `.sha256` file.
- The spacing: `utdata/avstand/avstand.R`; the replication `utdata/avstand/replikering.R` with the plan `analysplaner/2026-10-31-avstand-replikering.md`. The neighbouring stones: `utdata/avstand/grannar.py` and `utdata/avstand/grannar_trappa.py`.
- The family's place and the generation: `utdata/familjens_plats/data.py`, `utdata/familjens_plats/analys.R`, `utdata/familjens_plats/generation.py` and `utdata/familjens_plats/trappa.R`; results and deviations in `resultat.md`, `generation_resultat.md` and `trappan_resultat.md` in the same folders.
- The material's version: corpus `{FP}`.
- The report is built by `utdata/blogg/build/build_rapport_familjens_plats.py`, which reads every figure from the result files and stops if anything disagrees.

## References

- Baddeley, A., Rubak, E. & Turner, R. 2015. *Spatial Point Patterns: Methodology and Applications with R*. Boca Raton: Chapman & Hall/CRC.
- Bates, D., Mächler, M., Bolker, B. & Walker, S. 2015. Fitting linear mixed-effects models using lme4. *Journal of Statistical Software* 67 (1), pp. 1–48.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, pp. 137 ff.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- McLeod, S. 2014. The rediscovery of U 170: runestones, churchyards, and burial grounds in Sweden. *Journal of the North Atlantic* 25. doi:10.3721/037.006.2503
- Swedish National Heritage Board (Riksantikvarieämbetet). The register of ancient monuments (Kulturmiljöregistret); *Runor* (register of runic inscriptions), 2020 extract.
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2nd ed. Boca Raton: Chapman & Hall/CRC.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholm University.

:::box The essentials
- Runestones often stand in groups, and the stones in a group name the same people – eight times as often as stones further apart.
- The groups stand by the grave fields and were usually raised within one generation: the family's monument by the family's burial place, not the road's or the boundary's.
- The pattern is clearest in Uppland, where the stones still stand; that is also where it is surest.
:::
"""

# the plain-words sentence rests on these numbers (mallen version 4)
assert "7,9 gånger så ofta" in body
assert "82 procent av stenarna i grupp" in body
assert "mot 55 procent av de ensamma" in body
assert "i medel 20 år mot 36 år" in body
assert "I klartext" in body and "In plain words" in body_en
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Geografi", "Kvinnor och barn"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_familjens_plats.json")
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
                 "topic": "Rapport|familjens_plats", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
