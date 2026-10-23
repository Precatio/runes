"""Export från huggspårsanalysen: bilder, rutnät och tabeller ur en analys, med skanningens kreditering.

Inga mätvärden räknas om: tabellerna är analysens snitt som de lagrats, och ristningskartan och granskningsbilden är
den automatiska analysens egna bilder. Bilderna ur skanningen räknas fram ur 3D-modellen när filerna skapas, med
samma funktioner som stenrapporten: värmekartan är stenrapportens figur 2 (stone_report.depth_figure), rutnätet samma
djup som tal, och reliefen och strykljuset samma bilder som render_relief. I den automatiska analysen räknas
sammanfattningen och verktygstumregeln om för forskarens grupper (se nedan). ITEMS är den enda källan till filernas
namn och förklaringar: appens hjälptext ("Vad innehåller filerna?"), kryssrutorna och README.txt i ZIP-paketet läser
alla härifrån (METHODS.md, 2f).

Krediteringen av skanningen följer med i varje fil: som text i PNG-filernas metadata (iTXt), som en synlig rad under
figurerna och granskningsbilden, som '#'-rader överst i tabellerna och i README.txt och kalla.json. Reliefen och
ristningskartan får ingen synlig rad (deras pixlar lämnas orörda), så de skickas alltid i en ZIP med README.txt
(NO_FOOTER). En öppen datamängd krediteras bara när den inlästa filen känns igen som en av datamängdens publicerade
filer (scan_sources.identify), aldrig utifrån det signum som skrivits in.

Den automatiska analysen exporteras med forskarens etiketter som stenrapporten läser dem (web/src/lib/stoneReport.ts
fromSession): godkända snitt utom de uteslutna, grupperade efter etikett, och sammanfattningarna räknas om för
grupperna med projektets egna funktioner (src/stats). Mätformen läses ur analysens proveniens, och bilderna ur
skanningen ses längs samma normal som stenrapportens (view_normal, delad med api/routers/reports.py).
"""
from __future__ import annotations

import base64
import binascii
import datetime
import io
import json
import math
import re
import unicodedata
import zipfile
from typing import Callable

import numpy as np

from src import limitations, scan_sources
from src.stats import METRICS, summarize_by_rune, summarize_slices

APP_NAME = "Vitki"
APP_VERSION = "3.0.0"
METHOD_VERSION = "groove-5"
try:  # the API's own constants when they are importable (they are the source of truth)
    from api.config import APP_NAME, APP_VERSION, METHOD_VERSION  # noqa: F811
except Exception:  # pragma: no cover - src used without the api package
    pass

COMPUTED_NOTE = "Bilden är beräknad i Vitki."
TABLE_NOTE = "Tabellen är beräknad i Vitki."
FILES_NOTE = "Filerna är beräknade i Vitki."
UNKNOWN_SCAN_TEXT = "okänd – ange vem som skannat stenen."
UNKNOWN_SCAN = "Skanning: " + UNKNOWN_SCAN_TEXT
USER_SCAN_TEXT = "enligt den som exporterade: "
USER_SCAN = "Skanning (enligt den som exporterade): "
VITKI = "Bygger på Vitki, ursprungligen utvecklad av Viktor Kvant (https://github.com/Precatio/runes)."
CITE = "Citera Vitki enligt CITATION.cff (https://github.com/Precatio/runes/blob/main/CITATION.cff)."
EXPORTED_FROM = "Vitki, Mäta huggspår (3D)"
SOURCE = ("Vitkis huggspårsanalys av 3D-skanningen; metoden beskrivs i METHODS.md, avsnitt 2 "
          "(https://vitkirunor.se/docs/metod).")
COORDS = "mm i 3D-modellen centrerad på sin omslutande lådas mitt (centered_by)"
# Items whose pixels are left untouched, so they carry the credit only in their metadata: on their own they are sent
# in a ZIP with README.txt, never as a bare image
NO_FOOTER = {"relief", "groove_map"}
OLD_SCALE = "skalan sparades inte (äldre analys)"
NODATA = -9999
FIGURE_DPI = 220  # stone_report._png
RAKING = (("nordväst", "nordvast", 315), ("nordost", "nordost", 45), ("sydost", "sydost", 135),
          ("sydväst", "sydvast", 225))
GROUPS = {"skanning": "Bilder ur skanningen", "matning": "Bilder ur mätningen", "data": "Tabeller och data"}

# Limits for what the browser sends (the API returns 400 above them)
MAX_SIGNUM = 100
MAX_SLICES = 20_000
MAX_PROFILE_POINTS = 20_000
MAX_IMAGE_BYTES = 25 * 1024 * 1024  # one embedded PNG (the automatic analysis' images are at most 1 600 px)
MAX_IMAGE_SIDE = 4_000
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
LABELS = ("rune", "ornament", "unknown", "excluded")
GROUP_ORDER = ("rune", "ornament", "unknown")  # as stone_report.build_facts orders the analyses
# provenance.parameters.mode of each measuring form (api/routers/threed.py) -> the export's name for it
MODES = {"automatic": "auto", "one-click": "oneclick", "slices": "manual", "path": "path"}
NORMAL_SOURCES = {
    "analys": "analysens egen normal (den automatiska analysens; bilderna ligger då som ristningskartan)",
    "snitt": "medelriktningen av snittens uppåtriktning, som i stenrapporten",
    "angiven": "den angivna riktningen",
    "vy": "3D-vyns riktning när filerna skapades (analysen anger ingen normal)",
    "uppskattad": "stenens tunnaste riktning (uppskattad; ingen analys och ingen vy)",
}


class BadInput(ValueError):
    """Indata som inte går att exportera (API:t svarar 400)."""

