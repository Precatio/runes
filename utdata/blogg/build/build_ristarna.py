"""Artikeln "Vem höll i mejseln?" om sidan Ristarna i Vitki (web/src/app/(app)/ristare): ristarnas fingeravtryck ur de
signerade stenarna, kärna och ytterkant, Balle och Balle den röde, provningen av attribueringsmodellen mot de signerade
stenarna och korsformen. Varje siffra hämtas ur sidans data (web/public/geo/ristare.json), provningen
(utdata/attribuering_provad/resultat.json), appens körning (attribution.json) och Rundata, och låses med asserts.
Skärmbilderna tas med ristarna_bilder.py.
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
from src import blog_figures, blog_labels, commons  # noqa: E402

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

# ---- korpusen ---------------------------------------------------------------------------------------
N_ALL = len(CORPUS)
N_NONE = sum(not r["carver"] for r in CORPUS)
N_SIGNED = sum(r["signed"] == "1" for r in CORPUS)
N_ATTR = sum(bool(r["carver"]) and r["signed"] != "1" for r in CORPUS)
assert (N_ALL, N_NONE, N_SIGNED, N_ATTR) == (2321, 1665, 246, 460)
assert round(4 * N_NONE / N_ALL) == 3  # three of four

# ---- Balle ------------------------------------------------------------------------------------------
B = next(c for c in PAGE["carvers"] if c["name"] == "Balle")
BV, BU = B["variants"]["med"], B["variants"]["utan_rodballe"]
assert (BV["n"]["signerad"], BV["n"]["attribuerad"], BV["n"]["granne"], len(BV["traits"])) == (20, 49, 501, 22)
T = {t["id"]: t for t in BV["traits"]}
tr = lambda k: (T[k]["kc"], T[k]["nc"], T[k]["kn"], T[k]["nn"])  # noqa: E731
assert tr("msg_gard") == (5, 20, 8, 478) and tr("ord_goðan") == (7, 20, 23, 480) and tr("prep_at") == (12, 15, 106, 381)
assert tr("skilj_punkt") == (14, 20, 93, 465) and tr("pm_kors") == (6, 20, 305, 480) and tr("ord_and") == (0, 20, 68, 480)
assert tr("rel_barn") == (0, 16, 93, 381) and tr("skilj_apostrof") == (0, 20, 72, 465)
klass = Counter(s["klass"] for s in BV["stones"] if s["set"] == "attribuerad")
assert dict(klass) == {"kärna": 3, "inom spannet": 23, "ytterkant": 8, "som grannarna": 4, "kan inte avgöras": 11}
MEAS = 49 - klass["kan inte avgöras"]
assert MEAS == 38 and klass["kärna"] + klass["inom spannet"] == 26
st = {s["id"]: s for s in BV["stones"]}
stu = {s["id"]: s for s in BU["stones"]}
assert st["U 34"]["klass"] == "som grannarna" and st["U 34"]["style"] == "Pr1" and st["U 34"]["set"] == "attribuerad"
signed = sorted((s for s in BV["stones"] if s["set"] == "signerad"), key=lambda s: s["score"])
assert signed[0]["id"] == "Vs 15" and st["Vs 15"]["klass"] == "som grannarna" and stu["Vs 15"]["klass"] == "som grannarna"
assert st["Vs 24"]["klass"] == "ytterkant" and stu["Vs 24"]["klass"] == "ytterkant"
EDGE_SIGNED = sorted(s["id"] for s in signed if s["klass"] == "ytterkant")
assert EDGE_SIGNED == ["Sö 203", "U 726", "U 750", "Vs 24"]
assert REC["Vs 15"]["style"] == REC["Vs 24"]["style"] == "Pr4"

# The texts quoted (Rundata's normalisation), exactly
Q729 = 'Raði drængR/tøkR þaR rynn se runum þæim, sum "Balli risti.'
Q15 = 'Stæin hafiR rettan, þann standa ma, "Balli hi[nn] "Rauði æftiR broður.'
Q24 = '"Rauð-BalliR risti runiR þessaR.'
for s, q in (("U 729", Q729), ("Vs 15", Q15), ("Vs 24", Q24)):
    assert q in REC[s]["normalization"], s
# Shown without Rundata's name marks (a " before each name)
D729, D15, D24 = (q.replace('"', "") for q in (Q729, Q15, Q24))
assert REC["U 729"]["place"] == "Ågersta" and REC["Vs 15"]["place"] == "Lilla Kyringe" and REC["Vs 24"]["place"] == "Hassmyra"

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
assert (len(SUGG), len(OK), sum(float(r["p_cal"]) >= 0.7 for r in OK)) == (923, 385, 219)
BS = B["forslag"]["rows"]
assert len(BS) == 62 and (BS[0]["id"], BS[0]["place"], pr(BS[0]["p"])) == ("U 806", "Fröslunda kyrka", 96)
assert (BS[1]["id"], BS[1]["place"], pr(BS[1]["p"])) == ("U 830", "Furby", 95)
VIS = Counter(s["klass"] for s in next(c for c in PAGE["carvers"] if c["name"] == "Visäte")["variants"]["med"]["stones"] if s["set"] == "attribuerad")
assert VIS["som grannarna"] == 11 and sum(VIS.values()) == 23
SMALL = [c["name"] for c in PAGE["carvers"] if c.get("bygd") is not None]
assert len(SMALL) == 10 and len(PAGE["carvers"]) == 24
SIGNED_MODE = [c["name"] for c in PAGE["carvers"] if c["variants"]["med"]["profil"] == "signerade"]
assert SIGNED_MODE == ["Öpir 1", "Balle", "Åsmund", "Visäte", "Livsten"]

# ---- bilderna ----------------------------------------------------------------------------------------


def bild(fil, alt, text, max_w=1600):
    im = Image.open(os.path.join(BILDER, fil)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return f"![{alt}]({blog_figures.freeze(out.getvalue())})\n{text}"


FILES = commons.wikidata_files(["U 729", "Vs 15"])
INFO = commons.commons_info([FILES[s] for s in ("U 729", "Vs 15")])
CREDIT = {"U 729": ("Bengt A. Lundberg", "CC BY 2.5 se"), "Vs 15": ("Bengt A. Lundberg", "CC BY 2.5 se")}


def photo(signum, text, lang="sv"):
    img = {**INFO[FILES[signum]], "signum": signum}
    assert (img["author"], img["licence"]) == CREDIT[signum], (signum, img["author"], img["licence"])
    cap = commons.caption(img, lang)
    head = f"{signum}. Foto: " if lang == "sv" else f"{signum}. Photo: "
    assert cap.startswith(head), cap
    word = "Foto" if lang == "sv" else "Photo"
    return f"![{'Runstenen' if lang == 'sv' else 'The runestone'} {signum}]({img['thumb']})\n{text} {word}: {cap[len(head):]}"


IMG1 = bild("01_fingeravtryck.png", "Balles fingeravtryck i Vitki",
            "Balles fingeravtryck på sidan Ristarna: för varje drag andelen bland de 20 signerade stenarna (rost) och bland "
            "grannstenarna (grå). Överst det Balle gör oftare, nederst det Balle gör mer sällan. Skärmbild ur Vitki.")
IMG2 = bild("02_heatmap.png", "Balles stenar sten för sten",
            "Sten för sten: varje rad en sten, varje kolumn ett drag. Rost betyder att stenen gör som Balle, grått att den gör "
            "som grannarna, ljust att draget inte går att avläsa. Stapeln till höger visar hur väl stenen följer profilen. "
            "Skärmbild ur Vitki (de signerade stenarna och de första attribuerade).")
IMG3 = bild("03_karna_ytterkant.png", "Kärna, spann och ytterkant för Balle",
            "Varje prick är en sten. Längst till höger kärnan, längst till vänster stenar som liknar grannarna mer än Balle. "
            "De små grå prickarna är grannstenarna. Skärmbild ur Vitki.")
PH729 = photo("U 729", "U 729 vid Ågersta i Löts socken, Uppland. Namnet Balle står sist i slingan.")
PH15 = photo("Vs 15", "Vs 15 vid Lilla Kyringe i Björksta socken, Västmanland: Balle den rödes sten.")
PH729_EN = photo("U 729", "U 729 at Ågersta in Löt parish, Uppland. The name Balle stands at the end of the band.", "en")
PH15_EN = photo("Vs 15", "Vs 15 at Lilla Kyringe in Björksta parish, Västmanland: the stone of Balle the Red.", "en")

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
summary = (f"Tre av fyra svenska runstenar saknar ristare. Vitkis nya sida Ristarna går igenom de kända ristarna en i taget: "
           f"vad som skiljer var och en från grannarna, vilka av stenarna som ligger mitt i stilen och vilka i ytterkanten, "
           f"och vilka stenar utan ristare som kan vara deras.")

body = f"""Den som står framför en runsten läser oftast tre saker: vem som reste den, efter vem och varför. Vem som höll i mejseln står sällan där. Av de {sv(N_ALL)} vikingatida runstenarna i Vitkis svenska korpus har {sv(N_NONE)} ingen säker ristare i Rundata, nästan tre av fyra. Bara {N_SIGNED} är signerade.

