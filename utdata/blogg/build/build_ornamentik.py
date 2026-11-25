"""Artikeln "Rundjuren som bara finns kvar på papper" (populärvetenskap, sv + en): ornamentkodningen 2026-11-24–25.

Bygger på utdata/nya_ristare/resultat.md §§ 10–12 (kodningen ur SRI:s planscher, ristargrupperna, källkontrollen av
1600–1700-talets teckningar, de förlorade stenarna) och utdata/graslund/resultat.md (Gräslund 1). Låsta planer:
analysplaner/2026-11-24-nya-ristare-ornamentik.md, 2026-11-25-ornamentik-kallkontroll-teckningar.md och
2026-11-25-graslund-1-stilgrupper.md. Varje tal i texten räknas här ur utfallsfilerna (och cachens koder) och låses
med assert.

Bilder: två träsnitt ur Bautil (Umeå universitetsbiblioteks exemplar, "fritt från kända upphovsrättsliga
restriktioner"), utskurna och förminskade i utdata/blogg/figurer/ornamentik/. SRI:s planscher är skyddade och visas inte.
    ../../../.venv/bin/python build_ornamentik.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402
from utdata.nya_ristare.ornamentik.m2 import consensus  # noqa: E402
from utdata.nya_ristare.ornamentik.overens import by_stone  # noqa: E402

ORN = os.path.join(ROOT, "utdata", "nya_ristare", "ornamentik")
CACHE = os.path.join(ROOT, "data", "cache", "hander", "ornamentik")
J = lambda *p: json.load(open(os.path.join(*p), encoding="utf-8"))  # noqa: E731


def pc(x):
    """Procent avrundat som i resultat.md (halvor uppåt)."""
    return int(100 * x + 0.5)


def kv(x, sv=True):
    s = f"{x:.2f}"
    return s.replace(".", ",") if sv else s


# ---- kodningen ur planscherna (resultat.md § 10) -------------------------------------------------------------------
M2 = J(ORN, "m2_utveckling.json")
F = M2["fält"]
N_KODAD = M2["stenar_med_kod"]
assert N_KODAD == 981
assert [F[f]["kappa"] for f in ("djurhuvud", "huvud_vy", "oga", "koppel")] == [0.95, 0.93, 0.92, 0.91]
LAG = [F[f]["kappa"] for f in ("lappflik", "flatverk", "nackflik", "fotter", "svans")]
assert (min(LAG), max(LAG)) == (0.72, 0.80)
TACK = [F[f]["tackning"] for f in ("djurhuvud", "antal_djur", "huvud_vy", "oga", "nackflik", "lappflik", "svans")]
assert (min(TACK), max(TACK)) == (0.35, 0.62)  # "en tredjedel till drygt hälften"
N_PLANSCH, N_KORPUS, N_UTAN_BILD = 1170, 2314, 64  # resultat.md § 10 och planen (bildtexterna i SRI:s textlager)
RES = open(os.path.join(ROOT, "utdata", "nya_ristare", "resultat.md"), encoding="utf-8").read()
assert "1 170 stenar" in RES and "64 stenar hade ingen användbar bild" in RES
assert "2 314" in open(os.path.join(ROOT, "analysplaner", "2026-11-24-nya-ristare-ornamentik.md"), encoding="utf-8").read()

# ---- ristargrupperna (§ 10, slutprov 3) ---------------------------------------------------------------------------
S3 = J(ORN, "slutprov3.json")
assert M2["G1"]["håller"] and M2["G1"]["grupper"] == 10
O1 = S3["O1"]
assert (O1["grupper"], O1["grupper"] - O1["med_skillnad"], O1["bättre"], O1["sämre"]) == (25, 19, 2, 4) and not O1["håller"] and S3["O2"]["håller"]
assert "19 grupper är oförändrade, 2 blev bättre och 4 sämre" in RES and "Bara O2 höll" in RES

# ---- Gräslund 1 -----------------------------------------------------------------------------------------------------
G = J(ROOT, "utdata", "graslund", "graslund1.json")
F1, F2, F3, F4 = G["F1"], G["F2"], G["F3"], G["F4"]
assert F1["stenar"] == 620 and F1["H1_håller"] and F1["p"] == 0.001 and F2["H2_håller"] and F2["p"] == 0.001
assert (pc(F1["träffsäkerhet"]), pc(F1["vanligaste_gruppen"])) == (62, 26)
STYLES = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
CONF = F1["förväxlingar"]
N_STIL = {s: sum(CONF[s].values()) for s in STYLES}
HIT = {s: CONF[s].get(s, 0) / N_STIL[s] for s in STYLES}
assert {s: pc(HIT[s]) for s in STYLES} == {"RAK": 92, "Fp": 63, "Pr1": 32, "Pr2": 41, "Pr3": 22, "Pr4": 84, "Pr5": 0}
assert max(CONF, key=lambda s: N_STIL[s]) == "Pr4"  # den vanligaste gruppen
assert N_STIL["Pr5"] - CONF["Pr5"].get("Pr4", 0) == 4  # "alla utom fyra blir Pr4"
assert (F2["fel_inom_Pr"], F2["avstånd"]["1"], F2["avstånd"]["2"], F2["avstånd"]["3"]) == (158, 131, 24, 3)
assert (pc(F2["andel_till_granne"]), pc(F2["omblandning_medel"])) == (83, 59)
assert F3["k"] == 3
K = {c["stenar"]: c["rundata"] for c in F3["klasser"]}
assert sorted(K) == [134, 191, 295]
assert (K[191]["RAK"], K[191]["Fp"]) == (141, 33)
assert (K[134]["Fp"], K[134]["Pr2"], K[134]["Pr1"], K[134]["Pr3"]) == (56, 28, 16, 15)
assert (K[295]["Pr4"], K[295]["Pr3"]) == (144, 71)
assert (pc(F4["inom_uppland_cv"]), pc(F4["Sö"]["träffsäkerhet"])) == (59, 41)
SO = F4["Sö"]["per_grupp"]
assert (pc(SO["RAK"]), pc(SO["Fp"]), pc(SO["Pr3"])) == (88, 35, 18)

# Utforskande (resultat.md "varför faller finindelningen?"): räknat på nytt ur koderna och stenarna i provet
OC = J(CACHE, "orn_koder.json")
ROWS = list(csv.DictReader(open(os.path.join(ROOT, "utdata", "graslund", "stil_sannolikhet.csv"), encoding="utf-8")))
assert len(ROWS) == 620


def saknas(f, g):
    rs = [r for r in ROWS if r["rundata"] == g]
    return sum(1 for r in rs if f not in OC.get(r["signum"], {})), len(rs)


NACK = [saknas("nackflik", g)[0] / saknas("nackflik", g)[1] for g in ("Pr2", "Pr3", "Pr4", "Pr5")]
LAPP = [saknas("lappflik", g)[0] / saknas("lappflik", g)[1] for g in ("Pr2", "Pr3", "Pr4", "Pr5")]
assert (pc(min(NACK)), pc(max(NACK)), pc(min(LAPP)), pc(max(LAPP))) == (75, 91, 84, 90)
assert saknas("nackflik", "Pr4") == (146, 160)
FPV = Counter(OC[r["signum"]]["huvud_vy"] for r in ROWS if r["rundata"] == "Fp" and "huvud_vy" in OC.get(r["signum"], {}))
assert (FPV["uppifran"], sum(FPV.values())) == (32, 52)

# ---- källkontrollen av teckningarna (§ 11) --------------------------------------------------------------------------
KK = J(ORN, "kallkontroll.json")
TP = KK["teckning_mot_plansch"]["alla"]
N_TECKN = KK["teckningar"]
PT = KK["per_typ"]
assert N_TECKN == 129 and (PT["bautil"], PT["rhezelius"], PT["peringskiold"], PT["ovrig"]) == (37, 37, 28, 27)
KT = {f: TP[f]["kappa"] for f in TP}
assert (KT["djurhuvud"], KT["huvud_vy"], KT["nackflik"], KT["koppel"], KT["kors"], KT["flatverk"], KT["antal_djur"]) == \
    (0.86, 0.83, 0.88, 0.86, 0.81, 0.74, 0.73)
assert (KT["svans"], KT["oga"], KT["lappflik"], KT["fotter"]) == (0.60, 0.57, 0.30, 0.0)
assert TP["lappflik"]["jämförbara"] == 16 and TP["nackflik"]["jämförbara"] == 19
BT = KK["teckning_mot_plansch"]["bautil"]["djurhuvud"]
assert (BT["jämförbara"], BT["lika"]) == (17, 1.0)
USE = KK["fält_som_får_läsas"]
assert all("lappflik" not in v and "fotter" not in v for v in USE.values())
assert all(f in USE["bautil"] for f in ("djurhuvud", "huvud_vy", "nackflik", "koppel", "svans", "oga", "kors"))
# Hur många av jämförelserna hade en flik alls (teckningens och planschens konsensus, räknat på nytt)
_runs = J(CACHE, "kodning_kallkontroll.json")
_draw = defaultdict(dict)
for r in _runs:
    if r["batch"].startswith("t"):
        for s in r["stenar"] or []:
            _draw[s["signum"].strip()][r["coder"]] = s
DC = consensus(_draw)
assert len(DC) <= N_TECKN


def par(f):
    return [(DC[s][f], OC[s][f]) for s in DC if s in OC and f in DC[s] and f in OC[s]]


NP = par("nackflik")
NP_LIKA = sum(a == b for a, b in NP)
NP_FLIK = sum(1 for a, b in NP if a != "ingen" or b != "ingen")
LP_FLIK = sum(1 for a, b in par("lappflik") if a != "ingen" or b != "ingen")
assert (len(NP), NP_LIKA, NP_FLIK, LP_FLIK) == (19, 18, 5, 2)
FOT = par("fotter")
assert (len(FOT), sum(1 for a, b in FOT if a == b == "inga")) == (39, 38)
# U 1154 (bevarad, Bautil 659): teckning och plansch lika i alla jämförbara fält
U1154 = [f for f in M2["godkända_fält"] if f in DC["U 1154"] and f in OC["U 1154"]]
assert len(U1154) == 9 and all(DC["U 1154"][f] == OC["U 1154"][f] for f in U1154) and DC["U 1154"]["huvud_vy"] == "uppifran"

# ---- de förlorade stenarna (§ 12) ------------------------------------------------------------------------------------
FB = {s["sig"] for b in J(CACHE, "forlorade_batcher.json") for s in b["stones"]}
LOST_READ = consensus(by_stone(os.path.join(CACHE, "kodning_forlorade.json")))
FL = J(CACHE, "orn_koder_forlorade.json")
KALLA = Counter(v["källa"] for v in FL.values())
assert (len(FB), len(LOST_READ), len(FL), sum(1 for v in FL.values() if len(v["koder"]) >= 3)) == (200, 196, 185, 167)
assert (KALLA["Bautil"], KALLA["Peringskiöld"], KALLA["Rhezelius"], KALLA["SRI-text"]) == (135, 24, 13, 13)
assert all("lappflik" not in v["koder"] and "fotter" not in v["koder"] for v in FL.values())
import pandas as pd  # noqa: E402

CORP = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"), low_memory=False).set_index("signum")
LANDSK = Counter(CORP.loc[s, "province"] for s in FL)
assert (LANDSK["U"], LANDSK["Sö"], LANDSK["Sm"]) == (128, 17, 16)
assert all(CORP.loc[s, "lost"] == 1 for s in FL)
N_UTAN_STIL = int(CORP.loc[list(FL), "style"].isna().sum())
assert N_UTAN_STIL == 135
N_FORLORADE_KORPUS = int((CORP["lost"] == 1).sum())
assert N_FORLORADE_KORPUS == 415
U16 = FL["U 16"]
assert U16["källa"] == "Bautil" and U16["koder"] == {
    "djurhuvud": "ja", "antal_djur": "1", "huvud_vy": "profil", "oga": "rund", "nackflik": "spiral", "svans": "spiral",
    "koppel": "ja", "flatverk": "inget", "fyrfota": "nej", "orm_extra": "nej", "kors": "ja"}
assert pd.isna(CORP.loc["U 16", "style"]) and CORP.loc["U 16", "parish"] == "Ekerö sn"
assert CORP.loc["U 1154", "lost"] == 0 and CORP.loc["U 1154", "style"] == "Fp" and CORP.loc["U 1154", "parish"] == "Simtuna sn"
assert CORP.loc["U 1154", "carver"] == "Erik" and CORP.loc["U 1154", "carvers_uncertain"] == 0
N_STILGRUPP = int(CORP["style"].isin(STYLES).sum())
assert 1000 < N_STILGRUPP < 1100  # "drygt tusen"
DAT = {s: (int(CORP.loc[CORP["style"] == s, "style_from"].iloc[0]), int(CORP.loc[CORP["style"] == s, "style_to"].iloc[0]))
       for s in ("RAK", "Pr5")}
assert DAT == {"RAK": (980, 1015), "Pr5": (1100, 1130)}

# ---- bilderna: två Bautilträsnitt (Umeå UB) ---------------------------------------------------------------------------
TECKN = J(ROOT, "data", "cache", "hander", "plansch", "teckningar.json")
assert "fritt från kända upphovsrättsliga restriktioner" in TECKN["_källor"]["Bautil"]
for sig, nr in (("U 16", 279), ("U 1154", 659)):
    assert any(x["källa"] == "Bautil" and x["bautil_nr"] == nr and x.get("fil", "").endswith(f"_bautil_{nr}.jpg") for x in TECKN[sig])
FIG = {}
for k in ("u16_bautil_279", "u1154_bautil_659"):
    FIG[k] = blog_figures.freeze(open(os.path.join(ROOT, "utdata", "blogg", "figurer", "ornamentik", f"{k}.png"), "rb").read())


def chart(sv):
    namn = {"RAK": ("RAK – raka bandändar", "RAK – straight band ends"), "Fp": ("Fp – huvud ovanifrån", "Fp – head seen from above"),
            "Pr1": ("Pr1 – profil", "Pr1 – profile"), "Pr2": ("Pr2", "Pr2"), "Pr3": ("Pr3", "Pr3"), "Pr4": ("Pr4", "Pr4"), "Pr5": ("Pr5", "Pr5")}
    rows = [":::chart Stenar där rundjurets drag pekar ut Rundatas stilgrupp, procent" if sv
            else ":::chart Stones where the rune animal's features point to Rundata's style group, percent"]
    rows.append("# Per stilgrupp, i Gräslunds ordning" if sv else "# Per style group, in Gräslund's order")
    for s in STYLES:
        rows.append(f"{namn[s][0 if sv else 1]} | {pc(HIT[s])} | {N_STIL[s]} {'stenar' if sv else 'stones'}")
    rows.append("# Alla stenar" if sv else "# All stones")
    rows.append(f"+{'Rundjurets drag' if sv else 'The animal’s features'} | {pc(F1['träffsäkerhet'])} | {F1['stenar']} {'stenar' if sv else 'stones'}")
    rows.append(f"{'Gissa alltid Pr4' if sv else 'Always guess Pr4'} | {pc(F1['vanligaste_gruppen'])} | –")
    rows.append("Korsvaliderat, grupperat på socken; provet låstes i förväg. Diagram: Vitki, ur kodningen av SRI:s planscher och Rundata 3.1."
                if sv else "Cross-validated, grouped by parish; the test was locked in advance. Chart: Vitki, from the coding of the SRI plates and Rundata 3.1.")
    return "\n".join(rows) + "\n:::"


BAUTIL_SV = "Umeå universitetsbiblioteks exemplar (Digitala samlingar), fritt från kända upphovsrättsliga restriktioner"
BAUTIL_EN = "Umeå University Library copy (Digital collections), free of known copyright restrictions"

SLUG = "rundjuren-som-bara-finns-kvar-pa-papper"
title = "Rundjuren som bara finns kvar på papper"
title_en = "The rune animals that survive only on paper"
summary = (f"{len(FL)} försvunna runstenar har nu fått rundjurets drag kodade, ur träsnitt och teckningar från 1600- och "
           "1700-talen. Först prövade vi om tecknarna gick att lita på, och om dragen bär Anne-Sofie Gräslunds stilgrupper. "
           "Huvudlinjerna håller.")
summary_en = (f"{len(FL)} lost runestones now have their rune animal's features coded, from woodcuts and drawings of the 17th "
              "and 18th centuries. First we tested whether the draughtsmen can be trusted, and whether the features carry "
              "Anne-Sofie Gräslund's style groups. The main lines hold.")

body = f"""Väster om prästgården i Ekerö socken stod en gång en runsten som i dag heter U 16. Den finns inte längre. Det som finns är ett träsnitt, nummer 279 i boken *Bautil*, skuret på 1600-talet och tryckt 1750. På träsnittet ringlar ett rundjur längs stenens kant. Huvudet är sett från sidan, med ett runt öga och en flik som rullar upp sig i nacken. Svansen slutar i en spiral, och nedtill binder en ögla ihop bandets två delar. Ovanför står ett kors.

