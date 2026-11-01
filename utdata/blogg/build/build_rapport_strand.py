"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4; Fullt prövat fynd): "Runstenarna restes vid sin tids
vatten – 64 procent inom 500 meter från vattnet år 1050, mot 46 procent av marken runt dem" (sv + en). Den låsta planen
analysplaner/2026-10-23-strand-och-gravfalt.md (H1–H3, R1–R7, S1–S4), tillägget med T1 (2026-10-31-strand-tillagg.md)
och tilläggsplanen för robusthetsstegen (2026-11-01-strand-trappan.md). Alla siffror asserteras mot
utdata/strand/resultat.json och trappan.json.
    ../../../.venv/bin/python build_rapport_strand.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402

APP_VERSION = json.load(open(os.path.join(ROOT, "web", "package.json")))["version"]
assert APP_VERSION == "3.0.0"
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 1
TODAY = "2026-11-01"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = ("analysplanen låstes 2026-10-23; tillägget för flyttade stenar låstes 2026-10-31; analysen kördes 2026-10-31; "
         "tilläggsplanen för känslighetsanalyserna låstes och kördes 2026-11-01")
TL_EN = ("the analysis plan was locked 2026-10-23; the addendum for moved stones was locked 2026-10-31; the analysis was run "
         "2026-10-31; the addendum plan for the sensitivity analyses was locked and run 2026-11-01")
SD = os.path.join(ROOT, "utdata", "strand")
R = json.load(open(os.path.join(SD, "resultat.json"), encoding="utf-8"))
TR = json.load(open(os.path.join(SD, "trappan.json"), encoding="utf-8"))
IL = json.load(open(os.path.join(SD, "illustration.json"), encoding="utf-8"))  # kartorna ur 06_illustration.R
assert (IL["n_stones"], IL["n_random"], IL["median_stones_m"], IL["median_random_m"], IL["n_overview"]) == (40, 100, 214, 397, 891)
SHA = {k: open(os.path.join(ROOT, "analysplaner", f"{k}.sha256")).read().split()[0][:16]
       for k in ("2026-10-23-strand-och-gravfalt", "2026-10-31-strand-tillagg", "2026-11-01-strand-trappan")}
assert SHA["2026-10-23-strand-och-gravfalt"] == R["plan_sha256"][:16] == "4ddb7d6cecb470a1"
assert SHA["2026-10-31-strand-tillagg"] == "dc63b72b3147f9c2" and SHA["2026-11-01-strand-trappan"] == TR["plan_sha256"][:16] == "2993273eff5006c6"

pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731


def num(x, d=2, en=False):
    s = f"{x:.{d}f}"
    return s if en else s.replace(".", ",")


def m(x, en=False):
    return f"{x:,}" if en else f"{x:,}".replace(",", " ")


def pfmt(p, en=False):
    if p < 0.0001:
        return "p < 0.0001" if en else "p < 0,0001"
    s = f"{p:.4f}" if p < 0.001 else (f"{p:.3f}" if p < 0.1 else f"{p:.2f}")
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the locked plan ------------------------------------------------------------------------------------------------
V, PO = R["verdict"], R["population"]
assert V["H1"] == "håller" and all(V["H1_criteria"].values()) and V["H3"] == "håller" and all(V["H3_criteria"].values())
assert V["H2"] == "tydligare med dåtidens vatten" and V["R6_all_delta"] is True
assert V["provinces_h1"] == V["provinces_h3"] == ["U", "Sö", "Ög", "Sm", "Vg"]
assert (PO["n"], PO["n_random"], PO["n_sites"], PO["n_dated"], PO["n_gravfalt"], PO["stones_in_water_1050"], PO["stones_in_water_1949"]) == \
    (1099, 10990, 935, 587, 18633, 108, 88)
assert PO["provinces"] == {"Ög": 89, "Öl": 20, "Sm": 69, "Sö": 234, "U": 623, "Vg": 64} and sum(PO["other_provinces_not_tested"].values()) == 45
assert PO["halves"] == {"A": 543, "B": 556}
H1, HA, HB, HS = R["H1"]["overall"], R["H1"]["halves"]["A"], R["H1"]["halves"]["B"], R["H1"]["sites"]
assert (H1["median_stones_m"], H1["median_random_m"], pc(H1["within_500_stones"]), pc(H1["within_500_random"]), num(H1["auc"])) == (305, 555, 64, 46, "0,63")
assert (pc(H1["within_1000_stones"]), pc(H1["within_1000_random"])) == (83, 76) and H1["p"] < 1e-40
assert all(x["p"] < 1e-15 for x in (HA, HB, HS)) and (HA["n_parishes"], HB["n_parishes"]) == (190, 187)
P1 = {r["province"]: r for r in R["H1"]["provinces"]}
P3 = {r["province"]: r for r in R["H3"]["provinces"]}
assert all(P1[k]["q_bh"] < 0.01 for k in ("U", "Sö", "Ög", "Sm", "Vg")) and 0.05 < P1["Öl"]["q_bh"] < 0.06
assert all(P3[k]["q_bh"] < 1e-6 for k in ("U", "Sö", "Ög", "Sm", "Vg")) and P3["Öl"]["q_bh"] > 0.3
NOW = R["today"]["overall"]
assert (NOW["median_stones_m"], NOW["median_random_m"], pc(NOW["within_500_stones"]), pc(NOW["within_500_random"]), num(NOW["auc"], 3)) == (364, 601, 60, 42, "0,620")
H2 = R["H2"]
assert (num(H2["auc_then"], 3), num(H2["auc_now"], 3), num(H2["delta_auc"], 3), [num(x, 3) for x in H2["ci95"]], H2["B"]) == \
    ("0,629", "0,620", "0,009", ["0,002", "0,017"], 2000)
H2P = {r["province"]: r for r in H2["provinces"]}
assert [k for k in H2P if H2P[k]["auc_then"] > H2P[k]["auc_now"]] == ["U", "Sö", "Ög", "Öl"]
H3, H3A, H3B, H3S = R["H3"]["overall"], R["H3"]["halves"]["A"], R["H3"]["halves"]["B"], R["H3"]["sites"]
assert (H3["median_stones_m"], H3["median_random_m"], pc(H3["within_500_stones"]), pc(H3["within_500_random"]), num(H3["auc"])) == (304, 1045, 67, 24, "0,78")
assert all(x["p"] < 1e-100 for x in (H3A, H3B, H3S))
S = R["secondary"]
assert (num(S["S1a"]["or"], 1), num(S["S1b"]["or"], 1)) == ("1,7", "3,5") and S["S1a"]["halves"]["replicated"] and S["S1b"]["halves"]["replicated"]
assert S["S1a"]["q_bh"] < 1e-30 and S["S1b"]["q_bh"] < 1e-100
assert all(S[k]["q_bh"] > 0.05 and not S[k]["halves"]["replicated"] for k in ("S2", "S3", "S4"))
assert (pc(S["S2"]["early"]), pc(S["S2"]["late"]), S["S4"]["n_bridge"], S["S4"]["median_bridge_m"], S["S4"]["median_other_m"]) == (84, 84, 82, 207, 309)
RB = R["robustness"]
R1 = RB["R1"]
assert set(R1) == {"AD750", "AD950", "AD1150", "AD1250", "AD550", "AD1550"} and all(v["p"] < 1e-30 for v in R1.values())
R1A = (min(v["auc"] for v in R1.values()), max(v["auc"] for v in R1.values()))
assert (num(R1A[0]), num(R1A[1])) == ("0,62", "0,64")
R2, R5 = RB["R2"], RB["R5"]
assert num(R2["auc"], 3) == "0,566" and R2["p"] < 1e-10 and R5["n_excluded"] == 108 and num(R5["auc"], 3) == "0,589" and R5["p"] < 1e-15
R6 = RB["R6"]
assert all(v["p"] < 1e-40 for v in R6.values()) and (num(R6["minus1"]["auc"], 3), num(R6["plus1"]["auc"], 3)) == ("0,630", "0,645")
R7 = RB["R7"]
assert (num(R7["r2km"]["water"]["auc"], 3), num(R7["r10km"]["water"]["auc"], 3), num(R7["r2km"]["grave"]["auc"], 3), num(R7["r10km"]["grave"]["auc"], 3)) == \
    ("0,628", "0,627", "0,707", "0,829")
