"""Metodartikeln om appfunktionen *Skala av vittringen* (src/peel.py, METHODS.md 2d2): hur bilden räknas, hur man använder
den och vad det låsta provet mot Viktors granskade textslingor visade (analysplaner/2026-11-07-skala-av-provet.md,
utdata/skala_av/provet.json). Alla tal ur provet.json och låses här. Bilder ur utdata/skala_av/ (prova.py, provet_figur.py,
dialog/ från dialog_bilder.py), frysta i bloggens bildarkiv (src/blog_figures.freeze).
    .venv/bin/python utdata/blogg/build/build_skala_av.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import os
import re
import statistics as st
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels, peel, scan_sources  # noqa: E402

SA = os.path.join(ROOT, "utdata", "skala_av")
R = json.load(open(os.path.join(SA, "provet.json"), encoding="utf-8"))
assert R["plan_sha"] == "380fccf4" and R["files_measured"] == R["files_planned"] == 95 and not R["missing"] and not R["skipped"]
FILES = R["per_file"]
N = len(FILES)
OBJ = len({r["signum"] or r["stem"] for r in FILES})
assert (N, OBJ) == (95, 89)
P1, P2, EX = R["P1"], R["P2"], R["extra_C_vs_A_same_share"]
assert not P1["holds"] and P1["p"] > 0.99 and P1["median_diff"] < 0
B_BETTER = sum(r["lift_B"] > r["lift_A"] for r in FILES)
B_WORSE = sum(r["lift_B"] < r["lift_A"] for r in FILES)
C_BETTER = sum(r["lift_C"] > r["lift_A"] for r in FILES)
C_SAME_BETTER = sum(r["lift_C"] > r["lift_A_at_C"] for r in FILES)
assert (B_BETTER, B_WORSE, C_BETTER, C_SAME_BETTER) == (15, 80, 59, 38), (B_BETTER, B_WORSE, C_BETTER, C_SAME_BETTER)
BAND = st.median(r["band_share"] for r in FILES)
SHOWN_B = st.median(r["shown_B"] for r in FILES)
SHOWN_C = st.median(r["shown_C"] for r in FILES)
assert round(100 * BAND) == 25 and round(100 * SHOWN_B) == 28 and round(100 * SHOWN_C) == 24
P2_ONE_IN = round(1 / P2["p"], -2)
assert P2_ONE_IN == 300
SO128 = next(r for r in FILES if r["signum"] == "Sö 128")
assert round(100 * SO128["band_share"]) == 29
PREC128 = {k: SO128[f"lift_{k}"] * SO128["band_share"] for k in "ABC"}
assert [round(100 * PREC128[k]) for k in "ABC"] == [43, 39, 39]
SER = R["per_series"]
SER_EN = {"Södermanland": "Södermanland", "Västergötland": "Västergötland", "Medelpad": "Medelpad",
          "Hälsingland": "Hälsingland", "Gravmonument Ög/Sm": "Grave monuments Ög/Sm", "Åsmund": "Åsmund"}
assert [SER[k]["n"] for k in SER_EN] == [36, 18, 15, 12, 11, 3]
assert round(100 * SER["Södermanland"]["B_better"]) == 8 and round(100 * SER["Hälsingland"]["C_better_same_share"]) == 58
# the settings the text describes, as src/peel.py has them
assert (peel.BLOCK_MM, peel.LEVEL_Q, peel.EDGE_MM, peel.MAX_SLOPE_DEG) == (60.0, 70, 10.0, 60.0)
assert (peel.GROOVE_LENGTH_MM, peel.GROOVE_ELONGATION, peel.OFFSET_RANGE) == (12.0, 3.0, (-1.0, 3.0))
METHODS = open(os.path.join(ROOT, "METHODS.md"), encoding="utf-8").read()
assert "0,29 mm mot 0,08 mm" in METHODS and "går nivån från 0,6 till 1,2 mm" in METHODS

dec = lambda x, n=2, sv=True: (f"{x:.{n}f}".replace(".", ",") if sv else f"{x:.{n}f}")  # noqa: E731
pc = lambda x: round(100 * x)  # noqa: E731

DS = {d["key"]: d for d in scan_sources.DATASETS}
LIC_SV, LIC_EN = "https://creativecommons.org/licenses/by/4.0/deed.sv", "https://creativecommons.org/licenses/by/4.0/"
PROJ_EN = {"sodermanland": "the research project Runristandets dynamik (2009–2014)",
           "asmund": "the research project Runristandets dynamik (2009–2014)",
           "vastergotland": "the research project Runristandets dynamik (2009–2014)",
           "halsingland": "the project Runverket",
           "medelpad": "the research project Evighetsrunor: a research platform for Sweden's runic inscriptions",
           "gravmonument_og_sm": "Cecilia Ljung's doctoral project on early Christian grave monuments (scanned 2008)"}
NAME = {"sodermanland": ("Södermanland", "Södermanland"), "asmund": ("Stenar signerade av Åsmund Kåresson",
        "Stones signed by Åsmund Kåresson"), "vastergotland": ("Västergötland", "Västergötland"),
        "halsingland": ("Hälsingland", "Hälsingland"), "medelpad": ("Medelpad", "Medelpad"),
        "gravmonument_og_sm": ("Tidigkristna gravmonument i Östergötland och Småland",
                               "Early Christian grave monuments in Östergötland and Småland")}
assert DS["sodermanland"]["project"] == "forskningsprojektet Runristandets dynamik (2009–2014)"
assert DS["halsingland"]["scanner"] == DS["medelpad"]["scanner"] == "Henrik Zedig"


def credit(key: str, sv: bool) -> str:
    """The scan's credit under a picture: who scanned it, institution, project, licence and DOI."""
    d = DS[key]
    who = ", ".join(x for x in (d["scanner"], d["institution"]) if x)
    proj = d["project"] if sv else PROJ_EN[key]
    lic = f"[CC BY 4.0]({LIC_SV if sv else LIC_EN})"
    doi = f"[doi:{d['doi']}]({d['url']})"
    if d["creator"] != d["scanner"]:
        extra = f" (datamängd av {d['creator']})" if sv else f" (dataset by {d['creator'].replace(' och ', ' and ')})"
    else:
        extra = ""
    return (f"Skanning: {who}, {proj}{extra} · {lic} · {doi}." if sv else f"Scan: {who}, {proj}{extra} · {lic} · {doi}.")