![U 16 i Bautil]({FIG['u16_bautil_279']})
Träsnitt nummer 279 i Johan Göranssons *Bautil* (1750), med bildtexten ”Västan för Prästegården”: runstenen U 16 i Ekerö socken, som inte finns kvar. {BAUTIL_SV}.

Den som står framför en runsten i Uppland ser ofta djuret innan runorna. Det är också till stor del efter djuret som forskningen daterar stenarna. Men kan man lita på en träsnidares bild av ett djur som ingen har sett på flera hundra år? Och vad säger djurets drag egentligen, om man räknar dem på alla stenar på en gång? Den här artikeln handlar om de två frågorna. För att svara på den första måste vi börja med den andra.

## Sju stilar och ett djur

Arkeologen Anne-Sofie Gräslund delade in rundjursstilen i sju grupper, och drygt tusen svenska runstenar har fått en av dem i Rundata, den samnordiska runtextdatabasen. RAK är stenar där runbandets ändar är raka, utan djurhuvud. Fp, efter ”fågelperspektiv”, är stenar där djurets huvud är sett ovanifrån, som en mask med två ögon. Pr1 till Pr5 är djur med huvudet i profil, i fem steg där bland annat flikarna vid nacke och läppar, huvudets form och linjernas svängar ändras. Grupperna har tider, från RAK omkring {DAT['RAK'][0]}–{DAT['RAK'][1]} till Pr5 omkring {DAT['Pr5'][0]}–{DAT['Pr5'][1]}, och indelningen är en av de viktigaste grunderna för att datera de svenska runstenarna.

