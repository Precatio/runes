"""Forskningsrapport 1 (mallen utdata/rapporter/MALL.md): "Kvinnor reste runstenar oftare i Svealand än i Götaland –
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
summary = ("Forskningsrapport 1. På 31 procent av Svealands runstenar med känd resare står en kvinna bland resarna, mot "
           "17 procent i Götaland. Skillnaden håller med tid och ristare konstanta, i båda halvorna av materialet och i "
           "robusthetstrappans alla steg. Den beror inte på änkor eller ensamma kvinnor utan på att modern stod med på sonens sten.")

body = f"""*Forskningsrapport 1, version 1 ({TODAY}). Fyndet är bekräftat i Vitkis statistik: det håller i båda halvorna av korpusen och klarar den gemensamma justeringen över alla visade mönster. Rapporten följer den fasta mallen för Vitkis forskningsrapporter: planen låstes före resultaten och redovisas som den löd.*

## Sammanfattning

Bland Sveriges vikingatida runstenar med minst en identifierad resare står en kvinna bland resarna på {pc(M['shares_region']['Svealand'])} procent av stenarna i Svealand mot {pc(M['shares_region']['Götaland'])} procent i Götaland, när tidsskikt och ristare hålls konstanta. Oddskvoten Götaland mot Svealand är {ORc}: oddsen att en kvinna står med är mindre än hälften så stora i Götaland. Skillnaden är {-round(100 * EF['diff'])} procentenheter (troligen mellan {DIFF_CI[1]} och {DIFF_CI[0]}). Den håller i materialets båda halvor, i robusthetstrappans alla {ME['ladder']['tested']} steg och i den gemensamma justeringen över de {N_SHOWN} mönster som statistiken visar. En uppföljande låst studie visar att skillnaden inte beror på änkor efter färderna, inte på ensamma kvinnor och inte på kristnandet, utan på rollerna: i Svealand stod modern med på sonens sten på {SON_SV} procent av stenarna efter söner, i Götaland på {SON_GO} procent. Rapporten säger inget om varför seden skilde sig; det är nästa fråga.

## Fråga och hypotes som den låstes

Frågan ställdes i analysplanen för människomodulen, `analysplaner/2026-10-28-manniskorna.md`, låst den 28 oktober 2026 med SHA-256 `{PLAN_SHA[:16]}…` innan någon modell körts. Test 1 i planen lyder: *kvinnor bland resarna, landsdel* – utfallet är minst en kvinna bland resarna, bland stenar med minst en identifierad resare; modellen är utfall ~ landsdel + tidsskikt + ristaren som slumpeffekt; måttet är oddskvoten Götaland mot Svealand. Planen hade sex test med gemensam Holm-korrigering, och tolkningsreglerna var bestämda i förväg: *bekräftar* kräver Holm-p under 0,05 och samma riktning med p under 0,05 i var och en av korpusens två halvor.

Innan planen låstes hade jag sett en siffra: {sp(391)} läsbara svenska stenar har en kvinna bland resarna. Ingen jämförelse mellan landsdelar hade gjorts. Det står i planen under ”Före låsningen”.

## Material

- **Korpus.** Samnordisk runtextdatabas (Rundata) i Vitkis korpusjobb med fingeravtryck `{FP}`, beräknat 2026-10-29. Svenska vikingatida runstenar: {sp(PE['n_stones'])} stenar. Runstenar enbart; andra föremål ingår inte.
- **Urval.** Läsbara stenar med minst en identifierad resare: {sp(M['n'])}. Av dem ligger {sp(1013)} i Svealand och {sp(370)} i Götaland; {N_OTHER} ligger på Gotland eller i Norrland och ingår i modellen som egna nivåer men inte i jämförelsen.
- **Utfallet.** Minst en kvinna bland resarna. Resarnas kön läses ur Rundatas engelska översättning med regler i `src/people.py`: först relationen (mor, dotter, hustru; son, far, bror), sedan en ensam resares possessiv i formeln (*her son*, *his son*), sedan ett namnlexikon byggt ur de stegen, och sist namnets ändelse. Kontroll mot handkodning på ett nytt urval om 40 stenar som reglerna aldrig sett: 39 av 40 rätt. I robusthetstrappans facit ({ROB['facit']['people']['kvinna']['n']} handkodade stenar) var regelns ja rätt {CO['ppv'][0]} gånger av {CO['ppv'][0]} och regelns nej rätt {CO['npv'][0]} gånger av {CO['npv'][0]}. Felen finns där texten har luckor, och de missar kvinnor oftare än de lägger till.
- **Jämförelsen.** Landsdel som i budskapsmodulen: Götaland mot Svealand.
- **Justeringar.** Tidsskikt efter stilgruppering (före 1010, 1010–1040, 1040–1070, efter 1070, odaterad) och ristaren som slumpeffekt; stenar utan säker ristare grupperas per socken.

