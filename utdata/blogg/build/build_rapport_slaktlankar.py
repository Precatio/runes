"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4; Metodrapport, delvis prövad): länkningen av samma
släkt över flera runstenar med avståndsband (src/linking.py sedan 2026-11-01). Planerna
analysplaner/2026-11-01-slaktnatverket-steg1.md och -steg1b.md. Alla siffror asserteras mot data/links.json och
utdata/slakt/ (steg1.json, handprov_resultat.json, williams1990_bilaga.json, peterson2007_samma_person.json, steg2a.json).
    ../../../.venv/bin/python build_rapport_slaktlankar.py [--write | --update DOC]"""
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
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 1
TODAY = "2026-11-01"
TL_SV = ("länkmodellen byggdes 2026-10-27; analysplanen för länkningen med avståndsband låstes och kördes 2026-11-01; "
         "planen för det blinda handprovet låstes och provet bedömdes 2026-11-01")
TL_EN = ("the linking model was built 2026-10-27; the analysis plan for linking with distance bands was locked and run "
         "2026-11-01; the plan for the blind hand test was locked and the test was judged 2026-11-01")
SD = os.path.join(ROOT, "utdata", "slakt")
J = lambda *p: json.load(open(os.path.join(*p), encoding="utf-8"))  # noqa: E731
D = J(ROOT, "data", "links.json")
S1, H, W, P, F = J(SD, "steg1.json"), J(SD, "handprov_resultat.json"), J(SD, "williams1990_bilaga.json"), J(SD, "peterson2007_samma_person.json"), J(SD, "steg2a.json")
SHA = {k: open(os.path.join(ROOT, "analysplaner", f"{k}.sha256")).read().split()[0][:16]
       for k in ("2026-11-01-slaktnatverket-steg1", "2026-11-01-slaktnatverket-steg1b")}
assert SHA == {"2026-11-01-slaktnatverket-steg1": "403fa352cc19e0f2", "2026-11-01-slaktnatverket-steg1b": "f3ba7e7872794e87"}

pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731

# ---- the material and the expert lists ---------------------------------------------------------------------------------
assert (W["n_groups"], W["n_members"], W["n_pairs"], W["n_pairs_sure"]) == (144, 382, 613, 355)
PV = P["validation"]
assert (PV["n_pairs"], PV["n_in_williams"]) == (118, 110)
# ---- step 1 (Swedish runestones) -----------------------------------------------------------------------------------
M0, M1, M2 = S1["M0"], S1["M1"], S1["sensitivity"]["null_province_banded"]
assert S1["n_stones"] == 2320 and not S1["M1_holds"]
assert (M0["n_sure"], M0["W1"]["hit"], M0["W1"]["n_stones"], M0["W2"]["hit"], M0["W2"]["n_links"], M0["J"]["sure"]) == (23, 34, 202, 19, 21, 0)
assert (M1["n_sure"], M1["W1"]["hit"], M1["W2"]["hit"], M1["W2"]["n_links"], M1["J"]["sure"], M1["K"]["share"]) == (47, 69, 42, 45, 1, 0.0)
assert (M2["n_sure"], M2["W1"]["hit"], M2["W2"]["hit"], M2["W2"]["n_links"], M2["J"]["sure"]) == (59, 80, 54, 57, 6)
assert (pc(M0["W1"]["share"]), pc(M1["W1"]["share"]), pc(M2["W1"]["share"]), pc(M2["W2"]["share"])) == (17, 34, 40, 95)
# ---- the blind hand test ----------------------------------------------------------------------------------------------
HP = H["primary"]
assert H["verdict"] == "inte avgörande" and (HP["k"]["ny"], HP["k"]["känd"], HP["k"]["namn"]) == (5, 3, 3)
assert 0.0035 < HP["fisher_p"] < 0.0037 and H["per_group"]["namn"] == {"N": 6, "?": 6, "J": 3}
# ---- the model in the app (all Nordic runestones; Swedish links counted apart) --------------------------------------
assert (D["n_stones"], D["n_links"], D["n_sure"], D["n_sure_pooled"], D["n_contradicted"]) == (2633, 420, 70, 28, 2)
assert [x["n_sure"] for x in D["seeds"]] == [70, 70, 70] and D["n_sure_by_band"] == {"A": 42, "B": 23, "C": 2, "utan koordinater": 3}
NB, OB = D["null_mean_by_band"], D["obs_by_band"]
assert (round(NB["A"]), round(NB["B"]), round(NB["C"]), OB["A"], OB["B"], OB["C"]) == (3, 14, 329, 42, 40, 323)
SE = ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "J", "D", "Bo", "Vr")
sure_se = [x for x in D["links"] if x["q"] < 0.1 and not x["contradictions"] and x["a"].split(" ")[0] in SE and x["b"].split(" ")[0] in SE]
assert len(sure_se) == 61
assert (D["validation"]["parsten"]["found"], D["validation"]["parsten"]["n"], D["validation"]["rundata_noted"]["found"]) == (6, 14, 9)
assert 0.36 < D["validation"]["jarlabanke"]["q_max"] < 0.37 and pc(D["share_sure_within_10km"]) == 97 and D["n_sure_interval"] == [68.0, 70.0]
assert (D["validation"]["parsten"]["missed_shared_none"], D["validation"]["parsten"]["missed_shared_one"]) == (5, 3)
# ---- the families (step 2a) ------------------------------------------------------------------------------------------
assert (F["n_families"], F["stones_in_families"], F["persons_in_families"], F["persons_on_2plus"]) == (42, 95, 175, 105)
assert F["by_size"] == {"2": 35, "3": 3, "4": 4} and max(int(k) for k in F["by_generations"]) == 3 and F["by_province"]["U"] == 32
NEW = [("U 941", "U 986"), ("U 1027", "U 1047"), ("U 147", "U 287")]
# Williams against the links as they stand in the app (all Nordic runestones; Swedish links)
WPROV = {"Ög", "Sö", "Sm", "Vg", "U", "Vs", "Hs"}
WG = {}
for gi, g in enumerate(W["groups"]):
    for mm in g["members"]:
        if mm["rundata"]:
            WG.setdefault(mm["rundata"], set()).add(gi)
w2a = [x for x in sure_se if x["a"].split(" ")[0] in WPROV and x["b"].split(" ")[0] in WPROV]
W2A = (sum(1 for x in w2a if WG.get(x["a"], set()) & WG.get(x["b"], set())), len(w2a))
assert W2A == (54, 59) and pc(W2A[0] / W2A[1]) == 92
N_SE, N_ALL = "2 320", "2 633"
assert S1["n_stones"] == 2320 and D["n_stones"] == 2633

SLUG = "slaktlankar-mellan-runstenar"
title = "Samma släkt på flera runstenar: en öppen länkmodell återfinner 40 procent av runologernas släktsamband, och 92 procent av dess länkar står i deras förteckning"
title_en = "The same family on several runestones: an open linking model recovers 40 per cent of the runologists' family ties, and 92 per cent of its links stand in their list"
summary = ("Metodrapport. En modell som länkar runstenar som delar namn, prövad mot slumpen på samma avstånd, hittar på egen hand "
           "40 procent av de stenar som runologerna har knutit samman, och nio av tio av dess länkar står i deras förteckning. "
           "Räknesättet valdes efter att ha sett förteckningen, och ett blint handprov var inte avgörande.")
summary_en = ("Methods report. A model that links runestones sharing names, tested against chance at the same distance, finds on "
              "its own 40 per cent of the stones that runologists have tied together, and nine in ten of its links stand in their "
              "list. The way of counting was chosen after seeing the list, and a blind hand test was not decisive.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/forskningsrapporter/{SLUG}")


def chart(sv):
    f = (lambda x: f"{min(100.0, 100 * x):.0f}")
    rows = [":::chart Kandidatpar som slumpen väntas ge, andel av paren i data" if sv else
            ":::chart Candidate pairs that chance is expected to give, share of the pairs in the data"]
    for bd, lab_sv, lab_en in (("A", "Upp till 2 km", "Up to 2 km"), ("B", "2–10 km", "2–10 km"), ("C", "Över 10 km", "Over 10 km")):
        rows.append(f"{'+' if bd == 'A' else ''}{lab_sv if sv else lab_en} | {f(NB[bd] / OB[bd])} | "
                    f"{round(NB[bd])} {'av' if sv else 'of'} {OB[bd]} {'par' if sv else 'pairs'}")
    rows += ["Diagram: Vitki. Källa: Samnordisk runtextdatabas, 2 000 nollkörningar; över 10 km ger slumpen fler par än data."
             if sv else "Chart: Vitki. Source: the Scandinavian Runic-text Database, 2,000 null runs; beyond 10 km chance gives more pairs than the data.", ":::"]
    return "\n".join(rows)


body = f"""*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, prosopografi, släkter, personnamn, länkning, nollmodell, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Vad som inte är prövat.** Räknesättet med avståndsband valdes efter att ha sett runologernas förteckning, som också är det främsta facit. Det blinda handprov som skulle pröva det på nytt var inte avgörande: bedömaren kände bara igen 3 av 5 kända släktlänkar ur texterna, mot kravet 4.
**Bakgrund och syfte.** Samma människor står ofta på flera runstenar. Runologerna har knutit samman sådana stenar för hand (Williams 1990; Peterson 2007), men det finns ingen öppen metod som gör det med angiven osäkerhet och som kan köras om när data ändras. Syftet är att bygga och pröva en sådan.
**Material.** De {N_SE} svenska vikingatida runstenarna i Samnordisk runtextdatabas med personernas namn, roller och släktband, och Henrik Williams förteckning över inskrifter med genealogiskt samband (1990), avskriven för hand: {W['n_groups']} grupper, {W['n_members']} inskrifter.
**Metod.** Två stenar är kandidater när de delar minst två ovanliga personnamn eller ett gårdsnamn. Kandidaterna prövas mot en nollmodell där namnen blandas mellan stenarna inom landskapet, och andelen falska länkar räknas för sig i tre avståndsband. Två förregistrerade planer: jämförelsen med Williams och ett blint handprov.
**Resultat.** Modellen ger {len(sure_se)} länkar mellan svenska runstenar, mot 23 med den tidigare modellen. Den hittar {M2['W1']['hit']} av {M2['W1']['n_stones']} stenar som Williams knyter samman ({pc(M2['W1']['share'])} procent, mot {pc(M0['W1']['share'])} tidigare), och {W2A[0]} av {W2A[1]} ({pc(W2A[0] / W2A[1])} procent) av länkarna står i hans grupper. I handprovet bedömdes alla 5 länkar utanför Williams som samma släkt, mot 3 av 15 namnpar som modellen inte länkar.
**Slutsats.** Avståndet är nyckeln. Släktlänkar ligger nästan alltid inom en mil, och där är slumpens par få. Modellen återfinner experternas länkar träffsäkert, men nätverket den ger är tunt: {F['n_families']} släkter över {F['stones_in_families']} stenar. Den duger som öppet, prövat underlag, inte som ersättning för den runologiska läsningen.

