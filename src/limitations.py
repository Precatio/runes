"""Kända brister i Vitkis metoder – en enda lista som följer med varje analys (se METHODS.md, 18).

Listan visas under analyssidorna i appen, står i varje rapport (alla publiceringsformer) och sparas i
proveniensen för varje mätning. När en brist åtgärdas ändras den här, och VERSION höjs.

Varje post har en akademisk text, en kort populär text, vad som behövs för att åtgärda bristen och de
sammanhang den gäller:
  grooves     huggspårsmått över huvud taget
  auto        automatisk spåranalys (runigenkänning, urval)
  comparison  jämförelser mellan stenar och mot mätkorpusen
  attribution ristarattribuering och syntes
  statistics  statistiska analyser och p-värden
  research    Forskningsluckor och automatiska fynd
  ai          AI-läsningar, AI-bedömningar och AI-text
  rundata     uppgifter ur Samnordisk runtextdatabas
  r           korpusanalyserna i R
  software    programvaran som helhet
"""
from __future__ import annotations

VERSION = "2026-10-10"

# Riktvärden för antal mätta runor (avsnitt 2 i METHODS.md)
MIN_RUNES_DESCRIBE = 10
MIN_RUNES_COMPARE = 20

LIMITATIONS = [
    {"key": "validity", "contexts": {"grooves", "comparison", "attribution"},
     "title": "Måtten är inte validerade som spår av ristarens hand",
     "text": "Huggspårsmåtten beskriver spårens form men är inte visade att skilja ristare åt. När den automatiska "
             "analysen kördes på Kitzler Åhfeldts 36 skanningar från Södermanland (2026) återskapades inte hennes "
             "indelning i grupper, och bergarten påverkade måtten mer än ristaren; ett svagare samband med Rundatas "
             "ristare fanns kvar efter kontroll för bergart (utforskande). Samma sak gällde när bara runorna mättes "
             "enligt Vitki-protokollet (groove-5): hennes Rak 1 och Rak 2 skildes inte åt (p 0,43), medan ristar- och "
             "materialsignalen kvarstod. Skillnader mellan stenar kan därför bero på "
             "bergart, vittring och skanning lika väl som på ristare.",
     "short": "Måtten visar hur spåren är huggna, men det är ännu inte visat att de skiljer ristare åt – bergart och "
              "vittring påverkar mycket.",
     "needed": "Stenar med känd ristare på samma bergart, jämförelse med Groove Measure-data och gärna experimentella "
               "ristningar med kända ristare och verktyg."},
    {"key": "weak_metrics", "contexts": {"grooves", "comparison"},
     "title": "Bottenradie och asymmetri är osäkra mått",
     "text": "Bottenradien beror fortfarande på skanningens punkttäthet (r = 0,44 mellan stenar) och skiljer knappt "
             "stenar åt. Asymmetrin varierar så mycket mellan snitt och runor att stenens medelvärde är osäkert "
             "(tillförlitlighet 0,75 med 10 runor, 0,9 först med 30) och ändras när analysen ändras (ICC 0,40 i "
             "robusthetsstudien). V-vinkel, djup, bredd och djup/bredd är stabilare.",
     "short": "Två av måtten, bottenradie och asymmetri, är för osäkra för att lita på.",
     "needed": "Bättre bottenmodell och test på skanningar av samma sten med olika punkttäthet."},
    {"key": "reliability", "contexts": {"grooves", "comparison"},
     "title": "Ingen sten är mätt i oberoende skanningar",
     "text": "Robusthetsstudien (METHODS.md 1e, åtta stenar) visar att stenens medelvärden för vinkel, djup, bredd och "
             "djup/bredd står sig när rutnät, ytnormal, känslighet och skanningens täthet ändras (ICC 0,95–0,98), men "
             "vilka ställen som mäts ändras mycket, samma ställe skiljer ca 2° i vinkel, djupet beror på ytnormalen och "
             "glesa skanningar ger upp till 9° annan vinkel. Ingen sten har mätts i två oberoende skanningar, och manuell "
             "och automatisk mätning på samma ställen på Sö 113 skilde i median 6°. Valideringen på syntetiska stenar "
             "(idealiska V-spår) visar att beräkningen är rätt, inte att knackade, U-formade och vittrade spår mäts rätt. "
             "Lav och ommålning påverkar också resultatet.",
     "short": "Resultatet för en hel sten står sig när analysen ändras, men samma sten har inte mätts i två olika "
              "skanningar, och glesa skanningar ger sämre resultat.",
     "needed": "Test–omtest med oberoende skanningar av samma stenar, och manuell mot automatisk mätning; samma rutnät "
               "och känslighet för alla stenar som jämförs."},
    {"key": "groove_measure", "contexts": {"grooves", "comparison"},
     "title": "Inte jämförbart med tidigare 3D-studier utan kalibrering",
     "text": "Måtten är inte verifierade som likvärdiga med Groove Measure-variablerna i Kitzler Åhfeldts studier "
             "(t.ex. hennes 'ideal depth' räknas annorlunda), och urvalet skiljer sig: hon valde de bäst bevarade "
             "spåren, medan den automatiska analysen mäter alla igenkända runor och därför får med mer vittring.",
     "short": "Siffrorna kan inte direkt jämföras med tidigare forskares mätningar.",
     "needed": "Samma referensstenar mätta med båda metoderna."},
    {"key": "rune_detection", "contexts": {"auto"},
     "title": "Runigenkänningen är inte utvärderad",
     "text": "Vilka spår som räknas som runor avgörs av regler som justerats för hand på Sö 113 och Sö 128, inte "
             "prövats mot handmärkta stenar, så träffsäkerheten (andel mätta streck som verkligen är runor, andel runor "
             "som hittas) är okänd. Antalet igenkända runor på 19 skanningar var i median 0,9 gånger antalet runor i "
             "Rundatas translitterering men varierade från 0,3 (grunda, vittrade runor som faller sönder, t.ex. Sö 160 "
             "och Sö 206) till 1,5 (Sö 143, där korsarmar bitvis togs för runor); på Sö 371, utan läsbara runor i "
             "Rundata, hittades sex. Slinglinjer som brutits av vittring kan räknas som runor, och runor kan delas eller "
             "slås ihop. Granska alltid granskningsbilden.",
     "short": "Programmet som letar upp runorna kan missa runor och ibland ta fel; det är inte utvärderat.",
     "needed": "Handmärkta facit för 8–10 stenar som inte använts för att justera reglerna (facit-läget i 3D-vyn, "
               "scripts/evaluate_rune_detection.py), med låsta regler."},
    {"key": "sample_size", "contexts": {"auto", "comparison"},
     "title": f"Gränserna {MIN_RUNES_DESCRIBE} och {MIN_RUNES_COMPARE} runor är riktvärden",
     "text": f"Riktvärdena ({MIN_RUNES_DESCRIBE} runor för att beskriva en sten, {MIN_RUNES_COMPARE} för att jämföra "
             "stenar) bygger på 18 stenar mätta med samma metod, bland dem de två som runigenkänningen justerades på. "
             "Skillnaderna mellan stenarna omfattar bergart och punkttäthet, vilket får tillförlitligheten att se "
             "bättre ut än den är, och igenkänningstestet jämförde två halvor av samma skanning. För att skilja "
             "ristare på samma bergart behövs fler runor.",
     "short": f"Hur många runor som räcker ({MIN_RUNES_DESCRIBE}–{MIN_RUNES_COMPARE}) är en tumregel, inte en standard.",
     "needed": "Ny beräkning när test–omtest och stenar med känd ristare på samma bergart finns."},
    {"key": "attribution_circular", "contexts": {"attribution", "statistics"},
     "title": "Attribueringen riskerar att bli cirkulär",
     "text": "Rundatas ristaruppgifter är hypoteser i litteraturen, i Mälardalen främst Axelsons (1993), som själv vägde "
             "in stil, stavning och geografi – samma slags drag som modellerna använder. Korsvalideringen mäter därför "
             "överensstämmelse med tidigare bedömningar, inte med en oberoende sanning.",
     "short": "Datorn jämför med tidigare forskares gissningar om ristare, och de gissningarna kan vara fel.",
     "needed": "Prövning på signerade stenar som inte använts i träningen och med variabler som inte låg bakom "
               "attribueringarna."},
    {"key": "cv_leakage", "contexts": {"attribution", "statistics", "r"},
     "title": "Träffsäkerheten beror på om platsen är känd",
     "text": "Vid slumpvis korsvalidering hamnar stenar från samma plats både i tränings- och testdata. R-modellen "
             "redovisas därför också med hela socknar och härader utelämnade: rätt ristare 72 % slumpvis, 68 % på en ny "
             "socken och 57 % i ett nytt härad (geografi ensamt 44, 40 och 30 %). Sannolikheterna för enskilda stenar "
             "kommer från den slumpvisa korsvalideringen och gäller en ny sten på en känd plats. Mätkorpusens "
             "attribuering (lämna-en-ute) är inte grupperad.",
     "short": "Modellen träffar rätt oftare på platser den redan känner till än på nya platser.",
     "needed": "Grupperad korsvalidering även för mätkorpusens attribuering, när korpusen är stor nog."},
    {"key": "exploratory", "contexts": {"statistics", "research", "attribution"},
     "title": "Många utforskande test på samma data",
     "text": "Plattformen kör många analyser på samma korpus (ortografi, språkdrag, R-modeller, Forskningsluckor, "
             "syntes). P-värdena är justerade inom varje analys men inte över plattformen som helhet. Ett automatiskt "
             "fynd är en hypotes att pröva med en förhandsbestämd analysplan, inte ett resultat.",
     "short": "Många samband prövas samtidigt, så en del av dem är slump; fynden är idéer att pröva vidare.",
     "needed": "Förregistrerade analysplaner för de hypoteser som ska publiceras."},
    {"key": "size", "contexts": {"research", "rundata"},
     "title": "Stenarnas mått är ofullständiga och ojämna",
     "text": "Måtten läses ur Kulturmiljöregistrets fritext och finns för knappt hälften av de vikingatida runstenarna "
             "(1 101 av 2 321 med höjd). Höjden är oftast höjden över mark, inte stenens hela längd, och stenar har "
             "flyttats och rests om. Fornlämningar med flera stenar som inte går att skilja åt är uteslutna, liksom "
             "fragment. Statusord och antal namn är grova mått på resarnas makt.",
     "short": "Stenarnas storlek är bara känd för ungefär hälften av dem, och oftast bara höjden över mark.",
     "needed": "Mått ur Sveriges runinskrifter eller nya mätningar för stenarna som saknas; hela höjden för resta stenar."},
    {"key": "ai", "contexts": {"ai"},
     "title": "AI-resultat är okalibrerade och kan vara påhittade",
     "text": "Blinda AI-läsningar och AI-bedömningar av stil är inte kalibrerade. I ett test på Sö 113 återgav blinda "
             "läsningar text ur minnet i stället för ur bilden, bland annat Jellingstenens text. Läsningarna valideras "
             "mot Rundata och kända inskrifter, och AI-text i rapporter märks, men inget AI-resultat bör bära ett "
             "argument.",
     "short": "AI kan hitta på; allt som AI skrivit eller läst är märkt och måste granskas.",
     "needed": "Kalibrering mot runologers läsningar av samma bilder."},
    {"key": "rundata", "contexts": {"rundata", "attribution", "research"},
     "title": "Rundata är en äldre utgåva",
     "text": "Appen bygger på Samnordisk runtextdatabas version 3.1 (2018); nyare förslag stäms av mot Runor (2020) och "
             "Wikidata men inte mot senare litteratur. Ristare, stilgrupper och dateringar är bedömningar, inte facit.",
     "short": "Uppgifterna om stenarna kommer från en databas från 2018 och kan vara inaktuella.",
     "needed": "Uppdatering till senaste utgåvan av Runor."},
    {"key": "software", "contexts": {"software", "grooves", "attribution", "comparison"},
     "title": "Programvaran är under utveckling",
     "text": "Mätmetoden har ändrats flera gånger (groove-1 till groove-5 under oktober 2026) efter att fel hittats. "
             "Resultat är bara jämförbara inom samma metodversion, som anges i varje analys. Koden är inte granskad av "
             "utomstående, och ingen låst version med DOI finns ännu.",
     "short": "Verktyget är nytt och ändras fortfarande; versionen anges så att resultaten kan upprepas.",
     "needed": "Låst version med DOI (Zenodo) och extern granskning av koden."},
]


