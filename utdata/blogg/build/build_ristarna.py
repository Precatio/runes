"""Artikeln "Vem höll i mejseln?" om sidan Ristarna i Vitki (web/src/app/(app)/ristare): vad sidan gör och hur – förslagen
för stenar utan ristare, fingeravtrycket ur de signerade stenarna, heatmapen, kärna och ytterkant – med Balle, Åsmund och
Visäte som exempel, och provningen av attribueringsmodellen mot de signerade stenarna. Varje siffra hämtas ur sidans data
(web/public/geo/ristare.json), provningen (utdata/attribuering_provad/resultat.json), appens körning (attribution.json)
och Rundata, och låses med asserts. Skärmbilderna tas med ristarna_bilder.py.
    ../../../.venv/bin/python build_ristarna.py [--write | --update DOC]
Skriver utdata/blogg/ristarna.json; --write sparar ett nytt opublicerat utkast i Firestore."""
import csv
import datetime as dt
import io
import json
import os
import re
import sys
from collections import Counter

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402

FP = "82193667b35e54a7"
RUN = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
OLD = os.path.join(ROOT, "data", "cache", "r", "corpus", "7b9061c9a1c12c73")  # before the cross forms
BILDER = os.path.join(ROOT, "utdata", "blogg", "ristarna")
PAGE = json.load(open(os.path.join(ROOT, "web", "public", "geo", "ristare.json"), encoding="utf-8"))
AUD = json.load(open(os.path.join(ROOT, "utdata", "attribuering_provad", "resultat.json"), encoding="utf-8"))
ATT = json.load(open(os.path.join(RUN, "attribution.json"), encoding="utf-8"))
ATT_OLD = json.load(open(os.path.join(OLD, "attribution.json"), encoding="utf-8"))
RD = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))
REC = {r["signum"]: r for v in RD.values() if isinstance(v, list) for r in v if isinstance(r, dict) and "signum" in r}
csv.field_size_limit(10 ** 9)
CORPUS = list(csv.DictReader(open(os.path.join(RUN, "corpus.csv"), encoding="utf-8")))
SUGG = list(csv.DictReader(open(os.path.join(ROOT, "utdata", "ristare", "modellforslag.csv"), encoding="utf-8")))
pr = lambda x: round(100 * x)  # noqa: E731
sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_ = lambda n: f"{n:,}"  # noqa: E731
CARVER = {c["name"]: c for c in PAGE["carvers"]}

# ---- korpusen ---------------------------------------------------------------------------------------
N_ALL = len(CORPUS)
N_NONE = sum(not r["carver"] for r in CORPUS)
N_SIGNED = sum(r["signed"] == "1" for r in CORPUS)
N_ATTR = sum(bool(r["carver"]) and r["signed"] != "1" for r in CORPUS)
assert (N_ALL, N_NONE, N_SIGNED, N_ATTR) == (2321, 1665, 246, 460)
assert round(4 * N_NONE / N_ALL) == 3  # three of four

# ---- sidan ------------------------------------------------------------------------------------------
assert len(PAGE["carvers"]) == 24
N_CERTAIN = {c["name"]: c["variants"]["med"]["n"].get("signerad", 0) + c["variants"]["med"]["n"].get("attribuerad", 0)
             for c in PAGE["carvers"]}
assert min(N_CERTAIN.values()) == 6  # every carver with at least six stones with a certain carver
SIGNED_MODE = [c["name"] for c in PAGE["carvers"] if c["variants"]["med"]["profil"] == "signerade"]
assert SIGNED_MODE == ["Öpir 1", "Balle", "Åsmund", "Visäte", "Livsten"]
SMALL = [c["name"] for c in PAGE["carvers"] if c.get("bygd") is not None]
assert len(SMALL) == 10


def measured(name):
    """(in the core or within the span, measurable) among the carver's attributed stones."""
    k = Counter(s["klass"] for s in CARVER[name]["variants"]["med"]["stones"] if s["set"] == "attribuerad")
    return k["kärna"] + k["inom spannet"], sum(k.values()) - k["kan inte avgöras"], k