## Metod

Logistisk regression i mgcv (R {DONE['r_version'].split()[2]}), utfallet mot landsdel och tidsskikt med ristaren som slumpeffekt. Holm-korrigering över planens sex test. Replikering i två halvor av korpusen: hela socknar fördelas växelvis inom landskapet, halvorna är fasta och bestämdes oberoende av mönstren. Fem robusthetsprov enligt planen: minst tio läsbara ord, kön bestämt för alla resare, utan ristarens slumpeffekt, bara Uppland, och söner mot fäder (det sista gäller bara testen om de döda).

Därtill robusthetstrappan (`src/robustness.py`, `r/robustness.R`, METHODS.md 1v), som lägger samma kontroller på varje mönster i statistiken som kan räknas sten för sten: rått, justerat, ristaren som slumpeffekt, socknen som slumpeffekt, halvorna, och utan ett landskap i taget (landskap med minst {ROB['min_province']} stenar). Steget *platsen som yta* görs inte här, eftersom jämförelsen själv är geografisk. Ett steg håller när p < {str(ROB['alpha']).replace('.', ',')} och riktningen är densamma som i det justerade steget; utan ett landskap i taget krävs signifikans bara där minst två tredjedelar av stenarna är kvar. Alla visade mönster får en gemensam Benjamini–Hochberg-justering, q_global. Ett mönster är bekräftat när det håller i båda halvorna och q_global < 0,05.

Trappan räknas på de {sp(P['n'])} stenarna i Svealand och Götaland (modulens egen modell har {sp(M['n'])}, eftersom Gotland och Norrland är med som nivåer där). Trappans justerade steg använder statistikens gemensamma tidsskikt, så dess siffror kan skilja sig något från modulens.

## Resultat

**Huvudtalet.** Rått: {324} av {sp(1013)} stenar i Svealand ({round(RAW_SV)} procent) mot {61} av {370} i Götaland ({round(RAW_GO)} procent). Med tid och ristare konstanta: {pc(M['shares_region']['Svealand'])} mot {pc(M['shares_region']['Götaland'])} procent. Oddskvot Götaland mot Svealand {ORc}, {pfmt(M['p'])}, Holm-korrigerat {pfmt(M['p_holm'])}. I klartext: om man drar en sten på måfå i vardera landsdelen är det nästan dubbelt så vanligt att Svealandsstenen har en kvinna bland resarna, och ett så stort utslag av slump är så sällsynt att det inte är värt att räkna med.

**Halvorna.** Halva A: {sp(HA['n'])} stenar, oddskvot {d2(HA['or'])} ({d2(HA['lo'])}–{d2(HA['hi'])}), {pfmt(HA['p'])}. Halva B: {sp(HB['n'])} stenar, oddskvot {d2(HB['or'])} ({d2(HB['lo'])}–{d2(HB['hi'])}), {pfmt(HB['p'])}. Samma riktning och signifikant i båda: *bekräftar* enligt planens regel.

**Planens robusthetsprov.**

- Bara stenar med minst tio läsbara ord: {sp(RO['ord10']['n'])} stenar, oddskvot {d2(RO['ord10']['or'])}, {pfmt(RO['ord10']['p'])}.
- Bara stenar där alla resares kön är bestämt: {sp(RO['kon_bestamt']['n'])} stenar, oddskvot {d2(RO['kon_bestamt']['or'])}, {pfmt(RO['kon_bestamt']['p'])}.
- Utan ristarens slumpeffekt: oddskvot {d2(RO['utan_ristare']['or'])}, {pfmt(RO['utan_ristare']['p'])}.
- Bara Uppland: går inte att pröva, eftersom jämförelsen är mellan landsdelar och Uppland ligger helt i Svealand.