Gräslund byggde indelningen på noggranna iakttagelser av stenarna. Det vi kan bidra med är att mäta samma drag på alla avbildade stenar på en gång och se hur väl grupperna syns i siffrorna. Målet är att pröva och förfina hennes indelning, steg för steg, inte att ersätta den.

## Att läsa ett djur

*Sveriges runinskrifter*, det stora utgåvsverket över de svenska runstenarna, har planscher med foton. {N_PLANSCH:,} av korpusens {N_KORPUS:,} stenar finns avbildade där. Planscherna är skyddade av upphovsrätten, så vi kan läsa och räkna på dem men inte visa dem här.

Vi skrev en kodbok med frågor om rundjuret. Slutar bandet i ett djurhuvud? Hur många djur är det? Är huvudet sett från sidan eller ovanifrån? Är ögat runt eller mandelformat? Finns en flik i nacken eller vid läpparna? Hur slutar svansen? Finns ett koppel, en ögla som binder ihop två djur, och finns flätverk eller ett kors? Varje sten lästes av två läsare oberoende av varandra, två separata körningar av Anthropics språkmodell Claude (Claude Opus). Läsarna såg bara bilden och stenens signum och ombads att inte använda vad de visste om stenen. Ett drag räknades bara när båda gav samma svar.

Hur eniga var de? Vi mätte det med Cohens kappa, ett mått där slumpens bidrag är borträknat. Ett kappa på 1 betyder att läsarna alltid är eniga, och 0 att de inte är eniga oftare än om de hade gissat. För om bandet har ett djurhuvud var kappa {kv(F['djurhuvud']['kappa'])}, för hur huvudet är vänt {kv(F['huvud_vy']['kappa'])}, för ögat {kv(F['oga']['kappa'])} och för kopplet {kv(F['koppel']['kappa'])}, alltså nästan full enighet. Flikarna, svansen, fötterna och flätverket låg mellan {kv(min(LAG))} och {kv(max(LAG))}, vilket brukar räknas som god enighet.

