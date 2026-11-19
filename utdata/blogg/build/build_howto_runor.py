"""Så gör du-artikeln om att mäta bara runorna, som huggspårsanalysen fungerar i appen sedan groove-7 (2026-11-03):
Vänd ristade sidan mot mig, runslingorna, granskningsbilden, runorna indelade längs slingan, Markera runorna och bilden
Runor och ornamentik (samma vy varje gång, från 2026-11-08), med skärmbilder ur appen på M 15 vid Sköns kyrka
(Henrik Zedigs skanning, CC BY 4.0).

Skärmbilderna och siffrorna kommer ur howto_runor_bilder.py och howto_runor_klick.py (utdata/blogg/howto_runor/):
analys_startvy.json och analys.json (analysens svar före och efter knappen), resultat_auto.json (runan som enhet med
appens egen indelning), klick.json och resultat.json (runorna markerade för hand), band_bild.json (Runor och
ornamentik); de engelska skärmbilderna och filerna har ändelsen _en. Övriga tal läses ur
utdata/forskningsplan/resultat.md (studie 1b), utdata/stavlosa/ka_tabell.json (runindelningen på 34 skanningar),
data/runmodell/band/ (de granskade slingorna), Rundata (via src/rune_links) och src/limitations. Varje tal i texten
läses ur de filerna och låses här med assert.
    ../../../.venv/bin/python build_howto_runor.py [--write | --update DOC]"""
import datetime as dt
import glob
import io
import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.config import METHOD_VERSION  # noqa: E402
from src import blog_figures, blog_labels, limitations, rune_links  # noqa: E402

D = os.path.join(ROOT, "utdata", "blogg", "howto_runor")
load = lambda name: json.load(open(os.path.join(D, name), encoding="utf-8"))  # noqa: E731
A0, A0_EN = load("analys_startvy.json"), load("analys_startvy_en.json")
A, A_EN = load("analys.json"), load("analys_en.json")
RA, RA_EN = load("resultat_auto.json"), load("resultat_auto_en.json")
KLICK = load("klick.json")
R, R_EN = load("resultat.json"), load("resultat_en.json")
BB, BB_EN = load("band_bild.json"), load("band_bild_en.json")

svn = lambda x, d=1: f"{x:.{d}f}".replace(".", ",")  # noqa: E731
eng = lambda x, d=1: f"{x:.{d}f}"  # noqa: E731
sv_int = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_int = lambda n: f"{n:,}"  # noqa: E731

# ---- the analysis of M 15 (Vitki protocol), before and after Vänd ristade sidan mot mig ---------------------------
assert METHOD_VERSION == "groove-7"
for a in (A0, A0_EN, A, A_EN):
    assert a["provenance"]["mesh"]["filename"].startswith("M 15 Sköns kyrka")
    assert a["provenance"]["method_version"] == METHOD_VERSION, a["provenance"].get("method_version")
    assert a["parameters"]["measure"] == "runes" and a["parameters"]["runes_only"] is True
    assert a["provenance"]["protocol"]["compliant"], a["provenance"]["protocol"]
# the Swedish and the English run measured the same thing from the same view
assert A["counts"] == A_EN["counts"] and np.allclose(A["parameters"]["normal"], A_EN["parameters"]["normal"])
assert A["bands"] == A_EN["bands"] and A["bands"]["source"] == "ritade" and not A["bands"].get("note")
C = A["counts"]
ACC, CAND = C["accepted"], C["candidates"]
RUNES_MEASURED, RUNES_FOUND = C["runes_measured"], C["runes_identified"]
COVER = round(A["bands"]["coverage"] * 100)
# from the starting view (behind) nothing is measured since 2026-11-19: every cross-section is rejected as seen from
# behind, and the line under the run button says why (rune_bands.BEHIND_NOTE)
from src import rune_bands  # noqa: E402
for a0 in (A0, A0_EN):
    assert a0["counts"]["accepted"] == 0 and a0["bands"].get("behind") is True and a0["bands"]["note"] == rune_bands.BEHIND_NOTE
    assert a0["counts"]["rejection_reasons"] == {rune_bands.BEHIND_REASON: a0["counts"]["candidates"]}
assert A0["counts"] == A0_EN["counts"]
CAND0 = A0["counts"]["candidates"]
# the starting view looks at the scan from behind (the open scan is a shell: from the back only its edges show) and
# at an angle to the stone's axis; the angle is taken between the two lines of sight, the side from the sign
COS0 = float(np.dot(A0["parameters"]["normal"], A["parameters"]["normal"]))
FROM_BEHIND = COS0 < 0
TILT_DEG = round(math.degrees(math.acos(min(1.0, abs(COS0)))))
assert FROM_BEHIND and TILT_DEG >= 5 and ACC > 0, (COS0, TILT_DEG, ACC)
REASONS = C["rejection_reasons"]
OUT_BANDS = REASONS.get("utanför runslingorna", 0)
BAND_EDGE = REASONS.get("slingkant, inte runa", 0)
assert OUT_BANDS and BAND_EDGE