def _r_items() -> list[dict]:
    from src.r_report import LIMITATIONS as R
    return [{"key": f"r{i + 1}", "contexts": {"r"}, "title": "Korpusanalyserna i R", "text": t, "short": t, "needed": ""}
            for i, t in enumerate(R)]


def select(contexts) -> list[dict]:
    """Bristerna som gäller något av sammanhangen, i listans ordning."""
    ctx = set(contexts)
    items = [x for x in LIMITATIONS if x["contexts"] & ctx]
    if "r" in ctx:
        items += _r_items()
    return items


def keys(contexts) -> list[str]:
    return [x["key"] for x in select(contexts)]


def as_json(items: list[dict]) -> list[dict]:
    return [{**{k: v for k, v in x.items() if k != "contexts"}, "contexts": sorted(x["contexts"])} for x in items]


def bullet(x: dict, popular: bool = False) -> str:
    if popular:
        return x["short"]
    return f"{x['title']}. {x['text']}" + (f" Behövs: {x['needed']}" if x["needed"] else "")


def specific(n_runes: int | None = None, n_slices: int | None = None, runes_only: bool = False) -> list[str]:
    """Varningar för just den här analysen."""
    out = []
    if runes_only and n_runes is not None:
        if n_runes < MIN_RUNES_DESCRIBE:
            out.append(f"Bara {n_runes} runor är mätta – färre än riktvärdet {MIN_RUNES_DESCRIBE} för att beskriva en sten; "
                       "stenens medelvärden är mycket osäkra.")
        elif n_runes < MIN_RUNES_COMPARE:
            out.append(f"{n_runes} runor är mätta – nog för att beskriva stenen men färre än riktvärdet "
                       f"{MIN_RUNES_COMPARE} för jämförelser med andra stenar.")
    elif n_slices is not None and n_slices < 30:
        out.append(f"Bara {n_slices} tvärsnitt är mätta; medelvärdena är osäkra.")
    return out
