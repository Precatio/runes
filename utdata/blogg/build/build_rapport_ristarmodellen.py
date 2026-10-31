"""Forskningsrapport, metodrapport (låst mall utdata/rapporter/MALL.md, version 2; Metodrapport, delvis prövad):
"Statistiska ristarförslag ur runtexterna: 82 procent rätt bland de säkra förslagen i ett låst blindprov, mot 44 procent
för närmaste ristare" (sv + en). Blindprovet enligt utdata/forslag/analysplan_forslag.md (låst 2026-10-21), omkört
oförändrat på dagens korpus 2026-10-31 (blindprov_e83202.json, identiskt sten för sten); modellen r/attribution.R.
Alla siffror asserteras mot filerna.
    ../../../.venv/bin/python build_rapport_ristarmodellen.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

FP = "e83202e01a5e6d27"
C = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
DONE = json.load(open(os.path.join(C, "done.json"), encoding="utf-8"))
assert DONE["fingerprint"] == FP and DONE["r_version"].startswith("R version 4.6.1")
APP_VERSION = json.load(open(os.path.join(ROOT, "web", "package.json")))["version"]
assert APP_VERSION == "3.0.0"
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("d857ec3f")
REPORT_VERSION = 1
TODAY = "2026-10-31"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = "modellen byggdes 2026-10-05; blindprovets plan låstes 2026-10-21; blindprovet kördes 2026-10-21; provet kördes om på dagens material 2026-10-31"
TL_EN = "the model was built 2026-10-05; the plan of the blind test was locked 2026-10-21; the blind test was run 2026-10-21; the test was rerun on today's material 2026-10-31"
FD = os.path.join(ROOT, "utdata", "forslag")
PLAN_SHA = open(os.path.join(FD, "analysis_plan_forslag.sha256")).read().split()[0]
assert PLAN_SHA.startswith("5ed0b2f3")
BP = json.load(open(os.path.join(FD, "blindprov.json"), encoding="utf-8"))
BN = json.load(open(os.path.join(FD, "blindprov_e83202.json"), encoding="utf-8"))
AT = json.load(open(os.path.join(C, "attribution.json"), encoding="utf-8"))
AT_OLD = os.path.join(ROOT, "data", "cache", "r", "corpus", "5fdfd1e095bfb6fb", "attribution.json")
assert open(AT_OLD, "rb").read() == open(os.path.join(C, "attribution.json"), "rb").read()  # same model then and now

pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731
d1 = lambda x: f"{x:.1f}".replace(".", ",")  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731


def pexp(p, en=False):
    """A very small p as 3 · 10⁻²³."""
    m, e = f"{p:.1e}".split("e")
    m = m if en else m.replace(".", ",")
    sup = str(int(e)).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
    return f"{m} · 10{sup}"


def pfmt(p, en=False):
    if p < 0.001:
        return f"p = {pexp(p, en)}"
    s = f"{p:.3f}" if p < 0.1 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the locked blind test, then and now ------------------------------------------------------------------------------
assert BP["plan_sha256"].startswith("5ed0b2f3") and BP["corpus"] == "5fdfd1e095bfb6fb" and BN["corpus"] == FP
assert all(json.dumps(BP[k], sort_keys=True) == json.dumps(BN[k], sort_keys=True) for k in BP if k != "corpus")
assert (BP["n_attributed"], BP["n_in_universe"]) == (769, 636)
assert BP["status_counts"] == {"inget förslag": 272, "möjligt förslag": 195, "nytt förslag": 302}
NY, MO, SI, MN, SE = BP["nytt"], BP["mojligt"], BP["nytt_signed"], BP["nytt_model_named"], BP["nytt_someone_else"]
assert (NY["n"], NY["right"], NY["nearest_right"], NY["vitki_only"], NY["nearest_only"]) == (302, 248, 133, 132, 17)
assert (pc(NY["precision"]), pc(NY["ci"][0]), pc(NY["ci"][1]), pc(NY["nearest_precision"])) == (82, 77, 86, 44)
assert 3.0e-23 < NY["mcnemar_p"] < 3.1e-23
assert (SI["n"], SI["right"], SI["nearest_right"]) == (100, 72, 42) and 9e-6 < SI["mcnemar_p"] < 1e-5
assert (MO["n"], MO["right"], MO["nearest_right"], pc(MO["precision"]), pc(MO["nearest_precision"])) == (195, 108, 66, 55, 34)
assert (MN["n"], MN["right"], SE["n"], SE["right"]) == (254, 213, 48, 35) and BP["nytt_no_model"]["n"] == 0
assert BP["outside_universe"] == {"n": 133, "nytt": 23}
BS = {b["label"]: b for b in BP["by_strength"]}
assert [(BS[k]["n"], BS[k]["right"]) for k in ("0.5–0.6", "0.6–0.7", "0.7–1.01")] == [(72, 50), (65, 56), (165, 142)]
PU, PS = BP["by_province"]["U"], BP["by_province"]["Sö"]
assert (PU["n"], PU["right"], pc(PU["nearest_precision"]), PS["n"], PS["right"], PS["nearest_right"]) == (270, 227, 43, 28, 17, 13)
assert 0.38 < PS["mcnemar_p"] < 0.39 and PU["mcnemar_p"] < 1e-20
NYR = [r for r in BP["rows"] if r["status"] == "nytt förslag"]
assert len(NYR) == 302
PER = {}
for r in NYR:
    k = r["suggested"]
    a, b = PER.get(k, (0, 0))
    PER[k] = (a + (k in r["truth"]), b + 1)
assert PER["Öpir 1"] == (68, 104) and PER["Åsmund"] == (37, 39) and PER["Balle"] == (34, 37) and PER["Fot 2"] == (30, 35)
assert PER["Gunnar"] == (21, 22) and PER["Traen"] == (11, 15) and PER["Erik"] == (14, 14) and PER["Livsten"] == (10, 10)
BIG = sorted(((k, v) for k, v in PER.items() if v[1] > 3), key=lambda kv: -kv[1][1])
assert min(v[0] / v[1] for _, v in BIG) == 68 / 104
TRAEN_MISS = sorted((r["signum"] for r in NYR if r["suggested"] == "Traen" and "Traen" not in r["truth"]), key=lambda x: int(x.split()[1]))
assert TRAEN_MISS == ["Sö 46", "Sö 159", "Sö 160", "Sö 296"], TRAEN_MISS
EX = BP["external"]
assert (EX["n"], EX["in_universe"], EX["n_nytt"], EX["n_mojligt"], EX["agree_mojligt"]) == (19, 8, 0, 3, 1)

# ---- the model (r/attribution.R) --------------------------------------------------------------------------------------
assert (AT["n_train"], len(AT["carvers"]), AT["min_inscriptions"], AT["folds"], AT["repeats"], AT["trees"]) == (497, 18, 8, 5, 3, 500)
assert pc(AT["majority_baseline"]) == 19 and AT["near_km"] == 25
AB = {a["features"]: a for a in AT["ablation"]}
assert [d1(100 * AB[k]["accuracy"]) for k in ("Alla", "Språk och innehåll", "Geografi", "Stil", "Bergart")] == ["72,8", "61,4", "43,9", "33,0", "18,9"]
assert d1(100 * AB["Alla"]["top3"]) == "86,7"
GS = {a["features"]: a for a in AT["grouped_cv"]["Socken"]["ablation"]}
GH = {a["features"]: a for a in AT["grouped_cv"]["Härad"]["ablation"]}
assert (AT["grouped_cv"]["Socken"]["n_groups"], AT["grouped_cv"]["Härad"]["n_groups"]) == (164, 69)
assert [d1(100 * GS["Alla"]["accuracy"]), d1(100 * GH["Alla"]["accuracy"]), d1(100 * GH["Språk och innehåll"]["accuracy"]),
        d1(100 * GH["Geografi"]["accuracy"])] == ["68,8", "58,6", "50,1", "30,2"]
CAL = {b["bin"]: b for b in AT["calibration"]["bins"]}
assert [(pc(CAL[k]["mean_p"]), pc(CAL[k]["accuracy"]), CAL[k]["n"]) for k in ("(0.2,0.3]", "(0.4,0.5]", "(0.6,0.7]")] == \
    [(25, 51, 111), (45, 81, 90), (65, 98, 61)]
assert d1(100 * AT["calibration"]["ece"]) == "32,0"
OS = AT["open_set"]
assert (OS["threshold"], pc(OS["left_out"]["flagged"]), pc(OS["known"]["flagged"]), d1(100 * OS["known"]["accuracy_kept"])) == (0.35, 80, 41, "86,9")
GI = {g["group"]: g for g in AT["group_importance"]}
assert (pc(GI["Språk och innehåll"]["share"]), pc(GI["Geografi"]["share"]), pc(GI["Stil"]["share"])) == (72, 22, 6)
CONF = {(c["truth"], c["pred"]): c["Freq"] for c in AT["confused"]}
assert (CONF[("Åsmund", "Öpir 1")], CONF[("Gunnar", "Öpir 1")], CONF[("Visäte", "Öpir 1")], CONF[("Tidkume", "Balle")]) == (10, 8, 8, 10)
N_ATTR = sum(1 for r in BP["rows"] if not r["signed"])
assert N_ATTR == 769 - 246
NF = json.load(open(os.path.join(FD, "nya_forslag.json"), encoding="utf-8"))
assert NF["n_unattributed"] == 1550 and NF["counts"]["nytt förslag"] == 86 and NF["counts"]["möjligt förslag"] == 292

SLUG = "ristarforslag-blindprov"
title = "Statistiska ristarförslag ur runtexterna: 82 procent rätt bland de säkra förslagen i ett låst blindprov, mot 44 procent för närmaste ristare"
title_en = "Statistical carver suggestions from the runic texts: 82 percent right among the confident suggestions in a locked blind test, against 44 percent for the nearest carver"
summary = ("Metodrapport. En statistisk förslagsregel som bygger på det som står i runtextdatabasen föreslog rätt ristare för "
           "82 procent av de stenar där den gav ett säkert förslag, när ristaren var dold, mot 44 procent för en regel som "
           "föreslår ristaren bakom närmaste sten. Provet låstes i förväg. Regeln sattes dock på samma material, och de "
           "flesta attribueringar som provet jämförs med bygger på samma slags drag.")
summary_en = ("Methods report. A statistical suggestion rule built on what the runic-text database contains suggested the right "
              "carver for 82 percent of the stones where it gave a confident suggestion, with the carver hidden, against "
              "44 percent for a rule that suggests the carver of the nearest stone. The test was locked in advance. The rule "
              "was however set on the same material, and most attributions in the answer key rest on the same kind of "
              "features.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report (methods report), report version {REPORT_VERSION}; analysis in "
           f"Vitki {APP_VERSION}. https://vitkirunor.se/en/forskningsrapporter/{SLUG}")


def chart(sv):
    v, n = ("Förslagsregeln", "Närmaste ristare") if sv else ("Suggestion rule", "Nearest carver")
    of = "av" if sv else "of"
    f = d1 if sv else (lambda x: f"{x:.1f}")
    rows = [":::chart Rätt ristare i blindprovet, procent" if sv else ":::chart Right carver in the blind test, percent"]
    for lab_sv, lab_en, s in (("Säkra förslag", "Confident suggestions", NY), ("Säkra förslag, signerade stenar", "Confident suggestions, signed stones", SI),
                              ("Möjliga förslag", "Possible suggestions", MO)):
        rows += [f"# {lab_sv if sv else lab_en}",
                 f"+{v} | {f(100 * s['right'] / s['n'])} | {s['right']} {of} {s['n']}",
                 f"{n} | {f(100 * s['nearest_right'] / s['n'])} | {s['nearest_right']} {of} {s['n']}"]
    rows += ["Källa: Rundata; ristaren dold sten för sten." if sv else "Source: Rundata; the carver hidden stone by stone.", ":::"]
    return "\n".join(rows)


def carvers(sv):
    of = "av" if sv else "of"
    return "; ".join(f"{k}: {a} {of} {b}" for k, (a, b) in BIG)


body = f"""*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, runristare, attribuering, random forest, blindprov, förregistrering, ortografi. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Vad som inte är prövat.** Blindprovet låstes i förväg och varje stens ristare var dold, men förslagsregelns vikter och gränser sattes på samma material, och ett prov på stenar som har attribuerats först efter att regeln låstes är ännu för litet för att säga något.
**Bakgrund och syfte.** Runristare attribueras av runologer efter ornamentik, runformer, stavning och plats, och sedan 1990-talet också statistiskt efter huggspårens form i laserskanningar. Frågan här är hur ofta en statistisk regel som bara använder det som står i runtextdatabasen föreslår rätt ristare, när ristaren är dold.
**Material.** {BP['n_attributed']} svenska vikingatida runstenar med säker ristare i Samnordisk runtextdatabas (Rundata); 28 ristare kan föreslås.
**Metod.** Ett blindprov låst före körningen: för varje sten döljs ristaren, alla ristarprofiler räknas om utan den, och förslaget jämförs parvis med en regel som föreslår ristaren bakom närmaste sten med känd ristare (McNemars exakta test). Förslagen bygger på en random forest-modell över språk, innehåll, stil och plats, korsvaliderad, och på en jämförelse av stavningen.
**Resultat.** Regeln gav ett säkert förslag för {NY['n']} stenar och hade rätt på {NY['right']} ({pc(NY['precision'])} procent, 95 %-intervall {pc(NY['ci'][0])}–{pc(NY['ci'][1])}); närmaste ristare hade rätt på {NY['nearest_right']} ({pc(NY['nearest_precision'])} procent), {pfmt(NY['mcnemar_p'])}. På signerade stenar, där ristaren själv skrev sitt namn: {SI['right']} av {SI['n']} mot {SI['nearest_right']}. Fördelen är säker i Uppland men inte i Södermanland. Samma prov omkört på dagens version av materialet gav samma resultat sten för sten.
**Slutsats.** Förslagen är ungefär dubbelt så ofta rätt som en enkel gissning efter plats och har en känd felrisk, så de kan läggas fram som prövbara hypoteser. De visar framför allt hur väl regeln återger runologernas egna bedömningar, och de ersätter inte en runologisk granskning.