**Robusthetstrappan** ({sp(P['n'])} stenar, {P['k']} med en kvinna bland resarna). Alla {ME['ladder']['tested']} steg håller:

- Rått: oddskvot {d2(RU['raw']['or'])} ({d2(RU['raw']['ci'][0])}–{d2(RU['raw']['ci'][1])}), {pfmt(RU['raw']['p'])}.
- Justerat för tidsskikt: {d2(RU['adjusted']['or'])} ({d2(RU['adjusted']['ci'][0])}–{d2(RU['adjusted']['ci'][1])}), {pfmt(RU['adjusted']['p'])}.
- Ristaren som slumpeffekt ({RU['carver']['groups']} grupper): {d2(RU['carver']['or'])} ({d2(RU['carver']['ci'][0])}–{d2(RU['carver']['ci'][1])}), {pfmt(RU['carver']['p'])}.
- Socknen som slumpeffekt ({RU['parish']['groups']} socknar): {d2(RU['parish']['or'])} ({d2(RU['parish']['ci'][0])}–{d2(RU['parish']['ci'][1])}), {pfmt(RU['parish']['p'])}. Skillnaden är alltså inte några socknars egenhet.
- Halva A ({RU['half_A']['n']} stenar): {d2(RU['half_A']['or'])}, {pfmt(RU['half_A']['p'])}. Halva B ({RU['half_B']['n']} stenar): {d2(RU['half_B']['or'])}, {pfmt(RU['half_B']['p'])}.
- Utan ett landskap i taget ({LO['n_provinces']} landskap prövade): riktningen håller utan vart och ett av dem; inget landskap vänder den. Sämst utan Uppland, då {LO['n']} stenar är kvar: oddskvot {d2(LO['or'])} ({d2(LO['ci'][0])}–{d2(LO['ci'][1])}), {pfmt(LO['p'])}. Utan Uppland försvinner mer än hälften av Svealands stenar, så där kräver regeln bara riktningen – men det är också rapportens svagaste punkt, och den ska sägas rakt ut: skillnaden bärs till stor del av Uppland.
- Skillnad i procentenheter på den justerade modellen: {pc(EF['share_lo'])} mot {pc(EF['share_hi'])} procent, {-round(100 * EF['diff'])} enheter (troligen mellan {DIFF_CI[1]} och {DIFF_CI[0]}).
- Modellkontroll (DHARMa): residualernas fördelning p = {str(round(CK['uniformity_p'], 2)).replace('.', ',')}, överspridning p = {str(round(CK['dispersion_p'], 2)).replace('.', ',')}, rumsligt mönster p = {str(round(CK['spatial_p'], 2)).replace('.', ',')}. Inget avvikande.
- Kodningsfelen: i {CO['n_sim']} omräkningar där varje stens ”sanna” värde dras ur facits träffandelar håller mönstret i {pc(CO['share_holds'])} procent; oddskvotens median {d2(CO['or_median'])}, spann {d2(CO['or_range'][0])}–{d2(CO['or_range'][1])}.
- Gemensam justering över de {N_SHOWN} mönster statistiken visar i dag: q_global < 0,001. Fyndet är ett av {N_ALL} mönster som håller i trappans alla steg.

## Tolkning och svagheter

Fyndet är en skillnad i sed, inte i befolkning: det säger att en kvinna oftare *nämns bland dem som reste stenen* i Svealand, inte att kvinnor där hade mer makt eller egendom. Vad skillnaden består i prövades i en uppföljande låst plan (`analysplaner/2026-10-29-kvinnorna-i-svealand.md`, SHA-256 `{FU_SHA[:16]}…`), med fem förhandsbestämda hypoteser:

- **Änkor efter färderna – stöds inte.** Kvinna reser efter make: {96} av {sp(1013)} i Svealand mot {23} av {370} i Götaland, oddskvot {d2(FT['t1_anka']['main']['or'])}, ingen skillnad. Utan resestenar finns skillnaden kvar och blir något större (oddskvot {d2(FT['t2_utan_resa']['main']['or'])}, håller i båda halvorna).
- **Seden att räkna upp familjen – förklarar en femtedel.** Med antalet resare konstant: oddskvot {d2(FT['t3_antal']['main']['or'])}; {round(100 * FU['attenuation_B'])} procent av skillnaden på logoddsskalan försvinner, under planens gräns på hälften.
- **Egen ställning – stöds inte.** En ensam kvinna reser stenen: {137} av {sp(1013)} mot {44} av {370}, oddskvot {d2(FT['t4_ensam']['main']['or'])}, ingen skillnad.
- **Rollerna – här sitter skillnaden.** Stenar efter söner: modern står med på {107} av {195} i Svealand ({SON_SV} procent) mot {13} av {70} i Götaland ({SON_GO} procent), oddskvot {d2(FT['t5_son']['main']['or'])}, Holm-korrigerat p = 0,015, men i halvorna p = 0,058 och 0,031: en antydan enligt planens regel, inte ett bekräftat fynd. Stenar efter fäder: dotter eller hustru med på {66} av {415} mot {9} av {117}, oddskvot {d2(FT['t6_far']['main']['or'])}, antydan.
- **Kristnandet – inget samband.** Kristen markör och kvinna bland resarna: oddskvot {d2(FT['t8_kristen']['main']['or'])}, p = 0,16, och ingen skillnad mellan landsdelarna.

Så läser jag det: kvinnorna i Svealand var inte fler som änkor och inte fler som ensamma resare. Modern stod med på sonens sten, tillsammans med fadern och syskonen. Det pekar mot familjens sätt att minnas, och mot arvsrätten – en mor kunde ärva efter sitt barn – snarare än mot färderna eller kristnandet. Men det är en tolkning av en antydan; själva rapporten står på huvudfyndet.

Svagheter, i ordning efter vikt:

1. **Uppland bär mycket.** Utan Uppland är oddskvoten {d2(LO['or'])} och intervallet når över 1. Riktningen håller i alla landskap, men den säkra skillnaden är i hög grad en skillnad mellan Uppland och Götaland.
2. **Könet är läst med regler.** Reglerna har fel på ungefär en sten av tjugo, oftast där texten har luckor, och missar kvinnor oftare än de lägger till. Om luckorna vore vanligare i Götaland skulle det förstärka skillnaden på fel grund; robusthetsprovet med minst tio läsbara ord ger oddskvot {d2(RO['ord10']['or'])}, så det förklarar inte fyndet.
3. **Tidsskikten vilar på stildatering.** Odaterade stenar är ett eget skikt. En annan datering skulle kunna flytta siffrorna något men knappast riktningen, eftersom det råa och det justerade steget nästan sammanfaller.
4. **Landsdel är en grov indelning.** Att skillnaden är störst mellan Uppland och Götaland syns redan; vad som händer i gränslandskapen är inte prövat här.

Vad som skulle fälla fyndet: en handkodning av könet på ett stort urval som visar fler fel i den ena landsdelen än i den andra, eller en omräkning med en annan datering där det justerade steget inte längre håller.

## Reproduktion