def bild(path: str, alt: str, text: str, max_w: int = 1600) -> str:
    """The picture frozen in the blog's archive, as markdown with its caption."""
    assert os.path.exists(path), f"bild saknas: {path}"
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return f"![{alt}]({blog_figures.freeze(out.getvalue())})\n{text}"


def pic(name: str, sv: bool) -> str:
    base, ext = os.path.splitext(name)
    return os.path.join(SA, name if sv else base + "_en" + ext)


def chart(sv: bool) -> str:
    out = [":::chart " + ("Andel skanningar där avskalningen samlade mer i texten än dagens bild" if sv else
                          "Share of scans where peeling gathered more in the text than today's image")]
    out.append("# " + ("Avskalat, allt som är kvar (samma visade yta)" if sv else "Peeled, everything left (same area shown)"))
    for k, en in SER_EN.items():
        d = SER[k]
        note = f"{d['n']} skanningar" if sv else f"{d['n']} scans"
        out.append(f"{k if sv else en} | {pc(d['B_better'])} | {note}")
    out.append("# " + ("Bara spåren (samma visade yta)" if sv else "Grooves only (same area shown)"))
    for k, en in SER_EN.items():
        d = SER[k]
        note = f"{d['n']} skanningar" if sv else f"{d['n']} scans"
        out.append(f"{k if sv else en} | {pc(d['C_better_same_share'])} | {note}")
    out.append(("Källa: Vitkis prov mot Viktor Kvants granskade textslingor, analysplan låst 2026-11-07. Procent av "
                "skanningarna i varje serie; 50 procent vore lika ofta bättre som sämre. Diagram: Vitki, ur skanningarna nedan.")
               if sv else
               ("Source: Vitki's test against Viktor Kvant's checked text bands, analysis plan locked 7 November 2026. Percent "
                "of the scans in each series; 50 percent would be better as often as worse. Chart: Vitki, from the scans below."))
    return "\n".join(out) + "\n:::"


SKS = "Bild: Vitki, ur skanningen."
SKE = "Image: Vitki, from the scan."
IMG_GS11 = {sv: bild(pic("Gs_11_1_4_thin05.png", sv),
                     "Gs 11: dagens djupbild och den avskalade bilden" if sv else "Gs 11: today's depth image and the peeled image",
                     ("Gs 11, en av Åsmund Kåressons signerade stenar. Överst dagens djupbild i Vitki, under den avskalade bilden vid "
                      "reglaget 0 mm: långa spår roströda, korta fläckar och gropar grå. " + credit("asmund", True) + " " + SKS)
                     if sv else
                     ("Gs 11, one of Åsmund Kåresson's signed stones. Top: today's depth image in Vitki; below: the peeled image at "
                      "slider 0 mm – long grooves in rust, short specks and pits in grey. " + credit("asmund", False) + " " + SKE))
            for sv in (True, False)}