## 1. Inledning

Runologer attribuerar osignerade runstenar till ristare efter ornamentik, runformer, stavning, formler och plats. Claiborne Thompson (1975) visade hur stavningen skiljer de uppländska ristarna åt. Jan Axelson (1993) förtecknade de signerade och attribuerade inskrifterna i Mellansverige, och de flesta attribueringar i Rundata för Uppland, Södermanland, Västmanland och Gästrikland bygger på hans förteckning. Per Stille (1999) attribuerade stenarna i Fjädrundaland, och Magnus Källström (2007) har studerat ristarna och deras skriftmiljöer i hela Norden.

Statistisk attribuering är inte ny. Laila Kitzler (1998) visade i en metodstudie med en nutida ristare att huggspårens form i laserskanningar skiljer ristare åt med minst 70 procents träffsäkerhet, med klusteranalys och diskriminantanalys, och fann att Öpir troligen är minst två ristare. Hon har sedan använt metoden på vikingatida stenar i Uppland och Östergötland (Kitzler Åhfeldt 2002) och på Bornholm (Kitzler Åhfeldt 2020). Metoden kräver en skanning av varje sten.

Vi har inte funnit någon metod som föreslår ristare för alla runstenar ur det som står i runtextdatabasen och som har prövats i ett blindprov låst i förväg, mot en enkel jämförelseregel på samma stenar. Syftet här är att redovisa ett sådant prov.