## 1. Inledning

Runstenarnas texter nämner tusentals människor, och många av dem står på mer än en sten. Att knyta ihop dem är grunden för all släktforskning i materialet. Henrik Williams (1990, bilaga s. 185–187) sammanställde de samband som Sveriges runinskrifter och Fornvännen hade pekat ut, landskap för landskap, och påpekade att många vilar på ett ovanligt namn eller på geografisk närhet. Lena Peterson (2007) markerar i Nordiskt runnamnslexikon de fall där belägg på olika stenar avser samma person, efter Williams och andra. Tristan Mueller-Vollmer (2021) byggde en relationsdatabas över namnen på svenska runstenar för en studie av namnskicket; den är inte öppen.

Sambanden används för datering och för frågor om arv: Birgit Sawyer (2000) läste runstenarna som förklaringar om vem som ärvde. Men förteckningarna är gjorda för hand, utan angiven osäkerhet, och kan inte köras om när läsningar ändras. Syftet här är att bygga en öppen modell som länkar stenar med en uppskattad andel falska länkar, och att pröva den mot experternas förteckning och i ett blint prov.

## 2. Förregistrering: proven och deras planer

**Steg 1** (plan låst 2026-11-01, SHA-256 `{SHA['2026-11-01-slaktnatverket-steg1']}…`). Planen jämförde appens tidigare modell med en ny där nollmodellen blandar namnen inom häradet och andelen falska länkar räknas per avståndsband. Den nya skulle minst fördubbla täckningen mot Williams (och nå minst 25 procent), inte bli mer än tio procentenheter mindre träffsäker, länka alla tio par bland Jarlabankes fem stenar och ha högst 5 procent motsägelser. Före låsningen var bara den tidigare modellens resultat kända. Den nya modellen klarade alla villkor utom Jarlabanke (1 av 10 par) och infördes därför inte.