T1 = R["T1"]
assert T1["n"] == 657 and T1["water_holds"] and T1["grave_holds"] and num(T1["water"]["auc"], 3) == "0,629" and num(T1["grave"]["auc"], 3) == "0,786"
D1, D2 = R["D1"], R["D2"]
assert (D1["n_all"], D1["n_moved"], num(D1["then"]["auc"], 3), num(D1["moved_only_then"]["auc"], 3)) == (2167, 1068, "0,650", "0,659")
assert (num(D2["water_viking"]["median_stones_km"], 1), num(D2["water_viking"]["median_random_km"], 1), D2["water_viking"]["n_stones"]) == ("3,6", "5,3", 2254)

# ---- the addendum ladder ----------------------------------------------------------------------------------------------
assert TR["plan"] == "analysplaner/2026-11-01-strand-trappan.md" and TR["H1"]["all_hold"] and TR["H3"]["all_hold"]
C = TR["counts"]
assert len(TR["H1"]["steps"]) == len(TR["H3"]["steps"]) == 9  # nio steg i tilläggsplanen
assert (C["reerected"], C["moved_runor"], C["not_staying_now"], C["carvers"], C["sure_carver_stones"], C["early"], C["late"]) == (101, 177, 295, 67, 399, 335, 252)
G1, G3, L1, L3 = TR["H1"]["rungs"], TR["H3"]["rungs"], TR["H1"]["lopo"], TR["H3"]["lopo"]
for G in (G1, G3):
    assert all(v["holds"] for v in G.values()) and not G["socken_slumpeffekt"]["warnings"]
assert all(v["holds"] for L in (L1, L3) for v in L.values()) and num(L1["U"]["share_kept"], 2) == "0,43"
assert abs(G1["huvud"]["auc"] - H1["auc"]) < 1e-9 and abs(G3["huvud"]["auc"] - H3["auc"]) < 1e-9  # same measures as the plan
MM1, MM3 = G1["socken_slumpeffekt"], G3["socken_slumpeffekt"]
assert (num(MM1["or"]), num(MM3["or"]), MM1["n_parishes"]) == ("1,82", "3,57", 373)
assert (G1["en_per_ristare"]["n_stones"], G1["utan_aterresta"]["n_stones"], G1["utan_flyttade_runor"]["n_stones"], G1["dagens_flyttregel"]["n_stones"]) == (767, 998, 922, 804)
LA1 = (min(v["auc"] for v in L1.values()), max(v["auc"] for v in L1.values()))
LA3 = (min(v["auc"] for v in L3.values()), max(v["auc"] for v in L3.values()))
GA1 = (min(v["auc"] for k, v in G1.items() if "auc" in v), max(v["auc"] for k, v in G1.items() if "auc" in v))
GA3 = (min(v["auc"] for k, v in G3.items() if "auc" in v), max(v["auc"] for k, v in G3.items() if "auc" in v))
assert (num(GA1[0]), num(GA1[1]), num(GA3[0]), num(GA3[1])) == ("0,61", "0,65", "0,72", "0,80")
assert (num(LA1[0]), num(LA1[1]), num(LA3[0]), num(LA3[1])) == ("0,62", "0,63", "0,74", "0,79")

NAME = {"U": ("Uppland", "Uppland"), "Sö": ("Södermanland", "Södermanland"), "Ög": ("Östergötland", "Östergötland"),
        "Sm": ("Småland", "Småland"), "Vg": ("Västergötland", "Västergötland"), "Öl": ("Öland", "Öland")}
ORDER = ["U", "Sö", "Ög", "Sm", "Vg", "Öl"]


def rung(r, en=False, n=True):
    if en:
        return (f"{m(r['n_stones'], True) + ' stones, ' if n else ''}median {m(r['median_stones_m'], True)} against "
                f"{m(r['median_random_m'], True)} m, AUC {num(r['auc'], 2, True)}, {pfmt(r['p'], True)}")
    return (f"{m(r['n_stones']) + ' stenar, ' if n else ''}median {m(r['median_stones_m'])} mot {m(r['median_random_m'])} m, "
            f"AUC {num(r['auc'])}, {pfmt(r['p'])}")


def chart(sv):
    f = (lambda x: f"{100 * x:.1f}".replace(".", ",")) if sv else (lambda x: f"{100 * x:.1f}")
    st, rn = ("Runstenar", "Slumpmark i samma bygd") if sv else ("Runestones", "Random land in the same district")
    rows = [":::chart Inom 500 meter, procent" if sv else ":::chart Within 500 metres, percent"]
    for lab, r in ((("Vattnet år 1050", "The water of AD 1050"), H1), (("Dagens vatten (1949)", "Today's water (1949)"), NOW),
                   (("Registrerade gravfält", "Registered grave fields"), H3)):
        rows += [f"# {lab[0] if sv else lab[1]}", f"+{st} | {f(r['within_500_stones'])} | {m(r['n_stones'], not sv)} {'stenar' if sv else 'stones'}",
                 f"{rn} | {f(r['within_500_random'])} |"]
    rows += ["Källa: SGU:s strandförskjutningsmodell (CC BY 4.0), Rundata och Riksantikvarieämbetets kulturmiljöregister." if sv else
             "Source: SGU's shore displacement model (CC BY 4.0), Rundata and the Swedish register of ancient monuments.", ":::"]
    return "\n".join(rows)


def figure(name, lang, caption):
    """En karta ur 06_illustration.R som bild i inlägget (blog_figures.freeze) med bildtexten under."""
    with open(os.path.join(SD, f"{name}_{lang}.png"), "rb") as fh:
        url = blog_figures.freeze(fh.read())
    return f"![{caption.split('.')[0]}]({url})\n{caption}"


FIG1_SV = figure("karta_oversikt", "sv", "Figur 1. Mälardalen år 1050 och i dag. Ljusblått är vatten då men land i dag. Rutan visar området i figur 2. Karta: Vitki, efter SGU:s modell (CC BY 4.0) och Rundata.")
FIG1_EN = figure("karta_oversikt", "en", "Figure 1. The Lake Mälaren region in AD 1050 and today. Light blue is water then but land today. The box shows the area of figure 2. Map: Vitki, after SGU's model (CC BY 4.0) and Rundata.")
FIG2_SV = figure("karta_detalj", "sv", f"Figur 2. Vad som mättes, kring Vassunda, Håtuna och Haga i Uppland: avståndet från varje sten (rött) och slumppunkt (grått) till närmaste vatten år 1050. Median här: stenarna {IL['median_stones_m']} meter, punkterna {IL['median_random_m']}. Karta: Vitki, efter SGU:s modell och Rundata.")
FIG2_EN = figure("karta_detalj", "en", f"Figure 2. What was measured, around Vassunda, Håtuna and Haga in Uppland: the distance from each stone (red) and random point (grey) to the nearest water of AD 1050. Median here: stones {IL['median_stones_m']} metres, points {IL['median_random_m']}. Map: Vitki, after SGU's model and Rundata.")


SLUG = "runstenarna-vid-sin-tids-vatten"
title = "Runstenarna restes vid sin tids vatten – 64 procent inom 500 meter från vattnet år 1050, mot 46 procent av marken runt dem"
title_en = "The runestones were raised by the water of their time – 64 per cent within 500 metres of the water of AD 1050, against 46 per cent of the land around them"
summary = ("Förregistrerad studie. Av de runstenar som står kvar på sin plats står nästan två av tre inom 500 meter från vattnet "
           "som det låg år 1050, mot knappt hälften av marken runt dem. Det håller i båda halvorna av materialet, med en "
           "oberoende höjdmodell och i alla känslighetsanalyser. Gravfälten drar ännu starkare, och båda sambanden finns kvar "
           "när det andra hålls lika.")
summary_en = ("Pre-registered study. Of the runestones that still stand in place, almost two in three stand within 500 metres of "
              "the water as it lay in AD 1050, against fewer than half of the land around them. This holds in both halves of the "
              "material, with an independent elevation model and in every sensitivity analysis. The grave fields draw even more "
              "strongly, and both associations remain when the other is held equal.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/forskningsrapporter/{SLUG}")