# ---- why the bands: the old stroke classification against the checked bands (study 1b) ---------------------------
RES_MD = open(os.path.join(ROOT, "utdata", "forskningsplan", "resultat.md"), encoding="utf-8").read()
m = re.search(r"Viktors granskade slingor på (\d+) filer.*?kallade runa ligger (\d+) % helt utanför textslingorna; "
              r"av det den\s+kallade ornamentik är (\d+) % runor", RES_MD, re.S)
OLD_FILES, OLD_OUT, OLD_ORN = (int(g) for g in m.groups())
N_BANDS = sum(1 for f in glob.glob(os.path.join(ROOT, "data", "runmodell", "band", "*", "*.json"))
              if json.load(open(f, encoding="utf-8")).get("status") == "granskad")

# ---- Rundata: runes and word dividers in M 15's transliteration --------------------------------------------------
REC, _ = rune_links.rundata_record("M 15")
TR = rune_links.transliteration_for(REC)
TRANSLIT = TR["transliteration"]
N_RUNOR = sum(t["kind"] == "rune" for t in TR["tokens"])
N_DIV = sum(t["kind"] == "divider" for t in TR["tokens"])
assert N_RUNOR + N_DIV == len(TR["tokens"])

# ---- the rune as the unit: the app's own division along the band -------------------------------------------------
assert RA == RA_EN or RA["rune_summary"] == RA_EN["rune_summary"]
RSA = RA["rune_summary"]
AUTO_RUNES = RSA["n_runes"]
S_ANG, RA_ANG = RA["summary"]["apex_vinkel_deg"], RSA["metrics"]["apex_vinkel_deg"]
assert S_ANG["n"] == ACC
half = lambda s: (s["ci95"][1] - s["ci95"][0]) / 2  # noqa: E731
S_HALF, RA_HALF = half(S_ANG), half(RA_ANG)
assert RA_HALF > S_HALF
ICC_A = RA_ANG["icc"]
PER_RUNE = round(ACC / AUTO_RUNES)
# the division along the band on Kitzler Åhfeldt's Södermanland scans (METHODS 2c, groove-7)
KA = json.load(open(os.path.join(ROOT, "utdata", "stavlosa", "ka_tabell.json"), encoding="utf-8"))["summary"]
KA_N, KA_RATIO, KA_WITHIN = KA["med_minst_10_textrunor"], KA["slinga_matta"]["kvot_median"], KA["slinga_matta"]["inom_25_procent"]
KA_OVER = round((KA_RATIO - 1) * 100)
assert KA_OVER > 0 and AUTO_RUNES > 1.25 * N_RUNOR  # M 15 lies outside the quarter: "one of the harder cases"
MIN_DESCRIBE, MIN_COMPARE = limitations.MIN_RUNES_DESCRIBE, limitations.MIN_RUNES_COMPARE

# ---- the marks ----------------------------------------------------------------------------------------------------
MARKS = len(KLICK)
assert R["rune_summary"] == R_EN["rune_summary"] or R["rune_summary"]["n_runes"] == R_EN["rune_summary"]["n_runes"]
RSM = R["rune_summary"]
assert RSM["n_runes"] <= MARKS
MARKED = RSM["n_runes"]
RM_ANG = RSM["metrics"]["apex_vinkel_deg"]
RM_HALF = half(RM_ANG)
ICC_M = RM_ANG["icc"]

# ---- Runor och ornamentik -----------------------------------------------------------------------------------------
for bb in (BB, BB_EN):
    assert bb["source"] == "ritade" and bb["view"]["kind"] == "protokoll", bb["view"]
IN_BANDS, BAND_SHARE = round(BB["in_bands"] * 100), round(BB["band_share"] * 100)
assert (IN_BANDS, BAND_SHARE) == (round(BB_EN["in_bands"] * 100), round(BB_EN["band_share"] * 100))
assert IN_BANDS > BAND_SHARE

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
    """A screenshot with its caption; the English article gets the English screenshot (…_en.png)."""
    if en:
        stem, ext = os.path.splitext(fil)
        fil = stem + "_en" + ext
    credit = (SCAN_EN if en else SKANNING) if scan else ""
    return f"![{alt}]({url(fil)})\n{text}" + (f" {credit}" if credit else "")


title = "Så gör du: mät runorna, inte ormen"
summary = ("En runsten är mer än sin text: ormen, slingans kanter, korset. Så får du Vitkis huggspårsanalys att mäta "
           "bara runorna – eller bara ornamentiken – och så räknar du med runan som enhet, så att varje runa väger lika "
           "mycket.")