Balle var en av dem som skrev sitt namn. På stenen vid Ågersta i Uppland avslutar Balle med en uppmaning till den som läser:

> {D729}

”Må den kunnige, som är runkunnig, tyda de runor som Balle ristade.” Tusen år senare gör vi just det, men med en annan fråga: om Balle inte hade skrivit sitt namn, hade vi känt igen handen ändå?

{PH729}

## Hur forskarna känner igen en hand

När en ristare inte signerat sin sten kan forskarna ändå tillskriva den, efter ornamentiken, stavningen och platsen. {N_ATTR} stenar i korpusen har en sådan attribuerad ristare. Det är skickligt arbete, men det är bedömningar, och de bygger på samma slags drag som en dator skulle använda.

Därför har Vitki fått en ny sida, **Ristarna**, som går igenom de kända ristarna en i taget. Den bygger varje ristares fingeravtryck bara av de stenar ristaren själv signerade. De attribuerade stenarna prövas sedan mot avtrycket, i stället för att få forma det. Annars skulle svaret få bestämma frågan.

## Balles fingeravtryck

Balles 20 signerade stenar jämförs med {BV['n']['granne']} samtida grannstenar inom tre mil som andra har rest. Det som skiljer sig är inte stort var för sig, men det går åt samma håll:

- **Gården.** Fem av Balles tjugo stenar nämner var den döde bodde. Bland grannarna gör knappt två av hundra det.
- **Den gode.** Sju av tjugo kallar den döde *góðan*, god. Bland grannarna en av tjugo.
- **Orden.** Tolv av femton skriver *at* för ”efter” där grannarna oftast skriver *æftiR*, och fjorton av tjugo skiljer orden med en punkt.
- **Det som saknas.** Bara sex av tjugo har ett kors, mot två av tre bland grannarna. Ingen av Balles signerade stenar ber för den dödes *and*, själ, och ingen är rest av den dödes barn.

