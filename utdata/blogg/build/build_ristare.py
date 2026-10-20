"""Artikeln om möjliga okända ristare (r/anonymous.R + utdata/ristare/): grupper av stenar utan ristare i Rundata som
liknar varandra i handens drag, prövade på ristare metoden inte sett (hållet-utanför-test) och med den svaga punkten
redovisad: kalibreringen kommer nästan helt från Uppland och Södermanland, och kandidatgrupperna ligger där få stenar
har någon ristare. Varje siffra hämtas ur analysfilerna och låses med asserts.
    ../../../.venv/bin/python build_ristare.py [--write | --update DOC]
Skriver utdata/blogg/ristareartikel.json; --write sparar ett nytt opublicerat utkast i Firestore."""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
RUN = os.path.join(ROOT, "data", "cache", "r", "corpus", "255da407de30e6cb")
UT = os.path.join(ROOT, "utdata", "ristare")
A = json.load(open(os.path.join(RUN, "anonymous.json"), encoding="utf-8"))
H3 = json.load(open(os.path.join(UT, "ut", "ristare_heldout_3delar.json"), encoding="utf-8"))
H2 = json.load(open(os.path.join(UT, "ut", "ristare_heldout_2delar.json"), encoding="utf-8"))
OV = json.load(open(os.path.join(UT, "ut", "ristare_overforing.json"), encoding="utf-8"))

svn = lambda x, d=0: f"{x:,.{d}f}".replace(",", " ").replace(".", ",")  # noqa: E731
enn = lambda x, d=0: f"{x:.{d}f}"  # noqa: E731
pr = lambda x: round(100 * x)  # noqa: E731

# ---- låsningarna -----------------------------------------------------------------------------------
C, V, T = A["calibration"], A["validation"], A["time_free"]
assert (A["n_stones"], A["n_unattributed"], A["n_known"]) == (1292, 691, 441)
assert C["link_km"] == 30 and C["lr_min"] == 12 and C["lr"] == 13.6 and pr(C["precision"]) == 71 and pr(C["tpr"]) == 7
assert (V["n_groups"], V["n_stones"], pr(V["purity"]), pr(V["purity_geography"])) == (15, 182, 69, 43)
assert pr(V["purity_no_time"]) == 68 and A["n_candidates"] == 8
assert H3["n_kanda_ristare"] == 35 and H3["n_kanda_stenar"] == 441 and H3["omgangar"] == 30 and H3["delar"] == 3
h, hn = H3["huvud"], H3["utan_tid"]
assert (pr(h["renhet"]), pr(h["geografi"]), pr(h["skillnad"])) == (86, 69, 17)
assert (pr(hn["renhet"]), pr(hn["geografi"])) == (85, 68)
assert h["omgangar_over_geografi"] == 30 and h["omgangar_p05"] == 30 and h["p_per_omgang_median"] < 0.01
assert pr(h["skillnad_ci"][0]) == 16 and pr(h["skillnad_ci"][1]) == 18
sens = [pr(k["skillnad"]) for k in H3["kanslighet"]] + [pr(H2["huvud"]["skillnad"])]
assert min(sens) == 12 and max(sens) == 19, sens
assert pr(H2["huvud"]["renhet"]) == 80 and pr(H2["huvud"]["geografi"]) == 61
land = OV["per_landskap"]
assert land["U"] == 25 and land["Sö"] == 8 and sum(land.values()) == 35
so_u = OV["Sö_till_U"]
assert pr(so_u["renhet"]) == 74 and pr(so_u["geografi"]) == 61 and so_u["median_p_per_körning"] > 0.05 and so_u["körningar_p05"] == 0
assert OV["U_till_Sö"]["grupper_per_körning"] == 1.0