Problemet var ett annat. Huvudets detaljer är små på ett foto av en hel sten, och båda läsarna kunde se dem säkert bara på en tredjedel till drygt hälften av stenarna. {N_UTAN_BILD} stenar saknade en användbar bild. {N_KODAD} stenar fick så många eniga drag att de kunde jämföras med varandra.

## Gräslunds huvudlinjer syns

Innan vi jämförde koderna med stilgrupperna skrev vi ned hur provet skulle gå till och vad som skulle räknas som att det höll. {F1['stenar']} stenar hade både minst tre eniga drag och en stilgrupp i Rundata.

Den första frågan var enkel: räcker dragen för att känna igen stilgruppen? En statistisk modell fick lära sig sambandet på stenarna i fyra femtedelar av socknarna och gissa stilgruppen på stenarna i den sista femtedelen, fem gånger om. Så bedömdes ingen sten av en modell som hade sett den eller dess grannar i samma socken. Modellen satte rätt grupp på {pc(F1['träffsäkerhet'])} procent av stenarna. Den som alltid gissar på den vanligaste gruppen, Pr4, träffar {pc(F1['vanligaste_gruppen'])} procent. Vi blandade också om stilgrupperna slumpvis mellan stenarna och gjorde om alltihop 999 gånger, och ingen av omblandningarna kom upp i modellens träffar.

{chart(True)}

Det intressanta är var modellen träffar och var den missar. RAK känns igen på {pc(HIT['RAK'])} procent av stenarna, Pr4 på {pc(HIT['Pr4'])} och Fp på {pc(HIT['Fp'])}. Huvudets vy gör mycket av arbetet för Fp: av de {sum(FPV.values())} Fp-stenar där läsarna var eniga om huvudet var det sett ovanifrån på {FPV['uppifran']}, medan Pr-stenarnas huvuden nästan alltid är i profil. Pr1, Pr2 och Pr3 känns däremot igen bara på mellan en av fem och två av fem stenar, och Pr5 inte alls. Alla Pr5-stenar utom fyra blir Pr4.

Vart hamnar då felen? Av de {F2['fel_inom_Pr']} stenar som fick fel Pr-grupp hamnade {F2['avstånd']['1']} ett steg bort, {F2['avstånd']['2']} två steg bort och bara {F2['avstånd']['3']} tre steg bort. Det är {pc(F2['andel_till_granne'])} procent hos närmaste granne. Även slumpen ger många grannfel, eftersom de flesta Pr-grupper har två grannar bland bara fyra andra. Hade felen fördelats på måfå hade ungefär {pc(F2['omblandning_medel'])} procent landat hos en granne, och inte heller här kom någon av 999 omblandningar upp i {pc(F2['andel_till_granne'])}. En Pr3-sten förväxlas alltså med Pr2 och Pr4, inte med Pr5. Pr-grupperna beter sig som en ordnad följd, och det stämmer med Gräslunds tanke att grupperna följer på varandra.

Till sist lät vi dragen själva visa vilka grupper de bildar, med en modell som letar efter grupper utan att få veta stilgrupperna. Den fann tre:

- **Inget djurhuvud och inget flätverk:** 191 stenar, varav {K[191]['RAK']} RAK och {K[191]['Fp']} Fp.
- **Ett djur med enkelt huvud, runt öga och svansen i spiral, utan flikar och oftast utan koppel:** 134 stenar, mest Fp ({K[134]['Fp']}), Pr2 ({K[134]['Pr2']}), Pr1 ({K[134]['Pr1']}) och Pr3 ({K[134]['Pr3']}).
- **Huvud i profil, mandelformat öga, koppel och oftast en extra orm:** 295 stenar, mest Pr4 ({K[295]['Pr4']}) och Pr3 ({K[295]['Pr3']}).

Det är Gräslunds huvudlinjer – bandet utan djur, det enkla djuret och följden av profilhuvuden – och de kom fram ur dragen utan att någon talade om dem för modellen. Tre grupper är ändå inte sju. Var gränserna inom Pr-följden går syns inte i de här dragen.

## Där finindelningen tar slut

Varför känns Pr1, Pr2, Pr3 och Pr5 inte igen lika väl? Svaret finns i vad läsarna kunde se. Pr-grupperna skiljs åt framför allt med flikarna vid nacke och läppar, med huvudets form och med linjernas proportioner. Men nackfliken saknar ett enigt värde på {pc(min(NACK))}–{pc(max(NACK))} procent av stenarna i Pr2–Pr5, och läppfliken på {pc(min(LAPP))}–{pc(max(LAPP))} procent. På Pr4-stenarna saknas nackfliken för 146 av 160. Det beror inte på att stenarna saknar flikar, utan på att flikarna inte gick att läsa säkert på ett foto av hela stenen.