# Balle
BV, BU = CARVER["Balle"]["variants"]["med"], CARVER["Balle"]["variants"]["utan_rodballe"]
assert (BV["n"]["signerad"], BV["n"]["attribuerad"], BV["n"]["granne"], len(BV["traits"])) == (20, 49, 501, 22)
T = {t["id"]: t for t in BV["traits"]}
tr = lambda k: (T[k]["kc"], T[k]["nc"], T[k]["kn"], T[k]["nn"])  # noqa: E731
assert tr("msg_gard") == (5, 20, 8, 478) and tr("ord_goðan") == (7, 20, 23, 480) and tr("pm_kors") == (6, 20, 305, 480)
B_IN, B_MEAS, _ = measured("Balle")
assert (B_IN, B_MEAS) == (26, 38)
prov = Counter(s["prov"] for s in BV["stones"] if s["set"] in ("signerad", "attribuerad"))
assert prov.most_common(2) == [("U", 54), ("Sö", 13)]
st = {s["id"]: s for s in BV["stones"]}
stu = {s["id"]: s for s in BU["stones"]}
signed = sorted((s for s in BV["stones"] if s["set"] == "signerad"), key=lambda s: s["score"])
assert signed[0]["id"] == "Vs 15" and st["Vs 15"]["klass"] == "som grannarna" and stu["Vs 15"]["klass"] == "som grannarna"
assert st["Vs 24"]["klass"] == "ytterkant" and stu["Vs 24"]["klass"] == "ytterkant"
assert REC["Vs 15"]["style"] == REC["Vs 24"]["style"] == "Pr4"
assert 'Balli hi[nn] "Rauði' in REC["Vs 15"]["normalization"]
assert REC["Vs 15"]["place"] == "Lilla Kyringe" and REC["Vs 24"]["place"] == "Hassmyra"
# Åsmund
AV = CARVER["Åsmund"]["variants"]["med"]
assert (AV["n"]["signerad"], AV["n"]["attribuerad"], len(AV["traits"])) == (16, 33, 17)
A_IN, A_MEAS, _ = measured("Åsmund")
assert (A_IN, A_MEAS) == (25, 29)
AS = CARVER["Åsmund"]["forslag"]
assert (len(AS["rows"]), AS["n_blocked"]) == (18, 21)
assert (AS["rows"][0]["id"], AS["rows"][0]["place"], pr(AS["rows"][0]["p"])) == ("U 1149", "Fleräng", 96)
# Visäte
_, _, VIS = measured("Visäte")
assert VIS["som grannarna"] == 11 and sum(VIS.values()) == 23

# ---- provningen och modellen ------------------------------------------------------------------------
Q1 = AUD["q1"]
assert (Q1["n"], pr(Q1["top1"][0]), pr(Q1["top1"][1]), pr(Q1["top1"][2]), pr(Q1["top3"][0])) == (117, 71, 64, 79, 86)
assert pr(AUD["q4"]["geografi"][0]) == 38 and AUD["q2"]["glmer"]["p"] > 0.5
PC = {r["carver"]: r for r in Q1["per_carver"]}
assert (PC["Öpir 1"]["n"], pr(PC["Öpir 1"]["top1"]), PC["Balle"]["n"], pr(PC["Balle"]["top1"]), PC["Åsmund"]["n"], pr(PC["Åsmund"]["top1"])) == (38, 96, 20, 93, 16, 73)
ZERO = sorted(c for c, r in PC.items() if r["top1"] == 0)
assert len(ZERO) == 6 and max(PC[c]["n"] for c in ZERO) == 4 and min(PC[c]["n"] for c in ZERO) == 1
ABL = {x["features"]: pr(x["accuracy"]) for x in ATT["ablation"]}
ABL_OLD = {x["features"]: pr(x["accuracy"]) for x in ATT_OLD["ablation"]}
assert (ABL["Stil"], ABL_OLD["Stil"], ABL["Alla"], ABL["Geografi"], ABL["Språk och innehåll"], ABL["Bergart"]) == (54, 33, 74, 44, 61, 19)
assert (ATT["n_train"], len(ATT["carvers"])) == (497, 18)
CAL = ATT["calibration"]["grouped"]
assert abs(CAL["ece_before"] - 0.295) < 1e-3 and abs(CAL["ece_after"] - 0.047) < 1e-3

# ---- förslagen ---------------------------------------------------------------------------------------
OK = [r for r in SUGG if r["someone_else"] == "FALSE"]
N70 = sum(float(r["p_cal"]) >= 0.7 for r in OK)
assert (len(SUGG), len(OK), N70) == (923, 385, 219)

# ---- bilderna ----------------------------------------------------------------------------------------