IMG_DIALOG = {sv: bild(os.path.join(SA, "dialog", "so128_efter.png"),
                       "Dialogen Skala av vittringen med Sö 128" if sv else "The Peel away the weathering dialog with Sö 128",
                       ("Dialogen *Skala av vittringen* med Sö 128 vid Lids kyrka. Ramslingan till vänster räknades som en enda "
                        "stor grop och var grå; ett klick i läget *Klick gör till spår* gjorde den till spår för hand, i mörkare "
                        "rostrött. " + credit("sodermanland", True) + " Skärmbild: Vitki.")
                       if sv else
                       ("The *Peel away the weathering* dialog with Sö 128 at Lid church (the app's interface in Swedish). The "
                        "frame band on the left counted as one large pit and was grey; one click in the mode *Click makes a "
                        "groove* made it a groove by hand, in darker rust. " + credit("sodermanland", False) + " Screenshot: Vitki."))
              for sv in (True, False)}
IMG_TEST = {sv: bild(pic("provet_figur_So_128_1_4_thin_closed_holes.png", sv),
                     "Vad provet räknar, på Sö 128" if sv else "What the test counts, on Sö 128",
                     ("Vad provet räknar, på Sö 128. Rostrött är det bilden visar inne i textslingorna, grått det den visar "
                      "utanför dem – ornament, sprickor, gropar – och den svarta linjen är slingornas kant. A: dagens djupbild "
                      "avskuren med en gemensam gräns. B: avskalat, allt som är kvar. C: avskalat, bara spåren. Slingor: Viktor "
                      "Kvant. " + credit("sodermanland", True) + " " + SKS)
                     if sv else
                     ("What the test counts, on Sö 128. Rust is what the picture shows inside the text bands, grey what it shows "
                      "outside them – ornament, cracks, pits – and the black line is the edge of the bands. A: today's depth "
                      "image cut at one common threshold. B: peeled, everything left. C: peeled, grooves only. Text bands: "
                      "Viktor Kvant. " + credit("sodermanland", False) + " " + SKE))
            for sv in (True, False)}
IMG_HS14 = {sv: bild(pic("HS_14_1mm_complete_thin03.png", sv),
                     "Hs 14: dagens djupbild och den avskalade bilden" if sv else "Hs 14: today's depth image and the peeled image",
                     ("Hs 14, där avskalningen inte räcker. I dagens djupbild (överst) syns runornas tunna linjer; i den "
                      "avskalade blir mycket av texten grått och sprickorna roströda, eftersom den grovkorniga stenens korn är "
                      "lika djupa som strecken. " + credit("halsingland", True) + " " + SKS)
                     if sv else
                     ("Hs 14, where peeling is not enough. Today's depth image (top) shows the thin lines of the runes; in the "
                      "peeled image much of the text turns grey and the cracks rust, because the coarse stone's grains are as "
                      "deep as the strokes. " + credit("halsingland", False) + " " + SKE))
            for sv in (True, False)}

GH = "https://github.com/Precatio/runes/blob/main"


def scans_section(sv: bool) -> str:
    lines = []
    for key in ("sodermanland", "asmund", "vastergotland", "medelpad", "halsingland", "gravmonument_og_sm"):
        d = DS[key]
        who = d["scanner"] + (f" ({d['institution']})" if d["institution"] else "")
        dev = d["device"]
        if sv:
            # the article has no reference list entry for Ljung 2016, so the dataset's own pointer to it is left out here
            proj = {"Runverket": "projektet Runverket"}.get(d["project"], d["project"]).replace("; Ljung 2016", "")
            lines.append(f"- **{NAME[key][0]}:** skannade av {who} inom {proj}" + (f", med {dev}" if dev else "")
                         + f". Publicerade av {d['creator']} på Zenodo med licensen [CC BY 4.0]({LIC_SV}), "
                         f"[doi:{d['doi']}]({d['url']}).")
        else:
            dev_en = {"ATOS I (GOM), strukturerat ljus": "ATOS I (GOM), structured light",
                      "HandySCAN BLACK Elite (Creaform), handhållen laserskanner": "HandySCAN BLACK Elite (Creaform), handheld laser scanner",
                      "HandySCAN BLACK Elite (Creaform), handhållen laserskanner, upplösning 0,40 mm":
                          "HandySCAN BLACK Elite (Creaform), handheld laser scanner, resolution 0.40 mm",
                      "ATOS II (GOM), strukturerat ljus, punktavstånd 0,27 mm": "ATOS II (GOM), structured light, point spacing 0.27 mm",
                      "": ""}[dev]
            lines.append(f"- **{NAME[key][1]}:** scanned by {who} in {PROJ_EN[key]}" + (f", with {dev_en}" if dev_en else "")
                         + f". Published by {d['creator'].replace(' och ', ' and ')} on Zenodo under the licence "
                         f"[CC BY 4.0]({LIC_EN}), [doi:{d['doi']}]({d['url']}).")
    return "\n".join(lines)