ITEMS = [
    {"id": "depth_heatmap", "group": "skanning", "formats": ["PNG"], "needs": ["mesh"],
     "label": "Spårdjup som värmekarta",
     "file": "{sig}_djup_under_stenytan.png",
     "explanation": "Färgen visar hur djupt varje punkt ligger under en referensyta som räknats fram ur skanningen "
                    "genom att fylla igen alla fördjupningar smalare än 20 mm. Referensytan ligger i nivå med ytan "
                    "runt spåren och spårkanterna, inte på en tänkt ursprunglig stenyta. Ljust betyder i nivå med "
                    "referensytan och svart det djupaste. Skalan i mm står bredvid; den slutar vid stenens 99,5:e "
                    "percentil, så den djupaste halva procenten av ytan blir lika svart. Kartan visar formen. "
                    "Spårdjupen i mättabellen blir ofta 10–40 % större än kartans, ibland mindre, eftersom de mäts i "
                    "täta tvärsnitt från spårkanten till botten, medan kartan är ett grövre rutnät där varje ruta har "
                    "den högsta punkten i sin ruta och den smala botten i ett spår sällan träffas exakt. Den yttersta centimetern mot skanningens kant är tom, "
                    "eftersom referensytan inte går att räkna fram säkert där. Branta partier innanför den, som "
                    "stenens sidor eller kanten på en avslagen yta, liksom sprickor, vittringsgropar och borrhål, kan "
                    "ändå se ut som djupa spår."},
    {"id": "depth_grid", "group": "skanning", "formats": ["ASC", "JSON"], "needs": ["mesh"],
     "label": "Spårdjup som rådata (rutnät i mm)",
     "file": "{sig}_djup_under_stenytan_mm.asc + .json",
     "explanation": "Samma djup som i värmekartan, som tal: ett värde i millimeter per ruta. Rutans storlek står i "
                    "filhuvudet (cellsize) och beror på skanningens täthet och stenens storlek, eftersom rutnätet "
                    "har högst 1 800 rutor på längden. Filen öppnas i QGIS, i R (terra) eller i Python, och där kan "
                    "du rita egna kartor, höjdkurvor eller profiler. Rutor med −9999 ligger utanför skanningen eller "
                    "i kantzonen. Koordinaterna är millimeter i stenytans eget plan, inte geografiska. Samma "
                    "förbehåll gäller som för kartan: referensytan ligger i nivå med spårkanterna, och branta "
                    "partier, sprickor och vittring kommer med."},
    {"id": "relief", "group": "skanning", "formats": ["PNG"], "needs": ["mesh"],
     "label": "Reliefbild (ljus från alla håll)",
     "file": "{sig}_relief.png",
     "explanation": "Stenytan belyst från fyra håll på en gång, där det mörkaste värdet behålls. Varje spår blir "
                    "därför mörkt, oavsett åt vilket håll det går. Bilden är till för att läsa och visa runorna. "
                    "Gråtonen är inte ett mått i millimeter, och kontrasten är sträckt för just denna sten. En pixel "
                    "är en ruta i ytans rutnät; storleken i mm står i filens metadata och i README.txt. Bilden har ingen "
                    "synlig rad om skanningen, bara metadata, som bildprogram ofta tar bort; därför kommer den "
                    "alltid i en ZIP med README.txt, också när den laddas ned ensam."},
    {"id": "raking", "group": "skanning", "formats": ["PNG"], "needs": ["mesh"],
     "label": "Strykljus från fyra håll",
     "file": "{sig}_strykljus_nordvast.png, _nordost.png, _sydost.png, _sydvast.png",
     "explanation": "Digitalt strykljus, 20° över ytan, från fyra håll, som när man fotograferar en sten i lågt "
                    "sidoljus. Ett spår syns tydligast när ljuset faller tvärs över det och kan nästan försvinna när "
                    "ljuset går längs med, så titta på alla fyra. 'Nordväst' betyder snett uppifrån vänster i "
                    "bilden, inte ett väderstreck vid stenen. En pixel är en ruta i ytans rutnät, som i reliefen."},
    {"id": "groove_map", "group": "matning", "formats": ["PNG"], "needs": ["auto", "groove_map"],
     "label": "Ristningskarta (automatiska analysens djupkarta)",
     "file": "{sig}_ristningskarta.png",
     "explanation": "Spårdjupet i den automatiska analysens rutnät (0,6 mm med Vitki-protokollet), i gråskala och i "
                    "samma läge och storlek som granskningsbilden, så att punkter och rutor stämmer. Svart sätts vid "
                    "95:e percentilen av djupen i de rutor som ligger djupare än analysens tröskel, och allt djupare "
                    "blir också svart; värdet i mm (black_mm) står i metadata. Gråtonerna kan därför inte jämföras "
                    "mellan stenar. Kartan är inte begränsad till det område analysen mätte i: kantzonen och branta "
                    "partier, som analysen hoppar över, finns med och kan se djupa ut, liksom sprickor och "
                    "ornamentik. Svart betyder black_mm eller djupare, och svartpunkten kan sättas av skanningens kant, "
                    "så runorna kan se mellangrå ut. Bilden har ingen synlig rad om skanningen, bara metadata; därför "
                    "kommer den alltid i en ZIP med README.txt."},
    {"id": "review_image", "group": "matning", "formats": ["PNG"], "needs": ["auto", "review_image"],
     "label": "Granskningsbild med mätpunkter",
     "file": "{sig}_granskningsbild.png",
     "explanation": "Visar var programmet mätte. Orange är spår som hittats och gråblått är ytor för breda att "
                    "mäta. De färgade prickarna är godkända snitt, färgade efter V-vinkel (skala 30–130°, klippt i "
                    "ändarna), och de små grå prickarna är bortsorterade snitt. Vinklar på 130° eller mer blir gula. "
                    "Bilden visar analysens egen sortering, inte de etiketter du har satt, och den kan visa punkter "
                    "på ramlinjer eller slingband som tagits för runor. Den är till för att granska analysen, inte "
                    "ett resultat i sig."},
    {"id": "positions_figure", "group": "matning", "formats": ["PNG"], "needs": ["mesh", "point>=1"],
     "label": "Snittens läge färgade efter V-vinkel",
     "file": "{sig}_snittpositioner_v_vinkel.png",
     "explanation": "Var varje mätt tvärsnitt ligger på stenen, färgat efter V-vinkeln. Färgskalan följer stenens "
                    "egna värden och står bredvid. Bokstäverna A–L hör till bilden med tvärsnittsprofiler. Med "
                    "bilden ser man om breda eller smala vinklar samlas i en del av ristningen, till exempel där "
                    "ytan är mer vittrad. Snitt du har märkt som uteslutna är inte med."},
    {"id": "spatial_figure", "group": "matning", "formats": ["PNG"], "needs": ["mesh", "point>=3"],
     "label": "Spårdjup, spårbredd och ytråhet på stenen",
     "file": "{sig}_djup_bredd_ytrahet.png",
     "explanation": "Tvärsnittens spårdjup, spårbredd och ytråhet, ritade där de mättes. Det är mätningarna i "
                    "tabellen, inte djupkartan. Ytråheten är mycket små tal, hundradels millimeter, och ligger nära "
                    "skanningens brus."},
    {"id": "profiles_figure", "group": "matning", "formats": ["PNG"], "needs": ["profile"],
     "label": "Tvärsnittsprofiler (bild)",
     "file": "{sig}_tvarsnittsprofiler.png",
     "explanation": "Upp till tolv representativa tvärsnitt med samma skala på båda axlarna, så att formen inte "
                    "överdrivs. Punkterna kommer från skanningen, de röda linjerna är de anpassade väggarna "
                    "(20–80 % av djupet) och den streckade linjen är spårkanternas nivå: medel av de högsta punkterna "
                    "strax utanför spårets båda kanter, som bredden räknas vid. Över varje ruta står vinkel, djup och "
                    "bredd. Här ser man om måtten rimligen beskriver spåret, till exempel V- eller U-form eller en "
                    "avslagen kant."},
    {"id": "slices_csv", "group": "data", "formats": ["CSV"], "needs": ["slices"],
     "label": "Mättabell, ett tvärsnitt per rad",
     "file": "{sig}_snitt.csv",
     "explanation": "En rad per tvärsnitt. V-vinkel är öppningen mellan spårets väggar (°), spårdjup avståndet från "
                    "spårkanten till botten och spårbredd bredden där väggarnas linjer når spårkanternas nivå (mm). "
                    "Ytråhet är väggarnas ojämnhet, och fit_r2 är det sämre av de två väggarnas R², alltså hur väl "
                    "väggarna följer en rak linje. Den automatiska analysen sorterar bort snitt med fit_r2 under 0,8; "
                    "de andra mätformerna sorterar inte på fit_r2. Bottenradie och asymmetri är osäkra mått. Snitt i "
                    "samma runa hänger ihop och är inte oberoende mätningar, så använd sammanfattningen per runa för "
                    "stenens värde. feature_type är spårtypen för mätningar med Ett klick, manuellt och längs en "
                    "bana; i den automatiska analysen är kolumnen tom och label (din etikett) är snittets grupp. "
                    "Koordinaterna är millimeter i den centrerade 3D-modellen, inte i originalfilen; img_x och img_y "
                    "är pixlar i granskningsbilden. I den automatiska analysen är position_mm provpunktens "
                    "ordningsnummer över hela stenen gånger snittavståndet, inte ett avstånd längs ett spår. "
                    "Rader som börjar med # anger källa och proveniens."},
    {"id": "summary_csv", "group": "data", "formats": ["CSV"], "needs": ["summary"],
     "label": "Sammanfattning per sten och per runa",
     "file": "{sig}_sammanfattning.csv",
     "explanation": "Stenens medelvärden med spridning (sd) och 95-procentigt konfidensintervall. Raderna per runa "
                    "räknar varje runa som en mätning och ger det ärliga värdet för stenen; intervallet per snitt "
                    "blir för smalt, eftersom snitten i en runa liknar varandra. ICC visar hur stor del av "
                    "spridningen som ligger mellan runorna. Den skattas ur en variansanalys och kan bli negativ när "
                    "snitten i samma runa skiljer sig minst lika mycket som runorna sinsemellan; ett negativt värde "
                    "läses som ingen skillnad mellan runorna. I den automatiska analysen räknas sammanfattningen om "
                    "för de grupper du har märkt (runa, ornamentik, okänt), utan de uteslutna snitten; raderna per "
                    "runa och ICC finns bara för gruppen runa och bara när analysen mätte enbart runor. Riktmärke: "
                    "minst 10 mätta runor för att beskriva en sten och minst 20 för att jämföra stenar. Gissningen "
                    "om verktyg (pikmejsel eller bredmejsel) är en tumregel och inte kalibrerad."},
    {"id": "runes_csv", "group": "data", "formats": ["CSV"], "needs": ["auto", "runes"],
     "label": "Runor och kvalitetskontroll (automatisk analys)",
     "file": "{sig}_runor.csv",
     "explanation": "Det programmet har räknat som en runa: en grupp sammanhängande raka streck, inte en runa som "
                    "programmet känt igen. För varje grupp anges höjd i mm, antal streck och antal godkända snitt; "
                    "rutan anges i granskningsbildens pixlar. Överst står hur många snitt som prövades och varför de "
                    "bortsorterade föll bort. Igenkänningen är inte validerad, så jämför med granskningsbilden."},
    {"id": "profiles_csv", "group": "data", "formats": ["CSV"], "needs": ["profile"],
     "label": "Tvärsnittsprofiler som tal",
     "file": "{sig}_profiler.csv",
     "explanation": "De uppmätta punkterna i varje tvärsnitt, innan något jämnats ut: x går tvärs över spåret och z "
                    "i höjdled, i mm, med mätpunkten som nollpunkt. Med dem kan vem som helst mäta om spåren med en "
                    "annan metod eller rita profilerna själv."},
    {"id": "length_profile_csv", "group": "data", "formats": ["CSV"], "needs": ["depth_profile"],
     "label": "Längdprofil längs den ritade banan",
     "file": "{sig}_langdprofil.csv",
     "explanation": "Spårdjupet längs banan du ritade, snitt för snitt. Där syns var ett streck börjar och slutar och "
                    "spår av omhuggning eller vittring. Banans snitt sorteras inte lika strängt som den automatiska "
                    "analysens; alla snitt med en giltig vinkel kommer med."},
    {"id": "full_json", "group": "data", "formats": ["JSON"], "needs": ["slices"],
     "label": "Hela analysen (JSON med proveniens)",
     "file": "{sig}_analys.json",
     "explanation": "Hela analysen i maskinläsbar form: alla snitt med profiler, sammanfattningar, inställningar och "
                    "kvalitetskontroll. För den automatiska analysen kommer också runor, streck, skälen till "
                    "bortsorterade snitt, dina etiketter och sammanfattningarna per grupp med. Proveniensen anger "
                    "programversion, mätmetod (groove-5), skanningsfilens namn och SHA-256-fingeravtryck, datum och "
                    "metodens kända brister. Det är filen som behövs för att göra om eller granska analysen."},
]
BY_ID = {x["id"]: x for x in ITEMS}
IMAGE_ITEMS = {"depth_heatmap", "depth_grid", "relief", "raking", "positions_figure", "spatial_figure"}

# Not files of their own: the ZIP package and the stone report (shown by the UI's help text and in README.txt)
BUNDLE = {"id": "bundle_zip", "label": "Allt valt i ett paket (ZIP med README.txt)",
          "file": "{sig}_vitki_export_{datum}.zip",
          "explanation": "När du väljer mer än en fil kommer allt i en ZIP-fil. README.txt i paketet förklarar varje "
                         "fil, och kalla.json anger proveniensen: programversion, mätmetod, skanningsfil, inställningar "
                         "och vem som skannat stenen. Skicka med README.txt om du delar filerna vidare; där står också "
                         "vem som ska krediteras för skanningen."}
STONE_REPORT = {"id": "stone_report_link", "label": "Stenrapport (Word, LaTeX, Markdown) – allt med figurtexter",
                "explanation": "Vill du ha figurerna med bildtexter, mättabeller, kvalitetskontroll och kända brister i "
                               "ett och samma dokument, välj stenrapporten. Den innehåller samma figurer som filerna "
                               "här, men inte sammanfattningen per runa eller ICC, och krediterar skanningen på samma "
                               "sätt: bara när filen känns igen som en publicerad fil, aldrig utifrån signumet."}
README_INTRO = ("Filerna är exporterade från Vitkis huggspårsanalys (Mäta huggspår, 3D). Inga mätvärden räknas om: "
                "tabellerna återger analysens snitt som de lagrats. Bilderna ur skanningen räknas fram ur 3D-modellen "
                "när filerna skapas, och i den automatiska analysen räknas sammanfattningen och verktygstumregeln om "
                "för dina grupper. Tre koordinatsystem används. Tabellernas punkter och riktningar är millimeter i "
                "3D-modellen, centrerad på sin omslutande lådas mitt, inte i originalfilens eller geografiska "
                "koordinater. Rutnätet (.asc) är millimeter i stenytans eget plan, med origo och bas i JSON-filen "
                "bredvid. img_x, img_y och box_* är pixlar i granskningsbilden, med origo uppe till vänster.")
README_CAVEAT = ("Måtten beskriver hur spåren är huggna, men det är inte visat att de skiljer ristare åt. Använd minst "
                 f"{limitations.MIN_RUNES_DESCRIBE} mätta runor för att beskriva en sten och minst "
                 f"{limitations.MIN_RUNES_COMPARE} för att jämföra stenar.")


def catalogue() -> dict:
    """Svaret från GET /api/3d/export_items."""
    return {"items": [{k: x[k] for k in ("id", "label", "file", "explanation", "group", "formats", "needs")}
                      for x in ITEMS],
            "groups": GROUPS, "bundle": BUNDLE, "stone_report": STONE_REPORT,
            "readme_intro": README_INTRO, "caveat": README_CAVEAT}


# ---- names, credit ---------------------------------------------------------------------------------------------------

_TRANSLIT = str.maketrans({"æ": "ae", "Æ": "Ae", "ø": "o", "Ø": "O", "þ": "th", "Þ": "Th", "ð": "d", "Ð": "D"})


def slug(signum: str | None) -> str:
    """'Sö 370' -> 'So_370', 'Sö Fv1948;282' -> 'So_Fv1948_282'; utan signum 'vitki'. Bara ASCII."""
    s = unicodedata.normalize("NFKD", (signum or "").translate(_TRANSLIT))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s[:60] or "vitki"


