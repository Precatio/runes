"""Forskningsrapport (mallen utdata/rapporter/MALL.md, kanonisk IMRaD-/registrerad form): "Kvinnor reste runstenar oftare i Svealand än i Götaland –
31 mot 17 procent" (sv + en). Fyndet ur människomodulen (r/people.R, låst plan analysplaner/2026-10-28-manniskorna.md),
robusthetstrappan (src/robustness.py, METHODS 1v) och uppföljningen (analysplaner/2026-10-29-kvinnorna-i-svealand.md).
Alla siffror asserteras mot korpusjobbets filer (data/cache/r/corpus/<FP>/) och utdata/kvinnor_landsdel/kvinnor_landsdel.json.
    ../../../.venv/bin/python build_rapport_kvinnor.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels, r_findings, robustness  # noqa: E402
from src import r_bridge as rb  # noqa: E402

FP = "e83202e01a5e6d27"  # the corpus job the report rests on (computed 2026-10-29)
C = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
DONE = json.load(open(os.path.join(C, "done.json"), encoding="utf-8"))
assert DONE["fingerprint"] == FP and DONE["computed_at"].startswith("2026-10-29") and DONE["r_version"].startswith("R version 4.6.1")
PE = json.load(open(os.path.join(C, "people.json"), encoding="utf-8"))
ROB = json.load(open(os.path.join(C, "robustness.json"), encoding="utf-8"))
FU = json.load(open(os.path.join(ROOT, "utdata", "kvinnor_landsdel", "kvinnor_landsdel.json"), encoding="utf-8"))
PLAN_SHA = open(os.path.join(ROOT, "analysplaner", "2026-10-28-manniskorna.sha256")).read().split()[0]
FU_SHA = open(os.path.join(ROOT, "analysplaner", "2026-10-29-kvinnorna-i-svealand.sha256")).read().split()[0]
assert PLAN_SHA.startswith("ea26a388") and FU_SHA.startswith("6a03f6fd")

pc = lambda x: int(100 * x + 0.5)  # noqa: E731
d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731
d2e = lambda x: f"{x:.2f}"  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_n = lambda n: f"{n:,}"  # noqa: E731


def pfmt(p, en=False):
    if p < 0.001:
        return "p < 0.001" if en else "p < 0,001"
    s = f"{p:.3f}" if p < 0.01 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the people module's own test (r/people.R) -----------------------------------------------------------------------
assert PE["n_stones"] == 2320 and PE["plan"] == "analysplaner/2026-10-28-manniskorna.md" and PE["min_events"] == 15
T = next(t for t in PE["tests"] if t["key"] == "kvinna_landsdel")
M, HA, HB, RO = T["main"], T["halves"]["A"], T["halves"]["B"], T["robustness"]
assert T["status"] == "bekräftar" and T["replicated"] is True
assert (M["n"], M["k"]) == (1425, 391) and d2(M["or"]) == "0,46" and (d2(M["lo"]), d2(M["hi"])) == ("0,32", "0,66")
assert M["p"] < 1e-4 and 1e-4 < M["p_holm"] < 2e-4
assert (pc(M["shares_region"]["Svealand"]), pc(M["shares_region"]["Götaland"])) == (31, 17)
assert (HA["n"], HB["n"]) == (730, 695) and d2(HA["or"]) == "0,41" and d2(HB["or"]) == "0,51"
assert HA["p"] < 0.001 and 0.005 < HB["p"] < 0.01
assert (pc(HA["shares_region"]["Svealand"]), pc(HA["shares_region"]["Götaland"]), pc(HB["shares_region"]["Svealand"]), pc(HB["shares_region"]["Götaland"])) == (30, 15, 31, 19)
assert (RO["ord10"]["n"], d2(RO["ord10"]["or"])) == (951, "0,51") and RO["ord10"]["p"] < 0.005
assert (RO["kon_bestamt"]["n"], d2(RO["kon_bestamt"]["or"])) == (1390, "0,46") and RO["kon_bestamt"]["p"] < 1e-4
assert d2(RO["utan_ristare"]["or"]) == "0,46" and RO["utan_ristare"]["p"] < 1e-5
assert "or" not in RO["uppland"] and RO["son_far"] is None  # one region only: the comparison does not exist there
STATUS = {t["key"]: t["status"] for t in PE["tests"]}
assert STATUS == {"kvinna_landsdel": "bekräftar", "kvinna_tid": "indikation", "drengr_ung": "mönster att pröva",
                  "thegn_ung": "mönster att pröva", "dod_borta_ung": "bekräftar", "bro_kvinna": "ingen skillnad påvisad"}

# ---- the raw counts (follow-up study, same corpus rows) ------------------------------------------------------------------
assert FU["n_stones"] == 1425 and FU["plan"] == "analysplaner/2026-10-29-kvinnorna-i-svealand.md"
F0 = FU["tests"]["t0_huvud"]["raw"]
assert F0 == {"Svealand": {"k": 324, "n": 1013}, "Götaland": {"k": 61, "n": 370}}
RAW_SV, RAW_GO = 100 * 324 / 1013, 100 * 61 / 370
assert (round(RAW_SV), round(RAW_GO)) == (32, 16)
N_OTHER = 1425 - 1013 - 370
assert N_OTHER == 42

# ---- the robustness ladder (src/robustness.py, METHODS 1v) ------------------------------------------------------------
P = ROB["patterns"]["Människorna|people_kvinna_landsdel"]
RU = P["rungs"]
assert (P["n"], P["k"], P["direction"]) == (1383, 385, -1) and set(RU) == {"raw", "adjusted", "carver", "parish", "half_A", "half_B", "lopo"}
assert all(r["holds"] for r in RU.values())
assert d2(RU["raw"]["or"]) == "0,42" and d2(RU["adjusted"]["or"]) == "0,46" and d2(RU["carver"]["or"]) == "0,45" and d2(RU["parish"]["or"]) == "0,46"
assert (RU["carver"]["groups"], RU["parish"]["groups"]) == (483, 469) and not RU["carver"]["singular"] and not RU["parish"]["singular"]
assert (RU["half_A"]["n"], RU["half_B"]["n"]) == (701, 682) and d2(RU["half_A"]["or"]) == "0,43" and d2(RU["half_B"]["or"]) == "0,49"
assert RU["half_A"]["p"] < 0.001 and 0.004 < RU["half_B"]["p"] < 0.005
LO = RU["lopo"]
assert (LO["without"], LO["n"], LO["n_provinces"], LO["all_hold"], LO["flips"]) == ("U", 643, 6, True, []) and d2(LO["or"]) == "0,66" and 0.06 < LO["p"] < 0.07
EF = P["effect"]
assert (pc(EF["share_lo"]), pc(EF["share_hi"])) == (31, 17) and round(100 * EF["diff"]) == -14
DIFF_CI = [round(-100 * x) for x in EF["diff_ci"]]
assert DIFF_CI == [20, 9]
CK = P["check"]
assert CK["ok"] and CK["uniformity_p"] > 0.5 and CK["dispersion_p"] > 0.5 and CK["spatial_p"] > 0.5
CO = P["coding"]
assert (CO["n_sim"], CO["share_holds"], CO["ppv"], CO["npv"]) == (200, 1, [13, 0], [67, 0]) and d2(CO["or_median"]) == "0,47"
assert (d2(CO["or_range"][0]), d2(CO["or_range"][1])) == ("0,44", "0,55")
assert ROB["facit"]["people"]["kvinna"]["n"] == 80 and ROB["alpha"] == 0.05 and ROB["min_province"] == 30
# the common adjustment over every pattern the app shows (computed as the app computes it, today)
ANN = robustness.annotate(r_findings.corpus_patterns(rb.JOB.result(FP)), robustness.load(FP))
BY = {p["key"]: p for p in ANN}
ME = BY["people_kvinna_landsdel"]
SUMM = robustness.summary(ANN)
assert ME["confirmed"] is True and ME["q_global"] < 1e-4 and ME["ladder"]["passed"] == ME["ladder"]["tested"] == 7
N_SHOWN, N_ALL = SUMM["n_fdr"], SUMM["all_rungs"]
assert N_SHOWN >= 40 and N_ALL == 15

# ---- the follow-up (analysplaner/2026-10-29-kvinnorna-i-svealand.md) --------------------------------------------------
FT = FU["tests"]
assert FT["t1_anka"]["raw"] == {"Svealand": {"k": 96, "n": 1013}, "Götaland": {"k": 23, "n": 370}} and FT["t1_anka"]["utslag"] == "ingen skillnad påvisad"
assert FT["t2_utan_resa"]["utslag"] == "håller" and d2(FT["t2_utan_resa"]["main"]["or"]) == "0,40"
assert FT["t3_antal"]["utslag"] == "antydan" and d2(FT["t3_antal"]["main"]["or"]) == "0,53" and round(100 * FU["attenuation_B"]) == 20
assert FT["t4_ensam"]["raw"] == {"Svealand": {"k": 137, "n": 1013}, "Götaland": {"k": 44, "n": 370}} and FT["t4_ensam"]["utslag"] == "ingen skillnad påvisad"
assert FT["t5_son"]["raw"] == {"Svealand": {"k": 107, "n": 195}, "Götaland": {"k": 13, "n": 70}} and FT["t5_son"]["utslag"] == "antydan" and d2(FT["t5_son"]["main"]["or"]) == "0,23"
assert FT["t6_far"]["raw"] == {"Svealand": {"k": 66, "n": 415}, "Götaland": {"k": 9, "n": 117}} and FT["t6_far"]["utslag"] == "antydan"
assert FT["t8_kristen"]["utslag"] == "ingen skillnad påvisad" and d2(FT["t8_kristen"]["main"]["or"]) == "1,27"
SON_SV, SON_GO = pc(107 / 195), pc(13 / 70)
assert (SON_SV, SON_GO) == (55, 19)

TODAY = dt.date.today().isoformat()
ORc = f"{d2(M['or'])} (95 %-intervall {d2(M['lo'])}–{d2(M['hi'])})"
ORe = f"{d2e(M['or'])} (95 % interval {d2e(M['lo'])}–{d2e(M['hi'])})"

title = "Kvinnor reste runstenar oftare i Svealand än i Götaland – 31 mot 17 procent"
summary = ("Förregistrerad studie. På 31 procent av Svealands runstenar med känd resare står en kvinna bland resarna, mot "
           "17 procent i Götaland. Skillnaden håller med tid och ristare konstanta, i båda halvorna av materialet och i "
           "robusthetstrappans alla steg. Den beror inte på änkor eller ensamma kvinnor utan på att modern stod med på sonens sten.")
title_en = "Women raised runestones more often in Svealand than in Götaland – 31 against 17 percent"
summary_en = ("Pre-registered study. A woman stands among the raisers on 31 percent of Svealand's runestones with a known raiser, "
              "against 17 percent in Götaland. The difference holds with time and carver constant, in both halves of the "
              "material and at every rung of the robustness ladder. It is not widows or lone women: the mother stood on her son's stone.")
SLUG = "kvinnor-bland-resarna-svealand-gotaland"
CITE_EN = f"Kvant, V. ({TODAY[:4]}). {title_en}. Vitki, version 1. https://vitkirunor.se/en/artiklar/{SLUG}"


def chart(sv):
    rows = [":::chart En kvinna bland resarna, andel av stenarna med känd resare" if sv else
            ":::chart A woman among the raisers, share of the stones with a known raiser",
            "# " + ("Med tid och ristare konstanta" if sv else "With time and carver constant"),
            f"+Svealand | {pc(M['shares_region']['Svealand'])} | {'rått' if sv else 'raw'} {324} {'av' if sv else 'of'} {sp(1013) if sv else en_n(1013)}",
            f"Götaland | {pc(M['shares_region']['Götaland'])} | {'rått' if sv else 'raw'} {61} {'av' if sv else 'of'} 370",
            "# " + ("Halva A" if sv else "Half A"),
            f"+Svealand | {pc(HA['shares_region']['Svealand'])} | {HA['n']} {'stenar' if sv else 'stones'}",
            f"Götaland | {pc(HA['shares_region']['Götaland'])} |",
            "# " + ("Halva B" if sv else "Half B"),
            f"+Svealand | {pc(HB['shares_region']['Svealand'])} | {HB['n']} {'stenar' if sv else 'stones'}",
            f"Götaland | {pc(HB['shares_region']['Götaland'])} |",
            ("Källa: Rundata. Modellens andelar (marginaleffekter) med tid och ristare konstanta." if sv else "Source: Rundata. Model shares (marginal effects) with time and carver constant."),
            ":::"]
    return "\n".join(rows)


SV_PROV = "Uppland, Södermanland, Västmanland, Närke, Gästrikland, Dalarna och Värmland"
GO_PROV = "Östergötland, Västergötland, Småland, Öland, Bohuslän, Halland och Dalsland"
EN_SV_PROV = "Uppland, Södermanland, Västmanland, Närke, Gästrikland, Dalarna and Värmland"
EN_GO_PROV = "Östergötland, Västergötland, Småland, Öland, Bohuslän, Halland and Dalsland"
# the provinces as the code maps them (src/messages.REGION), so that the text cannot drift from the analysis
from src.messages import REGION  # noqa: E402
assert sorted(k for k, v in REGION.items() if v == "Svealand") == sorted(["U", "Sö", "Vs", "Nä", "Gs", "D", "Vr"])
assert sorted(k for k, v in REGION.items() if v == "Götaland") == sorted(["Ög", "Vg", "Sm", "Öl", "Bo", "Hr", "Ds"])

body = f"""*Viktor Kvant, oberoende forskare. Version 1, {TODAY}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, kvinnor, resare, Svealand, Götaland, logistisk regression, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Att kvinnor reste runstenar är känt, och att deras andel skiftar mellan landskapen har iakttagits förr. Frågan här är om skillnaden mellan Svealand och Götaland står kvar när stenarnas ålder och ristarnas egna vanor hålls konstanta, och om den tål en fast serie känslighetsanalyser.
**Material.** {sp(M['n'])} läsbara svenska runstenar från vikingatiden med minst en namngiven eller omnämnd resare, ur Samnordisk runtextdatabas (Rundata): {sp(1013)} i Svealand och {sp(370)} i Götaland. Resarnas kön är bestämt med regler som kontrollerats mot handkodning.
**Metod.** Förregistrerad logistisk regression med landsdel och dateringsperiod som förklarande variabler och ristaren som slumpeffekt; Holm-korrigering över studiens sex test; intern replikering i två på förhand bestämda halvor av materialet; åtta känslighetsanalyser; justering för alla {N_SHOWN} samband som projektet redovisar (Benjamini–Hochberg).
**Resultat.** En kvinna bland resarna på {pc(M['shares_region']['Svealand'])} procent av stenarna i Svealand mot {pc(M['shares_region']['Götaland'])} procent i Götaland; oddskvot Götaland mot Svealand {ORc}, {pfmt(M['p'])}, Holm-korrigerat {pfmt(M['p_holm'])}. Samma riktning och signifikant i båda halvorna, och alla känslighetsanalyser håller; justerat för alla samband q < 0,001. En uppföljande förregistrerad studie finner att skillnaden sitter i rollerna – modern står med på sonens sten på {SON_SV} mot {SON_GO} procent – och inte hos änkor, ensamma kvinnor eller i kristnandet.
**Slutsats.** Skillnaden är verklig och stor, men den gäller minnesseden, inte kvinnors ställning, och den bärs i hög grad av Uppland.