FAM = "https://vitkirunor.se/forskningsrapporter/familjegrupper-vid-gravfalten"
VAG = "https://vitkirunor.se/forskningsrapporter/ristningen-vand-mot-vagen"

body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, placering, strandförskjutning, landhöjning, gravfält, rumslig statistik, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Var runstenarna restes har diskuterats länge: vid gravfält, vid vägar och broar, vid gårdar och gränser. Vattnet är svårare att mäta, eftersom landet har höjt sig sedan vikingatiden och dagens strand inte är stenarnas. Frågan här är om stenarna restes närmare sin egen tids vatten än marken runt omkring, och om det sambandet finns kvar när närheten till gravfälten hålls lika.
**Material.** {m(PO['n'])} vikingatida runstenar som står kvar på sin plats, i Uppland, Södermanland, Östergötland, Småland, Västergötland och på Öland, och {m(PO['n_random'])} slumpvisa punkter på land inom fem kilometer från stenarna. Vattnet år 1050 enligt Sveriges geologiska undersöknings (SGU) strandförskjutningsmodell, gravfälten ur Riksantikvarieämbetets kulturmiljöregister.
**Metod.** Förregistrerad studie. Avståndet till närmaste vatten jämförs mellan stenar och punkter med Wilcoxons rangsummetest och AUC, sannolikheten att en sten står närmare än en punkt. Intern replikering i två halvor, sju känslighetsprov i planen och nio känslighetsanalyser enligt en låst tilläggsplan.
**Resultat.** {pc(H1['within_500_stones'])} procent av stenarna står inom 500 meter från vattnet år 1050, mot {pc(H1['within_500_random'])} procent av punkterna; medianavståndet är {H1['median_stones_m']} mot {H1['median_random_m']} meter, AUC {num(H1['auc'])}, {pfmt(H1['p'])}. Det håller i båda halvorna, i fem av sex landskap, för andra årtal mellan 550 och 1550, med en oberoende höjdmodell och i alla känslighetsanalyser, också jämfört med marken i samma socken. Gravfälten drar starkare: {pc(H3['within_500_stones'])} mot {pc(H3['within_500_random'])} procent inom 500 meter, AUC {num(H3['auc'])}. Båda sambanden finns kvar när det andra hålls lika. Dåtidens vatten stämmer något bättre med stenarna än dagens, men skillnaden är liten.
**Slutsats.** De som reste runstenarna valde platser nära vattnet, och ännu oftare nära gravfälten, inom bygder som redan låg vid vatten. Den största svagheten är att modellen för vattnet år 1050 är grov: {PO['stones_in_water_1050']} av stenarna hamnar i modellens vatten.

## 1. Inledning

Gunnar Ekholm (1950) frågade var runstenarna restes. Torun Zachrisson (1998) har satt dem i samband med gård, gräns och gravfält, Lydia Klos (2009) har hävdat att de flesta restes vid gravfält, och Shane McLeod (2014) har invänt att det överbetonar gravfälten på bekostnad av andra platser, som vägarna. Brostenarna, som berättar om broar och vägbyggen över vatten och sank mark, visar att vattnet hörde till stenarnas sammanhang.

Att mäta närheten till vatten är svårt. Landet har höjt sig sedan vikingatiden, i Mälardalen med omkring fem meter, så en sten som stod vid en vik kan i dag stå på torr mark, och en sten vid dagens strand kan ha stått långt från vattnet. SGU:s strandförskjutningsmodell (SGU 2022, efter Påsse & Daniels 2015) ger en öppen modell över hela landet för var vattnet låg vid olika tider.

Vi känner inte till någon studie som har mätt avståndet till vattnet på stenarnas egen tid för hela det svenska materialet, med en modell för strandförskjutningen, bara stenar som står kvar och en jämförelse med marken i samma bygd. Syftet är att göra det och pröva om sambandet finns kvar när närheten till gravfälten hålls lika.

## 2. Förregistrering: hypotes och plan

Hypoteserna, måtten och tolkningsreglerna skrevs ned i en analysplan den 23 oktober 2026, innan något avstånd hade räknats. Planen har kontrollsumman SHA-256 `{SHA['2026-10-23-strand-och-gravfalt']}…` och lades in i versionshanteringen samma kväll. Före låsningen var bara datakällorna hämtade, lagren listade, antalet stenar per landskap räknat och stilgruppernas mittår sammanställda för att välja årtal (median 1035). En provkörning av skriptet samma kväll, efter att planen hade fått sin kontrollsumma men före incheckningen, skrev bara ut förloppet och inga siffror. Statistiken kördes först den 31 oktober.

Riktningen var väntad. Projektets tidigare mått, med en grov landhöjning och med flyttade stenar, hade redan visat att stenarna står närmare vatten och gravfält än marken runt dem. Studien prövar alltså om ett känt mönster håller med bättre data, inte ett nytt.

Planens hypoteser, ordagrant: **H1 (primärt): stenarna står närmare vattnet år 1050 än slumppunkterna.** **H2: närheten är tydligare mot dåtidens vatten än mot dagens.** **H3: gravfälten, på samma urval** (stenarna står närmare registrerade gravfält än slumppunkterna). H1 *håller* om fem villkor är uppfyllda: p under 0,05 och AUC över 0,5 sammantaget, samma i båda halvorna, samma när stenar inom 200 meter från varandra slås ihop till en plats, samma för fyra andra årtal inom 200 år (750, 950, 1150 och 1250), och samma med bara havet utan modellens sjöar. H3 håller om det gäller sammantaget, i båda halvorna och för platserna. H2 kallas tydligare bara om hela 95 %-intervallet för skillnaden ligger över noll.

Två tillägg låstes senare, båda innan de räknades. Den 31 oktober (SHA-256 `{SHA['2026-10-31-strand-tillagg']}…`), innan statistiken kördes: H1 och H3 prövas också på de stenar som står kvar enligt tre källor, eftersom regeln för flyttade stenar hade rättats efter att planen låstes. Den 1 november (SHA-256 `{SHA['2026-11-01-strand-trappan']}…`), när planens resultat var kända: nio fasta känslighetsanalyser för avstånd, motsvarande dem projektet gör för andra fynd. De är konfirmatoriska i den meningen att stegen och gränserna låstes innan de räknades, men de valdes efter att huvudresultatet var känt.

## 3. Material

- **Stenarna.** Svenska vikingatida runstenar i Samnordisk runtextdatabas (Rundata), i den version som låstes i planen. Av dem har vi tagit de som har koordinater och inte är flyttade: Rundatas placering eller plats är inte kyrka, kyrkogård, mur, museum eller samling. Bara landskap med minst 20 sådana stenar prövas: Uppland ({P1['U']['n_stones']}), Södermanland ({P1['Sö']['n_stones']}), Östergötland ({P1['Ög']['n_stones']}), Småland ({P1['Sm']['n_stones']}), Västergötland ({P1['Vg']['n_stones']}) och Öland ({P1['Öl']['n_stones']}), sammanlagt {m(PO['n'])}. De {sum(PO['other_provinces_not_tested'].values())} stenarna i övriga landskap prövas inte. Bara runstenar.
- **Vattnet.** SGU:s strandförskjutningsmodell, öppna data version 1.0 (2022, CC BY 4.0). Den bygger på strandförskjutningskurvor över hela landet, en modell för landhöjningen och en höjdmodell med 50 meters upplösning. Vattnet år 1050 är modellens hav och sjöar i tidssnittet 900 år före 1950; dagens vatten är tidssnittet för år 1949. Avstånden räknas på ett rutnät med 25 meters celler.
- **Gravfälten.** Riksantikvarieämbetets kulturmiljöregister via K-samsök, hämtat den 12 oktober 2026: {m(PO['n_gravfalt'])} registrerade gravfält med koordinater.
- **Den oberoende höjdmodellen.** Copernicus DEM GLO-30 (omkring 30 meter), med landskapets landhöjning sedan vikingatiden som höjdgräns.
- **Dateringen** efter stenens ornamentikstil (Gräslund 2006): {PO['n_dated']} av stenarna.
- **Halvorna** är projektets fasta indelning socken för socken: {PO['halves']['A']} och {PO['halves']['B']} stenar.