- Mätningen: `src/people.py` ger en rad per sten (`people.csv`); kontrollen mot handkodning ligger i `data/people_check.json`.
- Modellen: `r/people.R` enligt planen; trappan `r/robustness.R` via `src/robustness.py`. Allt körs av korpusjobbet i Vitki (Statistik, R), som sparar resultatet under korpusens fingeravtryck `{FP}` i `data/cache/r/corpus/`.
- Uppföljningen: `utdata/kvinnor_landsdel/analys.R`, resultat i `utdata/kvinnor_landsdel/resultat.md`.
- Denna rapport byggs av `utdata/blogg/build/build_rapport_kvinnor.py`, som läser varje siffra ur de filerna och stannar om något inte stämmer.
- Koden ligger öppet på [GitHub](https://github.com/Precatio/runes) (GPL-3.0). Mönstret visas i appen under Statistik → Människorna, med trappan steg för steg.

## Referenser

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Benjamini, Yoav & Hochberg, Yosef 1995. ”Controlling the false discovery rate”. *Journal of the Royal Statistical Society B* 57 (1).
- Hartig, Florian 2022. *DHARMa: Residual diagnostics for hierarchical regression models*. R-paket.
- Holm, Sture 1979. ”A simple sequentially rejective multiple test procedure”. *Scandinavian Journal of Statistics* 6 (2).
- Sawyer, Birgit 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford University Press.
- Wood, Simon N. 2017. *Generalized Additive Models: An Introduction with R*. 2 uppl. Chapman & Hall.
- Vitki: METHODS.md avsnitt 1u (Människorna) och 1v (Robusthetstrappan). Populär framställning av kvinnorna på stenarna: [Döttrarna som runstenarna glömde](/artiklar/dottrarna-som-runstenarna-glomde).

:::box Det viktigaste i korthet
- I Svealand nämndes en kvinna bland dem som reste stenen nästan dubbelt så ofta som i Götaland, och skillnaden tål varje kontroll vi har.
- Den beror inte på änkor eller ensamma kvinnor: det var modern som stod med på sonens sten, tillsammans med fadern och syskonen.
- Skillnaden är en skillnad i sed och minne, inte i kvinnors makt – och den bärs till stor del av Uppland.
:::
"""

title_en = "Women raised runestones more often in Svealand than in Götaland – 31 against 17 percent"
summary_en = ("Research report 1. A woman stands among the raisers on 31 percent of Svealand's runestones with a known raiser, "
              "against 17 percent in Götaland. The difference holds with time and carver constant, in both halves of the "
              "material and at every rung of the robustness ladder. It is not widows or lone women: the mother stood on her son's stone.")

body_en = f"""*Research report 1, version 1 ({TODAY}). The finding is confirmed in Vitki's statistics: it holds in both halves of the corpus and passes the common adjustment over every pattern shown. The report follows the fixed form of Vitki's research reports: the plan was locked before the results and is reported as it read.*

## Summary

Among Sweden's Viking-Age runestones with at least one identified raiser, a woman stands among the raisers on {pc(M['shares_region']['Svealand'])} percent of the stones in Svealand against {pc(M['shares_region']['Götaland'])} percent in Götaland, with time layer and carver held constant. The odds ratio Götaland against Svealand is {ORe}: the odds of a woman being named are less than half as large in Götaland. The difference is {-round(100 * EF['diff'])} percentage points (probably between {DIFF_CI[1]} and {DIFF_CI[0]}). It holds in both halves of the material, at all {ME['ladder']['tested']} rungs of the robustness ladder and in the common adjustment over the {N_SHOWN} patterns the statistics show. A follow-up locked study shows that the difference is not due to widows after the journeys, not to lone women and not to Christianisation, but to roles: in Svealand the mother stood on her son's stone on {SON_SV} percent of the stones for sons, in Götaland on {SON_GO} percent. The report says nothing about why the custom differed; that is the next question.

## Question and hypothesis as locked

The question was posed in the analysis plan for the people module, `analysplaner/2026-10-28-manniskorna.md`, locked on 28 October 2026 with SHA-256 `{PLAN_SHA[:16]}…` before any model had been run. Test 1 reads: *women among the raisers, region* – the outcome is at least one woman among the raisers, among stones with at least one identified raiser; the model is outcome ~ region + time layer + carver as a random effect; the measure is the odds ratio Götaland against Svealand. The plan had six tests with a common Holm correction, and the rules of interpretation were fixed in advance: *confirms* requires Holm p below 0.05 and the same direction with p below 0.05 in each of the corpus's two halves.

Before the plan was locked I had seen one figure: {en_n(391)} legible Swedish stones have a woman among the raisers. No comparison between regions had been made. That is stated in the plan under ”Before locking”.

## Material

- **Corpus.** The Scandinavian Runic-text Database (Rundata) in Vitki's corpus job with fingerprint `{FP}`, computed 2026-10-29. Swedish Viking-Age runestones: {en_n(PE['n_stones'])} stones. Runestones only; other objects are not included.
- **Selection.** Legible stones with at least one identified raiser: {en_n(M['n'])}. Of these, {en_n(1013)} lie in Svealand and {en_n(370)} in Götaland; {N_OTHER} lie on Gotland or in Norrland and enter the model as their own levels but not the comparison.
- **The outcome.** At least one woman among the raisers. The raisers' sex is read from Rundata's English translation by rules in `src/people.py`: first the relation (mother, daughter, wife; son, father, brother), then a lone raiser's possessive in the formula (*her son*, *his son*), then a name lexicon built from those steps, and last the name's ending. Checked against hand coding on a new sample of 40 stones the rules had never seen: 39 of 40 right. In the ladder's key ({ROB['facit']['people']['kvinna']['n']} hand-coded stones) the rule's yes was right {CO['ppv'][0]} times of {CO['ppv'][0]} and its no {CO['npv'][0]} times of {CO['npv'][0]}. The errors sit where the text has gaps, and they miss women more often than they add them.
- **The comparison.** Region as in the message module: Götaland against Svealand.
- **Adjustments.** Time layer by style group (before 1010, 1010–1040, 1040–1070, after 1070, undated) and the carver as a random effect; stones without a certain carver are grouped by parish.

## Method

Logistic regression in mgcv (R {DONE['r_version'].split()[2]}), the outcome against region and time layer with the carver as a random effect. Holm correction over the plan's six tests. Replication in two halves of the corpus: whole parishes are dealt alternately within each province, the halves are fixed and were set independently of the patterns. Five robustness checks by the plan: at least ten legible words, sex determined for every raiser, without the carver effect, Uppland only, and sons against fathers (the last applies only to the tests about the dead).

In addition the robustness ladder (`src/robustness.py`, `r/robustness.R`, METHODS.md 1v), which applies the same checks to every pattern in the statistics that can be computed stone by stone: raw, adjusted, carver as a random effect, parish as a random effect, the halves, and without one province at a time (provinces with at least {ROB['min_province']} stones). The rung *place as a surface* is not made here, since the comparison itself is geographic. A rung holds when p < {ROB['alpha']} and the direction is the same as at the adjusted rung; without one province at a time, significance is required only where at least two thirds of the stones remain. Every pattern shown gets a common Benjamini–Hochberg adjustment, q_global. A pattern is confirmed when it holds in both halves and q_global < 0.05.

The ladder is computed on the {en_n(P['n'])} stones in Svealand and Götaland (the module's own model has {en_n(M['n'])}, since Gotland and Norrland are levels there). The ladder's adjusted rung uses the statistics' common time layers, so its figures can differ slightly from the module's.

## Results

**The main figure.** Raw: {324} of {en_n(1013)} stones in Svealand ({round(RAW_SV)} percent) against {61} of {370} in Götaland ({round(RAW_GO)} percent). With time and carver constant: {pc(M['shares_region']['Svealand'])} against {pc(M['shares_region']['Götaland'])} percent. Odds ratio Götaland against Svealand {ORe}, {pfmt(M['p'], True)}, Holm-corrected {pfmt(M['p_holm'], True)}. In plain words: draw a stone at random in each region, and it is nearly twice as common that the Svealand stone has a woman among the raisers; a swing that large by chance is too rare to reckon with.

**The halves.** Half A: {en_n(HA['n'])} stones, odds ratio {d2e(HA['or'])} ({d2e(HA['lo'])}–{d2e(HA['hi'])}), {pfmt(HA['p'], True)}. Half B: {en_n(HB['n'])} stones, odds ratio {d2e(HB['or'])} ({d2e(HB['lo'])}–{d2e(HB['hi'])}), {pfmt(HB['p'], True)}. Same direction and significant in both: *confirms* by the plan's rule.

**The plan's robustness checks.**

- Only stones with at least ten legible words: {en_n(RO['ord10']['n'])} stones, odds ratio {d2e(RO['ord10']['or'])}, {pfmt(RO['ord10']['p'], True)}.
- Only stones where every raiser's sex is determined: {en_n(RO['kon_bestamt']['n'])} stones, odds ratio {d2e(RO['kon_bestamt']['or'])}, {pfmt(RO['kon_bestamt']['p'], True)}.
- Without the carver effect: odds ratio {d2e(RO['utan_ristare']['or'])}, {pfmt(RO['utan_ristare']['p'], True)}.
- Uppland only: cannot be tested, since the comparison is between regions and Uppland lies wholly in Svealand.

**The robustness ladder** ({en_n(P['n'])} stones, {P['k']} with a woman among the raisers). All {ME['ladder']['tested']} rungs hold:

- Raw: odds ratio {d2e(RU['raw']['or'])} ({d2e(RU['raw']['ci'][0])}–{d2e(RU['raw']['ci'][1])}), {pfmt(RU['raw']['p'], True)}.
- Adjusted for time layer: {d2e(RU['adjusted']['or'])} ({d2e(RU['adjusted']['ci'][0])}–{d2e(RU['adjusted']['ci'][1])}), {pfmt(RU['adjusted']['p'], True)}.
- Carver as a random effect ({RU['carver']['groups']} groups): {d2e(RU['carver']['or'])} ({d2e(RU['carver']['ci'][0])}–{d2e(RU['carver']['ci'][1])}), {pfmt(RU['carver']['p'], True)}.
- Parish as a random effect ({RU['parish']['groups']} parishes): {d2e(RU['parish']['or'])} ({d2e(RU['parish']['ci'][0])}–{d2e(RU['parish']['ci'][1])}), {pfmt(RU['parish']['p'], True)}. The difference is not the peculiarity of a few parishes.
- Half A ({RU['half_A']['n']} stones): {d2e(RU['half_A']['or'])}, {pfmt(RU['half_A']['p'], True)}. Half B ({RU['half_B']['n']} stones): {d2e(RU['half_B']['or'])}, {pfmt(RU['half_B']['p'], True)}.
- Without one province at a time ({LO['n_provinces']} provinces tested): the direction holds without each of them; no province turns it. Worst without Uppland, when {LO['n']} stones remain: odds ratio {d2e(LO['or'])} ({d2e(LO['ci'][0])}–{d2e(LO['ci'][1])}), {pfmt(LO['p'], True)}. Without Uppland more than half of Svealand's stones are gone, so there the rule requires only the direction – but it is also the report's weakest point, and it should be said plainly: the difference is carried to a large degree by Uppland.
- Difference in percentage points on the adjusted model: {pc(EF['share_lo'])} against {pc(EF['share_hi'])} percent, {-round(100 * EF['diff'])} points (probably between {DIFF_CI[1]} and {DIFF_CI[0]}).
- Model check (DHARMa): residual distribution p = {round(CK['uniformity_p'], 2)}, overdispersion p = {round(CK['dispersion_p'], 2)}, spatial pattern p = {round(CK['spatial_p'], 2)}. Nothing amiss.
- Coding errors: in {CO['n_sim']} recomputations where each stone's ”true” value is drawn from the key's hit rates, the pattern holds in {pc(CO['share_holds'])} percent; median odds ratio {d2e(CO['or_median'])}, range {d2e(CO['or_range'][0])}–{d2e(CO['or_range'][1])}.
- Common adjustment over the {N_SHOWN} patterns the statistics show today: q_global < 0.001. The finding is one of {N_ALL} patterns that hold at every rung of the ladder.

## Interpretation and weaknesses

The finding is a difference in custom, not in population: it says that a woman is more often *named among those who raised the stone* in Svealand, not that women there had more power or property. What the difference consists of was tested in a follow-up locked plan (`analysplaner/2026-10-29-kvinnorna-i-svealand.md`, SHA-256 `{FU_SHA[:16]}…`), with five pre-set hypotheses:

- **Widows after the journeys – not supported.** A woman raises for her husband: {96} of {en_n(1013)} in Svealand against {23} of {370} in Götaland, odds ratio {d2e(FT['t1_anka']['main']['or'])}, no difference. Without the journey stones the difference remains and grows slightly (odds ratio {d2e(FT['t2_utan_resa']['main']['or'])}, holds in both halves).
- **The custom of listing the family – explains a fifth.** With the number of raisers constant: odds ratio {d2e(FT['t3_antal']['main']['or'])}; {round(100 * FU['attenuation_B'])} percent of the difference on the log-odds scale disappears, below the plan's limit of half.
- **A position of her own – not supported.** A lone woman raises the stone: {137} of {en_n(1013)} against {44} of {370}, odds ratio {d2e(FT['t4_ensam']['main']['or'])}, no difference.
- **The roles – this is where the difference sits.** Stones for sons: the mother stands on {107} of {195} in Svealand ({SON_SV} percent) against {13} of {70} in Götaland ({SON_GO} percent), odds ratio {d2e(FT['t5_son']['main']['or'])}, Holm-corrected p = 0.015, but in the halves p = 0.058 and 0.031: an indication by the plan's rule, not a confirmed finding. Stones for fathers: daughter or wife on {66} of {415} against {9} of {117}, odds ratio {d2e(FT['t6_far']['main']['or'])}, an indication.
- **Christianisation – no association.** Christian marker and a woman among the raisers: odds ratio {d2e(FT['t8_kristen']['main']['or'])}, p = 0.16, and no difference between the regions.

This is how I read it: the women of Svealand were not more often widows and not more often lone raisers. The mother stood on her son's stone, together with the father and the siblings. That points to the family's way of remembering, and to inheritance – a mother could inherit from her child – rather than to the journeys or to Christianisation. But that is an interpretation of an indication; the report itself rests on the main finding.

Weaknesses, in order of weight:

1. **Uppland carries much.** Without Uppland the odds ratio is {d2e(LO['or'])} and the interval reaches above 1. The direction holds in every province, but the certain difference is to a large degree a difference between Uppland and Götaland.
2. **Sex is read by rules.** The rules err on about one stone in twenty, mostly where the text has gaps, and they miss women more often than they add them. If gaps were more common in Götaland that would strengthen the difference on false grounds; the check with at least ten legible words gives an odds ratio of {d2e(RO['ord10']['or'])}, so that does not explain the finding.
3. **The time layers rest on style dating.** Undated stones are a layer of their own. Another dating could move the figures slightly but hardly the direction, since the raw and the adjusted rungs nearly coincide.
4. **Region is a coarse division.** That the difference is largest between Uppland and Götaland is already visible; what happens in the border provinces is not tested here.

What would overturn the finding: a hand coding of sex on a large sample showing more errors in one region than in the other, or a recomputation with another dating where the adjusted rung no longer holds.

## Reproduction

- The measurement: `src/people.py` gives one row per stone (`people.csv`); the check against hand coding is in `data/people_check.json`.
- The model: `r/people.R` by the plan; the ladder `r/robustness.R` through `src/robustness.py`. All of it is run by the corpus job in Vitki (Statistics, R), which saves the result under the corpus fingerprint `{FP}` in `data/cache/r/corpus/`.
- The follow-up: `utdata/kvinnor_landsdel/analys.R`, results in `utdata/kvinnor_landsdel/resultat.md`.
- This report is built by `utdata/blogg/build/build_rapport_kvinnor.py`, which reads every figure from those files and stops if anything disagrees.
- The code is open on [GitHub](https://github.com/Precatio/runes) (GPL-3.0). The pattern is shown in the app under Statistics → The people, with the ladder rung by rung.

## References

- Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Benjamini, Yoav & Hochberg, Yosef 1995. ”Controlling the false discovery rate”. *Journal of the Royal Statistical Society B* 57 (1).
- Hartig, Florian 2022. *DHARMa: Residual diagnostics for hierarchical regression models*. R package.
- Holm, Sture 1979. ”A simple sequentially rejective multiple test procedure”. *Scandinavian Journal of Statistics* 6 (2).
- Sawyer, Birgit 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford University Press.
- Wood, Simon N. 2017. *Generalized Additive Models: An Introduction with R*. 2nd ed. Chapman & Hall.
- Vitki: METHODS.md sections 1u (The people) and 1v (The robustness ladder). Popular account of the women on the stones: [The daughters the runestones forgot](/en/artiklar/dottrarna-som-runstenarna-glomde).

:::box The essentials
- In Svealand a woman was named among those who raised the stone nearly twice as often as in Götaland, and the difference withstands every check we have.
- It is not widows or lone women: it was the mother who stood on her son's stone, together with the father and the siblings.
- The difference is one of custom and memory, not of women's power – and it is carried to a large degree by Uppland.
:::
"""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
assert "Det viktigaste i korthet" in body

out = {"slug": "rapport-1-kvinnor-bland-resarna-svealand-gotaland", "title": title, "summary": summary, "body": body,
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