Balles stenar talar alltså oftare om gården och den gode mannen och mer sällan om korset och själen. En del av det kan vara beställarnas val snarare än ristarens, för det är de som bestämmer vad stenen ska säga. Men valen följer med ristaren mellan gårdarna.

{IMG1}

## Sten för sten

På sidan står Balles stenar sedan i en lång rad, en sten per rad och ett drag per kolumn. Rost betyder att stenen gör som Balle, grått att den gör som grannarna. Överst ligger de stenar som följer avtrycket bäst.

{IMG2}

## Kärna och ytterkant

Varje sten får ett värde för hur mycket dess drag talar för Balle mot grannarna. De signerade stenarna sätter själva gränserna: **kärnan** börjar vid den mittersta av dem, och en sten **inom spannet** liknar Balle mer än nio av tio grannstenar gör. I **ytterkanten** ligger stenar som följer avtrycket svagt, och längst ut de som liknar grannarna mer än Balle.

{IMG3}

Av de {MEAS} attribuerade stenar som har tillräckligt med läsbar text ligger {klass['kärna'] + klass['inom spannet']} i kärnan eller inom spannet, {klass['ytterkant']} i ytterkanten och {klass['som grannarna']} bland grannarna. En av de fyra är U 34 vid Sundby, som också i stilen hör till en tidigare generation (Pr1) än Balles stenar. Det betyder inte att attribueringen är fel, men det är en sten att titta på igen.