def bild(fil, alt, text, max_w=1600):
    im = Image.open(os.path.join(BILDER, fil)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return f"![{alt}]({blog_figures.freeze(out.getvalue())})\n{text}"


URL = {f: bild(f, "", "").split("](", 1)[1].split(")", 1)[0]
       for f in ("00_oversikt.png", "01_fingeravtryck.png", "02_heatmap.png", "03_karna_ytterkant.png")}
fig = lambda f, alt, text: f"![{alt}]({URL[f]})\n{text}"  # noqa: E731

IMG0 = fig("00_oversikt.png", "Sidan Ristarna i Vitki, här för Åsmund",
           "Sidan Ristarna, här för Åsmund. Överst väljer man ristare i listan eller bläddrar med pilarna. Under rubriken står "
           "vad profilen bygger på, och därunder appens förslag: runstenar utan säker ristare som modellen tror att Åsmund "
           "ristade, med modellens procent, den näst troligaste ristaren och hur stenen ligger mot Åsmunds fingeravtryck. "
           "Skärmbild ur Vitki.")
IMG1 = fig("01_fingeravtryck.png", "Fingeravtrycket för Balle i Vitki",
           "Fingeravtrycket, här för Balle: för varje drag andelen bland ristarens 20 signerade stenar (rost) och bland "
           "grannstenarna (grå). Överst det ristaren gör oftare, nederst det ristaren gör mer sällan. Skärmbild ur Vitki.")
IMG2 = fig("02_heatmap.png", "Sten för sten, här för Balle",
           "Sten för sten: varje rad en sten, varje kolumn ett drag. Rost betyder att stenen gör som ristaren, grått att den "
           "gör som grannarna, ljust att draget inte går att avläsa. Stapeln till höger visar hur väl stenen följer profilen. "
           "Skärmbild ur Vitki (de signerade stenarna och de första attribuerade).")
IMG3 = fig("03_karna_ytterkant.png", "Kärna, spann och ytterkant, här för Balle",
           "Varje prick är en sten. Längst till höger kärnan, längst till vänster stenar som liknar grannarna mer än ristaren. "
           "De små grå prickarna är grannstenarna. Skärmbild ur Vitki.")
IMG0_EN = fig("00_oversikt.png", "The page The carvers in Vitki, here for Åsmund",
              "The page The carvers, here for Åsmund. At the top you pick a carver from the list or step through with the "
              "arrows. Below the heading is what the profile rests on, and below that the app's suggestions: runestones without "
              "a certain carver that the model thinks Åsmund carved, with the model's percentage, the next most likely carver "
              "and where the stone lies against Åsmund's fingerprint. Screenshot from Vitki (Swedish edition).")
IMG1_EN = fig("01_fingeravtryck.png", "The fingerprint for Balle in Vitki",
              "The fingerprint, here for Balle: for each trait the share among the carver's 20 signed stones (rust) and among "
              "the neighbouring stones (grey). At the top what the carver does more often, at the bottom what the carver does "
              "less often. Screenshot from Vitki (Swedish edition).")
IMG2_EN = fig("02_heatmap.png", "Stone by stone, here for Balle",
              "Stone by stone: each row a stone, each column a trait. Rust means the stone does as the carver does, grey that it "
              "does as the neighbours do, pale that the trait cannot be read. The bar on the right shows how well the stone "
              "follows the profile. Screenshot from Vitki (the signed stones and the first attributed ones).")
IMG3_EN = fig("03_karna_ytterkant.png", "Core, span and edge, here for Balle",
              "Each dot is a stone. On the far right the core, on the far left stones that resemble the neighbours more than the "
              "carver. The small grey dots are the neighbouring stones. Screenshot from Vitki.")

CHART = f""":::chart Vad varje slags belägg räcker till
Bergarten | {ABL['Bergart']} |
Platsen | {ABL['Geografi']} |
Stil och kors, förut | {ABL_OLD['Stil']} |
+Stil och kors, med korsets form | {ABL['Stil']} |
Språk och innehåll | {ABL['Språk och innehåll']} |
+Allt tillsammans | {ABL['Alla']} |
Källa: Vitki. Andel stenar där modellen satte rätt ristare först, bland {ATT['n_train']} runstenar med säker ristare av {len(ATT['carvers'])} ristare; varje sten prövad mot en modell som inte sett den. Efter Rundata och RAÄ:s Runor.
:::"""
CHART_EN = f""":::chart What each kind of evidence achieves
The rock | {ABL['Bergart']} |
The place | {ABL['Geografi']} |
Style and cross, before | {ABL_OLD['Stil']} |
+Style and cross, with the form of the cross | {ABL['Stil']} |
Language and content | {ABL['Språk och innehåll']} |
+Everything together | {ABL['Alla']} |
Source: Vitki. Share of stones where the model put the right carver first, among {ATT['n_train']} runestones with a certain carver by {len(ATT['carvers'])} carvers; each stone tested against a model that had not seen it. After Rundata and the Swedish National Heritage Board's Runor.
:::"""

title = "Vem höll i mejseln? Vitki lär sig känna igen ristarnas handlag"
summary = ("Tre av fyra svenska runstenar saknar ristare. Vitkis nya sida Ristarna går igenom de kända ristarna en i taget: "
           "vad som skiljer var och en från grannarna, vilka av stenarna som ligger mitt i stilen och vilka i ytterkanten, "
           "och vilka stenar utan ristare som kan vara deras.")

body = f"""Den som står framför en runsten läser oftast tre saker: vem som reste den, efter vem och varför. Vem som höll i mejseln står sällan där. Av de {sv(N_ALL)} vikingatida runstenarna i Vitkis svenska korpus har {sv(N_NONE)} ingen säker ristare i Rundata, nästan tre av fyra. Bara {N_SIGNED} är signerade, oftast med ett enda ord efter namnet: *risti*, ristade. Resten har forskarna fått tillskriva en ristare efter stil, stavning och plats, eller lämna öppna.

Vitki har nu fått en sida för just den frågan: **Ristarna**. Den går igenom de kända ristarna en i taget och visar vad som skiljer var och en från grannarna, vilka av deras stenar som ligger mitt i stilen och vilka i ytterkanten, och vilka stenar utan ristare som kan vara deras.

{IMG0}

## En sida per ristare

Sidan har {len(PAGE['carvers'])} ristare, alla som har minst sex stenar med säker ristare i Rundata. Man väljer ristare i en lista eller bläddrar med pilarna, och varje sida är byggd på samma sätt, uppifrån och ned:

- **Förslagen.** Stenar utan ristare som appen tror att ristaren gjorde.
- **Fingeravtrycket.** De drag där ristarens stenar skiljer sig tydligast från grannarnas.
- **Sten för sten.** En rad per sten och en kolumn per drag.
- **Kärna, spann och ytterkant.** Var varje sten hamnar mellan ristarens stil och grannarnas.
- **Karta, likhet och listor.** Var stenarna står, vilka som liknar varandra, vilka som ligger längst ut och vilka grannstenar som liknar ristaren mest.
- **Så är det gjort.** Metoden och vad den inte säger, för just den ristaren.

## Facit: de signerade stenarna

Det svåra är att inte lura sig själv. {N_ATTR} stenar har en attribuerad ristare, tillskriven av forskare efter just stil, stavning och plats. Om en dator lär sig av dem, lär den sig forskarnas bedömningar och ger dem tillbaka. Därför bygger sidan varje ristares fingeravtryck bara av de stenar ristaren själv signerade. De attribuerade stenarna prövas mot avtrycket i stället för att få forma det.

Det går för fem ristare: Öpir, Balle, Åsmund, Visäte och Livsten har tillräckligt många signerade stenar. För de övriga bygger avtrycket på alla deras säkra stenar. Då mäter sidan hur samstämmig forskningens grupp är, inte om den stämmer, och det står i en gul ruta överst.

## Fingeravtrycket

Ta Balle, som ristade mest i Uppland och Södermanland. Balles 20 signerade stenar jämförs med {BV['n']['granne']} samtida grannstenar inom tre mil som andra har rest. Fem av de tjugo nämner gården där den döde bodde, mot knappt två av hundra bland grannarna. Sju av tjugo kallar den döde *góðan*, god, mot en av tjugo. Bara sex av tjugo har ett kors, mot två av tre bland grannarna. Var och en av skillnaderna är liten, men tillsammans blir de ett avtryck: {len(BV['traits'])} drag för Balle.

Sidan visar varje drag som två prickar, ristarens andel och grannarnas. En del av dragen kan vara beställarnas val snarare än ristarens, för det är de som bestämmer vad stenen ska säga. Men valen följer med ristaren mellan gårdarna.

{IMG1}

## Sten för sten

Sedan står ristarens stenar i en lång rad, en sten per rad och ett drag per kolumn. Rost betyder att stenen gör som ristaren, grått att den gör som grannarna, och en ljus ruta att draget inte går att avläsa på en kort eller skadad sten. Överst ligger de stenar som följer avtrycket bäst. Man ser genast vilka stenar som bär hela avtrycket och vilka som bara bär några få drag.

{IMG2}

## Kärna, spann och ytterkant

Varje sten får ett värde för hur mycket dess drag talar för ristaren mot grannarna. De signerade stenarna sätter själva gränserna: **kärnan** börjar vid den mittersta av dem, och en sten **inom spannet** liknar ristaren mer än nio av tio grannstenar gör. I **ytterkanten** ligger stenar som följer avtrycket svagt, och längst ut de som liknar grannarna mer än ristaren.

{IMG3}

För de flesta ristare passar forskningens attribueringar. Av Balles attribuerade stenar som går att mäta ligger {B_IN} av {B_MEAS} i kärnan eller inom spannet, av Åsmunds {A_IN} av {A_MEAS}. Hos Visäte är det annorlunda: {VIS['som grannarna']} av de 23 attribuerade stenarna liknar grannarna mer än Visätes signerade stenar. Det är inget bevis för att attribueringarna är fel, men det är ett skäl att se på dem igen.

Sidan kan också ställa gamla frågor på nytt. Två av Balles signerade stenar står i Västmanland, och på den ena, vid Lilla Kyringe, kallar sig ristaren *Balli hi[nn] Rauði*, Balle den röde. *Sveriges runinskrifter* räknar båda till Balles stenar. På sidan är Lilla Kyringe-stenen den signerade sten som minst liknar Balles övriga, medan Hassmyrastenen bara hamnar i ytterkanten. Det kan vara en tidig sten, en annan bygd med en senare stil, eller en annan ristare. En knapp bygger om Balles avtryck utan de två, så att man kan se skillnaden själv.

## Stenar som kan vara deras

Det är därför sidan finns. Rutan överst samlar de runstenar utan säker ristare där Vitkis attribueringsmodell sätter den här ristaren först. Över alla ristare gäller det {sv(len(OK))} stenar, och för {N70} av dem säger modellen minst 70 procent. För Åsmund föreslår den {len(AS['rows'])} stenar, starkast U 1149 vid Fleräng med {pr(AS['rows'][0]['p'])} procent. Där modellen är så osäker att det lika gärna kan vara en ristare den inte känner, säger den ingenting. För Åsmund sorterades {AS['n_blocked']} sådana stenar bort.

Bredvid modellens procent står den näst troligaste ristaren och hur stenen ligger mot fingeravtrycket, en andra och delvis oberoende bedömning. För de tio små ristarna finns ytterligare en, en modell som väger in var och när ristaren verkade. Den hittar oftare rätt för små verkstäder men klarade inte vår låsta prövning, och den står därför tydligt märkt under huvudmodellens förslag. Allt är förslag, inte attribueringar.

## Hur bra är maskinen?

Vitkis attribueringsmodell väger samman plats, stil, korsets form, stavning, formler och runpar. Vi prövade den den 4 november mot det enda facit som finns, de {Q1['n']} signerade stenarna av de {len(ATT['carvers'])} ristare som har minst åtta stenar. Varje gång hölls hela socknen utanför, som om stenen kom från en bygd modellen aldrig sett.

Modellen satte rätt ristare först på {pr(Q1['top1'][0])} procent av de signerade stenarna (mellan {pr(Q1['top1'][1])} och {pr(Q1['top1'][2])} procent om man räknar med slumpen) och hade rätt ristare bland sina tre första på {pr(Q1['top3'][0])} procent. Bara platsen ger {pr(AUD['q4']['geografi'][0])} procent. De attribuerade stenarna var inte lättare för modellen än de signerade, så den gör mer än att upprepa forskarnas bedömningar.

Men den känner de stora verkstäderna mycket bättre än de små. Öpir fick rätt på {pr(PC['Öpir 1']['top1'])} procent av sina {PC['Öpir 1']['n']} signerade stenar, Balle på {pr(PC['Balle']['top1'])} procent av {PC['Balle']['n']}, Åsmund på {pr(PC['Åsmund']['top1'])} procent av {PC['Åsmund']['n']}. Sex små ristare med mellan en och fyra signerade stenar fick inte en enda rätt.

Det nya är korsets form. Riksantikvarieämbetets Runor beskriver korsen enligt Linn Lagers typologi: hur armarna slutar, hur mitten ser ut, vad korset står på. Med bara stil och kors hittade modellen förut rätt ristare för en tredjedel av stenarna. Med korsets form hittar den rätt för mer än hälften.

{CHART}

Modellen säger också hur säker den är, och det ska gå att lita på. Förut var den för försiktig. Nu är procenten justerade efter provningen, så att ett förslag på 80 procent stämmer ungefär så ofta.

## Vad sidan inte ser

Forskarnas viktigaste belägg saknas fortfarande: ornamentiken utöver korset, alltså hur djurhuvudena är tecknade, hur svansarna slutar och hur flikarna löper, och runornas former. Vi har försökt läsa ornamentiken ur beskrivningarna i *Sveriges runinskrifter*, men att ett ord står i en artikel säger för lite. Det kräver att varje sten beskrivs på samma sätt, och det arbetet återstår. Runformerna kräver skanningar, och i dag finns som mest fyra skannade stenar per ristare.

## Pröva själv

Öppna Vitki och välj Korpus → Ristarna. Välj en ristare i listan och bläddra med pilarna. Titta särskilt på rutan Ytterkanten och utanför: där står de stenar som inte följer ristarens drag. Har du en av dem nära dig, så gå dit och titta på slingan och korset. Det är där maskinen ännu inte ser, och där ett mänskligt öga fortfarande gör skillnad.

Tidigare har vi skrivit om [stenar som söker sin ristare](/artiklar/fem-runstenar-soker-sin-ristare/) och om [ristarna som aldrig blev ihågkomna](/artiklar/ristarna-som-aldrig-blev-ihagkomna/).

:::box Det viktigaste i korthet
- Sidan Ristarna visar varje känd ristares fingeravtryck, byggt bara av de stenar ristaren själv signerade.
- Den prövar forskningens attribueringar mot avtrycket. För de flesta ristare passar de, och de få stenar som inte gör det förtjänar en ny blick.
- Den föreslår stenar utan ristare, med en modell som har rätt på sju av tio signerade stenar och säger till när den inte vet.
- Maskinen känner de stora verkstäderna men knappt de små. Nästa steg är ornamentiken.
:::

## Så har vi gjort

Avtrycken bygger på de drag som skiljer ristarens signerade stenar från samtida grannstenar inom tre mil (Fishers test, minst dubbla eller halva oddsen). Provningen av modellen och varje försök att förbättra den låstes i en plan innan den kördes, och allt finns i Vitkis öppna källkod på GitHub. Korsets form kommer ur Riksantikvarieämbetets Runor, texterna ur Samnordisk runtextdatabas.

## Källor

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter.* Runrön 5. Uppsala.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: Stoklund, M. m.fl. (red.), *Runes and their Secrets.* København.
- Jansson, S. B. F. 1964. *Västmanlands runinskrifter.* Sveriges runinskrifter 13. Stockholm.
- Lager, L. 2002. *Den synliga tron. Runstenskors som en spegling av kristnandet i Sverige.* OPIA 31. Uppsala.
- Wessén, E. & Jansson, S. B. F. 1940–1958. *Upplands runinskrifter.* Sveriges runinskrifter 6–9. Stockholm.
- Runor. Riksantikvarieämbetet, utgåva 2020.
- Samnordisk runtextdatabas, version 3.1 (ODbL).
- Bilder: skärmbilder ur Vitki."""

title_en = "Who Held the Chisel? Vitki Learns to Recognise the Carvers' Hands"
summary_en = ("Three in four Swedish runestones have no known carver. Vitki's new page The carvers goes through the known carvers one "
              "at a time: what sets each apart from the neighbours, which of the stones lie at the heart of the style and which "
              "at the edge, and which stones without a carver could be theirs.")

body_en = f"""Standing in front of a runestone, you usually read three things: who raised it, for whom, and why. Who held the chisel is seldom there. Of the {en_(N_ALL)} Viking Age runestones in Vitki's Swedish corpus, {en_(N_NONE)} have no certain carver in Rundata, nearly three in four. Only {N_SIGNED} are signed, usually with a single word after the name: *risti*, carved. For the rest, researchers have had to attribute a carver from style, spelling and place, or leave the question open.

Vitki now has a page for exactly that question: **The carvers**. It goes through the known carvers one at a time and shows what sets each apart from the neighbours, which of their stones lie at the heart of the style and which at the edge, and which stones without a carver could be theirs.

{IMG0_EN}

## One page per carver

The page has {len(PAGE['carvers'])} carvers, all those with at least six stones with a certain carver in Rundata. You pick a carver from a list or step through with the arrows, and every page is built the same way, from top to bottom:

- **The suggestions.** Stones without a carver that the app thinks the carver made.
- **The fingerprint.** The traits where the carver's stones differ most clearly from the neighbours'.
- **Stone by stone.** One row per stone and one column per trait.
- **Core, span and edge.** Where each stone falls between the carver's style and the neighbours'.
- **Map, similarity and lists.** Where the stones stand, which resemble each other, which lie furthest out and which neighbouring stones resemble the carver most.
- **How it is done.** The method and what it does not say, for that carver.

## The reference: the signed stones

The hard part is not to fool oneself. {N_ATTR} stones have an attributed carver, assigned by researchers from exactly style, spelling and place. A computer that learns from them learns the researchers' judgements and hands them back. So the page builds each carver's fingerprint from the stones the carver signed, and only those. The attributed stones are tested against the fingerprint instead of shaping it.

That works for five carvers: Öpir, Balle, Åsmund, Visäte and Livsten have enough signed stones. For the others the fingerprint rests on all their stones with a certain carver. The page then measures how consistent research's group is, not whether it is right, and says so in a yellow box at the top.

## The fingerprint

Take Balle, who carved mostly in Uppland and Södermanland. Balle's 20 signed stones are compared with {BV['n']['granne']} contemporary neighbouring stones within 30 km raised by others. Five of the twenty say which farm the dead person lived on, against fewer than two in a hundred among the neighbours. Seven in twenty call the dead *góðan*, good, against one in twenty. Only six in twenty have a cross, against two in three among the neighbours. Each difference is small, but together they make a fingerprint: {len(BV['traits'])} traits for Balle.

The page shows each trait as two dots, the carver's share and the neighbours'. Some traits may be the patrons' choice rather than the carver's, for they decided what the stone should say. But the choices follow the carver from farm to farm.

{IMG1_EN}

## Stone by stone

Then the carver's stones are listed, one stone per row and one trait per column. Rust means the stone does as the carver does, grey that it does as the neighbours do, and a pale square that the trait cannot be read on a short or damaged stone. The stones that follow the fingerprint best are at the top. You see at once which stones carry the whole fingerprint and which carry only a few traits.

{IMG2_EN}

## Core, span and edge

Each stone gets a value for how much its traits speak for the carver against the neighbours. The signed stones set the limits themselves: **the core** begins at the middle one of them, and a stone **within the span** resembles the carver more than nine in ten neighbouring stones do. **At the edge** are stones that follow the fingerprint only weakly, and furthest out those that resemble the neighbours more than the carver.

{IMG3_EN}

For most carvers, research's attributions fit. Of Balle's measurable attributed stones, {B_IN} of {B_MEAS} lie in the core or within the span; of Åsmund's, {A_IN} of {A_MEAS}. Visäte is different: {VIS['som grannarna']} of the 23 attributed stones resemble the neighbours more than Visäte's signed stones. That does not prove the attributions wrong, but it is a reason to look at them again.

The page can also put old questions anew. Two of Balle's signed stones stand in Västmanland, and on one, at Lilla Kyringe, the carver is called *Balli hi[nn] Rauði*, Balle the Red. *Sveriges runinskrifter* counts both among Balle's stones. On the page, the Lilla Kyringe stone is the signed stone least like Balle's others, while the Hassmyra stone ends up only at the edge. It may be an early stone, another district with a later style, or another carver. A button rebuilds Balle's fingerprint without the two, so you can see the difference yourself.

## Stones that could be theirs

That is why the page exists. The box at the top gathers the runestones without a certain carver where Vitki's attribution model puts this carver first. Across all carvers that is {en_(len(OK))} stones, and for {N70} of them the model says at least 70 per cent. For Åsmund it suggests {len(AS['rows'])} stones, the strongest U 1149 at Fleräng at {pr(AS['rows'][0]['p'])} per cent. Where the model is so unsure that it could just as well be a carver it does not know, it says nothing. For Åsmund, {AS['n_blocked']} such stones were left out.

Beside the model's percentage stands the next most likely carver and where the stone lies against the fingerprint, a second and partly independent judgement. For the ten small carvers there is yet another, a model that weighs in where and when the carver worked. It finds the right carver more often for small workshops but did not pass our locked test, so it stands clearly marked below the main model's suggestions. All of these are suggestions, not attributions.

## How good is the machine?

Vitki's attribution model weighs together place, style, the form of the cross, spelling, formulas and rune pairs. On 4 November we tested it against the only reference there is, the {Q1['n']} signed stones of the {len(ATT['carvers'])} carvers with at least eight stones. Each time the whole parish was left out, as if the stone came from a district the model had never seen.

The model put the right carver first for {pr(Q1['top1'][0])} per cent of the signed stones (between {pr(Q1['top1'][1])} and {pr(Q1['top1'][2])} per cent allowing for chance) and had the right carver among its first three for {pr(Q1['top3'][0])} per cent. The place alone gives {pr(AUD['q4']['geografi'][0])} per cent. The attributed stones were no easier for the model than the signed ones, so it does more than repeat the researchers' judgements.

But it knows the large workshops far better than the small ones. Öpir was right for {pr(PC['Öpir 1']['top1'])} per cent of {PC['Öpir 1']['n']} signed stones, Balle for {pr(PC['Balle']['top1'])} per cent of {PC['Balle']['n']}, Åsmund for {pr(PC['Åsmund']['top1'])} per cent of {PC['Åsmund']['n']}. Six small carvers with between one and four signed stones did not get a single one right.

What is new is the form of the cross. The Swedish National Heritage Board's Runor describes the crosses following Linn Lager's typology: how the arms end, what the centre looks like, what the cross stands on. With style and cross alone, the model used to find the right carver for a third of the stones. With the form of the cross it finds the right one for more than half.

{CHART_EN}

The model also says how sure it is, and that should be something to rely on. It used to be too cautious. Now the percentages are adjusted after the test, so that a suggestion of 80 per cent is right about that often.

## What the page does not see

The researchers' most important evidence is still missing: the ornament beyond the cross – how the animal heads are drawn, how the tails end, how the lobes run – and the forms of the runes. We tried to read the ornament from the descriptions in *Sveriges runinskrifter*, but that a word occurs in an article says too little. It needs every stone described in the same way, and that work remains. The rune forms need scans, and today there are at most four scanned stones per carver.

## Try it yourself

Open Vitki and choose Corpus → The carvers. Pick a carver from the list and step through with the arrows. Look especially at the box At the edge and outside: there are the stones that do not follow the carver's traits. If one of them is near you, go there and look at the band and the cross. That is where the machine does not yet see, and where a human eye still makes the difference.

We have written before about [stones looking for their carver](/en/artiklar/fem-runstenar-soker-sin-ristare/) and about [the carvers no one remembered](/en/artiklar/ristarna-som-aldrig-blev-ihagkomna/).

:::box In short
- The page The carvers shows each known carver's fingerprint, built only from the stones the carver signed.
- It tests research's attributions against the fingerprint. For most carvers they fit, and the few stones that do not deserve a fresh look.
- It suggests stones without a carver, with a model that is right on seven in ten signed stones and says when it does not know.
- The machine knows the large workshops but hardly the small ones. The next step is the ornament.
:::

## How we did it

The fingerprints rest on the traits that set the carver's signed stones apart from contemporary neighbouring stones within 30 km (Fisher's test, at least double or half the odds). The test of the model and every attempt to improve it were locked in a plan before they were run, and everything is in Vitki's open source code on GitHub. The form of the cross comes from the Swedish National Heritage Board's Runor, the texts from the Scandinavian Runic-text Database.

## Sources

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter.* Runrön 5. Uppsala.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: Stoklund, M. et al. (eds), *Runes and their Secrets.* Copenhagen.
- Jansson, S. B. F. 1964. *Västmanlands runinskrifter.* Sveriges runinskrifter 13. Stockholm.
- Lager, L. 2002. *Den synliga tron. Runstenskors som en spegling av kristnandet i Sverige.* OPIA 31. Uppsala.
- Wessén, E. & Jansson, S. B. F. 1940–1958. *Upplands runinskrifter.* Sveriges runinskrifter 6–9. Stockholm.
- Runor. Swedish National Heritage Board, 2020 edition.
- Scandinavian Runic-text Database, version 3.1 (ODbL).
- Images: screenshots from Vitki."""

# ---- kontroller ---------------------------------------------------------------------------------------
for b_ in (body, body_en):
    assert not re.search(r"^\|", b_, re.M)  # no tables (the article page cannot show them)
    assert b_.count(":::") == 4  # one chart and one box, each closed
    assert b_.count("](/api/blog/figures/") == 4 and "wikimedia" not in b_  # four screenshots, no photographs
assert body_en.count("## ") == body.count("## ")
for word in (" han ", " hans ", " hon ", " henne ", " hennes "):  # no gendered pronouns for the carvers
    assert word not in body, word
for word in (" he ", " his ", " him ", " she ", " her "):
    assert word not in body_en.lower(), word
assert not re.search(r"\b(jag|mig|min)\b", body, re.I)  # we-voice
assert ":::box Det viktigaste i korthet" in body
assert body.count("Balle") < 20  # the page, not the carver, is the subject
LABELS = ["Forskning", "Ristare"]
assert blog_labels.check(LABELS) is None

out = {"slug": "vem-holl-i-mejseln", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en, "labels": LABELS}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "ristarna.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "ristarna.json"), len(body.split()), "ord", len(body_en.split()), "words",
      body.count("Balle"), "× Balle")

if {"--update", "--write"} & set(sys.argv):
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--write" in sys.argv:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Ristarna|fingeravtryck", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    else:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and old.get("slug") == out["slug"], "Fel dokument"
        assert not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    blog._forget()