{FIG1_SV}

## 4. Metod

**4.1 Måttet och jämförelsen.** För varje sten och varje punkt räknas avståndet till närmaste vatten år 1050, till dagens vatten och till närmaste gravfält; en punkt i vattnet får avståndet noll. Jämförelsen är en nollmodell: för varje landskap dras tio slumpvisa punkter per sten, likformigt inom fem kilometer från landskapets stenar, och bara punkter som är land både år 1050 och år 1949 behålls. Punkterna ligger alltså i de bygder där stenar restes, så provet gäller var i bygden stenen står, inte var bygderna ligger. Stenarna och punkterna jämförs med Wilcoxons rangsummetest (Wilcoxon 1945; Mann & Whitney 1947), ensidigt. Effekten anges som medianerna, andelen inom 500 meter och AUC, sannolikheten att en slumpvis vald sten står närmare än en slumpvis vald punkt (0,5 betyder ingen skillnad). Figur 2 visar mätningen i en bygd.

{FIG2_SV}

**4.2 Korrigering och replikering.** Varje hypotes prövas i var halva för sig. Landskapen prövas var för sig med Benjamini–Hochberg-korrigering (Benjamini & Hochberg 1995) över de sex, och de sekundära proven likaså över de fem. Skillnaden mellan dåtidens och dagens vatten (H2) får ett 95 %-intervall ur 2 000 bootstrapurval där stenarna dras plats för plats.

**4.3 Känslighetsanalyserna.** Planens sju prov, tilläggets prov och tilläggsplanens nio steg står med sina resultat i 5.2 och 5.3. Socknen som slumpeffekt är en logistisk regression (Bates m.fl. 2015) där punkterna får den närmaste stenens socken. När stenar tas bort tas också de punkter bort som hör till dem. Ett steg håller när AUC är över 0,5 och p under 0,05; utan ett landskap i taget krävs signifikans bara där minst två tredjedelar av stenarna är kvar.

**4.4 Avvikelser från planen.** Statistiken kördes åtta dagar efter att avstånden räknades, efter tillägget för flyttade stenar; planens prov är oförändrade. De {m(PO['distances_at_tile_margin'])} avstånd som nådde kanten av beräkningsrutorna, nästan alla för bara havet långt inne i landet, räknades om på ett rutnät med 100 meters celler över hela landskapet; planen anger ingen cellstorlek. Känslighetsanalyserna i tilläggsplanen lades till efter att planens resultat var kända (se 2). I övrigt inga.

## 5. Resultat

**5.1 Vattnet år 1050 (H1), gravfälten (H3) och dagens vatten (H2).** Av de {m(PO['n'])} stenarna står {pc(H1['within_500_stones'])} procent inom 500 meter från vattnet år 1050, mot {pc(H1['within_500_random'])} procent av de {m(PO['n_random'])} punkterna; inom en kilometer {pc(H1['within_1000_stones'])} mot {pc(H1['within_1000_random'])} procent. Medianavståndet är {H1['median_stones_m']} mot {H1['median_random_m']} meter, AUC {num(H1['auc'], 3)}, {pfmt(H1['p'])}. Halva A ({HA['n_stones']} stenar i {HA['n_parishes']} socknar): AUC {num(HA['auc'], 3)}, {pfmt(HA['p'])}. Halva B ({HB['n_stones']} stenar i {HB['n_parishes']} socknar): AUC {num(HB['auc'], 3)}, {pfmt(HB['p'])}. Med {HS['n_sites']} platser i stället för stenar: AUC {num(HS['auc'], 3)}, {pfmt(HS['p'])}. H1 *håller* enligt alla fem villkoren. I klartext: jämför man en runsten med en slumpvis vald plats i samma bygd står runstenen närmare dåtidens vatten i {pc(H1['auc'])} fall av 100, och nästan två av tre stenar står inom 500 meter från vattnet, mot knappt hälften av marken.

Per landskap, med q korrigerat över de sex: AUC {num(P1['U']['auc'])} i Uppland, {num(P1['Sö']['auc'])} i Södermanland, {num(P1['Ög']['auc'])} i Östergötland, {num(P1['Sm']['auc'])} i Småland och {num(P1['Vg']['auc'])} i Västergötland, alla q < 0,01, och {num(P1['Öl']['auc'])} på Öland, q = {num(P1['Öl']['q_bh'], 3)}, där de {P1['Öl']['n_stones']} stenarna går åt samma håll men inte räcker.

Gravfälten (H3): {pc(H3['within_500_stones'])} procent av stenarna står inom 500 meter från ett registrerat gravfält, mot {pc(H3['within_500_random'])} procent av punkterna; medianen är {H3['median_stones_m']} mot {m(H3['median_random_m'])} meter, AUC {num(H3['auc'], 3)}, {pfmt(H3['p'])}. Halva A: AUC {num(H3A['auc'], 3)}, halva B: AUC {num(H3B['auc'], 3)}, platserna: AUC {num(H3S['auc'], 3)}, alla {pfmt(max(H3A['p'], H3B['p'], H3S['p']))}. H3 *håller*, i samma fem landskap som H1. I klartext: två av tre stenar står inom 500 meter från ett gravfält, mot en av fyra platser i bygden.

Dagens vatten (H2): mot vattnet år 1949 står {pc(NOW['within_500_stones'])} procent av stenarna inom 500 meter, mot {pc(NOW['within_500_random'])} procent av punkterna, AUC {num(NOW['auc'], 3)}. Skillnaden i AUC mot dåtidens vatten är {num(H2['delta_auc'], 3)}, 95 %-intervall {num(H2['ci95'][0], 3)} till {num(H2['ci95'][1], 3)}. Hela intervallet ligger över noll, så närheten är enligt planen *tydligare* mot dåtidens vatten, men skillnaden är liten. Den finns i Uppland, Södermanland, Östergötland och på Öland; i Småland och Västergötland passar dagens vatten lika bra eller något bättre.

{chart(True)}

**5.2 Planens känslighetsprov.** Alla håller för H1:

- Andra årtal: AUC mellan {num(R1A[0])} och {num(R1A[1])} för alla sex, från år 550 till år 1550, alla {pfmt(max(v['p'] for v in R1.values()))}.
- Bara havet, utan modellens sjöar: {rung(R2)}. I Östergötland, Småland och Västergötland säger provet inget, eftersom de flesta stenar och punkter där ligger mil från havet.
- Utan de {R5['n_excluded']} stenar som står i modellens vatten år 1050: {rung(R5)}.
- Den oberoende höjdmodellen: landhöjningen en meter lägre: {rung(R6['minus1'], n=False)}; lika: {rung(R6['zero'], n=False)}; en meter högre: {rung(R6['plus1'], n=False)}. Mönstret hänger alltså inte på SGU:s höjdmodell.
- Punkter inom två kilometer: AUC {num(R7['r2km']['water']['auc'], 3)}; inom tio kilometer: AUC {num(R7['r10km']['water']['auc'], 3)}.

Vatten och gravfält samtidigt, i en logistisk regression med landskapet konstant: när avståndet till vattnet halveras blir oddsen att platsen har en runsten {num(S['S1a']['or'], 2)} gånger så stora (95 %-intervall {num(S['S1a']['lo'], 2)}–{num(S['S1a']['hi'], 2)}), med avståndet till gravfälten lika; för gravfälten är oddskvoten {num(S['S1b']['or'], 2)} ({num(S['S1b']['lo'], 2)}–{num(S['S1b']['hi'], 2)}). Båda håller i båda halvorna och efter korrigering. I klartext: vattnet är inte bara ett tecken på att gravfälten ligger där, och tvärtom; gravfälten väger ungefär dubbelt så tungt.

De övriga sekundära proven håller inte: andelen inom en kilometer från vattnet är densamma för tidiga och sena stenar ({pc(S['S2']['early'])} procent), kristna markörer gör ingen skillnad ({pfmt(S['S3']['p'])}), och bro- och vägstenarna står något närmare ({S['S4']['median_bridge_m']} mot {S['S4']['median_other_m']} meter i median) men inte säkert ({pfmt(S['S4']['p'])}, q = {num(S['S4']['q_bh'], 2)}).