## Balle den röde

Två av de signerade stenarna står i Västmanland. På den ena, vid Lilla Kyringe, står namnet Balle flera gånger, och på stenens andra sida står:

> {D15}

”En sten har rest, som stå må, Balle den röde efter brodern.” På den andra, vid Hassmyra, står bara *{D24}* – ”Röd-Balle ristade dessa runor.” *Sveriges runinskrifter* räknar dem till Balles mest berömda stenar, och Lilla Kyringe-stenen till de tidigaste, från omkring 1050.

{PH15}

Mätningen säger något om dem, men inte allt. Vs 15 vid Lilla Kyringe är den signerade sten som följer Balles drag sämst av alla tjugo, och den hamnar bland grannarna, vare sig den själv räknas in i avtrycket eller inte. Vs 24 vid Hassmyra ligger bara i ytterkanten, tillsammans med tre signerade stenar i Uppland och Södermanland. Mätningen pekar alltså ut den ena, inte båda.

Vad det beror på kan vi inte avgöra. Lilla Kyringe kan vara en ung ristares tidiga sten, innan stilen satt sig. Den står i en annan bygd, och båda Västmanlandsstenarna hör till den senare stilgruppen Pr4. Eller så var Balle den röde någon annan än Balle i Uppland. Frågan är gammal, men nu går den att mäta.

## Hur bra är maskinen?

Vitkis attribueringsmodell väger samman plats, stil, korsets form, stavning, formler och runpar. Vi prövade den den 4 november mot det enda facit som finns, de {Q1['n']} signerade stenarna av de {len(ATT['carvers'])} ristare som har minst åtta stenar. Varje gång hölls hela socknen utanför, som om stenen kom från en bygd modellen aldrig sett.

Modellen satte rätt ristare först på {pr(Q1['top1'][0])} procent av de signerade stenarna (mellan {pr(Q1['top1'][1])} och {pr(Q1['top1'][2])} procent om man räknar med slumpen) och hade rätt ristare bland sina tre första på {pr(Q1['top3'][0])} procent. Bara platsen ger {pr(AUD['q4']['geografi'][0])} procent. Och de attribuerade stenarna var inte lättare för modellen än de signerade, så den gör mer än att upprepa forskarnas bedömningar.

Men den känner de stora verkstäderna mycket bättre än de små. Öpir fick rätt på {pr(PC['Öpir 1']['top1'])} procent av sina {PC['Öpir 1']['n']} signerade stenar, Balle på {pr(PC['Balle']['top1'])} procent av {PC['Balle']['n']}, Åsmund på {pr(PC['Åsmund']['top1'])} procent av {PC['Åsmund']['n']}. Sex små ristare med mellan en och fyra signerade stenar fick inte en enda rätt.

Det nya är korsets form. Riksantikvarieämbetets Runor beskriver korsen enligt Linn Lagers typologi: hur armarna slutar, hur mitten ser ut, vad korset står på. Med bara stil och kors hittade modellen förut rätt ristare för en tredjedel av stenarna. Med korsets form hittar den rätt för mer än hälften.

{CHART}

Modellen säger också hur säker den är, och det ska gå att lita på. Förut var den för försiktig. Nu är procenten justerade efter provningen, så att ett förslag på 80 procent stämmer ungefär så ofta.

## Stenar som kan vara deras

Det är därför sidan finns: för {sv(len(OK))} runstenar utan ristare sätter modellen en känd ristare först, och för {len([r for r in OK if float(r['p_cal']) >= 0.7])} av dem med minst 70 procent. Där modellen är så osäker att det lika gärna kan vara en ristare den inte känner, säger den ingenting. För Balle föreslår den {len(BS)} stenar. De starkaste är U 806 vid Fröslunda kyrka och U 830 vid Furby, båda med {pr(BS[1]['p'])} procent eller mer.

Det är förslag, inte attribueringar. För de tio små ristarna visar sidan också en andra bedömning, en modell som väger in var och när ristaren verkade. Den hittar oftare rätt för små verkstäder men klarade inte vår låsta prövning, och den står därför tydligt märkt bredvid huvudmodellen.