G = {g["id"]: g for g in A["groups"]}
cand = {g["id"]: g for g in A["groups"] if g["status"] == "candidate"}
assert sorted(cand) == [2, 4, 5, 6, 11, 12, 13, 14]
NAMES = {2: "Konungsund", 4: "Viby", 5: "Vetlanda", 6: "Kölaby", 11: "Sättna", 12: "Leksberg", 13: "Husaby", 14: "Dalum"}
assert all(cand[i]["name"].startswith(NAMES[i]) for i in cand)
mark = lambda i, key: next(m for m in cand[i]["marks"] if m["feature"].startswith(key))  # noqa: E731
st = lambda i: pr(cand[i]["stability"])  # noqa: E731
nt = lambda i: pr(cand[i]["robust_no_time"])  # noqa: E731
assert [(st(i), nt(i)) for i in (2, 5, 12, 13, 6)] == [(81, 83), (95, 79), (82, 83), (84, 83), (74, 68)]
assert [(st(i), nt(i)) for i in (4, 11, 14)] == [(89, 62), (83, 57), (77, 14)]
assert [cand[i]["n"] for i in (2, 4, 5, 6, 11, 12, 13, 14)] == [28, 14, 14, 13, 7, 6, 6, 5]
assert len(cand[2]["parishes"]) == 20 and round(cand[12]["spread_km"]) == 2 and round(cand[2]["spread_km"]) == 15
KON_ORD = mark(2, "Ordföljd"); KON_REST = mark(2, "Resarformel"); KON_EFT = mark(2, "æftiR")
assert (pr(KON_ORD["share_group"]), pr(KON_ORD["share_area"])) == (96, 51)
assert (pr(KON_REST["share_group"]), pr(KON_REST["share_area"])) == (89, 51)
assert (pr(KON_EFT["share_group"]), pr(KON_EFT["share_area"])) == (100, 65)
VET = mark(5, "Resarformel"); assert (VET["feature"], pr(VET["share_group"]), pr(VET["share_area"])) == ("Resarformel: satte", 64, 5)
HUS = mark(13, "Resarformel"); assert (HUS["feature"], pr(HUS["share_group"]), pr(HUS["share_area"])) == ("Resarformel: satte", 83, 11)
LEK = mark(12, "ʀ skrivet"); assert (pr(LEK["share_group"]), pr(LEK["share_area"])) == (80, 12)
SAT = mark(11, "Resarformel"); assert (SAT["feature"], pr(SAT["share_group"]), pr(SAT["share_area"])) == ("Resarformel: rätte", 71, 0)
VIB = mark(4, "Stavning av 'efter'"); assert (pr(VIB["share_group"]), pr(VIB["share_area"])) == (85, 26)
assert cand[2]["nearest_carver"]["carver"] == "Traen" and round(cand[2]["nearest_carver"]["km"]) == 32
assert cand[4]["nearest_carver"]["carver"] == "Torkel" and round(cand[4]["nearest_carver"]["km"]) == 14
assert not any(cand[i].get("nearest_carver") for i in (5, 6, 11, 12, 13, 14))
known_groups = [g for g in A["groups"] if g["status"] == "known"]
assert len(known_groups) == 8 and len(A["groups"]) == 16

# Andel av stenarna (minst fem läsbara ord) som har en ristare i Rundata, per landskap
import pandas as pd  # noqa: E402

d = pd.read_csv(os.path.join(RUN, "corpus.csv"), na_values="", keep_default_na=False, low_memory=False)
g = pd.read_csv(os.path.join(RUN, "geography_stones.csv"))
f = d.merge(g[["signum"]], on="signum")
f = f[f.n_words >= 5]
f["har"] = f.carver.astype(str).str.len().gt(0) & f.carver.notna()
RATE = f.groupby("province").har.mean()
NSTONE = f.groupby("province").size()
assert len(f) == 1292
rate = {p: pr(RATE[p]) for p in ("U", "Sö", "Ög", "Sm", "Vg", "M")}
assert rate == {"U": 57, "Sö": 40, "Ög": 5, "Sm": 1, "Vg": 0, "M": 8}, rate
assert NSTONE["Vg"] == 95 and NSTONE["Ög"] == 134 and NSTONE["M"] == 12 and NSTONE["U"] == 671

# ---- figuren (kartan ur körningen, fryst i bloggens arkiv) ---------------------------------------
from src import blog_figures  # noqa: E402

FIG = "okanda_ristare.png"
dsc = blog_figures.describe(FIG)
url_sv = blog_figures.freeze(open(os.path.join(RUN, FIG), "rb").read())
url_en = blog_figures.freeze(open(os.path.join(UT, "en", FIG), "rb").read())
MAP_SV = blog_figures.markdown(url_sv, dsc, "sv")
MAP_EN = blog_figures.markdown(url_en, dsc, "en")

title = "Möjliga ristare utan namn"
summary = ("Var tredje runsten har en känd ristare; resten är anonyma. Vi lät datorn söka grupper av namnlösa stenar "
           "som liknar varandra i stavning, formler och stil lika mycket som en ristares stenar. Metoden prövades först "
           "på ristare den aldrig sett – och klarade det. Men den är bara kalibrerad i Mälardalen, och de sju grupperna "
           "ligger någon annanstans.")

