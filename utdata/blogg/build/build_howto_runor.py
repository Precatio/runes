"""Så gör du-artikeln om att mäta bara runorna (groove-6): runslingorna, Vänd ristade sidan mot mig, granskningsbilden
och Markera runorna, med skärmbilder ur appen på M 15 vid Sköns kyrka (Henrik Zedigs skanning, CC BY 4.0).
Skärmbilderna och siffrorna kommer ur howto_runor_bilder.py och howto_runor_klick.py (utdata/blogg/howto_runor/):
analys.json (analysens svar), klick.json (markeringarna) och resultat.json (sammanfattningen med runan som enhet).
Varje siffra i texten låses här mot de filerna.
    ../../../.venv/bin/python build_howto_runor.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, limitations  # noqa: E402

D = os.path.join(ROOT, "utdata", "blogg", "howto_runor")
A = json.load(open(os.path.join(D, "analys.json"), encoding="utf-8"))
KLICK = json.load(open(os.path.join(D, "klick.json"), encoding="utf-8"))
R = json.load(open(os.path.join(D, "resultat.json"), encoding="utf-8"))

svn = lambda x, d=1: f"{x:.{d}f}".replace(".", ",")  # noqa: E731
eng = lambda x, d=1: f"{x:.{d}f}"  # noqa: E731

# ---- the analysis of M 15 (Vitki protocol, carved side turned towards the viewer) -------------------------------
C = A["counts"]
assert A["bands"]["source"] == "ritade" and A["provenance"]["mesh"]["filename"].startswith("M 15 Sköns kyrka")
ACC, CAND = C["accepted"], C["candidates"]
OLD_RUNES, OLD_FOUND = C["runes_measured"], C["runes_identified"]
COVER = round(A["bands"]["coverage"] * 100)
assert (ACC, CAND, OLD_RUNES, OLD_FOUND, COVER) == (449, 1798, 27, 46, 30)
# the same file seen 15° off the stone's surface (the page's starting view), run 2026-10-26 before the button existed
TILT_DEG, TILT_ACC = 15, 91
# the old stroke classification measured against the checked bands (utdata/forskningsplan/resultat.md, study 1b)
OLD_OUT, OLD_ORN = 26, 24
assert f"{OLD_OUT} % helt utanför" in open(os.path.join(ROOT, "utdata", "forskningsplan", "resultat.md"), encoding="utf-8").read()
N_BANDS = sum(1 for f in __import__("glob").glob(os.path.join(ROOT, "data", "runmodell", "band", "*", "*.json"))
              if json.load(open(f, encoding="utf-8")).get("status") == "granskad")
assert N_BANDS == 95

# ---- the marks and the rune as the unit ---------------------------------------------------------------------------
MARKS = len(KLICK)
RS = R["rune_summary"]
assert MARKS == 49 and RS["n_runes"] == MARKS
# Rundata: 42 runes and 5 word dividers in M 15's transliteration
TRANSLIT = "biurn : riti stain þino : aftiR : ufriþ : auk at : un sunu sin"
N_RUNOR = sum(ch.isalpha() for ch in TRANSLIT)
N_DIV = TRANSLIT.count(":")
assert (N_RUNOR, N_DIV) == (42, 5)
S_ANG, RS_ANG = R["summary"]["apex_vinkel_deg"], RS["metrics"]["apex_vinkel_deg"]
S_HALF = (S_ANG["ci95"][1] - S_ANG["ci95"][0]) / 2
R_HALF = (RS_ANG["ci95"][1] - RS_ANG["ci95"][0]) / 2
ICC = RS_ANG["icc"]
S_D, RS_D = R["summary"]["spårdjup_mm"], RS["metrics"]["spårdjup_mm"]
assert S_ANG["n"] == ACC and R_HALF > S_HALF
MIN_DESCRIBE, MIN_COMPARE = limitations.MIN_RUNES_DESCRIBE, limitations.MIN_RUNES_COMPARE

SKANNING = ("Skanning: Henrik Zedig, Länsstyrelsen Västra Götalands län · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.sv) · "
            "[doi:10.5281/zenodo.14141222](https://doi.org/10.5281/zenodo.14141222). Bilden är beräknad i Vitki.")
SCAN_EN = ("Scan: Henrik Zedig, Länsstyrelsen Västra Götalands län · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · "
           "[doi:10.5281/zenodo.14141222](https://doi.org/10.5281/zenodo.14141222). Image computed in Vitki.")
_frozen: dict[str, str] = {}


def url(fil: str, max_w: int = 1600) -> str:
    """The screenshot frozen in the blog's image archive (at most max_w px wide), once per file."""
    if fil not in _frozen:
        im = Image.open(os.path.join(D, fil)).convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        out = io.BytesIO()
        im.save(out, "PNG", optimize=True)
        _frozen[fil] = blog_figures.freeze(out.getvalue())
    return _frozen[fil]