## 1. Inledning

Kvinnorna på runstenarna har varit ett eget forskningsfält sedan 1990-talet. Judith Jesch (1991) samlade vad inskrifterna säger om kvinnor, och Birgit Sawyer (2000) räknade dem som reste stenarna landskap för landskap och visade att kvinnornas andel skiftar mellan landskapen. Sawyer läste stenarna som arvshandlingar: den som reste stenen visade sig som arvinge, och där kvinnor kunde ärva syntes de oftare. Anne-Sofie Gräslund (1995) har diskuterat samma kvinnor i förhållande till kristnandet. Räkningarna i den litteraturen är råa andelar. De tar inte hänsyn till att stenarna i Svealand i genomsnitt är yngre än i Götaland, eller till att några få ristare står för många stenar i Uppland.

Syftet är att pröva om skillnaden mellan Svealand och Götaland håller när stenarnas ålder och ristarna hålls konstanta, med en modell som bestämdes innan den kördes, och att låta den gå igenom samma känslighetsanalyser som projektets alla andra samband. Studien säger inget nytt om varför kvinnor reste stenar. Den prövar om den regionala skillnaden är ett fynd att bygga vidare på.

## 2. Förregistrering: hypotes och plan

Hypotesen, modellen och tolkningsreglerna skrevs ned i en analysplan den 28 oktober 2026, innan någon modell hade körts. Planen gällde en större studie av vilka som reste runstenarna och efter vem, med sex test; detta är det första. Planen är tidsstämplad i projektets versionshantering och har kontrollsumman SHA-256 `{PLAN_SHA[:16]}…`, så att varje senare ändring skulle synas (se Data och kod).