def sources(sv: bool) -> str:
    keys = ("sodermanland", "asmund", "vastergotland", "medelpad", "halsingland", "gravmonument_og_sm")
    out = []
    for k in keys:
        url = DS[k]["url"]
        assert DS[k]["citation"].endswith(url)
        out.append("- " + DS[k]["citation"].replace(url, f"[{url}]({url})"))
    if sv:
        out += [f"- Vitki 2026. Metodbeskrivning, avsnitt 2d2: Skala av vittringen. [METHODS.md]({GH}/METHODS.md)",
                f"- Vitki 2026. Analysplan: skiljer Skala av vittringen huggning från vittring bättre än dagens djupbild? Låst "
                f"2026-11-07. [analysplaner/2026-11-07-skala-av-provet.md]({GH}/analysplaner/2026-11-07-skala-av-provet.md)",
                f"- Vitki 2026. Provets resultat per serie och per skanning. [utdata/skala_av/provet.md]({GH}/utdata/skala_av/provet.md)",
                f"- Vitki 2026. Analysplan: referensytan i huggspårsanalysen – fyrkantig stängning eller rullande paraboloid. "
                f"Låst 2026-11-07. [analysplaner/2026-11-07-referensyta-paraboloid.md]({GH}/analysplaner/2026-11-07-referensyta-paraboloid.md)"]
    else:
        out += [f"- Vitki 2026. Method description, section 2d2: Skala av vittringen (in Swedish). [METHODS.md]({GH}/METHODS.md)",
                f"- Vitki 2026. Analysis plan: does Skala av vittringen separate carving from weathering better than today's depth "
                f"image? Locked 7 November 2026 (in Swedish). [analysplaner/2026-11-07-skala-av-provet.md]({GH}/analysplaner/2026-11-07-skala-av-provet.md)",
                f"- Vitki 2026. The test's results by series and by scan (in Swedish). [utdata/skala_av/provet.md]({GH}/utdata/skala_av/provet.md)",
                f"- Vitki 2026. Analysis plan: the reference surface of the groove analysis – square closing or rolling paraboloid. "
                f"Locked 7 November 2026 (in Swedish). [analysplaner/2026-11-07-referensyta-paraboloid.md]({GH}/analysplaner/2026-11-07-referensyta-paraboloid.md)"]
    return "\n".join(out)


SLUG = "kan-man-skala-av-vittringen-fran-en-runsten"
title = "Kan man skala av tusen års vittring från en runsten?"
title_en = "Can you peel a thousand years of weathering off a runestone?"
summary = ("Vitkis nya bild *Skala av vittringen* visar bara det som ligger djupare än vittringen runt omkring, färgar de långa "
           "spåren röda och låter läsaren klicka bort gropar och lägga till missade spår. Så fungerar den, så använder du den – "
           f"och det här visade ett låst prov mot {N} skanningar om var bildens styrka ligger.")
summary_en = ("Vitki's new picture *Peel away the weathering* shows only what lies deeper than the weathering around it, colours "
              "the long grooves red and lets the reader click away pits and add missed grooves. How it works, how to use it – "
              f"and what a locked test on {N} scans showed about where the picture's strength lies.")