**5.3 Känslighetsanalyserna.** Bara stenar som står kvar enligt tre källor ({T1['n']} stenar): vattnet AUC {num(T1['water']['auc'], 3)}, gravfälten AUC {num(T1['grave']['auc'], 3)}, båda {pfmt(max(T1['water']['p'], T1['grave']['p']))}. I tilläggsplanens nio analyser håller alla steg för både vattnet och gravfälten. För vattnet:

- Halvorna: se 5.1.
- Utan ett landskap i taget: AUC mellan {num(LA1[0])} och {num(LA1[1])}, också utan Uppland, när bara {pc(L1['U']['share_kept'])} procent av stenarna är kvar ({pfmt(L1['U']['p'])}).
- Socknen som enhet ({G1['socken']['n_parishes']} socknar): {rung(G1['socken'])}.
- Socknen som slumpeffekt: oddskvot {num(MM1['or'])} när avståndet halveras (95 %-intervall {num(MM1['lo'])}–{num(MM1['hi'])}), {pfmt(MM1['p'])}; modellen konvergerade utan varningar. I klartext: också jämfört med marken i samma socken står stenarna närmare vattnet.
- En sten per säker ristare ({C['carvers']} ristare): {rung(G1['en_per_ristare'])}.
- Utan återresta stenar ({C['reerected']} bort): {rung(G1['utan_aterresta'])}.
- Utan stenar som Runor anger som flyttade ({C['moved_runor']} bort): {rung(G1['utan_flyttade_runor'])}.
- Med dagens regel för flyttade stenar ({C['not_staying_now']} bort): {rung(G1['dagens_flyttregel'])}.
- De tidiga stenarna, före 1050: {rung(G1['tidiga'])}. De sena: {rung(G1['sena'])}.

För gravfälten ligger AUC mellan {num(GA3[0])} och {num(GA3[1])} i alla steg, utan ett landskap i taget mellan {num(LA3[0])} och {num(LA3[1])}, och socknen som slumpeffekt ger oddskvoten {num(MM3['or'])} ({num(MM3['lo'])}–{num(MM3['hi'])}), {pfmt(MM3['p'])}.

Studien är fristående, så korrigeringen gäller inom planen och inte bland de samband projektet justerar gemensamt. Inga handkodade drag ingår; felkällan är modellen för vattnet (se 6).

## 6. Diskussion

**Vad fyndet säger.** De som reste runstenarna valde platser nära vattnet. Jämförelsen gäller marken i samma bygd, och sambandet finns kvar socken för socken, så det beror inte bara på att bygderna låg vid vatten. Det beror inte heller på några få landskap, platser eller ristare, inte på stenar som har flyttats eller rests upp på nytt, och inte på SGU:s höjdmodell. Det gällde både före och efter 1050. Gravfälten drar starkare, och de två sambanden är oberoende av varandra: de mest sannolika platserna för en runsten låg nära både vatten och gravfält.

**Dåtidens och dagens vatten.** Att dåtidens vatten stämmer bara lite bättre än dagens betyder inte att landhöjningen saknar betydelse. I de flesta trakter har stranden flyttat sig mindre än de hundratals meter som skiljer stenarna från punkterna (figur 2), och sjöarna ligger kvar. Modellen för år 1050 behövs främst för att fyndet inte ska vara ett resultat av dagens kust.

**Mot tidigare forskning.** Att två av tre stenar står inom 500 meter från ett gravfält stöder Klos (2009) och stämmer med att stenar i familjegrupper oftare står vid gravfält än ensamma stenar ([Kvant 2026b]({FAM})). Att vattnet finns kvar när gravfälten hålls lika ger samtidigt McLeod (2014) rätt i att gravfälten inte är hela svaret. Fyndet passar med att stenarnas text oftast vändes mot vägen ([Kvant 2026c]({VAG})): stenarna restes där människor färdades, till lands och till sjöss. Det är en tolkning; studien visar var stenarna står, inte varför.

**Svagheter, i ordning efter vikt.**

1. **Modellen för vattnet är grov.** SGU:s modell är regional, med en höjdmodell på 50 meter, tidsfel på upp till 500 år och ungefärliga sjöar; åar, bäckar och våtmarker saknas. {PO['stones_in_water_1050']} stenar hamnar i modellens vatten år 1050, där ingen sten kan ha rests. Utan dem är sambandet svagare men tydligt (AUC {num(R5['auc'], 2)}), och den oberoende höjdmodellen ger samma resultat.
2. **Riktningen var väntad.** Projektets tidigare mått visade samma sak med grövre data. Studien bekräftar ett känt mönster; den upptäcker inget nytt.
3. **Känslighetsanalyserna valdes efter huvudresultatet.** Stegen och gränserna låstes innan de räknades, men efter att planens resultat var kända.
4. **Stenarnas plats.** En sten kan ha flyttats en bit utan att det har registrerats; tre källor för flyttade stenar och en ordlista för återresta stenar ger samma resultat men fångar inte allt.
5. **Gravfälten** är olika väl inventerade i olika trakter och oftast odaterade; en del kan vara yngre eller äldre än stenarna.
6. **Öland** har för få stenar för att visa något säkert.

**Vad som skulle fälla fyndet.** Att sambandet med vattnet försvann med en finare höjdmodell, till exempel Lantmäteriets med en meters upplösning, och strandförskjutningskurvor för varje bygd, eller att stenarnas ursprungliga platser på de äldsta kartorna låg systematiskt längre från vattnet.

## 7. Slutsats