## 2. Förregistrering: blindprovets plan

Planen skrevs och låstes den 21 oktober 2026, innan blindprovet räknades. Den är tidsstämplad i projektets versionshantering och har kontrollsumman SHA-256 `{PLAN_SHA[:16]}…` (se Data och kod). Frågan lyder i planen: har förslagen med status *nytt förslag* rätt klart oftare än en enkel regel som föreslår ristaren bakom den närmaste stenen med säker ristare, på samma stenar? *Ja* om McNemars test ger p under 0,05. Ett nej skulle redovisas lika tydligt. Planen förbjuder ändringar av vikter, gränser och regler efter att resultaten setts.

Före låsningen var två saker kända: hur många stenar utan ristare som fick varje status i projektets översikt, och vilka stenar som har en ristare i Riksantikvarieämbetets register Runor (2020) men inte i Rundata. Förslagsregeln och modellen var låsta i den version som provades. Men de hade utvecklats på samma material: modellens gräns för ”kanske någon annan” valdes med stenar av ristare som lämnades utanför modellen, och tre av regelns detaljer justerades den 11 oktober 2026 efter granskning av enskilda stenar (U 92, U 735 och U 1026). Svaret var alltså dolt för varje sten i provet, men inte när regeln utformades. Det är skälet till att rapporten är *delvis prövad*.

Avsnitt 5.1 och 5.4 är planens prov. Avsnitt 5.2 och 5.3 är tillägg utöver planen.

## 3. Material

- **Källa.** Samnordisk runtextdatabas (Rundata) 3.1, Institutionen för nordiska språk vid Uppsala universitet: translitterering, normalisering, landskap, socken, plats, ristare, stilgrupp och bergart för varje inskrift.
- **Stenarna i provet.** Alla {BP['n_attributed']} svenska vikingatida runstenar med en säker ristare i Rundata, signerad eller attribuerad utan frågetecken. {BP['n_in_universe']} har en ristare som kan föreslås. {BP['outside_universe']['n']} har en ristare som inte kan föreslås; de kan inte få rätt men ingår, så att det syns hur ofta en fel ristare föreslås.
- **Ristarna som kan föreslås.** 28: de {len(AT['carvers'])} ristare som modellen tränas på (minst {AT['min_inscriptions']} säkra stenar) och de ristare som har en stavningsprofil (minst fem säkra inskrifter).
- **Bara runstenar.** Andra föremål med runor ingår inte.

## 4. Metod

**4.1 Modellen.** En random forest (Breiman 2001) med {AT['trees']} träd, tränad på {AT['n_train']} stenar av {len(AT['carvers'])} ristare. Variablerna är läge och landskap, stilgrupp, kors och kortkvistrunor, elva språkdrag, fem formler, de hundra vanligaste runparen och nio innehållskategorier. Modellen utvärderas med femfaldig korsvalidering upprepad tre gånger, så att varje stens sannolikheter kommer från modeller som inte såg stenen, och dessutom med hela socknar och hela härader utelämnade. Är förstavalets sannolikhet under {str(OS['threshold']).replace('.', ',')} säger modellen *kanske någon annan*. Förslag ges bara för stenar inom {AT['near_km']} km från en träningssten.

**4.2 Stavningen.** Varje inskrift jämförs med ristarnas stavningsprofiler: delar av ord om två och tre runor, skiljetecken och bindrunor, utan egennamn, så att en signatur inte avslöjar svaret. Stenen själv räknas inte in i profilen.