def bild(fil: str, alt: str, text: str, en: bool = False, scan: bool = True) -> str:
    credit = (SCAN_EN if en else SKANNING) if scan else ""
    return f"![{alt}]({url(fil)})\n{text}" + (f" {credit}" if credit else "")


title = "Så gör du: mät runorna, inte ormen"
summary = ("En runsten är mer än sin text: ormen, slingans kanter, korset. Så får du Vitkis huggspårsanalys att mäta "
           "bara runorna – eller bara ornamentiken – och så markerar du runorna med ett klick var, så att varje runa "
           "väger lika mycket.")

body = f"""Den som mäter huggspåren på en runsten vill oftast veta hur runorna är huggna. Men stenen är full av annat som också är huggning: ormens kropp, slingans kanter, korset i mitten. Mäter man allt i en klump blandas ristarens bokstäver med hans ornamentik, och då säger medelvärdet inte längre något bestämt om någondera.

Vitki har därför fått ett nytt sätt att avgöra vad som är runor. Det gamla gick på strecken: korta raka spår blev runor, långa jämna spår ornamentik. När vi prövade det mot slingor som ritats för hand visade det sig fel åt båda hållen. Av det den gamla klassningen kallade runor låg {OLD_OUT} % helt utanför textslingorna, och av det den kallade ornamentik var {OLD_ORN} % runor. Nu går Vitki på var texten står. Den här handledningen visar hur det fungerar, steg för steg, på en verklig sten.

## Stenen i exemplet

Vi använder M 15 vid Sköns kyrka i Medelpad. Björn reste stenen efter två söner, Ofrid och Un, och lät texten löpa i en orm som slingrar sig runt ett kors. Henrik Zedig skannade den, och skanningen ligger öppet på Zenodo. Mer om skanningen står sist.

## Steg 1. Vänd den ristade sidan mot dig

Analysen mäter det som vetter mot dig på skärmen. Ser du stenen snett blir spåren snedskurna, och många snitt sorteras bort som för grunda eller för otydliga. Därför finns knappen **Vänd ristade sidan mot mig** nere till vänster i 3D-vyn. Den vrider vyn så att du ser rakt på stenens bredaste sida. Är det fel sida trycker du en gång till.

Skillnaden är stor. När vi körde analysen på M 15 från sidans startvy, {TILT_DEG}° snett, godkändes {TILT_ACC} snitt. Efter ett tryck på knappen godkändes {ACC}.

{bild("01b_vy.png", "M 15 i 3D-vyn med knappen Vänd ristade sidan mot mig", "M 15 efter ett tryck på knappen: vyn ser rakt på den ristade sidan.")}

## Steg 2. Välj vad som ska mätas

Välj **Automatiskt** som mätsätt. Överst i panelen frågar Vitki **Vad ska mätas?** Förvalt är **Runor**. Väljer du **Ornamentik** mäts i stället spåren utanför textslingorna. Under valet står i fem korta punkter hur Vitki avgör vad som är vad. Låt **Vitki-protokollet** vara ikryssat, så kan stenen jämföras med andra som mätts på samma sätt. Klicka sedan på **Kör automatisk analys**.

{bild("01_vad_ska_matas.png", "Panelen för automatisk analys med valet Runor eller Ornamentik", "Valet mellan runor och ornamentik och förklaringen under det.", scan=False)}
"""