body = f"""Av de {svn(A['n_stones'])} runstenar vi har läsbar text från har {A['n_known']} en ristare med minst tre stenar, utpekad av forskningen med en signatur på stenen eller av stilen, och det är på dem metoden kan prövas. Och {A['n_unattributed']} saknar helt ristare i databasen. Frågan är om de är ett enda anonymt flöde, eller om det bland dem finns händer som ännu saknar namn.

Vi kan inte fråga stenarna, men vi kan göra ett test som en skeptiker skulle godkänna: dölja de kända ristarna för oss själva och se om metoden hittar dem.

## Hur man söker efter en hand

Vi mäter hur lika två stenar är i det som en ristare tar med sig från sten till sten: stilgruppen, korset, kortkvistrunor, stavningen av vanliga ord, skiljetecknen, bindrunorna, formlerna och vilka runpar som förekommer. Innehållet i texten och platsen ingår *inte* i likheten.

Sedan kalibrerar vi på stenar med känd ristare. Ligger två stenar inom 30 kilometer från varandra och är lika nog, är det {svn(C['lr'], 1)} gånger vanligare att de är av samma ristare än av olika. Sju av tio sådana par är verkligen samma ristare ({pr(C['precision'])} procent). Det är en försiktig sållning: bara {pr(C['tpr'])} procent av alla par som *är* av samma ristare blir så lika att metoden fångar dem. Hellre få och säkra än många och osäkra.

Därefter bildar stenarna grupper (de som är lika varandra och ligger nära varandra hänger ihop) och vi redovisar bara grupper med minst fyra stenar som inte är mer utspridda än nio av tio kända ristares stenar.

## Testet: ristare metoden aldrig sett

Gör man som om en känd ristare vore okänd och söker grupper bland hans stenar, blir {pr(V['purity'])} procent av stenarna i en grupp i genomsnitt av samma ristare. Grupper av lika många närliggande stenar, utan hänsyn till handens drag, ger {pr(V['purity_geography'])} procent. Det är ett bra resultat, men det räknades med gränsvärden som vi själva justerade efter just den kontrollen, och det överskattar därför.

Det strängare testet delar ristarna slumpvis i tre delar. Gränsen tas fram på två delar och prövas på den tredje, som metoden aldrig sett, och allt upprepas trettio gånger med nya indelningar. Då är grupperna i snitt {pr(h['renhet'])} procent samma ristare, mot {pr(h['geografi'])} procent för närliggande stenar. (Procenttalen är högre än i det första testet eftersom varje prov bara har en tredjedel av ristarna, så grupperna blir lättare att få rena. Det som räknas är avståndet till närhetsgrupperna.) Skillnaden är {pr(h['skillnad'])} procentenheter, med osäkerhet mellan {pr(h['skillnad_ci'][0])} och {pr(h['skillnad_ci'][1])}, och den var till gruppernas fördel i alla trettio upprepningar. Skillnaden krymper alltså från 26 procentenheter i det första testet till {pr(h['skillnad'])} i det strängare, och i andra inställningar av avstånd och sållning landar den mellan {min(sens)} och {max(sens)}.

Metoden vilar inte heller på sådant som bara följer tiden. Tar man bort stilgrupp, kors, stungna runor, böner och signaturer, och räknar om gränsen, blir resultatet {pr(hn['renhet'])} mot {pr(hn['geografi'])} procent. Samtida stenar ser alltså inte ut som en hand bara för att dragen följer tiden.

:::box Den svaga punkten
Nästan alla ristare vi kan pröva på finns i Mälardalen. Av de {sum(land.values())} kända ristare som har minst tre stenar är {land['U']} i Uppland och {land['Sö']} i Södermanland. Av Upplands stenar har {rate['U']} procent en ristare i databasen och av Södermanlands {rate['Sö']} procent, men av Östergötlands bara {rate['Ög']} procent, Smålands {rate['Sm']} procent, Västergötlands {rate['Vg']} procent (inte en enda av {NSTONE['Vg']} stenar) och Medelpads {rate['M']} procent. Gränsen har alltså aldrig kunnat prövas där kandidaterna finns. Vi försökte flytta den: tränar man på Södermanlands ristare och prövar på Upplands, blir grupperna {pr(so_u['renhet'])} procent rena mot {pr(so_u['geografi'])} för närhet, men det är inte säkert nog att skilja från slump. Åt andra hållet blir det för få grupper för att räkna alls. Vi vet därför att metoden fungerar där ristare är kända, inte att den gör det i Västergötland.
:::

## Sju grupper utan namn

Efter sållningen finns {len(G)} grupper av stenar utan ristare. Hälften av dem, {len(known_groups)} stycken, liknar en känd ristare, vilket är gott tecken för metoden: den hittar det som redan är känt. Återstår sju som inte liknar någon känd ristare i närheten, och en åttonde, Dalum, som föll bort. De har fått arbetsnamn efter socknen vid den sten som ligger mest i mitten, och namnet är en etikett för gruppen, inte ett påstående om en person.

{MAP_SV}

Fem av grupperna håller även utan de tidsberoende dragen och när en femtedel av länkarna slumpas bort:

**Konungsund** (Östergötland, {cand[2]['n']} stenar i {len(cand[2]['parishes'])} socknar, vanligen inom {svn(cand[2]['spread_km'])} km från mitten). I gruppen står substantivet före pronomenet på {pr(KON_ORD['share_group'])} procent av stenarna, mot {pr(KON_ORD['share_area'])} procent hos stenarna inom 50 km (*stæin þenna*, ’sten denna’, i stället för *þenna stæin*, ’denna sten’), verbet *reste* på {pr(KON_REST['share_group'])} procent mot {pr(KON_REST['share_area'])} och prepositionen *æftiR* på {pr(KON_EFT['share_group'])} procent mot {pr(KON_EFT['share_area'])}. Närmaste kända ristare, Traen, ligger {svn(cand[2]['nearest_carver']['km'])} km bort och är inte så lik som en ristares egna stenar brukar vara. Gruppen återfinns till {st(2)} procent när länkar tas bort och {nt(2)} procent utan tidsdragen.

**Vetlanda** (Småland, {cand[5]['n']} stenar). Verbet *satte* i stället för *reste* står på {pr(VET['share_group'])} procent av stenarna, mot {pr(VET['share_area'])} procent runtom. Återfinns till {st(5)} procent, {nt(5)} procent utan tid.

**Husaby** (Västergötland, {cand[13]['n']} stenar). Också här *satte*: {pr(HUS['share_group'])} procent mot {pr(HUS['share_area'])} procent i trakten. Återfinns till {st(13)} procent, {nt(13)} procent utan tid.

**Leksberg** (Västergötland, {cand[12]['n']} stenar med omkring två kilometer mellan de mest avlägsna). Skrivningen av ändelse-*ʀ* med vanligt r i stället för yr-runan står på {pr(LEK['share_group'])} procent av stenarna, mot {pr(LEK['share_area'])} procent i trakten. Återfinns till {st(12)} procent, {nt(12)} procent utan tid.

**Kölaby** (Västergötland, {cand[6]['n']} stenar). Den svagaste av de fem, med stungna runor på alla stenar mot knappt hälften av stenarna i trakten. Återfinns till {st(6)} procent, {nt(6)} procent utan tid.

Två grupper håller bara delvis. **Viby** (Östergötland, {cand[4]['n']} stenar, stavningen *e-…-iR* av *efter* på {pr(VIB['share_group'])} procent mot {pr(VIB['share_area'])}) återfinns till {st(4)} procent men bara {nt(4)} procent utan tidsdragen. **Sättna** i Medelpad ({cand[11]['n']} stenar) har verbet *rätte* ('rätade upp') på {pr(SAT['share_group'])} procent av stenarna och ingen sten runtom har det, men gruppen är liten och återfinns till {nt(11)} procent utan tid. **Dalum** ({cand[14]['n']} stenar) återfinns till {nt(14)} procent utan tidsdragen och räknas inte.

De drag som listas är de där en grupp skiljer sig mest från sin omgivning. Eftersom grupperna bildas efter likhet i just de dragen visar listan hur gruppen ser ut, inte att den är en hand. Det är valideringen ovan som talar för det, och bara där ristare är kända.

## Ristare, verkstad eller tradition

En grupp som skriver lika kan ha tre förklaringar vi inte kan skilja på: en ristare, en verkstad med flera händer, eller en lokal skrivvana som många delade (verbet *satte* kan lika gärna vara beställarnas ord som ristarens). Det som skiljer dem är sådant vi inte har mätt här: hur runorna är huggna, ornamentet, och om sådant som huggspår stämmer från sten till sten. Ett första steg är att granska stenarna i Husaby- och Leksbergsgrupperna i fält eller i 3D. Och en runolog som känner Västergötlands stenar kan förmodligen snabbt säga om grupperna redan är beskrivna.

:::box Så räknade vi
Underlag: {svn(A['n_stones'])} vikingatida runstenar i Samnordisk runtextdatabas med minst fem läsbara ord och koordinater. Likheten är Gowers avstånd (som hanterar både ja/nej-drag och kategorier) på stilgrupp, kors, kortkvistrunor, ett tjugotal språkdrag, formler och runbigram. Gränsen för att länka två stenar valdes så att par under gränsen är minst tolv gånger vanligare bland samma ristares par än bland olika ristares, bland par inom 30 km. Grupperna hittades med Louvain-metoden för nätverk. Stabiliteten är andelen av en grupp som återkommer när en femtedel av länkarna slumpas bort, femtio gånger. Hållet-utanför-testet delar ristarna (inte stenarna) slumpvis i tre delar, tar fram gräns och största spridning på två och bildar grupper på den tredje; jämförelsen är grupper av lika många närliggande stenar ur samma tredjedel. Trettio upprepningar; p-värden över upprepningarna räknas inte eftersom stenarna delas mellan dem, och vi rapporterar skillnadens osäkerhetsintervall över upprepningarna. Kandidaterna är inte jämförda med litteraturen. All kod och alla resultat ligger öppet i kodförrådet (r/anonymous.R, utdata/ristare).
:::

:::box Det viktigaste i korthet
- En metod som söker grupper av stenar med samma handstil hittar rätt ristare tydligt oftare än slumpen och närheten ensamma, även för ristare den inte sett – men effekten är mindre än vi först mätte (17 procentenheter mot 26).
- Metoden är bara prövad i Mälardalen. Där kandidatgrupperna ligger, i Östergötland, Småland, Västergötland och Medelpad, har knappt några stenar en känd ristare, så den kan inte prövas.
- Fem grupper håller sig även när tidsberoende drag tas bort. De är hypoteser om en ristare, en verkstad eller en lokal skrivvana, och steget som avgör är en granskning av själva stenarna.
:::

## Källor och data

Samnordisk runtextdatabas (Uppsala universitet, ODbL), Vitkis R-modul Okända ristare.

*Data: Scandinavian Runic Text Database (Uppsala University).*"""