Sidan vänder sig också åt andra hållet, mot forskningens egna attribueringar. Av de 23 stenar som har attribuerats till Visäte liknar {VIS['som grannarna']} grannarna mer än de signerade Visätestenarna. Det är ett skäl att titta på dem igen, inte ett bevis för att något är fel.

## Vad maskinen inte ser

Forskarnas viktigaste belägg saknas fortfarande: ornamentiken utöver korset, alltså hur djurhuvudena är tecknade, hur svansarna slutar och hur flikarna löper, och runornas former. Vi har försökt läsa ornamentiken ur beskrivningarna i *Sveriges runinskrifter*, men att ett ord står i en artikel säger för lite. Det kräver att varje sten beskrivs på samma sätt, och det arbetet återstår. Runformerna kräver skanningar, och i dag finns som mest fyra skannade stenar per ristare.

Bara fem av de 24 ristarna på sidan har nog med signerade stenar för att bygga ett avtryck på dem: Öpir, Balle, Åsmund, Visäte och Livsten. För de övriga bygger avtrycket på de attribuerade stenarna, och sidan säger det.

## Pröva själv

Öppna Vitki och välj Korpus → Ristarna. Välj en ristare i listan och bläddra med pilarna. Titta särskilt på rutan Ytterkanten och utanför: där står de stenar som inte följer ristarens drag. Har du en av dem nära dig, så gå dit och titta på slingan och korset. Det är där maskinen ännu inte ser, och där ett mänskligt öga fortfarande gör skillnad.

Tidigare har vi skrivit om [stenar som söker sin ristare](/artiklar/fem-runstenar-soker-sin-ristare/) och om [ristarna som aldrig blev ihågkomna](/artiklar/ristarna-som-aldrig-blev-ihagkomna/).

:::box Det viktigaste i korthet
- En ristares hand går att mäta i texten: Balle skrev om gården och den gode mannen, sällan om korset och själen.
- De flesta stenar som forskningen gett Balle passar Balles signerade stenar. Några få gör det inte, och de förtjänar en ny blick.
- Balle den rödes sten vid Lilla Kyringe liknar Balles övriga stenar minst av alla. Det kan vara en tidig sten, en annan bygd eller en annan person.
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
- Bilder: se bildtexterna."""

title_en = "Who Held the Chisel? Vitki Learns to Recognise the Carvers' Hands"
summary_en = ("Three in four Swedish runestones have no known carver. Vitki's new page The carvers goes through the known carvers one "
              "at a time: what sets each apart from the neighbours, which of the stones lie at the heart of the style and which "
              "at the edge, and which stones without a carver could be theirs.")

body_en = f"""Standing in front of a runestone, you usually read three things: who raised it, for whom, and why. Who held the chisel is seldom there. Of the {en_(N_ALL)} Viking Age runestones in Vitki's Swedish corpus, {en_(N_NONE)} have no certain carver in Rundata, nearly three in four. Only {N_SIGNED} are signed.

Balle was one of those who wrote their name. On the stone at Ågersta in Uppland, Balle ends with a request to the reader:

> {D729}

“May the knowing one, who is skilled in runes, interpret the runes that Balle carved.” A thousand years later we are doing just that, but with another question: had Balle not written that name, would we still recognise the hand?

{PH729_EN}

## How researchers recognise a hand

When a carver did not sign a stone, researchers can still attribute it from the ornament, the spelling and the place. {N_ATTR} stones in the corpus have such an attributed carver. It is skilled work, but these are judgements, and they rest on the same kind of traits a computer would use.

So Vitki has a new page, **The carvers**, that goes through the known carvers one at a time. It builds each carver's fingerprint from the stones the carver signed, and only those. The attributed stones are then tested against the fingerprint instead of shaping it. Otherwise the answer would decide the question.

## Balle's fingerprint

Balle's 20 signed stones are compared with {BV['n']['granne']} contemporary neighbouring stones within 30 km raised by others. No single difference is large, but they point the same way:

- **The farm.** Five of Balle's twenty stones say where the dead person lived. Among the neighbours, fewer than two in a hundred do.
- **The good one.** Seven in twenty call the dead *góðan*, good. Among the neighbours, one in twenty.
- **The words.** Twelve in fifteen write *at* for “in memory of” where the neighbours mostly write *æftiR*, and fourteen in twenty divide the words with a dot.
- **What is missing.** Only six in twenty have a cross, against two in three among the neighbours. None of Balle's signed stones prays for the dead person's *and*, the spirit, and none was raised by the dead person's children.