**Efter steg 1.** Känslighetsanalysen visade att samma avståndsband med nollmodellen inom landskapet fungerade bäst ({M2['n_sure']} länkar, {pc(M2['W1']['share'])} procents täckning, 6 av 10 Jarlabankepar). Det är den modell som rapporten gäller. Den valdes efter att ha sett Williams förteckning och kan därför inte prövas mot den. Petersons anmärkningar kunde inte ersätta den: {PV['n_in_williams']} av hennes {PV['n_pairs']} svenska släktpar står redan hos Williams.

**Steg 1b, det blinda handprovet** (plan låst 2026-11-01, SHA-256 `{SHA['2026-11-01-slaktnatverket-steg1b']}…`). 25 par drogs med ett fast slumpfrö: de 5 länkar utanför Williams förteckning, 5 av hans säkra par och 15 namnpar som modellen inte länkar. De blandades och visades för bedömaren, Viktor Kvant, utan signum. Gränserna: minst 3 av 5 nya bedömda som samma släkt, fler sådana bedömningar bland de nya än bland namnparen (Fishers exakta test, p under 0,05), och minst 4 av 5 kända länkar igenkända. Annars är provet inte avgörande. Svaren checkades in innan nyckeln öppnades.

## 3. Material

- **Inskrifterna.** Samnordisk runtextdatabas (Rundata), svenska vikingatida runstenar: {N_SE} stenar. Modellen körs på alla {N_ALL} nordiska runstenar, och de svenska länkarna redovisas för sig. Bara runstenar.
- **Personerna** läses ur Rundatas engelska översättning och normalisering med regler: namn, roll (den som reser, den som minns, ristaren, nämnd), släktband och gårdsnamn. Ristarna länkar inte. Reglerna är prövade blint på 60 stenar: rätt roll för 90 procent av personerna, och ungefär vart fjärde släktband fångas inte.
- **Williams förteckning** (1990, bilaga s. 185–187), avskriven för hand ur en skanning: {W['n_groups']} grupper, {W['n_members']} inskrifter, {W['n_pairs_sure']} säkra par enligt hans notation.
- **Petersons anmärkningar** (2007), tolkade ur två textversioner av lexikonet och bara där båda läser likadant, utan ristare och utan Ingvars-, Knuts- och Frögersstenarna, som Williams också undantar: {PV['n_pairs']} svenska släktpar.

## 4. Metod

**4.1 Kandidaterna och styrkan.** Två stenar är kandidater när de delar minst två personnamn eller ett gårdsnamn, och minst ett av de delade namnen står på högst 60 runstenar. Varje delat namn vägs efter hur ovanligt det är, log(N/n), där n är antalet stenar med namnet. Länkens styrka är summan.

**4.2 Nollmodellen och avstånden.** Namnen blandas mellan stenarna inom landskapet 2 000 gånger. Varje sten behåller sitt antal namn och varje namn sitt antal stenar. För varje kandidat räknas andelen falska länkar (q) som det väntade antalet lika starka par i nollmodellen delat med antalet i data, och det görs för sig i tre band: upp till 2 km, 2–10 km och över 10 km mellan stenarna. En länk är säker när q är under 0,1, alltså när högst var tionde så stark länk på det avståndet väntas vara slump (jfr Benjamini & Hochberg 1995; Storey & Tibshirani 2003).

**4.3 Motsägelser.** En länk avfärdas när stenarna ger samma namn olika fäder eller mödrar, eller när en person är död på en sten och reser en sten som enligt stilgrupperna är minst 30 år yngre.