body = f"""Den som mäter huggspåren på en runsten vill oftast veta hur runorna är huggna. Men stenen är full av annat som också är huggning: ormens kropp, slingans kanter, korset i mitten. Mäter man allt i en klump blandas runorna med ornamentiken, och då säger medelvärdet inte längre något bestämt om någondera.

Vitki avgör därför vad som är runor efter var texten står, inte efter hur strecken ser ut. Vi prövade det gamla sättet, som gick på strecken – korta raka spår blev runor, långa jämna spår ornamentik – mot slingor som ritats för hand på {OLD_FILES} skanningar. Det blev fel åt båda hållen. Av det den gamla klassningen kallade runor låg {OLD_OUT} % helt utanför textslingorna, och av det den kallade ornamentik var {OLD_ORN} % runor. Den här handledningen visar hur analysen fungerar i dag, steg för steg, på en verklig sten.

## Stenen i exemplet

Vi använder M 15 vid Sköns kyrka i Medelpad. Björn reste stenen efter två söner, Ofrid och Un, och lät texten löpa i en orm som slingrar sig runt ett kors. Henrik Zedig skannade den, och skanningen ligger öppet på Zenodo. Mer om skanningen står sist.

## Steg 1. Vänd den ristade sidan mot dig

Analysen mäter det som vetter mot dig på skärmen. Ser du stenen snett blir spåren snedskurna, och många snitt sorteras bort som för grunda eller för otydliga. Därför finns knappen **Vänd ristade sidan mot mig** nere till vänster i 3D-vyn. Den vrider vyn så att du ser rakt på stenens bredaste sida. Är det fel sida trycker du en gång till.

Det spelar roll. När M 15 laddats ser sidans startvy på skanningen bakifrån och {TILT_DEG}° snett. Skanningen är bara stenens yta, ett tunt skal, så bakifrån syns nästan bara kanterna. De ritade slingorna gäller den ristade sidan, så kör du analysen därifrån mäts ingenting: alla {sv_int(CAND0)} snitt sorteras bort som *stenen sedd bakifrån*, och raden under knappen säger efter ett **Obs** vad du ska göra. Efter ett tryck på knappen godkändes {ACC} snitt.

{bild("01a_startvy.png", "M 15 i startvyn, sedd bakifrån så att bara kanterna syns", f"M 15 i sidans startvy: skanningen sedd bakifrån och {TILT_DEG}° snett.")}

{bild("01c_bakifran_obs.png", "Varningen under knappen Kör automatisk analys när stenen ses bakifrån", "Bakifrån mäter analysen ingenting och säger varför.", scan=False)}

{bild("01b_vy.png", "M 15 i 3D-vyn med knappen Vänd ristade sidan mot mig", f"Samma skanning efter ett tryck på knappen: vyn ser rakt på den ristade sidan, och analysen godkände {ACC} snitt.")}

## Steg 2. Välj vad som ska mätas

Välj **Automatiskt** som mätsätt. Överst i panelen frågar Vitki **Vad ska mätas?** Förvalt är **Runor**. Väljer du **Ornamentik** mäts i stället spåren utanför textslingorna. Under valet står i några korta punkter hur Vitki avgör vad som är vad. Har stenen stavlösa runor (hälsingerunor) kryssar du i **Stavlösa runor**; Vitki gör det själv när Rundata anger att stenen bara har sådana. Låt **Vitki-protokollet** vara ikryssat, så kan stenen jämföras med andra som mätts på samma sätt. Klicka sedan på **Kör automatisk analys**.

{bild("01_vad_ska_matas.png", "Panelen för automatisk analys med valet Runor eller Ornamentik", "Valet mellan runor och ornamentik, förklaringen under det och Vitki-protokollet.", scan=False)}

## Steg 3. Läs raden om runslingorna

När analysen är klar står en rad under knappen: varifrån runslingorna kom, hur stor del av ytan de täcker och vad som mättes. Runslingorna är banden som texten står i. Vitki hittar dem på två sätt. För de öppna skanningarna finns slingor som vi har ritat och granskat för hand, {N_BANDS} stenar hittills, och Vitki känner igen filen på dess fingeravtryck. För andra skanningar föreslår en liten bildmodell var slingorna går, tränad på de handritade. Det är ett förslag, och raden säger det: *kontrollera dem i granskningsbilden*.

Finns det ritade slingor för filen men kan Vitki inte använda dem, till exempel för att du ser stenen från ett helt annat håll än slingorna ritades i, står det på samma rad efter ett **Obs**, och analysen använder modellens slingor i stället.

{bild("02_status_slingor.png", "Raden om runslingorna under knappen Kör automatisk analys", f"På M 15 kom slingorna från de handritade, och de täcker {COVER} % av ytan.")}
"""