def clean_signum(raw) -> str:
    """Signumet som det skrivits in, utan styrtecken och med ett mellanslag mellan orden. BadInput om det är längre
    än MAX_SIGNUM tecken."""
    s = unicodedata.normalize("NFC", str(raw or ""))
    s = "".join(" " if unicodedata.category(c) in ("Cc", "Zl", "Zp") else c for c in s
                if unicodedata.category(c) not in ("Cf", "Co", "Cs"))
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > MAX_SIGNUM:
        raise BadInput(f"Signumet får vara högst {MAX_SIGNUM} tecken.")
    return s


def scan_credit(filename: str | None = None, sha256: str | None = None, md5: str | None = None,
                size: int | None = None) -> dict:
    """Skanningens kreditering (svaret från GET /api/3d/scan_credit; samma text som filerna får).

    known är True bara när filen känns igen som en publicerad fil i en av de öppna serierna (scan_sources.identify:
    SHA-256, md5, eller filnamn och storlek; ett filnamn utan storlek räcker inte). Ett signum räcker aldrig: då får
    filerna ingen kreditering av någon annan, och den som exporterar kan ange sin egen."""
    hit = scan_sources.identify(filename, sha256, md5, size)
    if not hit:
        return {"known": False, "match": None, "file": None, "dataset": None, "credit_text": None,
                "computed_note": COMPUTED_NOTE}
    ds, f = hit["dataset"], hit["file"]
    return {"known": True, "match": hit["match"],
            "file": {"name": f["name"], "signum": f.get("signum"), "signa": scan_sources.file_signa(f),
                     "size": f.get("size")},
            "dataset": {"key": ds["key"], "creator": ds["creator"],
                        "scanned_by": ds.get("scanner") or ds.get("scanned_by") or ds["creator"],
                        "institution": ds.get("institution"), "project": ds["project"], "license": ds["license"],
                        "license_url": scan_sources.LICENSE_URLS.get(ds["license"]), "doi": ds["doi"],
                        "url": ds["url"], "citation": ds["citation"], "short": ds["short"], "device": ds["device"]},
            "credit_text": scan_sources.file_credit_text(ds, f), "computed_note": COMPUTED_NOTE}


def credit_for_mesh(mesh: dict | None) -> dict:
    """scan_credit för en modell eller en analys proveniens (filename, sha256, md5, bytes)."""
    m = mesh if isinstance(mesh, dict) else {}
    size = m.get("bytes")
    return scan_credit(m.get("filename"), m.get("sha256"), m.get("md5"),
                       int(size) if isinstance(size, (int, float)) and not isinstance(size, bool)
                       and math.isfinite(size) else None)


def credit_line(credit: dict, note: str = COMPUTED_NOTE) -> str:
    """Raden under figurerna: den igenkända seriens kreditering, annars den exporterandes egen text, annars en
    uppmaning; sist note (vad Vitki har beräknat)."""
    if credit.get("known") and credit.get("credit_text"):
        text = credit["credit_text"]
    elif (credit.get("scan_note") or "").strip():
        text = USER_SCAN + _one_line(credit["scan_note"])
    else:
        text = UNKNOWN_SCAN
    return f"{text} {note}"


def credit_value(credit: dict, note: str = TABLE_NOTE) -> str:
    """Krediteringen som värde efter etiketten 'Skanning:' i tabellhuvudet, utan att upprepa ordet."""
    if credit.get("known") and credit.get("credit_text"):
        text = credit["credit_text"]
    elif (credit.get("scan_note") or "").strip():
        text = USER_SCAN_TEXT + _one_line(credit["scan_note"])
    else:
        text = UNKNOWN_SCAN_TEXT
    return f"{text} {note}"