body += f"""
## Steg 3. Läs raden om runslingorna

När analysen är klar står en rad under knappen: varifrån runslingorna kom, hur stor del av ytan de täcker och vad som mättes. Runslingorna är banden som texten står i. Vitki hittar dem på två sätt. För de öppna skanningarna finns slingor som vi har ritat och granskat för hand, {N_BANDS} stenar hittills, och Vitki känner igen filen på dess fingeravtryck. För andra skanningar föreslår en liten bildmodell var slingorna går, tränad på de handritade. Det är ett förslag, och raden säger det: *kontrollera dem i granskningsbilden*.

{bild("02_status_slingor.png", "Raden om runslingorna under knappen Kör automatisk analys", "På M 15 kom slingorna från de handritade, och de täcker {COVER} % av ytan.")}

## Steg 4. Granska slingorna i bilden

Under 3D-vyn kommer granskningsbilden. Slingorna syns som ett ljusblått fält, de mätta snitten som små prickar. Ett snitt räknas som runa om det ligger inne i slingan och går tvärs eller snett över den, alltså som en runas stav. Spår som löper längs slingan är slingans egna kanter och mäts inte. Allt utanför slingan räknas som ornamentik.

Titta efter två saker. Ligger en runa utanför det blå har slingan blivit för smal där. Ligger ornamentik inne i det blå har den blivit för bred. Då kan du vrida stenen rakare och köra igen, märka punkterna med en ruta som *Ornamentik* eller *Utesluten*, eller mäta just de runorna för hand.

{bild("03_granskning.png", "Granskningsbilden för M 15 med runslingan som ljusblått fält", "Granskningsbilden för M 15. Det blå fältet följer ormen med texten; korset och ormens huvud ligger utanför och mäts inte. Analysen godkände {ACC} av {CAND} snitt.")}

## Steg 5. Markera runorna

Här kommer det nya. Snitten tas med jämna mellanrum, var tredje millimeter, så en lång runa med flera stavar får många snitt och en liten runa få. Räknar man stenens medelvärde över snitten väger de stora runorna tyngst, och osäkerheten ser mindre ut än den är, eftersom snitten i samma runa inte är oberoende av varandra. De delar ristarens slag, hans verktyg och samma vittring. Det ärliga är att låta runan vara enheten: först varje runas medelvärde, sedan medelvärdet av runorna.

Då måste Vitki veta var den ena runan slutar och nästa börjar. Den gamla analysen gissade det ur strecken och hittade {OLD_RUNES} mätta runor på M 15. Bättre är att du talar om det. Klicka på **Markera runorna** och klicka sedan en gång mitt på varje runa, i läsordning. Du behöver inte veta vilken runa det är. Varje runsnitt hör sedan till den närmaste markeringen. Snitt långt från alla markeringar, till exempel i en runa du hoppat över, hör inte till någon och visas bleka. **Ångra senaste** tar bort den sista markeringen.

{bild("04_markerade.png", "Granskningsbilden med numrerade markeringar på runorna", "M 15 med {MARKS} markeringar längs slingan, i läsordning.")}

{bild("05_markera_ruta.png", "Rutan Markera runorna med antal markerade runor", "Rutan säger hur många runor du markerat och hur många av runsnitten som fått en runa.", scan=False)}

En ärlig anmärkning om bilderna: markeringarna i dem satte vi med ett skript som följer slingans mittlinje och sätter en markering där det finns mätta spår. Det blev {MARKS}, fler än stenens {N_RUNOR} runor, eftersom några av de {N_DIV} skiljetecknen och några delade runor fick egna. Gör du det själv klickar du bara på runorna.
"""