**4.3 Förslagsregeln.** Förslagets styrka räknas ur modellens sannolikhet och stavningens förstaval och skrivs ned efter fyra kontroller: om stenen står inom ristarens område, om stilgruppen hör till ristarens vanliga, om språkdragen stämmer och om bergarten stämmer. *Nytt förslag*, här kallat säkert förslag, ges vid styrka minst 0,5 och *möjligt förslag* vid minst 0,3.

**4.4 Blindprovet.** För varje sten i provet görs ristaren okänd i en kopia av materialet, och ristarnas områden, stilgrupper, bergarter och språkprofiler räknas om utan stenen. Förslaget jämförs med regeln *närmaste ristare*: ristaren bakom den närmaste andra stenen med säker ristare, alla ristare om flera stenar står på samma avstånd. Måtten är andelen rätt med Wilsons 95 %-intervall och den parvisa jämförelsen med McNemars exakta test. En oberoende kontroll räknade om 60 slumpvis valda stenar på ett annat sätt och fick samma utfall för alla.

**4.5 Avvikelser och omkörning.** Tre avvikelser från planen. Ett kodfel kortade listan över modellens förslag till de första 400 stenarna; det rättades efter den första körningen. Redan den körningen gav {247} rätt av 300 säkra förslag, alltså 82 procent, mot 41 procent för närmaste ristare. Regeln närmaste ristare gjordes därefter generös vid lika avstånd, vilket gör jämförelsen svårare för förslagsregeln. Fördelningen per landskap och ristare i 5.2 är ett tillägg. Den 31 oktober 2026 kördes provet om oförändrat på dagens version av materialet; modellens sannolikheter är identiska och utfallet är detsamma för varje sten.

## 5. Resultat

**5.1 Blindprovet.** Av de {BP['n_attributed']} stenarna fick {NY['n']} ett säkert förslag, {MO['n']} ett möjligt och {BP['status_counts']['inget förslag']} inget.

- **Säkra förslag:** rätt på {NY['right']} av {NY['n']} ({pc(NY['precision'])} procent, {pc(NY['ci'][0])}–{pc(NY['ci'][1])}). Närmaste ristare: {NY['nearest_right']} ({pc(NY['nearest_precision'])} procent). På {NY['vitki_only']} stenar hade bara förslagsregeln rätt, på {NY['nearest_only']} bara den enkla regeln: {pfmt(NY['mcnemar_p'])}. Svaret på planens fråga är *ja*.
- **Signerade stenar**, där jämförelsen är ristarens eget namn: {SI['right']} av {SI['n']} ({pc(SI['precision'])} procent) mot {SI['nearest_right']}, {pfmt(SI['mcnemar_p'])}.
- **När modellen ger ett namn:** {MN['right']} av {MN['n']} ({pc(MN['precision'])} procent). När den säger *kanske någon annan*: {SE['right']} av {SE['n']} ({pc(SE['precision'])} procent).
- **Möjliga förslag:** {MO['right']} av {MO['n']} ({pc(MO['precision'])} procent) mot {MO['nearest_right']} ({pc(MO['nearest_precision'])} procent).
- **Efter styrka:** 0,5–0,6 rätt på {BS['0.5–0.6']['right']} av {BS['0.5–0.6']['n']}; 0,6–0,7 på {BS['0.6–0.7']['right']} av {BS['0.6–0.7']['n']}; minst 0,7 på {BS['0.7–1.01']['right']} av {BS['0.7–1.01']['n']}.
- **Ristare utanför de 28:** {BP['outside_universe']['nytt']} av de {BP['outside_universe']['n']} stenarna fick ändå ett säkert förslag, som med nödvändighet är fel; de ingår i siffrorna ovan.

{chart(True)}

**5.2 Per landskap och per ristare (utöver planen).** Uppland: {PU['right']} av {PU['n']} ({pc(PU['precision'])} procent) mot {pc(PU['nearest_precision'])} procent, {pfmt(PU['mcnemar_p'])}. Södermanland: {PS['right']} av {PS['n']} ({pc(PS['precision'])} procent) mot {PS['nearest_right']} ({pc(PS['nearest_precision'])} procent), {pfmt(PS['mcnemar_p'])}, alltså ingen säker skillnad. Per föreslagen ristare med fler än tre säkra förslag: {carvers(True)}. Öpir har lägst andel rätt. Alla fyra fel för Traen ({', '.join(TRAEN_MISS)}) gäller stenar som är signerade av andra ristare i Södermanland.

**5.3 Modellen för sig (korsvalideringen).** Modellen ensam sätter rätt ristare först på {d1(100 * AB['Alla']['accuracy'])} procent av träningsstenarna och bland de tre första på {d1(100 * AB['Alla']['top3'])} procent; att alltid gissa den vanligaste ristaren ger {pc(AT['majority_baseline'])} procent. Med hela socknar utelämnade: {d1(100 * GS['Alla']['accuracy'])} procent; med hela härader: {d1(100 * GH['Alla']['accuracy'])} procent.

- **Vad som bär modellen.** Bara språk och innehåll: {d1(100 * AB['Språk och innehåll']['accuracy'])} procent; bara geografi: {d1(100 * AB['Geografi']['accuracy'])}; bara stil: {d1(100 * AB['Stil']['accuracy'])}; bara bergart: {d1(100 * AB['Bergart']['accuracy'])}. Med hela härader utelämnade står sig språket bättre än geografin, {d1(100 * GH['Språk och innehåll']['accuracy'])} mot {d1(100 * GH['Geografi']['accuracy'])} procent. Språk och innehåll står för {pc(GI['Språk och innehåll']['share'])} procent av variablernas samlade vikt.
- **Kalibreringen.** Modellen är försiktig: när den anger omkring {pc(CAL['(0.2,0.3]']['mean_p'])} procent för sitt förstaval är det rätt i {pc(CAL['(0.2,0.3]']['accuracy'])} procent av fallen, vid {pc(CAL['(0.4,0.5]']['mean_p'])} procent i {pc(CAL['(0.4,0.5]']['accuracy'])} och vid {pc(CAL['(0.6,0.7]']['mean_p'])} procent i {pc(CAL['(0.6,0.7]']['accuracy'])}. Sannolikheterna underskattar alltså träffsäkerheten, och de ska läsas som en rangordning snarare än som odds.
- **Kanske någon annan.** Gränsen {str(OS['threshold']).replace('.', ',')} flaggar {pc(OS['left_out']['flagged'])} procent av stenarna när deras ristare har lämnats utanför modellen, men också {pc(OS['known']['flagged'])} procent av de kända ristarnas stenar; bland de stenar som inte flaggas har förstavalet rätt i {d1(100 * OS['known']['accuracy_kept'])} procent.
- **Förväxlingarna.** Vanligast är att Åsmund ({CONF[('Åsmund', 'Öpir 1')]} stenar), Gunnar ({CONF[('Gunnar', 'Öpir 1')]}) och Visäte ({CONF[('Visäte', 'Öpir 1')]}) tas för Öpir, och Tidkume för Balle ({CONF[('Tidkume', 'Balle')]}).