n_known_en = len(known_groups)
body_en = f"""Of the {enn(A['n_stones'])} runestones we have legible text from, {A['n_known']} have a carver with at least three stones, identified by research through a signature on the stone or by its style, and it is on them that the method can be tested. And {A['n_unattributed']} have no carver at all in the database. The question is whether they are one anonymous stream, or whether there are hands among them that still have no name.

We cannot ask the stones, but we can run a test a sceptic would accept: hide the known carvers from ourselves and see whether the method finds them.

## How to search for a hand

We measure how alike two stones are in what a carver carries from stone to stone: the style group, the cross, short-twig runes, the spelling of common words, the punctuation, the bind-runes, the formulas and which rune pairs occur. The content of the text and the place are *not* part of the similarity.

Then we calibrate on stones with a known carver. If two stones lie within 30 kilometres of each other and are alike enough, it is {enn(C['lr'], 1)} times more common that they are by the same carver than by different ones. Seven in ten such pairs really are the same carver ({pr(C['precision'])} per cent). It is a cautious sieve: only {pr(C['tpr'])} per cent of all pairs that *are* by the same carver become so alike that the method catches them. Better few and certain than many and uncertain.

The stones are then formed into groups (those that are alike and lie close together hang together), and we report only groups of at least four stones that are no more spread out than nine in ten known carvers' stones.

## The test: carvers the method has never seen

If one acts as though a known carver were unknown and searches for groups among his stones, {pr(V['purity'])} per cent of the stones in a group are on average by the same carver. Groups of the same number of nearby stones, with no regard to the hand, give {pr(V['purity_geography'])} per cent. That is a good result, but it was computed with thresholds that we ourselves tuned on that very check, so it overestimates.

The stricter test divides the carvers at random into three parts. The threshold is derived on two parts and tested on the third, which the method has never seen, and everything is repeated thirty times with new divisions. The groups are then on average {pr(h['renhet'])} per cent by the same carver, against {pr(h['geografi'])} per cent for nearby stones. (The percentages are higher than in the first test because each sample has only a third of the carvers, which makes the groups easier to get pure. What counts is the distance to the proximity groups.) The difference is {pr(h['skillnad'])} percentage points, with uncertainty between {pr(h['skillnad_ci'][0])} and {pr(h['skillnad_ci'][1])}, and it favoured the groups in all thirty repetitions. The difference thus shrinks from 26 percentage points in the first test to {pr(h['skillnad'])} in the stricter one, and in other settings of distance and sieve it lands between {min(sens)} and {max(sens)}.

Nor does the method rest on anything that merely follows time. Remove style group, cross, dotted runes, prayers and signatures, and recompute the threshold, and the result is {pr(hn['renhet'])} against {pr(hn['geografi'])} per cent. Contemporary stones thus do not look like one hand just because the features follow time.

:::box The weak point
Almost all the carvers we can test on are in the Mälaren valley. Of the {sum(land.values())} known carvers with at least three stones, {land['U']} are in Uppland and {land['Sö']} in Södermanland. Of Uppland's stones, {rate['U']} per cent have a carver in the database and {rate['Sö']} per cent of Södermanland's, but only {rate['Ög']} per cent of Östergötland's, {rate['Sm']} per cent of Småland's, {rate['Vg']} per cent of Västergötland's (not one of {NSTONE['Vg']} stones) and {rate['M']} per cent of Medelpad's. The threshold has therefore never been testable where the candidates are. We tried moving it: trained on Södermanland's carvers and tested on Uppland's, the groups are {pr(so_u['renhet'])} per cent pure against {pr(so_u['geografi'])} for proximity, but that is not certain enough to tell from chance. In the other direction there are too few groups to count at all. So we know that the method works where carvers are known, not that it does in Västergötland.
:::

## Seven groups without a name

After the sieve there are {len(G)} groups of stones without a carver. Half of them, {n_known_en}, resemble a known carver, which is a good sign for the method: it finds what is already known. That leaves seven that resemble no known carver nearby, and an eighth, Dalum, that dropped out. They have been given working names after the parish of the stone nearest the middle, and the name is a label for the group, not a claim about a person.

{MAP_EN}

Five of the groups hold up even without the time-dependent features and when a fifth of the links are removed at random:

**Konungsund** (Östergötland, {cand[2]['n']} stones in {len(cand[2]['parishes'])} parishes, typically within {enn(cand[2]['spread_km'])} km of the middle). In the group the noun precedes the demonstrative (*stæin þenna*, 'stone this', rather than *þenna stæin*) on {pr(KON_ORD['share_group'])} per cent of the stones, against {pr(KON_ORD['share_area'])} per cent for stones within 50 km, the verb *reste* on {pr(KON_REST['share_group'])} per cent against {pr(KON_REST['share_area'])}, and the preposition *æftiR* on {pr(KON_EFT['share_group'])} per cent against {pr(KON_EFT['share_area'])}. The nearest known carver, Traen, is {enn(cand[2]['nearest_carver']['km'])} km away and not as alike as a carver's own stones tend to be. The group is recovered {st(2)} per cent of the time when links are removed and {nt(2)} per cent without the time features.

**Vetlanda** (Småland, {cand[5]['n']} stones). The verb *satte* ('set') instead of *reste* ('raised') is on {pr(VET['share_group'])} per cent of the stones, against {pr(VET['share_area'])} per cent around them. Recovered {st(5)} per cent, {nt(5)} per cent without time.

**Husaby** (Västergötland, {cand[13]['n']} stones). Again *satte*: {pr(HUS['share_group'])} per cent against {pr(HUS['share_area'])} per cent in the district. Recovered {st(13)} per cent, {nt(13)} per cent without time.

**Leksberg** (Västergötland, {cand[12]['n']} stones, about two kilometres between the most distant). The ending *-ʀ* written with an ordinary r instead of the yr-rune is on {pr(LEK['share_group'])} per cent of the stones, against {pr(LEK['share_area'])} per cent in the district. Recovered {st(12)} per cent, {nt(12)} per cent without time.

**Kölaby** (Västergötland, {cand[6]['n']} stones). The weakest of the five, with dotted runes on every stone against fewer than half of the stones in the district. Recovered {st(6)} per cent, {nt(6)} per cent without time.

Two groups hold only in part. **Viby** (Östergötland, {cand[4]['n']} stones, the spelling *e-…-iR* of *efter* on {pr(VIB['share_group'])} per cent against {pr(VIB['share_area'])}) is recovered {st(4)} per cent of the time but only {nt(4)} per cent without the time features. **Sättna** in Medelpad ({cand[11]['n']} stones) has the verb *rätte* ('set upright') on {pr(SAT['share_group'])} per cent of the stones and no other stone in the district has it, but the group is small and is recovered {nt(11)} per cent of the time without time. **Dalum** ({cand[14]['n']} stones) is recovered {nt(14)} per cent without the time features and does not count.

The features listed are those in which a group differs most from its surroundings. Because the groups are formed by likeness in those very features, the list shows what the group looks like, not that it is one hand. The validation above speaks for that, and only where carvers are known.

## Carver, workshop or tradition

A group that writes alike can have three explanations we cannot tell apart: one carver, a workshop with several hands, or a local writing habit that many shared (the verb *satte* may just as well be the commissioners' word as the carver's). What separates them is something we have not measured here: how the runes are cut, the ornament, and whether tool marks agree from stone to stone. A first step is to examine the stones of the Husaby and Leksberg groups in the field or in 3D. And a runologist who knows Västergötland's stones can probably say quickly whether the groups have already been described.

:::box How we counted
Basis: {enn(A['n_stones'])} Viking-age runestones in the Scandinavian Runic-text Database with at least five legible words and coordinates. Similarity is Gower's distance (which handles both yes/no features and categories) on style group, cross, short-twig runes, some twenty linguistic features, formulas and rune bigrams. The threshold for linking two stones was chosen so that pairs under it are at least twelve times more common among the same carver's pairs than among different carvers', among pairs within 30 km. The groups were found with the Louvain method for networks. Stability is the share of a group that returns when a fifth of the links are removed at random, fifty times. The hold-out test divides the carvers (not the stones) at random into three parts, derives the threshold and the greatest spread on two and forms groups on the third; the comparison is groups of the same number of nearby stones from the same third. Thirty repetitions; p-values across the repetitions are not counted because the stones are shared between them, and we report the interval of the difference across the repetitions. The candidates have not been compared with the literature. All code and results are open in the repository (r/anonymous.R, utdata/ristare).
:::

:::box The essentials in brief
- A method that searches for groups of stones with the same handwriting finds the right carver clearly more often than chance and proximity alone, even for carvers it has not seen – but the effect is smaller than we first measured (17 percentage points against 26).
- The method has been tested only in the Mälaren valley. Where the candidate groups are, in Östergötland, Småland, Västergötland and Medelpad, hardly any stones have a known carver, so it cannot be tested.
- Five groups hold up even when time-dependent features are removed. They are hypotheses about a carver, a workshop or a local writing habit, and the deciding step is an examination of the stones themselves.
:::

## Sources and data

Scandinavian Runic-text Database (Uppsala University, ODbL), Vitki's R module Unknown carvers.

*Data: Scandinavian Runic Text Database (Uppsala University).*"""