body += f"""
## Steg 4. Granska slingorna i bilden

Under 3D-vyn kommer granskningsbilden. Slingorna syns som ett ljusblått fält, de mätta snitten som prickar färgade efter V-vinkeln. Ett snitt räknas som runa om det ligger inne i slingan och går tvärs eller snett över den, alltså som en runas stav. Spår som löper längs slingan är slingans egna kanter och mäts inte. Allt utanför slingan räknas som ornamentik. På M 15 sorterades {OUT_BANDS} snitt bort för att de låg utanför slingorna och {BAND_EDGE} för att de var slingkant; under tabellen kan du fälla ut alla skäl.

Titta efter två saker. Ligger en runa utanför det blå har slingan blivit för smal där. Ligger ornamentik inne i det blå har den blivit för bred. Då kan du vrida stenen rakare och köra igen, märka punkterna med en ruta som *Ornamentik* eller *Utesluten*, eller mäta just de runorna för hand.

{bild("03_granskning.png", "Granskningsbilden för M 15 med runslingan som ljusblått fält", f"Granskningsbilden för M 15. Det blå fältet följer ormen med texten; korset och ormens huvud ligger utanför och mäts inte. Analysen godkände {ACC} av {sv_int(CAND)} snitt, i {RUNES_MEASURED} runor.")}

Vill du se slingorna på hela stenen på en gång, öppna **Runor och ornamentik – se textslingorna** under *Bilder ur skanningen*. Bilden visar det som ligger djupare än en gemensam nivå för hela stenen: rostrött inne i slingorna, grått utanför. Den räknas som standard från samma vy varje gång – för de öppna skanningarna samma vy som slingorna ritades i – och inte från där kameran råkar stå, så att två bilder av samma skanning går att jämföra. Kryssrutan *Samma vy varje gång* styr det. Analysen i steg 1–4 utgår däremot alltid från din vy i 3D-fönstret. På M 15 låg {IN_BANDS} % av det som visades inne i slingorna, som täcker {BAND_SHARE} % av ytan. Det djupa ligger alltså oftare i texten än slingornas andel av ytan skulle ge.

{bild("08_runor_ornamentik.png", "Bilden Runor och ornamentik för M 15, med texten roströd och ornamentiken grå", f"Runor och ornamentik för M 15: rostrött i textslingorna, grått utanför, slingornas kant svart. {IN_BANDS} % av det visade ligger i slingorna, som täcker {BAND_SHARE} % av ytan.")}

## Steg 5. Räkna med runan som enhet

Snitten tas med jämna mellanrum, var tredje millimeter, så en lång runa med flera stavar får många snitt och en liten runa få. Räknar man stenens medelvärde över snitten väger de stora runorna tyngst, och osäkerheten ser mindre ut än den är, eftersom snitten i samma runa inte är oberoende av varandra. De delar samma slag, samma verktyg och samma vittring. Det ärliga är att låta runan vara enheten: först varje runas medelvärde, sedan medelvärdet av runorna.

Då måste Vitki veta var den ena runan slutar och nästa börjar. Det gör analysen nu själv. Inne i slingan får varje streck sin plats längs slingan, och streck som står tätt förs till samma runa, så länge runan inte blir bredare än slingan är hög. På M 15 blev det {AUTO_RUNES} runor med mätta snitt. Rundata läser {N_RUNOR} runor och {N_DIV} skiljetecken i texten.

Klicka på **Använd runorna som resultat**. Rutorna överst visar stenens mått räknade över snitten. Under dem kommer rutan **Med runan som enhet**: samma mått, räknade på runornas medelvärden.

{bild("06_runan_auto.png", "Rutan Med runan som enhet med analysens egen runindelning", f"Med runan som enhet, med analysens egen indelning i {AUTO_RUNES} runor: 95 %-intervall och ICC för varje mått.")}

På M 15 är V-vinkeln – vinkeln i spårets botten – {svn(S_ANG["mean"])}° räknad över {ACC} snitt och {svn(RA_ANG["mean"])}° räknad över {AUTO_RUNES} runor. Medelvärdet flyttar sig lite. Det som ändras mest är osäkerheten. Över snitten ser vinkeln ut att vara känd på ±{svn(S_HALF)}°. Över runorna är intervallet ±{svn(RA_HALF)}°. Det bredare intervallet är det ärliga: det räknar med att varje runa är ett eget stycke huggning, inte {PER_RUNE} oberoende mätningar.

ICC, {svn(ICC_A, 2)} för V-vinkeln, säger hur stor del av spridningen som ligger mellan runorna snarare än inom dem. Ett värde nära noll betyder att runorna är huggna ungefär lika och att skillnaderna mest finns inom varje runa. Ett värde nära ett betyder att runorna skiljer sig åt sinsemellan, och då är det särskilt viktigt att räkna med runan som enhet.

Indelningen är ett förslag, inte en läsning. Den kan dela en runa i två eller slå ihop två grannar. På {KA_N} skanningar från Södermanland räknade den i mitten {KA_OVER} % för många runor, och på {KA_WITHIN} av de {KA_N} låg antalet inom en fjärdedel av textens. M 15 är ett av de svårare fallen: {AUTO_RUNES} runor mot textens {N_RUNOR}. Därför finns nästa steg. Riktvärdena är {MIN_DESCRIBE} mätta runor för att beskriva en sten och {MIN_COMPARE} för att jämföra den med andra. De är tumregler, inte garantier.

## Steg 6. Markera runorna när indelningen ska vara exakt

Vill du bestämma själv var runorna går klickar du på **Markera runorna** i granskningen och klickar sedan en gång mitt på varje runa, i läsordning. Du behöver inte veta vilken runa det är. Varje runsnitt hör sedan till den närmaste markeringen och ersätter analysens egen indelning. Snitt långt från alla markeringar, till exempel i en runa du hoppat över, hör inte till någon och visas bleka. **Ångra senaste** tar bort den sista markeringen.

{bild("04_markerade.png", "Granskningsbilden med numrerade markeringar på runorna", f"M 15 med {MARKS} markeringar längs slingan, i läsordning.")}

{bild("05_markera_ruta.png", "Rutan Markera runorna med antal markerade runor", "Rutan säger hur många runor du markerat och hur många av runsnitten som fått en runa.", scan=False)}

Klicka på **Klar med runorna** och sedan på **Använd runorna som resultat** igen. Med markeringarna blev V-vinkeln {svn(RM_ANG["mean"])}° ±{svn(RM_HALF)}° över {MARKED} runor, med ICC {svn(ICC_M, 2)}.

{bild("07_runan_som_enhet.png", "Rutan Med runan som enhet räknad på de markerade runorna", f"Med runan som enhet, räknad på {MARKED} markerade runor.")}

En ärlig anmärkning om bilderna: markeringarna i dem satte vi med ett skript som följer slingans mittlinje och sätter en markering där det finns mätta spår. Det blev {MARKS}, inte stenens {N_RUNOR} runor, eftersom skriptet sätter en markering för varje samling mätta spår längs slingan: ett skiljetecken eller en runa i två delar kan få en egen, och två tätt ställda runor kan få en gemensam. Gör du det själv klickar du bara på runorna.

Känner Vitki igen stenens signum i Rundata finns också knappen **Runa för runa**. Då visas translittereringen som en remsa, och varje klick kopplas till nästa runa i texten. Skiljetecken hoppas över av sig själva, en runa som inte syns kan hoppas över, och en bindruna kan få ett klick för två runor. Kopplingarna kan sparas som facit för runigenkänningen och exporteras som en utgåva i TEI/EpiDoc med en 3D-punkt per runa.

## Vad verktyget inte gör

Vitki läser inte runorna. Analysens indelning och dina markeringar säger var en runa är, inte vilken; det är bara med Runa för runa som du själv kopplar klicken till texten. Slingorna från bildmodellen är förslag: på stenar som ingen har ritat slingorna på kan modellen hitta bara delar av slingan, och därför finns granskningsbilden och bilden Runor och ornamentik. Och måtten beskriver hur spåren är huggna, inte vem som högg dem. Bergarten och vittringen formar också spåren, så måtten ensamma säger inte vem som ristade.

:::box Det viktigaste i korthet
- Runor och ornamentik huggs ofta olika. Vitki skiljer dem efter var texten står, inte efter hur strecken ser ut, och du ser själv i bilden var gränsen gick.
- Vänd den ristade sidan mot dig innan du mäter. Bakifrån mäter Vitki ingenting och säger till; rakt framifrån godkändes {ACC} snitt på M 15.
- Runan, inte snittet, är den ärliga enheten. Vitki delar nu själv in runorna längs slingan; vill du ha indelningen exakt markerar du dem med ett klick var.
- Allt detta beskriver huggningen. Vem som högg är en annan fråga.
:::

## Om skanningen

M 15 vid Sköns kyrka i Sundsvalls kommun, Medelpad, är en runsten i stilgrupp Pr2 från vikingatiden. Rundata läser texten *{TRANSLIT}*, »Björn reste denna sten efter Ofrid och efter Un, sina söner«. Stenen skannades av Henrik Zedig vid Länsstyrelsen Västra Götalands län med en handhållen laserskanner (Creaform HandySCAN BLACK Elite, upplösning 0,40 mm) inom forskningsprojektet *Evighetsrunor: en forskningsplattform för Sveriges runinskrifter* och som förberedelse för en korpusutgåva av Medelpads runinskrifter. Skanningen publicerades öppet på Zenodo den 13 november 2024 i datamängden *3D-data Runstenar i Medelpad* av Laila Kitzler Åhfeldt (Riksantikvarieämbetet) och Henrik Zedig, under licensen [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.sv). Vi har använt filen som den är publicerad; alla bilder och mått i artikeln är beräknade i Vitki ({METHOD_VERSION}) ur den. Tack till Henrik Zedig och Laila Kitzler Åhfeldt för att skanningarna är fritt tillgängliga.

## Källor

- Kitzler Åhfeldt, L. & Zedig, H. 2024. *3D-data Runstenar i Medelpad* [Dataset]. Riksantikvarieämbetet. [https://doi.org/10.5281/zenodo.14141222](https://doi.org/10.5281/zenodo.14141222)
- Samnordisk runtextdatabas (Rundata), M 15.
- Vitkis metoddokumentation, avsnitt 2c (*Runslingorna* och *Runor markerade för hand*), 2d (*Runor och ornamentik*, *Samma vy varje gång*) och 3 (*Osäkerhet*)."""