**4.4 Prövningen.** Täckning: andelen av de runstenar som ingår i ett säkert par hos Williams som modellen knyter till minst en annan sten i samma grupp. Träffsäkerhet: andelen av modellens länkar, i de landskap Williams tar upp, där båda stenarna står i samma grupp hos honom. Det är ett golv, eftersom förteckningen inte är fullständig. Handprovet enligt 2.

**4.5 Avvikelser och rättelser.** Planen för handprovet angav 270 säkra par hos Williams; det är 270 rader och 266 unika par, eftersom några stenar står i två grupper. Bedömningen gjordes i en webbsida med samma par, ordning och texter som formuläret. Inga kodfel rättades efter körningarna. Ett första försök med Fellegi–Sunter-länkning (Fellegi & Sunter 1969), 2026-10-27, fångade bygd snarare än identitet och används inte.

## 5. Resultat

**5.1 Handprovet mot gränserna.** Alla {HP['n']['ny']} nya länkar bedömdes som samma släkt. Av de kända länkarna bedömdes {HP['k']['känd']} som samma släkt och 2 som osäkra. Av namnparen bedömdes {HP['k']['namn']} som samma släkt, 6 som osäkra och 6 som inte samma släkt. Skillnaden mellan de nya länkarna och namnparen ger p = {HP['fisher_p']:.4f} (Fishers exakta test, ensidigt), men villkoret om de kända länkarna uppfylldes inte, så provet är enligt planen inte avgörande. I klartext: varje länk som modellen ensam hittade bedömdes blint som samma släkt, mot var femte av de namnpar den inte länkar, men bedömaren kände bara säkert igen tre av fem länkar som experterna redan gjort. Av kommentarerna framgår varför: i det ena paret (Ög 81 och Ög 84) vilar Williams samband på en ristare, Þorkell, och i det andra (U 136 och U 147) krävs kunskap om Jarlabankes släkt utöver de två texterna.

**5.2 Mot Williams och per avstånd.** På de svenska runstenarna, med samma material för alla:

- Den tidigare modellen (en pool, nollmodell inom landskapet): {M0['n_sure']} länkar, täckning {M0['W1']['hit']} av {M0['W1']['n_stones']} stenar ({pc(M0['W1']['share'])} procent), träffsäkerhet {M0['W2']['hit']} av {M0['W2']['n_links']}, Jarlabanke 0 av 10.
- Avståndsband med nollmodell inom häradet (steg 1:s plan): {M1['n_sure']} länkar, täckning {pc(M1['W1']['share'])} procent, träffsäkerhet {M1['W2']['hit']} av {M1['W2']['n_links']}, inga motsägelser, Jarlabanke 1 av 10.
- Avståndsband med nollmodell inom landskapet (rapportens modell): {M2['n_sure']} länkar, täckning {M2['W1']['hit']} av {M2['W1']['n_stones']} ({pc(M2['W1']['share'])} procent), träffsäkerhet {M2['W2']['hit']} av {M2['W2']['n_links']} ({pc(M2['W2']['share'])} procent), Jarlabanke 6 av 10.

Körd på alla nordiska runstenar, som den används, ger samma modell {len(sure_se)} länkar mellan svenska stenar: täckning {M2['W1']['hit']} av {M2['W1']['n_stones']}, träffsäkerhet {W2A[0]} av {W2A[1]} ({pc(W2A[0] / W2A[1])} procent). Skillnaden kommer av att nollmodellens par per avstånd då räknas på fler stenar.

Förklaringen syns i avstånden. Upp till 2 km ger slumpen i genomsnitt {round(NB['A'])} kandidatpar mot {OB['A']} i data, men över 10 km {round(NB['C'])} mot {OB['C']}: där ger slumpen fler par än verkligheten. När alla avstånd prövas i en pool drunknar de nära, äkta länkarna i de avlägsna, slumpmässiga.

{chart(True)}

Häradsmodellen var för sträng mot stora släkter: sju av Jarlabankes nio stenar står i samma härad, så när namnen blandas inom häradet återskapar slumpen hans släkt. U 127 står 10–14 km från de andra Jarlabankestenarna och blir aldrig säker; där är slumpens par för många.

**5.3 Stabilitet och kalibrering.** Körd på alla nordiska runstenar ger modellen {D['n_sure']} säkra länkar med alla fyra slumpfrön (68–70 när nollkörningarna dras om), {D['n_sure_by_band']['A']} upp till 2 km, {D['n_sure_by_band']['B']} på 2–10 km och {D['n_sure_by_band']['C']} längre bort. {len(sure_se)} av dem förenar svenska runstenar. Två länkar avfärdas av motsägelser. Länkarna anger högst 10 procent falska; mot Williams är {pc(W2A[0] / W2A[1])} procent bekräftade, vilket stämmer med det, med reservation för att några obekräftade kan vara riktiga. Rundatas parstenar: {D['validation']['parsten']['found']} av {D['validation']['parsten']['n']} hittas, mot 2 tidigare; av de missade delar de flesta inget läst namn alls.

**5.4 Vad nätverket ger (beskrivande).** De svenska länkarna knyter ihop {F['stones_in_families']} runstenar i {F['n_families']} släkter med {F['persons_in_families']} personer, varav {F['persons_on_2plus']} står på minst två stenar. 35 släkter består av två stenar, 3 av tre och 4 av fyra, och högst tre generationer kan följas. {F['by_province']['U']} av släkterna finns i Uppland. Tre länkar anges varken av Rundata, Williams eller Peterson: U 941 och U 986 (Áli, Ingifastr och Sigvaldi, 5 km isär), U 1027 och U 1047 (Gísl och Ígull, 10 km) och U 147 och U 287 (Ingifastr och Ingvarr, 10 km).