body += f"""
## Steg 6. Läs måtten med runan som enhet

Klicka på **Använd runorna som resultat**. Rutorna överst visar stenens mått räknade över snitten. Under dem kommer rutan **Med runan som enhet**: samma mått, räknade på runornas medelvärden.

{bild("07_runan_som_enhet.png", "Rutan Med runan som enhet med mått, intervall och ICC", "Stenens mått med runan som enhet, med 95 %-intervall och ICC för varje mått.")}

På M 15 är V-vinkeln – vinkeln i spårets botten – {svn(S_ANG["mean"])}° räknad över {ACC} snitt och {svn(RS_ANG["mean"])}° räknad över {RS["n_runes"]} runor. Medelvärdet flyttar sig lite. Det som ändras mest är osäkerheten. Över snitten ser vinkeln ut att vara känd på ±{svn(S_HALF)}°. Över runorna är intervallet ±{svn(R_HALF)}°. Det bredare intervallet är det ärliga: det räknar med att varje runa är ett eget hugg, inte {round(ACC / RS["n_runes"])} oberoende mätningar.

ICC, {svn(ICC, 2)} för V-vinkeln, säger hur stor del av spridningen som ligger mellan runorna snarare än inom dem. Ett värde nära noll betyder att runorna är huggna ungefär lika och att skillnaderna mest finns inom varje runa. Ett värde nära ett betyder att runorna skiljer sig åt sinsemellan, och då är det särskilt viktigt att räkna med runan som enhet.

Riktvärdena är {MIN_DESCRIBE} mätta runor för att beskriva en sten och {MIN_COMPARE} för att jämföra den med andra. De är tumregler, inte garantier.

## Vad verktyget inte gör

Vitki läser inte runorna. Markeringarna säger var en runa är, inte vilken. Slingorna från bildmodellen är förslag: på stenar som ingen har ritat slingorna på kan modellen hitta bara delar av slingan, och därför finns granskningsbilden. Och måtten beskriver hur spåren är huggna, inte vem som högg dem. Bergarten och vittringen formar också spåren, så måtten ensamma säger inte vem som ristade.

:::box Det viktigaste i korthet
- Runor och ornamentik huggs ofta olika. Vitki skiljer dem nu efter var texten står, inte efter hur strecken ser ut, och du ser själv i bilden var gränsen gick.
- Vänd den ristade sidan mot dig innan du mäter. På M 15 var det skillnaden mellan {TILT_ACC} och {ACC} godkända snitt.
- Ett klick per runa gör runan till enhet. Medelvärdet ändras lite, men osäkerheten blir ärlig.
- Allt detta beskriver huggningen. Vem som högg är en annan fråga.
:::

## Om skanningen

M 15 vid Sköns kyrka i Sundsvalls kommun, Medelpad, är en runsten i stilgrupp Pr2 från vikingatiden. Rundata läser texten *biurn : riti stain þino : aftiR : ufriþ : auk at : un sunu sin*, »Björn reste denna sten efter Ofrid och efter Un, sina söner«. Stenen skannades av Henrik Zedig vid Länsstyrelsen Västra Götalands län med en handhållen laserskanner (Creaform HandySCAN BLACK Elite, upplösning 0,40 mm) inom forskningsprojektet *Evighetsrunor: en forskningsplattform för Sveriges runinskrifter* och som förberedelse för en korpusutgåva av Medelpads runinskrifter. Skanningen publicerades öppet på Zenodo den 13 november 2024 i datamängden *3D-data Runstenar i Medelpad* av Laila Kitzler Åhfeldt (Riksantikvarieämbetet) och Henrik Zedig, under licensen [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.sv). Vi har använt filen som den är publicerad; alla bilder och mått i artikeln är beräknade i Vitki ur den. Tack till Henrik Zedig och Laila Kitzler Åhfeldt för att skanningarna är fritt tillgängliga.

## Källor

- Kitzler Åhfeldt, L. & Zedig, H. 2024. *3D-data Runstenar i Medelpad* [Dataset]. Riksantikvarieämbetet. [https://doi.org/10.5281/zenodo.14141222](https://doi.org/10.5281/zenodo.14141222)
- Samnordisk runtextdatabas (Rundata), M 15.
- Vitkis metoddokumentation, avsnitt 2c (*Runslingorna* och *Runor markerade för hand*) och avsnitt 3 (*Osäkerhet*)."""


title_en = "How to: measure the runes, not the serpent"
summary_en = ("A runestone is more than its text: the serpent, the edges of the band, the cross. This is how you get "
              "Vitki's groove analysis to measure only the runes – or only the ornament – and how you mark the runes "
              "with one click each, so that every rune weighs the same.")

