"""Forskningsrapport (låst mall utdata/rapporter/MALL.md): "Söner och bröder dog utanför Norden oftare än fäder och makar
– 10 mot 3 procent" (sv + en). Test 5 i den låsta planen för människomodulen (analysplaner/2026-10-28-manniskorna.md),
robusthetstrappan (src/robustness.py, METHODS 1v) och testen 3–4 (drengr, þegn) i samma plan. Alla siffror asserteras
mot korpusjobbets filer (data/cache/r/corpus/<FP>/) och räknas om ur corpus.csv och people.csv.
    ../../../.venv/bin/python build_rapport_unga.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels, r_findings, robustness  # noqa: E402
from src import r_bridge as rb  # noqa: E402

FP = "e83202e01a5e6d27"
C = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
DONE = json.load(open(os.path.join(C, "done.json"), encoding="utf-8"))
assert DONE["fingerprint"] == FP and DONE["r_version"].startswith("R version 4.6.1")
APP_VERSION = json.load(open(os.path.join(ROOT, "web", "package.json")))["version"]
assert APP_VERSION == "3.0.0"
REPORT_VERSION = 1
TODAY = "2026-10-31"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = "analysplanen låstes 2026-10-28; materialet frystes 2026-10-29"
TL_EN = "the analysis plan was locked 2026-10-28; the material was frozen 2026-10-29"
PE = json.load(open(os.path.join(C, "people.json"), encoding="utf-8"))
ROB = json.load(open(os.path.join(C, "robustness.json"), encoding="utf-8"))
PLAN_SHA = open(os.path.join(ROOT, "analysplaner", "2026-10-28-manniskorna.sha256")).read().split()[0]
assert PLAN_SHA.startswith("ea26a388")

pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731
d1 = lambda x: f"{x:.1f}".replace(".", ",")  # noqa: E731
d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_n = lambda n: f"{n:,}"  # noqa: E731


def pfmt(p, en=False):
    if p < 0.001:
        return "p < 0.001" if en else "p < 0,001"
    s = f"{p:.3f}" if p < 0.01 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the plan's tests (r/people.R) -------------------------------------------------------------------------------------
assert PE["n_stones"] == 2320 and PE["plan"] == "analysplaner/2026-10-28-manniskorna.md"
T = {t["key"]: t for t in PE["tests"]}
DB, DR, TH = T["dod_borta_ung"], T["drengr_ung"], T["thegn_ung"]
assert DB["status"] == "bekräftar" and DB["replicated"] is True
assert DR["status"] == "mönster att pröva" and TH["status"] == "mönster att pröva"
M, HA, HB, RO = DB["main"], DB["halves"]["A"], DB["halves"]["B"], DB["robustness"]
assert (M["n"], M["k"]) == (945, 56) and d2(M["or"]) == "4,10" and (d2(M["lo"]), d2(M["hi"])) == ("2,18", "7,69")
assert M["p"] < 1e-4 and M["p_holm"] < 2e-4
SH_Y, SH_O = M["shares"]["1"], M["shares"]["0"]
assert (d1(100 * SH_Y), d1(100 * SH_O)) == ("9,7", "2,6")
assert (HA["n"], HB["n"]) == (481, 464) and d2(HA["or"]) == "3,03" and d2(HB["or"]) == "5,82" and 0.01 < HA["p"] < 0.02 and HB["p"] < 0.001
assert (d1(100 * HA["shares"]["1"]), d1(100 * HA["shares"]["0"]), d1(100 * HB["shares"]["1"]), d1(100 * HB["shares"]["0"])) == ("8,2", "2,9", "11,1", "2,2")
assert (RO["ord10"]["n"], d2(RO["ord10"]["or"])) == (661, "4,80") and RO["ord10"]["p"] < 0.001
assert d2(RO["utan_ristare"]["or"]) == "4,02" and RO["utan_ristare"]["p"] < 0.001 and RO["kon_bestamt"] is None
assert (RO["uppland"]["n"], d2(RO["uppland"]["or"])) == (489, "4,93") and 0.002 < RO["uppland"]["p"] < 0.003
assert (RO["son_far"]["n"], d2(RO["son_far"]["or"])) == (653, "5,26") and RO["son_far"]["p"] < 0.001
DRM, THM = DR["main"], TH["main"]
assert d1(DRM["or"]) == "8,7" and 2e-4 < DRM["p_holm"] < 4e-4 and DR["halves"]["B"]["too_few"] and DR["halves"]["A"]["p"] < 0.01
assert d2(THM["or"]) == "0,22" and 0.01 < THM["p_holm"] < 0.02 and TH["halves"]["A"]["p"] > 0.05 and TH["halves"]["B"]["p"] > 0.05

# ---- the raw counts, the same selection as r/people.R ----------------------------------------------------------------
c = pd.read_csv(os.path.join(C, "corpus.csv"), low_memory=False)
p = pd.read_csv(os.path.join(C, "people.csv"))
x = c.merge(p, on="signum")
x = x[(x.legible == 1) & x.region.isin(["Svealand", "Götaland", "Gotland", "Norrland"])]
young = ((x.rel_barn == 1) | (x.rel_syskon == 1)) & ~((x.rel_foralder == 1) | (x.rel_make == 1))
older = ((x.rel_foralder == 1) | (x.rel_make == 1)) & ~((x.rel_barn == 1) | (x.rel_syskon == 1))
men = (x.doda_k == 0) & (x.doda_m >= 1)
Y, O = x[young & men], x[older & men]
RAW = {"y_n": len(Y), "y_k": int(Y.dod_borta.sum()), "o_n": len(O), "o_k": int(O.dod_borta.sum()),
       "y_dr": int(Y.drengr.sum()), "o_dr": int(O.drengr.sum()), "y_th": int(Y.thegn.sum()), "o_th": int(O.thegn.sum())}
assert RAW == {"y_n": 393, "y_k": 41, "o_n": 552, "o_k": 15, "y_dr": 27, "o_dr": 4, "y_th": 5, "o_th": 26}, RAW
YB = Y[Y.dod_borta == 1]
WHO = {"barn": int(YB.rel_barn.sum()), "syskon": int(YB.rel_syskon.sum()), "moder": int(((YB.resare_k > 0) & (YB.rel_barn == 1)).sum()),
       "kvinna": int((YB.resare_k > 0).sum())}
assert WHO == {"barn": 26, "syskon": 15, "moder": 13, "kvinna": 13}, WHO
ALL = x[men & (x.dod_borta == 1)]
WIDOW = {"n": len(ALL), "make": int(ALL.rel_make.sum())}
assert WIDOW == {"n": 69, "make": 4}, WIDOW
sons = men & (x.rel_barn == 1) & ~((x.rel_foralder == 1) | (x.rel_make == 1))
fathers = men & (x.rel_foralder == 1) & ~((x.rel_barn == 1) | (x.rel_syskon == 1))
SONS, FATHERS = (int(x[sons].dod_borta.sum()), int(sons.sum())), (int(x[fathers].dod_borta.sum()), int(fathers.sum()))
assert (SONS, FATHERS) == ((26, 230), (13, 496))
REG = {r: ((int(Y[Y.region == r].dod_borta.sum()), int((Y.region == r).sum())), (int(O[O.region == r].dod_borta.sum()), int((O.region == r).sum())))
       for r in ("Svealand", "Götaland")}
assert REG == {"Svealand": ((26, 261), (12, 423)), "Götaland": ((15, 124), (3, 121))}, REG

# ---- the robustness ladder (src/robustness.py, METHODS 1v) ------------------------------------------------------------
P = ROB["patterns"]["Människorna|people_dod_borta_ung"]
SPEC = ROB["specs"]["Människorna|people_dod_borta_ung"]
RU = P["rungs"]
assert (P["n"], P["k"], P["direction"]) == (945, 56, 1) and set(RU) == {"raw", "adjusted", "carver", "parish", "place", "half_A", "half_B", "lopo"}
assert all(r["holds"] for r in RU.values()) and SPEC["adjust"] == ["province", "epoch"] and SPEC["lopo"] and SPEC["place"]
assert [d2(RU[k]["or"]) for k in ("raw", "adjusted", "carver", "parish", "place", "half_A", "half_B", "lopo")] == \
    ["4,17", "3,90", "4,41", "4,04", "2,56", "3,19", "5,53", "3,64"]
assert (RU["carver"]["groups"], RU["parish"]["groups"], RU["place"]["n"], RU["half_A"]["n"], RU["half_B"]["n"]) == (394, 399, 567, 476, 469)
LO = RU["lopo"]
assert (LO["without"], LO["n"], LO["n_provinces"], LO["all_hold"], LO["flips"]) == ("U", 456, 5, True, []) and 0.001 < LO["p"] < 0.002
assert 0.01 < RU["place"]["p"] < 0.02
EF, CK, CO = P["effect"], P["check"], P["coding"]
assert (d1(100 * EF["share_hi"]), d1(100 * EF["share_lo"]), d1(100 * EF["diff"]), [d1(100 * v) for v in EF["diff_ci"]]) == ("9,9", "2,9", "7,0", ["3,8", "10,2"])
assert CK["ok"] is False and 0.03 < CK["dispersion_p"] < 0.04 and CK["uniformity_p"] > 0.5 and CK["spatial_p"] > 0.1
assert (CO["n_sim"], CO["share_holds"], CO["ppv"], CO["npv"]) == (200, 1, [92, 0], [113, 0]) and d2(CO["or_median"]) == "3,65"
assert (d2(CO["or_range"][0]), d2(CO["or_range"][1])) == ("2,37", "4,17") and ROB["facit"]["messages"]["dod_borta"]["n"] == 205
ANN = robustness.annotate(r_findings.corpus_patterns(rb.JOB.result(FP)), robustness.load(FP))
ME = next(q for q in ANN if q["key"] == "people_dod_borta_ung")
SUMM = robustness.summary(ANN)
N_SHOWN, N_ALLRUNG = SUMM["n_fdr"], SUMM["all_rungs"]
assert ME["confirmed"] is True and ME["ladder"]["passed"] == ME["ladder"]["tested"] == 8 and ME["q_global"] < 0.001
assert (N_SHOWN, N_ALLRUNG) == (48, 15)

SLUG = "soner-och-broder-dog-utanfor-norden"
title = "Söner och bröder dog utanför Norden oftare än fäder och makar – 10 mot 3 procent"
title_en = "Sons and brothers died outside Scandinavia more often than fathers and husbands – 10 against 3 percent"
summary = ("Förregistrerad studie. På runstenar efter söner och bröder står det att den döde dog utanför Norden på 10 procent av "
           "stenarna, mot 3 procent efter fäder och makar. Skillnaden håller med tid, landskap och ristare konstanta, i båda "
           "halvorna av materialet och i alla känslighetsanalyser. Färderna tycks ha hört till en livsfas: tiden innan egen familj.")
summary_en = ("Pre-registered study. On runestones for sons and brothers the stone says the dead man died outside Scandinavia on "
              "10 percent of the stones, against 3 percent for fathers and husbands. The difference holds with time, province and "
              "carver constant, in both halves of the material and in every sensitivity analysis. The journeys seem to have "
              "belonged to a stage of life: the time before a family of one's own.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/forskningsrapporter/{SLUG}")


def chart(sv):
    yl, ol = ("Söner och bröder", "Fäder och makar") if sv else ("Sons and brothers", "Fathers and husbands")
    rows = [":::chart Dog utanför Norden, andel av stenarna efter den dödes plats i släkten" if sv else
            ":::chart Died outside Scandinavia, share of the stones by the dead man's place in the family",
            "# " + ("Hela materialet, tid, landskap och ristare konstanta" if sv else "All the material, time, province and carver constant"),
            f"+{yl} | {d1(100 * SH_Y) if sv else f'{100 * SH_Y:.1f}'} | {'rått' if sv else 'raw'} {RAW['y_k']} {'av' if sv else 'of'} {RAW['y_n']}",
            f"{ol} | {d1(100 * SH_O) if sv else f'{100 * SH_O:.1f}'} | {'rått' if sv else 'raw'} {RAW['o_k']} {'av' if sv else 'of'} {RAW['o_n']}",
            "# " + ("Halva A" if sv else "Half A"),
            f"+{yl} | {d1(100 * HA['shares']['1']) if sv else f'{100 * HA['shares']['1']:.1f}'} | {HA['n']} {'stenar' if sv else 'stones'}",
            f"{ol} | {d1(100 * HA['shares']['0']) if sv else f'{100 * HA['shares']['0']:.1f}'} |",
            "# " + ("Halva B" if sv else "Half B"),
            f"+{yl} | {d1(100 * HB['shares']['1']) if sv else f'{100 * HB['shares']['1']:.1f}'} | {HB['n']} {'stenar' if sv else 'stones'}",
            f"{ol} | {d1(100 * HB['shares']['0']) if sv else f'{100 * HB['shares']['0']:.1f}'} |",
            ("Källa: Rundata. Modellens andelar (marginaleffekter)." if sv else "Source: Rundata. Model shares (marginal effects)."),
            ":::"]
    return "\n".join(rows)


body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, utlandsfärder, släktskap, livsfas, drengr, þegn, logistisk regression, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Runstenarna efter män som dog i öster och väster är bland de mest kända, och orden för de döda – *drengr* och *þegn* – har lästs som ord för unga respektive äldre män. Frågan här är om de som dog utanför Norden oftare var söner och bröder än fäder och makar, när tid, landskap och ristare hålls konstanta.
**Material.** {sp(M['n'])} läsbara svenska runstenar från vikingatiden där alla döda är män och den döde är antingen son eller bror (en yngre plats i släkten) eller far eller make (en äldre plats), ur Samnordisk runtextdatabas (Rundata): {RAW['y_n']} respektive {RAW['o_n']} stenar.
**Metod.** Förregistrerad logistisk regression med släktplats, landsdel och dateringsperiod som förklarande variabler och ristaren som slumpeffekt; Holm-korrigering över studiens sex test; intern replikering i två på förhand bestämda halvor; åtta känslighetsanalyser; justering för alla {N_SHOWN} samband som projektet redovisar.
**Resultat.** Stenen säger att den döde dog utanför Norden på {d1(100 * SH_Y)} procent av stenarna efter söner och bröder mot {d1(100 * SH_O)} procent efter fäder och makar; oddskvot {d2(M['or'])} (95 %-intervall {d2(M['lo'])}–{d2(M['hi'])}), {pfmt(M['p'])}, Holm-korrigerat {pfmt(M['p_holm'])}. Samma riktning och signifikant i båda halvorna, och alla känslighetsanalyser håller, också utan ett landskap i taget; justerat för alla samband q < 0,001. Av alla {WIDOW['n']} stenar efter män som dog borta är bara {WIDOW['make']} resta av en hustru.
**Slutsats.** Färderna i öster och väster hörde i första hand till unga män i en familj, inte till familjefäderna. Det stöder läsningen av *drengr* som ett ord för den unga mannen, men talar om en livsfas och inte om en exakt ålder.

## 1. Inledning

Runstenar efter män som dog utomlands hör till de mest studerade. Mats G. Larsson (1990) har gått igenom stenarna om utlandsfärder och vad de säger om samhället bakom dem. Judith Jesch (2001) har undersökt ordförrådet i runinskrifterna och skaldediktningen om färder och följen, bland annat orden *drengr* och *þegn*. Lauren Goetting (2006) har argumenterat för att *drengr* främst användes om unga män i ett krigarfölje och *þegn* om äldre, etablerade män, och Denis Sukhino-Khomenko (2024) har följt *þegn* runt Nordsjön. Ingen av dem har mätt om den som dog borta oftare var en ung man i sin familj än en äldre, med tid, trakt och ristare konstanta.

Syftet med den här studien är att pröva det, med släktplatsen som mått: en son eller bror står i en yngre plats i släkten än en far eller make. Det är inte detsamma som ålder, men det är det närmaste mått inskrifterna själva ger.

## 2. Förregistrering: hypotes och plan

Hypotesen, modellen och tolkningsreglerna skrevs ned i en analysplan den 28 oktober 2026, innan någon modell hade körts. Planen gällde en studie av vilka som reste runstenarna och efter vem, med sex test; detta är test 5. Planen är tidsstämplad i projektets versionshantering och har kontrollsumman SHA-256 `{PLAN_SHA[:16]}…` (se Data och kod).

Testet lyder i planen: utfallet är att stenen säger att den döde dog utanför Norden, bland stenar där budskapet går att läsa; den döde är *ung* i släkten när han är barn eller syskon till resaren och varken förälder eller make, och *äldre* när han är förälder eller make och varken barn eller syskon; bara stenar där alla döda är män; modellen är utfall ~ ung + landsdel + dateringsperiod + ristaren som slumpeffekt. De sex testen korrigeras tillsammans med Holms metod. Ett test *bekräftar* när Holm-p är under 0,05 och riktningen är densamma med p under 0,05 i var och en av materialets två halvor; ett *mönster att pröva* har Holm-p under 0,05 men håller inte i båda halvorna.

Innan planen låstes hade ingen räkning av död utanför Norden efter släktplats gjorts. För testen 3 och 4 om *drengr* och *þegn* hade jag däremot sett en grov räkning utan modell: *drengr* på 8 procent av stenarna efter söner och bröder mot 0,4 procent efter fäder, och *þegn* tvärtom. Det står i planen. Testen 3 och 4 redovisas därför i avsnitt 5.5 som kompletterande, inte som huvudresultat.

Avsnitt 5.1–5.3 är de analyser planen föreskriver för test 5. Avsnitt 5.4 är beskrivande räkningar på samma urval, gjorda efter testet. Inga andra analyser ingår.

## 3. Material

- **Källa.** Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk vid Uppsala universitet: translitterering, normalisering, engelsk översättning, landskap, socken, ristare och stilgruppering för varje inskrift. Materialet frystes för analysen den 29 oktober 2026.
- **Stenarna.** Vikingatida runstenar i de svenska landskapen: {sp(PE['n_stones'])} stenar. Bara runstenar; andra föremål med runor ingår inte. Skåne och Blekinge förs i Rundata till Danmark och ingår inte.
- **Urval.** Stenar vars text är så bevarad att den döde och hans relation till resaren kan läsas, där alla döda är män och där den döde är antingen ung eller äldre i släkten enligt planen: {RAW['y_n']} stenar efter söner och bröder och {RAW['o_n']} efter fäder och makar, sammanlagt {sp(M['n'])}.
- **Släktplatsen.** Relationen läses ur Rundatas engelska översättning med regler (son, bror, far, make och deras former). Reglerna kontrollerades mot handkodning på ett nytt urval om 40 stenar som de aldrig sett: relationen var rätt på 38 av 40.
- **Utfallet** är att stenen säger att den döde dog utanför Norden: ett ord för död eller ett sätt att dö, nära en plats utanför Norden (öster, väster, Grekland, England, Serkland, Ingvars färd med flera). Att bara ha rest räcker inte, och inte heller att dö på en resa hemma. Regeln kontrollerades mot handkodning av {ROB['facit']['messages']['dod_borta']['n']} stenar: regelns ja var rätt {CO['ppv'][0]} gånger av {CO['ppv'][0]} och regelns nej {CO['npv'][0]} gånger av {CO['npv'][0]}.
- **Landsdel** efter dagens landskap (Svealand, Götaland, Gotland, Norrland) och **dateringsperiod** efter stenens ornamentikstil (Gräslund 2006): före 1010, 1010–1040, 1040–1070, efter 1070, och odaterad som egen grupp.
- **Ristaren.** Den ristare Rundata anger. Stenar utan känd ristare grupperas per socken.

## 4. Metod

**4.1 Modellen.** Logistisk regression i R-paketet mgcv (R {DONE['r_version'].split()[2]}; Wood 2017): utfallet mot släktplats, landsdel och dateringsperiod, med ristaren som slumpeffekt, så att en flitig ristares sätt att formulera stenarna inte räknas som ett mönster. Andelarna är modellens marginaleffekter.

**4.2 Korrigering och replikering.** Holm-korrigering (Holm 1979) över studiens sex test. Intern replikering: materialet delades en gång, för alla projektets analyser, i två halvor socken för socken, och testet ska hålla i var halva för sig. Planens robusthetsprov: bara stenar med minst tio läsbara ord, modellen utan ristarens slumpeffekt, bara Uppland, och bara söner mot bara fäder.

**4.3 Känslighetsanalyser.** Samma fasta serie som för alla samband projektet redovisar: rå modell; justerad för landskap och dateringsperiod; ristaren som slumpeffekt; socknen som slumpeffekt; stenens läge som rumslig yta (bara stenar som står kvar); var halva för sig; och utan ett landskap i taget (landskap med minst {ROB['min_province']} stenar). En analys håller när p är under {str(ROB['alpha']).replace('.', ',')} och riktningen är densamma som i den justerade modellen; utan ett landskap krävs signifikans bara där minst två tredjedelar av stenarna är kvar. p-värdena justeras dessutom tillsammans för alla {N_SHOWN} samband som redovisas (Benjamini & Hochberg 1995); det justerade värdet kallas q. Modellens antaganden prövas med simulerade residualer (DHARMa; Hartig 2022). Felen i utfallsregeln prövas genom {CO['n_sim']} omräkningar där varje stens ”sanna” utfall dras ur kontrollurvalets träffandelar.

**4.4 Avvikelser från planen.** Inga. Planens prov ”kön bestämt för alla resare” gäller bara testen om resarna och görs inte här.

## 5. Resultat

**5.1 Huvudtestet.** Rått säger stenen att den döde dog utanför Norden på {RAW['y_k']} av {RAW['y_n']} stenar efter söner och bröder ({d1(100 * RAW['y_k'] / RAW['y_n'])} procent) och på {RAW['o_k']} av {RAW['o_n']} efter fäder och makar ({d1(100 * RAW['o_k'] / RAW['o_n'])} procent). Med tid, landsdel och ristare konstanta är andelarna {d1(100 * SH_Y)} mot {d1(100 * SH_O)} procent. Oddskvoten är {d2(M['or'])} (95 %-intervall {d2(M['lo'])}–{d2(M['hi'])}), {pfmt(M['p'])}, Holm-korrigerat {pfmt(M['p_holm'])}. I klartext: på en sten efter en son eller bror är det tre till fyra gånger så vanligt att den döde dog borta som på en sten efter en far eller make. Halva A: {HA['n']} stenar, oddskvot {d2(HA['or'])} ({d2(HA['lo'])}–{d2(HA['hi'])}), {pfmt(HA['p'])}. Halva B: {HB['n']} stenar, oddskvot {d2(HB['or'])} ({d2(HB['lo'])}–{d2(HB['hi'])}), {pfmt(HB['p'])}. Testet *bekräftar* enligt planens regel.

{chart(True)}

**5.2 Planens robusthetsprov.**

- Bara stenar med minst tio läsbara ord: {RO['ord10']['n']} stenar, oddskvot {d2(RO['ord10']['or'])}, {pfmt(RO['ord10']['p'])}.
- Utan ristarens slumpeffekt: oddskvot {d2(RO['utan_ristare']['or'])}, {pfmt(RO['utan_ristare']['p'])}.
- Bara Uppland: {RO['uppland']['n']} stenar, oddskvot {d2(RO['uppland']['or'])}, {pfmt(RO['uppland']['p'])}.
- Bara söner mot bara fäder: {RO['son_far']['n']} stenar, oddskvot {d2(RO['son_far']['or'])}, {pfmt(RO['son_far']['p'])}. Rått {SONS[0]} av {SONS[1]} mot {FATHERS[0]} av {FATHERS[1]}.

**5.3 Känslighetsanalyserna** ({M['n']} stenar, {M['k']} med utfallet). Alla {ME['ladder']['tested']} håller:

- Rå modell: oddskvot {d2(RU['raw']['or'])} ({d2(RU['raw']['ci'][0])}–{d2(RU['raw']['ci'][1])}), {pfmt(RU['raw']['p'])}.
- Justerad för landskap och dateringsperiod: {d2(RU['adjusted']['or'])} ({d2(RU['adjusted']['ci'][0])}–{d2(RU['adjusted']['ci'][1])}), {pfmt(RU['adjusted']['p'])}.
- Ristaren som slumpeffekt ({RU['carver']['groups']} ristare och sockengrupper): {d2(RU['carver']['or'])} ({d2(RU['carver']['ci'][0])}–{d2(RU['carver']['ci'][1])}), {pfmt(RU['carver']['p'])}.
- Socknen som slumpeffekt ({RU['parish']['groups']} socknar): {d2(RU['parish']['or'])} ({d2(RU['parish']['ci'][0])}–{d2(RU['parish']['ci'][1])}), {pfmt(RU['parish']['p'])}.
- Stenens läge som rumslig yta ({RU['place']['n']} stenar som står kvar): {d2(RU['place']['or'])} ({d2(RU['place']['ci'][0])}–{d2(RU['place']['ci'][1])}), {pfmt(RU['place']['p'])}. Skillnaden är mindre här, men den står kvar när trakten hålls konstant.
- Halva A ({RU['half_A']['n']} stenar): {d2(RU['half_A']['or'])}, {pfmt(RU['half_A']['p'])}. Halva B ({RU['half_B']['n']} stenar): {d2(RU['half_B']['or'])}, {pfmt(RU['half_B']['p'])}.
- Utan ett landskap i taget ({LO['n_provinces']} landskap prövade): riktningen håller utan vart och ett av dem och är signifikant överallt. Svagast utan Uppland, då {LO['n']} stenar är kvar: oddskvot {d2(LO['or'])} ({d2(LO['ci'][0])}–{d2(LO['ci'][1])}), {pfmt(LO['p'])}.
- Skillnaden i procentenheter i den justerade modellen: {d1(100 * EF['share_hi'])} mot {d1(100 * EF['share_lo'])} procent, {d1(100 * EF['diff'])} enheter (troligen mellan {d1(100 * EF['diff_ci'][0])} och {d1(100 * EF['diff_ci'][1])}).
- Modellens antaganden: residualernas fördelning p = {d2(CK['uniformity_p'])}, kvarvarande rumsligt mönster p = {d2(CK['spatial_p'])}, men överspridning p = {d2(CK['dispersion_p']).rstrip('0')}: modellen fångar inte all variation mellan stenarna, så intervallen är troligen något för smala (se 6).
- Felen i utfallsregeln: sambandet håller i {pc(CO['share_holds'])} procent av de {CO['n_sim']} omräkningarna; oddskvotens median {d2(CO['or_median'])}, spann {d2(CO['or_range'][0])}–{d2(CO['or_range'][1])}.
- Justerat för alla {N_SHOWN} samband som projektet redovisar: q < 0,001. Sambandet är ett av {N_ALLRUNG} som håller i alla känslighetsanalyser.

**5.4 Vilka de var (beskrivande, samma urval).** Av de {RAW['y_k']} söner och bröder som dog utanför Norden var {WHO['barn']} söner och {WHO['syskon']} bröder. På {WHO['kvinna']} av stenarna står en kvinna bland resarna, och alla {WHO['moder']} är mödrar efter sina söner. Av alla {WIDOW['n']} stenar efter män som dog utanför Norden, vilken relation de än hade till resaren, är bara {WIDOW['make']} resta av en hustru. Skillnaden finns i båda de stora landsdelarna: i Svealand {REG['Svealand'][0][0]} av {REG['Svealand'][0][1]} efter söner och bröder mot {REG['Svealand'][1][0]} av {REG['Svealand'][1][1]} efter fäder och makar, i Götaland {REG['Götaland'][0][0]} av {REG['Götaland'][0][1]} mot {REG['Götaland'][1][0]} av {REG['Götaland'][1][1]}.

**5.5 Orden för de döda (planens test 3 och 4).** *drengr* står om den döde på {RAW['y_dr']} av {RAW['y_n']} stenar efter söner och bröder mot {RAW['o_dr']} av {RAW['o_n']} efter fäder och makar: oddskvot {d1(DRM['or'])}, Holm-korrigerat {pfmt(DRM['p_holm'])}, men för få fall i halva B för att pröva där. *þegn* står på {RAW['y_th']} av {RAW['y_n']} mot {RAW['o_th']} av {RAW['o_n']}: oddskvot {d2(THM['or'])}, Holm-korrigerat {pfmt(THM['p_holm'])}, men inte signifikant i någon av halvorna. Båda är *mönster att pröva* enligt planens regel, och för båda var en grov räkning sedd före låsningen.

## 6. Diskussion

**Vad fyndet säger.** De män vars runstenar säger att de dog i öster eller väster var oftare söner och bröder än fäder och makar. Skillnaden är stor, tre till fyra gånger, och den står kvar med tid, landskap och ristare konstanta, i var halva för sig, i varje landskap och när trakten hålls konstant. Bara fyra av de {WIDOW['n']} stenarna efter män som dog borta är resta av en hustru. Färderna tycks ha hört till en livsfas: tiden innan mannen hade en egen familj att resa stenen efter honom.

**Mot tidigare forskning.** Resultatet ger ett mått åt den läsning av orden för de döda som Goetting (2006) har argumenterat för: *drengr* om unga män, *þegn* om äldre. Här följer båda orden släktplatsen åt samma håll som döden borta, men bara som mönster att pröva. Fyndet om döden borta vilar inte på orden utan på relationen, och det är därför ett självständigt stöd för att utlandsfärderna i första hand var unga mäns sak (jfr Jesch 2001; Larsson 1990).

**Svagheter, i ordning efter vikt.**

1. **Släktplats är inte ålder.** En son kan vara medelålders, en bror kan vara äldre än den som reser stenen. Måttet säger att den döde ännu inte var den som andra reste stenar *åt* som far eller make, inte hur gammal han var.
2. **Vem som reser stenen och vad som skrivs hänger ihop.** En far som dog borta kan ha minnts av söner som skrev stenen på ett annat sätt, utan plats för döden. Fyndet gäller vad stenarna säger, och det kan delvis vara en skillnad i hur olika resare formulerade sig.
3. **Överspridning.** Modellkontrollen visar mer variation mellan stenarna än modellen räknar med (p = {d2(CK['dispersion_p']).rstrip('0')}). Oddskvoten påverkas knappast, men intervallen är troligen något för smala. Med {M['k']} stenar med utfallet är de redan breda.
4. **Relationen är läst med regler.** Reglerna hade 38 rätt av 40 på ett nytt urval. Felen i relationen ingår inte i omräkningarna, bara felen i utfallet.

**Vad som skulle fälla fyndet.** Ett prov där resaren hålls konstant – till exempel bara stenar som en förälder reser efter en son jämfört med stenar som en son reser efter en förälder – där skillnaden försvann, eller en handkodning av relationen som visade fler fel bland stenarna om döden borta.

## 7. Slutsats

På runstenarna efter söner och bröder står det oftare att den döde dog utanför Norden än på stenarna efter fäder och makar, {d1(100 * SH_Y)} mot {d1(100 * SH_O)} procent med tid, landskap och ristare konstanta, och skillnaden tål varje känslighetsanalys. Utlandsfärderna hörde i första hand till de unga männen i familjen. Nästa steg är att hålla resaren konstant och pröva orden för de döda på ett större material.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 31 oktober 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod, analysplanen och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Analysplanen: `analysplaner/2026-10-28-manniskorna.md`, med kontrollsumman i `.sha256`-filen bredvid.
- Släktplatsen och resarna: `src/people.py`; handkodningen: `data/people_check.json`.
- Utfallet: `src/messages.py` (döden utanför Norden); handkodningen: `data/messages_facit_ost.csv` och `utdata/brittiska/hemma_kodning.csv`.
- Modellen: `r/people.R`. Känslighetsanalyserna: `r/robustness.R` och `src/robustness.py` (metodbeskrivning i `METHODS.md`, avsnitt 1u och 1v). Resultaten sparas under materialets version `{FP}`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_unga.py`, som räknar de beskrivande talen, läser resten ur resultatfilerna och stannar om något inte stämmer.
- I Vitki visas sambandet under Statistik, Människorna, med känslighetsanalyserna steg för steg. Populär framställning: [Färderna var de ungas](/artiklar/fardena-var-de-ungas).

## Referenser

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), s. 289–300.
- Goetting, L. 2006. Þegn and drengr in the Viking Age. *Scandinavian Studies* 78 (4), s. 375–404.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R-paket.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Jesch, J. 2001. *Ships and Men in the Late Viking Age: The Vocabulary of Runic Inscriptions and Skaldic Verse*. Woodbridge: Boydell.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Larsson, M. G. 1990. *Runstenar och utlandsfärder. Aspekter på det senvikingatida samhället med utgångspunkt i de fasta fornlämningarna*. Acta Archaeologica Lundensia, Series in 8°, 18. Stockholm: Almqvist & Wiksell.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Sukhino-Khomenko, D. 2024. *Thegns Around the North Sea*. Doktorsavhandling. Göteborg: Göteborgs universitet.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2 uppl. Boca Raton: Chapman & Hall/CRC.

:::box Det viktigaste i korthet
- De som dog i öster och väster var oftare söner och bröder än fäder och makar – tre till fyra gånger så ofta, och skillnaden tål varje kontroll vi har.
- Bara fyra av 69 stenar efter män som dog borta är resta av en hustru: de flesta hade ännu ingen egen familj som minnades dem.
- Utlandsfärderna var en livsfas för de unga männen i familjen, inte familjefädernas sak.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, journeys abroad, kinship, life stage, drengr, þegn, logistic regression, pre-registration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** The runestones for men who died in the east and the west are among the best known, and the words for the dead – *drengr* and *þegn* – have been read as words for young and older men respectively. The question here is whether those who died outside Scandinavia were more often sons and brothers than fathers and husbands, with time, province and carver held constant.
**Material.** {en_n(M['n'])} legible Swedish Viking-Age runestones on which all the dead are men and the dead man is either a son or brother (a younger place in the family) or a father or husband (an older place), from the Scandinavian Runic-text Database (Rundata): {RAW['y_n']} and {RAW['o_n']} stones respectively.
**Method.** Pre-registered logistic regression with family place, region and dating period as explanatory variables and the carver as a random effect; Holm correction over the study's six tests; internal replication in two pre-defined halves; eight sensitivity analyses; adjustment for all {N_SHOWN} associations the project reports.
**Results.** The stone says the dead man died outside Scandinavia on {100 * SH_Y:.1f} percent of the stones for sons and brothers against {100 * SH_O:.1f} percent for fathers and husbands; odds ratio {M['or']:.2f} (95 % interval {M['lo']:.2f}–{M['hi']:.2f}), {pfmt(M['p'], True)}, Holm-corrected {pfmt(M['p_holm'], True)}. Same direction and significant in both halves, and every sensitivity analysis holds, also without one province at a time; adjusted for all associations q < 0.001. Of all {WIDOW['n']} stones for men who died abroad, only {WIDOW['make']} were raised by a wife.
**Conclusion.** The journeys east and west belonged first of all to the young men of a family, not to its fathers. That supports the reading of *drengr* as a word for the young man, but speaks of a stage of life and not of an exact age.

## 1. Introduction

Runestones for men who died abroad are among the most studied. Mats G. Larsson (1990) went through the stones about journeys abroad and what they say about the society behind them. Judith Jesch (2001) examined the vocabulary of runic inscriptions and skaldic verse on journeys and retinues, among them the words *drengr* and *þegn*. Lauren Goetting (2006) argued that *drengr* was used chiefly of young men in a warrior retinue and *þegn* of older, established men, and Denis Sukhino-Khomenko (2024) followed *þegn* around the North Sea. None of them measured whether the man who died abroad was more often a young man in his family than an older one, with time, district and carver held constant.

The aim of this study is to test that, with the family place as the measure: a son or brother stands in a younger place in the family than a father or husband. That is not the same as age, but it is the nearest measure the inscriptions themselves give.

## 2. Pre-registration: hypothesis and plan

The hypothesis, the model and the rules of interpretation were written down in an analysis plan on 28 October 2026, before any model had been run. The plan concerned a study of who raised the runestones and for whom, with six tests; this is test 5. The plan is time-stamped in the project's version control and has the SHA-256 checksum `{PLAN_SHA[:16]}…` (see Data and code).

The test reads in the plan: the outcome is that the stone says the dead man died outside Scandinavia, among stones where the message can be read; the dead man is *young* in the family when he is a child or sibling of the sponsor and neither parent nor spouse, and *older* when he is a parent or spouse and neither child nor sibling; only stones on which all the dead are men; the model is outcome ~ young + region + dating period + carver as a random effect. The six tests are corrected together by Holm's method. A test *confirms* when Holm p is below 0.05 and the direction is the same with p below 0.05 in each of the material's two halves; a *pattern to test* has Holm p below 0.05 but does not hold in both halves.

Before the plan was locked no count of death abroad by family place had been made. For tests 3 and 4 on *drengr* and *þegn*, however, I had seen a rough count without a model: *drengr* on 8 percent of the stones for sons and brothers against 0.4 percent for fathers, and *þegn* the other way round. The plan says so. Tests 3 and 4 are therefore reported in section 5.5 as complementary, not as main results.

Sections 5.1–5.3 are the analyses the plan prescribes for test 5. Section 5.4 is descriptive counts on the same selection, made after the test. No other analyses are included.

## 3. Material

- **Source.** The Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University: transliteration, normalisation, English translation, province, parish, carver and style group for each inscription. The material was frozen for the analysis on 29 October 2026.
- **The stones.** Viking-Age runestones in the Swedish provinces: {en_n(PE['n_stones'])} stones. Runestones only; other objects with runes are not included. Skåne and Blekinge are counted as Denmark in Rundata and are not included.
- **Selection.** Stones whose text is preserved well enough for the dead man and his relation to the sponsor to be read, on which all the dead are men, and on which the dead man is either young or older in the family by the plan: {RAW['y_n']} stones for sons and brothers and {RAW['o_n']} for fathers and husbands, {en_n(M['n'])} in all.
- **The family place.** The relation is read from Rundata's English translation by rules (son, brother, father, husband and their forms). The rules were checked against hand coding on a new sample of 40 stones they had never seen: the relation was right on 38 of 40.
- **The outcome** is that the stone says the dead man died outside Scandinavia: a word for death or a manner of dying near a place outside Scandinavia (east, west, Greece, England, Serkland, Ingvar's expedition and others). Having merely travelled does not count, nor dying on a journey at home. The rule was checked against hand coding of {ROB['facit']['messages']['dod_borta']['n']} stones: the rule's yes was right {CO['ppv'][0]} times of {CO['ppv'][0]} and its no {CO['npv'][0]} times of {CO['npv'][0]}.
- **Region** by today's provinces (Svealand, Götaland, Gotland, Norrland) and **dating period** by the stone's ornamental style (Gräslund 2006): before 1010, 1010–1040, 1040–1070, after 1070, and undated as a group of its own.
- **The carver.** The carver Rundata gives. Stones without a known carver are grouped by parish.

## 4. Method

**4.1 The model.** Logistic regression with the R package mgcv (R {DONE['r_version'].split()[2]}; Wood 2017): the outcome against family place, region and dating period, with the carver as a random effect, so that a prolific carver's way of wording the stones is not counted as a pattern. The shares are the model's marginal effects.

**4.2 Correction and replication.** Holm correction (Holm 1979) over the study's six tests. Internal replication: the material was divided once, for all the project's analyses, into two halves parish by parish, and the test must hold in each half on its own. The plan's robustness checks: only stones with at least ten legible words, the model without the carver effect, Uppland only, and only sons against only fathers.

**4.3 Sensitivity analyses.** The same fixed series as for every association the project reports: the raw model; adjusted for province and dating period; the carver as a random effect; the parish as a random effect; the stone's location as a spatial surface (only stones that stand in place); each half on its own; and without one province at a time (provinces with at least {ROB['min_province']} stones). An analysis holds when p is below {ROB['alpha']} and the direction is the same as in the adjusted model; without a province, significance is required only where at least two thirds of the stones remain. The p-values are also adjusted together for all {N_SHOWN} associations reported (Benjamini & Hochberg 1995); the adjusted value is called q. The model's assumptions are checked with simulated residuals (DHARMa; Hartig 2022). The errors in the outcome rule are tested by {CO['n_sim']} refits in which each stone's ”true” outcome is drawn from the hand-coded sample's hit rates.

**4.4 Deviations from the plan.** None. The plan's check ”sex determined for every sponsor” applies only to the tests about the sponsors and is not made here.

## 5. Results

**5.1 The main test.** Raw, the stone says the dead man died outside Scandinavia on {RAW['y_k']} of {RAW['y_n']} stones for sons and brothers ({100 * RAW['y_k'] / RAW['y_n']:.1f} percent) and on {RAW['o_k']} of {RAW['o_n']} for fathers and husbands ({100 * RAW['o_k'] / RAW['o_n']:.1f} percent). With time, region and carver constant the shares are {100 * SH_Y:.1f} against {100 * SH_O:.1f} percent. The odds ratio is {M['or']:.2f} (95 % interval {M['lo']:.2f}–{M['hi']:.2f}), {pfmt(M['p'], True)}, Holm-corrected {pfmt(M['p_holm'], True)}. In plain words: on a stone for a son or brother it is three to four times as common that the dead man died abroad as on a stone for a father or husband. Half A: {HA['n']} stones, odds ratio {HA['or']:.2f} ({HA['lo']:.2f}–{HA['hi']:.2f}), {pfmt(HA['p'], True)}. Half B: {HB['n']} stones, odds ratio {HB['or']:.2f} ({HB['lo']:.2f}–{HB['hi']:.2f}), {pfmt(HB['p'], True)}. The test *confirms* by the plan's rule.

{chart(False)}

**5.2 The plan's robustness checks.**

- Only stones with at least ten legible words: {RO['ord10']['n']} stones, odds ratio {RO['ord10']['or']:.2f}, {pfmt(RO['ord10']['p'], True)}.
- Without the carver effect: odds ratio {RO['utan_ristare']['or']:.2f}, {pfmt(RO['utan_ristare']['p'], True)}.
- Uppland only: {RO['uppland']['n']} stones, odds ratio {RO['uppland']['or']:.2f}, {pfmt(RO['uppland']['p'], True)}.
- Only sons against only fathers: {RO['son_far']['n']} stones, odds ratio {RO['son_far']['or']:.2f}, {pfmt(RO['son_far']['p'], True)}. Raw {SONS[0]} of {SONS[1]} against {FATHERS[0]} of {FATHERS[1]}.

**5.3 The sensitivity analyses** ({M['n']} stones, {M['k']} with the outcome). All {ME['ladder']['tested']} hold:

- Raw model: odds ratio {RU['raw']['or']:.2f} ({RU['raw']['ci'][0]:.2f}–{RU['raw']['ci'][1]:.2f}), {pfmt(RU['raw']['p'], True)}.
- Adjusted for province and dating period: {RU['adjusted']['or']:.2f} ({RU['adjusted']['ci'][0]:.2f}–{RU['adjusted']['ci'][1]:.2f}), {pfmt(RU['adjusted']['p'], True)}.
- Carver as a random effect ({RU['carver']['groups']} carvers and parish groups): {RU['carver']['or']:.2f} ({RU['carver']['ci'][0]:.2f}–{RU['carver']['ci'][1]:.2f}), {pfmt(RU['carver']['p'], True)}.
- Parish as a random effect ({RU['parish']['groups']} parishes): {RU['parish']['or']:.2f} ({RU['parish']['ci'][0]:.2f}–{RU['parish']['ci'][1]:.2f}), {pfmt(RU['parish']['p'], True)}.
- The stone's location as a spatial surface ({RU['place']['n']} stones that stand in place): {RU['place']['or']:.2f} ({RU['place']['ci'][0]:.2f}–{RU['place']['ci'][1]:.2f}), {pfmt(RU['place']['p'], True)}. The difference is smaller here, but it remains when the district is held constant.
- Half A ({RU['half_A']['n']} stones): {RU['half_A']['or']:.2f}, {pfmt(RU['half_A']['p'], True)}. Half B ({RU['half_B']['n']} stones): {RU['half_B']['or']:.2f}, {pfmt(RU['half_B']['p'], True)}.
- Without one province at a time ({LO['n_provinces']} provinces tested): the direction holds without each of them and is significant everywhere. Weakest without Uppland, when {LO['n']} stones remain: odds ratio {LO['or']:.2f} ({LO['ci'][0]:.2f}–{LO['ci'][1]:.2f}), {pfmt(LO['p'], True)}.
- The difference in percentage points in the adjusted model: {100 * EF['share_hi']:.1f} against {100 * EF['share_lo']:.1f} percent, {100 * EF['diff']:.1f} points (probably between {100 * EF['diff_ci'][0]:.1f} and {100 * EF['diff_ci'][1]:.1f}).
- The model's assumptions: residual distribution p = {CK['uniformity_p']:.2f}, remaining spatial pattern p = {CK['spatial_p']:.2f}, but overdispersion p = {CK['dispersion_p']:.3f}: the model does not capture all the variation between the stones, so the intervals are probably somewhat too narrow (see 6).
- Errors in the outcome rule: the association holds in {pc(CO['share_holds'])} percent of the {CO['n_sim']} refits; median odds ratio {CO['or_median']:.2f}, range {CO['or_range'][0]:.2f}–{CO['or_range'][1]:.2f}.
- Adjusted for all {N_SHOWN} associations the project reports: q < 0.001. The association is one of {N_ALLRUNG} that hold in every sensitivity analysis.

**5.4 Who they were (descriptive, same selection).** Of the {RAW['y_k']} sons and brothers who died outside Scandinavia, {WHO['barn']} were sons and {WHO['syskon']} brothers. On {WHO['kvinna']} of the stones a woman stands among the sponsors, and all {WHO['moder']} are mothers commemorating their sons. Of all {WIDOW['n']} stones for men who died outside Scandinavia, whatever their relation to the sponsor, only {WIDOW['make']} were raised by a wife. The difference is present in both large regions: in Svealand {REG['Svealand'][0][0]} of {REG['Svealand'][0][1]} for sons and brothers against {REG['Svealand'][1][0]} of {REG['Svealand'][1][1]} for fathers and husbands, in Götaland {REG['Götaland'][0][0]} of {REG['Götaland'][0][1]} against {REG['Götaland'][1][0]} of {REG['Götaland'][1][1]}.

**5.5 The words for the dead (the plan's tests 3 and 4).** *drengr* is said of the dead man on {RAW['y_dr']} of {RAW['y_n']} stones for sons and brothers against {RAW['o_dr']} of {RAW['o_n']} for fathers and husbands: odds ratio {DRM['or']:.1f}, Holm-corrected {pfmt(DRM['p_holm'], True)}, but too few cases in half B to test there. *þegn* stands on {RAW['y_th']} of {RAW['y_n']} against {RAW['o_th']} of {RAW['o_n']}: odds ratio {THM['or']:.2f}, Holm-corrected {pfmt(THM['p_holm'], True)}, but not significant in either half. Both are *patterns to test* by the plan's rule, and for both a rough count was seen before locking.

## 6. Discussion

**What the finding says.** The men whose runestones say they died in the east or the west were more often sons and brothers than fathers and husbands. The difference is large, three to four times, and it remains with time, province and carver constant, in each half, in every province and with the district held constant. Only four of the {WIDOW['n']} stones for men who died abroad were raised by a wife. The journeys seem to have belonged to a stage of life: the time before the man had a family of his own to raise the stone for him.

**Against earlier research.** The result gives a measure to the reading of the words for the dead that Goetting (2006) argued for: *drengr* for young men, *þegn* for older ones. Here both words follow the family place in the same direction as death abroad, but only as patterns to test. The finding on death abroad rests not on the words but on the relation, and so it is independent support for the journeys abroad having been chiefly a matter for young men (cf. Jesch 2001; Larsson 1990).

**Weaknesses, in order of weight.**

1. **Family place is not age.** A son may be middle-aged, a brother may be older than the sponsor. The measure says that the dead man was not yet the one whom others commemorated as father or husband, not how old he was.
2. **Who raises the stone and what is written go together.** A father who died abroad may have been commemorated by sons who worded the stone differently, without a place for the death. The finding concerns what the stones say, and it may partly be a difference in how different sponsors phrased themselves.
3. **Overdispersion.** The model check shows more variation between the stones than the model allows for (p = {CK['dispersion_p']:.3f}). The odds ratio is hardly affected, but the intervals are probably somewhat too narrow. With {M['k']} stones with the outcome they are already wide.
4. **The relation is read by rules.** The rules had 38 right of 40 on a new sample. Errors in the relation are not part of the refits, only errors in the outcome.

**What would overturn the finding.** A test in which the sponsor is held constant – for example only stones a parent raises for a son compared with stones a son raises for a parent – in which the difference disappeared, or a hand coding of the relation showing more errors among the stones about death abroad.

## 7. Conclusion

On the runestones for sons and brothers it says more often that the dead man died outside Scandinavia than on the stones for fathers and husbands, {100 * SH_Y:.1f} against {100 * SH_O:.1f} percent with time, province and carver constant, and the difference withstands every sensitivity analysis. The journeys abroad belonged chiefly to the young men of the family. The next step is to hold the sponsor constant and to test the words for the dead on a larger material.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 31 October 2026. No release with a DOI exists yet; when one is made, the report will refer to it. All code, the analysis plan and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The analysis plan: `analysplaner/2026-10-28-manniskorna.md`, with its checksum in the `.sha256` file beside it.
- The family place and the sponsors: `src/people.py`; the hand coding: `data/people_check.json`.
- The outcome: `src/messages.py` (death outside Scandinavia); the hand coding: `data/messages_facit_ost.csv` and `utdata/brittiska/hemma_kodning.csv`.
- The model: `r/people.R`. The sensitivity analyses: `r/robustness.R` and `src/robustness.py` (method description in `METHODS.md`, sections 1u and 1v). The results are saved under the material's version `{FP}`.
- The report is built by `utdata/blogg/build/build_rapport_unga.py`, which computes the descriptive counts, reads the rest from the result files and stops if anything disagrees.
- In Vitki the association is shown under Statistics, The people, with the sensitivity analyses step by step. Popular account: [The journeys belonged to the young](/en/artiklar/fardena-var-de-ungas).

## References

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), pp. 289–300.
- Goetting, L. 2006. Þegn and drengr in the Viking Age. *Scandinavian Studies* 78 (4), pp. 375–404.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R package.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Jesch, J. 2001. *Ships and Men in the Late Viking Age: The Vocabulary of Runic Inscriptions and Skaldic Verse*. Woodbridge: Boydell.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Larsson, M. G. 1990. *Runstenar och utlandsfärder. Aspekter på det senvikingatida samhället med utgångspunkt i de fasta fornlämningarna*. Acta Archaeologica Lundensia, Series in 8°, 18. Stockholm: Almqvist & Wiksell.
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Sukhino-Khomenko, D. 2024. *Thegns Around the North Sea*. Doctoral thesis. Gothenburg: University of Gothenburg.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2nd ed. Boca Raton: Chapman & Hall/CRC.

:::box The essentials
- Those who died in the east and the west were more often sons and brothers than fathers and husbands – three to four times as often, and the difference withstands every check we have.
- Only four of 69 stones for men who died abroad were raised by a wife: most had no family of their own yet to commemorate them.
- The journeys abroad were a stage of life for the young men of the family, not a matter for the fathers.
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

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Kvinnor och barn", "Geografi"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_unga.json")
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
                 "topic": "Rapport|dod_borta_ung", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