Testet lyder i planen: utfallet är minst en kvinna bland resarna, bland stenar med minst en identifierad resare; modellen är utfall ~ landsdel + dateringsperiod + ristaren som slumpeffekt; måttet är oddskvoten Götaland mot Svealand. De sex testen korrigeras tillsammans med Holms metod. Tolkningsreglerna bestämdes i förväg: ett test *bekräftar* när Holm-p är under 0,05 och riktningen är densamma med p under 0,05 i var och en av materialets två halvor; ett *mönster att pröva* har Holm-p under 0,05 men håller inte i båda halvorna; en *indikation* har bara okorrigerat p under 0,05.

Innan planen låstes hade jag sett en siffra: {sp(391)} läsbara svenska stenar har en kvinna bland resarna. Ingen jämförelse mellan landsdelar hade gjorts. Det står i planen.

Analyserna i avsnitt 5.1–5.3 är de som planen föreskriver. Uppföljningen i 5.4 kommer ur en andra analysplan, skriven och låst den 29 oktober 2026 (SHA-256 `{FU_SHA[:16]}…`) efter att huvudresultatet var känt. Den är alltså förregistrerad men inte en del av det första testet, och den redovisas som uppföljning. Inga explorativa analyser ingår.

## 3. Material

- **Källa.** Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk vid Uppsala universitet: translitterering, normalisering, översättning, landskap, socken, ristare och stilgruppering för varje inskrift. Materialet frystes för analysen den 29 oktober 2026.
- **Stenarna.** Alla vikingatida runstenar i de svenska landskapen: {sp(PE['n_stones'])} stenar. Bara runstenar; andra föremål med runor ingår inte. Skåne och Blekinge, som var danska under vikingatiden, förs i Rundata till Danmark och ingår inte.
- **Urval.** Stenar vars text är så bevarad att resarna kan läsas, och där minst en resare kan identifieras: {sp(M['n'])} stenar. Av dem ligger {sp(1013)} i Svealand och {sp(370)} i Götaland. {N_OTHER} ligger på Gotland eller i Norrland; de ingår i modellen som egna nivåer men jämförs inte.
- **Landsdelarna** efter dagens landskap: Svealand är {SV_PROV}; Götaland är {GO_PROV}.
- **Utfallet** är att minst en kvinna står bland resarna. Resarnas kön läses ur Rundatas engelska översättning med regler i fyra steg: först relationen (mor, dotter, hustru; son, far, bror), sedan den ensamma resarens possessiv i formeln (*her son*, *his son*), sedan ett namnlexikon som byggts ur de två första stegen, och sist namnets ändelse. Reglerna kontrollerades mot handkodning på ett nytt urval om 40 stenar som reglerna aldrig sett: 39 av 40 rätt. I de handkodade kontrollurvalen tillsammans ({ROB['facit']['people']['kvinna']['n']} stenar som kunde jämföras) var regelns ja rätt {CO['ppv'][0]} gånger av {CO['ppv'][0]} och regelns nej rätt {CO['npv'][0]} gånger av {CO['npv'][0]}. Felen finns där texten har luckor, och de missar kvinnor oftare än de lägger till.
- **Dateringsperiod** efter stenens ornamentikstil (Gräslund 2006): före 1010, 1010–1040, 1040–1070, efter 1070, och odaterad som egen grupp.
- **Ristaren.** Den ristare Rundata anger. Stenar utan känd ristare grupperas per socken.