title_en = "How to: measure the runes, not the serpent"
summary_en = ("A runestone is more than its text: the serpent, the edges of the band, the cross. This is how you get "
              "Vitki's groove analysis to measure only the runes – or only the ornament – and how you count with the "
              "rune as the unit, so that every rune weighs the same.")

body_en = f"""Anyone who measures the grooves on a runestone usually wants to know how the runes were cut. But the stone is full of other carving: the serpent's body, the edges of the band, the cross in the middle. Measure it all in one lump and the runes mix with the ornament, and the average no longer says anything definite about either.

So Vitki decides what a rune is by where the text stands, not by what the strokes look like. We tested the old way, which went by the strokes – short straight grooves became runes, long even grooves ornament – against bands drawn by hand on {OLD_FILES} scans. It was wrong in both directions. Of what the old classification called runes, {OLD_OUT} % lay entirely outside the text bands, and of what it called ornament, {OLD_ORN} % were runes. This guide shows how the analysis works today, step by step, on a real stone.

## The stone in the example

We use M 15 at Skön church in Medelpad. Bjôrn raised the stone in memory of two sons, Ófriðr and Unn, and let the text run in a serpent coiled around a cross. Henrik Zedig scanned it, and the scan is openly available on Zenodo. More about the scan at the end.

## Step 1. Turn the carved side towards you

The analysis measures what faces you on the screen. Seen at an angle, the grooves are cut obliquely, and many cross-sections are rejected as too shallow or too unclear. That is why there is a button, **Turn the carved side towards me**, at the bottom left of the 3D view. It turns the view so that you look straight at the stone's broadest side. If it is the wrong side, press it once more.

It matters. Once M 15 has loaded, the page's starting view looks at the scan from behind and {TILT_DEG}° off. The scan is only the stone's surface, a thin shell, so from behind little more than its edges shows. The drawn bands belong to the carved side, so if you run the analysis from there nothing is measured: all {en_int(CAND0)} cross-sections are rejected as *stone seen from behind*, and the line under the button tells you after a **Note** what to do. After one press of the button, {ACC} cross-sections were accepted.

{bild("01a_startvy.png", "M 15 in the starting view, seen from behind so that only the edges show", f"M 15 in the page's starting view: the scan seen from behind and {TILT_DEG}° off.", en=True)}

{bild("01c_bakifran_obs.png", "The warning under the button Run automatic analysis when the stone is seen from behind", "From behind the analysis measures nothing and says why.", en=True, scan=False)}

{bild("01b_vy.png", "M 15 in the 3D view with the button Turn the carved side towards me", f"The same scan after one press of the button: the view looks straight at the carved side, and the analysis accepted {ACC} cross-sections.", en=True)}

## Step 2. Choose what to measure

Choose **Automatic** as the measuring mode. At the top of the panel Vitki asks **What should be measured?** The default is **Runes**. If you choose **Ornament**, the grooves outside the text bands are measured instead. Below the choice, a few short points explain how Vitki decides which is which. If the stone has staveless runes (Hälsinge runes), tick **Staveless runes**; Vitki does so itself when Rundata says the stone has only such runes. Leave the **Vitki protocol** ticked, so that the stone can be compared with others measured the same way. Then click **Run automatic analysis**.

{bild("01_vad_ska_matas.png", "The automatic analysis panel with the choice Runes or Ornament", "The choice between runes and ornament, the explanation below it and the Vitki protocol.", en=True, scan=False)}

## Step 3. Read the line about the runic bands

When the analysis is done, a line appears under the button: where the runic bands came from, how much of the surface they cover and what was measured. The runic bands are the ribbons the text stands in. Vitki finds them in two ways. For the open scans there are bands we have drawn and checked by hand, {N_BANDS} stones so far, and Vitki recognises the file by its fingerprint. For other scans, a small image model trained on the hand-drawn bands proposes where they run. It is a proposal, and the line says so: *check them in the review image*.

If there are drawn bands for the file but Vitki cannot use them – for example because you are looking at the stone from a very different direction from the one they were drawn in – the same line says so after a **Note**, and the analysis uses the model's bands instead.

{bild("02_status_slingor.png", "The line about the runic bands under the button Run automatic analysis", f"On M 15 the bands came from the hand-drawn ones, and they cover {COVER} % of the surface.", en=True)}

## Step 4. Check the bands in the image

Below the 3D view comes the review image. The bands appear as a light-blue field, the measured cross-sections as dots coloured by their V-angle. A cross-section counts as a rune if it lies inside the band and runs across or diagonally over it, the way a rune's staff does. Grooves running along the band are the band's own edges and are not measured. Everything outside the band counts as ornament. On M 15, {OUT_BANDS} cross-sections were rejected for lying outside the bands and {BAND_EDGE} for being band edge; below the table you can fold out every reason.

Look for two things. If a rune lies outside the blue, the band has become too narrow there. If ornament lies inside the blue, it has become too wide. You can then turn the stone straighter and run again, label the dots with a box as *Ornament* or *Excluded*, or measure those runes by hand.

{bild("03_granskning.png", "The review image for M 15 with the runic band as a light-blue field", f"The review image for M 15. The blue field follows the serpent with the text; the cross and the serpent's head lie outside and are not measured. The analysis accepted {ACC} of {en_int(CAND)} cross-sections, in {RUNES_MEASURED} runes.", en=True)}

To see the bands on the whole stone at once, open **Runes and ornament – see the text bands** under *Images from the scan*. The picture shows what lies deeper than one common level for the whole stone: rust inside the bands, grey outside. By default it is computed from the same view every time – for the open scans the view the bands were drawn in – and not from wherever the camera happens to be, so that two pictures of the same scan can be compared. The *Same view every time* box controls this. The analysis in steps 1–4, on the other hand, always starts from your view in the 3D window. On M 15, {IN_BANDS} % of what was shown lay inside the bands, which cover {BAND_SHARE} % of the surface. So the deep grooves lie in the text more often than the bands' share of the surface would give.

{bild("08_runor_ornamentik.png", "The picture Runes and ornament for M 15, with the text in rust and the ornament grey", f"Runes and ornament for M 15: rust in the text bands, grey outside, the bands' edge black. {IN_BANDS} % of what is shown lies in the bands, which cover {BAND_SHARE} % of the surface.", en=True)}

## Step 5. Count with the rune as the unit

Cross-sections are taken at even intervals, every third millimetre, so a long rune with several staves gets many and a small rune few. Average the stone over the cross-sections and the large runes weigh the most, and the uncertainty looks smaller than it is, because cross-sections in the same rune are not independent of each other. They share the same blows, the same tool and the same weathering. The honest way is to let the rune be the unit: first each rune's mean, then the mean of the runes.

Vitki then has to know where one rune ends and the next begins. The analysis now works this out itself. Inside the band each stroke gets its place along the band, and strokes that stand close together go to the same rune, as long as the rune does not become wider than the band is high. On M 15 this gave {AUTO_RUNES} runes with measured cross-sections. Rundata reads {N_RUNOR} runes and {N_DIV} word dividers in the text.

Click **Use the runes as the result**. The boxes at the top show the stone's measurements computed over the cross-sections. Below them comes the box **With the rune as the unit**: the same measurements, computed on the runes' means.

{bild("06_runan_auto.png", "The box With the rune as the unit with the analysis's own division into runes", f"With the rune as the unit, with the analysis's own division into {AUTO_RUNES} runes: a 95 % interval and ICC for each measurement.", en=True)}

On M 15 the V-angle – the angle at the bottom of the groove – is {eng(S_ANG["mean"])}° computed over {ACC} cross-sections and {eng(RA_ANG["mean"])}° computed over {AUTO_RUNES} runes. The mean moves a little. What changes most is the uncertainty. Over the cross-sections, the angle seems known to ±{eng(S_HALF)}°. Over the runes, the interval is ±{eng(RA_HALF)}°. The wider interval is the honest one: it counts each rune as one piece of carving, not as {PER_RUNE} independent measurements.

ICC, {eng(ICC_A, 2)} for the V-angle, tells how much of the spread lies between the runes rather than within them. A value near zero means the runes were cut much alike and the differences lie mostly within each rune. A value near one means the runes differ from each other, and then it matters most to count with the rune as the unit.

The division is a proposal, not a reading. It can split a rune in two or join two neighbours. On {KA_N} scans from Södermanland it counted, at the median, {KA_OVER} % too many runes, and on {KA_WITHIN} of the {KA_N} the count lay within a quarter of the text's. M 15 is one of the harder cases: {AUTO_RUNES} runes against the text's {N_RUNOR}. That is what the next step is for. The guidelines are {MIN_DESCRIBE} measured runes to describe a stone and {MIN_COMPARE} to compare it with others. They are rules of thumb, not guarantees.

## Step 6. Mark the runes when the division must be exact

If you want to decide yourself where the runes are, click **Mark the runes** in the review and then click once in the middle of each rune, in reading order. You do not need to know which rune it is. Every rune cross-section then belongs to the nearest mark, replacing the analysis's own division. Cross-sections far from every mark, for example in a rune you skipped, belong to none and are shown faded. **Undo the last one** removes the last mark.

{bild("04_markerade.png", "The review image with numbered marks on the runes", f"M 15 with {MARKS} marks along the band, in reading order.", en=True)}

{bild("05_markera_ruta.png", "The Mark the runes box with the number of marked runes", "The box tells you how many runes you have marked and how many of the rune cross-sections have been given a rune.", en=True, scan=False)}

Click **Done with the runes** and then **Use the runes as the result** again. With the marks, the V-angle was {eng(RM_ANG["mean"])}° ±{eng(RM_HALF)}° over {MARKED} runes, with an ICC of {eng(ICC_M, 2)}.

{bild("07_runan_som_enhet.png", "The box With the rune as the unit computed on the marked runes", f"With the rune as the unit, computed on {MARKED} marked runes.", en=True)}

An honest note about the pictures: we placed the marks in them with a script that follows the band's centre line and puts a mark wherever there are measured grooves. That gave {MARKS}, not the stone's {N_RUNOR} runes, because the script puts one mark on each cluster of measured grooves along the band: a word divider or a rune in two parts can get one of its own, and two runes set close together can share one. When you do it yourself, you click only on the runes.

If Vitki recognises the stone's signum in Rundata, there is also a button **Rune by rune**. The transliteration is then shown as a strip, and each click is tied to the next rune of the text. Word dividers are skipped by themselves, a rune that cannot be seen can be skipped, and a bind rune can take one click for two runes. The links can be saved as a reference for the rune recognition and exported as a TEI/EpiDoc edition with one 3D point per rune.

## What the tool does not do

Vitki does not read the runes. The analysis's division and your marks say where a rune is, not which one; only with Rune by rune do you tie the clicks to the text yourself. Bands from the image model are proposals: on stones whose bands nobody has drawn, the model may find only parts of the band, which is why the review image and the Runes and ornament picture are there. And the measurements describe how the grooves were cut, not who cut them. The stone and its weathering shape the grooves too, so the measurements alone do not say who carved.

:::box The essentials in brief
- Runes and ornament are often cut differently. Vitki tells them apart by where the text stands, not by what the strokes look like, and you can see for yourself in the image where the line was drawn.
- Turn the carved side towards you before you measure. From behind Vitki measures nothing and tells you so; straight on, {ACC} cross-sections were accepted on M 15.
- The rune, not the cross-section, is the honest unit. Vitki now divides the runes along the band itself; if you want the division exact, mark them with one click each.
- All of this describes the carving. Who carved is another question.
:::

## About the scan

M 15 at Skön church in Sundsvall municipality, Medelpad, is a Viking-age runestone in style group Pr2. Rundata reads the text *{TRANSLIT}*, "Bjôrn erected this stone in memory of Ófriðr and in memory of Unn, his sons". The stone was scanned by Henrik Zedig of Länsstyrelsen Västra Götalands län with a handheld laser scanner (Creaform HandySCAN BLACK Elite, resolution 0.40 mm) within the research project *Evighetsrunor: en forskningsplattform för Sveriges runinskrifter* (Everlasting Runes: a research platform for Sweden's runic inscriptions) and in preparation for a corpus edition of the runic inscriptions of Medelpad. The scan was published openly on Zenodo on 13 November 2024 in the dataset *3D-data Runstenar i Medelpad* by Laila Kitzler Åhfeldt (Swedish National Heritage Board) and Henrik Zedig, under the licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). We used the file as published; every image and measurement in this article was computed from it in Vitki ({METHOD_VERSION}). Our thanks to Henrik Zedig and Laila Kitzler Åhfeldt for making the scans freely available.

## Sources

- Kitzler Åhfeldt, L. & Zedig, H. 2024. *3D-data Runstenar i Medelpad* [Dataset]. Riksantikvarieämbetet. [https://doi.org/10.5281/zenodo.14141222](https://doi.org/10.5281/zenodo.14141222)
- Scandinavian Runic-text Database (Rundata), M 15.
- Vitki's method documentation, sections 2c (*Runslingorna* and *Runor markerade för hand*), 2d (*Runor och ornamentik*, *Samma vy varje gång*) and 3 (*Osäkerhet*)."""