Runstenarna restes vid sin tids vatten: nästan två av tre står inom 500 meter från vattnet som det låg år 1050, mot knappt hälften av marken runt dem, och sambandet tål varje känslighetsanalys. Gravfälten drog ännu starkare, och de två sambanden är oberoende. Nästa steg är en finare höjdmodell och de äldsta kartorna.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 1 november 2026. Någon release med DOI finns ännu inte; när den görs hänvisar rapporten till den. All kod, analysplanerna och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Analysplanerna: `analysplaner/2026-10-23-strand-och-gravfalt.md`, `analysplaner/2026-10-31-strand-tillagg.md` och `analysplaner/2026-11-01-strand-trappan.md`, med kontrollsummorna i `.sha256`-filerna bredvid.
- Korpusen: fingeravtryck `d6cffd1578418f74` (låst i planen); dagens regel för flyttade stenar ur `e83202e01a5e6d27`.
- Analysen, ett steg per R-process: `utdata/strand/01_avstand.R`, `01b_marginal.R`, `02_r6.R`, `03_statistik.R`, `04_figurer.R` och känslighetsanalyserna `05_trappa.R`. Resultat i `utdata/strand/resultat.json` och `trappan.json`, stenarna i `stenar.csv`, hela redovisningen i `resultat.md`.
- SGU:s modell (`strandforskjutning_1_900.gpkg`, `strandforskjutning_1000_1900.gpkg`) och Copernicus DEM laddas ned till en cache och ingår inte i repot; kontrollsummorna står i planen.
- Kartorna: `utdata/strand/06_illustration.R` (rutan i figur 2 valdes som den 12-kilometersruta i Mälardalen med flest stenar gånger andelen mark som var vatten år 1050 men är land i dag).
- Rapporten byggs av `utdata/blogg/build/build_rapport_strand.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer.

## Referenser

- Bates, D., Mächler, M., Bolker, B. & Walker, S. 2015. Fitting linear mixed-effects models using lme4. *Journal of Statistical Software* 67 (1), s. 1–48.
- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society, Series B* 57 (1), s. 289–300.
- Copernicus DEM GLO-30. © DLR e.V. 2010–2014 och © Airbus Defence and Space GmbH 2014–2018, tillhandahållen under Copernicusprogrammet. Via AWS Open Data.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, s. 137 ff.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Kvant, V. 2026a. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Kvant, V. 2026b. Runstenarna samlas i familjegrupper vid gravfälten. Forskningsrapport. {FAM}
- Kvant, V. 2026c. Runstenarna vände texten mot vägen. Forskningsrapport. {VAG}
- Mann, H. B. & Whitney, D. R. 1947. On a test of whether one of two random variables is stochastically larger than the other. *Annals of Mathematical Statistics* 18 (1), s. 50–60.
- McLeod, S. 2014. The rediscovery of U 170: runestones, churchyards, and burial grounds in Sweden. *Journal of the North Atlantic* 25. doi:10.3721/037.006.2503
- Påsse, T. & Daniels, J. 2015. *Past shore-level and sea-level displacements*. Sveriges geologiska undersökning, Rapporter och meddelanden 137.
- Riksantikvarieämbetet. Kulturmiljöregistret (fornlämningar), via K-samsök, hämtat oktober 2026; *Runor* (runinskriftsregister), uttag 2020.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- SGU 2022. *Strandförskjutningsmodell (öppna data)*. Produktbeskrivning, version 1.0. Uppsala: Sveriges geologiska undersökning. CC BY 4.0.
- Wilcoxon, F. 1945. Individual comparisons by ranking methods. *Biometrics Bulletin* 1 (6), s. 80–83.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholms universitet.

:::box Det viktigaste i korthet
- De som reste runstenarna valde platser nära sin tids vatten, inte bara för att bygden låg vid vattnet utan också inom bygden.
- Gravfälten drog ännu starkare, och de två sambanden är oberoende: stenen stod helst där både vattnet och de döda fanns.
- Tillsammans med att texten vändes mot vägen pekar det mot stenar som restes för att ses av dem som färdades.
- Svagheten är modellen för vattnet år 1050, som är grov nära stränderna; nästa prov är en finare höjdmodell.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. Cite as: {CITE_EN}. Keywords: runestones, Viking Age, placement, shore displacement, land uplift, grave fields, spatial statistics, pre-registration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** Where the runestones were raised has long been debated: by grave fields, by roads and bridges, by farms and boundaries. Water is harder to measure, because the land has risen since the Viking Age and today's shore is not the stones' shore. The question here is whether the stones were raised closer to the water of their own time than the land around them, and whether that association remains when nearness to the grave fields is held equal.
**Material.** {m(PO['n'], True)} Viking-Age runestones that still stand in place, in Uppland, Södermanland, Östergötland, Småland, Västergötland and on Öland, and {m(PO['n_random'], True)} random points on land within five kilometres of the stones. The water of AD 1050 from the shore displacement model of the Geological Survey of Sweden (SGU), the grave fields from the Swedish National Heritage Board's register of ancient monuments.
**Method.** Pre-registered study. The distance to the nearest water is compared between stones and points with Wilcoxon's rank-sum test and the AUC, the probability that a stone stands closer than a point. Internal replication in two halves, seven sensitivity tests in the plan and nine sensitivity analyses under a locked addendum plan.
**Results.** {pc(H1['within_500_stones'])} per cent of the stones stand within 500 metres of the water of AD 1050, against {pc(H1['within_500_random'])} per cent of the points; the median distance is {H1['median_stones_m']} against {H1['median_random_m']} metres, AUC {num(H1['auc'], 2, True)}, {pfmt(H1['p'], True)}. It holds in both halves, in five of six provinces, for other years between 550 and 1550, with an independent elevation model and in every sensitivity analysis, including against the land in the same parish. The grave fields draw more strongly: {pc(H3['within_500_stones'])} against {pc(H3['within_500_random'])} per cent within 500 metres, AUC {num(H3['auc'], 2, True)}. Both associations remain when the other is held equal. The water of the time fits the stones slightly better than today's, but the difference is small.
**Conclusion.** Those who raised the runestones chose places near the water, and even more often near the grave fields, within districts that already lay by water. The main weakness is that the model of the water of AD 1050 is coarse: {PO['stones_in_water_1050']} of the stones fall in the model's water.

## 1. Introduction

Gunnar Ekholm (1950) asked where the runestones were raised. Torun Zachrisson (1998) has linked them to farm, boundary and grave field, Lydia Klos (2009) has argued that most were raised at grave fields, and Shane McLeod (2014) has objected that this overstates the grave fields at the expense of other places, such as the roads. The bridge stones, which tell of bridges and causeways over water and wet ground, show that water belonged to the stones' setting.

Measuring the nearness to water is hard. The land has risen since the Viking Age, in the Mälaren valley by about five metres, so a stone that stood by a bay may now stand on dry land, and a stone by today's shore may have stood far from the water. SGU's shore displacement model (SGU 2022, after Påsse & Daniels 2015) gives an open model for the whole country of where the water lay at different times.

We know of no study that has measured the distance to the water of the stones' own time for the whole Swedish material, with a model of shore displacement, only stones that still stand in place, and a comparison with the land in the same district. The aim is to do so and test whether the association remains when nearness to the grave fields is held equal.

## 2. Pre-registration: hypothesis and plan

The hypotheses, measures and rules of interpretation were written down in an analysis plan on 23 October 2026, before any distance had been computed. The plan has the SHA-256 checksum `{SHA['2026-10-23-strand-och-gravfalt']}…` and was committed to version control the same evening. Before the lock, only the data sources had been fetched, the layers listed, the number of stones per province counted and the mid-years of the style groups compiled to choose the year (median 1035). A test run of the script the same evening, after the plan had its checksum but before the commit, printed only its progress and no figures. The statistics were first run on 31 October.

The direction was expected. The project's earlier measure, with a coarse land uplift and with moved stones, had already shown that the stones stand closer to water and grave fields than the land around them. The study therefore tests whether a known pattern holds with better data, not a new one.

The plan's hypotheses, verbatim (translated): **H1 (primary): the stones stand closer to the water of AD 1050 than the random points.** **H2: the nearness is clearer relative to the water of the time than to today's.** **H3: the grave fields, on the same selection** (the stones stand closer to registered grave fields than the random points). H1 *holds* if five conditions are met: p below 0.05 and AUC above 0.5 overall, the same in both halves, the same when stones within 200 metres of each other are merged into one place, the same for four other years within 200 years (750, 950, 1150 and 1250), and the same with only the sea, without the model's lakes. H3 holds if it holds overall, in both halves and for the places. H2 is called clearer only if the whole 95 % interval for the difference lies above zero.

Two addenda were locked later, both before they were computed. On 31 October (SHA-256 `{SHA['2026-10-31-strand-tillagg']}…`), before the statistics were run: H1 and H3 are also tested on the stones that stand in place according to three sources, because the rule for moved stones had been corrected after the plan was locked. On 1 November (SHA-256 `{SHA['2026-11-01-strand-trappan']}…`), when the plan's results were known: nine fixed sensitivity analyses for distances, corresponding to those the project makes for other findings. They are confirmatory in the sense that the steps and limits were locked before they were computed, but they were chosen after the main result was known.

## 3. Material

- **The stones.** Swedish Viking-Age runestones in the Scandinavian Runic-text Database (Rundata), in the version locked in the plan. Of them we took those that have coordinates and have not been moved: Rundata's placement or site is not church, churchyard, wall, museum or collection. Only provinces with at least 20 such stones are tested: Uppland ({P1['U']['n_stones']}), Södermanland ({P1['Sö']['n_stones']}), Östergötland ({P1['Ög']['n_stones']}), Småland ({P1['Sm']['n_stones']}), Västergötland ({P1['Vg']['n_stones']}) and Öland ({P1['Öl']['n_stones']}), {m(PO['n'], True)} in all. The {sum(PO['other_provinces_not_tested'].values())} stones in the other provinces are not tested. Runestones only.
- **The water.** SGU's shore displacement model, open data version 1.0 (2022, CC BY 4.0). It is built on shore displacement curves across the country, a model of land uplift and an elevation model with a resolution of 50 metres. The water of AD 1050 is the model's sea and lakes in the slice 900 years before 1950; today's water is the slice for 1949. The distances are computed on a grid of 25-metre cells.
- **The grave fields.** The Swedish National Heritage Board's register of ancient monuments via K-samsök, retrieved on 12 October 2026: {m(PO['n_gravfalt'], True)} registered grave fields with coordinates.
- **The independent elevation model.** Copernicus DEM GLO-30 (about 30 metres), with the province's land uplift since the Viking Age as the height limit.
- **The dating** by the stone's ornamental style (Gräslund 2006): {PO['n_dated']} of the stones.
- **The halves** are the project's fixed division parish by parish: {PO['halves']['A']} and {PO['halves']['B']} stones.

{FIG1_EN}

## 4. Method

**4.1 The measure and the comparison.** For every stone and every point the distance is computed to the nearest water of AD 1050, to today's water and to the nearest grave field; a point in the water gets the distance zero. The comparison is a null model: for each province ten random points per stone are drawn, uniformly within five kilometres of the province's stones, and only points that are land both in AD 1050 and in 1949 are kept. The points thus lie in the districts where stones were raised, so the test concerns where in the district the stone stands, not where the districts lie. Stones and points are compared with Wilcoxon's rank-sum test (Wilcoxon 1945; Mann & Whitney 1947), one-sided. The effect is given as the medians, the share within 500 metres and the AUC, the probability that a randomly chosen stone stands closer than a randomly chosen point (0.5 means no difference). Figure 2 shows the measurement in one district.

{FIG2_EN}

**4.2 Correction and replication.** Each hypothesis is tested in each half on its own. The provinces are tested separately with Benjamini–Hochberg correction (Benjamini & Hochberg 1995) over the six, and the secondary tests likewise over the five. The difference between the water of the time and today's (H2) gets a 95 % interval from 2,000 bootstrap samples in which the stones are drawn place by place.

**4.3 The sensitivity analyses.** The plan's seven tests, the addendum's test and the nine steps of the addendum plan are given with their results in 5.2 and 5.3. The parish as a random effect is a logistic regression (Bates et al. 2015) in which the points get the parish of the nearest stone. When stones are removed, the points that belong to them are removed too. A step holds when the AUC is above 0.5 and p below 0.05; without one province at a time, significance is required only where at least two thirds of the stones remain.

**4.4 Deviations from the plan.** The statistics were run eight days after the distances were computed, after the addendum for moved stones; the plan's tests are unchanged. The {m(PO['distances_at_tile_margin'], True)} distances that reached the edge of the computation tiles, nearly all for the sea alone far inland, were recomputed on a grid of 100-metre cells over the whole province; the plan gives no cell size. The sensitivity analyses of the addendum plan were added after the plan's results were known (see 2). Otherwise none.

## 5. Results

**5.1 The water of AD 1050 (H1), the grave fields (H3) and today's water (H2).** Of the {m(PO['n'], True)} stones, {pc(H1['within_500_stones'])} per cent stand within 500 metres of the water of AD 1050, against {pc(H1['within_500_random'])} per cent of the {m(PO['n_random'], True)} points; within one kilometre {pc(H1['within_1000_stones'])} against {pc(H1['within_1000_random'])} per cent. The median distance is {H1['median_stones_m']} against {H1['median_random_m']} metres, AUC {num(H1['auc'], 3, True)}, {pfmt(H1['p'], True)}. Half A ({HA['n_stones']} stones in {HA['n_parishes']} parishes): AUC {num(HA['auc'], 3, True)}, {pfmt(HA['p'], True)}. Half B ({HB['n_stones']} stones in {HB['n_parishes']} parishes): AUC {num(HB['auc'], 3, True)}, {pfmt(HB['p'], True)}. With {HS['n_sites']} places instead of stones: AUC {num(HS['auc'], 3, True)}, {pfmt(HS['p'], True)}. H1 *holds* on all five conditions. In plain words: compare a runestone with a randomly chosen place in the same district, and the runestone stands closer to the water of its time in {pc(H1['auc'])} cases out of 100; almost two in three stones stand within 500 metres of the water, against fewer than half of the land.

By province, with q corrected over the six: AUC {num(P1['U']['auc'], 2, True)} in Uppland, {num(P1['Sö']['auc'], 2, True)} in Södermanland, {num(P1['Ög']['auc'], 2, True)} in Östergötland, {num(P1['Sm']['auc'], 2, True)} in Småland and {num(P1['Vg']['auc'], 2, True)} in Västergötland, all q < 0.01, and {num(P1['Öl']['auc'], 2, True)} on Öland, q = {num(P1['Öl']['q_bh'], 3, True)}, where the {P1['Öl']['n_stones']} stones go the same way but are not enough.

The grave fields (H3): {pc(H3['within_500_stones'])} per cent of the stones stand within 500 metres of a registered grave field, against {pc(H3['within_500_random'])} per cent of the points; the median is {H3['median_stones_m']} against {m(H3['median_random_m'], True)} metres, AUC {num(H3['auc'], 3, True)}, {pfmt(H3['p'], True)}. Half A: AUC {num(H3A['auc'], 3, True)}, half B: AUC {num(H3B['auc'], 3, True)}, the places: AUC {num(H3S['auc'], 3, True)}, all {pfmt(max(H3A['p'], H3B['p'], H3S['p']), True)}. H3 *holds*, in the same five provinces as H1. In plain words: two in three stones stand within 500 metres of a grave field, against one in four places in the district.

Today's water (H2): relative to the water of 1949, {pc(NOW['within_500_stones'])} per cent of the stones stand within 500 metres, against {pc(NOW['within_500_random'])} per cent of the points, AUC {num(NOW['auc'], 3, True)}. The difference in AUC from the water of the time is {num(H2['delta_auc'], 3, True)}, 95 % interval {num(H2['ci95'][0], 3, True)} to {num(H2['ci95'][1], 3, True)}. The whole interval lies above zero, so by the plan the nearness is *clearer* relative to the water of the time, but the difference is small. It shows in Uppland, Södermanland, Östergötland and on Öland; in Småland and Västergötland today's water fits as well or slightly better.

{chart(False)}

**5.2 The plan's sensitivity tests.** All hold for H1:

- Other years: AUC between {num(R1A[0], 2, True)} and {num(R1A[1], 2, True)} for all six, from AD 550 to AD 1550, all {pfmt(max(v['p'] for v in R1.values()), True)}.
- Only the sea, without the model's lakes: {rung(R2, True)}. In Östergötland, Småland and Västergötland the test says nothing, since most stones and points there lie tens of kilometres from the sea.
- Without the {R5['n_excluded']} stones that stand in the model's water of AD 1050: {rung(R5, True)}.
- The independent elevation model: land uplift one metre lower: {rung(R6['minus1'], True, False)}; equal: {rung(R6['zero'], True, False)}; one metre higher: {rung(R6['plus1'], True, False)}. The pattern thus does not depend on SGU's elevation model.
- Points within two kilometres: AUC {num(R7['r2km']['water']['auc'], 3, True)}; within ten kilometres: AUC {num(R7['r10km']['water']['auc'], 3, True)}.

Water and grave fields together, in a logistic regression with the province held constant: when the distance to the water halves, the odds that the place has a runestone become {num(S['S1a']['or'], 2, True)} times as large (95 % interval {num(S['S1a']['lo'], 2, True)}–{num(S['S1a']['hi'], 2, True)}), with the distance to the grave fields equal; for the grave fields the odds ratio is {num(S['S1b']['or'], 2, True)} ({num(S['S1b']['lo'], 2, True)}–{num(S['S1b']['hi'], 2, True)}). Both hold in both halves and after correction. In plain words: the water is not merely a sign that the grave fields lie there, nor the other way round; the grave fields weigh about twice as much.

The other secondary tests do not hold: the share within one kilometre of the water is the same for early and late stones ({pc(S['S2']['early'])} per cent), Christian markers make no difference ({pfmt(S['S3']['p'], True)}), and the bridge and road stones stand somewhat closer ({S['S4']['median_bridge_m']} against {S['S4']['median_other_m']} metres in median) but not reliably ({pfmt(S['S4']['p'], True)}, q = {num(S['S4']['q_bh'], 2, True)}).

**5.3 The sensitivity analyses.** Only stones that stand in place according to three sources ({T1['n']} stones): water AUC {num(T1['water']['auc'], 3, True)}, grave fields AUC {num(T1['grave']['auc'], 3, True)}, both {pfmt(max(T1['water']['p'], T1['grave']['p']), True)}. In the nine analyses of the addendum plan every step holds for both the water and the grave fields. For the water:

- The halves: see 5.1.
- Without one province at a time: AUC between {num(LA1[0], 2, True)} and {num(LA1[1], 2, True)}, also without Uppland, when only {pc(L1['U']['share_kept'])} per cent of the stones remain ({pfmt(L1['U']['p'], True)}).
- The parish as the unit ({G1['socken']['n_parishes']} parishes): {rung(G1['socken'], True)}.
- The parish as a random effect: odds ratio {num(MM1['or'], 2, True)} when the distance halves (95 % interval {num(MM1['lo'], 2, True)}–{num(MM1['hi'], 2, True)}), {pfmt(MM1['p'], True)}; the model converged without warnings. In plain words: also compared with the land in the same parish, the stones stand closer to the water.
- One stone per certain carver ({C['carvers']} carvers): {rung(G1['en_per_ristare'], True)}.
- Without re-erected stones ({C['reerected']} removed): {rung(G1['utan_aterresta'], True)}.
- Without stones that Runor gives as moved ({C['moved_runor']} removed): {rung(G1['utan_flyttade_runor'], True)}.
- With today's rule for moved stones ({C['not_staying_now']} removed): {rung(G1['dagens_flyttregel'], True)}.
- The early stones, before AD 1050: {rung(G1['tidiga'], True)}. The late: {rung(G1['sena'], True)}.

For the grave fields the AUC lies between {num(GA3[0], 2, True)} and {num(GA3[1], 2, True)} in every step, without one province at a time between {num(LA3[0], 2, True)} and {num(LA3[1], 2, True)}, and the parish as a random effect gives the odds ratio {num(MM3['or'], 2, True)} ({num(MM3['lo'], 2, True)}–{num(MM3['hi'], 2, True)}), {pfmt(MM3['p'], True)}.

The study stands alone, so the correction applies within the plan and not among the associations the project adjusts jointly. No hand-coded traits are involved; the source of error is the model of the water (see 6).

## 6. Discussion

**What the finding says.** Those who raised the runestones chose places near the water. The comparison concerns the land in the same district, and the association remains parish by parish, so it is not only because the districts lay by water. Nor does it depend on a few provinces, places or carvers, on stones that have been moved or re-erected, or on SGU's elevation model. It held both before and after AD 1050. The grave fields draw more strongly, and the two associations are independent of each other: the most likely places for a runestone lay near both water and grave fields.

**The water of the time and today's.** That the water of the time fits only slightly better than today's does not mean that the land uplift is unimportant. In most districts the shore has moved less than the hundreds of metres that separate the stones from the points (figure 2), and the lakes remain. The model for AD 1050 is needed above all so that the finding is not an artefact of today's coast.

**Against earlier research.** That two in three stones stand within 500 metres of a grave field supports Klos (2009) and agrees with stones in family groups standing at grave fields more often than single stones ([Kvant 2026b]({FAM})). That the water remains when the grave fields are held equal at the same time bears out McLeod (2014) that the grave fields are not the whole answer. The finding fits with the stones' text being turned mostly towards the road ([Kvant 2026c]({VAG})): the stones were raised where people travelled, by land and by water. That is an interpretation; the study shows where the stones stand, not why.

**Weaknesses, in order of importance.**

1. **The model of the water is coarse.** SGU's model is regional, with an elevation model of 50 metres, time errors of up to 500 years and approximate lakes; rivers, streams and wetlands are missing. {PO['stones_in_water_1050']} stones fall in the model's water of AD 1050, where no stone can have been raised. Without them the association is weaker but clear (AUC {num(R5['auc'], 2, True)}), and the independent elevation model gives the same result.
2. **The direction was expected.** The project's earlier measure showed the same with coarser data. The study confirms a known pattern; it discovers nothing new.
3. **The sensitivity analyses were chosen after the main result.** The steps and limits were locked before they were computed, but after the plan's results were known.
4. **The stones' places.** A stone may have been moved a little without it being recorded. Three sources for moved stones and a word list for re-erected stones give the same result, but do not catch everything.
5. **The grave fields** are unevenly surveyed in different districts and mostly undated; some may be younger or older than the stones.
6. **Öland** has too few stones to show anything for certain.

**What would overturn the finding.** If the association with water disappeared with a finer elevation model, for example Lantmäteriet's at one metre's resolution, and shore displacement curves for each district, or if the stones' original places on the oldest maps lay systematically farther from the water.

## 7. Conclusion

The runestones were raised by the water of their time: almost two in three stand within 500 metres of the water as it lay in AD 1050, against fewer than half of the land around them, and the association withstands every sensitivity analysis. The grave fields drew even more strongly, and the two associations are independent. The next step is a finer elevation model and the oldest maps.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 1 November 2026. No release with a DOI exists yet; when one is made, the report will refer to it. All code, the analysis plans and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The analysis plans: `analysplaner/2026-10-23-strand-och-gravfalt.md`, `analysplaner/2026-10-31-strand-tillagg.md` and `analysplaner/2026-11-01-strand-trappan.md`, with their checksums in the `.sha256` files beside them.
- The corpus: fingerprint `d6cffd1578418f74` (locked in the plan); today's rule for moved stones from `e83202e01a5e6d27`.
- The analysis, one step per R process: `utdata/strand/01_avstand.R`, `01b_marginal.R`, `02_r6.R`, `03_statistik.R`, `04_figurer.R` and the sensitivity analyses `05_trappa.R`. Results in `utdata/strand/resultat.json` and `trappan.json`, the stones in `stenar.csv`, the full account in `resultat.md` (Swedish).
- SGU's model (`strandforskjutning_1_900.gpkg`, `strandforskjutning_1000_1900.gpkg`) and Copernicus DEM are downloaded to a cache and are not in the repository; their checksums are in the plan.
- The maps: `utdata/strand/06_illustration.R` (the window in figure 2 was chosen as the 12-kilometre window in the Mälaren region with the most stones times the share of land that was water in AD 1050 but is land today).
- The report is built by `utdata/blogg/build/build_rapport_strand.py`, which reads every number from the result files and stops if anything disagrees.

## References

- Bates, D., Mächler, M., Bolker, B. & Walker, S. 2015. Fitting linear mixed-effects models using lme4. *Journal of Statistical Software* 67 (1), pp. 1–48.
- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society, Series B* 57 (1), pp. 289–300.
- Copernicus DEM GLO-30. © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under the Copernicus programme. Via AWS Open Data.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, pp. 137 ff.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Kvant, V. 2026a. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Kvant, V. 2026b. Runestones gather in family groups by the grave fields. Research report. {FAM.replace('vitkirunor.se/', 'vitkirunor.se/en/')}
- Kvant, V. 2026c. The runestones turned their text towards the road. Research report. {VAG.replace('vitkirunor.se/', 'vitkirunor.se/en/')}
- Mann, H. B. & Whitney, D. R. 1947. On a test of whether one of two random variables is stochastically larger than the other. *Annals of Mathematical Statistics* 18 (1), pp. 50–60.
- McLeod, S. 2014. The rediscovery of U 170: runestones, churchyards, and burial grounds in Sweden. *Journal of the North Atlantic* 25. doi:10.3721/037.006.2503
- Påsse, T. & Daniels, J. 2015. *Past shore-level and sea-level displacements*. Geological Survey of Sweden, Rapporter och meddelanden 137.
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- SGU 2022. *Strandförskjutningsmodell (öppna data)* [Shore displacement model, open data]. Product description, version 1.0. Uppsala: Geological Survey of Sweden. CC BY 4.0.
- Swedish National Heritage Board (Riksantikvarieämbetet). The register of ancient monuments (Kulturmiljöregistret), via K-samsök, retrieved October 2026; *Runor* (register of runic inscriptions), 2020 extract.
- Wilcoxon, F. 1945. Individual comparisons by ranking methods. *Biometrics Bulletin* 1 (6), pp. 80–83.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholm University.

:::box The essentials
- Those who raised the runestones chose places near the water of their time, not only because the district lay by the water but also within the district.
- The grave fields drew even more strongly, and the two associations are independent: the stone stood best where both the water and the dead were.
- Together with the text being turned towards the road, it points to stones raised to be seen by those who travelled.
- The weakness is the model of the water of AD 1050, which is coarse near the shores; the next test is a finer elevation model.
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
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion 1, 2026-11-01. Tidslinje: ")
assert body_en.split("\n", 1)[0].startswith("*Viktor Kvant, independent researcher. Fully tested finding. Report version 1, 2026-11-01. Timeline: ")

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Geografi"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_strand.json")
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
                 "topic": "Rapport|strand", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