## 6. Diskussion

**Vad metoden klarar.** Den återfinner runologernas länkar träffsäkert och gör det öppet, med en angiven andel falska länkar som kan räknas om när Rundata ändras. Avståndet är det som gör skillnaden: släktlänkar ligger nästan alltid inom en mil (97 procent av länkarna), och där är slumpens namnpar få.

**Var metoden inte ska användas.**

1. **Långt isär.** Över 10 km ger slumpen fler namnpar än data. En länk där är nästan aldrig säker, även när den är äkta, som U 127 hos Jarlabanke.
2. **Vanliga namn.** Par som bara delar Sveinn, Bjôrn, Þorsteinn eller Ulfr prövas inte. Många verkliga släkter med vanliga namn syns därför inte.
3. **Ristare och kända män.** Ristarna länkar inte, och Ingvarr, Knútr och Frøgærr på flera stenar är kända män, inte släktingar.
4. **Skadade texter och missade släktband.** Ungefär vart fjärde släktband på en sten fångas inte av reglerna, och ett namn som inte kan läsas länkar inget. Modellen ser bara det som står i Rundatas läsning.
5. **Arvsfrågor i stor skala.** Nätverket är tunt: 4 procent av runstenarna, mest par av två stenar. Det räcker för fallstudier men ger svaga statistiska prov.

**Mot tidigare forskning.** Williams förteckning är bredare. Den bygger också på lokalkännedom, ristare och litteratur, och modellen hittar fyra av tio av hans stenar. Det modellen tillför är prövbarheten: varje länk har en uppskattad osäkerhet, och förteckningen kan räknas om.

**Svagheter, i ordning efter vikt.**

1. **Efterhandsvalet.** Räknesättet valdes efter att ha sett det främsta facit, och det blinda provet var inte avgörande.
2. **Handprovet är litet** och har en enda bedömare. De fem nya länkarna är för få för en säker andel.
3. **Facit är inte oberoende av texterna.** Williams samband bygger på samma inskrifter, ibland på sådant modellen inte ser.
4. **Reglerna som läser personerna** missar en del av släktbanden, och det sänker täckningen.

**Vad som skulle fälla metoden.** Att länkar som modellen kallar säkra ofta visade sig vara olika släkter när en runolog prövar dem blint, eller att andelen bekräftade länkar sjönk tydligt i en oberoende förteckning.

## 7. Slutsats

En öppen modell som prövar namnpar mot slumpen på samma avstånd återfinner {pc(M2['W1']['share'])} procent av runologernas släktsamband, och {pc(W2A[0] / W2A[1])} procent av dess länkar står i deras förteckning. Avståndet är nyckeln. Valet av räknesätt gjordes efter att ha sett facit, och det blinda provet var inte avgörande, så metoden är delvis prövad. Nästa steg är en blind prövning med flera bedömare och fler par.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION} ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts fram till den 1 november 2026. Någon release med DOI finns ännu inte. All kod, planerna och resultaten finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Planerna: `analysplaner/2026-11-01-slaktnatverket-steg1.md` och `analysplaner/2026-11-01-slaktnatverket-steg1b.md`, med kontrollsummorna bredvid.
- Länkmodellen: `src/linking.py` (avståndsbanden `null_scores_banded`, `fdr_banded`) och `scripts/link_entities.py` → `data/links.json`; personerna `src/entities.py`.
- Steg 1: `utdata/slakt/steg1.py` → `steg1.json`, `steg1_resultat.md`. Williams avskrift: `utdata/slakt/williams1990_bilaga.py`. Petersons anmärkningar: `utdata/slakt/peterson2007_samma_person.py`.
- Handprovet: `utdata/slakt/handprov.py`, svaren `handprov_svar.json`, nyckeln `handprov_nyckel.json`, resultatet `handprov_resultat.md`.
- Släkterna: `utdata/slakt/steg2a.py` → `steg2a.json`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_slaktlankar.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer.

## Referenser

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society, Series B* 57 (1), s. 289–300.
- Fellegi, I. P. & Sunter, A. B. 1969. A theory for record linkage. *Journal of the American Statistical Association* 64 (328), s. 1183–1210.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md, avsnitt 1r). https://github.com/Precatio/runes
- Mueller-Vollmer, T. 2021. *Personal Names on Swedish Viking Age Runestones*. Doktorsavhandling, University of Wisconsin–Madison.
- Peterson, L. 2007. *Nordiskt runnamnslexikon*. 5 uppl. Uppsala: Institutet för språk och folkminnen.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Storey, J. D. & Tibshirani, R. 2003. Statistical significance for genomewide studies. *Proceedings of the National Academy of Sciences* 100 (16), s. 9440–9445.
- Williams, H. 1990. *Åsrunan. Användning och ljudvärde i runsvenska steninskrifter*. Runrön 3. Uppsala: Institutionen för nordiska språk.

:::box Det viktigaste i korthet
- Samma människor står på flera runstenar, och en öppen modell kan hitta dem med en angiven osäkerhet, om namnparen prövas mot slumpen på samma avstånd.
- Avståndet avgör: släktlänkarna ligger nästan alltid inom en mil, och där är slumpens namnpar få.
- Modellen återfinner experternas länkar träffsäkert men bara en del av dem; den är ett prövbart underlag, inte en ersättning för runologens läsning.
- Räknesättet valdes efter att ha sett facit, och det blinda provet var inte avgörande; nästa steg är fler bedömare.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Methods report, partially tested. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. Cite as: {CITE_EN}. Keywords: runestones, Viking Age, prosopography, families, personal names, record linkage, null model, pre-registration. Competing interests: none. Funding: none.*