**5.4 Externt prov (planens sekundära).** {EX['n']} runstenar har en namngiven ristare i Runor (2020) men ingen i Rundata; {EX['in_universe']} av dem har en ristare som kan föreslås. Ingen fick ett säkert förslag, {EX['n_mojligt']} fick ett möjligt, och {EX['agree_mojligt']} av dem stämde. Det är för få stenar för att säga något, som planen väntade.

## 6. Diskussion

**Vad metoden klarar.** När förslagsregeln ger ett säkert förslag har det i provet varit rätt ungefär fyra gånger av fem, dubbelt så ofta som en gissning efter närmaste sten. Det gäller också signerade stenar, där jämförelsen inte är en bedömning utan ristarens eget namn. Därmed får de {NF['counts']['nytt förslag']} säkra och {NF['counts']['möjligt förslag']} möjliga förslag som regeln ger för de {sp(NF['n_unattributed'])} stenarna utan ristare en känd felrisk, och de kan läggas fram som hypoteser som går att pröva mot stenarna själva.

**Mot tidigare forskning.** Kitzler Åhfeldts metod och den här mäter olika saker. Hennes bygger på hur ristaren förde mejseln och kräver en skanning; den här bygger på vad ristaren skrev och var stenen står, och fungerar för alla stenar i databasen. Att Öpir är den ristare regeln träffar sämst och den som andra ristare oftast tas för passar med hennes iakttagelse att Öpir troligen är minst två ristare (Kitzler 1998). De två metoderna är oberoende av varandra, och där båda kan användas är de en prövning av varandra.

**Svagheter, i ordning efter vikt.**

1. **Jämförelsen är till stor del bedömningar av samma slag.** Av de {BP['n_attributed']} stenarna är {N_ATTR} attribuerade, inte signerade, och attribueringarna bygger på stil, stavning och plats, i Mellansverige till stor del via Axelson (1993). Provet mäter därför delvis hur väl regeln återger runologernas bedömningar. De signerade stenarna är det oberoende provet, och där är andelen rätt lägre: {pc(SI['precision'])} procent.
2. **Regeln sattes på samma material.** Vikter och gränser låstes före provet men valdes med materialet synligt (avsnitt 2). Det ger troligen en något för hög träffsäkerhet. Ett prov på stenar som attribueras först efter att regeln låstes skulle undanröja det; i dag finns bara {EX['in_universe']} sådana stenar.
3. **Bara 28 ristare.** En sten av en annan ristare kan bara få fel förslag. {BP['outside_universe']['nytt']} sådana stenar fick ett säkert förslag. Bland stenarna utan ristare finns säkert många av ristare som regeln inte känner.
4. **Södermanland.** Fördelen är inte säker där ({PS['right']} av {PS['n']} mot {PS['nearest_right']}), och nästan alla säkra förslag gäller Uppland.
5. **Öpir.** Den största ristaren i modellen drar till sig stenar av andra ristare, och andelen rätt är lägst för honom ({PER['Öpir 1'][0]} av {PER['Öpir 1'][1]}).

**Var metoden inte ska användas.** Utanför Uppland, för stenar mer än {AT['near_km']} km från en sten med känd ristare, för att avgöra mellan grannstenar i en och samma ristarmiljö och som bevis för en attribuering. Ett förslag är en hypotes.

**Vad som skulle fälla metoden.** Att andelen rätt sjönk till närmaste ristares nivå på stenar som attribueras efter att regeln låstes, eller att huggspårsanalyser på skannade stenar motsade de säkra förslagen.

## 7. Slutsats