body_en = f"""Anyone who measures the grooves on a runestone usually wants to know how the runes were cut. But the stone is full of other carving: the serpent's body, the edges of the band, the cross in the middle. Measure it all in one lump and the carver's letters mix with his ornament, and the average no longer says anything definite about either.

So Vitki has a new way of deciding what a rune is. The old one went by the strokes: short straight grooves became runes, long even grooves ornament. When we tested it against bands drawn by hand, it was wrong in both directions. Of what the old classification called runes, {OLD_OUT} % lay entirely outside the text bands, and of what it called ornament, {OLD_ORN} % were runes. Now Vitki goes by where the text stands. This guide shows how it works, step by step, on a real stone.

## The stone in the example

We use M 15 at Skön church in Medelpad. Bjôrn raised the stone in memory of two sons, Ófriðr and Unn, and let the text run in a serpent coiled around a cross. Henrik Zedig scanned it, and the scan is openly available on Zenodo. More about the scan at the end.

## Step 1. Turn the carved side towards you

The analysis measures what faces you on the screen. Seen at an angle, the grooves are cut obliquely, and many cross-sections are rejected as too shallow or too unclear. That is why there is a button, **Turn the carved side towards me**, at the bottom left of the 3D view. It turns the view so that you look straight at the stone's broadest side. If it is the wrong side, press it once more.

The difference is large. When we ran the analysis on M 15 from the page's starting view, {TILT_DEG}° off, {TILT_ACC} cross-sections were accepted. After one press of the button, {ACC} were.

{bild("01b_vy.png", "M 15 in the 3D view with the button Turn the carved side towards me", "M 15 after one press of the button: the view looks straight at the carved side.", en=True)}

## Step 2. Choose what to measure

Choose **Automatic** as the measuring mode. At the top of the panel Vitki asks **What should be measured?** The default is **Runes**. If you choose **Ornament**, the grooves outside the text bands are measured instead. Below the choice, five short points explain how Vitki decides which is which. Leave the **Vitki protocol** ticked, so that the stone can be compared with others measured the same way. Then click **Run automatic analysis**.

{bild("01_vad_ska_matas.png", "The automatic analysis panel with the choice Runes or Ornament", "The choice between runes and ornament, and the explanation below it.", en=True, scan=False)}

## Step 3. Read the line about the runic bands

When the analysis is done, a line appears under the button: where the runic bands came from, how much of the surface they cover and what was measured. The runic bands are the ribbons the text stands in. Vitki finds them in two ways. For the open scans there are bands we have drawn and checked by hand, {N_BANDS} stones so far, and Vitki recognises the file by its fingerprint. For other scans, a small image model trained on the hand-drawn bands proposes where they run. It is a proposal, and the line says so: *check them in the review image*.

{bild("02_status_slingor.png", "The line about the runic bands under the button Run automatic analysis", "On M 15 the bands came from the hand-drawn ones, and they cover {COVER} % of the surface.", en=True)}
"""