Balle's stones speak more often of the farm and the good man, and less often of the cross and the soul. Some of this may be the patrons' choice rather than the carver's, for they decided what the stone should say. But the choices follow the carver from farm to farm.

{IMG1.replace("Balles fingeravtryck i Vitki", "Balle's fingerprint in Vitki").split(chr(10))[0]}
Balle's fingerprint on the page The carvers: for each trait the share among the 20 signed stones (rust) and among the neighbouring stones (grey). At the top what Balle does more often, at the bottom what Balle does less often. Screenshot from Vitki (Swedish edition).

## Stone by stone

The page then lists Balle's stones one per row, one trait per column. Rust means the stone does as Balle does, grey that it does as the neighbours do. The stones that follow the fingerprint best are at the top.

{IMG2.split(chr(10))[0]}
Stone by stone: each row a stone, each column a trait. Rust means the stone does as Balle does, grey that it does as the neighbours do, pale that the trait cannot be read. The bar on the right shows how well the stone follows the profile. Screenshot from Vitki (the signed stones and the first attributed ones).

## The core and the edge

Each stone gets a value for how much its traits speak for Balle against the neighbours. The signed stones set the limits themselves: **the core** begins at the middle one of them, and a stone **within the span** resembles Balle more than nine in ten neighbouring stones do. **At the edge** are stones that follow the fingerprint only weakly, and furthest out those that resemble the neighbours more than Balle.

{IMG3.split(chr(10))[0]}
Each dot is a stone. On the far right the core, on the far left stones that resemble the neighbours more than Balle. The small grey dots are the neighbouring stones. Screenshot from Vitki.

Of the {MEAS} attributed stones with enough readable text, {klass['kärna'] + klass['inom spannet']} lie in the core or within the span, {klass['ytterkant']} at the edge and {klass['som grannarna']} among the neighbours. One of those four is U 34 at Sundby, which in its style also belongs to an earlier generation (Pr1) than Balle's stones. That does not make the attribution wrong, but it is a stone worth looking at again.

## Balle the Red

Two of the signed stones stand in Västmanland. On one, at Lilla Kyringe, the name Balle appears several times, and the other side of the stone says:

> {D15}

“A stone has raised, that may stand, Balle the Red in memory of the brother.” On the other, at Hassmyra, it says only *{D24}* – “Red-Balle carved these runes.” *Sveriges runinskrifter* counts them among Balle's most famous stones, and the Lilla Kyringe stone among the earliest, from around 1050.

{PH15_EN}

The measurement says something about them, but not everything. Vs 15 at Lilla Kyringe is the signed stone that follows Balle's traits least of all twenty, and it ends up among the neighbours whether or not it is itself counted into the fingerprint. Vs 24 at Hassmyra lies only at the edge, together with three signed stones in Uppland and Södermanland. So the measurement singles out one of them, not both.

What lies behind it we cannot tell. Lilla Kyringe may be a young carver's early stone, before the style had settled. It stands in another district, and both Västmanland stones belong to the later style group Pr4. Or Balle the Red was someone other than Balle in Uppland. The question is old, but now it can be measured.

## How good is the machine?

Vitki's attribution model weighs together place, style, the form of the cross, spelling, formulas and rune pairs. On 4 November we tested it against the only reference there is, the {Q1['n']} signed stones of the {len(ATT['carvers'])} carvers with at least eight stones. Each time the whole parish was left out, as if the stone came from a district the model had never seen.

The model put the right carver first for {pr(Q1['top1'][0])} per cent of the signed stones (between {pr(Q1['top1'][1])} and {pr(Q1['top1'][2])} per cent allowing for chance) and had the right carver among its first three for {pr(Q1['top3'][0])} per cent. The place alone gives {pr(AUD['q4']['geografi'][0])} per cent. And the attributed stones were no easier for the model than the signed ones, so it does more than repeat the researchers' judgements.