En statistisk förslagsregel som bara använder det som står i runtextdatabasen föreslog i ett låst blindprov rätt ristare för {pc(NY['precision'])} procent av de stenar där den gav ett säkert förslag, mot {pc(NY['nearest_precision'])} procent för närmaste ristare, och för {pc(SI['precision'])} procent av de signerade stenarna. Den fungerar som ett sätt att sortera fram prövbara attribueringar i Uppland. Nästa steg är ett prov på stenar som attribuerats efter att regeln låstes, och en jämförelse med huggspårsanalyser på de skannade stenarna.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 31 oktober 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod, analysplanen och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Blindprovets plan: `utdata/forslag/analysplan_forslag.md`, med kontrollsumman i `analysis_plan_forslag.sha256`.
- Blindprovet: `utdata/forslag/blindprov.py` (resultat `blindprov.json`; omkörningen på dagens material `blindprov_e83202.json`), den oberoende kontrollen `kontroll.py`, avvikelserna i `resultat.md`.
- Modellen: `r/attribution.R` (resultat `attribution.json` under materialets version `{FP}`). Stavningen: `src/orthography.py`. Förslagsregeln: `src/stone_overview.py`. Metodbeskrivning: `METHODS.md`, avsnitt 1, 7 och 14c.
- Rapporten byggs av `utdata/blogg/build/build_rapport_ristarmodellen.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer. Mallen: `utdata/rapporter/MALL.md`, version 2.
- I Vitki visas förslagen i Stenöversikt och modellen under Statistik, Ristare. Populär framställning: [Fem runstenar söker sin ristare](/artiklar/fem-runstenar-soker-sin-ristare).

## Referenser

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Breiman, L. 2001. Random forests. *Machine Learning* 45, s. 5–32.
- Kitzler, L. 1998. Learning to know a rune carver and his cutting technique. A method study and some results. *Journal of Nordic Archaeological Science* 10, s. 89–103.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Archaeology B:9. Stockholm: Stockholms universitet.
- Kitzler Åhfeldt, L. 2020. Provenancing rune carvers on Bornholm through 3D-scanning and multivariate statistics of the carving technique. *European Journal of Archaeology* 23 (1), s. 82–104. https://doi.org/10.1017/eaa.2019.37
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholms universitet.
- Riksantikvarieämbetet. 2020. *Runor*. Runinskrifter i Sverige, databas. https://app.raa.se/open/runor
- Samnordisk runtextdatabas (Rundata) 3.1. Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Thompson, C. W. 1975. *Studies in Upplandic Runography*. Austin: University of Texas Press.

:::box Det viktigaste i korthet
- En regel som bara läser det som står i databasen kan föreslå vem som ristade en sten, och när den är säker har den rätt ungefär fyra gånger av fem.
- Den slår en gissning efter närmaste sten med god marginal, också på de stenar där ristaren själv skrev sitt namn.
- Förslagen är hypoteser med känd felrisk, bäst i Uppland, och de ersätter inte runologens granskning av stenen.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Methods report, partially tested. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, rune carvers, attribution, random forest, blind test, pre-registration, orthography. Competing interests: none. Funding: none.*

## Abstract

**What has not been tested.** The blind test was locked in advance and each stone's carver was hidden, but the weights and limits of the suggestion rule were set on the same material, and a test on stones attributed only after the rule was locked is still too small to say anything.
**Background and aim.** Rune carvers are attributed by runologists from ornament, rune forms, spelling and place, and since the 1990s also statistically from the shape of the grooves in laser scans. The question here is how often a statistical rule that uses only what the runic-text database contains suggests the right carver when the carver is hidden.
**Material.** {BP['n_attributed']} Swedish Viking-Age runestones with a secure carver in the Scandinavian Runic-text Database (Rundata); 28 carvers can be suggested.
**Method.** A blind test locked before it was run: for each stone the carver is hidden, all carver profiles are recomputed without it, and the suggestion is compared pairwise with a rule that suggests the carver of the nearest stone with a known carver (McNemar's exact test). The suggestions rest on a cross-validated random-forest model of language, content, style and place, and on a comparison of spelling.
**Results.** The rule gave a confident suggestion for {NY['n']} stones and was right on {NY['right']} ({pc(NY['precision'])} percent, 95 % interval {pc(NY['ci'][0])}–{pc(NY['ci'][1])}); the nearest carver was right on {NY['nearest_right']} ({pc(NY['nearest_precision'])} percent), {pfmt(NY['mcnemar_p'], True)}. On signed stones, where the carver wrote his own name: {SI['right']} of {SI['n']} against {SI['nearest_right']}. The advantage is clear in Uppland but not in Södermanland. The same test rerun on today's version of the material gave the same result stone by stone.
**Conclusion.** The suggestions are right about twice as often as a simple guess by place and carry a known error rate, so they can be put forward as testable hypotheses. They show above all how well the rule reproduces the runologists' own judgements, and they do not replace a runological examination.

## 1. Introduction

Runologists attribute unsigned runestones to carvers from ornament, rune forms, spelling, formulas and place. Claiborne Thompson (1975) showed how spelling tells the Upplandic carvers apart. Jan Axelson (1993) listed the signed and attributed inscriptions of central Sweden, and most attributions in Rundata for Uppland, Södermanland, Västmanland and Gästrikland rest on his list. Per Stille (1999) attributed the stones of Fjädrundaland, and Magnus Källström (2007) has studied the carvers and their writing milieus across Scandinavia.

Statistical attribution is not new. In a method study with a modern carver, Laila Kitzler (1998) showed that the shape of the grooves in laser scans tells carvers apart with at least 70 percent accuracy, using cluster and discriminant analysis, and found that Öpir is probably at least two carvers. She has since applied the method to Viking-Age stones in Uppland and Östergötland (Kitzler Åhfeldt 2002) and on Bornholm (Kitzler Åhfeldt 2020). The method requires a scan of every stone.

We have found no method that suggests carvers for all runestones from what the runic-text database contains and that has been tested in a blind test locked in advance, against a simple comparison rule on the same stones. The aim here is to report such a test.

## 2. Pre-registration: the plan of the blind test

The plan was written and locked on 21 October 2026, before the blind test was computed. It is time-stamped in the project's version control and has the SHA-256 checksum `{PLAN_SHA[:16]}…` (see Data and code). The question in the plan reads: are the suggestions with the status *new suggestion* right clearly more often than a simple rule that suggests the carver of the nearest stone with a secure carver, on the same stones? *Yes* if McNemar's test gives p below 0.05. A no would be reported just as clearly. The plan forbids changes to weights, limits and rules after the results have been seen.

Two things were known before the plan was locked: how many stones without a carver received each status in the project's overview, and which stones have a carver in the Swedish National Heritage Board's register Runor (2020) but not in Rundata. The suggestion rule and the model were locked in the version tested. But they had been developed on the same material: the model's limit for "perhaps someone else" was chosen with stones by carvers left out of the model, and three details of the rule were adjusted on 11 October 2026 after examination of individual stones (U 92, U 735 and U 1026). The answer was thus hidden for every stone in the test, but not when the rule was designed. That is why the report is *partially tested*.

Sections 5.1 and 5.4 are the plan's tests. Sections 5.2 and 5.3 are additions beyond the plan.

## 3. Material

- **Source.** The Scandinavian Runic-text Database (Rundata) 3.1, Department of Scandinavian Languages, Uppsala University: transliteration, normalisation, province, parish, place, carver, style group and rock type for each inscription.
- **The stones in the test.** All {BP['n_attributed']} Swedish Viking-Age runestones with a secure carver in Rundata, signed or attributed without a question mark. {BP['n_in_universe']} have a carver who can be suggested. {BP['outside_universe']['n']} have a carver who cannot be suggested; they cannot be right but are included, so that it shows how often a wrong carver is suggested.
- **The carvers who can be suggested.** 28: the {len(AT['carvers'])} carvers the model is trained on (at least {AT['min_inscriptions']} secure stones) and the carvers who have a spelling profile (at least five secure inscriptions).
- **Runestones only.** Other objects with runes are not included.

## 4. Method

**4.1 The model.** A random forest (Breiman 2001) with {AT['trees']} trees, trained on {AT['n_train']} stones by {len(AT['carvers'])} carvers. The variables are location and province, style group, cross and short-twig runes, eleven language traits, five formulas, the hundred most common rune pairs and nine content categories. The model is evaluated by fivefold cross-validation repeated three times, so that each stone's probabilities come from models that did not see it, and also with whole parishes and whole hundreds left out. If the first choice's probability is below {OS['threshold']}, the model says *perhaps someone else*. Suggestions are given only for stones within {AT['near_km']} km of a training stone.

**4.2 The spelling.** Each inscription is compared with the carvers' spelling profiles: parts of words of two and three runes, word dividers and bind-runes, without proper names, so that a signature does not give the answer away. The stone itself is not counted in the profile.

**4.3 The suggestion rule.** The strength of a suggestion is computed from the model's probability and the spelling's first choice and lowered by four checks: whether the stone stands within the carver's area, whether the style group is among the carver's usual ones, whether the language traits agree and whether the rock type agrees. A *new suggestion*, here called a confident suggestion, is given at a strength of at least 0.5 and a *possible suggestion* at at least 0.3.

**4.4 The blind test.** For each stone in the test the carver is made unknown in a copy of the material, and the carvers' areas, style groups, rock types and language profiles are recomputed without the stone. The suggestion is compared with the rule *nearest carver*: the carver of the nearest other stone with a secure carver, all carvers if several stones stand at the same distance. The measures are the share right with Wilson's 95 % interval and the pairwise comparison with McNemar's exact test. An independent check recomputed 60 randomly chosen stones in a different way and got the same outcome for all of them.

**4.5 Deviations and rerun.** Three deviations from the plan. A coding error cut the list of the model's suggestions to the first 400 stones; it was corrected after the first run. That first run already gave {247} right of 300 confident suggestions, 82 percent, against 41 percent for the nearest carver. The nearest-carver rule was then made generous at equal distances, which makes the comparison harder for the suggestion rule. The breakdown by province and carver in 5.2 is an addition. On 31 October 2026 the test was rerun unchanged on today's version of the material; the model's probabilities are identical and the outcome is the same for every stone.

## 5. Results

**5.1 The blind test.** Of the {BP['n_attributed']} stones, {NY['n']} received a confident suggestion, {MO['n']} a possible one and {BP['status_counts']['inget förslag']} none.

- **Confident suggestions:** right on {NY['right']} of {NY['n']} ({pc(NY['precision'])} percent, {pc(NY['ci'][0])}–{pc(NY['ci'][1])}). Nearest carver: {NY['nearest_right']} ({pc(NY['nearest_precision'])} percent). On {NY['vitki_only']} stones only the suggestion rule was right, on {NY['nearest_only']} only the simple rule: {pfmt(NY['mcnemar_p'], True)}. The answer to the plan's question is *yes*.
- **Signed stones**, where the answer key is the carver's own name: {SI['right']} of {SI['n']} ({pc(SI['precision'])} percent) against {SI['nearest_right']}, {pfmt(SI['mcnemar_p'], True)}.
- **When the model gives a name:** {MN['right']} of {MN['n']} ({pc(MN['precision'])} percent). When it says *perhaps someone else*: {SE['right']} of {SE['n']} ({pc(SE['precision'])} percent).
- **Possible suggestions:** {MO['right']} of {MO['n']} ({pc(MO['precision'])} percent) against {MO['nearest_right']} ({pc(MO['nearest_precision'])} percent).
- **By strength:** 0.5–0.6 right on {BS['0.5–0.6']['right']} of {BS['0.5–0.6']['n']}; 0.6–0.7 on {BS['0.6–0.7']['right']} of {BS['0.6–0.7']['n']}; at least 0.7 on {BS['0.7–1.01']['right']} of {BS['0.7–1.01']['n']}.
- **Carvers outside the 28:** {BP['outside_universe']['nytt']} of the {BP['outside_universe']['n']} stones still received a confident suggestion, which is necessarily wrong; they are included in the figures above.

{chart(False)}

**5.2 By province and by carver (beyond the plan).** Uppland: {PU['right']} of {PU['n']} ({pc(PU['precision'])} percent) against {pc(PU['nearest_precision'])} percent, {pfmt(PU['mcnemar_p'], True)}. Södermanland: {PS['right']} of {PS['n']} ({pc(PS['precision'])} percent) against {PS['nearest_right']} ({pc(PS['nearest_precision'])} percent), {pfmt(PS['mcnemar_p'], True)}, so no clear difference. By suggested carver with more than three confident suggestions: {carvers(False)}. Öpir has the lowest share right. All four errors for Traen ({', '.join(TRAEN_MISS)}) concern stones signed by other carvers in Södermanland.

**5.3 The model on its own (the cross-validation).** The model alone puts the right carver first on {100 * AB['Alla']['accuracy']:.1f} percent of the training stones and among the first three on {100 * AB['Alla']['top3']:.1f} percent; always guessing the most common carver gives {pc(AT['majority_baseline'])} percent. With whole parishes left out: {100 * GS['Alla']['accuracy']:.1f} percent; with whole hundreds: {100 * GH['Alla']['accuracy']:.1f} percent.

- **What carries the model.** Language and content only: {100 * AB['Språk och innehåll']['accuracy']:.1f} percent; geography only: {100 * AB['Geografi']['accuracy']:.1f}; style only: {100 * AB['Stil']['accuracy']:.1f}; rock type only: {100 * AB['Bergart']['accuracy']:.1f}. With whole hundreds left out, language holds up better than geography, {100 * GH['Språk och innehåll']['accuracy']:.1f} against {100 * GH['Geografi']['accuracy']:.1f} percent. Language and content account for {pc(GI['Språk och innehåll']['share'])} percent of the variables' combined importance.
- **The calibration.** The model is cautious: when it gives about {pc(CAL['(0.2,0.3]']['mean_p'])} percent to its first choice it is right in {pc(CAL['(0.2,0.3]']['accuracy'])} percent of cases, at {pc(CAL['(0.4,0.5]']['mean_p'])} percent in {pc(CAL['(0.4,0.5]']['accuracy'])} and at {pc(CAL['(0.6,0.7]']['mean_p'])} percent in {pc(CAL['(0.6,0.7]']['accuracy'])}. The probabilities thus underestimate the accuracy, and they should be read as a ranking rather than as odds.
- **Perhaps someone else.** The limit {OS['threshold']} flags {pc(OS['left_out']['flagged'])} percent of the stones when their carver has been left out of the model, but also {pc(OS['known']['flagged'])} percent of the known carvers' stones; among the stones not flagged, the first choice is right in {100 * OS['known']['accuracy_kept']:.1f} percent.
- **The confusions.** Most often Åsmund ({CONF[('Åsmund', 'Öpir 1')]} stones), Gunnar ({CONF[('Gunnar', 'Öpir 1')]}) and Visäte ({CONF[('Visäte', 'Öpir 1')]}) are taken for Öpir, and Tidkume for Balle ({CONF[('Tidkume', 'Balle')]}).

**5.4 External test (the plan's secondary).** {EX['n']} runestones have a named carver in Runor (2020) but none in Rundata; {EX['in_universe']} of them have a carver who can be suggested. None received a confident suggestion, {EX['n_mojligt']} received a possible one, and {EX['agree_mojligt']} of those was right. That is too few stones to say anything, as the plan expected.

## 6. Discussion

**What the method can do.** When the suggestion rule gives a confident suggestion, it has in the test been right about four times in five, twice as often as a guess by the nearest stone. That holds also for signed stones, where the answer key is not a judgement but the carver's own name. The {NF['counts']['nytt förslag']} confident and {NF['counts']['möjligt förslag']} possible suggestions the rule gives for the {NF['n_unattributed']:,} stones without a carver therefore carry a known error rate, and they can be put forward as hypotheses to be tested against the stones themselves.

**Against earlier research.** Kitzler Åhfeldt's method and this one measure different things. Hers rests on how the carver drove the chisel and requires a scan; this one rests on what the carver wrote and where the stone stands, and works for every stone in the database. That Öpir is the carver the rule hits least often, and the one other carvers are most often taken for, fits her observation that Öpir is probably at least two carvers (Kitzler 1998). The two methods are independent of each other, and where both can be used they test each other.

**Weaknesses, in order of weight.**

1. **The answer key is largely judgements of the same kind.** Of the {BP['n_attributed']} stones, {N_ATTR} are attributed, not signed, and the attributions rest on style, spelling and place, in central Sweden largely via Axelson (1993). The test therefore partly measures how well the rule reproduces the runologists' judgements. The signed stones are the independent test, and there the share right is lower: {pc(SI['precision'])} percent.
2. **The rule was set on the same material.** Weights and limits were locked before the test but chosen with the material in view (section 2). That probably gives a somewhat too high accuracy. A test on stones attributed only after the rule was locked would remove this; today there are only {EX['in_universe']} such stones.
3. **Only 28 carvers.** A stone by another carver can only receive a wrong suggestion. {BP['outside_universe']['nytt']} such stones received a confident suggestion. Among the stones without a carver there are surely many by carvers the rule does not know.
4. **Södermanland.** The advantage is not clear there ({PS['right']} of {PS['n']} against {PS['nearest_right']}), and almost all confident suggestions concern Uppland.
5. **Öpir.** The largest carver in the model attracts stones by other carvers, and the share right is lowest for him ({PER['Öpir 1'][0]} of {PER['Öpir 1'][1]}).

**Where the method should not be used.** Outside Uppland, for stones more than {AT['near_km']} km from a stone with a known carver, to decide between neighbouring stones in one and the same carving milieu, and as proof of an attribution. A suggestion is a hypothesis.

**What would overturn the method.** If the share right fell to the nearest-carver level on stones attributed after the rule was locked, or if groove analyses of scanned stones contradicted the confident suggestions.

## 7. Conclusion

A statistical suggestion rule that uses only what the runic-text database contains suggested, in a locked blind test, the right carver for {pc(NY['precision'])} percent of the stones where it gave a confident suggestion, against {pc(NY['nearest_precision'])} percent for the nearest carver, and for {pc(SI['precision'])} percent of the signed stones. It works as a way of sorting out testable attributions in Uppland. The next step is a test on stones attributed after the rule was locked, and a comparison with groove analyses of the scanned stones.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 31 October 2026. No release with a DOI exists yet; when one is made, the report will refer to it. All code, the analysis plan and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The plan of the blind test: `utdata/forslag/analysplan_forslag.md`, with its checksum in `analysis_plan_forslag.sha256`.
- The blind test: `utdata/forslag/blindprov.py` (results `blindprov.json`; the rerun on today's material `blindprov_e83202.json`), the independent check `kontroll.py`, the deviations in `resultat.md`.
- The model: `r/attribution.R` (results `attribution.json` under the material's version `{FP}`). The spelling: `src/orthography.py`. The suggestion rule: `src/stone_overview.py`. Method description: `METHODS.md`, sections 1, 7 and 14c.
- The report is built by `utdata/blogg/build/build_rapport_ristarmodellen.py`, which reads every number from the result files and stops if anything disagrees. The template: `utdata/rapporter/MALL.md`, version 2.
- In Vitki the suggestions are shown in the Stone overview and the model under Statistics, Carvers. Popular account: [Five runestones in search of their carver](/en/artiklar/fem-runstenar-soker-sin-ristare).

## References

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Breiman, L. 2001. Random forests. *Machine Learning* 45, pp. 5–32.
- Kitzler, L. 1998. Learning to know a rune carver and his cutting technique. A method study and some results. *Journal of Nordic Archaeological Science* 10, pp. 89–103.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Archaeology B:9. Stockholm: Stockholm University.
- Kitzler Åhfeldt, L. 2020. Provenancing rune carvers on Bornholm through 3D-scanning and multivariate statistics of the carving technique. *European Journal of Archaeology* 23 (1), pp. 82–104. https://doi.org/10.1017/eaa.2019.37
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholm University.
- Riksantikvarieämbetet. 2020. *Runor*. Runic inscriptions in Sweden, database. https://app.raa.se/open/runor
- Scandinavian Runic-text Database (Rundata) 3.1. Department of Scandinavian Languages, Uppsala University. Open Database License.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Thompson, C. W. 1975. *Studies in Upplandic Runography*. Austin: University of Texas Press.

:::box The essentials
- A rule that reads only what the database contains can suggest who carved a stone, and when it is confident it is right about four times in five.
- It beats a guess by the nearest stone by a wide margin, also on the stones where the carver wrote his own name.
- The suggestions are hypotheses with a known error rate, best in Uppland, and they do not replace the runologist's examination of the stone.
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
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion")
assert body_en.split("\n", 1)[0].startswith("*Viktor Kvant, independent researcher. Methods report, partially tested. Report version")
assert "## Sammanfattning\n\n**Vad som inte är prövat.**" in body  # mallen v2: status först för allt utom nivå 1

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Ristare", "Sannolikhetsmodellen"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_ristarmodellen.json")
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
                 "topic": "Rapport|ristarforslag", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