## 4. Metod

**4.1 Modellen.** Logistisk regression i R-paketet mgcv (R {DONE['r_version'].split()[2]}; Wood 2017): utfallet mot landsdel och dateringsperiod, med ristaren som slumpeffekt. Slumpeffekten ger varje ristare en egen nivå, så att en flitig ristares vanor inte räknas som en landsdels sed. Andelarna per landsdel är modellens marginaleffekter, det vill säga medelvärdet över stenarna som de är.

**4.2 Korrigering och replikering.** Holm-korrigering (Holm 1979) över studiens sex test. Intern replikering: materialet delades i två halvor socken för socken, med hela socknar växelvis inom varje landskap. Indelningen gjordes en gång, före studien och lika för alla projektets analyser, och testet ska hålla i var halva för sig. Därtill fem robusthetsprov som planen föreskriver: bara stenar med minst tio läsbara ord, bara stenar där alla resares kön är bestämt, modellen utan ristarens slumpeffekt, bara Uppland, och söner mot fäder (det sista gäller bara studiens test om de döda).

**4.3 Känslighetsanalyser.** Projektet lägger samma fasta serie känslighetsanalyser på varje samband det redovisar, oavsett vilken studie sambandet kommer ur: rå modell; modellen justerad för dateringsperiod; ristaren som slumpeffekt; socknen som slumpeffekt, för att se om skillnaden är några socknars egenhet; var halva för sig; och modellen omräknad utan ett landskap i taget (landskap med minst {ROB['min_province']} stenar). En analys med stenens läge som rumslig yta görs inte här, eftersom jämförelsen själv är geografisk. En analys håller när p är under {str(ROB['alpha']).replace('.', ',')} och riktningen är densamma som i den justerade modellen. När ett landskap tas bort krävs signifikans bara där minst två tredjedelar av stenarna är kvar; annars räcker riktningen.

Eftersom projektet prövar många samband justeras p-värdena dessutom tillsammans för alla {N_SHOWN} samband som redovisas (Benjamini & Hochberg 1995). Det justerade värdet kallas q nedan. Ett samband räknas som bekräftat när det håller i båda halvorna och q är under 0,05. Modellens antaganden prövas med simulerade residualer (DHARMa; Hartig 2022). Felen i könsbestämningen prövas genom att modellen räknas om {CO['n_sim']} gånger, där varje stens ”sanna” utfall dras ur kontrollurvalets träffandelar.

Känslighetsanalyserna räknas på de {sp(P['n'])} stenarna i Svealand och Götaland. Huvudmodellen har {sp(M['n'])}, eftersom Gotland och Norrland är med som egna nivåer där. Känslighetsanalyserna använder projektets gemensamma dateringsperioder, så siffrorna kan skilja sig något från huvudtestets.

**4.4 Avvikelser från planen.** Inga för huvudplanen. I uppföljningens plan kördes ett av testen (en ensam kvinna reser stenen) först med en variabel som saknades i datafilen, vilket gav noll stenar. Variabeln räknades sedan fram exakt som planen definierar den och testet kördes om. Inget annat ändrades.

## 5. Resultat

**5.1 Huvudtestet.** Rått står en kvinna bland resarna på {324} av {sp(1013)} stenar i Svealand ({round(RAW_SV)} procent) mot {61} av {370} i Götaland ({round(RAW_GO)} procent). Med tid och ristare konstanta är andelarna {pc(M['shares_region']['Svealand'])} mot {pc(M['shares_region']['Götaland'])} procent. Oddskvoten Götaland mot Svealand är {ORc}, {pfmt(M['p'])}, Holm-korrigerat {pfmt(M['p_holm'])}. I klartext: drar man en sten på måfå i vardera landsdelen är det nästan dubbelt så vanligt att Svealandsstenen har en kvinna bland resarna, och ett så stort utslag av ren slump är så sällsynt att det inte är värt att räkna med. Halva A: {sp(HA['n'])} stenar, oddskvot {d2(HA['or'])} ({d2(HA['lo'])}–{d2(HA['hi'])}), {pfmt(HA['p'])}. Halva B: {sp(HB['n'])} stenar, oddskvot {d2(HB['or'])} ({d2(HB['lo'])}–{d2(HB['hi'])}), {pfmt(HB['p'])}. Samma riktning och signifikant i båda halvorna: testet *bekräftar* enligt planens regel.

{chart(True)}

**5.2 Planens robusthetsprov.**

- Bara stenar med minst tio läsbara ord: {sp(RO['ord10']['n'])} stenar, oddskvot {d2(RO['ord10']['or'])}, {pfmt(RO['ord10']['p'])}.
- Bara stenar där alla resares kön är bestämt: {sp(RO['kon_bestamt']['n'])} stenar, oddskvot {d2(RO['kon_bestamt']['or'])}, {pfmt(RO['kon_bestamt']['p'])}.
- Utan ristarens slumpeffekt: oddskvot {d2(RO['utan_ristare']['or'])}, {pfmt(RO['utan_ristare']['p'])}.
- Bara Uppland: kan inte prövas, eftersom jämförelsen gäller landsdelar och Uppland ligger helt i Svealand.

**5.3 Känslighetsanalyserna** ({sp(P['n'])} stenar, {P['k']} med en kvinna bland resarna). Alla {ME['ladder']['tested']} håller:

- Rå modell: oddskvot {d2(RU['raw']['or'])} ({d2(RU['raw']['ci'][0])}–{d2(RU['raw']['ci'][1])}), {pfmt(RU['raw']['p'])}.
- Justerad för dateringsperiod: {d2(RU['adjusted']['or'])} ({d2(RU['adjusted']['ci'][0])}–{d2(RU['adjusted']['ci'][1])}), {pfmt(RU['adjusted']['p'])}.
- Ristaren som slumpeffekt ({RU['carver']['groups']} ristare och sockengrupper): {d2(RU['carver']['or'])} ({d2(RU['carver']['ci'][0])}–{d2(RU['carver']['ci'][1])}), {pfmt(RU['carver']['p'])}.
- Socknen som slumpeffekt ({RU['parish']['groups']} socknar): {d2(RU['parish']['or'])} ({d2(RU['parish']['ci'][0])}–{d2(RU['parish']['ci'][1])}), {pfmt(RU['parish']['p'])}. Skillnaden är alltså inte några socknars egenhet.
- Halva A ({RU['half_A']['n']} stenar): {d2(RU['half_A']['or'])}, {pfmt(RU['half_A']['p'])}. Halva B ({RU['half_B']['n']} stenar): {d2(RU['half_B']['or'])}, {pfmt(RU['half_B']['p'])}.
- Utan ett landskap i taget ({LO['n_provinces']} landskap prövade): riktningen håller utan vart och ett av dem, och inget landskap vänder den. Svagast utan Uppland, då {LO['n']} stenar är kvar: oddskvot {d2(LO['or'])} ({d2(LO['ci'][0])}–{d2(LO['ci'][1])}), {pfmt(LO['p'])}. Utan Uppland försvinner mer än hälften av Svealands stenar, och där krävs bara riktningen.
- Skillnaden i procentenheter i den justerade modellen: {pc(EF['share_lo'])} mot {pc(EF['share_hi'])} procent, {-round(100 * EF['diff'])} enheter (troligen mellan {DIFF_CI[1]} och {DIFF_CI[0]}).
- Modellens antaganden: residualernas fördelning p = {str(round(CK['uniformity_p'], 2)).replace('.', ',')}, överspridning p = {str(round(CK['dispersion_p'], 2)).replace('.', ',')}, kvarvarande rumsligt mönster p = {str(round(CK['spatial_p'], 2)).replace('.', ',')}. Inget avvikande.
- Felen i könsbestämningen: sambandet håller i {pc(CO['share_holds'])} procent av de {CO['n_sim']} omräkningarna; oddskvotens median {d2(CO['or_median'])}, spann {d2(CO['or_range'][0])}–{d2(CO['or_range'][1])}.
- Justerat för alla {N_SHOWN} samband som projektet redovisar: q < 0,001. Sambandet är ett av {N_ALL} som håller i alla känslighetsanalyser.

**5.4 Uppföljning (andra förregistrerade planen).** Fem förhandsbestämda förklaringar till vad skillnaden består i, prövade med samma modell och samma tolkningsregler:

- **Änkor efter färderna – stöds inte.** En kvinna reser stenen efter sin make: {96} av {sp(1013)} i Svealand mot {23} av {370} i Götaland, oddskvot {d2(FT['t1_anka']['main']['or'])}, ingen skillnad. Utan stenarna som nämner resor finns skillnaden kvar och blir något större (oddskvot {d2(FT['t2_utan_resa']['main']['or'])}, håller i båda halvorna).
- **Seden att räkna upp familjen – förklarar en femtedel.** Med antalet resare konstant: oddskvot {d2(FT['t3_antal']['main']['or'])}. {round(100 * FU['attenuation_B'])} procent av skillnaden på logoddsskalan försvinner, under planens gräns på hälften.
- **Egen ställning – stöds inte.** En ensam kvinna reser stenen: {137} av {sp(1013)} mot {44} av {370}, oddskvot {d2(FT['t4_ensam']['main']['or'])}, ingen skillnad.
- **Rollerna – här sitter skillnaden.** På stenar efter söner står modern med på {107} av {195} i Svealand ({SON_SV} procent) mot {13} av {70} i Götaland ({SON_GO} procent), oddskvot {d2(FT['t5_son']['main']['or'])}, Holm-korrigerat p = 0,015. I halvorna är p = 0,058 och 0,031, så enligt planens regel är det en indikation, inte ett bekräftat fynd. På stenar efter fäder står dotter eller hustru med på {66} av {415} mot {9} av {117}, oddskvot {d2(FT['t6_far']['main']['or'])}, också en indikation.
- **Kristnandet – inget samband.** Ett kristet kännetecken på stenen (kors eller bön) och en kvinna bland resarna: oddskvot {d2(FT['t8_kristen']['main']['or'])}, p = 0,16, och ingen skillnad mellan landsdelarna.

## 6. Diskussion

**Vad fyndet säger.** Skillnaden mellan Svealand och Götaland beror inte på att Svealands stenar är yngre eller på att några ristare där ristade många stenar. Den står kvar när båda hålls konstanta, i var halva för sig och i varje känslighetsanalys. Det är en skillnad i sed, inte i befolkning: en kvinna *nämns* oftare bland dem som reste stenen i Svealand. Det säger inte att kvinnor där hade mer makt eller egendom.

**Mot tidigare forskning.** Sawyers (2000) iakttagelse att kvinnornas andel skiftar mellan landskapen står sig alltså också när ålder och ristare hålls konstanta. Uppföljningen pekar åt samma håll som hennes tolkning. Kvinnorna i Svealand var inte oftare änkor och inte oftare ensamma resare; modern stod med på sonens sten tillsammans med fadern och syskonen. Det stämmer med en arvsregel där en mor kunde ärva efter sitt barn, bättre än med färderna eller kristnandet (jfr Gräslund 1995). Men rollfyndet är en indikation enligt planens regel, och tolkningen är en tolkning. Rapporten står på huvudfyndet.

**Svagheter, i ordning efter vikt.**

1. **Uppland bär mycket.** Utan Uppland är oddskvoten {d2(LO['or'])} och intervallet når över 1. Riktningen håller i alla landskap, men den säkra skillnaden är i hög grad en skillnad mellan Uppland och Götaland.
2. **Könet är bestämt med regler.** Reglerna har fel på ungefär en sten av tjugo, oftast där texten har luckor, och de missar kvinnor oftare än de lägger till. Vore luckorna vanligare i Götaland skulle det förstärka skillnaden på fel grund. Med bara stenar med minst tio läsbara ord är oddskvoten {d2(RO['ord10']['or'])}, så det förklarar inte fyndet.
3. **Dateringen vilar på ornamentikstil.** Odaterade stenar är en egen grupp. En annan datering kunde flytta siffrorna något men knappast riktningen, eftersom den råa och den justerade modellen nästan sammanfaller.
4. **Landsdel är en grov indelning.** Att skillnaden är störst mellan Uppland och Götaland syns redan. Vad som händer i gränslandskapen är inte prövat här.

**Vad som skulle fälla fyndet.** En handkodning av könet på ett stort urval som visar fler fel i den ena landsdelen än i den andra, eller en omräkning med en annan datering där den justerade modellen inte längre håller.

## 7. Slutsats

En kvinna står bland resarna på {pc(M['shares_region']['Svealand'])} procent av Svealands runstenar med känd resare mot {pc(M['shares_region']['Götaland'])} procent av Götalands, med ålder och ristare konstanta, och skillnaden tål varje känslighetsanalys. Den beror på hur familjen mindes sina döda – modern på sonens sten – och är därför ett fynd om minnesseden, inte ett mått på kvinnors ställning. Nästa fråga är varför seden skilde sig, och den kräver annat material än inskrifternas egna ord.

## Data och kod