But it knows the large workshops far better than the small ones. Öpir was right for {pr(PC['Öpir 1']['top1'])} per cent of {PC['Öpir 1']['n']} signed stones, Balle for {pr(PC['Balle']['top1'])} per cent of {PC['Balle']['n']}, Åsmund for {pr(PC['Åsmund']['top1'])} per cent of {PC['Åsmund']['n']}. Six small carvers with between one and four signed stones did not get a single one right.

What is new is the form of the cross. The Swedish National Heritage Board's Runor describes the crosses following Linn Lager's typology: how the arms end, what the centre looks like, what the cross stands on. With style and cross alone, the model used to find the right carver for a third of the stones. With the form of the cross it finds the right one for more than half.

{CHART_EN}

The model also says how sure it is, and that should be something to rely on. It used to be too cautious. Now the percentages are adjusted after the test, so that a suggestion of 80 per cent is right about that often.

## Stones that could be theirs

That is why the page exists: for {en_(len(OK))} runestones without a carver the model puts a known carver first, and for {len([r for r in OK if float(r['p_cal']) >= 0.7])} of them with at least 70 per cent. Where the model is so unsure that it could just as well be a carver it does not know, it says nothing. For Balle it suggests {len(BS)} stones. The strongest are U 806 at Fröslunda church and U 830 at Furby, both at {pr(BS[1]['p'])} per cent or more.

These are suggestions, not attributions. For the ten small carvers the page also shows a second opinion, a model that weighs in where and when the carver worked. It finds the right carver more often for small workshops but did not pass our locked test, so it stands clearly marked beside the main model.

The page also turns the other way, towards research's own attributions. Of the 23 stones attributed to Visäte, {VIS['som grannarna']} resemble the neighbours more than the signed Visäte stones. That is a reason to look at them again, not proof that anything is wrong.

## What the machine does not see

The researchers' most important evidence is still missing: the ornament beyond the cross – how the animal heads are drawn, how the tails end, how the lobes run – and the forms of the runes. We tried to read the ornament from the descriptions in *Sveriges runinskrifter*, but that a word occurs in an article says too little. It needs every stone described in the same way, and that work remains. The rune forms need scans, and today there are at most four scanned stones per carver.

Only five of the 24 carvers on the page have enough signed stones to build a fingerprint on them: Öpir, Balle, Åsmund, Visäte and Livsten. For the others the fingerprint rests on the attributed stones, and the page says so.

## Try it yourself

Open Vitki and choose Corpus → The carvers. Pick a carver from the list and step through with the arrows. Look especially at the box At the edge and outside: there are the stones that do not follow the carver's traits. If one of them is near you, go there and look at the band and the cross. That is where the machine does not yet see, and where a human eye still makes the difference.

We have written before about [stones looking for their carver](/en/artiklar/fem-runstenar-soker-sin-ristare/) and about [the carvers no one remembered](/en/artiklar/ristarna-som-aldrig-blev-ihagkomna/).

:::box In short
- A carver's hand can be measured in the text: Balle wrote of the farm and the good man, seldom of the cross and the soul.
- Most stones that research has given to Balle fit Balle's signed stones. A few do not, and they deserve a fresh look.
- Balle the Red's stone at Lilla Kyringe resembles Balle's other stones least of all. It may be an early stone, another district or another person.
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
- Images: see the captions."""

# ---- kontroller ---------------------------------------------------------------------------------------
for b_ in (body, body_en):
    assert not re.search(r"^\|", b_, re.M)  # no tables (the article page cannot show them)
    assert b_.count(":::") == 4  # one chart and one box, each closed
assert body_en.count("## ") == body.count("## ")
for word in (" han ", " hans ", " hon ", " henne ", " hennes "):  # no gendered pronouns for the carvers
    assert word not in body, word
for word in (" he ", " his ", " him ", " she ", " her "):
    assert word not in body_en.lower(), word
assert not re.search(r"\b(jag|mig|min)\b", body, re.I)  # we-voice
assert ":::box Det viktigaste i korthet" in body
LABELS = ["Forskning", "Ristare"]
assert blog_labels.check(LABELS) is None

out = {"slug": "vem-holl-i-mejseln", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en, "labels": LABELS}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "ristarna.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "ristarna.json"), len(body.split()), "ord", len(body_en.split()), "words")

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