Provet kan därför inte avgöra om Pr-grupperna är fem skilda grupper eller ett glidande kontinuum. Att finindelningen inte syns beror på vad vi kunde se, inte nödvändigtvis på indelningen. Det säger också tydligt vad som ska göras härnäst.

En sak till. En modell som lärt sig på Upplands stenar kände igen Södermanlands stilgrupper på bara {pc(F4['Sö']['träffsäkerhet'])} procent av stenarna, mot {pc(F4['inom_uppland_cv'])} procent i Uppland. RAK fungerade ({pc(SO['RAK'])} procent), men det som kallas Fp och Pr3 i Södermanland liknade inte Upplands ({pc(SO['Fp'])} och {pc(SO['Pr3'])} procent). Om det är en regional variant av stilen eller en skillnad i hur grupperna har satts är en egen fråga.

## Tecknarna som såg stenarna innan de försvann

Nu tillbaka till U 16. {N_FORLORADE_KORPUS} av runstenarna i vår korpus är förlorade enligt Rundata. De har sprängts, murats in, blivit byggsten eller helt enkelt kommit bort. Många känner vi bara från teckningar. Den viktigaste samlingen för oss är *Bautil*, med över tusen träsnitt som skars på 1600-talet och trycktes först 1750. Andra stenar tecknades av Johannes Rhezelius på 1630-talet eller av Johan Peringskiöld kring år 1700, och *Sveriges runinskrifter* återger många av deras bilder.

Men en teckning är en tolkning. Tecknaren kan ha förenklat, träsnidaren kan ha förenklat igen, och stenen kan ha vittrat. Innan vi läste djuren på de förlorade stenarna prövade vi därför tecknarna på stenar som finns kvar. Vi tog {N_TECKN} bevarade stenar som har både en gammal teckning och ett foto på planscherna: {PT['bautil']} träsnitt ur Bautil, {PT['rhezelius']} teckningar av Rhezelius, {PT['peringskiold']} av Peringskiöld och {PT['ovrig']} av andra tecknare. Två nya läsare kodade teckningarna utan att se fotona. Regeln skrevs ned i förväg: ett drag får läsas från teckningar om teckning och foto stämmer med ett kappa på minst 0,40, mätt på minst 15 stenar.

![U 1154 i Bautil]({FIG['u1154_bautil_659']})
Träsnitt nummer 659 i Johan Göranssons *Bautil* (1750): U 1154 i Simtuna socken, en sten som finns kvar och som Rundata tillskriver ristaren Erik. Huvudet är sett ovanifrån, med två ögon, alltså Gräslunds Fp. Teckning och foto gav samma svar i alla nio drag som gick att jämföra. {BAUTIL_SV}.

Tecknarna återgav djurets huvuddrag troget. Om djuret har ett huvud stämde med kappa {kv(KT['djurhuvud'])}, hur huvudet är vänt {kv(KT['huvud_vy'])}, nackfliken {kv(KT['nackflik'])}, kopplet {kv(KT['koppel'])}, korset {kv(KT['kors'])}, flätverket {kv(KT['flatverk'])} och antalet djur {kv(KT['antal_djur'])}. Det gällde också Bautils träsnitt, trots att de förenklar formerna: om djuret hade ett huvud stämde på alla {BT['jämförbara']} stenar där det gick att jämföra. Svansen ({kv(KT['svans'])}) och ögat ({kv(KT['oga'])}) stämde måttligt men klarade regeln.

Två drag klarade den inte: läppfliken ({kv(KT['lappflik'])}) och fötterna ({kv(KT['fotter'])}). Fötter syntes nästan aldrig, varken på teckningarna eller på fotona, och av de {TP['lappflik']['jämförbara']} stenar där läppfliken gick att jämföra syntes en flik alls bara på {LP_FLIK}. Det är för lite att bygga på, och därför läser vi aldrig läppfliken från en teckning.

Talen är små. Nackfliken stämde på {NP_LIKA} av {len(NP)} stenar, men bara {NP_FLIK} av dem hade en flik alls. Fotot på planschen är inte heller facit, utan en annan återgivning av samma sten. Det vi har mätt är att två bilder av samma sten säger samma sak.

## {len(FL)} försvunna stenar får sina djur kodade

Sedan läste vi teckningarna av de förlorade stenarna. {len(FB)} förlorade stenar har en teckning från 1500- till 1700-talet. Vi valde Bautil i första hand och därefter Peringskiöld, Rhezelius och övriga. {len(LOST_READ)} teckningar gick att läsa, och {len(FL)} stenar fick minst ett godkänt drag, {sum(1 for v in FL.values() if len(v['koder']) >= 3)} av dem minst tre. {KALLA['Bautil']} av stenarna är kodade ur Bautil. De flesta är från Uppland ({LANDSK['U']}), följda av Södermanland ({LANDSK['Sö']}) och Småland ({LANDSK['Sm']}). Läppfliken och fötterna tas aldrig med, och varje kod är märkt med vilken teckning den kommer från.

För de här stenarna är det första gången rundjurets drag finns i en form som går att räkna med. {N_UTAN_STIL} av de {len(FL)} har ingen stilgrupp alls i Rundata. U 16 är en av dem. Ur träsnittet har den nu fått sina drag: ett djur med huvudet i profil, runt öga, nackflik i spiral, svans i spiral, ett koppel och ett kors.

Koderna säger ännu inte vilken stilgrupp stenarna hör till. De gör det möjligt att fråga. Nästa gång vi prövar Gräslunds indelning kan de förlorade stenarna vara med, märkta så att man alltid ser att de bygger på en teckning.

## Och ristarna?

Arbetet började med en annan fråga. Vi hade en modell som föreslår grupper av runstenar som kan vara gjorda av samma hand, också när ingen ristare har namn. Kunde rundjuret göra grupperna bättre? Delvis. Stenar som runologerna säger har samma ristare liknar varandra mer i rundjurets drag än grannstenar på samma avstånd, så ornamentiken bär spår av handen. Men när dragen lades till i modellen blev grupperna inte mätbart bättre i det låsta provet: av 25 grupper förblev 19 oförändrade, 2 blev bättre och 4 sämre. Det mesta av det ornamentiken kunde tillföra såg modellen redan i stilgruppen, korsformen och utgivarnas ord om ornamentiken. Vitki behåller därför den gamla modellen.

## Det vi inte vet än