## Abstract

**What is not tested.** The way of counting with distance bands was chosen after seeing the runologists' list, which is also the main yardstick. The blind hand test meant to test it anew was not decisive: the judge recognised only 3 of 5 known family links from the texts, against the required 4.
**Background and aim.** The same people often stand on several runestones. Runologists have tied such stones together by hand (Williams 1990; Peterson 2007), but there is no open method that does so with a stated uncertainty and can be rerun when the data change. The aim is to build and test one.
**Material.** The 2,320 Swedish Viking-Age runestones in the Scandinavian Runic-text Database with the persons' names, roles and kin ties, and Henrik Williams's list of inscriptions with genealogical ties (1990), transcribed by hand: {W['n_groups']} groups, {W['n_members']} inscriptions.
**Method.** Two stones are candidates when they share at least two uncommon personal names or a farm name. Candidates are tested against a null model in which the names are shuffled between the stones within the province, and the share of false links is counted separately in three distance bands. Two pre-registered plans: the comparison with Williams and a blind hand test.
**Results.** The model gives {len(sure_se)} links between Swedish runestones, against 23 with the earlier model. It finds {M2['W1']['hit']} of the {M2['W1']['n_stones']} stones that Williams ties together ({pc(M2['W1']['share'])} per cent, against {pc(M0['W1']['share'])} before), and {W2A[0]} of {W2A[1]} ({pc(W2A[0] / W2A[1])} per cent) of the links stand in his groups. In the hand test all 5 links outside Williams were judged the same family, against 3 of 15 name pairs the model does not link.
**Conclusion.** Distance is the key. Family links almost always lie within ten kilometres, and there chance gives few pairs. The model recovers the experts' links accurately, but the network it gives is thin: {F['n_families']} families across {F['stones_in_families']} stones. It serves as open, tested groundwork, not as a replacement for runological reading.

## 1. Introduction

The runestone texts name thousands of people, and many of them stand on more than one stone. Tying them together is the basis of all family research in the material. Henrik Williams (1990, appendix pp. 185–187) compiled the ties that Sveriges runinskrifter and Fornvännen had pointed out, province by province, and noted that many rest on an uncommon name or on geographical closeness. Lena Peterson (2007) marks in Nordiskt runnamnslexikon the cases where attestations on different stones refer to the same person, following Williams and others. Tristan Mueller-Vollmer (2021) built a relational database of the names on Swedish runestones for a study of naming practice; it is not open.

The ties are used for dating and for questions of inheritance: Birgit Sawyer (2000) read the runestones as declarations of who inherited. But the lists are made by hand, without a stated uncertainty, and cannot be rerun when readings change. The aim here is to build an open model that links stones with an estimated share of false links, and to test it against the experts' list and in a blind test.

## 2. Pre-registration: the tests and their plans

**Step 1** (plan locked 2026-11-01, SHA-256 `{SHA['2026-11-01-slaktnatverket-steg1']}…`). The plan compared the app's earlier model with a new one in which the null model shuffles the names within the hundred (härad) and the share of false links is counted per distance band. The new one had to at least double the coverage against Williams (and reach at least 25 per cent), not lose more than ten percentage points of precision, link all ten pairs among Jarlabanke's five stones and have at most 5 per cent contradictions. Before the lock only the earlier model's results were known. The new model met every condition except Jarlabanke (1 of 10 pairs) and was therefore not introduced.

**After step 1.** The sensitivity analysis showed that the same distance bands with the null model within the province worked best ({M2['n_sure']} links, {pc(M2['W1']['share'])} per cent coverage, 6 of 10 Jarlabanke pairs). That is the model this report concerns. It was chosen after seeing Williams's list and cannot therefore be tested against it. Peterson's notes could not replace it: {PV['n_in_williams']} of her {PV['n_pairs']} Swedish family pairs already stand in Williams.

**Step 1b, the blind hand test** (plan locked 2026-11-01, SHA-256 `{SHA['2026-11-01-slaktnatverket-steg1b']}…`). 25 pairs were drawn with a fixed seed: the 5 links outside Williams's list, 5 of his sure pairs and 15 name pairs the model does not link. They were shuffled and shown to the judge, Viktor Kvant, without signa. The limits: at least 3 of 5 new links judged the same family, more such judgements among the new than among the name pairs (Fisher's exact test, p below 0.05), and at least 4 of 5 known links recognised. Otherwise the test is not decisive. The answers were committed before the key was opened.

## 3. Material

- **The inscriptions.** The Scandinavian Runic-text Database (Rundata), Swedish Viking-Age runestones: 2,320 stones. The model runs on all 2,633 Nordic runestones, and the Swedish links are reported separately. Runestones only.
- **The persons** are read from Rundata's English translation and normalisation by rules: name, role (the one who raises, the one commemorated, the carver, mentioned), kin ties and farm names. Carvers do not link. The rules were tested blind on 60 stones: the right role for 90 per cent of the persons, and about one kin tie in four is not caught.
- **Williams's list** (1990, appendix pp. 185–187), transcribed by hand from a scan: {W['n_groups']} groups, {W['n_members']} inscriptions, {W['n_pairs_sure']} sure pairs by his notation.
- **Peterson's notes** (2007), parsed from two text versions of the lexicon and only where both read alike, without carvers and without the Ingvarr, Knútr and Frøgærr stones, which Williams also leaves out: {PV['n_pairs']} Swedish family pairs.

## 4. Method