body_en += f"""
## Step 4. Check the bands in the image

Below the 3D view comes the review image. The bands appear as a light-blue field, the measured cross-sections as small dots. A cross-section counts as a rune if it lies inside the band and runs across or diagonally over it, the way a rune's staff does. Grooves running along the band are the band's own edges and are not measured. Everything outside the band counts as ornament.

Look for two things. If a rune lies outside the blue, the band has become too narrow there. If ornament lies inside the blue, it has become too wide. You can then turn the stone straighter and run again, label the dots with a box as *Ornament* or *Excluded*, or measure those runes by hand.

{bild("03_granskning.png", "The review image for M 15 with the runic band as a light-blue field", "The review image for M 15. The blue field follows the serpent with the text; the cross and the serpent's head lie outside and are not measured. The analysis accepted {ACC} of {CAND} cross-sections.", en=True)}

## Step 5. Mark the runes

This is the new part. Cross-sections are taken at even intervals, every third millimetre, so a long rune with several staves gets many and a small rune few. Average the stone over the cross-sections and the large runes weigh the most, and the uncertainty looks smaller than it is, because cross-sections in the same rune are not independent of each other. They share the carver's blows, his tool and the same weathering. The honest way is to let the rune be the unit: first each rune's mean, then the mean of the runes.

Vitki then has to know where one rune ends and the next begins. The old analysis guessed it from the strokes and found {OLD_RUNES} measured runes on M 15. It is better if you tell it. Click **Mark the runes** and then click once in the middle of each rune, in reading order. You do not need to know which rune it is. Every rune cross-section then belongs to the nearest mark. Cross-sections far from every mark, for example in a rune you skipped, belong to none and are shown faded. **Undo the last one** removes the last mark.

{bild("04_markerade.png", "The review image with numbered marks on the runes", "M 15 with {MARKS} marks along the band, in reading order.", en=True)}

{bild("05_markera_ruta.png", "The Mark the runes box with the number of marked runes", "The box tells you how many runes you have marked and how many of the rune cross-sections have been given a rune.", en=True, scan=False)}

An honest note about the pictures: we placed the marks in them with a script that follows the band's centre line and puts a mark wherever there are measured grooves. That gave {MARKS}, more than the stone's {N_RUNOR} runes, because some of the {N_DIV} word dividers and some split runes got marks of their own. When you do it yourself, you click only on the runes.

## Step 6. Read the measurements with the rune as the unit

Click **Use the runes as the result**. The boxes at the top show the stone's measurements computed over the cross-sections. Below them comes the box **With the rune as the unit**: the same measurements, computed on the runes' means.

{bild("07_runan_som_enhet.png", "The box With the rune as the unit with measurements, intervals and ICC", "The stone's measurements with the rune as the unit, with a 95 % interval and ICC for each measurement.", en=True)}

On M 15 the V-angle – the angle at the bottom of the groove – is {eng(S_ANG["mean"])}° computed over {ACC} cross-sections and {eng(RS_ANG["mean"])}° computed over {RS["n_runes"]} runes. The mean moves a little. What changes most is the uncertainty. Over the cross-sections, the angle seems known to ±{eng(S_HALF)}°. Over the runes, the interval is ±{eng(R_HALF)}°. The wider interval is the honest one: it counts each rune as one piece of carving, not as {round(ACC / RS["n_runes"])} independent measurements.

ICC, {eng(ICC, 2)} for the V-angle, tells how much of the spread lies between the runes rather than within them. A value near zero means the runes were cut much alike and the differences lie mostly within each rune. A value near one means the runes differ from each other, and then it matters most to count with the rune as the unit.

The guidelines are {MIN_DESCRIBE} measured runes to describe a stone and {MIN_COMPARE} to compare it with others. They are rules of thumb, not guarantees.

## What the tool does not do

Vitki does not read the runes. The marks say where a rune is, not which one. Bands from the image model are proposals: on stones whose bands nobody has drawn, the model may find only parts of the band, which is why the review image is there. And the measurements describe how the grooves were cut, not who cut them. The stone and its weathering shape the grooves too, so the measurements alone do not say who carved.

:::box The essentials in brief
- Runes and ornament are often cut differently. Vitki now tells them apart by where the text stands, not by what the strokes look like, and you can see for yourself in the image where the line was drawn.
- Turn the carved side towards you before you measure. On M 15 it was the difference between {TILT_ACC} and {ACC} accepted cross-sections.
- One click per rune makes the rune the unit. The mean changes a little, but the uncertainty becomes honest.
- All of this describes the carving. Who carved is another question.
:::

## About the scan

M 15 at Skön church in Sundsvall municipality, Medelpad, is a Viking-age runestone in style group Pr2. Rundata reads the text *biurn : riti stain þino : aftiR : ufriþ : auk at : un sunu sin*, "Bjôrn erected this stone in memory of Ófriðr and in memory of Unn, his sons". The stone was scanned by Henrik Zedig of Länsstyrelsen Västra Götalands län with a handheld laser scanner (Creaform HandySCAN BLACK Elite, resolution 0.40 mm) within the research project *Evighetsrunor: en forskningsplattform för Sveriges runinskrifter* (Everlasting Runes: a research platform for Sweden's runic inscriptions) and in preparation for a corpus edition of the runic inscriptions of Medelpad. The scan was published openly on Zenodo on 13 November 2024 in the dataset *3D-data Runstenar i Medelpad* by Laila Kitzler Åhfeldt (Swedish National Heritage Board) and Henrik Zedig, under the licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). We used the file as published; every image and measurement in this article was computed from it in Vitki. Our thanks to Henrik Zedig and Laila Kitzler Åhfeldt for making the scans freely available.

## Sources

- Kitzler Åhfeldt, L. & Zedig, H. 2024. *3D-data Runstenar i Medelpad* [Dataset]. Riksantikvarieämbetet. [https://doi.org/10.5281/zenodo.14141222](https://doi.org/10.5281/zenodo.14141222)
- Scandinavian Runic-text Database (Rundata), M 15.
- Vitki's method documentation, section 2c (*Runslingorna* and *Runor markerade för hand*) and section 3 (*Osäkerhet*)."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M)  # BlogBody has no tables
    assert b.count(":::box") == 1 and "Kitzler Åhfeldt" in b and "Zedig" in b
out = {"slug": "sa-gor-du-mat-runorna-inte-ormen", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en, "labels": ["Så gör du", "Huggspår och 3D"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "howto_runor.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "howto_runor.json"), len(body.split()), "ord,", len(body_en.split()), "words")

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
                 "topic": "Så gör du|huggspår", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
