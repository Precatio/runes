"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 2; Fullt prövat fynd): "Monoftongstavningen blir
ovanligare på runstenarna – från 69 till 22 procent mellan omkring år 1000 och 1115" (sv + en). Mönstret
Förändring|ai_alla i projektets genomgång av hur 14 drag förändras över tid (r/change.R), robusthetsstegen
(src/robustness.py, METHODS 1v), mätkontrollerna i r/change.R (ai_checks) och kodningskontrollen i utdata/monoftong/.
Inte förregistrerat. Alla siffror asserteras mot korpusjobbets filer (data/cache/r/corpus/<FP>/) och räknas om ur
corpus.csv där de är beskrivande.
    ../../../.venv/bin/python build_rapport_monoftong.py [--write | --update DOC]"""
import datetime as dt
import json
import math
import os
import re
import sys

import pandas as pd
from scipy.stats import fisher_exact

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
MALL_SHA = open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().split()[0]
assert MALL_SHA.startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 1
TODAY = "2026-10-31"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = "mönstret upptäcktes och mätkontrollerna lades till 2026-10-11; materialet frystes 2026-10-29; kodningen kontrollerades 2026-10-31"
TL_EN = "the pattern was found and the checks of the measurement were added 2026-10-11; the material was frozen 2026-10-29; the coding was checked 2026-10-31"
CH = json.load(open(os.path.join(C, "change.json"), encoding="utf-8"))
ROB = json.load(open(os.path.join(C, "robustness.json"), encoding="utf-8"))
MD = os.path.join(ROOT, "utdata", "monoftong")
KOD = json.load(open(os.path.join(MD, "kodning.json"), encoding="utf-8"))
KM = json.load(open(os.path.join(MD, "kodning_modeller.json"), encoding="utf-8"))

pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731
d1 = lambda x: f"{x:.1f}".replace(".", ",")  # noqa: E731
d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_n = lambda n: f"{n:,}"  # noqa: E731
orb = lambda b: math.exp(b)  # noqa: E731  log-oddset per 50 år som oddskvot


def pfmt(p, en=False):
    if p < 0.001:
        return "p < 0.001" if en else "p < 0,001"
    s = f"{p:.3f}" if p < 0.1 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the main test: the change over time (r/change.R) -----------------------------------------------------------------
assert CH["n_stones"] == 2318 and CH["draws"] == 10
FEAT = {f["key"]: f for f in CH["features"]}
N_TIME = sum(1 for f in CH["features"] if f.get("time", {}).get("tested"))
assert N_TIME == 14
F = FEAT["ai_alla"]
T = F["time"]
assert (F["n"], T["n"], T["n_yes"], T["shape"]) == (1091, 649, 363, "falls")
assert (T["year_first"], T["year_last"]) == (998, 1115)
assert (pc(T["first"]), pc(T["last"])) == (69, 22) and (pc(-T["change"]), pc(-T["change_lo"]), pc(-T["change_hi"])) == (48, 66, 22)
assert 0.004 < T["p"] < 0.005 and 0.028 < T["q"] < 0.029
HA, HB = T["halves"]["A"], T["halves"]["B"]
assert T["halves"]["replicated"] and (HA["n"], HB["n"]) == (343, 306) and 0.04 < HA["p"] < 0.05 and 0.01 < HB["p"] < 0.02
assert (pc(HA["first"]), pc(HA["last"]), pc(HB["first"]), pc(HB["last"])) == (70, 24, 69, 33)
DR = T["draws"]
assert (DR["n"], DR["share_sig"], DR["share_same_shape"]) == (10, 0.9, 1) and (pc(-DR["change_max"]), pc(-DR["change_min"])) == (22, 33)
CURVE = {c["year"]: c for c in T["curve"]}
assert (pc(CURVE[1028]["share"]), pc(CURVE[1068]["share"])) == (58, 55)
BS = {b["style"]: b for b in T["by_style"]}
STYLES = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
assert [BS[s]["n"] for s in STYLES] == [148, 123, 44, 72, 90, 152, 20]
assert [d1(100 * BS[s]["share"]) for s in STYLES] == ["81,1", "53,7", "65,9", "40,3", "47,8", "48,7", "10,0"]
assert [BS[s]["year"] for s in STYLES] == [998, 1030, 1030, 1035, 1065, 1085, 1115]

# ---- the regional level (same analysis) -------------------------------------------------------------------------------
PR = {r["province"]: r for r in F["provinces"]["rows"]}
assert [pc(PR[p]["share1050"]) for p in ("Vg", "Ög", "U", "Sö")] == [84, 80, 55, 35] and F["provinces"]["p_differ"] < 1e-5

# ---- the twelve checks of the measurement (r/change.R, ai_checks) ------------------------------------------------------
AR = CH["ai_robustness"]
assert (AR["n_stones"], AR["n_words"], pc(AR["share_sten"])) == (649, 1278, 48)
K = AR["checks"]
assert len(K) == 12 and all(k["tested"] for k in K.values())
assert all(k["b"] < 0 for k in K.values())
SIG = [k for k, v in K.items() if v["p"] < 0.05]
assert sorted(set(K) - set(SIG)) == ["signed", "trimmed", "within"]
assert (K["word"]["n"], K["sten"]["n"], K["other"]["n"], K["attributed"]["n"], K["unattributed"]["n"], K["signed"]["n"],
        K["within"]["n"], K["within"]["carvers"], K["trimmed"]["n"], K["uppland"]["n"], K["sodermanland"]["n"]) == \
    (649, 569, 531, 270, 379, 106, 174, 11, 481, 348, 113)
assert [d2(orb(K[k]["b"])) for k in ("stone", "word", "sten", "other", "attributed", "unattributed", "signed", "no_carver",
                                     "within", "trimmed", "uppland", "sodermanland")] == \
    ["0,55", "0,54", "0,59", "0,64", "0,46", "0,55", "0,91", "0,54", "0,50", "0,67", "0,42", "0,31"]
BSW = {b["style"]: b for b in AR["by_style"]}
assert [d1(100 * BSW[s]["mono_i"]) for s in STYLES] == ["63,1", "39,8", "56,0", "30,4", "29,6", "31,2", "3,3"]
assert [d1(100 * BSW[s]["mono_e"]) for s in STYLES] == ["7,3", "4,1", "4,4", "2,0", "3,5", "9,9", "3,3"]
assert [BSW[s]["words"] for s in STYLES] == [301, 246, 91, 148, 199, 263, 30]


def kline(key, sv=True):
    k = K[key]
    o, lo, hi = orb(k["b"]), orb(k["lo"]), orb(k["hi"])
    if sv:
        return f"oddskvot per 50 år {d2(o)} ({d2(lo)}–{d2(hi)}), {pfmt(k['p'])}"
    return f"odds ratio per 50 years {o:.2f} ({lo:.2f}–{hi:.2f}), {pfmt(k['p'], True)}"


# ---- the robustness ladder (src/robustness.py, METHODS 1v) ------------------------------------------------------------
P = ROB["patterns"]["Förändring|ai_alla"]
SPEC = ROB["specs"]["Förändring|ai_alla"]
RU = P["rungs"]
assert (P["n"], P["k"], P["direction"]) == (649, 363, -1) and set(RU) == {"raw", "adjusted", "carver", "parish", "place", "half_A", "half_B", "lopo"}
assert all(r["holds"] for r in RU.values()) and SPEC["adjust"] == ["province"] and (SPEC["x_lo"], SPEC["x_hi"]) == (-1, 1)
assert [d2(RU[k]["or"]) for k in ("raw", "adjusted", "carver", "parish", "place", "half_A", "half_B", "lopo")] == \
    ["0,44", "0,55", "0,52", "0,49", "0,54", "0,60", "0,49", "0,53"]
assert (RU["carver"]["groups"], RU["parish"]["groups"], RU["place"]["n"], RU["half_A"]["n"], RU["half_B"]["n"]) == (315, 326, 390, 340, 309)
LO = RU["lopo"]
assert (LO["without"], LO["n"], LO["n_provinces"], LO["all_hold"], LO["flips"]) == ("U", 301, 4, True, []) and 0.11 < LO["p"] < 0.12
EF, CK = P["effect"], P["check"]
assert (pc(EF["share_lo"]), pc(EF["share_hi"]), pc(-EF["diff"]), pc(-EF["diff_ci"][1]), pc(-EF["diff_ci"][0])) == (68, 42, 25, 12, 39)
assert CK["ok"] is True and CK["uniformity_p"] > 0.2 and CK["dispersion_p"] > 0.2 and CK["spatial_p"] > 0.2
ANN = robustness.annotate(r_findings.corpus_patterns(rb.JOB.result(FP)), robustness.load(FP))
ME = next(q for q in ANN if q["key"] == "ai_alla" and q["topic"] == "Förändring")
SUMM = robustness.summary(ANN)
N_SHOWN, N_ALLRUNG = SUMM["n_fdr"], SUMM["all_rungs"]
assert ME["confirmed"] is True and ME["ladder"]["passed"] == ME["ladder"]["tested"] == 8 and ME["q_global"] < 0.001
assert (N_SHOWN, N_ALLRUNG) == (48, 15)

# ---- the coding check (utdata/monoftong/kodning.py, kodning.R) ---------------------------------------------------------
assert (KOD["n_stones"], KOD["n_words"], KOD["rule_mono_words"], KOD["rule_mono_to_uncertain"]) == (649, 1278, 599, 79)
assert KOD["strict"] == {"diftong": 679, "monoftong": 520, "osäkert": 79} and (KOD["stones_changed"], KOD["stones_dropped"]) == (28, 16)
assert list(KOD["uncertain_examples"])[:3] == ["stan", "rasa", "þaR"]
KR, KS = KM["y_rule"], KM["y_strict"]
assert d2(KR["raw"]["or"]) == "0,44" and KR["raw"]["n"] == 649 and KS["raw"]["n"] == 633
assert [d2(KS[k]["or"]) for k in ("raw", "adjusted", "half_A", "half_B", "uppland")] == ["0,41", "0,53", "0,57", "0,46", "0,58"]
assert all(KS[k]["p"] < 0.01 for k in ("raw", "adjusted", "half_A", "half_B", "uppland"))
assert [d2(KR[k]["or"]) for k in ("adjusted", "half_A", "half_B", "uppland")] == ["0,54", "0,57", "0,47", "0,55"]

# ---- the ends and the carvers (descriptive, exploratory; corpus.csv) ---------------------------------------------------
c = pd.read_csv(os.path.join(C, "corpus.csv"), low_memory=False)
d = c[c.trait_ai_alla.notna() & c.style_from.notna() & c.style_to.notna()].copy()
assert len(d) == 649
d["mono"] = d.trait_ai_alla.isin(["monoftong", "båda"]).astype(int)
u = d[d.province == "U"]
U_ST = {s: (int(u[u["style"] == s].mono.sum()), int((u["style"] == s).sum())) for s in STYLES}
assert U_ST == {"RAK": (19, 23), "Fp": (20, 37), "Pr1": (16, 25), "Pr2": (13, 38), "Pr3": (39, 69), "Pr4": (67, 136), "Pr5": (2, 20)}, U_ST
U_RAK_GUNNAR = int((u[u["style"] == "RAK"].carver == "Gunnar").sum())
U_PR5_OPIR = int((u[u["style"] == "Pr5"].carver == "Öpir 1").sum())
assert (U_RAK_GUNNAR, U_PR5_OPIR) == (16, 16)
op = d[(d.carver == "Öpir 1") & (d.carvers_uncertain == 0)]
OP = {s: (int(op[op["style"] == s].mono.sum()), int((op["style"] == s).sum())) for s in ("Pr4", "Pr5")}
assert OP == {"Pr4": (11, 21), "Pr5": (1, 16)}, OP
OP_P = fisher_exact([[OP["Pr4"][0], OP["Pr4"][1] - OP["Pr4"][0]], [OP["Pr5"][0], OP["Pr5"][1] - OP["Pr5"][0]]]).pvalue
assert 0.004 < OP_P < 0.005
gu = d[(d.carver == "Gunnar") & (d.carvers_uncertain == 0)]
GU = (int(gu.mono.sum()), len(gu))
assert GU == (19, 20), GU

SLUG = "monoftongstavningen-blir-ovanligare"
title = "Monoftongstavningen blir ovanligare på runstenarna – från 69 till 22 procent mellan omkring år 1000 och 1115"
title_en = "Monophthong spellings become rarer on the runestones – from 69 to 22 percent between about 1000 and 1115"
summary = ("Stavningen stin i stället för stain har använts för att datera när monoftongeringen nådde Sverige. Men på "
           "runstenarna blir monoftongstavningen ovanligare med tiden, inte vanligare: från 69 till 22 procent av stenarna, "
           "med plats och ristare konstanta, i båda halvorna av materialet och i alla känslighetsanalyser. Den sena "
           "uppländska stavningen ser ut som en skriftnorm, inte som uttalet.")
summary_en = ("The spelling stin instead of stain has been used to date when the monophthongisation reached Sweden. But on the "
              "runestones the monophthong spelling becomes rarer over time, not more common: from 69 to 22 percent of the "
              "stones, with place and carver constant, in both halves of the material and in every sensitivity analysis. "
              "The late Upplandic spelling looks like a written norm, not like the pronunciation.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/forskningsrapporter/{SLUG}")


def chart(sv):
    rows = [":::chart Stenar med monoftongstavning, andel per stilgrupp" if sv else
            ":::chart Stones with a monophthong spelling, share by style group",
            "# " + ("Alla landskap" if sv else "All provinces")]
    for s in STYLES:
        v = 100 * BS[s]["share"]
        rows.append(f"{s} {BS[s]['year']} | {d1(v) if sv else f'{v:.1f}'} | {BS[s]['n']} {'stenar' if sv else 'stones'}")
    rows.append("# " + ("Bara Uppland" if sv else "Uppland only"))
    for s in STYLES:
        k, n = U_ST[s]
        v = 100 * k / n
        rows.append(f"{s} {BS[s]['year']} | {d1(v) if sv else f'{v:.1f}'} | {k} {'av' if sv else 'of'} {n}")
    rows.append("Källa: Rundata. Rå andel stenar med minst ett æi-ord skrivet med monoftong; stilgruppens mittår efter Gräslund (2006)."
                if sv else "Source: Rundata. Raw share of stones with at least one æi word spelled with a monophthong; style group midpoint after Gräslund (2006).")
    rows.append(":::")
    return "\n".join(rows)


body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, runsvenska, monoftongering, stavning, skriftnorm, ristare, stilkronologi, logistisk regression. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Den östnordiska monoftongeringen, där diftongen æi blev ē (*stæinn* > *stēn*), har daterats med hjälp av runstenarnas stavning: när ristaren skriver *stin* i stället för *stain* har det lästs som att ljudbytet hade nått bygden. Enligt den dateringen borde monoftongstavningen bli vanligare i Mälardalen under 1000-talet. Frågan här är hur andelen faktiskt förändras över tid, med plats och ristare konstanta.
**Material.** {sp(T['n'])} daterade svenska runstenar från vikingatiden med minst ett ord som har æi i Samnordisk runtextdatabas (Rundata), sammanlagt {sp(AR['n_words'])} sådana ord.
**Metod.** Logistisk regression med stilgruppens mittår som tid, stenens läge som rumslig utjämning och ristaren som slumpeffekt; Holm-korrigering över de {N_TIME} drag vars förändring prövades på samma sätt; intern replikering i två halvor; åtta känslighetsanalyser; tolv kontroller av mätningen och en kontroll av kodningen; justering för alla {N_SHOWN} samband som projektet redovisar.
**Resultat.** Andelen stenar med monoftongstavning sjunker från {pc(T['first'])} procent omkring år {T['year_first']} till {pc(T['last'])} procent omkring {T['year_last']}, en förändring på {pc(-T['change'])} procentenheter (95 %-intervall {pc(-T['change_hi'])}–{pc(-T['change_lo'])}), {pfmt(T['p'])}, Holm-korrigerat {pfmt(T['q'])}. Samma riktning och signifikant i båda halvorna; alla känslighetsanalyser håller; justerat för alla samband q < 0,001. Nedgången syns också ord för ord och i både Uppland och Södermanland. Den ligger i periodens början och slut: mellan omkring 1030 och 1070 står andelen nästan still, och utan den tidigaste och den senaste stilgruppen är trenden inte signifikant. I Uppland är ändarna i hög grad två ristare, Gunnar och Öpir.
**Slutsats.** Stavningen gick åt motsatt håll mot den ljudutveckling den har använts för att datera. Den sena uppländska stavningen *stain* speglar troligen en skriftnorm och inte uttalet, och runstenarnas stavning i Mälardalen kan därför inte ensam visa när monoftongeringen nådde dit.

## 1. Inledning

Det råder enighet om att den östnordiska monoftongeringen, där diftongerna æi, au och øy blev långa monoftonger, började i Danmark under 900-talet, och beviset är stavningen i runinskrifterna: digraferna ersätts av en enda runa, så att *stain* blir *stin* (Marklund 2018, s. 12, med litteratur). Elias Wessén antog utifrån runstenarnas stavning att ljudbytet nådde Östergötland och Västergötland omkring år 1000 och Mellansverige mot slutet av 1000-talet (Wessén 1968, s. 32 f., efter Marklund 2018, s. 12). Magnus Källström (2014) har läst stavningen *sten*, med stungen i-runa, som tecken på att æi hade blivit [e:] i Västmanland, kring Uppsala, i västra Uppland och på två platser i Södermanland, och han ställer frågan som en fråga om skriftnorm och dialekt (efter Marklund 2018, s. 13). Att ristarna stavade olika och att stavningen kan användas för att skilja dem åt är känt sedan länge (Thompson 1975).

Vi har inte funnit någon studie som mäter hur andelen monoftongstavningar förändras över tid när plats och ristare hålls konstanta. Om stavningen följde uttalet, borde andelen öka i Mälardalen under 1000-talet. Syftet här är att mäta förändringen och pröva om den håller.

## 2. Förregistrering: vad som var bestämt i förväg och vad som är explorativt

Ingen analysplan låstes för den här frågan innan resultaten var kända. Fyndet är alltså inte förregistrerat, och det ska läsas som upptäckt i en systematisk genomgång.

Genomgången var en allmän metod som tillämpades på en gång på {N_TIME} drag i runstenarnas stavning och innehåll: samma modell, samma tidsmått, samma korrigering över dragen och samma indelning av materialet i två halvor för alla drag, bestämda i programkoden innan genomgången kördes. Draget i den här rapporten lades till i genomgången den 11 oktober 2026. Samma dag, efter att mönstret hade visats, lades tolv kontroller av mätningen till för att pröva de invändningar en runolog rimligen skulle resa; alla redovisas i avsnitt 5.4, också de som inte håller.

p-värdet är korrigerat för de {N_TIME} drag som prövades och för alla {N_SHOWN} samband som projektet redovisar, och halvorna bestämdes oberoende av mönstren. Avsnitt 5.5 om ristarna och stavningssätten är explorativt: det räknades efter att mönstret var känt och redovisas med p-värden som inte är justerade. Kontrollen av kodningen i 5.4 gjordes den 31 oktober 2026, när rapporten skrevs.

## 3. Material

- **Källa.** Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk vid Uppsala universitet: translitterering, normalisering, landskap, socken, ristare och stilgruppering för varje inskrift. Materialet frystes för analysen den 29 oktober 2026.
- **Stenarna.** Vikingatida runstenar i de svenska landskapen. Bara runstenar; andra föremål med runor ingår inte. Skåne och Blekinge förs i Rundata till Danmark och ingår inte.
- **Orden.** Ord med æi i Rundatas normalisering (*ræisa*, *stæinn*, *þæiR*, *bæði* med flera), jämförda ord för ord med translitteringen, bara när de två texterna har lika många ord; egennamn och osäkra läsningar räknas inte. Ett ord är skrivet med *diftong* när translitteringen har ai, ia, ei eller ae, annars med *monoftong*. *stæinn* står för {pc(AR['share_sten'])} procent av de {sp(AR['n_words'])} orden.
- **Draget.** En sten har *monoftongstavning* när minst ett av dess æi-ord är skrivet med monoftong. Draget kan avgöras på {sp(F['n'])} stenar; {sp(T['n'])} av dem är daterade, och {T['n_yes']} har monoftongstavning.
- **Tiden.** Stilgruppens mittår efter Gräslunds ornamentikkronologi (Gräslund 2006): RAK {BS['RAK']['year']}, Fp {BS['Fp']['year']}, Pr1 {BS['Pr1']['year']}, Pr2 {BS['Pr2']['year']}, Pr3 {BS['Pr3']['year']}, Pr4 {BS['Pr4']['year']}, Pr5 {BS['Pr5']['year']}. Stilgrupperna bygger på ornamentiken, inte på stavningen.
- **Ristaren.** Den ristare Rundata anger utan frågetecken. Stenar utan säker ristare grupperas per socken.

## 4. Metod

**4.1 Modellen.** Logistisk regression (R-paketet mgcv, R {DONE['r_version'].split()[2]}; Wood 2017) med draget mot stilgruppens mittår som en utjämnad kurva, stenens läge som rumslig utjämning och ristaren som slumpeffekt, så att en flitig ristares vana inte räknas som en förändring. Kurvan visas som justerad andel för en typisk ristare, med 95 %-intervall ur 300 dragningar av modellens koefficienter. Dateringens osäkerhet prövas genom att dra varje stens årtal jämnt inom stilgruppens intervall, tio gånger.

**4.2 Korrigering och replikering.** Holm-korrigering (Holm 1979) över de {N_TIME} drag vars förändring prövades. Intern replikering: materialet delades en gång, för alla projektets analyser, i två halvor socken för socken, och förändringen ska hålla i var halva för sig.

**4.3 Känslighetsanalyser.** Samma fasta serie som för alla samband projektet redovisar, med tiden i steg om 50 år och oddskvoten för ett sådant steg: rå modell; justerad för landskapet; ristaren som slumpeffekt; socknen som slumpeffekt; stenens läge som rumslig yta (bara stenar som står kvar); var halva för sig; och utan ett landskap i taget (landskap med minst {ROB['min_province']} stenar). En analys håller när p är under {str(ROB['alpha']).replace('.', ',')} och riktningen är densamma som i den justerade modellen; utan ett landskap krävs signifikans bara där minst två tredjedelar av stenarna är kvar. p-värdena justeras dessutom tillsammans för alla {N_SHOWN} samband som redovisas (Benjamini & Hochberg 1995); det justerade värdet kallas q. Modellens antaganden prövas med simulerade residualer (DHARMa; Hartig 2022).

**4.4 Kontroller av mätningen.** Tolv varianter av samma raka trend i tiden, med läget och ristaren som i 4.1 om inte annat sägs (listade i 5.4), och en kontroll av kodningen med en strängare regel.

**4.5 Avvikelser och fel.** Ingen plan fanns, så inga avvikelser från en plan kan redovisas. När rapporten skrevs visade ett slumpvis urval av orden att regeln också räknar ord skrivna med bara a eller utan vokal som monoftong. Resultatet räknades därför om med en strängare kodning (5.4); det ändras inte.

## 5. Resultat

**5.1 Huvudtestet.** Med läge och ristare konstanta sjunker andelen från {pc(T['first'])} procent omkring år {T['year_first']} till {pc(T['last'])} procent omkring {T['year_last']}, en förändring på {pc(-T['change'])} procentenheter (95 %-intervall {pc(-T['change_hi'])}–{pc(-T['change_lo'])}), {pfmt(T['p'])}, Holm-korrigerat {pfmt(T['q'])}. Kurvan sjunker inte jämnt: den går från {pc(T['first'])} till {pc(CURVE[1028]['share'])} procent fram till omkring 1030, ligger nästan still till omkring 1070 ({pc(CURVE[1068]['share'])} procent) och sjunker sedan igen. Halva A: {HA['n']} stenar, från {pc(HA['first'])} till {pc(HA['last'])} procent, {pfmt(HA['p'])}. Halva B: {HB['n']} stenar, från {pc(HB['first'])} till {pc(HB['last'])} procent, {pfmt(HB['p'])}. Förändringen håller alltså i båda halvorna. I klartext: omkring år 1000 hade ungefär sju stenar av tio minst ett ord stavat med monoftong, omkring 1115 ungefär två av tio. Känslighetsanalysernas oddskvot på omkring 0,5 per 50 år betyder att oddsen för monoftongstavning ungefär halveras på femtio år.

{chart(True)}

**5.2 Dateringens osäkerhet.** När varje stens årtal dras inom stilgruppens intervall är förändringen signifikant i {pc(DR['share_sig']) // 10} av {DR['n']} omräkningar och har samma form i alla; den blir då mindre, mellan {pc(-DR['change_max'])} och {pc(-DR['change_min'])} procentenheter.

**5.3 Känslighetsanalyserna** ({P['n']} stenar, {P['k']} med monoftongstavning; tiden i steg om 50 år). Alla {ME['ladder']['tested']} håller:

- Rå modell: oddskvot {d2(RU['raw']['or'])} ({d2(RU['raw']['ci'][0])}–{d2(RU['raw']['ci'][1])}), {pfmt(RU['raw']['p'])}.
- Justerad för landskapet: {d2(RU['adjusted']['or'])} ({d2(RU['adjusted']['ci'][0])}–{d2(RU['adjusted']['ci'][1])}), {pfmt(RU['adjusted']['p'])}. Det motsvarar {pc(EF['share_lo'])} procent år 1000 mot {pc(EF['share_hi'])} procent år 1100 (skillnaden troligen {pc(-EF['diff_ci'][1])}–{pc(-EF['diff_ci'][0])} procentenheter).
- Ristaren som slumpeffekt ({RU['carver']['groups']} ristare och sockengrupper): {d2(RU['carver']['or'])} ({d2(RU['carver']['ci'][0])}–{d2(RU['carver']['ci'][1])}), {pfmt(RU['carver']['p'])}.
- Socknen som slumpeffekt ({RU['parish']['groups']} socknar): {d2(RU['parish']['or'])} ({d2(RU['parish']['ci'][0])}–{d2(RU['parish']['ci'][1])}), {pfmt(RU['parish']['p'])}.
- Stenens läge som rumslig yta ({RU['place']['n']} stenar som står kvar): {d2(RU['place']['or'])} ({d2(RU['place']['ci'][0])}–{d2(RU['place']['ci'][1])}), {pfmt(RU['place']['p'])}.
- Halva A ({RU['half_A']['n']} stenar): {d2(RU['half_A']['or'])}, {pfmt(RU['half_A']['p'])}. Halva B ({RU['half_B']['n']} stenar): {d2(RU['half_B']['or'])}, {pfmt(RU['half_B']['p'])}. Halvorna följer samma regel som i 5.1 men räknas för sig, så att tre stenar hamnar i den andra halvan.
- Utan ett landskap i taget ({LO['n_provinces']} landskap prövade): riktningen håller utan vart och ett. Svagast utan Uppland, då {LO['n']} stenar är kvar, mindre än två tredjedelar: oddskvot {d2(LO['or'])} ({d2(LO['ci'][0])}–{d2(LO['ci'][1])}), {pfmt(LO['p'])}.
- Modellens antaganden: residualernas fördelning p = {d2(CK['uniformity_p'])}, överspridning p = {d2(CK['dispersion_p'])}, kvarvarande rumsligt mönster p = {d2(CK['spatial_p'])}; inga avvikelser.
- Justerat för alla {N_SHOWN} samband som projektet redovisar: q < 0,001. Sambandet är ett av {N_ALLRUNG} som håller i alla känslighetsanalyser.

**5.4 Kontrollerna av mätningen.** Riktningen är densamma i alla tolv; nio är signifikanta och tre inte:

- Per sten: {kline('stone')}. Per ord, så att en sten med många æi-ord inte väger tyngre: {kline('word')}.
- Bara *stæinn*: {kline('sten')} ({K['sten']['n']} stenar). Bara andra æi-ord: {kline('other')} ({K['other']['n']} stenar). Förändringen gäller alltså inte bara ordet för sten.
- Bara stenar med säker ristare: {kline('attributed')} ({K['attributed']['n']} stenar). Bara stenar utan: {kline('unattributed')} ({K['unattributed']['n']} stenar). Utan ristaren i modellen: {kline('no_carver')}.
- Bara Uppland: {kline('uppland')} ({K['uppland']['n']} stenar). Bara Södermanland: {kline('sodermanland')} ({K['sodermanland']['n']} stenar).
- **Inte signifikant:** bara signerade stenar, {kline('signed')} ({K['signed']['n']} stenar); inom samma ristare, {kline('within')} ({K['within']['carvers']} ristare med stenar i minst två stilgrupper, {K['within']['n']} stenar); utan den tidigaste och den senaste stilgruppen, {kline('trimmed')} ({K['trimmed']['n']} stenar).
- **Kodningen.** Av de {KOD['rule_mono_words']} ord som regeln räknar som monoftong är {KOD['rule_mono_to_uncertain']} skrivna med bara a eller utan vokal (vanligast *stan*, *rasa* och *þaR*); de visar ingen monoftong. Med en strängare regel, där bara i eller e i diftongens plats räknas som monoftong och de övriga orden som osäkra, byter {KOD['stones_changed']} stenar grupp och {KOD['stones_dropped']} faller bort. Oddskvoten per 50 år blir {d2(KS['adjusted']['or'])} justerad för landskapet (mot {d2(KR['adjusted']['or'])} med regeln), {d2(KS['half_A']['or'])} och {d2(KS['half_B']['or'])} i halvorna och {d2(KS['uppland']['or'])} i bara Uppland, alla med p under 0,01.

**5.5 Ändarna och ristarna (explorativt, beskrivande).**

- I Uppland har {U_ST['RAK'][0]} av de {U_ST['RAK'][1]} RAK-stenarna monoftongstavning, och {U_RAK_GUNNAR} av de {U_ST['RAK'][1]} är ristade av Gunnar, som skriver monoftong på {GU[0]} av sina {GU[1]} stenar. Av de {U_ST['Pr5'][1]} Pr5-stenarna har {U_ST['Pr5'][0]} monoftongstavning, och {U_PR5_OPIR} av de {U_ST['Pr5'][1]} är Öpirs. Mellan dem ligger andelen mellan {pc(U_ST['Pr2'][0] / U_ST['Pr2'][1])} och {pc(U_ST['Pr1'][0] / U_ST['Pr1'][1])} procent i varje stilgrupp.
- Öpir själv skriver monoftong på {OP['Pr4'][0]} av {OP['Pr4'][1]} stenar i stilgrupp Pr4 men på {OP['Pr5'][0]} av {OP['Pr5'][1]} i Pr5 (Fishers exakta test, {pfmt(OP_P)}, inte justerat). Det är den tydligaste förändringen inom en och samma ristare i materialet.
- Monoftongen skrivs på två sätt: med vanlig i-runa (*stin*) eller med stungen i-runa (*sten*). Det är i-stavningen som försvinner, från {d1(100 * BSW['RAK']['mono_i'])} procent av æi-orden på RAK-stenarna till {d1(100 * BSW['Pr5']['mono_i'])} procent på Pr5-stenarna. e-stavningen är sällsynt i alla stilgrupper, mellan {d1(100 * BSW['Pr2']['mono_e'])} och {d1(100 * BSW['Pr4']['mono_e'])} procent, och vanligast på Pr4-stenarna. Stungna runor blir vanligare under perioden, så e-stavningen var inte möjlig överallt från början.

## 6. Diskussion

**Vad fyndet säger.** På runstenarna blir monoftongstavningen ovanligare med tiden. Det gäller med läge och ristare konstanta, i båda halvorna, i Uppland och i Södermanland, ord för ord och för både *stæinn* och andra ord. Om stavningen följde uttalet skulle det betyda att Mälardalen hade monoftong tidigt och förlorade den, och det antar ingen: fornsvenskan har monoftong. Den rimligaste läsningen är att stavningen inte följde uttalet. De tidiga ristarna skrev ofta en enda runa för diftongen, och de sena uppländska ristarna skrev *ai* nästan alltid. Det ser ut som en skriftnorm som slog igenom, buren av ristare som Öpir, snarare än en förändring i talet.

**Mot tidigare forskning.** Wessén daterade ljudbytet med hjälp av runstenarnas stavning. Vårt resultat säger att den stavningen i Mälardalen rör sig åt fel håll för att kunna bära en sådan datering: de sena stenarna skriver diftong oftare än de tidiga. Det stöder Källströms (2014) sätt att ställa frågan, där skriftnormen och dialekten måste hållas isär, och det passar med att det är i-stavningen som försvinner medan e-stavningen, som Källström läser som monoftong, står kvar och är vanligast på Pr4-stenarna. Det säger inte när monoftongeringen nådde Mälardalen. Det säger att runstenarnas *stin* och *stain* inte ensamma kan visa det.

**Svagheter, i ordning efter vikt.**

1. **Ändarna bär nedgången.** Mellan omkring 1030 och 1070 står andelen nästan still, och utan den tidigaste och den senaste stilgruppen är trenden inte signifikant ({pfmt(K['trimmed']['p'])}). Pr5 har bara {BS['Pr5']['n']} stenar.
2. **I Uppland är ändarna två ristare.** Gunnar står för {U_RAK_GUNNAR} av {U_ST['RAK'][1]} RAK-stenar och Öpir för {U_PR5_OPIR} av {U_ST['Pr5'][1]} Pr5-stenar. Inom samma ristare går trenden åt samma håll men är inte signifikant ({pfmt(K['within']['p'])}). Fyndet kan därför läsas som en skillnad mellan ristartraditioner snarare än en gradvis förändring hos alla. Det passar med en skriftnorm, men det betyder att resultatet vilar på få verkstäder.
3. **Dateringen.** Stilgrupperna är en relativ kronologi med osäkra årtal. RAK är en bred och tidig grupp vars stenar mest står i Götaland; modellen håller läget konstant, och Uppland ensamt visar samma riktning, men där är RAK i hög grad Gunnar. Med årtal dragna inom stilgruppernas intervall blir förändringen {pc(-DR['change_max'])}–{pc(-DR['change_min'])} procentenheter i stället för {pc(-T['change'])}.
4. **Mätningen.** Draget bygger på Rundatas normalisering och translittering, ord för ord. Kodningskontrollen ändrar ingenting, men bara signerade stenar ger inget signifikant resultat ({K['signed']['n']} stenar).
5. **Vad stavningen betyder.** Om *stin* betecknar en monoftong eller är ett förkortat sätt att skriva diftongen är just den fråga resultatet berör. Resultatet visar att stavningen inte följer ljudbytet i den väntade riktningen, men det kan inte självt avgöra vad stavningen betecknar.

**Vad som skulle fälla fyndet.** En datering som inte bygger på ornamentiken, där de sena stenarna i Mälardalen hade monoftongstavning lika ofta som de tidiga; eller om Öpirs Pr5-stenar visade sig stå i en trakt där alla ristare skrev diftong, så att skillnaden är en fråga om plats och inte om tid.

## 7. Slutsats

Monoftongstavningen blir ovanligare på runstenarna, från {pc(T['first'])} till {pc(T['last'])} procent med läge och ristare konstanta, och förändringen tål varje känslighetsanalys. Den går mot den ljudutveckling som stavningen har använts för att datera. Den sena uppländska stavningen *stain* speglar troligen en skriftnorm. Nästa steg är att pröva förändringen inom ristarskolor över generationer och mot en datering som är oberoende av ornamentiken.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 31 oktober 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Draget: `src/language_profile.py` (ai_alla och ai_counts).
- Förändringen över tid, halvorna och mätkontrollerna: `r/change.R`. Känslighetsanalyserna: `r/robustness.R` och `src/robustness.py` (metodbeskrivning i `METHODS.md`, avsnitt 1v). Resultaten sparas under materialets version `{FP}`.
- Kodningskontrollen: `utdata/monoftong/kodning.py` och `utdata/monoftong/kodning.R`, med urvalet om 40 ord i `kodning.json`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_monoftong.py`, som räknar de beskrivande talen, läser resten ur resultatfilerna och stannar om något inte stämmer. Mallen: `utdata/rapporter/MALL.md`, version 2.
- I Vitki visas förändringen under Statistik, Förändring, med känslighetsanalyserna steg för steg.

## Referenser

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), s. 289–300.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R-paket.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Källström, M. 2014. Skriftnorm och runsvensk dialekt – en pilotstudie från Västmanland. I: M. Bylin m.fl. (red.), *Studier i svensk språkhistoria 12. Variation och förändring*. Stockholm, s. 110–122.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Marklund, F. 2018. *Monoftongeringen i Sverige och Danmark*. Masteruppsats. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Thompson, C. W. 1975. *Studies in Upplandic Runography*. Austin: University of Texas Press.
- Wessén, E. 1968. *Svensk språkhistoria 1. Ljudlära och ordböjningslära*. 8 uppl. Stockholm.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2 uppl. Boca Raton: Chapman & Hall/CRC.

:::box Det viktigaste i korthet
- Runstenarna skrev monoftong allt mer sällan, fast språket var på väg åt andra hållet.
- Den sena uppländska stavningen *stain* ser ut som en skriftnorm, buren av ristare som Öpir, och inte som uttalet.
- Stavningen på stenarna i Mälardalen kan därför inte ensam visa när monoftongeringen kom dit.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, Runic Swedish, monophthongisation, spelling, written norm, carvers, stylistic chronology, logistic regression. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** The East Norse monophthongisation, in which the diphthong æi became ē (*stæinn* > *stēn*), has been dated from the spelling of the runestones: when the carver writes *stin* instead of *stain*, it has been read as a sign that the sound change had reached the district. By that dating the monophthong spelling should become more common in the Mälaren region during the eleventh century. The question here is how the share actually changes over time, with place and carver held constant.
**Material.** {en_n(T['n'])} dated Swedish Viking-Age runestones with at least one word that has æi in the Scandinavian Runic-text Database (Rundata), {en_n(AR['n_words'])} such words in all.
**Method.** Logistic regression with the midpoint of the stone's style group as time, the stone's location as a spatial smooth and the carver as a random effect; Holm correction over the {N_TIME} traits whose change was tested in the same way; internal replication in two halves; eight sensitivity analyses; twelve checks of the measurement and one check of the coding; adjustment for all {N_SHOWN} associations the project reports.
**Results.** The share of stones with a monophthong spelling falls from {pc(T['first'])} percent around {T['year_first']} to {pc(T['last'])} percent around {T['year_last']}, a change of {pc(-T['change'])} percentage points (95 % interval {pc(-T['change_hi'])}–{pc(-T['change_lo'])}), {pfmt(T['p'], True)}, Holm-corrected {pfmt(T['q'], True)}. Same direction and significant in both halves; every sensitivity analysis holds; adjusted for all associations q < 0.001. The decline is also seen word by word and in both Uppland and Södermanland. It lies at the beginning and end of the period: between about 1030 and 1070 the share hardly moves, and without the earliest and the latest style group the trend is not significant. In Uppland the two ends are largely two carvers, Gunnar and Öpir.
**Conclusion.** The spelling moved in the opposite direction to the sound change it has been used to date. The late Upplandic spelling *stain* probably reflects a written norm rather than the pronunciation, and the runestone spelling in the Mälaren region therefore cannot by itself show when the monophthongisation reached it.

## 1. Introduction

There is agreement that the East Norse monophthongisation, in which the diphthongs æi, au and øy became long monophthongs, began in Denmark in the tenth century, and the evidence is the spelling of the runic inscriptions: the digraphs are replaced by a single rune, so that *stain* becomes *stin* (Marklund 2018, p. 12, with references). From the spelling of the runestones Elias Wessén assumed that the sound change reached Östergötland and Västergötland around the year 1000 and central Sweden towards the end of the eleventh century (Wessén 1968, pp. 32 f., after Marklund 2018, p. 12). Magnus Källström (2014) has read the spelling *sten*, with a dotted i-rune, as a sign that æi had become [e:] in Västmanland, around Uppsala, in western Uppland and at two places in Södermanland, and he frames the question as one of written norm and dialect (after Marklund 2018, p. 13). That the carvers spelled differently, and that spelling can be used to tell them apart, has long been known (Thompson 1975).

We have found no study that measures how the share of monophthong spellings changes over time with place and carver held constant. If the spelling followed the pronunciation, the share should rise in the Mälaren region during the eleventh century. The aim here is to measure the change and to test whether it holds.

## 2. Pre-registration: what was fixed in advance and what is exploratory

No analysis plan was locked for this question before the results were known. The finding is therefore not pre-registered, and it should be read as a discovery in a systematic survey.

The survey was a general method applied at once to {N_TIME} traits in the spelling and content of the runestones: the same model, the same measure of time, the same correction over the traits and the same division of the material into two halves for every trait, fixed in the program code before the survey was run. The trait in this report was added to the survey on 11 October 2026. On the same day, after the pattern had been seen, twelve checks of the measurement were added to test the objections a runologist would reasonably raise; all are reported in section 5.4, including those that do not hold.

The p-value is corrected for the {N_TIME} traits tested and for all {N_SHOWN} associations the project reports, and the halves were fixed independently of the patterns. Section 5.5 on the carvers and the ways of spelling is exploratory: it was computed after the pattern was known and is reported with p-values that are not adjusted. The check of the coding in 5.4 was made on 31 October 2026, while the report was being written.

## 3. Material

- **Source.** The Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University: transliteration, normalisation, province, parish, carver and style group for each inscription. The material was frozen for the analysis on 29 October 2026.
- **The stones.** Viking-Age runestones in the Swedish provinces. Runestones only; other objects with runes are not included. Skåne and Blekinge are counted as Denmark in Rundata and are not included.
- **The words.** Words with æi in Rundata's normalisation (*ræisa*, *stæinn*, *þæiR*, *bæði* and others), compared word by word with the transliteration, only when the two texts have the same number of words; proper names and uncertain readings are not counted. A word is spelled with a *diphthong* when the transliteration has ai, ia, ei or ae, otherwise with a *monophthong*. *stæinn* makes up {pc(AR['share_sten'])} percent of the {en_n(AR['n_words'])} words.
- **The trait.** A stone has a *monophthong spelling* when at least one of its æi words is spelled with a monophthong. The trait can be determined on {en_n(F['n'])} stones; {en_n(T['n'])} of them are dated, and {T['n_yes']} have a monophthong spelling.
- **Time.** The midpoint of the style group in Gräslund's chronology of the ornament (Gräslund 2006): RAK {BS['RAK']['year']}, Fp {BS['Fp']['year']}, Pr1 {BS['Pr1']['year']}, Pr2 {BS['Pr2']['year']}, Pr3 {BS['Pr3']['year']}, Pr4 {BS['Pr4']['year']}, Pr5 {BS['Pr5']['year']}. The style groups rest on the ornament, not on the spelling.
- **The carver.** The carver Rundata gives without a question mark. Stones without a secure carver are grouped by parish.

## 4. Method

**4.1 The model.** Logistic regression (the R package mgcv, R {DONE['r_version'].split()[2]}; Wood 2017) with the trait against the style-group midpoint as a smooth curve, the stone's location as a spatial smooth and the carver as a random effect, so that a prolific carver's habit is not counted as a change. The curve is shown as the adjusted share for a typical carver, with 95 % intervals from 300 draws of the model's coefficients. The uncertainty of the dating is tested by drawing each stone's year evenly within its style group's interval, ten times.

**4.2 Correction and replication.** Holm correction (Holm 1979) over the {N_TIME} traits whose change was tested. Internal replication: the material was divided once, for all the project's analyses, into two halves parish by parish, and the change must hold in each half on its own.

**4.3 Sensitivity analyses.** The same fixed series as for every association the project reports, with time in steps of 50 years and the odds ratio for one such step: the raw model; adjusted for province; the carver as a random effect; the parish as a random effect; the stone's location as a spatial surface (only stones that stand in place); each half on its own; and without one province at a time (provinces with at least {ROB['min_province']} stones). An analysis holds when p is below {ROB['alpha']} and the direction is the same as in the adjusted model; without a province, significance is required only where at least two thirds of the stones remain. The p-values are also adjusted together for all {N_SHOWN} associations reported (Benjamini & Hochberg 1995); the adjusted value is called q. The model's assumptions are checked with simulated residuals (DHARMa; Hartig 2022).

**4.4 Checks of the measurement.** Twelve variants of the same straight trend in time, with location and carver as in 4.1 unless stated (listed in 5.4), and a check of the coding with a stricter rule.

**4.5 Deviations and errors.** No plan existed, so no deviations from a plan can be reported. While the report was being written, a random sample of the words showed that the rule also counts words spelled with a alone or without a vowel as monophthongs. The result was therefore recomputed with a stricter coding (5.4); it does not change.

## 5. Results

**5.1 The main test.** With location and carver constant the share falls from {pc(T['first'])} percent around {T['year_first']} to {pc(T['last'])} percent around {T['year_last']}, a change of {pc(-T['change'])} percentage points (95 % interval {pc(-T['change_hi'])}–{pc(-T['change_lo'])}), {pfmt(T['p'], True)}, Holm-corrected {pfmt(T['q'], True)}. The curve does not fall evenly: it goes from {pc(T['first'])} to {pc(CURVE[1028]['share'])} percent up to about 1030, hardly moves until about 1070 ({pc(CURVE[1068]['share'])} percent) and then falls again. Half A: {HA['n']} stones, from {pc(HA['first'])} to {pc(HA['last'])} percent, {pfmt(HA['p'], True)}. Half B: {HB['n']} stones, from {pc(HB['first'])} to {pc(HB['last'])} percent, {pfmt(HB['p'], True)}. The change thus holds in both halves. In plain words: around 1000 about seven stones in ten had at least one word spelled with a monophthong, around 1115 about two in ten. The sensitivity analyses' odds ratio of about 0.5 per 50 years means that the odds of a monophthong spelling roughly halve in fifty years.

{chart(False)}

**5.2 The uncertainty of the dating.** When each stone's year is drawn within its style group's interval, the change is significant in {pc(DR['share_sig']) // 10} of {DR['n']} refits and has the same shape in all of them; it then becomes smaller, between {pc(-DR['change_max'])} and {pc(-DR['change_min'])} percentage points.

**5.3 The sensitivity analyses** ({P['n']} stones, {P['k']} with a monophthong spelling; time in steps of 50 years). All {ME['ladder']['tested']} hold:

- Raw model: odds ratio {RU['raw']['or']:.2f} ({RU['raw']['ci'][0]:.2f}–{RU['raw']['ci'][1]:.2f}), {pfmt(RU['raw']['p'], True)}.
- Adjusted for province: {RU['adjusted']['or']:.2f} ({RU['adjusted']['ci'][0]:.2f}–{RU['adjusted']['ci'][1]:.2f}), {pfmt(RU['adjusted']['p'], True)}. That corresponds to {pc(EF['share_lo'])} percent in 1000 against {pc(EF['share_hi'])} percent in 1100, {pc(-EF['diff'])} percentage points (probably between {pc(-EF['diff_ci'][1])} and {pc(-EF['diff_ci'][0])}).
- Carver as a random effect ({RU['carver']['groups']} carvers and parish groups): {RU['carver']['or']:.2f} ({RU['carver']['ci'][0]:.2f}–{RU['carver']['ci'][1]:.2f}), {pfmt(RU['carver']['p'], True)}.
- Parish as a random effect ({RU['parish']['groups']} parishes): {RU['parish']['or']:.2f} ({RU['parish']['ci'][0]:.2f}–{RU['parish']['ci'][1]:.2f}), {pfmt(RU['parish']['p'], True)}.
- The stone's location as a spatial surface ({RU['place']['n']} stones that stand in place): {RU['place']['or']:.2f} ({RU['place']['ci'][0]:.2f}–{RU['place']['ci'][1]:.2f}), {pfmt(RU['place']['p'], True)}.
- Half A ({RU['half_A']['n']} stones): {RU['half_A']['or']:.2f}, {pfmt(RU['half_A']['p'], True)}. Half B ({RU['half_B']['n']} stones): {RU['half_B']['or']:.2f}, {pfmt(RU['half_B']['p'], True)}. The halves follow the same rule as in 5.1 but are computed separately, so that three stones fall in the other half.
- Without one province at a time ({LO['n_provinces']} provinces tested): the direction holds without each of them. Weakest without Uppland, when {LO['n']} stones remain, fewer than two thirds: odds ratio {LO['or']:.2f} ({LO['ci'][0]:.2f}–{LO['ci'][1]:.2f}), {pfmt(LO['p'], True)}.
- The model's assumptions: residual distribution p = {CK['uniformity_p']:.2f}, overdispersion p = {CK['dispersion_p']:.2f}, remaining spatial pattern p = {CK['spatial_p']:.2f}; no deviations.
- Adjusted for all {N_SHOWN} associations the project reports: q < 0.001. The association is one of {N_ALLRUNG} that hold in every sensitivity analysis.

**5.4 The checks of the measurement.** The direction is the same in all twelve; nine are significant and three are not:

- Per stone: {kline('stone', False)}. Per word, so that a stone with many æi words does not weigh more: {kline('word', False)}.
- *stæinn* only: {kline('sten', False)} ({K['sten']['n']} stones). Other æi words only: {kline('other', False)} ({K['other']['n']} stones). The change is thus not confined to the word for stone.
- Only stones with a secure carver: {kline('attributed', False)} ({K['attributed']['n']} stones). Only stones without: {kline('unattributed', False)} ({K['unattributed']['n']} stones). Without the carver in the model: {kline('no_carver', False)}.
- Uppland only: {kline('uppland', False)} ({K['uppland']['n']} stones). Södermanland only: {kline('sodermanland', False)} ({K['sodermanland']['n']} stones).
- **Not significant:** only signed stones, {kline('signed', False)} ({K['signed']['n']} stones); within the same carver, {kline('within', False)} ({K['within']['carvers']} carvers with stones in at least two style groups, {K['within']['n']} stones); without the earliest and the latest style group, {kline('trimmed', False)} ({K['trimmed']['n']} stones).
- **The coding.** Of the {KOD['rule_mono_words']} words the rule counts as monophthongs, {KOD['rule_mono_to_uncertain']} are spelled with a alone or without a vowel (most often *stan*, *rasa* and *þaR*); they show no monophthong. With a stricter rule, in which only i or e in the place of the diphthong counts as a monophthong and the other words as uncertain, {KOD['stones_changed']} stones change group and {KOD['stones_dropped']} drop out. The odds ratio per 50 years becomes {KS['adjusted']['or']:.2f} adjusted for province (against {KR['adjusted']['or']:.2f} with the rule), {KS['half_A']['or']:.2f} and {KS['half_B']['or']:.2f} in the halves and {KS['uppland']['or']:.2f} in Uppland only, all with p below 0.01.

**5.5 The ends and the carvers (exploratory, descriptive).**

- In Uppland {U_ST['RAK'][0]} of the {U_ST['RAK'][1]} RAK stones have a monophthong spelling, and {U_RAK_GUNNAR} of the {U_ST['RAK'][1]} were carved by Gunnar, who writes a monophthong on {GU[0]} of his {GU[1]} stones. Of the {U_ST['Pr5'][1]} Pr5 stones, {U_ST['Pr5'][0]} have a monophthong spelling, and {U_PR5_OPIR} of the {U_ST['Pr5'][1]} are Öpir's. In between, the share lies between {pc(U_ST['Pr2'][0] / U_ST['Pr2'][1])} and {pc(U_ST['Pr1'][0] / U_ST['Pr1'][1])} percent in every style group.
- Öpir himself writes a monophthong on {OP['Pr4'][0]} of {OP['Pr4'][1]} stones in style group Pr4 but on {OP['Pr5'][0]} of {OP['Pr5'][1]} in Pr5 (Fisher's exact test, {pfmt(OP_P, True)}, not adjusted). It is the clearest change within one and the same carver in the material.
- The monophthong is spelled in two ways: with a plain i-rune (*stin*) or with a dotted i-rune (*sten*). It is the i-spelling that disappears, from {100 * BSW['RAK']['mono_i']:.1f} percent of the æi words on the RAK stones to {100 * BSW['Pr5']['mono_i']:.1f} percent on the Pr5 stones. The e-spelling is rare in every style group, between {100 * BSW['Pr2']['mono_e']:.1f} and {100 * BSW['Pr4']['mono_e']:.1f} percent, and most common on the Pr4 stones. Dotted runes become more common during the period, so the e-spelling was not available everywhere from the start.

## 6. Discussion

**What the finding says.** On the runestones the monophthong spelling becomes rarer over time. This holds with location and carver constant, in both halves, in Uppland and in Södermanland, word by word and for both *stæinn* and other words. If the spelling followed the pronunciation, it would mean that the Mälaren region had the monophthong early and lost it, and nobody assumes that: Old Swedish has the monophthong. The most reasonable reading is that the spelling did not follow the pronunciation. The early carvers often wrote a single rune for the diphthong, and the late Upplandic carvers almost always wrote *ai*. That looks like a written norm that took hold, carried by carvers such as Öpir, rather than a change in speech.

**Against earlier research.** Wessén dated the sound change from the spelling of the runestones. Our result says that in the Mälaren region this spelling moves in the wrong direction to bear such a dating: the late stones write the diphthong more often than the early ones. It supports Källström's (2014) way of putting the question, in which the written norm and the dialect have to be kept apart, and it fits with the fact that it is the i-spelling that disappears, while the e-spelling, which Källström reads as a monophthong, remains and is most common on the Pr4 stones. It does not say when the monophthongisation reached the Mälaren region. It says that the runestones' *stin* and *stain* cannot show that on their own.

**Weaknesses, in order of weight.**

1. **The ends carry the decline.** Between about 1030 and 1070 the share hardly moves, and without the earliest and the latest style group the trend is not significant ({pfmt(K['trimmed']['p'], True)}). Pr5 has only {BS['Pr5']['n']} stones.
2. **In Uppland the ends are two carvers.** Gunnar accounts for {U_RAK_GUNNAR} of {U_ST['RAK'][1]} RAK stones and Öpir for {U_PR5_OPIR} of {U_ST['Pr5'][1]} Pr5 stones. Within the same carver the trend goes the same way but is not significant ({pfmt(K['within']['p'], True)}). The finding can therefore be read as a difference between carving traditions rather than a gradual change in everyone. That fits a written norm, but it means the result rests on few workshops.
3. **The dating.** The style groups are a relative chronology with uncertain years. RAK is a broad, early group whose stones stand mostly in Götaland; the model holds location constant, and Uppland on its own shows the same direction, but there RAK is largely Gunnar. With years drawn within the style groups' intervals the change becomes {pc(-DR['change_max'])}–{pc(-DR['change_min'])} percentage points instead of {pc(-T['change'])}.
4. **The measurement.** The trait rests on Rundata's normalisation and transliteration, word by word. The coding check changes nothing, but signed stones alone give no significant result ({K['signed']['n']} stones).
5. **What the spelling means.** Whether *stin* denotes a monophthong or is a shortened way of writing the diphthong is the very question the result touches. The result shows that the spelling does not follow the sound change in the expected direction, but it cannot by itself decide what the spelling denotes.

**What would overturn the finding.** A dating that does not rest on the ornament, in which the late stones of the Mälaren region had a monophthong spelling as often as the early ones; or if Öpir's Pr5 stones turned out to stand in a district where every carver wrote the diphthong, so that the difference is one of place and not of time.

## 7. Conclusion

The monophthong spelling becomes rarer on the runestones, from {pc(T['first'])} to {pc(T['last'])} percent with location and carver constant, and the change withstands every sensitivity analysis. It runs against the sound change the spelling has been used to date. The late Upplandic spelling *stain* probably reflects a written norm. The next step is to test the change within carving schools across generations and against a dating independent of the ornament.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 31 October 2026. No release with a DOI exists yet; when one is made, the report will refer to it. All code and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The trait: `src/language_profile.py` (ai_alla and ai_counts).
- The change over time, the halves and the checks of the measurement: `r/change.R`. The sensitivity analyses: `r/robustness.R` and `src/robustness.py` (method description in `METHODS.md`, section 1v). The results are saved under the material's version `{FP}`.
- The coding check: `utdata/monoftong/kodning.py` and `utdata/monoftong/kodning.R`, with the sample of 40 words in `kodning.json`.
- The report is built by `utdata/blogg/build/build_rapport_monoftong.py`, which computes the descriptive counts, reads the rest from the result files and stops if anything disagrees. The template: `utdata/rapporter/MALL.md`, version 2.
- In Vitki the change is shown under Statistics, Change, with the sensitivity analyses step by step.

## References

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), pp. 289–300.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R package.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Källström, M. 2014. Skriftnorm och runsvensk dialekt – en pilotstudie från Västmanland. In: M. Bylin et al. (eds), *Studier i svensk språkhistoria 12. Variation och förändring*. Stockholm, pp. 110–122.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Marklund, F. 2018. *Monoftongeringen i Sverige och Danmark*. Master's thesis. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Thompson, C. W. 1975. *Studies in Upplandic Runography*. Austin: University of Texas Press.
- Wessén, E. 1968. *Svensk språkhistoria 1. Ljudlära och ordböjningslära*. 8th ed. Stockholm.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2nd ed. Boca Raton: Chapman & Hall/CRC.

:::box The essentials
- The runestones wrote the monophthong less and less often, although the language was heading the other way.
- The late Upplandic spelling *stain* looks like a written norm, carried by carvers such as Öpir, and not like the pronunciation.
- The spelling on the stones of the Mälaren region therefore cannot by itself show when the monophthongisation arrived there.
:::
"""

# the plain-words sentence rests on these numbers (mallen version 4)
assert (pc(T['first']), pc(T['last'])) == (69, 22)
assert 0.5 <= RU['adjusted']['or'] < 0.6
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
       "body_en": body_en, "labels": ["Rapport", "Språk och stavning", "Datering och stil"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_monoftong.json")
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
                 "topic": "Rapport|ai_alla", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