labels = ["Så gör du", "Huggspår och 3D"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
for b in (body, body_en, summary, summary_en):
    assert not re.search(r"^\|", b, re.M)  # BlogBody has no tables
    assert not re.search(r"\{[A-Z_]+\}", b), re.findall(r"\{[A-Z_]+\}", b)  # no unfilled placeholders
    assert not re.search(r"\bAI\b", b)
    assert not re.search(r"\b(hans|hon|honom|hennes|his|her|him)\b", b.split("## Om skanningen")[0].split("## About the scan")[0])
for b in (body, body_en):
    assert b.count(":::box") == 1 and b.count("\n:::\n") == 1 and "Kitzler Åhfeldt" in b and "Zedig" in b
    assert b.count("/api/blog/figures/") == 11, b.count("/api/blog/figures/")
out = {"slug": "sa-gor-du-mat-runorna-inte-ormen", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en, "labels": labels}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "howto_runor.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "howto_runor.json"), len(body.split()), "ord,", len(body_en.split()), "words")
print(f"startvy bakifrån {TILT_DEG}°, 0 av {CAND0} snitt → {ACC} av {CAND}; runor {RUNES_MEASURED}/{RUNES_FOUND}, auto {AUTO_RUNES}, "
      f"markerade {MARKED} ({MARKS} klick); slingor {COVER} %; Runor och ornamentik {IN_BANDS} % i {BAND_SHARE} %")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        assert old.get("slug") == out["slug"], old.get("slug")
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Så gör du|huggspår", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