def _one_line(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


# ---- PNG -------------------------------------------------------------------------------------------------------------

def _font(px: int):
    from PIL import ImageFont
    try:
        import matplotlib
        path = f"{matplotlib.get_data_path()}/fonts/ttf/DejaVuSans.ttf"
        return ImageFont.truetype(path, px)
    except Exception:  # pragma: no cover - matplotlib ships the font
        return ImageFont.load_default()


def _wrap(draw, text: str, font, width: float) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and draw.textlength(trial, font=font) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def _font_px(width: int) -> int:
    return max(11, min(28, round(width / 95)))


def credit_footer(width: int, text: str, mode: str = "RGB"):
    """En vit remsa med krediteringen, lika bred som bilden (läggs under figurens pixlar, som lämnas orörda)."""
    from PIL import Image, ImageDraw
    px = _font_px(width)
    font = _font(px)
    pad = max(6, px // 2)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = _wrap(probe, text, font, width - 2 * pad)
    line_h = round(px * 1.3)
    strip = Image.new(mode, (width, 2 * pad + line_h * max(1, len(lines))), _white(mode))
    draw = ImageDraw.Draw(strip)
    for k, line in enumerate(lines):
        draw.text((pad, pad + k * line_h), line, fill=_ink(mode, (71, 85, 105)), font=font)
    return strip


def _white(mode: str):
    return {"RGBA": (255, 255, 255, 255), "L": 255, "LA": (255, 255)}.get(mode, (255, 255, 255))


def _ink(mode: str, rgb):
    if mode == "L":
        return int(round(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]))
    return (*rgb, 255) if mode == "RGBA" else tuple(rgb)


def _stack(top, *strips):
    """Bilden överst med sina pixlar oförändrade och remsorna under."""
    from PIL import Image
    h = top.height + sum(s.height for s in strips)
    out = Image.new(top.mode, (top.width, h), _white(top.mode))
    out.paste(top, (0, 0))
    y = top.height
    for s in strips:
        out.paste(s.convert(top.mode), (0, y))
        y += s.height
    return out


def legend_strip(width: int, angle_range=(30.0, 130.0)):
    """Teckenförklaring till granskningsbilden (src/auto_grooves._overlay_png): spårens färger, V-vinkelskalan
    (viridis, klippt i ändarna) och de bortsorterade snitten."""
    from matplotlib import colormaps
    from PIL import Image, ImageDraw
    px = _font_px(width)
    font = _font(px)
    pad = max(6, px // 2)
    sw = round(px * 1.2)
    # Swatches as _overlay_png tints a lit surface (shade ≈ 0.85 of the light grey)
    base = np.array([235, 232, 226], float) * 0.85
    orange = tuple(int(v) for v in base * 0.55 + np.array([183, 65, 14]) * 0.45)
    blue = tuple(int(v) for v in base * 0.6 + np.array([120, 140, 170]) * 0.4)
    row_h = sw + pad
    strip = Image.new("RGB", (width, 2 * pad + 3 * row_h + px), (255, 255, 255))
    d = ImageDraw.Draw(strip)
    x, y = pad, pad
    entries = [(orange, "spår som hittats"), (blue, "för brett för att mätas")]
    for col, label in entries:
        d.rectangle((x, y, x + sw, y + sw), fill=col, outline=(100, 100, 100))
        d.text((x + sw + pad // 2, y), label, fill=(30, 41, 59), font=font)
        x += sw + pad + int(d.textlength(label, font=font)) + 2 * pad
    r = 1.5 * max(1, sw / 10)
    cx, cy = x + sw / 2, y + sw / 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(120, 120, 120))
    d.text((x + sw + pad // 2, y), "bortsorterat snitt", fill=(30, 41, 59), font=font)
    # The angle scale
    y += row_h
    lo, hi = float(angle_range[0]), float(angle_range[1])
    title = f"godkänt snitt, färgat efter V-vinkel ({lo:g}–{hi:g}°, klippt i ändarna):"
    d.text((pad, y), title, fill=(30, 41, 59), font=font)
    y += row_h
    bar_w = max(60, width - 2 * pad)
    cmap = colormaps["viridis"]
    for i in range(bar_w):
        rr, gg, bb, _ = cmap(i / max(1, bar_w - 1))
        d.line((pad + i, y, pad + i, y + sw), fill=(int(rr * 255), int(gg * 255), int(bb * 255)))
    d.rectangle((pad, y, pad + bar_w - 1, y + sw), outline=(100, 100, 100))
    y += sw + 2
    for v in np.linspace(lo, hi, 6):
        tx = pad + (v - lo) / (hi - lo) * (bar_w - 1)
        lab = f"{v:g}°"
        tw = d.textlength(lab, font=font)
        d.text((min(max(pad, tx - tw / 2), width - pad - tw), y), lab, fill=(30, 41, 59), font=font)
    return strip


def png_with_meta(img, meta: dict, dpi: int | None = None) -> bytes:
    """PNG med texterna som iTXt (UTF-8): Title, Author, Copyright, Source, Description, Software, Creation Time,
    Comment (kompakt JSON)."""
    from PIL.PngImagePlugin import PngInfo
    info = PngInfo()
    for k, v in meta.items():
        if v is None or v == "":
            continue
        info.add_itxt(k, v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, separators=(",", ":")))
    buf = io.BytesIO()
    kw = {"dpi": (dpi, dpi)} if dpi else {}
    img.save(buf, format="PNG", pnginfo=info, optimize=True, **kw)
    return buf.getvalue()


def _decode_png(data: str, what: str = "bilden"):
    """En inbäddad bild ur analysen (data:image/png;base64,…). Bara PNG, högst MAX_IMAGE_BYTES och MAX_IMAGE_SIDE
    pixlar per sida; annars BadInput. Storleken kontrolleras innan bildpunkterna packas upp."""
    from PIL import Image
    if not isinstance(data, str) or not data:
        raise BadInput(f"{what} saknas")
    head, sep, body = data.partition(",")
    if sep:
        if not head.lower().startswith("data:image/png"):
            raise BadInput(f"{what} måste vara en PNG-bild")
        data = body
    if len(data) > MAX_IMAGE_BYTES * 4 // 3 + 4:
        raise BadInput(f"{what} är för stor (högst {MAX_IMAGE_BYTES // (1024 * 1024)} MB)")
    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as e:
        raise BadInput(f"{what} är inte giltig base64") from e
    if not raw.startswith(PNG_SIGNATURE):
        raise BadInput(f"{what} måste vara en PNG-bild")
    try:
        img = Image.open(io.BytesIO(raw), formats=["PNG"])
        if max(img.size) > MAX_IMAGE_SIDE:
            raise BadInput(f"{what} är för stor (högst {MAX_IMAGE_SIDE} pixlar per sida)")
        img.load()
    except BadInput:
        raise
    except Exception as e:
        raise BadInput(f"{what} kunde inte läsas som PNG") from e
    return img


def gray_image(gray: np.ndarray):
    """En gråskala 0–1 (rad 0 nederst, NaN = vit) som 8-bitarsbild på ytans eget rutnät, som render_relief gör den
    men utan uppskalning."""
    from PIL import Image
    img = np.nan_to_num(gray, nan=1.0)
    return Image.fromarray((np.flipud(np.clip(img, 0, 1)) * 255).astype(np.uint8))


def relief_images(surf) -> dict:
    """Strykljus från fyra håll (20° över ytan), relief (det mörkaste av de fyra, sträckt mellan 1:a och 99:e
    percentilen) och djup under referensytan (1 = i nivå, 0 = 99:e percentilen av djupet utanför kantzonen), som
    gråskalor 0–1 med rad 0 nederst. Används av render_relief och av exporten."""
    views = {name: surf.shaded(az, 20) for name, _, az in RAKING}
    # Relief: the darkest of the four directions makes every groove dark whatever its direction
    relief = np.nanmin(np.stack(list(views.values())), axis=0)
    relief = (relief - np.nanpercentile(relief, 1)) / max(np.nanpercentile(relief, 99) - np.nanpercentile(relief, 1), 1e-6)
    depth = np.clip(-surf.residual, 0, None)
    ref = float(np.nanpercentile(depth[surf.inner], 99)) if surf.inner.any() else 1.0
    depth_img = 1 - np.clip(depth / max(ref, 1e-6), 0, 1)
    depth_img[~surf.inner] = np.nan
    return {"relief": relief, "raking": views, "depth_img": depth_img, "depth_ref_mm": ref}


# ---- CSV and grids ---------------------------------------------------------------------------------------------------

def _cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return "" if not math.isfinite(v) else repr(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, (list, dict)):
        v = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    s = str(v)
    return '"' + s.replace('"', '""') + '"' if re.search(r'[",\n\r#]', s) else s


def csv_with_header(meta: list[tuple[str, str]], columns: list[str], rows: list[list]) -> bytes:
    """CSV med komma och decimalpunkt, källan först på rader som börjar med # (som web/src/lib/exportTable.ts:
    read.csv(comment.char = "#") och pandas.read_csv(comment = "#") hoppar över dem), med BOM för Excel."""
    head = [f"# {k}: {_one_line(v)}" if k else f"#   {_one_line(v)}" for k, v in meta]
    body = [",".join(_cell(c) for c in columns)] + [",".join(_cell(c) for c in r) for r in rows]
    return ("﻿" + "\r\n".join(head + body) + "\r\n").encode("utf-8")


def asc_grid(values: np.ndarray, cellsize: float, nodata: int = NODATA) -> bytes:
    """ESRI ASCII Grid: values med första raden överst, NaN som nodata, tre decimaler."""
    rows, cols = values.shape
    out = io.StringIO()
    out.write(f"ncols {cols}\nnrows {rows}\nxllcorner 0\nyllcorner 0\ncellsize {cellsize!r}\nNODATA_value {nodata}\n")
    for r in values:
        out.write(" ".join(str(nodata) if not np.isfinite(v) else f"{v:.3f}" for v in r.tolist()))
        out.write("\n")
    return out.getvalue().encode("ascii")


# ---- input -----------------------------------------------------------------------------------------------------------

def _finite(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def unit_vector(values) -> list[float] | None:
    """[x, y, z] som flyttal med längd > 0, annars None."""
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        return None
    try:
        v = [float(x) for x in values]
    except (TypeError, ValueError):
        return None
    return v if all(math.isfinite(x) for x in v) and float(np.linalg.norm(v)) > 0 else None


def view_normal(view: dict | None, analyses: list[dict]) -> tuple[list | None, list | None, str | None]:
    """Den ristade ytans normal och uppåtriktning, som stenrapporten väljer dem (api/routers/reports.py _view):
    en angiven vy, annars den första analysens normal i proveniensen, annars medelvärdet av snittens
    uppåtriktning. Returnerar (normal, up, källa) med källan 'angiven', 'analys' eller 'snitt', eller (None, None,
    None) när inget av dem finns."""
    v = view or {}
    if v.get("normal"):
        return v["normal"], v.get("up"), "angiven"
    for a in analyses:
        params = (a.get("provenance") or {}).get("parameters") or {}
        if params.get("normal"):
            return params["normal"], params.get("up"), "analys"
    ups = [s["up"] for a in analyses for s in a.get("slices") or [] if s.get("up")]
    if ups:
        return list(np.mean(np.asarray(ups, float), axis=0)), None, "snitt"
    return None, None, None


def analysis_mode(result: dict | None, fallback: str | None = None) -> str:
    """Mätformen ur analysens egen proveniens (parameters.mode), inte ur vilken flik som var öppen; fallback bara när
    analysen inte anger någon."""
    params = (((result or {}).get("provenance") or {}).get("parameters") or {})
    return MODES.get(params.get("mode")) or fallback or ""


def _check_vec(v, what: str):
    if v is not None and unit_vector(v) is None:
        raise BadInput(f"{what} måste vara [x, y, z] med tal")


def validate_result(result) -> dict:
    """Analysen som webbläsaren skickar: rätt typer och rimliga storlekar, annars BadInput (400). Talen ändras inte."""
    if result is None:
        return {}
    if not isinstance(result, dict):
        raise BadInput("result_json måste vara ett objekt.")
    slices = result.get("slices")
    if slices is not None:
        if not isinstance(slices, list):
            raise BadInput("slices måste vara en lista.")
        if len(slices) > MAX_SLICES:
            raise BadInput(f"Högst {MAX_SLICES} snitt kan exporteras.")
        for i, s in enumerate(slices):
            if not isinstance(s, dict):
                raise BadInput(f"Snitt {i + 1} är inte ett objekt.")
            for k in (*METRICS, "fit_r2", "position_mm", "halfwidth_mm", "img_x", "img_y"):
                if s.get(k) is not None and not (isinstance(s[k], (int, float)) and not isinstance(s[k], bool)):
                    raise BadInput(f"Snitt {i + 1}: {k} måste vara ett tal.")
            for k in ("point", "direction", "up"):
                if s.get(k) is not None and (not isinstance(s[k], list) or len(s[k]) != 3
                                             or not all(_finite(x) for x in s[k])):
                    raise BadInput(f"Snitt {i + 1}: {k} måste vara [x, y, z] med tal.")
            if s.get("accepted") is not None and not isinstance(s["accepted"], bool):
                raise BadInput(f"Snitt {i + 1}: accepted måste vara true eller false.")
            for k in ("rune_id", "stroke_id"):
                if s.get(k) is not None and (not isinstance(s[k], int) or isinstance(s[k], bool)):
                    raise BadInput(f"Snitt {i + 1}: {k} måste vara ett heltal.")
            p = s.get("profile")
            if p is not None:
                if not isinstance(p, dict) or not isinstance(p.get("x"), list) or not isinstance(p.get("z"), list):
                    raise BadInput(f"Snitt {i + 1}: profile måste ha listorna x och z.")
                if len(p["x"]) != len(p["z"]) or len(p["x"]) > MAX_PROFILE_POINTS:
                    raise BadInput(f"Snitt {i + 1}: profilens x och z måste vara lika långa (högst "
                                   f"{MAX_PROFILE_POINTS} punkter).")
                if not all(_finite(v) for v in p["x"]) or not all(_finite(v) for v in p["z"]):
                    raise BadInput(f"Snitt {i + 1}: profilen får bara innehålla tal.")
    for k in ("summary", "rune_summary", "tool_heuristic", "counts", "provenance", "depth_profile",
              "groove_map_scale"):
        if result.get(k) is not None and not isinstance(result[k], dict):
            raise BadInput(f"{k} måste vara ett objekt.")
    rs = result.get("rune_summary")
    if isinstance(rs, dict):
        met = rs.get("metrics")
        if met is not None and (not isinstance(met, dict)
                                or not all(v is None or isinstance(v, dict) for v in met.values())):
            raise BadInput("rune_summary.metrics måste vara ett objekt med ett objekt per mått.")
        if rs.get("n_runes") is not None and not _finite(rs["n_runes"]):
            raise BadInput("rune_summary.n_runes måste vara ett tal.")
    summ = result.get("summary")
    if isinstance(summ, dict) and not all(v is None or isinstance(v, dict) for v in summ.values()):
        raise BadInput("summary måste ha ett objekt per mått.")
    tool = result.get("tool_heuristic")
    if isinstance(tool, dict) and tool.get("adjustments") is not None and not isinstance(tool["adjustments"], list):
        raise BadInput("tool_heuristic.adjustments måste vara en lista.")
    for k in ("image_base64", "groove_map_base64"):
        if result.get(k) is not None and not isinstance(result[k], str):
            raise BadInput(f"{k} måste vara en bild som text (data:image/png;base64,…).")
    if result.get("runes") is not None and (not isinstance(result["runes"], list)
                                            or not all(isinstance(r, dict) for r in result["runes"])):
        raise BadInput("runes måste vara en lista av objekt.")
    dp = result.get("depth_profile")
    if isinstance(dp, dict):
        for k in ("distances", "depths"):
            if dp.get(k) is not None and (not isinstance(dp[k], list) or len(dp[k]) > MAX_SLICES
                                          or not all(v is None or _finite(v) for v in dp[k])):
                raise BadInput(f"depth_profile.{k} måste vara en lista med tal.")
    params = ((result.get("provenance") or {}).get("parameters"))
    if params is not None and not isinstance(params, dict):
        raise BadInput("provenance.parameters måste vara ett objekt.")
    if isinstance(params, dict):
        _check_vec(params.get("normal"), "provenance.parameters.normal")
        _check_vec(params.get("up"), "provenance.parameters.up")
    mesh = (result.get("provenance") or {}).get("mesh")
    if mesh is not None and not isinstance(mesh, dict):
        raise BadInput("provenance.mesh måste vara ett objekt.")
    for k in ("image_width", "image_height"):
        if result.get(k) is not None and not _finite(result[k]):
            raise BadInput(f"{k} måste vara ett tal.")
    return result


def validate_labels(labels, n_slices: int) -> list[str] | None:
    """Etiketterna från granskningen: en per snitt, 'rune', 'ornament', 'unknown' eller 'excluded' (null = 'unknown',
    som i fromSession). BadInput för annat."""
    if labels is None:
        return None
    if not isinstance(labels, list):
        raise BadInput("labels_json måste vara en lista.")
    if len(labels) > n_slices:
        raise BadInput("labels_json har fler etiketter än analysen har snitt.")
    bad = [x for x in labels if x is not None and x not in LABELS]
    if bad:
        raise BadInput("Okänd etikett i labels_json: " + ", ".join(sorted({str(x)[:20] for x in bad})))
    return labels


# ---- the export ------------------------------------------------------------------------------------------------------

def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def _measurable(s: dict) -> bool:
    return all(_finite(s.get(m)) for m in METRICS)


class _Context:
    """Allt som en export behöver veta om analysen, skanningen och ytan."""

    def __init__(self, *, mesh_entry, surface_factory, result, labels, signum, credit, view, mode, feature_type,
                 tool_fn=None):
        self.mesh_entry = mesh_entry
        self._surface_factory = surface_factory
        self._surf = None
        self._relief = None
        self.result = validate_result(result)
        self.signum = clean_signum(signum)
        self.sig = slug(self.signum)
        self.view = view or {}
        self.prov = self.result.get("provenance") or {}
        self.params = self.prov.get("parameters") or {}
        # The measuring form and feature type of the analysis itself; the form fields only when it states none
        self.mode = analysis_mode(self.result, mode)
        ft = self.prov.get("feature_type")
        self.feature_type = ft if ft in GROUP_ORDER else (feature_type or "rune")
        self.now = _now()
        self.slices = [s for s in (self.result.get("slices") or []) if isinstance(s, dict)]
        # The whole automatic analysis with the researcher's labels (not a selection already used from it)
        self.auto = (self.mode == "auto" and isinstance(self.result.get("counts"), dict)
                     and "selection" not in self.params)
        self.labels = validate_labels(labels, len(self.slices)) if self.auto else None
        # The groups as the stone report gets them (fromSession): accepted slices that are not excluded, by label;
        # the slices measured in each (every metric finite, as stone_report.build_facts keeps them)
        if self.auto:
            by: dict[str, list[dict]] = {}
            for i, s in enumerate(self.slices):
                lab = self.label_of(i)
                if s.get("accepted") is not True or lab == "excluded":
                    continue
                by.setdefault(lab, []).append(s)
            self.groups = {g: by[g] for g in GROUP_ORDER if by.get(g)}
        else:
            self.groups = {self.feature_type: [s for s in self.slices if s.get("accepted", True) is not False]}
            self.groups = {g: v for g, v in self.groups.items() if v}
        self.measured = [s for g in self.groups.values() for s in g if _measurable(s)]
        self._tool_fn = tool_fn
        mi = (self.prov.get("mesh") or {})
        einfo = (mesh_entry.info if mesh_entry is not None else {}) or {}
        self.mesh = {k: mi.get(k) or einfo.get(k) for k in ("filename", "sha256", "md5", "bytes", "centered_by")}
        self.credit = credit if credit is not None else credit_for_mesh(self.mesh)

    def label_of(self, i: int) -> str:
        """Snittets etikett som fromSession läser den: labels[i], annars 'unknown'."""
        lab = self.labels[i] if self.labels and i < len(self.labels) else None
        return lab or "unknown"

    @property
    def surf(self):
        if self._surf is None:
            if self._surface_factory is None:
                raise LookupError("ingen 3D-modell")
            self._surf = self._surface_factory()
        return self._surf

    @property
    def relief(self) -> dict:
        if self._relief is None:
            self._relief = relief_images(self.surf)
        return self._relief

    def surface_info(self) -> dict | None:
        if self._surf is None:
            return None
        s = self._surf
        return {"cell_mm": float(s.res), "normal": [float(v) for v in s.hf.n], "up": [float(v) for v in s.hf.v],
                "normal_source": self.view.get("normal_source"), "rows": int(s.H.shape[0]),
                "cols": int(s.H.shape[1])}

    # -- summaries
    def group_summaries(self) -> dict[str, dict]:
        """Sammanfattningarna per grupp. I den automatiska analysen räknas de om för forskarens grupper med
        projektets egna funktioner (src/stats: summarize_slices, och summarize_by_rune bara för gruppen 'rune' och
        bara när analysen mätte enbart runor, parameters.runes_only, som analysen själv gör; i andra grupper är
        rune_id den automatiska igenkänningens, som forskaren har avvisat); annars analysens egna, som de lagrats."""
        r = self.result
        if not self.auto:
            if not isinstance(r.get("summary"), dict) or not r["summary"]:
                return {}
            return {self.feature_type: {"summary": r["summary"], "rune_summary": r.get("rune_summary"),
                                        "tool_heuristic": r.get("tool_heuristic"), "n_slices": len(self.measured),
                                        "recomputed": False}}
        out = {}
        runes_only = self.params.get("runes_only") is True
        for g, sl in self.groups.items():
            summ = summarize_slices(sl)
            runes = (summarize_by_rune(sl) if g == "rune" and runes_only
                     and any(s.get("rune_id") is not None for s in sl) else None)
            tool = None
            angles = [s["apex_vinkel_deg"] for s in sl if _finite(s.get("apex_vinkel_deg"))]
            if self._tool_fn is not None and angles:
                tool = self._tool_fn(float(np.mean(angles)), self.params.get("meta_stone") or "",
                                     self.params.get("meta_weathering") or "")
            out[g] = {"summary": summ, "rune_summary": runes, "tool_heuristic": tool,
                      "n_slices": sum(1 for s in sl if _measurable(s)), "recomputed": True}
        return out

    # -- metadata
    def png_meta(self, what: str, description: str, scale: dict | None, pixel_mm: float | None = None,
                 surface: bool = True) -> dict:
        """PNG-texterna. pixel_mm anges bara för bilder där en pixel är en ruta med känd storlek (relief, strykljus,
        ristningskarta); figurerna har i stället axlar och skalstock i mm."""
        ds = self.credit.get("dataset") if self.credit.get("known") else None
        note = _one_line(self.credit.get("scan_note"))
        comment = {"mm_per_px": pixel_mm, "normal": None, "up": None, "normal_source": None}
        if surface and self._surf is not None:
            si = self.surface_info()
            comment.update({k: si[k] for k in ("normal", "up", "normal_source")})
            comment["surface_cell_mm"] = si["cell_mm"]
        comment.update({"mesh": {"filename": self.mesh["filename"], "sha256": self.mesh["sha256"]},
                        "scale": scale or {}, "method_version": METHOD_VERSION, "signum": self.signum or None,
                        "scan_identified": bool(ds), "scan_match": self.credit.get("match")})
        if ds:
            inst = f" ({ds['institution']})" if ds.get("institution") else ""
            lic = ds["license"] + (f" ({ds['license_url']})" if ds.get("license_url") else "")
            author = f"{APP_NAME} (beräknad); skanning: {ds['scanned_by']}{inst}"
            copyright_, source = f"{lic}, doi:{ds['doi']}", ds["citation"]
        else:
            # The exporter's own text, marked as theirs in every field (not only Copyright)
            author = (f"{APP_NAME} (beräknad); skanning enligt den som exporterade: {note}" if note
                      else f"{APP_NAME} (beräknad); skanning: okänd skannare")
            copyright_ = f"enligt den som exporterade: {note}" if note else "okänd licens"
            source = f"enligt den som exporterade: {note}" if note else ""
        return {
            "Title": f"{self.signum or 'Okänd sten'} – {what}",
            "Author": author,
            "Copyright": copyright_,
            "Source": source,
            "Description": f"{description} Bilden är beräknad i {APP_NAME} {APP_VERSION}, mätmetod {METHOD_VERSION}. "
                           f"{credit_line(self.credit)}",
            "Software": f"{APP_NAME} {APP_VERSION}",
            "Creation Time": self.now.isoformat(),
            "Comment": comment,
        }

    def specific_notes(self, groups: dict[str, dict] | None = None) -> list[str]:
        """Varningarna för just den här analysen: för få mätta runor eller snitt per grupp (limitations.specific)
        och avvikelser från Vitki-protokollet och dess anmärkningar (provenance.protocol)."""
        out = []
        for g, gs in (groups if groups is not None else self.group_summaries()).items():
            rs = gs.get("rune_summary")
            if isinstance(rs, dict):
                out += [f"{g}: {x}" for x in limitations.specific(n_runes=rs.get("n_runes"), n_slices=gs["n_slices"],
                                                                   runes_only=True)]
            else:
                out += [f"{g}: {x}" for x in limitations.specific(n_slices=gs["n_slices"])]
        pr = self.prov.get("protocol")
        if isinstance(pr, dict):
            as_list = lambda v: v if isinstance(v, list) else []  # noqa: E731 - the browser's data
            dev = [_one_line(x) for x in as_list(pr.get("deviations")) if isinstance(x, str)]
            if dev:
                out.append(f"Analysen avviker från Vitki-protokollet ({pr.get('version')}): {'; '.join(dev)}; den bör "
                           "bara jämföras med stenar mätta på samma sätt.")
            out += [f"Protokollet: {_one_line(x)}" for x in as_list(pr.get("notes")) if isinstance(x, str)]
        return out

    def csv_meta(self, title: str, notes: list[str] = ()) -> list[tuple[str, str]]:
        m = self.mesh
        fil = (f"{m['filename'] or 'okänt filnamn'} (SHA-256 {m['sha256']})" if m.get("sha256")
               else (m.get("filename") or "okänd"))
        method = self.prov.get("method_version") or METHOD_VERSION
        when = self.prov.get("timestamp")
        lines = [
            ("Tabell", f"{self.signum + ' – ' if self.signum else ''}{title}"),
            ("Källa", SOURCE),
            ("Exporterad från", EXPORTED_FROM),
            ("Datum", self.now.date().isoformat()),
            ("Programvara", f"{APP_NAME} {APP_VERSION}. {VITKI}"),
            ("Citering", CITE),
            ("Skanning", credit_value(self.credit)),
            ("Skanningsfil", fil),
            ("Mätform", self.mode or "okänd"),
            ("Mätmetod", f"{method}" + (f" (analysen gjord {when} med {self.prov.get('software', APP_NAME)} "
                                        f"{self.prov.get('version', '')})".replace(" )", ")") if when else "")),
            ("Parametrar", json.dumps(self.params, ensure_ascii=False, separators=(",", ":"))),
            ("Koordinater", COORDS + (f" {json.dumps(m['centered_by'])}" if m.get("centered_by") else "")),
        ]
        return lines + [("Not", n) for n in notes]

    def figure_png(self, b64: str, what: str, description: str, scale: dict | None, surface: bool = True) -> bytes:
        img = _decode_png(b64)
        out = _stack(img, credit_footer(img.width, credit_line(self.credit), img.mode))
        return png_with_meta(out, self.png_meta(what, description, scale, None, surface), dpi=FIGURE_DPI)


def _depth_heatmap(ctx):
    from src import stone_report
    surf = ctx.surf
    vmax = stone_report.depth_vmax(surf)
    png = ctx.figure_png(stone_report.depth_figure(surf), "djup under stenytan",
                         "Djup under referensytan (morfologisk stängning 20 mm, i nivå med ytan runt spåren) i mm; "
                         f"ljust = i nivå, svart = {vmax:.2f} mm eller djupare (99,5:e percentilen). Kantzonen "
                         "(10 mm) är utelämnad. Samma figur som stenrapportens djupkarta.",
                         {"vmax_mm": vmax, "percentile": 99.5, "colormap": "magma_r", "axes": "mm, med skalstock"})
    return [(f"{ctx.sig}_djup_under_stenytan.png", png, "image/png")]


def _depth_grid(ctx):
    from src import stone_report
    surf = ctx.surf
    depth = stone_report.depth_array(surf)
    grid = np.flipud(depth)  # first row = top of the image, as depth_figure draws it
    name = f"{ctx.sig}_djup_under_stenytan_mm"
    side = {
        "type": "vitki-depth-grid", "schema": 1, "signum": ctx.signum or None,
        "file": f"{name}.asc", "format": "ESRI ASCII Grid",
        "cellsize_mm": float(surf.res), "rows": int(grid.shape[0]), "cols": int(grid.shape[1]), "unit": "mm",
        "sign": "positivt = under referensytan (djup); 0 = i nivå med eller över referensytan",
        "reference_surface": ("morfologisk stängning 20 mm (src/auto_grooves.reference_surface), utjämnad 1 mm; "
                              "ligger i nivå med ytan runt spåren och spårkanterna"),
        "edge_zone_mm": 10.0,
        "nodata": NODATA, "nodata_meaning": "utanför skanningen eller i kantzonen (10 mm), där referensytan är osäker",
        "nodata_cells": int(np.count_nonzero(~np.isfinite(grid))),
        "first_row": "bildens överkant",
        "coordinates": ("x_mm från vänsterkanten, y_mm från nederkanten (xllcorner 0, yllcorner 0). En punkt p i den "
                        "centrerade 3D-modellen har u = p·basis.u, v = p·basis.v och höjd p·basis.n; x_mm = u − "
                        "origin_mm[0], y_mm = v − origin_mm[1]. Inte geografiska koordinater."),
        "origin_mm": [float(v) for v in surf.origin],
        "basis": {"u": [float(v) for v in surf.hf.u], "v": [float(v) for v in surf.hf.v],
                  "n": [float(v) for v in surf.hf.n]},
        "centered_by": ctx.mesh.get("centered_by"),
        "normal_source": ctx.view.get("normal_source"),
        "heatmap_vmax_mm": stone_report.depth_vmax(surf, depth),
        "mesh": {"filename": ctx.mesh.get("filename"), "sha256": ctx.mesh.get("sha256")},
        "software": f"{APP_NAME} {APP_VERSION}", "method_version": METHOD_VERSION,
        "created": ctx.now.isoformat(),
        "credit": _credit_block(ctx),
    }
    return [(f"{name}.asc", asc_grid(grid, float(surf.res)), "text/plain"),
            (f"{name}.json", _json_bytes(side), "application/json")]


def _relief(ctx):
    img = gray_image(ctx.relief["relief"])
    png = png_with_meta(img, ctx.png_meta(
        "relief", "Det mörkaste av fyra strykljus (20° över ytan), sträckt mellan stenens 1:a och 99:e percentil. "
                  "Gråtonen är inte ett mått i mm. En pixel är en ruta i ytans rutnät.",
        {"stretch_percentiles": [1, 99]}, float(ctx.surf.res)))
    return [(f"{ctx.sig}_relief.png", png, "image/png")]


def _raking(ctx):
    out = []
    for name, ascii_name, az in RAKING:
        img = gray_image(ctx.relief["raking"][name])
        png = png_with_meta(img, ctx.png_meta(
            f"strykljus från {name}", f"Digitalt strykljus från {name} i bilden (azimut {az}°, 20° över ytan). "
                                      "Väderstrecken avser bilden, inte stenen. En pixel är en ruta i ytans rutnät.",
            {"azimuth_deg": az, "altitude_deg": 20}, float(ctx.surf.res)))
        out.append((f"{ctx.sig}_strykljus_{ascii_name}.png", png, "image/png"))
    return out


def _groove_map(ctx):
    img = _decode_png(ctx.result["groove_map_base64"], "ristningskartan")
    sc = ctx.result.get("groove_map_scale")
    ok = isinstance(sc, dict) and _finite(sc.get("black_mm")) and _finite(sc.get("threshold_mm"))
    scale = ({"black_mm": sc.get("black_mm"), "threshold_mm": sc.get("threshold_mm"), "grid_mm": sc.get("grid_mm"),
              "mm_per_px": sc.get("mm_per_px")} if ok else {"note": OLD_SCALE})
    black = (f"svart = {sc['black_mm']:.2f} mm eller djupare (95:e percentilen av djupen i rutorna som ligger djupare "
             f"än tröskeln {sc['threshold_mm']:.2f} mm)" if ok else f"svart = stenens djupaste spår ({OLD_SCALE})")
    meta = ctx.png_meta("ristningskarta", f"Spårdjupet i den automatiska analysens rutnät som gråskala; vitt = i nivå "
                                          f"med referensytan, {black}. Samma läge och storlek som granskningsbilden. "
                                          "Kantzonen och branta partier, som analysen inte mätte i, är med; "
                                          "svartpunkten kan sättas av skanningens kant, så runorna kan se "
                                          "mellangrå ut.",
                        scale, sc.get("mm_per_px") if ok and _finite(sc.get("mm_per_px")) else None, surface=False)
    meta["Comment"].update({"normal": ctx.params.get("normal"), "up": ctx.params.get("up"), "normal_source": "analys"})
    return [(f"{ctx.sig}_ristningskarta.png", png_with_meta(img, meta), "image/png")]


def _review_image(ctx):
    img = _decode_png(ctx.result["image_base64"], "granskningsbilden").convert("RGB")
    rng = ctx.result.get("angle_color_range")
    rng = list(rng) if isinstance(rng, (list, tuple)) and len(rng) == 2 and all(_finite(v) for v in rng) \
        and rng[1] > rng[0] else [30, 130]
    out = _stack(img, legend_strip(img.width, rng), credit_footer(img.width, credit_line(ctx.credit)))
    meta = ctx.png_meta("granskningsbild", "Den automatiska analysens granskningsbild med teckenförklaring under. "
                                           "Bildens övre del är oförändrad, så img_x och img_y i mättabellen gäller. "
                                           "Bilden visar analysens egen sortering, inte forskarens etiketter.",
                        {"angle_range": list(rng), "image_width": img.width, "image_height": img.height},
                        surface=False)
    meta["Comment"].update({"normal": ctx.params.get("normal"), "up": ctx.params.get("up"), "normal_source": "analys"})
    return [(f"{ctx.sig}_granskningsbild.png", png_with_meta(out, meta), "image/png")]


def _picks(ctx):
    from src import stone_report
    picks = stone_report._pick_profiles(ctx.measured)
    return picks, {i: stone_report.LETTERS[k] for k, i in enumerate(picks)}


def _positions_figure(ctx):
    from src import stone_report
    _, marked = _picks(ctx)
    angles = [s["apex_vinkel_deg"] for s in ctx.measured if s.get("point")]
    png = ctx.figure_png(stone_report.overview_figure(ctx.surf, ctx.measured, marked), "snittens läge och V-vinkel",
                         "Tvärsnittens positioner på strykljusbilden, färgade efter V-vinkel (stenens egna värden). "
                         "Bokstäverna hänvisar till tvärsnittsprofilerna.",
                         {"angle_range": [min(angles), max(angles)], "colormap": "viridis"})
    return [(f"{ctx.sig}_snittpositioner_v_vinkel.png", png, "image/png")]


def _spatial_figure(ctx):
    from src import stone_report
    b64 = stone_report.spatial_figure(ctx.surf, ctx.measured)
    if b64 is None:
        raise _Skip("färre än 3 snitt med läge")
    rng = {m: [min(s[m] for s in ctx.measured if s.get("point")), max(s[m] for s in ctx.measured if s.get("point"))]
           for m in ("spårdjup_mm", "spårbredd_mm", "ytråhet_mm")}
    png = ctx.figure_png(b64, "spårdjup, spårbredd och ytråhet", "Tvärsnittens spårdjup, spårbredd och ytråhet (mm), "
                         "ritade där de mättes.", {"ranges_mm": rng})
    return [(f"{ctx.sig}_djup_bredd_ytrahet.png", png, "image/png")]


def _profiles_figure(ctx):
    from src import stone_report
    picks, _ = _picks(ctx)
    h = ctx.params.get("harmonize_mm")
    b64 = stone_report.profiles_figure(ctx.measured, picks, h if _finite(h) else None)
    if b64 is None:
        raise _Skip("inga tvärsnittsprofiler")
    png = ctx.figure_png(b64, "tvärsnittsprofiler", "Representativa tvärsnitt från minsta till största V-vinkel; "
                         "punkter = uppmätt profil, röda linjer = anpassade väggar, streckad linje = spårkanternas "
                         "nivå (medel av de högsta punkterna strax utanför spårets kanter), som figurens höjd räknas "
                         "från. Lika skala på axlarna.", {"axes": "lika skala, mm"}, surface=False)
    return [(f"{ctx.sig}_tvarsnittsprofiler.png", png, "image/png")]


SLICE_COLUMNS = ["slice", "mode", "feature_type", "label", "accepted", "reason", "rune_id", "stroke_id", "feature",
                 "position_mm", *METRICS, "fit_r2", "halfwidth_mm", "point_x", "point_y", "point_z", "dir_x", "dir_y",
                 "dir_z", "up_x", "up_y", "up_z", "img_x", "img_y", "method_version", "mesh_sha256"]


def _label(ctx, i: int):
    """Etiketten i tabellerna: forskarens i den automatiska analysen (som fromSession), annars analysens typ."""
    return ctx.label_of(i) if ctx.auto else ctx.feature_type


def _xyz(v):
    return list(v)[:3] if isinstance(v, (list, tuple)) and len(v) >= 3 else [None, None, None]


def _slices_csv(ctx):
    method = ctx.prov.get("method_version") or METHOD_VERSION
    sha = ctx.mesh.get("sha256")
    rows = []
    for i, s in enumerate(ctx.slices):
        # In the automatic analysis the group is the researcher's label; the analysis' own feature type only says
        # what it measured (runes only or all grooves), so it is not written per slice next to the label
        rows.append([i + 1, ctx.mode, None if ctx.auto else ctx.feature_type, _label(ctx, i), s.get("accepted", True),
                     s.get("reason"),
                     s.get("rune_id"), s.get("stroke_id"), s.get("feature"), s.get("position_mm"),
                     *[s.get(m) for m in METRICS], s.get("fit_r2"), s.get("halfwidth_mm"),
                     *_xyz(s.get("point")), *_xyz(s.get("direction")), *_xyz(s.get("up")),
                     s.get("img_x"), s.get("img_y"), method, sha])
    notes = ["Vinklar i grader, längder i mm. Tomma celler: måttet finns inte i den här mätformen eller snittet "
             "sorterades bort innan det mättes.",
             "Snitt i samma runa är inte oberoende mätningar; använd sammanfattningen per runa för stenens värde."]
    if ctx.auto:
        min_r2 = ctx.params.get("min_fit_r2")
        scope = ("bara spår som känns igen som runor" if ctx.prov.get("feature_type") == "rune" else
                 "alla spår, inte bara de som känns igen som runor")
        notes += ["label är din etikett från granskningen (rune, ornament, unknown, excluded; saknas den räknas "
                  "snittet som unknown, som i stenrapporten). Sammanfattningen och figurerna räknar bara godkända "
                  "snitt som inte är excluded, grupperade efter label.",
                  f"feature_type är tom, eftersom label är snittets grupp. Den automatiska analysen mätte {scope}.",
                  "img_x och img_y är pixlar i granskningsbilden (origo uppe till vänster).",
                  "position_mm är provpunktens ordningsnummer över hela stenen gånger snittavståndet"
                  + (f" ({ctx.params['spacing_mm']} mm)" if _finite(ctx.params.get("spacing_mm")) else "")
                  + ", inte ett avstånd längs ett spår.",
                  f"Den automatiska analysen sorterade bort snitt med fit_r2 under {min_r2 if min_r2 is not None else 0.8}."]
    else:
        notes.append("Den här mätformen sorterar inte bort snitt på fit_r2.")
    return [(f"{ctx.sig}_snitt.csv", csv_with_header(ctx.csv_meta("tvärsnitt", notes), SLICE_COLUMNS, rows),
             "text/csv; charset=utf-8")]


SUMMARY_COLUMNS = ["grupp", "nivå", "mått", "n", "medel", "sd", "ki95_lag", "ki95_hog", "min", "max", "icc",
                   "n_runor", "n_snitt"]


def _ci(s):
    ci = s.get("ci95")
    return list(ci)[:2] if isinstance(ci, (list, tuple)) and len(ci) >= 2 else [None, None]


def _summary_csv(ctx):
    rows, notes = [], []
    groups = ctx.group_summaries()
    for g, gs in groups.items():
        summ = gs.get("summary") or {}
        for m in METRICS:
            s = summ.get(m)
            if isinstance(s, dict):
                rows.append([g, "per_snitt", m, s.get("n"), s.get("mean"), s.get("sd"), *_ci(s), s.get("min"),
                             s.get("max"), None, None, s.get("n")])
        rs = gs.get("rune_summary")
        if isinstance(rs, dict):
            for m in METRICS:
                s = (rs.get("metrics") or {}).get(m)
                if isinstance(s, dict):
                    rows.append([g, "per_runa", m, s.get("n"), s.get("mean"), s.get("sd"), *_ci(s), s.get("min"),
                                 s.get("max"), s.get("icc"), rs.get("n_runes"), s.get("n_slices")])
    notes.append("per_snitt räknar varje tvärsnitt som en mätning; intervallet blir för smalt, eftersom snitten i en "
                 "runa liknar varandra. per_runa räknar varje runa som en mätning (n = antal runor) och ger stenens "
                 "värde.")
    notes.append("icc skattas ur en envägs variansanalys och kan bli negativ när snitten i samma runa skiljer sig minst "
                 "lika mycket som runorna sinsemellan; ett negativt värde läses som ingen skillnad mellan runorna.")
    if ctx.auto:
        notes.append("Räknat om för dina grupper (grupp = label i mättabellen) med src/stats (summarize_slices, "
                     "summarize_by_rune): godkända snitt, utan dem du märkt som excluded. Analysens egen "
                     "sammanfattning över alla godkända snitt finns i hela analysen (JSON).")
    notes.append(f"Riktmärke: minst {limitations.MIN_RUNES_DESCRIBE} mätta runor för att beskriva en sten och minst "
                 f"{limitations.MIN_RUNES_COMPARE} för att jämföra stenar.")
    notes += ctx.specific_notes(groups)
    for g, gs in groups.items():
        tool = gs.get("tool_heuristic")
        if isinstance(tool, dict):
            adj = "; ".join(str(a) for a in tool.get("adjustments") or []) or "inga justeringar"
            notes.append(f"{g}: verktyg (tumregel, inte kalibrerad): {tool.get('label')}; gräns "
                         f"{tool.get('threshold_deg')}° ({adj}). {tool.get('note') or ''}")
    return [(f"{ctx.sig}_sammanfattning.csv", csv_with_header(ctx.csv_meta("sammanfattning", notes), SUMMARY_COLUMNS,
                                                              rows), "text/csv; charset=utf-8")]


RUNE_COLUMNS = ["rune_id", "n_strokes", "height_mm", "n_slices", "box_x0", "box_y0", "box_x1", "box_y1"]


def _runes_csv(ctx):
    w, h = ctx.result.get("image_width"), ctx.result.get("image_height")
    rows = []
    for r in ctx.result.get("runes") or []:
        box = r.get("box") if isinstance(r.get("box"), (list, tuple)) and len(r.get("box")) == 4 else None
        px = ([box[0] * w, box[1] * h, box[2] * w, box[3] * h] if box and all(_finite(v) for v in box)
              and _finite(w) and _finite(h) else [None] * 4)
        rows.append([r.get("id"), r.get("n_strokes"), r.get("height_mm"), r.get("n_slices"), *px])
    c = ctx.result.get("counts") or {}
    notes = [f"{k}: {c.get(k)}" for k in ("candidates", "accepted", "rejected", "runes_identified", "runes_measured",
                                         "groove_area_mm2", "wide_area_mm2") if k in c]
    if isinstance(c.get("strokes"), dict):
        notes.append("strokes: " + ", ".join(f"{k} {v}" for k, v in c["strokes"].items()))
    if isinstance(c.get("rejection_reasons"), dict):
        notes += [f"rejection_reason: {k}: {v}" for k, v in c["rejection_reasons"].items()]
    notes += ["En runa är här en grupp sammanhängande raka streck, inte en igenkänd runa; igenkänningen är inte "
              "validerad. box_* är rutan i granskningsbildens pixlar (origo uppe till vänster). n_slices är analysens "
              "godkända snitt i runan, före dina etiketter."]
    return [(f"{ctx.sig}_runor.csv", csv_with_header(ctx.csv_meta("runor och kvalitetskontroll", notes), RUNE_COLUMNS,
                                                     rows), "text/csv; charset=utf-8")]


def _profiles_csv(ctx):
    rows = []
    for i, s in enumerate(ctx.slices):
        p = s.get("profile")
        if not isinstance(p, dict):
            continue
        for j, (x, z) in enumerate(zip(p.get("x") or [], p.get("z") or [], strict=False)):
            rows.append([i + 1, _label(ctx, i), s.get("accepted", True), j, x, z])
    notes = ["x tvärs över spåret och z i höjdled, mm, med mätpunkten som nollpunkt; råprofilen innan utjämning "
             "(src/slice_analysis.raw_profile, 4 decimaler). slice hänvisar till raden i mättabellen."]
    return [(f"{ctx.sig}_profiler.csv", csv_with_header(ctx.csv_meta("tvärsnittsprofiler", notes),
                                                        ["slice", "label", "accepted", "i", "x_mm", "z_mm"], rows),
             "text/csv; charset=utf-8")]


def _length_profile_csv(ctx):
    dp = ctx.result["depth_profile"]
    rows = [[d, z] for d, z in zip(dp.get("distances") or [], dp.get("depths") or [], strict=False)]
    notes = ["Avstånd längs den ritade banan (mm) och spårdjupet i varje snitt (mm)."]
    return [(f"{ctx.sig}_langdprofil.csv", csv_with_header(ctx.csv_meta("längdprofil", notes),
                                                           ["distance_mm", "spårdjup_mm"], rows),
             "text/csv; charset=utf-8")]


def _credit_block(ctx) -> dict:
    c = ctx.credit
    return {"known": bool(c.get("known")), "match": c.get("match"), "file": c.get("file"),
            "dataset": c.get("dataset"), "credit_text": c.get("credit_text"),
            "scan_note": _one_line(c.get("scan_note")) or None, "computed_note": COMPUTED_NOTE,
            "line": credit_line(c)}


def _strip_images(result: dict) -> dict:
    return {k: v for k, v in result.items() if k not in ("image_base64", "groove_map_base64")}


def _json_bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")


def _export_block(ctx, items, files=None, skipped=None) -> dict:
    out = {"timestamp": ctx.now.isoformat(), "vitki_version": APP_VERSION, "software": APP_NAME,
           "method_version": METHOD_VERSION, "analysis_method_version": ctx.prov.get("method_version"),
           "mode": ctx.mode, "items": list(items)}
    if files is not None:
        out["files"] = files
    if skipped is not None:
        out["skipped"] = [{"id": i, "reason": r} for i, r in skipped]
    si = ctx.surface_info()
    if si:
        out["surface"] = si
    return out


def _full_json(ctx, items):
    obj = {"type": "vitki-groove-export", "schema": 1, "signum": ctx.signum or None, "mode": ctx.mode,
           "feature_type": ctx.feature_type, "result": _strip_images(ctx.result)}
    if ctx.auto:
        obj["labels"] = [ctx.label_of(i) for i in range(len(ctx.slices))]
        obj["groups"] = {g: {"n_slices": gs["n_slices"], "summary": gs["summary"], "rune_summary": gs["rune_summary"],
                             "tool_heuristic": gs["tool_heuristic"]} for g, gs in ctx.group_summaries().items()}
    obj.update({"credit": _credit_block(ctx), "export": _export_block(ctx, items)})
    return [(f"{ctx.sig}_analys.json", _json_bytes(obj), "application/json")]


class _Skip(Exception):
    pass


def _why_not(ctx: _Context, item: str) -> str | None:
    """Varför ett val inte kan exporteras för den här analysen, eller None."""
    r = ctx.result
    if item in IMAGE_ITEMS and ctx._surface_factory is None:
        return "ingen 3D-modell"
    if item == "groove_map" and not (ctx.auto and r.get("groove_map_base64")):
        return "ingen ristningskarta (bara automatisk analys)"
    if item == "review_image" and not (ctx.auto and r.get("image_base64")):
        return "ingen granskningsbild (bara automatisk analys)"
    with_point = sum(1 for s in ctx.measured if s.get("point"))
    if item == "positions_figure" and with_point < 1:
        return "inget godkänt snitt med läge på stenen"
    if item == "spatial_figure" and with_point < 3:
        return "färre än 3 snitt med läge"
    if item == "profiles_figure" and not any(s.get("profile") for s in ctx.measured):
        return "inga tvärsnittsprofiler"
    if item == "profiles_csv" and not any(isinstance(s.get("profile"), dict) for s in ctx.slices):
        return "inga tvärsnittsprofiler"
    if item in ("slices_csv", "full_json") and not ctx.slices:
        return "ingen analys med snitt"
    if item == "summary_csv" and not ctx.group_summaries():
        return ("inga godkända snitt utanför de uteslutna" if ctx.auto
                else "ingen sammanfattning (inga godkända snitt)")
    if item == "runes_csv" and not (ctx.auto and r.get("runes")):
        return "inga runor (bara automatisk analys)"
    if item == "length_profile_csv" and not (isinstance(r.get("depth_profile"), dict)
                                             and r["depth_profile"].get("distances")):
        return "ingen längdprofil (bara mätning längs en ritad bana)"
    return None


BUILDERS: dict[str, Callable] = {
    "depth_heatmap": _depth_heatmap, "depth_grid": _depth_grid, "relief": _relief, "raking": _raking,
    "groove_map": _groove_map, "review_image": _review_image, "positions_figure": _positions_figure,
    "spatial_figure": _spatial_figure, "profiles_figure": _profiles_figure, "slices_csv": _slices_csv,
    "summary_csv": _summary_csv, "runes_csv": _runes_csv, "profiles_csv": _profiles_csv,
    "length_profile_csv": _length_profile_csv,
}


def parse_items(raw: str) -> list[str]:
    """'a,b' -> ['a', 'b'] i ITEMS ordning, utan dubbletter. ValueError för okända id."""
    ids = [x.strip() for x in (raw or "").split(",") if x.strip()]
    unknown = [x[:40] for x in ids if x not in BY_ID]
    if unknown:
        raise BadInput("Okänt exportval: " + ", ".join(unknown[:10]))
    if not ids:
        raise BadInput("Välj minst en fil att exportera.")
    return [x["id"] for x in ITEMS if x["id"] in ids]


def _build(items, *, mesh_entry=None, surface_factory=None, result=None, labels=None, signum=None, credit=None,
           view=None, mode=None, feature_type="rune", tool_fn=None):
    ctx = _Context(mesh_entry=mesh_entry, surface_factory=surface_factory, result=result, labels=labels,
                   signum=signum, credit=credit, view=view, mode=mode, feature_type=feature_type, tool_fn=tool_fn)
    tagged, skipped = [], []
    for item in items:
        if item not in BY_ID:
            raise BadInput(f"Okänt exportval: {item}")
        why = _why_not(ctx, item)
        if why:
            skipped.append((item, why))
            continue
        try:
            out = _full_json(ctx, items) if item == "full_json" else BUILDERS[item](ctx)
        except _Skip as e:
            skipped.append((item, str(e)))
            continue
        except (TypeError, AttributeError) as e:
            # A result whose fields have the wrong shape for this file (validate_result checks the common ones):
            # the browser's data, so 400 rather than a server error
            raise BadInput(f"Analysen har ett oväntat format för {BY_ID[item]['label'].lower()}.") from e
        tagged += [(n, d, m, item) for n, d, m in out]
    return ctx, tagged, skipped


def build(items, **kw):
    """Filerna för de valda exporterna: (files [(namn, bytes, medietyp)], skipped [(id, skäl)]).

    Nyckelord: mesh_entry, surface_factory, result, labels, signum, credit, view, mode, feature_type, tool_fn.
    credit är None som standard: då räknas krediteringen ut ur skanningsfilen (credit_for_mesh). surface_factory
    bygger ytan (stone_report.Surface) första gången en bild behöver den; alla bilder delar samma yta. Val vars
    underlag saknas hoppas över med ett skäl i stället för att ge fel. BadInput för felaktiga indata."""
    _, tagged, skipped = _build(items, **kw)
    return [(n, d, m) for n, d, m, _ in tagged], skipped


def readme_text(ctx: _Context, items, files, skipped) -> str:
    """README.txt i ZIP-paketet: vad varje fil är, enheter, skalor, koordinater, normalen, begränsningar,
    krediteringen och hur Vitki citeras. Texterna är desamma som appens hjälptext (ITEMS)."""
    by_item: dict[str, list[str]] = {}
    for name, item in files:
        by_item.setdefault(item, []).append(name)
    out = [f"Export från {APP_NAME} {APP_VERSION} – huggspårsanalys", "=" * 60, ""]
    out += [f"Sten: {ctx.signum or '(inget signum angivet)'}", f"Skapad: {ctx.now.isoformat()} (UTC)",
            f"Mätmetod: {METHOD_VERSION}" + (f" (analysen: {ctx.prov['method_version']})"
                                             if ctx.prov.get("method_version") else ""),
            f"Mätform: {ctx.mode or 'okänd'}"]
    if ctx.mesh.get("filename") or ctx.mesh.get("sha256"):
        out.append(f"Skanningsfil: {ctx.mesh.get('filename') or 'okänt namn'}"
                   + (f", SHA-256 {ctx.mesh['sha256']}" if ctx.mesh.get("sha256") else ""))
    out += ["", _wrap_text(README_INTRO), "", "SKANNINGEN – VEM SOM SKA KREDITERAS", "-" * 40,
            _wrap_text(credit_line(ctx.credit, FILES_NOTE))]
    ds = ctx.credit.get("dataset") if ctx.credit.get("known") else None
    if ds:
        f = ctx.credit.get("file") or {}
        out += [f"Citera datamängden: {ds['citation']}",
                f"Licens: {ds['license']}" + (f" ({ds['license_url']})" if ds.get("license_url") else ""),
                _wrap_text(f"Filen {f.get('name')} känns igen som en av datamängdens publicerade filer "
                           f"(jämfört med {ctx.credit.get('match')})."
                           + (" Bara filnamn och storlek kunde jämföras, inte kontrollsumman; kontrollera att det "
                              "är originalfilen." if ctx.credit.get("match") == "filnamn och storlek" else ""))]
    elif (ctx.credit.get("scan_note") or "").strip():
        out.append(_wrap_text("Krediteringen ovan är skriven av den som exporterade filerna; Vitki har inte "
                              "kunnat känna igen skanningen som en av de öppna datamängder appen känner till."))
    else:
        out.append(_wrap_text("Vitki känner inte igen skanningsfilen som en av de öppna datamängder appen känner "
                              "till, och ingen har angett vem som skannat stenen. Ta reda på det innan filerna delas."))
    out += ["Skicka med den här filen om du delar bilderna vidare.", "", "FILERNA", "-" * 40]
    for item in items:
        if item not in by_item:
            continue
        x = BY_ID[item]
        out += ["", f"{x['label']}", "  " + ", ".join(by_item[item]), _wrap_text(x["explanation"], indent="  ")]
    out += ["", "README.txt", _wrap_text("Den här filen.", indent="  "),
            "", "kalla.json", _wrap_text("Proveniensen i maskinläsbar form: programversion, mätmetod, skanningsfil "
                                         "med SHA-256, inställningar, ytans normal och upplösning, vem som skannat "
                                         "stenen och vilka val som hoppades över.", indent="  ")]
    if skipped:
        out += ["", "HOPPADES ÖVER", "-" * 40] + [f"  {BY_ID[i]['label']}: {r}" for i, r in skipped]
    si = ctx.surface_info()
    out += ["", "BILDERNA UR SKANNINGEN", "-" * 40]
    if si:
        n = ", ".join(f"{v:.4f}" for v in si["normal"])
        u = ", ".join(f"{v:.4f}" for v in si["up"])
        src = NORMAL_SOURCES.get(si["normal_source"], si["normal_source"] or "okänd")
        out += [_wrap_text(f"Ytan är sedd längs normalen ({n}), med uppåt i bilden ({u}); normalen är {src}. "
                           "Stenrapporten väljer normalen på samma sätt, så bilderna stämmer med dess figurer för "
                           f"samma analys. Rutnätet har {si['cols']} × {si['rows']} rutor på {si['cell_mm']:.4f} mm. "
                           "I reliefen, strykljuset och rutnätet (.asc) är en pixel eller ett tal en ruta, utan "
                           "uppskalning. Värmekartan och figurerna över snitten är diagram med axlar och skalstock i "
                           "mm; deras pixlar har ingen fast storlek i mm.", indent="  ")]
    else:
        out.append("  Inga bilder ur skanningen i det här paketet.")
    out += [_wrap_text("Tre olika gråskalor/färgskalor används, och bara värmekartan och rutnätet kan läsas i mm. "
                       "Värmekartans färgskala slutar vid stenens 99,5:e percentil av djupet; djupbilden i appen är "
                       "svart vid 99:e percentilen; ristningskartan är svart vid 95:e percentilen av djupen i de "
                       "rutor som ligger djupare än analysens tröskel. Allt som är djupare än toppen får samma färg. "
                       "Ristningskartans svartpunkt kan sättas av skanningens kant, så runorna kan se mellangrå ut. "
                       "Djupet räknas från en referensyta i nivå med ytan runt spåren och spårkanterna. Tvärsnittens "
                       "spårdjup är ofta 10–40 % större än kartans, ibland mindre, eftersom tvärsnitten mäts i en tät "
                       "profil från spårkanten till botten medan kartan är ett grövre rutnät där varje ruta har den "
                       "högsta punkten i sin ruta och den smala botten i ett spår sällan träffas exakt. Ta därför "
                       "spårdjup ur mättabellen. Branta partier, sprickor och vittringsgropar kan se ut som djupa "
                       "spår.", indent="  ")]
    if ctx.auto:
        counts = {g: len(v) for g, v in ctx.groups.items()}
        excluded = sum(1 for i, s_ in enumerate(ctx.slices) if s_.get("accepted") is True
                       and ctx.label_of(i) == "excluded")
        out += ["", "DINA ETIKETTER", "-" * 40,
                _wrap_text("Den automatiska analysen exporteras med etiketterna från granskningen, som stenrapporten "
                           "läser dem: godkända snitt grupperade efter etikett ("
                           + ", ".join(f"{g} {k}" for g, k in counts.items()) + f"), {excluded} uteslutna. "
                           "Sammanfattningen och figurerna över snitten räknar bara grupperna; mättabellen och "
                           "hela analysen har alla snitt med sin etikett.", indent="  ")]
    out += ["", "LÄSA TABELLERNA", "-" * 40,
            _wrap_text("CSV-filerna har komma som avgränsare, punkt som decimaltecken och UTF-8 med BOM (så att Excel "
                       "läser å, ä och ö rätt). Raderna som börjar med # anger källa och proveniens. I R:", indent="  "),
            '    read.csv("fil.csv", comment.char = "#", fileEncoding = "UTF-8-BOM")',
            "  I Python:", '    pandas.read_csv("fil.csv", comment="#", encoding="utf-8-sig")',
            _wrap_text("Rutnätet (.asc) öppnas med terra::rast() i R, rasterio i Python eller direkt i QGIS; "
                       "cellstorleken i filhuvudet är mm, och −9999 betyder att värde saknas.", indent="  ")]
    out += ["", "BEGRÄNSNINGAR", "-" * 40, _wrap_text(README_CAVEAT, indent="  ")]
    out += [_wrap_text(f"- {x}", indent="  ") for x in ctx.specific_notes()]
    lims = limitations.select(["grooves", "software"] + (["auto"] if ctx.auto else []))
    out += [_wrap_text(f"- {x['title']}. {x['short']}", indent="  ") for x in lims]
    out += ["", "CITERA VITKI", "-" * 40, _wrap_text(f"Vitki, version {APP_VERSION}. Programvara. "
                                                     "https://vitkirunor.se (källkod: https://github.com/Precatio/runes). "
                                                     + CITE, indent="  "), ""]
    return "\r\n".join(out) + "\r\n"


def _wrap_text(text: str, width: int = 100, indent: str = "") -> str:
    import textwrap
    return textwrap.fill(_one_line(text), width=width, initial_indent=indent, subsequent_indent=indent)


def kalla_json(ctx: _Context, items, files, skipped) -> dict:
    """kalla.json: proveniensen och krediteringen i maskinläsbar form."""
    return {"type": "vitki-groove-export-provenance", "schema": 1, "signum": ctx.signum or None, "mode": ctx.mode,
            "feature_type": ctx.feature_type,
            "mesh": ctx.mesh, "credit": _credit_block(ctx),
            "export": _export_block(ctx, items, files=[{"name": n, "item": i} for n, i in files], skipped=skipped),
            "analysis_provenance": ctx.prov}


def bundle(ctx: _Context, items, files, skipped) -> tuple[str, bytes]:
    """ZIP med en mapp som innehåller filerna, README.txt och kalla.json."""
    folder = f"{ctx.sig}_vitki_export_{ctx.now.date().isoformat()}"
    named = [(n, it) for n, _, _, it in files]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data, _, _ in files:
            z.writestr(f"{folder}/{name}", data)
        z.writestr(f"{folder}/README.txt", readme_text(ctx, items, named, skipped).encode("utf-8"))
        z.writestr(f"{folder}/kalla.json", _json_bytes(kalla_json(ctx, items, named, skipped)))
    return f"{folder}.zip", buf.getvalue()


def export(items, *, as_zip: bool = False, **kw) -> dict:
    """Hela exporten: {name, data, media, files, skipped}. En enda fil skickas som den är, annars en ZIP med
    README.txt och kalla.json; reliefen och ristningskartan (NO_FOOTER, utan synlig kreditering) kommer alltid i en
    ZIP. LookupError när inget av de valda kunde exporteras."""
    ctx, tagged, skipped = _build(items, **kw)
    if not tagged:
        raise LookupError("Inget av de valda kan exporteras för den här analysen.")
    if len(tagged) == 1 and not as_zip and tagged[0][3] not in NO_FOOTER:
        name, data, media, _ = tagged[0]
    else:
        name, data = bundle(ctx, items, tagged, skipped)
        media = "application/zip"
    return {"name": name, "data": data, "media": media, "files": [n for n, _, _, _ in tagged], "skipped": skipped,
            "surface": ctx.surface_info()}