Analysen är gjord i Vitki, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)). All kod, analysplanerna och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Analysplanerna: `analysplaner/2026-10-28-manniskorna.md` och `analysplaner/2026-10-29-kvinnorna-i-svealand.md`, med kontrollsummor i filerna `.sha256` bredvid.
- Könsbestämningen: `src/people.py`; handkodningen: `data/people_check.json`.
- Huvudmodellen: `r/people.R`. Känslighetsanalyserna: `r/robustness.R` och `src/robustness.py` (metodbeskrivning i `METHODS.md`, avsnitt 1u och 1v). Resultaten sparas under materialets version `{FP}`.
- Uppföljningen: `utdata/kvinnor_landsdel/analys.R`, resultat och avvikelser i `utdata/kvinnor_landsdel/resultat.md`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_kvinnor.py`, som läser varje siffra ur resultatfilerna och stannar om något inte stämmer.
- I Vitki visas sambandet under Statistik, Människorna, med känslighetsanalyserna steg för steg. En populär framställning av kvinnorna på stenarna finns i [Döttrarna som runstenarna glömde](/artiklar/dottrarna-som-runstenarna-glomde).

## Referenser

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), s. 289–300.
- Gräslund, A.-S. 1995. Runstenskvinnorna ännu en gång. *Tor* 27, s. 459–474.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R-paket.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Jesch, J. 1991. *Women in the Viking Age*. Woodbridge: Boydell.
- Kvant, V. 2026. *Vitki: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2 uppl. Boca Raton: Chapman & Hall/CRC.

:::box Det viktigaste i korthet
- I Svealand nämndes en kvinna bland dem som reste stenen nästan dubbelt så ofta som i Götaland, och skillnaden tål varje kontroll vi har.
- Den beror inte på änkor eller ensamma kvinnor: det var modern som stod med på sonens sten, tillsammans med fadern och syskonen.
- Skillnaden gäller minnesseden, inte kvinnors makt – och den bärs till stor del av Uppland.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Version 1, {TODAY}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, women, sponsors, Svealand, Götaland, logistic regression, pre-registration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** That women raised runestones is known, and that their share varies between provinces has been observed before. The question here is whether the difference between Svealand and Götaland remains when the age of the stones and the habits of individual carvers are held constant, and whether it withstands a fixed series of sensitivity analyses.
**Material.** {en_n(M['n'])} legible Swedish Viking-Age runestones with at least one named or mentioned sponsor, from the Scandinavian Runic-text Database (Rundata): {en_n(1013)} in Svealand and {en_n(370)} in Götaland. The sponsors' sex is determined by rules checked against hand coding.
**Method.** Pre-registered logistic regression with region and dating period as explanatory variables and the carver as a random effect; Holm correction over the study's six tests; internal replication in two pre-defined halves of the material; eight sensitivity analyses; adjustment for all {N_SHOWN} associations the project reports (Benjamini–Hochberg).
**Results.** A woman among the sponsors on {pc(M['shares_region']['Svealand'])} percent of the stones in Svealand against {pc(M['shares_region']['Götaland'])} percent in Götaland; odds ratio Götaland against Svealand {ORe}, {pfmt(M['p'], True)}, Holm-corrected {pfmt(M['p_holm'], True)}. Same direction and significant in both halves, and every sensitivity analysis holds; adjusted for all associations q < 0.001. A follow-up pre-registered study finds that the difference lies in the roles – the mother appears on her son's stone on {SON_SV} against {SON_GO} percent – and not in widows, lone women or Christianisation.
**Conclusion.** The difference is real and large, but it concerns commemorative custom, not women's standing, and it is carried to a large degree by Uppland.

## 1. Introduction

The women of the runestones have been a field of their own since the 1990s. Judith Jesch (1991) gathered what the inscriptions say about women, and Birgit Sawyer (2000) counted the sponsors province by province and showed that the share of women varies between provinces. Sawyer read the stones as documents of inheritance: whoever raised the stone presented herself or himself as the heir, and where women could inherit they appeared more often. Anne-Sofie Gräslund (1995) has discussed the same women in relation to Christianisation. The counts in that literature are raw shares. They take no account of the fact that the stones of Svealand are on average younger than those of Götaland, or that a few carvers account for many stones in Uppland.

The aim is to test whether the difference between Svealand and Götaland holds when the age of the stones and the carvers are held constant, with a model fixed before it was run, and to let it pass the same sensitivity analyses as every other association in the project. The study says nothing new about why women raised stones. It tests whether the regional difference is a finding to build on.

## 2. Pre-registration: hypothesis and plan

The hypothesis, the model and the rules of interpretation were written down in an analysis plan on 28 October 2026, before any model had been run. The plan concerned a larger study of who raised the runestones and for whom, with six tests; this is the first. The plan is time-stamped in the project's version control and has the SHA-256 checksum `{PLAN_SHA[:16]}…`, so that any later change would show (see Data and code).

The test reads in the plan: the outcome is at least one woman among the sponsors, among stones with at least one identified sponsor; the model is outcome ~ region + dating period + carver as a random effect; the measure is the odds ratio Götaland against Svealand. The six tests are corrected together by Holm's method. The rules of interpretation were fixed in advance: a test *confirms* when Holm p is below 0.05 and the direction is the same with p below 0.05 in each of the material's two halves; a *pattern to test* has Holm p below 0.05 but does not hold in both halves; an *indication* has only uncorrected p below 0.05.

Before the plan was locked I had seen one figure: {en_n(391)} legible Swedish stones have a woman among the sponsors. No comparison between regions had been made. The plan says so.

The analyses in sections 5.1–5.3 are those the plan prescribes. The follow-up in 5.4 comes from a second analysis plan, written and locked on 29 October 2026 (SHA-256 `{FU_SHA[:16]}…`) after the main result was known. It is thus pre-registered but not part of the first test, and it is reported as a follow-up. No exploratory analyses are included.

## 3. Material

- **Source.** The Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University: transliteration, normalisation, translation, province, parish, carver and style group for each inscription. The material was frozen for the analysis on 29 October 2026.
- **The stones.** All Viking-Age runestones in the Swedish provinces: {en_n(PE['n_stones'])} stones. Runestones only; other objects with runes are not included. Skåne and Blekinge, Danish in the Viking Age, are counted as Denmark in Rundata and are not included.
- **Selection.** Stones whose text is preserved well enough for the sponsors to be read, and where at least one sponsor can be identified: {en_n(M['n'])} stones. Of these, {en_n(1013)} lie in Svealand and {en_n(370)} in Götaland. {N_OTHER} lie on Gotland or in Norrland; they enter the model as their own levels but are not compared.
- **The regions** by today's provinces: Svealand is {EN_SV_PROV}; Götaland is {EN_GO_PROV}.
- **The outcome** is that at least one woman stands among the sponsors. The sponsors' sex is read from Rundata's English translation by rules in four steps: first the relation (mother, daughter, wife; son, father, brother), then a lone sponsor's possessive in the formula (*her son*, *his son*), then a name lexicon built from the first two steps, and last the name's ending. The rules were checked against hand coding on a new sample of 40 stones the rules had never seen: 39 of 40 right. In the hand-coded samples together ({ROB['facit']['people']['kvinna']['n']} stones that could be compared) the rule's yes was right {CO['ppv'][0]} times of {CO['ppv'][0]} and its no {CO['npv'][0]} times of {CO['npv'][0]}. The errors sit where the text has gaps, and they miss women more often than they add them.
- **Dating period** by the stone's ornamental style (Gräslund 2006): before 1010, 1010–1040, 1040–1070, after 1070, and undated as a group of its own.
- **The carver.** The carver Rundata gives. Stones without a known carver are grouped by parish.

## 4. Method

**4.1 The model.** Logistic regression with the R package mgcv (R {DONE['r_version'].split()[2]}; Wood 2017): the outcome against region and dating period, with the carver as a random effect. The random effect gives each carver a level of their own, so that a prolific carver's habits are not counted as a region's custom. The shares per region are the model's marginal effects, that is, the average over the stones as they are.

**4.2 Correction and replication.** Holm correction (Holm 1979) over the study's six tests. Internal replication: the material was divided into two halves parish by parish, with whole parishes dealt alternately within each province. The division was made once, before the study and the same for all the project's analyses, and the test must hold in each half on its own. In addition, five robustness checks prescribed by the plan: only stones with at least ten legible words, only stones where every sponsor's sex is determined, the model without the carver effect, Uppland only, and sons against fathers (the last applies only to the study's tests about the dead).

**4.3 Sensitivity analyses.** The project applies the same fixed series of sensitivity analyses to every association it reports, whatever study the association comes from: the raw model; the model adjusted for dating period; the carver as a random effect; the parish as a random effect, to see whether the difference is the peculiarity of a few parishes; each half on its own; and the model refitted without one province at a time (provinces with at least {ROB['min_province']} stones). An analysis with the stone's location as a spatial surface is not made here, since the comparison itself is geographic. An analysis holds when p is below {ROB['alpha']} and the direction is the same as in the adjusted model. When a province is removed, significance is required only where at least two thirds of the stones remain; otherwise the direction suffices.

Since the project tests many associations, the p-values are also adjusted together for all {N_SHOWN} associations reported (Benjamini & Hochberg 1995). The adjusted value is called q below. An association counts as confirmed when it holds in both halves and q is below 0.05. The model's assumptions are checked with simulated residuals (DHARMa; Hartig 2022). The errors in the sex determination are tested by refitting the model {CO['n_sim']} times, with each stone's ”true” outcome drawn from the hit rates in the hand-coded sample.

The sensitivity analyses are computed on the {en_n(P['n'])} stones in Svealand and Götaland. The main model has {en_n(M['n'])}, since Gotland and Norrland are included there as levels of their own. The sensitivity analyses use the project's common dating periods, so their figures can differ slightly from the main test's.

**4.4 Deviations from the plan.** None for the main plan. In the follow-up plan, one of the tests (a lone woman raises the stone) was first run with a variable that was missing from the data file, which gave zero stones. The variable was then computed exactly as the plan defines it and the test rerun. Nothing else was changed.

## 5. Results

**5.1 The main test.** Raw, a woman stands among the sponsors on {324} of {en_n(1013)} stones in Svealand ({round(RAW_SV)} percent) against {61} of {370} in Götaland ({round(RAW_GO)} percent). With time and carver constant the shares are {pc(M['shares_region']['Svealand'])} against {pc(M['shares_region']['Götaland'])} percent. The odds ratio Götaland against Svealand is {ORe}, {pfmt(M['p'], True)}, Holm-corrected {pfmt(M['p_holm'], True)}. In plain words: draw a stone at random in each region, and it is nearly twice as common that the Svealand stone has a woman among the sponsors; a swing that large from chance alone is too rare to reckon with. Half A: {en_n(HA['n'])} stones, odds ratio {d2e(HA['or'])} ({d2e(HA['lo'])}–{d2e(HA['hi'])}), {pfmt(HA['p'], True)}. Half B: {en_n(HB['n'])} stones, odds ratio {d2e(HB['or'])} ({d2e(HB['lo'])}–{d2e(HB['hi'])}), {pfmt(HB['p'], True)}. Same direction and significant in both halves: the test *confirms* by the plan's rule.

{chart(False)}

**5.2 The plan's robustness checks.**

- Only stones with at least ten legible words: {en_n(RO['ord10']['n'])} stones, odds ratio {d2e(RO['ord10']['or'])}, {pfmt(RO['ord10']['p'], True)}.
- Only stones where every sponsor's sex is determined: {en_n(RO['kon_bestamt']['n'])} stones, odds ratio {d2e(RO['kon_bestamt']['or'])}, {pfmt(RO['kon_bestamt']['p'], True)}.
- Without the carver effect: odds ratio {d2e(RO['utan_ristare']['or'])}, {pfmt(RO['utan_ristare']['p'], True)}.
- Uppland only: cannot be tested, since the comparison concerns regions and Uppland lies wholly in Svealand.

**5.3 The sensitivity analyses** ({en_n(P['n'])} stones, {P['k']} with a woman among the sponsors). All {ME['ladder']['tested']} hold:

- Raw model: odds ratio {d2e(RU['raw']['or'])} ({d2e(RU['raw']['ci'][0])}–{d2e(RU['raw']['ci'][1])}), {pfmt(RU['raw']['p'], True)}.
- Adjusted for dating period: {d2e(RU['adjusted']['or'])} ({d2e(RU['adjusted']['ci'][0])}–{d2e(RU['adjusted']['ci'][1])}), {pfmt(RU['adjusted']['p'], True)}.
- Carver as a random effect ({RU['carver']['groups']} carvers and parish groups): {d2e(RU['carver']['or'])} ({d2e(RU['carver']['ci'][0])}–{d2e(RU['carver']['ci'][1])}), {pfmt(RU['carver']['p'], True)}.
- Parish as a random effect ({RU['parish']['groups']} parishes): {d2e(RU['parish']['or'])} ({d2e(RU['parish']['ci'][0])}–{d2e(RU['parish']['ci'][1])}), {pfmt(RU['parish']['p'], True)}. The difference is not the peculiarity of a few parishes.
- Half A ({RU['half_A']['n']} stones): {d2e(RU['half_A']['or'])}, {pfmt(RU['half_A']['p'], True)}. Half B ({RU['half_B']['n']} stones): {d2e(RU['half_B']['or'])}, {pfmt(RU['half_B']['p'], True)}.
- Without one province at a time ({LO['n_provinces']} provinces tested): the direction holds without each of them, and no province turns it. Weakest without Uppland, when {LO['n']} stones remain: odds ratio {d2e(LO['or'])} ({d2e(LO['ci'][0])}–{d2e(LO['ci'][1])}), {pfmt(LO['p'], True)}. Without Uppland more than half of Svealand's stones are gone, and there only the direction is required.
- The difference in percentage points in the adjusted model: {pc(EF['share_lo'])} against {pc(EF['share_hi'])} percent, {-round(100 * EF['diff'])} points (probably between {DIFF_CI[1]} and {DIFF_CI[0]}).
- The model's assumptions: residual distribution p = {round(CK['uniformity_p'], 2)}, overdispersion p = {round(CK['dispersion_p'], 2)}, remaining spatial pattern p = {round(CK['spatial_p'], 2)}. Nothing amiss.
- Errors in the sex determination: the association holds in {pc(CO['share_holds'])} percent of the {CO['n_sim']} refits; median odds ratio {d2e(CO['or_median'])}, range {d2e(CO['or_range'][0])}–{d2e(CO['or_range'][1])}.
- Adjusted for all {N_SHOWN} associations the project reports: q < 0.001. The association is one of {N_ALL} that hold in every sensitivity analysis.

**5.4 Follow-up (second pre-registered plan).** Five pre-set explanations of what the difference consists of, tested with the same model and the same rules of interpretation:

- **Widows after the journeys – not supported.** A woman raises the stone for her husband: {96} of {en_n(1013)} in Svealand against {23} of {370} in Götaland, odds ratio {d2e(FT['t1_anka']['main']['or'])}, no difference. Without the stones that mention journeys the difference remains and grows slightly (odds ratio {d2e(FT['t2_utan_resa']['main']['or'])}, holds in both halves).
- **The custom of listing the family – explains a fifth.** With the number of sponsors constant: odds ratio {d2e(FT['t3_antal']['main']['or'])}. {round(100 * FU['attenuation_B'])} percent of the difference on the log-odds scale disappears, below the plan's limit of half.
- **A position of her own – not supported.** A lone woman raises the stone: {137} of {en_n(1013)} against {44} of {370}, odds ratio {d2e(FT['t4_ensam']['main']['or'])}, no difference.
- **The roles – this is where the difference lies.** On stones for sons the mother appears on {107} of {195} in Svealand ({SON_SV} percent) against {13} of {70} in Götaland ({SON_GO} percent), odds ratio {d2e(FT['t5_son']['main']['or'])}, Holm-corrected p = 0.015. In the halves p = 0.058 and 0.031, so by the plan's rule it is an indication, not a confirmed finding. On stones for fathers a daughter or wife appears on {66} of {415} against {9} of {117}, odds ratio {d2e(FT['t6_far']['main']['or'])}, also an indication.
- **Christianisation – no association.** A Christian feature on the stone (cross or prayer) and a woman among the sponsors: odds ratio {d2e(FT['t8_kristen']['main']['or'])}, p = 0.16, and no difference between the regions.

## 6. Discussion

**What the finding says.** The difference between Svealand and Götaland is not due to Svealand's stones being younger or to a few carvers there carving many stones. It remains when both are held constant, in each half and in every sensitivity analysis. It is a difference in custom, not in population: a woman is more often *named* among those who raised the stone in Svealand. It does not say that women there had more power or property.

**Against earlier research.** Sawyer's (2000) observation that the share of women varies between provinces thus stands also when age and carver are held constant. The follow-up points the same way as her interpretation. The women of Svealand were not more often widows and not more often lone sponsors; the mother appeared on her son's stone together with the father and the siblings. That fits a rule of inheritance under which a mother could inherit from her child better than it fits the journeys or Christianisation (cf. Gräslund 1995). But the role finding is an indication by the plan's rule, and the interpretation is an interpretation. The report rests on the main finding.

**Weaknesses, in order of weight.**

1. **Uppland carries much.** Without Uppland the odds ratio is {d2e(LO['or'])} and the interval reaches above 1. The direction holds in every province, but the certain difference is to a large degree a difference between Uppland and Götaland.
2. **Sex is determined by rules.** The rules err on about one stone in twenty, mostly where the text has gaps, and they miss women more often than they add them. If gaps were more common in Götaland that would strengthen the difference on false grounds. With only stones of at least ten legible words the odds ratio is {d2e(RO['ord10']['or'])}, so that does not explain the finding.
3. **The dating rests on ornamental style.** Undated stones are a group of their own. Another dating could move the figures slightly but hardly the direction, since the raw and the adjusted models nearly coincide.
4. **Region is a coarse division.** That the difference is largest between Uppland and Götaland is already visible. What happens in the border provinces is not tested here.

**What would overturn the finding.** A hand coding of sex on a large sample showing more errors in one region than in the other, or a recomputation with another dating in which the adjusted model no longer holds.

## 7. Conclusion

A woman stands among the sponsors on {pc(M['shares_region']['Svealand'])} percent of Svealand's runestones with a known sponsor against {pc(M['shares_region']['Götaland'])} percent of Götaland's, with age and carver constant, and the difference withstands every sensitivity analysis. It is due to how the family remembered its dead – the mother on her son's stone – and is therefore a finding about commemorative custom, not a measure of women's standing. The next question is why the custom differed, and it needs other material than the inscriptions' own words.

## Data and code

The analysis was made in Vitki, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)). All code, the analysis plans and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The analysis plans: `analysplaner/2026-10-28-manniskorna.md` and `analysplaner/2026-10-29-kvinnorna-i-svealand.md`, with checksums in the `.sha256` files beside them.
- The sex determination: `src/people.py`; the hand coding: `data/people_check.json`.
- The main model: `r/people.R`. The sensitivity analyses: `r/robustness.R` and `src/robustness.py` (method description in `METHODS.md`, sections 1u and 1v). The results are saved under the material's version `{FP}`.
- The follow-up: `utdata/kvinnor_landsdel/analys.R`, results and deviations in `utdata/kvinnor_landsdel/resultat.md`.
- The report is built by `utdata/blogg/build/build_rapport_kvinnor.py`, which reads every figure from the result files and stops if anything disagrees.
- In Vitki the association is shown under Statistics, The people, with the sensitivity analyses step by step. A popular account of the women on the stones is [The daughters the runestones forgot](/en/artiklar/dottrarna-som-runstenarna-glomde).

## References

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), pp. 289–300.
- Gräslund, A.-S. 1995. Runstenskvinnorna ännu en gång. *Tor* 27, pp. 459–474.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R package.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Jesch, J. 1991. *Women in the Viking Age*. Woodbridge: Boydell.
- Kvant, V. 2026. *Vitki: method description* (METHODS.md). https://github.com/Precatio/runes
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2nd ed. Boca Raton: Chapman & Hall/CRC.

:::box The essentials
- In Svealand a woman was named among those who raised the stone nearly twice as often as in Götaland, and the difference withstands every check we have.
- It is not widows or lone women: it was the mother who appeared on her son's stone, together with the father and the siblings.
- The difference concerns commemorative custom, not women's power – and it is carried to a large degree by Uppland.
:::
"""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
assert "Det viktigaste i korthet" in body

out = {"slug": SLUG, "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Rapport", "Kvinnor och barn", "Geografi"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport1_kvinnor.json")
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
                 "topic": "Rapport|kvinnor", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