Rundatas stilgrupp är inte facit. Den är experternas tillämpning av Gräslunds kriterier, och när koderna och Rundata inte stämmer kan felet ligga hos koderna, hos tilldelningen eller hos indelningen. Provet var dessutom väntat att hålla, eftersom grupperna en gång sattes efter samma slags drag. Det som säger något är mönstret i felen. Läsarna kan också ha känt igen kända stenar trots instruktionen. Och bara hälften av korpusens stenar är avbildade på planscherna.

Nästa steg är att se bättre. Vi ska läsa huvudena i egna utsnitt i stället för på hela stenen, ge läsarna ett exempelblad med Gräslunds egna huvudtyper och låta en tredje läsare avgöra när två är oeniga. Först när flikarna går att läsa på fler stenar kan frågan om fem grupper eller en glidande följd prövas på riktigt. Därefter kommer tiden: håller ordningen mot dateringar som inte bygger på stilen, som personer vi vet när de levde eller stenar som murats in i kyrkor med känd byggtid?

Den som har en runsten i närheten kan göra en del av provet själv. Titta på huvudet. Är det sett från sidan eller ovanifrån? Finns det en flik i nacken, och rullar den upp sig? Det är just de frågorna som avgör var i Gräslunds följd stenen hamnar.

:::box Det viktigaste i korthet
- Rundjurets drag, räknade på hundratals stenar, bär Gräslunds huvudlinjer: bandet utan djur, huvudet ovanifrån och en följd av profilhuvuden.
- Pr-grupperna beter sig som en ordnad följd. Om de är fem skilda grupper eller ett glidande kontinuum går inte att avgöra förrän flikarna vid nacke och läppar kan läsas på fler stenar.
- Tecknarna på 1600- och 1700-talen återgav djurets huvuddrag troget, men inte läppflikarna. Därför har {len(FL)} försvunna stenar nu koder för de drag som håller.
- Det här är ett första steg i att pröva och förfina Gräslunds indelning, inte att ersätta den.
:::

## Källor

Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139. Samnordisk runtextdatabas (Rundata) 3.1, Uppsala universitet. *Sveriges runinskrifter*, Riksantikvarieämbetet (planscher och textband, lästa men inte återgivna). Göransson, J. 1750. *Bautil*. Stockholm; {BAUTIL_SV}. De låsta analysplanerna (2026-11-24 och 2026-11-25), kodboken och resultaten finns i Vitkis öppna kodförråd."""

body_en = f"""West of the vicarage in Ekerö parish there once stood a runestone now called U 16. It is no longer there. What remains is a woodcut, number 279 in the book *Bautil*, cut in the seventeenth century and printed in 1750. On the woodcut a rune animal winds along the edge of the stone. The head is seen from the side, with a round eye and a lappet that curls up at the neck. The tail ends in a spiral, and lower down a loop binds the two parts of the band together. Above stands a cross.

![U 16 in Bautil]({FIG['u16_bautil_279']})
Woodcut number 279 in Johan Göransson's *Bautil* (1750), captioned "Västan för Prästegården" (west of the vicarage): the runestone U 16 in Ekerö parish, which no longer survives. {BAUTIL_EN}.

Anyone standing before a runestone in Uppland often sees the animal before the runes. It is also largely by the animal that research dates the stones. But can we trust a woodcutter's picture of an animal no one has seen for several hundred years? And what do the animal's features actually say, if we count them on all the stones at once? This article is about those two questions. To answer the first, we have to begin with the second.

## Seven styles and one animal