# aldrig siffra först i en mening (husregeln); bild- och diagramrader räknas inte
for b in (body, body_en):
    flat = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", b)
    flat = "\n".join(line for line in flat.splitlines() if "|" not in line and not line.startswith(":::"))
    for m in re.finditer(r"[.!?]\s+(\d)", flat.replace("\n", " ")):
        ctx = flat.replace("\n", " ")[max(0, m.start() - 40):m.end() + 20]
        raise AssertionError(f"Mening börjar med siffra: …{ctx}…")

out = {"slug": "mojliga-ristare-utan-namn", "title": title, "summary": summary, "body": body,
       "title_en": "Possible Carvers Without Names",
       "summary_en": ("One in three runestones has a known carver; the rest are anonymous. We had the computer search for "
                      "groups of nameless stones that resemble each other in spelling, formulas and style as much as one "
                      "carver's stones do. The method was first tested on carvers it had never seen – and passed. But it "
                      "is calibrated only in the Mälaren valley, and the seven groups lie somewhere else."),
       "body_en": body_en}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "ristareartikel.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "ristareartikel.json"), len(body), len(body_en))

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        json.dump({k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in old.items()},
                  open(os.path.join(ROOT, f"utdata/blogg/{old['slug']}.FORE.json"), "w"), ensure_ascii=False, indent=1, default=str)
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Ristare|okända", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