**4.1 The candidates and the strength.** Two stones are candidates when they share at least two personal names or a farm name, and at least one of the shared names stands on at most 60 runestones. Each shared name is weighted by how uncommon it is, log(N/n), where n is the number of stones with the name. The link's strength is the sum.

**4.2 The null model and the distances.** The names are shuffled between the stones within the province 2,000 times. Each stone keeps its number of names and each name its number of stones. For each candidate the share of false links (q) is the expected number of equally strong pairs in the null model divided by the number in the data, and this is done separately in three bands: up to 2 km, 2–10 km and over 10 km between the stones. A link is sure when q is below 0.1, that is when at most one in ten links that strong at that distance is expected to be chance (cf. Benjamini & Hochberg 1995; Storey & Tibshirani 2003).

**4.3 Contradictions.** A link is rejected when the stones give the same name different fathers or mothers, or when a person is dead on one stone and raises a stone that by the style groups is at least 30 years younger.

**4.4 The tests.** Coverage: the share of the runestones in a sure Williams pair that the model ties to at least one other stone of the same group. Precision: the share of the model's links, in the provinces Williams covers, where both stones stand in the same group of his. It is a floor, since the list is not complete. The hand test as in 2.

**4.5 Deviations and corrections.** The hand-test plan stated 270 sure pairs in Williams; these are 270 rows and 266 unique pairs, since a few stones stand in two groups. The judging was done in a web page with the same pairs, order and texts as the form. No code errors were corrected after the runs. A first attempt with Fellegi–Sunter linkage (Fellegi & Sunter 1969), 2026-10-27, captured district rather than identity and is not used.

## 5. Results