body = f"""Den som har stått framför en runsten i snett eftermiddagsljus vet hur runorna kommer och går. En bistav syns tydligt en minut och är borta när solen har flyttat sig. En 3D-skanning har inte det problemet. Den har mätt stenens yta punkt för punkt, på bråkdelar av en millimeter, och mätningen ändras inte med ljuset. Men skanningen har ett annat problem: vittringen har också djup. Gropar där korn har lossnat, sprickor och tusen år av frost ligger i samma mätning som ristarens mejselspår, och på en djupbild ser de ofta likadana ut.

Idén bakom den nya funktionen var enkel: om man kunde skala av den vittrade ytan borde de djupa spåren bli kvar. Vitki har nu en sådan bild, *Skala av vittringen*, på 3D-sidan. Här beskriver vi hur den räknas, hur man använder den och vad ett låst prov mot {N} skanningar visade om vad den är bra till.

{IMG_GS11[True]}

## Tre saker bilden gör annorlunda

**Ytan följer stenens välvning.** Djupet räknas mot en tänkt yta utan ristningar. Tänk dig ett styvt täcke som läggs över stenen: det följer stenens rundning men räcker inte ned i fåror smalare än två centimeter. Avståndet från täcket ned till stenen är djupet. Tekniskt är det en morfologisk stängning med ett fönster om 20 millimeter – samma yta som Vitkis huggspårsmätning använder.

**Djupet mäts vinkelrätt mot ytan.** På en sluttning räknas djupet rakt in i stenen, inte rakt bakåt sett från betraktaren. Där ytan lutar 30 grader är skillnaden 13 procent, vid 45 grader 29 procent. Stenens sidor, brantare än {peel.MAX_SLOPE_DEG:.0f} grader, och en kantzon på en centimeter lämnas utanför.

**Gränsen följer vittringen där den står.** Stenen delas i rutor om sex centimeter. I varje ruta är vittringens nivå det djup som {peel.LEVEL_Q} procent av rutan är grundare än, och nivåerna jämnas ut mellan rutorna. Det som ligger djupare än nivån visas, resten skalas av. Ett reglage flyttar gränsen från en millimeter grundare till tre millimeter djupare. På Sö 206 går nivån från 0,6 till 1,2 millimeter, så en gemensam gräns för hela stenen skulle skala av för mycket på ett ställe och för lite på ett annat. Det var tanken. Provet längre ned visar att den inte höll.

Det som blir kvar delas i fläckar. En fläck vars djupaste del är minst {peel.GROOVE_LENGTH_MM:.0f} millimeter lång – lika lång som den kortaste runa huggspårsanalysen räknar med – och minst tre gånger så lång som bred färgas rostrött och kallas **spår**. Resten är **gropar** och blir grå. Regeln vet inte vad en runa är. Ornament och sprickor är också långa och smala, och en ramslinga som vittringen har gjort till ett nät av gropar blir grå.

## Läsaren bestämmer

Därför är bilden byggd för att läsaren ska sortera. Ett klick på en fläck tar bort den. I det andra klickläget, *Klick gör till spår*, blir en grå fläck ett spår, i mörkare rostrött så att det syns vad som är gjort för hand. Ett nytt klick ångrar, och Skift-klick ger det andra läget utan att man byter. Klicken sparas i webbläsaren som punkter på 3D-modellen. De följer med när man flyttar reglaget och finns kvar nästa gång samma skanning öppnas i samma webbläsare.

{IMG_DIALOG[True]}

## Hjälper den att se texten?

Med ögat såg bilden lovande ut. På Gs 11 blev runorna nästan som en ritning. Men ögat är lätt att övertyga, så vi bestämde i förväg hur vi skulle mäta och låste planen innan något räknades.

Facit är de textslingor Viktor har ritat in och granskat på {N} skanningsfiler av {OBJ} stenar och gravmonument: {SER['Södermanland']['n']} från Södermanland, {SER['Västergötland']['n']} från Västergötland, {SER['Medelpad']['n']} från Medelpad, {SER['Hälsingland']['n']} från Hälsingland, {SER['Gravmonument Ög/Sm']['n']} från de tidigkristna gravmonumenten i Östergötland och Småland och {SER['Åsmund']['n']} från stenarna signerade av Åsmund Kåresson. En slinga är bandet där texten står. Den omfattar mellanrummen mellan runorna, och ornament och kors ligger utanför.

Måttet är enkelt: hur stor del av det bilden visar som ligger inne i slingorna. Om bilden visade slumpvisa punkter skulle andelen bli densamma som slingornas andel av ytan, i mitten av skanningarna en fjärdedel. Kvoten mellan de två kallar vi *lyft*. Ett lyft på 1,3 betyder att bilden har 30 procent mer av sitt innehåll i texten än slumpen skulle ge.

Jämförelsen måste vara rättvis. En bild som visar mindre har lättare att träffa rätt, så vi skar av dagens djupbild med en gemensam gräns för hela stenen, vald så att den visade exakt lika stor del av ytan som den avskalade – i mitten av skanningarna {pc(SHOWN_B)} procent.

{IMG_TEST[True]}

**Resultatet.** Den avskalade bilden samlade sig inte bättre i texten. I mitten av de {N} skanningarna var lyftet {dec(P1['median_A'])} för dagens bild och {dec(P1['median_B'])} för den avskalade, och den avskalade var bättre på bara {B_BETTER} av {N}. Planen krävde att den avskalade skulle ligga högre i mitten av skanningarna, med en skillnad som slumpen sällan ger. Den låg lägre och var sämre på {B_WORSE} av {N}.

Bara de röda spåren såg först bättre ut: lyftet var {dec(P2['median_C'])}, och de var bättre än dagens bild på {C_BETTER} av {N} skanningar – en skillnad som slumpen skulle ge ungefär en gång på {P2_ONE_IN:.0f}. Men spåren visar mindre av ytan än allt som är kvar, {pc(SHOWN_C)} procent i stället för {pc(SHOWN_B)}. När vi gav dagens bild samma mindre yta fick den {dec(EX['median_A'])}, och spåren var bättre bara på {C_SAME_BETTER} av {N}. Den jämförelsen lade vi till under körningen, när vi såg att spåren visar mindre; den ingick inte i den låsta planen och är bara beskrivande.

{chart(True)}

**Varför?** Förklaringen syns i figuren. Den lokala nivån visar per konstruktion ungefär lika stor del av varje ruta, också rutor där det inte står någon text: ornamentik, sprickor och tomma fält mellan slingorna. En gemensam gräns tar i stället det djupaste på hela stenen, och det djupaste är oftast runorna. Det som skulle vara bildens styrka – att den ser lika noga på det grunda partiet som på det djupa – kostar alltså träffsäkerhet. Det tydliga i bilden kommer av själva snittet och av sorteringen i spår och gropar, inte av att den lokala nivån hittar mer text.

Två saker begränsar provet. Ornamentik räknas som miss, fast den är lika mycket huggen som runorna. Och provet mäter var bilden hamnar, inte om någon läser fler runor rätt med den. Det är nästa, och svårare, prov.

## Där den inte räcker

{IMG_HS14[True]}

- **Grovkorniga stenar.** På Hs 14 är kornen lika djupa som strecken. Den avskalade bilden gör mycket av texten grå och sprickorna röda, och dagens djupbild är bättre.
- **Brus.** På Sö 206 och Sö 162 blir vittringsfläckar i fälten mellan slingorna röda och måste klickas bort.
- **Inget nytt ur intet.** Bilden skapar ingen information som inte finns i skanningen. Ett streck som är grundare än vittringen runt omkring, eller finare än skanningens upplösning, kommer inte tillbaka, och ett för högt reglagevärde tar bort svaga stavar.
- **En annan yta prövades och underkändes.** För att följa välvda stenar prövade vi först en rullande paraboloid som referensyta. Ett låst prov på konstgjorda spår visade att den underskattade djupet med upp till 0,29 millimeter mot 0,08 för den vanliga stängningen, utan att mäta jämnare åt olika håll. Stängningen följer redan en välvd sten, så bilden och huggspårsmätningen använder samma yta.

## Så använder du den

1. Öppna 3D-sidan i Vitki och ladda upp en skanning i STL-, OBJ- eller PLY-format. Fria skanningar finns på Zenodo, se nedan.
2. Vrid stenen så att du ser den ristade sidan rakt framifrån. Bilden räknas för den vy du har när du öppnar den.
3. Klicka på *Skala av vittringen – se de djupa spåren* i rutan *Bilder ur skanningen*. Första gången tar det några sekunder; sedan räknas varje nytt reglageläge på några tiondels sekunder.
4. Flytta reglaget. 0 millimeter är vittringens nivå; åt höger skalas mer av, åt vänster mindre. Dialogen visar stenens vittringsnivå från lägsta till högsta.
5. Sortera. I läget *Klick tar bort* klickar du bort gropar och sprickor. I läget *Klick gör till spår* gör du en grå fläck som hör till en runa till spår. *Visa gropar* tänder och släcker det grå.
6. Ladda ned bilden. Om du visar den för någon, skriv reglagets värde och vad du har klickat bort eller lagt till: bilden är en hjälp att se, inte en läsning.

:::box Det viktigaste i korthet
- *Skala av vittringen* visar bara det som ligger djupare än vittringen runt omkring och låter läsaren sortera resten: klicka bort gropar och gör missade spår till spår.
- Ett låst prov mot {N} skanningar visade att den lokala vittringsnivån inte samlar mer av texten än en enkel gemensam gräns. Bildens styrka ligger i snittet och sorteringen, inte i att den hittar mer.
- Bilden skapar inget som inte finns i skanningen. Det som är grundare än vittringen kommer inte tillbaka.
- Skriv alltid reglagets värde och vad du har klickat när du visar en sådan bild.
:::

## Om skanningarna

Alla bilder och mått i artikeln är beräknade i Vitki ur öppna skanningar, använda som de är publicerade. Textslingorna är ritade och granskade av Viktor Kvant i Vitki.

{scans_section(True)}

Tack till Laila Kitzler Åhfeldt och Henrik Zedig för att skanningarna är fritt tillgängliga.

## Källor

{sources(True)}"""