The archaeologist Anne-Sofie Gräslund divided the rune-animal style into seven groups, and just over a thousand Swedish runestones have been given one of them in Rundata, the Scandinavian Runic-text Database. RAK stones have rune bands with straight ends and no animal head. Fp, for the Swedish "fågelperspektiv" (bird's-eye view), are stones where the animal's head is seen from above, like a mask with two eyes. Pr1 to Pr5 are animals with the head in profile, in five steps in which, among other things, the lappets at neck and lips, the shape of the head and the curves of the lines change. The groups have dates, from RAK around {DAT['RAK'][0]}–{DAT['RAK'][1]} to Pr5 around {DAT['Pr5'][0]}–{DAT['Pr5'][1]}, and the division is one of the most important foundations for dating the Swedish runestones.

Gräslund built the division on careful observation of the stones. What we can add is to measure the same features on all the depicted stones at once and see how clearly the groups show in the numbers. The aim is to test and refine her division, step by step, not to replace it.

## Reading an animal

*Sveriges runinskrifter*, the great edition of the Swedish runic inscriptions, has plates with photographs. {N_PLANSCH:,} of the corpus's {N_KORPUS:,} stones are depicted there. The plates are protected by copyright, so we can read and count from them but not show them here.

We wrote a codebook of questions about the rune animal. Does the band end in an animal head? How many animals are there? Is the head seen from the side or from above? Is the eye round or almond-shaped? Is there a lappet at the neck or at the lips? How does the tail end? Is there a "koppel", a loop that binds two animals together, and is there interlace or a cross? Every stone was read by two readers independently of each other, two separate runs of Anthropic's language model Claude (Claude Opus). The readers saw only the picture and the stone's signum and were told not to use what they knew about the stone. A feature counted only when both gave the same answer.

How far did they agree? We measured it with Cohen's kappa, a measure from which the contribution of chance is removed. A kappa of 1 means the readers always agree, and 0 that they agree no more often than if they had guessed. For whether the band has an animal head kappa was {kv(F['djurhuvud']['kappa'], False)}, for which way the head faces {kv(F['huvud_vy']['kappa'], False)}, for the eye {kv(F['oga']['kappa'], False)} and for the koppel {kv(F['koppel']['kappa'], False)}, that is, almost complete agreement. The lappets, the tail, the feet and the interlace lay between {kv(min(LAG), False)} and {kv(max(LAG), False)}, which is usually counted as good agreement.

The problem was a different one. The details of the head are small in a photograph of a whole stone, and both readers could see them with certainty on only a third to just over half of the stones. {N_UTAN_BILD} stones had no usable picture. {N_KODAD} stones received enough agreed features to be compared with each other.

## Gräslund's main lines show

Before we compared the codes with the style groups, we wrote down how the test would be run and what would count as holding. {F1['stenar']} stones had both at least three agreed features and a style group in Rundata.

The first question was simple: are the features enough to recognise the style group? A statistical model learned the relationship on the stones in four fifths of the parishes and guessed the style group of the stones in the last fifth, five times over. So no stone was judged by a model that had seen it or its neighbours in the same parish. The model put {pc(F1['träffsäkerhet'])} percent of the stones in the right group. Someone who always guesses the most common group, Pr4, is right {pc(F1['vanligaste_gruppen'])} percent of the time. We also shuffled the style groups at random among the stones and repeated everything 999 times, and none of the shuffles reached the model's score.

{chart(False)}

What is interesting is where the model hits and where it misses. RAK is recognised on {pc(HIT['RAK'])} percent of the stones, Pr4 on {pc(HIT['Pr4'])} and Fp on {pc(HIT['Fp'])}. The view of the head does much of the work for Fp: of the {sum(FPV.values())} Fp stones where the readers agreed on the head, it was seen from above on {FPV['uppifran']}, while the heads on Pr stones are almost always in profile. Pr1, Pr2 and Pr3, on the other hand, are recognised on only between one in five and two in five stones, and Pr5 not at all. All Pr5 stones but four become Pr4.

Where do the errors go? Of the {F2['fel_inom_Pr']} stones given the wrong Pr group, {F2['avstånd']['1']} landed one step away, {F2['avstånd']['2']} two steps away and only {F2['avstånd']['3']} three steps away. That is {pc(F2['andel_till_granne'])} percent with the nearest neighbour. Chance also produces many neighbour errors, since most Pr groups have two neighbours among only four others. Had the errors fallen at random, about {pc(F2['omblandning_medel'])} percent would have landed with a neighbour, and here too none of 999 shuffles reached {pc(F2['andel_till_granne'])}. A Pr3 stone is confused with Pr2 and Pr4, then, not with Pr5. The Pr groups behave as an ordered sequence, which fits Gräslund's idea that the groups follow one another.

Finally we let the features themselves show what groups they form, with a model that looks for groups without being told the style groups. It found three:

- **No animal head and no interlace:** 191 stones, of which {K[191]['RAK']} RAK and {K[191]['Fp']} Fp.
- **One animal with a simple head, round eye and spiral tail, without lappets and mostly without a koppel:** 134 stones, mostly Fp ({K[134]['Fp']}), Pr2 ({K[134]['Pr2']}), Pr1 ({K[134]['Pr1']}) and Pr3 ({K[134]['Pr3']}).
- **Head in profile, almond eye, koppel and usually an extra serpent:** 295 stones, mostly Pr4 ({K[295]['Pr4']}) and Pr3 ({K[295]['Pr3']}).

These are Gräslund's main lines – the band without an animal, the simple animal and the sequence of profile heads – and they emerged from the features without anyone telling the model about them. Still, three groups are not seven. Where the borders within the Pr sequence lie does not show in these features.

## Where the fine division ends

Why are Pr1, Pr2, Pr3 and Pr5 not recognised as well? The answer lies in what the readers could see. The Pr groups are told apart above all by the lappets at neck and lips, by the shape of the head and by the proportions of the lines. But the neck lappet lacks an agreed value on {pc(min(NACK))}–{pc(max(NACK))} percent of the stones in Pr2–Pr5, and the lip lappet on {pc(min(LAPP))}–{pc(max(LAPP))} percent. On the Pr4 stones the neck lappet is missing for 146 of 160. That is not because the stones lack lappets, but because the lappets could not be read with certainty in a photograph of the whole stone.

The test therefore cannot decide whether the Pr groups are five separate groups or a sliding continuum. That the fine division does not show is down to what we could see, not necessarily to the division. It also says clearly what needs doing next.

One more thing. A model trained on the stones of Uppland recognised the style groups of Södermanland on only {pc(F4['Sö']['träffsäkerhet'])} percent of the stones, against {pc(F4['inom_uppland_cv'])} percent within Uppland. RAK worked ({pc(SO['RAK'])} percent), but what is called Fp and Pr3 in Södermanland did not resemble Uppland's ({pc(SO['Fp'])} and {pc(SO['Pr3'])} percent). Whether that is a regional variant of the style or a difference in how the groups were assigned is a question of its own.

## The draughtsmen who saw the stones before they vanished

Back to U 16. {N_FORLORADE_KORPUS} of the runestones in our corpus are lost according to Rundata. They have been blasted, walled in, used as building stone or simply gone missing. Many we know only from drawings. The most important collection for us is *Bautil*, with over a thousand woodcuts cut in the seventeenth century and not printed until 1750. Other stones were drawn by Johannes Rhezelius in the 1630s or by Johan Peringskiöld around 1700, and *Sveriges runinskrifter* reproduces many of their pictures.

But a drawing is an interpretation. The draughtsman may have simplified, the woodcutter may have simplified again, and the stone may have weathered. Before reading the animals on the lost stones, we therefore tested the draughtsmen on stones that survive. We took {N_TECKN} surviving stones that have both an old drawing and a photograph on the plates: {PT['bautil']} woodcuts from Bautil, {PT['rhezelius']} drawings by Rhezelius, {PT['peringskiold']} by Peringskiöld and {PT['ovrig']} by other draughtsmen. Two new readers coded the drawings without seeing the photographs. The rule was written down in advance: a feature may be read from drawings if drawing and photograph agree with a kappa of at least 0.40, measured on at least 15 stones.

![U 1154 in Bautil]({FIG['u1154_bautil_659']})
Woodcut number 659 in Johan Göransson's *Bautil* (1750): U 1154 in Simtuna parish, a stone that survives and that Rundata attributes to the carver Erik. The head is seen from above, with two eyes – Gräslund's Fp. Drawing and photograph gave the same answer in all nine features that could be compared. {BAUTIL_EN}.

The draughtsmen rendered the animal's main features faithfully. Whether the animal has a head agreed with a kappa of {kv(KT['djurhuvud'], False)}, which way the head faces {kv(KT['huvud_vy'], False)}, the neck lappet {kv(KT['nackflik'], False)}, the koppel {kv(KT['koppel'], False)}, the cross {kv(KT['kors'], False)}, the interlace {kv(KT['flatverk'], False)} and the number of animals {kv(KT['antal_djur'], False)}. This held for Bautil's woodcuts too, although they simplify the forms: whether the animal had a head agreed on all {BT['jämförbara']} stones where it could be compared. The tail ({kv(KT['svans'], False)}) and the eye ({kv(KT['oga'], False)}) agreed moderately but passed the rule.

Two features did not pass: the lip lappet ({kv(KT['lappflik'], False)}) and the feet ({kv(KT['fotter'], False)}). Feet hardly ever appeared, in the drawings or in the photographs, and of the {TP['lappflik']['jämförbara']} stones where the lip lappet could be compared, a lappet appeared at all on only {LP_FLIK}. That is too little to build on, so we never read the lip lappet from a drawing.

The numbers are small. The neck lappet agreed on {NP_LIKA} of {len(NP)} stones, but only {NP_FLIK} of them had a lappet at all. Nor is the photograph on the plate the truth; it is another rendering of the same stone. What we have measured is that two pictures of the same stone say the same thing.

## {len(FL)} lost stones have their animals coded

Then we read the drawings of the lost stones. {len(FB)} lost stones have a drawing from the sixteenth to the eighteenth century. We chose Bautil first, then Peringskiöld, Rhezelius and the others. {len(LOST_READ)} drawings could be read, and {len(FL)} stones received at least one approved feature, {sum(1 for v in FL.values() if len(v['koder']) >= 3)} of them at least three. {KALLA['Bautil']} of the stones are coded from Bautil. Most are from Uppland ({LANDSK['U']}), followed by Södermanland ({LANDSK['Sö']}) and Småland ({LANDSK['Sm']}). The lip lappet and the feet are never included, and every code is marked with the drawing it comes from.

For these stones it is the first time the rune animal's features exist in a form that can be counted. {N_UTAN_STIL} of the {len(FL)} have no style group at all in Rundata. U 16 is one of them. From the woodcut it now has its features: one animal with the head in profile, a round eye, a spiral neck lappet, a spiral tail, a koppel and a cross.

The codes do not yet say which style group the stones belong to. They make it possible to ask. The next time we test Gräslund's division, the lost stones can take part, marked so that one always sees they rest on a drawing.

## And the carvers?

The work began with another question. We had a model that proposes groups of runestones that may have been made by the same hand, even when no carver has a name. Could the rune animal make the groups better? Partly. Stones that the runologists say share a carver resemble each other more in the animal's features than neighbouring stones at the same distance, so the ornament carries traces of the hand. But when the features were added to the model, the groups did not become measurably better in the locked test: of 25 groups, 19 stayed unchanged, 2 got better and 4 worse. Most of what the ornament could add, the model already saw in the style group, the cross form and the editors' words about the ornament. Vitki therefore keeps the old model.

## What we do not know yet

Rundata's style group is not the truth. It is the experts' application of Gräslund's criteria, and when the codes and Rundata disagree the fault may lie with the codes, with the assignment or with the division. The test was also expected to hold, since the groups were once set by the same kind of features. What tells us something is the pattern in the errors. The readers may also have recognised well-known stones despite the instruction. And only half of the corpus's stones are depicted on the plates.

The next step is to see better. We will read the heads in their own crops rather than on the whole stone, give the readers an example sheet with Gräslund's own head types and let a third reader decide when two disagree. Only when the lappets can be read on more stones can the question of five groups or a sliding sequence be tested properly. Then comes time: does the order hold against dates that do not rest on style, such as people whose lifetimes we know, or stones built into churches of known date?

Anyone with a runestone nearby can do part of the test themselves. Look at the head. Is it seen from the side or from above? Is there a lappet at the neck, and does it curl up? Those are exactly the questions that decide where in Gräslund's sequence the stone ends up.

:::box The essentials in brief
- The rune animal's features, counted on hundreds of stones, carry Gräslund's main lines: the band without an animal, the head seen from above and a sequence of profile heads.
- The Pr groups behave as an ordered sequence. Whether they are five separate groups or a sliding continuum cannot be decided until the lappets at neck and lips can be read on more stones.
- The draughtsmen of the seventeenth and eighteenth centuries rendered the animal's main features faithfully, but not the lip lappets. So {len(FL)} lost stones now have codes for the features that hold.
- This is a first step in testing and refining Gräslund's division, not in replacing it.
:::

## Sources

Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139. Scandinavian Runic-text Database (Rundata) 3.1, Uppsala University. *Sveriges runinskrifter*, Swedish National Heritage Board (plates and text volumes, read but not reproduced). Göransson, J. 1750. *Bautil*. Stockholm; {BAUTIL_EN}. The locked analysis plans (2026-11-24 and 2026-11-25), the codebook and the results are in Vitki's open code repository."""

body = body.replace(f"{N_PLANSCH:,}", "1 170").replace(f"{N_KORPUS:,}", "2 314")

# ---- kontroller ---------------------------------------------------------------------------------------------------------
HOLDBACK = re.compile(r"\bAI\b|signifikan|p-värde|p-value|bootstrap|\bHolm\b", re.I)
PRONOUN = re.compile(r"\b(han|hon|hans|hennes|he|she|his|him)\b", re.I)
labels = ["Forskning", "Datering och stil", "Ristare"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not HOLDBACK.search(b), (lang, HOLDBACK.search(b).group(0))
    assert not re.search(r"^\s*\|", b, re.M)
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M))
    assert "{" not in b and "}" not in b
    assert b.index("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") < b.index("## Källor" if lang == "sv" else "## Sources")
    caps = [b.splitlines()[i + 1] for i, ln in enumerate(b.splitlines()) if ln.startswith("![")]
    assert len(caps) == 2 and all("Bautil" in c and ("Umeå" in c) for c in caps)
    assert "Claude Opus" in b and b.count("Claude") == 2  # en gång, i metoddelen
    box = b[b.index(":::box"):b.index(":::", b.index(":::box") + 3)]
    assert "Claude" not in box and "insikt" not in box.lower() and "nyhet" not in box.lower()
    # inga könade pronomen om ristare (Gräslunds "hennes"/"her" om indelningen är tillåtet)
    assert all(m.group(0).lower() in ("hennes",) for m in PRONOUN.finditer(b)), (lang, [m.group(0) for m in PRONOUN.finditer(b)])
assert "1 170" in body and "1,170" in body_en
OUT = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "ornamentik.json")
json.dump(OUT, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord sv,", len(body_en.split()), "words en")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published") and old.get("slug") == SLUG, "Bara det opublicerade utkastet skrivs över härifrån"
        ref.set({**OUT, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc, SLUG)
    else:
        assert not [p for p in blog._all() if p.get("slug") == SLUG], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**OUT, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Datering och stil|ornamentik", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