**5.1 The hand test against the limits.** All {HP['n']['ny']} new links were judged the same family. Of the known links {HP['k']['känd']} were judged the same family and 2 unsure. Of the name pairs {HP['k']['namn']} were judged the same family, 6 unsure and 6 not the same family. The difference between the new links and the name pairs gives p = {HP['fisher_p']:.4f} (Fisher's exact test, one-sided), but the condition on the known links was not met, so by the plan the test is not decisive. In plain words: every link the model found on its own was judged blind as the same family, against one in five of the name pairs it does not link, but the judge recognised for certain only three of five links the experts had already made. The comments show why: in one pair (Ög 81 and Ög 84) Williams's tie rests on a carver, Þorkell, and in the other (U 136 and U 147) knowledge of Jarlabanke's family beyond the two texts is needed.

**5.2 Against Williams and by distance.** On the Swedish runestones, with the same material for all:

- The earlier model (one pool, null model within the province): {M0['n_sure']} links, coverage {M0['W1']['hit']} of {M0['W1']['n_stones']} stones ({pc(M0['W1']['share'])} per cent), precision {M0['W2']['hit']} of {M0['W2']['n_links']}, Jarlabanke 0 of 10.
- Distance bands with the null model within the hundred (step 1's plan): {M1['n_sure']} links, coverage {pc(M1['W1']['share'])} per cent, precision {M1['W2']['hit']} of {M1['W2']['n_links']}, no contradictions, Jarlabanke 1 of 10.
- Distance bands with the null model within the province (the report's model): {M2['n_sure']} links, coverage {M2['W1']['hit']} of {M2['W1']['n_stones']} ({pc(M2['W1']['share'])} per cent), precision {M2['W2']['hit']} of {M2['W2']['n_links']} ({pc(M2['W2']['share'])} per cent), Jarlabanke 6 of 10.

Run on all Nordic runestones, as it is used, the same model gives {len(sure_se)} links between Swedish stones: coverage {M2['W1']['hit']} of {M2['W1']['n_stones']}, precision {W2A[0]} of {W2A[1]} ({pc(W2A[0] / W2A[1])} per cent). The difference comes from the null model's pairs per distance then being counted over more stones.

The explanation lies in the distances. Up to 2 km chance gives on average {round(NB['A'])} candidate pairs against {OB['A']} in the data, but beyond 10 km {round(NB['C'])} against {OB['C']}: there chance gives more pairs than reality. When all distances are tested in one pool, the near, genuine links drown in the distant, random ones.

{chart(False)}

The hundred model was too strict on large families: seven of Jarlabanke's nine stones stand in the same hundred, so when the names are shuffled within it, chance recreates his family. U 127 stands 10–14 km from the other Jarlabanke stones and never becomes sure; there chance gives too many pairs.

**5.3 Stability and calibration.** Run on all Nordic runestones, the model gives {D['n_sure']} sure links with all four random seeds (68–70 when the null runs are redrawn), {D['n_sure_by_band']['A']} up to 2 km, {D['n_sure_by_band']['B']} at 2–10 km and {D['n_sure_by_band']['C']} further. {len(sure_se)} of them join Swedish runestones. Two links are rejected by contradictions. The links claim at most 10 per cent false; against Williams {pc(W2A[0] / W2A[1])} per cent are confirmed, which agrees, with the reservation that some unconfirmed ones may be right. Rundata's paired stones: {D['validation']['parsten']['found']} of {D['validation']['parsten']['n']} are found, against 2 before; of those missed, most share no read name at all.

**5.4 What the network gives (descriptive).** The Swedish links tie together {F['stones_in_families']} runestones in {F['n_families']} families with {F['persons_in_families']} persons, {F['persons_on_2plus']} of whom stand on at least two stones. 35 families consist of two stones, 3 of three and 4 of four, and at most three generations can be followed. {F['by_province']['U']} of the families are in Uppland. Three links are given neither by Rundata, Williams nor Peterson: U 941 and U 986 (Áli, Ingifastr and Sigvaldi, 5 km apart), U 1027 and U 1047 (Gísl and Ígull, 10 km) and U 147 and U 287 (Ingifastr and Ingvarr, 10 km).

## 6. Discussion

**What the method achieves.** It recovers the runologists' links accurately and does so openly, with a stated share of false links that can be recounted when Rundata changes. Distance makes the difference: family links almost always lie within ten kilometres (97 per cent of the links), and there chance gives few name pairs.

**Where the method should not be used.**

1. **Far apart.** Beyond 10 km chance gives more name pairs than the data. A link there is almost never sure, even when it is genuine, like U 127 for Jarlabanke.
2. **Common names.** Pairs that share only Sveinn, Bjôrn, Þorsteinn or Ulfr are not tested. Many real families with common names therefore do not show.
3. **Carvers and famous men.** Carvers do not link, and Ingvarr, Knútr and Frøgærr on several stones are famous men, not relatives.
4. **Damaged texts and missed kin ties.** About one kin tie in four on a stone is not caught by the rules, and a name that cannot be read links nothing. The model sees only what stands in Rundata's reading.
5. **Inheritance questions at scale.** The network is thin: 4 per cent of the runestones, mostly pairs of two stones. It suffices for case studies but gives weak statistical tests.

**Against earlier research.** Williams's list is wider. It also builds on local knowledge, carvers and literature, and the model finds four in ten of his stones. What the model adds is testability: every link has an estimated uncertainty, and the list can be recounted.

**Weaknesses, in order of importance.**

1. **The post-hoc choice.** The way of counting was chosen after seeing the main yardstick, and the blind test was not decisive.
2. **The hand test is small** and has a single judge. The five new links are too few for a firm share.
3. **The yardstick is not independent of the texts.** Williams's ties rest on the same inscriptions, sometimes on things the model does not see.
4. **The rules that read the persons** miss some kin ties, which lowers the coverage.

**What would overturn the method.** If links the model calls sure often turned out to be different families when a runologist tests them blind, or if the share of confirmed links fell clearly in an independent list.

## 7. Conclusion

An open model that tests name pairs against chance at the same distance recovers {pc(M2['W1']['share'])} per cent of the runologists' family ties, and {pc(W2A[0] / W2A[1])} per cent of its links stand in their list. Distance is the key. The way of counting was chosen after seeing the yardstick, and the blind test was not decisive, so the method is partially tested. The next step is a blind test with several judges and more pairs.

## Data and code

The analysis was made in Vitki {APP_VERSION} ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made up to 1 November 2026. No release with a DOI exists yet. All code, the plans and the results are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The plans: `analysplaner/2026-11-01-slaktnatverket-steg1.md` and `analysplaner/2026-11-01-slaktnatverket-steg1b.md`, with their checksums beside them.
- The linking model: `src/linking.py` (the distance bands `null_scores_banded`, `fdr_banded`) and `scripts/link_entities.py` → `data/links.json`; the persons `src/entities.py`.
- Step 1: `utdata/slakt/steg1.py` → `steg1.json`, `steg1_resultat.md`. Williams's transcription: `utdata/slakt/williams1990_bilaga.py`. Peterson's notes: `utdata/slakt/peterson2007_samma_person.py`.
- The hand test: `utdata/slakt/handprov.py`, the answers `handprov_svar.json`, the key `handprov_nyckel.json`, the result `handprov_resultat.md`.
- The families: `utdata/slakt/steg2a.py` → `steg2a.json`.
- The report is built by `utdata/blogg/build/build_rapport_slaktlankar.py`, which reads every number from the result files and stops if anything disagrees.

## References

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society, Series B* 57 (1), pp. 289–300.
- Fellegi, I. P. & Sunter, A. B. 1969. A theory for record linkage. *Journal of the American Statistical Association* 64 (328), pp. 1183–1210.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md, section 1r). https://github.com/Precatio/runes
- Mueller-Vollmer, T. 2021. *Personal Names on Swedish Viking Age Runestones*. PhD dissertation, University of Wisconsin–Madison.
- Peterson, L. 2007. *Nordiskt runnamnslexikon*. 5th ed. Uppsala: Institutet för språk och folkminnen.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Storey, J. D. & Tibshirani, R. 2003. Statistical significance for genomewide studies. *Proceedings of the National Academy of Sciences* 100 (16), pp. 9440–9445.
- Williams, H. 1990. *Åsrunan. Användning och ljudvärde i runsvenska steninskrifter*. Runrön 3. Uppsala: Department of Scandinavian Languages.

:::box The essentials
- The same people stand on several runestones, and an open model can find them with a stated uncertainty, if the name pairs are tested against chance at the same distance.
- Distance decides: family links almost always lie within ten kilometres, and there chance gives few name pairs.
- The model recovers the experts' links accurately but only some of them; it is testable groundwork, not a replacement for the runologist's reading.
- The way of counting was chosen after seeing the yardstick, and the blind test was not decisive; the next step is more judges.
:::
"""

JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit\b(?! )|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    bad = [m for m in re.findall(r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|Vitkis|Vitki's|\bappen\b|`[^`]*/[^`]*`|METHODS", head)]
    assert not bad, bad
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
assert "I klartext" in body and "In plain words" in body_en
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion 1, 2026-11-01. Tidslinje: ")
assert "**Vad som inte är prövat.**" in body.split("## 1.")[0] and "**What is not tested.**" in body_en.split("## 1.")[0]

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Geografi"]}
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_slaktlankar.json")
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
                 "topic": "Rapport|slaktlankar", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