body_en = f"""Anyone who has stood in front of a runestone in slanting afternoon light knows how the runes come and go. A branch is clear for a minute and gone when the sun has moved. A 3D scan does not have that problem. It has measured the surface of the stone point by point, to fractions of a millimetre, and the measurement does not change with the light. But the scan has another problem: the weathering has depth too. Pits where grains have come loose, cracks and a thousand years of frost lie in the same measurement as the carver's chisel marks, and on a depth image they often look alike.

The idea behind the new feature was simple: if you could peel off the weathered surface, the deep grooves should remain. Vitki now has such a picture, *Peel away the weathering*, on the 3D page. Here we describe how it is computed, how to use it, and what a locked test on {N} scans showed about what it is good for.

{IMG_GS11[False]}

## Three things the picture does differently

**The surface follows the curve of the stone.** Depth is measured against an imagined surface without carvings. Think of a stiff blanket laid over the stone: it follows the stone's curve but does not reach down into furrows narrower than two centimetres. The distance from the blanket down to the stone is the depth. Technically it is a morphological closing with a 20-millimetre window – the same surface Vitki's groove measurement uses.

**Depth is measured perpendicular to the surface.** On a slope the depth is counted straight into the stone, not straight back as seen from the viewer. Where the surface slopes 30 degrees the difference is 13 percent, at 45 degrees 29 percent. The sides of the stone, steeper than {peel.MAX_SLOPE_DEG:.0f} degrees, and an edge zone of one centimetre are left out.

**The threshold follows the weathering where it is.** The stone is divided into squares of six centimetres. In each square the level of the weathering is the depth that {peel.LEVEL_Q} percent of the square is shallower than, and the levels are smoothed between squares. What lies deeper than the level is shown; the rest is peeled away. A slider moves the threshold from one millimetre shallower to three millimetres deeper. On Sö 206 the level runs from 0.6 to 1.2 millimetres, so one common threshold for the whole stone would peel away too much in one place and too little in another. That was the idea. The test further down shows that it did not hold.

What remains is divided into specks. A speck whose deepest part is at least {peel.GROOVE_LENGTH_MM:.0f} millimetres long – as long as the shortest rune the groove analysis counts – and at least three times as long as it is wide is coloured rust and called a **groove**. The rest are **pits** and turn grey. The rule does not know what a rune is. Ornament and cracks are also long and narrow, and a frame band that the weathering has turned into a net of pits turns grey.

## The reader decides

That is why the picture is built for the reader to sort. A click on a speck removes it. In the other click mode, *Click makes a groove*, a grey speck becomes a groove, in darker rust so that you can see what was done by hand. A second click undoes it, and Shift-click gives the other mode without switching. The clicks are saved in the browser as points on the 3D model. They follow when you move the slider and are still there the next time the same scan is opened in the same browser.

{IMG_DIALOG[False]}

## Does it help you see the text?

To the eye the picture looked promising. On Gs 11 the runes became almost like a drawing. But the eye is easy to convince, so we decided in advance how to measure and locked the plan before anything was counted.

The answer key is the text bands Viktor has drawn and checked on {N} scan files of {OBJ} stones and grave monuments: {SER['Södermanland']['n']} from Södermanland, {SER['Västergötland']['n']} from Västergötland, {SER['Medelpad']['n']} from Medelpad, {SER['Hälsingland']['n']} from Hälsingland, {SER['Gravmonument Ög/Sm']['n']} from the early Christian grave monuments in Östergötland and Småland and {SER['Åsmund']['n']} from the stones signed by Åsmund Kåresson. A band is the strip where the text stands. It includes the spaces between the runes, and ornament and crosses lie outside it.

The measure is simple: how much of what the picture shows lies inside the bands. If the picture showed random points, the share would equal the bands' share of the surface – in the middle of the scans, a quarter. We call the ratio between the two the *lift*. A lift of 1.3 means that the picture has 30 percent more of its content in the text than chance would give.

The comparison has to be fair. A picture that shows less finds it easier to be right, so we cut today's depth image at one common threshold for the whole stone, chosen so that it showed exactly as much of the surface as the peeled one – in the middle of the scans {pc(SHOWN_B)} percent.

{IMG_TEST[False]}

**The result.** The peeled picture did not gather better in the text. In the middle of the {N} scans the lift was {dec(P1['median_A'], sv=False)} for today's image and {dec(P1['median_B'], sv=False)} for the peeled one, and the peeled one was better on only {B_BETTER} of {N}. The plan required the peeled one to lie higher in the middle of the scans, by a difference chance seldom gives. It lay lower and was worse on {B_WORSE} of {N}.

Only the red grooves looked better at first: their lift was {dec(P2['median_C'], sv=False)}, and they beat today's image on {C_BETTER} of {N} scans – a difference chance would produce about once in {P2_ONE_IN:.0f}. But the grooves show less of the surface than everything left, {pc(SHOWN_C)} percent instead of {pc(SHOWN_B)}. When we gave today's image the same smaller area it reached {dec(EX['median_A'], sv=False)}, and the grooves were better on only {C_SAME_BETTER} of {N}. We added that comparison during the run, when we saw that the grooves show less; it was not part of the locked plan and is descriptive only.

{chart(False)}

**Why?** The explanation can be seen in the figure. By construction, the local level shows roughly the same share of every square, including squares where there is no text: ornament, cracks and empty fields between the bands. One common threshold instead takes the deepest parts of the whole stone, and the deepest parts are usually the runes. What was meant to be the picture's strength – that it looks as carefully at the shallow part as at the deep – therefore costs accuracy. The clarity of the picture comes from the cut itself and from the sorting into grooves and pits, not from the local level finding more text.

Two things limit the test. Ornament counts as a miss, although it is as much carved as the runes. And the test measures where the picture lands, not whether anyone reads more runes correctly with it. That is the next, and harder, test.

## Where it is not enough

{IMG_HS14[False]}

- **Coarse-grained stones.** On Hs 14 the grains are as deep as the strokes. The peeled picture turns much of the text grey and the cracks red, and today's depth image is better.
- **Noise.** On Sö 206 and Sö 162 weathering patches in the fields between the bands turn red and have to be clicked away.
- **Nothing from nothing.** The picture creates no information that is not in the scan. A stroke shallower than the weathering around it, or finer than the scan's resolution, does not come back, and too high a slider value removes faint staves.
- **Another surface was tried and rejected.** To follow domed stones we first tried a rolling paraboloid as the reference surface. A locked test on artificial grooves showed that it underestimated depth by up to 0.29 millimetres against 0.08 for the usual closing, without measuring more evenly in different directions. The closing already follows a domed stone, so the picture and the groove measurement use the same surface.

## How to use it

1. Open the 3D page in Vitki and upload a scan in STL, OBJ or PLY format. Free scans are available on Zenodo, see below.
2. Turn the stone so that you see the carved face straight on. The picture is computed for the view you have when you open it.
3. Click *Peel away the weathering – see the deep grooves* in the box *Images from the scan*. The first time takes a few seconds; after that each new slider position takes a few tenths of a second.
4. Move the slider. 0 millimetres is the level of the weathering; to the right more is peeled away, to the left less. The dialog shows the stone's weathering level from lowest to highest.
5. Sort. In the mode *Click removes* you click away pits and cracks. In the mode *Click makes a groove* you make a grey speck that belongs to a rune a groove. *Show pits* turns the grey on and off.
6. Download the picture. If you show it to anyone, state the slider's value and what you have clicked away or added: the picture is an aid to seeing, not a reading.

:::box The essentials in brief
- *Peel away the weathering* shows only what lies deeper than the weathering around it and lets the reader sort the rest: click away pits and make missed grooves grooves.
- A locked test on {N} scans showed that the local weathering level does not gather more of the text than one simple common threshold. The picture's strength lies in the cut and the sorting, not in finding more.
- The picture creates nothing that is not in the scan. What is shallower than the weathering does not come back.
- Always state the slider's value and what you have clicked when you show such a picture.
:::

## About the scans

All pictures and measurements in the article are computed in Vitki from open scans, used as published. The text bands were drawn and checked by Viktor Kvant in Vitki.

{scans_section(False)}

Our thanks to Laila Kitzler Åhfeldt and Henrik Zedig for making the scans freely available.

## Sources

{sources(False)}"""

EN_UI = json.load(open(os.path.join(ROOT, "web", "src", "i18n", "en.json"), encoding="utf-8"))
for sv_ui, en_ui in (("Skala av vittringen", "Peel away the weathering"),
                     ("Skala av vittringen – se de djupa spåren", "Peel away the weathering – see the deep grooves"),
                     ("Klick tar bort", "Click removes"), ("Klick gör till spår", "Click makes a groove"),
                     ("Visa gropar", "Show pits")):
    assert EN_UI[sv_ui] == en_ui and sv_ui in body and en_ui in body_en, sv_ui  # the app's own words
assert EN_UI.get("Bilder ur skanningen") == "Images from the scan" and "*Images from the scan*" in body_en, EN_UI.get("Bilder ur skanningen")
for lang, b in (("sv", body), ("en", body_en)):
    assert not re.search(r"^\|", b, re.M), "BlogBody visar inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 4 and all(re.match(r"/api/blog/figures/[0-9a-f]{16}\.png$", u) for u in imgs), imgs
    for doi in (d["doi"] for d in scan_sources.DATASETS):
        assert doi in b, doi
labels = ["Metod", "Huggspår och 3D"]
assert blog_labels.check(labels) is None
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "skala_av.json")
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
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Metod|skala-av", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
