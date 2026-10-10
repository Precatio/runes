"""Rapportmallar: samma stenanalys i olika publiceringsformer (se METHODS.md, 14e).

Stenrapporten (src/stone_report.py) byggs först i sin fullständiga form. En mall väljer sedan ut, ordnar
om och kompletterar dess avsnitt för en viss publiceringsform – från tidskriftsartikel och avhandlings-
kapitel till blogginlägg och antikvarisk dokumentationsrapport. Siffror, tabeller och figurer är desamma
som i stenrapporten; bara urval, ordning, rubriker och ton skiljer. Text som författaren måste skriva
själv markeras med hakparentes, och AI-text märks som i stenrapporten.
"""
from __future__ import annotations

import re

from src.academic import bullets, fmt, h, p, table
from src import limitations
from src.stone_report import FEATURE_TITLES, PERIODS, _carvers_text, report_limitations, sri_reference, sri_short

FILL = "[Fyll i: {}]"

# Riktvärden ur tidskrifternas författaranvisningar. De ändras; kontrollera alltid aktuella anvisningar.
VENUES = {
    "futhark": {"name": "Futhark: International Journal of Runic Studies", "language": "engelska (även tyska och skandinaviska språk)",
                "abstract_en": True, "keywords": True, "highlights": False, "citation": "författare–år (Harvard)",
                "words": "ca 6 000–10 000 ord", "note": "Runologisk tidskrift (Uppsala). För Futhark finns också ett färdigt "
                "manuspaket i Futharks mall (src/journal.py)."},
    "fornvannen": {"name": "Fornvännen. Journal of Swedish Antiquarian Research", "language": "svenska eller engelska",
                   "abstract_en": True, "keywords": False, "highlights": False, "citation": "författare–år",
                   "words": "ca 4 000–8 000 ord", "note": "Artiklar på svenska har en engelsk sammanfattning."},
    "vms": {"name": "Viking and Medieval Scandinavia", "language": "engelska", "abstract_en": True, "keywords": True,
            "highlights": False, "citation": "författare–år", "words": "ca 8 000–10 000 ord",
            "note": "Tvärvetenskaplig tidskrift för vikingatid och medeltid (Brepols)."},
    "jas": {"name": "Journal of Archaeological Science: Reports", "language": "engelska", "abstract_en": True,
            "keywords": True, "highlights": True, "citation": "författare–år", "words": "ca 6 000–8 000 ord",
            "note": "Naturvetenskapligt inriktad arkeologi (Elsevier); kräver 'highlights' (3–5 punkter, högst 85 tecken "
                    "vardera) och en datatillgänglighetsförklaring."},
    "dja": {"name": "Danish Journal of Archaeology", "language": "engelska", "abstract_en": True, "keywords": True,
            "highlights": False, "citation": "författare–år", "words": "ca 6 000–10 000 ord",
            "note": "Öppet tillgänglig; har publicerat 3D-studier av runstenar (Kitzler Åhfeldt & Imer 2019)."},
    "other": {"name": "Annan tidskrift", "language": "enligt tidskriften", "abstract_en": True, "keywords": True,
              "highlights": False, "citation": "enligt tidskriften", "words": "enligt tidskriften", "note": ""},
}

LEVELS = {"kandidat": "Kandidatuppsats", "magister": "Magisteruppsats", "master": "Masteruppsats"}

TEMPLATES = {
    "stenrapport": {
        "name": "Stenrapport (fullständig)", "group": "Vetenskapligt",
        "description": "Hela underlaget i artikelform: runologisk presentation, 3D-paradata, metod, alla resultat, "
                       "källkritik och bilagor. Utgångspunkten för de andra mallarna.",
        "audience": "Forskare och granskare", "length": "Allt underlag (ofta 20–40 sidor)",
        "structure": ["Sammanfattning", "Inledning", "Stenen och inskriften", "Material och metod", "Resultat",
                      "Diskussion", "Data och reproducerbarhet", "Referenser", "Bilagor"],
        "style": "Saklig, fullständig och reproducerbar.",
        "options": [], "ai": {}, "base_ai": True,
    },
    "tidskrift": {
        "name": "Artikel i forskningstidskrift", "group": "Vetenskapligt",
        "description": "Manus i IMRaD-form för en referentgranskad tidskrift: engelsk abstract, nyckelord, numrerade "
                       "avsnitt, datatillgänglighet och tilläggsmaterial i stället för bilagor.",
        "audience": "Referentgranskare och forskare", "length": "Enligt tidskriften (se riktvärden)",
        "structure": ["Titel och författare", "Abstract (engelska) och nyckelord", "1 Inledning", "2 Material",
                      "3 Metod", "4 Resultat", "5 Diskussion", "6 Slutsatser", "Datatillgänglighet", "Tack",
                      "Referenser", "Tilläggsmaterial"],
        "style": "Kortfattad och argumenterande; varje figur och tabell ska behövas för argumentet. "
                 "Bilagorna läggs som tilläggsmaterial (supplementary material).",
        "options": [{"key": "venue", "label": "Tidskrift", "type": "select",
                     "choices": {k: v["name"] for k, v in VENUES.items()}, "default": "futhark"}],
        "ai": {"abstract_en": "Abstract på engelska, 150–200 ord, utan siffror som inte finns i fakta",
               "keywords": "5–7 nyckelord på engelska, kommaseparerade",
               "highlights": "3–5 korta punkter på engelska (högst 85 tecken vardera), en per rad",
               "conclusions": "Slutsatser, 1 stycke på svenska: vad resultaten visar och inte visar"},
        "base_ai": True,
    },
    "uppsats": {
        "name": "Uppsats (kandidat, magister, master)", "group": "Utbildning",
        "description": "Självständigt arbete i arkeologi eller nordiska språk med svensk uppsatsdisposition: "
                       "titelsida, syfte och frågeställningar, forskningsöversikt, teori och metod, material, "
                       "resultat, diskussion, slutsatser och sammanfattning.",
        "audience": "Handledare, examinator och opponent", "length": "Kandidat ca 10 000–15 000 ord; magister/master längre",
        "structure": ["Titelsida", "Abstract (engelska)", "1 Inledning (bakgrund, syfte och frågeställningar, "
                      "avgränsningar)", "2 Forskningsöversikt", "3 Teori och metod", "4 Material", "5 Resultat",
                      "6 Diskussion", "7 Slutsatser", "8 Sammanfattning", "Referenser", "Bilagor"],
        "style": "Syfte, frågeställningar och teori formuleras av studenten – mallen markerar var. "
                 "Följ institutionens anvisningar för referenser (oftast Harvard) och layout.",
        "options": [{"key": "level", "label": "Nivå", "type": "select", "choices": LEVELS, "default": "kandidat"},
                    {"key": "university", "label": "Lärosäte och institution", "type": "text"},
                    {"key": "course", "label": "Kurs och termin", "type": "text"},
                    {"key": "supervisor", "label": "Handledare", "type": "text"}],
        "ai": {"abstract_en": "Abstract på engelska, 150–250 ord"},
        "base_ai": True,
    },
    "avhandling": {
        "name": "Avhandlingskapitel (monografi)", "group": "Vetenskapligt",
        "description": "Stenen som fallstudie i ett kapitel av en monografiavhandling: kapitelnumrerade avsnitt, "
                       "metoden refererad till avhandlingens metodkapitel, kapitelsammanfattning och alla data som "
                       "appendix. För en sammanläggningsavhandling används mallen Artikel i forskningstidskrift.",
        "audience": "Betygsnämnd, opponent och forskare", "length": "Ett kapitel (ofta 20–40 sidor)",
        "structure": ["Kapitel N: titel", "N.1 Inledning", "N.2 Stenen och inskriften", "N.3 Material och metod",
                      "N.4 Resultat", "N.5 Diskussion", "N.6 Sammanfattning av kapitlet", "Appendix"],
        "style": "Utförlig och självständig, med hänvisningar till avhandlingens övriga kapitel; inga förkortningar "
                 "av metoden som inte förklaras i metodkapitlet.",
        "options": [{"key": "chapter", "label": "Kapitelnummer", "type": "text", "default": "5"},
                    {"key": "method_chapter", "label": "Metodkapitel", "type": "text", "default": "3"}],
        "ai": {"chapter_summary": "Kapitelsammanfattning, 1–2 stycken på svenska"},
        "base_ai": True,
    },
    "utgava": {
        "name": "Runologisk utgåva (SRI-stil)", "group": "Vetenskapligt",
        "description": "Stenen som artikel i en korpusutgåva i Sveriges runinskrifters tradition: placering och "
                       "historik, material och mått, ornamentik, inskrift (translitterering, normalisering, "
                       "översättning), kommentar, ristare och datering, och nu även huggteknik ur 3D-skanningen.",
        "audience": "Runologer", "length": "1–4 sidor per sten",
        "structure": ["Signum och plats", "Placering och historik", "Material och mått", "Ornamentik", "Inskrift",
                      "Kommentar", "Ristare och datering", "Huggteknik (3D)", "Litteratur"],
        "style": "Koncis och normaliserad; translitterering i fetstil, normalisering i kursiv. Kommentaren om "
                 "läsningen skrivs av runologen.",
        "options": [], "ai": {}, "base_ai": False,
    },
    "konferens": {
        "name": "Konferensabstract", "group": "Vetenskapligt",
        "description": "Kort abstract för runologiska symposier, nordiska runforskningsmöten eller arkeologiska "
                       "konferenser (t.ex. EAA).",
        "audience": "Programkommitté och konferensdeltagare", "length": "200–300 ord",
        "structure": ["Titel", "Författare och lärosäte", "Abstract", "Nyckelord"],
        "style": "Ett stycke: fråga, material och metod, huvudresultat, betydelse.",
        "options": [{"key": "language", "label": "Språk", "type": "select",
                     "choices": {"sv": "Svenska", "en": "Engelska"}, "default": "en"}],
        "ai": {"conference_abstract": "Konferensabstract, 200–300 ord, ett stycke, på det språk som anges",
               "keywords": "4–6 nyckelord på samma språk, kommaseparerade"},
        "base_ai": False,
    },
    "poster": {
        "name": "Poster", "group": "Vetenskapligt",
        "description": "Innehåll för en konferensposter: korta punkter om bakgrund, metod, resultat och slutsats, "
                       "två till tre figurer och en länk till data.",
        "audience": "Konferensbesökare", "length": "300–600 ord",
        "structure": ["Titel", "Bakgrund", "Metod", "Resultat (figurer)", "Slutsats", "Data och kontakt"],
        "style": "Punkter i stället för stycken; stora figurer; en tydlig huvudpoäng.",
        "options": [], "ai": {"poster_conclusion": "2–3 korta slutsatspunkter på svenska, en per rad"},
        "base_ai": False,
    },
    "blogg": {
        "name": "Blogginlägg (populärvetenskap)", "group": "Populärt",
        "description": "Populärvetenskaplig text för en blogg, en hembygdsförening eller ett museum: en lockande "
                       "ingress, korta stycken utan facktermer, några bilder och vägar att läsa mer.",
        "audience": "Allmänheten", "length": "600–1 200 ord",
        "structure": ["Rubrik", "Ingress", "Vad vi undersökte", "Så mätte vi", "Vad vi såg", "Hur säkert är det?",
                      "Läs mer"],
        "style": "Personlig men korrekt; förklara 3D-skanning och huggspår med vardagliga ord; inga tabeller; "
                 "säg tydligt vad som är osäkert.",
        "options": [], "base_ai": False,
        "ai": {"blog_title": "Lockande rubrik, högst 12 ord", "blog_lede": "Ingress, 2–3 meningar",
               "blog_what": "Vad vi undersökte och varför, 1–2 korta stycken", "blog_how": "Så mätte vi, 1–2 korta stycken utan facktermer",
               "blog_found": "Vad vi såg, 2–3 korta stycken med några avrundade siffror ur fakta",
               "blog_certainty": "Hur säkert är det, 1 kort stycke"},
    },
    "press": {
        "name": "Pressmeddelande", "group": "Populärt",
        "description": "Kort pressmeddelande om ett resultat: rubrik, ingress, brödtext, plats för citat, fakta om "
                       "stenen och kontaktuppgifter.",
        "audience": "Journalister", "length": "300–500 ord",
        "structure": ["Rubrik", "Ingress", "Brödtext", "Citat", "Fakta om stenen", "Om studien", "Kontakt"],
        "style": "Det viktigaste först; korta meningar; inga överdrifter – ett mätresultat är inte en sensation.",
        "options": [{"key": "contact", "label": "Kontaktperson (namn, e-post, telefon)", "type": "text"}],
        "ai": {"press_headline": "Rubrik, högst 10 ord, saklig", "press_lede": "Ingress, 1–2 meningar",
               "press_body": "Brödtext, 2–3 korta stycken"},
        "base_ai": False,
    },
    "antikvarisk": {
        "name": "Antikvarisk dokumentationsrapport", "group": "Kulturmiljö",
        "description": "Rapport för länsstyrelse, museum eller Riksantikvarieämbetet: administrativa uppgifter, "
                       "syfte, metod, resultat, bevarandetillstånd, rekommendationer och arkivering av filerna.",
        "audience": "Länsstyrelse, museum, Riksantikvarieämbetet", "length": "5–15 sidor",
        "structure": ["Administrativa uppgifter", "Bakgrund och syfte", "Metod", "Resultat",
                      "Bevarandetillstånd", "Rekommendationer", "Arkivering", "Referenser", "Bilagor"],
        "style": "Saklig och förvaltningsinriktad, följ beställarens och länsstyrelsens krav på rapporter. "
                 "Bevarandetillstånd och rekommendationer bedöms av en konservator eller antikvarie.",
        "options": [{"key": "site_id", "label": "Fornlämningsnummer (L-nr / RAÄ-nr)", "type": "text"},
                    {"key": "property", "label": "Fastighet", "type": "text"},
                    {"key": "commissioner", "label": "Beställare", "type": "text"},
                    {"key": "case_no", "label": "Diarienummer", "type": "text"},
                    {"key": "archive", "label": "Arkivering (var filerna förvaras)", "type": "text"}],
        "ai": {}, "base_ai": True,
    },
    "data": {
        "name": "Dataartikel / datapaket", "group": "Data",
        "description": "Beskrivning av mätdata och skanning för en datatidskrift (t.ex. Journal of Open "
                       "Archaeology Data) eller som README till ett arkiv som Zenodo: översikt, metod, "
                       "datamängden, licens och återanvändning.",
        "audience": "Forskare som vill återanvända data", "length": "1 500–3 000 ord",
        "structure": ["Översikt", "Metod (insamling, urval, kvalitetskontroll)", "Datamängden (filer, format, "
                      "licens, förvaring)", "Återanvändning", "Referenser"],
        "style": "Beskriv data, inte tolkningar; ange format, versioner, kontrollsummor och licens.",
        "options": [{"key": "repository", "label": "Arkiv och DOI", "type": "text"},
                    {"key": "license", "label": "Licens för data", "type": "text", "default": "CC BY 4.0"}],
        "ai": {"reuse": "Återanvändningspotential, 1 stycke på svenska"},
        "base_ai": False,
    },
}


def catalogue() -> list[dict]:
    """Mallarna för gränssnittet (utan byggfunktioner)."""
    return [{"key": k, **{f: v[f] for f in ("name", "group", "description", "audience", "length", "structure", "style",
                                            "options")}, "uses_ai": bool(v["ai"]) or v["base_ai"]}
            for k, v in TEMPLATES.items()]


def guide(key: str, options: dict) -> dict:
    t = TEMPLATES[key]
    out = {"name": t["name"], "audience": t["audience"], "length": t["length"], "style": t["style"]}
    if key == "tidskrift":
        v = VENUES.get(options.get("venue") or "futhark", VENUES["other"])
        out.update({"venue": v["name"], "language": v["language"], "citation": v["citation"], "length": v["words"],
                    "note": (v["note"] + " " if v["note"] else "") + "Riktvärdena kan ha ändrats – kontrollera "
                    "tidskriftens aktuella författaranvisningar."})
    return out


# ---- AI ------------------------------------------------------------------------------------

def ai_request(key: str, options: dict, facts_text: str, known_limits: list[str] | None = None) -> tuple[str, dict] | None:
    """Prompt och JSON-schema för mallens AI-fält (utöver stenrapportens sammanfattning, inledning och
    diskussion, som bara efterfrågas när mallen använder dem)."""
    t = TEMPLATES[key]
    fields = dict(t["ai"])
    if key == "tidskrift":
        v = VENUES.get(options.get("venue") or "futhark", VENUES["other"])
        if not v["highlights"]:
            fields.pop("highlights", None)
        if not v["keywords"]:
            fields.pop("keywords", None)
    if t["base_ai"]:
        fields = {"abstract": "Sammanfattning, 4–6 meningar på svenska",
                  "introduction": "Inledning, 1–2 stycken om syfte och material",
                  "discussion": "Diskussion, 2–3 stycken: vad resultaten visar, hur säkra de är och vad som behövs härnäst",
                  **fields}
    if not fields:
        return None
    lang = {"sv": "svenska", "en": "engelska"}.get(options.get("language") or "", "")
    tone = {"blogg": "populärvetenskaplig, levande men korrekt, utan facktermer",
            "press": "nyhetsmässig och saklig, utan överdrifter",
            "poster": "kort och punktvis"}.get(key, "akademisk och saklig, utan överdrifter")
    prompt = f"""
Du skriver delar av en text om en runsten i formen "{t['name']}" för målgruppen {t['audience'].lower()}.
Ton: {tone}.{f' Språk för abstract och nyckelord: {lang}.' if lang else ''}
Använd ENDAST fakta nedan. Hitta inte på stenar, ristare, siffror, litteratur eller slutsatser som inte följer
av fakta. Huggspårsmåtten säger något om hur spåren är huggna, inte vem som högg dem; var försiktig med
attribueringar och säg vad som är osäkert.

FAKTA:
{facts_text}

KÄNDA BRISTER I METODEN (ska framgå av texten; tona inte ned dem):
""" + "\n".join(f"- {x}" for x in (known_limits or [])) + """

Svara med JSON med dessa fält:
""" + "\n".join(f'- "{k}": {v}' for k, v in fields.items())
    schema = {"type": "object", "properties": {k: {"type": "string"} for k in fields}, "required": list(fields)}
    return prompt, schema


# ---- building blocks -----------------------------------------------------------------------

_KEYS = [("Sammanfattning", "abstract"), ("1. Inledning", "intro"), ("2. Stenen", "stone"),
         ("3. Material", "method"), ("4. Resultat", "results"), ("5. Diskussion", "discussion"),
         ("Data och reproducerbarhet", "data"), ("Tack", "ack"), ("Referenser", "refs"),
         ("Bilaga B", "workflow"), ("Bilaga", "appendix")]
AI_NOTE = "Avsnitt markerade som AI-genererade"


def split_sections(blocks: list[dict]) -> tuple[dict, dict[str, list[dict]], list[dict]]:
    """Stenrapportens block -> (titelblock, avsnitt efter nyckel utan rubriken, AI-anmärkning)."""
    title = blocks[0]
    sections: dict[str, list[dict]] = {}
    note: list[dict] = []
    key = None
    for b in blocks[1:]:
        if b["type"] == "paragraph" and b["text"].startswith(AI_NOTE):
            note.append(b)
            continue
        if b["type"] == "heading" and b["level"] == 1:
            key = next((k for prefix, k in _KEYS if b["text"].startswith(prefix)), b["text"])
            sections[key] = []
            continue
        if key is not None:
            sections[key].append(b)
    return title, sections, note


def _subsections(content: list[dict], prefix: str | None) -> list[dict]:
    """Numrerar om nivå 2-rubriker ("3.1 X" -> "<prefix>.1 X"); utan prefix tas numret bort."""
    out, k = [], 0
    for b in content:
        if b["type"] == "heading" and b["level"] == 2:
            k += 1
            text = re.sub(r"^\d+(\.\d+)+ ", "", b["text"])
            b = {**b, "text": f"{prefix}.{k} {text}" if prefix else text}
        out.append(b)
    return out


def _only(content: list[dict], keep: set[str]) -> list[dict]:
    """Bara de block vars nivå 2-rubrik (utan nummer) börjar med något i keep."""
    out, on = [], False
    for b in content:
        if b["type"] == "heading" and b["level"] == 2:
            on = any(re.sub(r"^\d+(\.\d+)+ ", "", b["text"]).startswith(k) for k in keep)
        if on:
            out.append(b)
    return out


def _figures(sections: dict, slugs: list[str], limit: int) -> list[dict]:
    figs = [b for c in sections.values() for b in c if b["type"] == "figure"]
    pick = [next((f for f in figs if f["name"].endswith(f"_{s}.png")), None) for s in slugs]
    return [f for f in pick if f][:limit]


def renumber(blocks: list[dict]) -> list[dict]:
    """Numrerar figurer och tabeller löpande igen efter urvalet och rättar hänvisningarna i texten."""
    maps = {"Figur": {}, "Tabell": {}}
    for b in blocks:
        if b["type"] in ("figure", "table"):
            kind = "Figur" if b["type"] == "figure" else "Tabell"
            m = re.match(rf"^{kind} (\d+)\. ", b.get("caption", ""))
            if m:
                new = len(maps[kind]) + 1
                maps[kind][m.group(1)] = str(new)
                b["caption"] = f"{kind} {new}. " + b["caption"][m.end():]
                if b["type"] == "figure":
                    b["name"] = re.sub(r"^figur\d+_", f"figur{new}_", b["name"])

    def fix(text: str) -> str:
        def one(m):
            kind = "Figur" if m.group(1).lower().startswith("fig") else "Tabell"
            nums = [maps[kind].get(n) for n in re.findall(r"\d+", m.group(2))]
            if not all(nums):
                return f"{m.group(1)} i den fullständiga stenrapporten"
            return m.group(1) + " " + " och ".join(nums)
        return re.sub(r"\b([Ff]igur(?:erna)?|[Tt]abell(?:en)?) (\d+(?: och \d+)?)\b", one, text)

    for b in blocks:
        if b["type"] == "paragraph":
            b["text"] = fix(b["text"])
        elif b["type"] == "list":
            b["items"] = [fix(i) for i in b["items"]]
    return blocks


def key_numbers(f: dict) -> dict:
    main = (f.get("summaries") or {}).get(f.get("main_feature")) or {}
    counts = f.get("counts") or {}
    rec = f.get("rundata") or {}
    get = lambda m, k="mean": (main.get(m) or {}).get(k)  # noqa: E731
    return {"signum": f.get("signum") or "stenen", "place": rec.get("place") or (f.get("meta") or {}).get("location") or "",
            "n_slices": len(f.get("all_slices") or []), "n_runes": counts.get("runes_measured"),
            "angle": get("apex_vinkel_deg"), "angle_sd": get("apex_vinkel_deg", "sd"), "depth": get("spårdjup_mm"),
            "width": get("spårbredd_mm"), "feature": FEATURE_TITLES.get(f.get("main_feature") or "", "spåren").lower(),
            "carver": _carvers_text(rec) if rec.get("carvers") else "",
            "carver_names": " och ".join(c["name"] for c in rec.get("carvers") or [] if c.get("name")),
            "style": rec.get("style") or "", "dating": PERIODS.get(rec.get("dating") or "", rec.get("dating")) or "",
            "translation": rec.get("translation_en") or "", "transliteration": rec.get("transliteration") or ""}


def _limits(f: dict, ai: dict, popular: bool = False, top: int | None = None) -> list[str]:
    """Kända brister och varningar för analysen, som punkter (populärt eller fullständigt)."""
    items, warnings = report_limitations(f, bool(ai))
    items = items[:top] if top else items
    return warnings + [limitations.bullet(x, popular) for x in items]


def _limits_section(f: dict, ai: dict, heading: str = "Kända brister") -> list[dict]:
    return [h(1, heading), p(f"Metodens kända brister (förteckning version {limitations.VERSION}, METHODS.md avsnitt 18) "
                             "som gäller den här analysen:"), bullets(_limits(f, ai))]


def _ai(ai: dict, key: str, fallback: str) -> dict:
    return p(ai[key], ai=True) if ai.get(key) else p(fallback)


def _lines(text: str) -> list[str]:
    return [re.sub(r"^[-•*\d.)\s]+", "", x).strip() for x in (text or "").splitlines() if x.strip()]


# ---- templates -----------------------------------------------------------------------------

def _journal(title, s, note, f, ai, opt):
    v = VENUES.get(opt.get("venue") or "futhark", VENUES["other"])
    out = [title]
    if v["highlights"]:
        out += [h(1, "Highlights"), bullets(_lines(ai.get("highlights")) or [FILL.format("3–5 highlights på engelska, högst 85 tecken vardera")])]
    out += [h(1, "Abstract"), _ai(ai, "abstract_en", FILL.format("abstract på engelska, 150–200 ord. Utkast på svenska: ")
                                  + " ".join(b["text"] for b in s.get("abstract", []) if b["type"] == "paragraph"))]
    if v["keywords"]:
        out += [p("Keywords: " + (ai.get("keywords") or FILL.format("5–7 nyckelord på engelska")), ai=bool(ai.get("keywords")))]
    out += [h(1, "Sammanfattning")] + s.get("abstract", [])
    out += [h(1, "1 Inledning")] + s.get("intro", [])
    out += [h(1, "2 Material")] + _subsections(s.get("stone", []), "2")
    out += [h(1, "3 Metod")] + _subsections(s.get("method", []), "3")
    out += [h(1, "4 Resultat")] + _subsections(s.get("results", []), "4")
    out += [h(1, "5 Diskussion")] + _subsections(s.get("discussion", []), "5")
    out += [h(1, "6 Slutsatser"), _ai(ai, "conclusions", FILL.format("slutsatser – vad resultaten visar och inte visar"))]
    out += [h(1, "Datatillgänglighet")] + s.get("data", [])
    out += [h(1, "Tack")] + s.get("ack", [])
    out += [h(1, "Referenser")] + s.get("refs", [])
    supp = s.get("appendix", []) + s.get("workflow", [])
    if supp:
        out += [h(1, "Tilläggsmaterial"),
                p("Följande lämnas som tilläggsmaterial (supplementary material) i stället för att tryckas: mått per "
                  "tvärsnitt" + (" och arbetsgången med känslighetsanalys och läsningar" if s.get("workflow") else "")
                  + ". Exportera dem från den fullständiga stenrapporten.")]
    return out + note


def _thesis_essay(title, s, note, f, ai, opt):
    level = LEVELS.get(opt.get("level") or "kandidat", "Uppsats")
    rows = [["Typ", level], ["Lärosäte och institution", opt.get("university") or FILL.format("lärosäte och institution")],
            ["Kurs och termin", opt.get("course") or FILL.format("kurs, högskolepoäng och termin")],
            ["Författare", title.get("author") or FILL.format("författare")],
            ["Handledare", opt.get("supervisor") or FILL.format("handledare")]]
    out = [title, table(["", ""], rows, "Titelsida."),
           h(1, "Abstract"), _ai(ai, "abstract_en", FILL.format("abstract på engelska, 150–250 ord")),
           p("Keywords: " + FILL.format("nyckelord")),
           h(1, "1 Inledning"), h(2, "1.1 Bakgrund")] + s.get("intro", []) + [
           h(2, "1.2 Syfte och frågeställningar"),
           p(FILL.format("syfte och 2–4 frågeställningar, t.ex. Vilka huggtekniska drag har ristningen? Stämmer de med "
                         "tidigare attribuering? Hur tillförlitliga är automatiska spårmått på en vittrad sten?")),
           h(2, "1.3 Avgränsningar"), p(FILL.format("avgränsningar i material, tid och metod")),
           h(1, "2 Forskningsöversikt")]
    research = _only(s.get("stone", []), {"Stenen i forskningsläget", "Inskriftens syfte"})
    out += _subsections(research, "2") if research else []
    out += [p(FILL.format("forskningsöversikt: runologisk forskning om stenen och ristaren, tidigare 3D-studier av "
                          "huggteknik (t.ex. Kitzler Åhfeldt 2002) och metodfrågor"))]
    out += [h(1, "3 Teori och metod"), p(FILL.format("teoretiska utgångspunkter, t.ex. hantverk och kroppslig kunskap, "
                                                     "ristarattribuering som hypotesprövning"))]
    out += _subsections(s.get("method", []), "3")
    stone = [b for b in s.get("stone", []) if b not in research]
    out += [h(1, "4 Material")] + _subsections(stone, "4")
    out += [h(1, "5 Resultat")] + _subsections(s.get("results", []), "5")
    out += [h(1, "6 Diskussion")] + _subsections(s.get("discussion", []), "6")
    out += [h(1, "7 Slutsatser"), p(FILL.format("svar på frågeställningarna, en i taget"))]
    out += [h(1, "8 Sammanfattning")] + s.get("abstract", [])
    out += [h(1, "Referenser")] + s.get("refs", [])
    app = s.get("appendix", []) + s.get("workflow", [])
    if app:
        out += [h(1, "Bilagor")] + app
    return out + note


def _thesis_chapter(title, s, note, f, ai, opt):
    n = str(opt.get("chapter") or "5").strip()
    mc = str(opt.get("method_chapter") or "3").strip()
    k = key_numbers(f)
    ch_title = re.sub(r":.*$", "", title["text"])
    out = [{**title, "text": f"Kapitel {n}. {ch_title}: en fallstudie"}]
    out += [h(1, f"{n}.1 Inledning")] + s.get("intro", [])
    out += [h(1, f"{n}.2 Stenen och inskriften")] + _subsections(s.get("stone", []), f"{n}.2")
    out += [h(1, f"{n}.3 Material och metod"),
            p(f"Metoden för 3D-dokumentation och spårmätning beskrivs i kapitel {mc}; här redovisas det som är "
              f"specifikt för {k['signum']}.")] + _subsections(s.get("method", []), f"{n}.3")
    out += [h(1, f"{n}.4 Resultat")] + _subsections(s.get("results", []), f"{n}.4")
    out += [h(1, f"{n}.5 Diskussion")] + _subsections(s.get("discussion", []), f"{n}.5")
    out += [h(1, f"{n}.6 Sammanfattning av kapitlet"),
            _ai(ai, "chapter_summary", FILL.format("kapitelsammanfattning och övergång till nästa kapitel"))]
    app = s.get("appendix", []) + s.get("workflow", []) + s.get("data", [])
    if app:
        out += [h(1, f"Appendix till kapitel {n}")] + app
    out += [h(1, "Referenser (till avhandlingens samlade referenslista)")] + s.get("refs", [])
    return out + note


def _edition(title, s, note, f, ai, opt):
    rec = f.get("rundata") or {}
    meta, cond = f.get("meta") or {}, f.get("condition") or {}
    k = key_numbers(f)
    loc = ", ".join(x for x in [rec.get("place"), rec.get("parish"), rec.get("district"), rec.get("municipality")] if x)
    out = [{**title, "text": f"{k['signum']}{', ' + loc if loc else ''}"}]
    out += [h(1, "Placering och historik"),
            p(", ".join(x for x in [rec.get("placement"), loc] if x) + "." if (rec.get("placement") or loc) else FILL.format("placering"))
            , p(FILL.format("fyndhistorik, flyttningar och tidigare avbildningar"))]
    out += [h(1, "Material och mått"),
            p(", ".join(x for x in [rec.get("object"), rec.get("material") or meta.get("stone")] if x) or FILL.format("material")),
            p(FILL.format("höjd, bredd och tjocklek; runornas höjd; slingans bredd"))]
    out += [h(1, "Ornamentik"), p((meta.get("ornamentation") or "") + (f" Stilgrupp {rec['style']} (Rundata)." if rec.get("style") else "")
                                  or FILL.format("ornamentik och stilgrupp"))]
    insc = [b for b in s.get("stone", []) if b["type"] == "inscription"]
    out += [h(1, "Inskrift")] + (insc or [p(FILL.format("translitterering, normalisering och översättning"))])
    reading = [b for b in s.get("results", []) if b["type"] == "paragraph" and "läsning" in b["text"].lower()][:2]
    out += [h(1, "Kommentar"), p(FILL.format("runologisk kommentar till läsning och tolkning"))] + reading
    out += [h(1, "Ristare och datering"),
            p("; ".join(x for x in [f"Ristare: {k['carver']}" if k["carver"] else "", f"datering: {k['dating']}" if k["dating"] else ""] if x)
              + "." if (k["carver"] or k["dating"]) else FILL.format("ristare och datering"))]
    tech = f"{k['n_slices']} tvärsnitt" + (f" i {k['n_runes']} runor" if k.get("n_runes") else "")
    out += [h(1, "Huggteknik (3D)"),
            p(f"Huggspåren mättes i en 3D-skanning ({tech}). V-vinkeln är i medel {fmt(k['angle'], 1)}° (SD "
              f"{fmt(k['angle_sd'], 1)}°), spårdjupet {fmt(k['depth'], 1)} mm och spårbredden {fmt(k['width'], 1)} mm."
              if k["angle"] is not None else "Inga godkända tvärsnitt.")]
    if cond.get("weathering") or meta.get("weathering"):
        out.append(p(f"Vittring: {cond.get('weathering') or meta.get('weathering')}."))
    out += _limits_section(f, ai, "Kända brister i huggteknikmätningen")
    out += [h(1, "Litteratur")] + s.get("refs", [])
    return out + note


def _conference(title, s, note, f, ai, opt):
    k = key_numbers(f)
    en = (opt.get("language") or "en") == "en"
    fallback = (f"{k['signum']}{' (' + k['place'] + ')' if k['place'] else ''} was documented with 3D scanning and "
                f"{k['n_slices']} groove cross-sections were measured automatically"
                + (f" in {k['n_runes']} runes" if k.get("n_runes") else "") + ". "
                + (f"The mean V-angle is {fmt(k['angle'], 1)}° and the mean depth {fmt(k['depth'], 1)} mm. " if k["angle"] is not None else "")
                + "[Fill in: the question, the main result and why it matters.]") if en else (
                f"{k['signum']}{' (' + k['place'] + ')' if k['place'] else ''} dokumenterades med 3D-skanning och "
                f"{k['n_slices']} tvärsnitt mättes automatiskt" + (f" i {k['n_runes']} runor" if k.get("n_runes") else "") + ". "
                + (f"V-vinkeln är i medel {fmt(k['angle'], 1)}° och djupet {fmt(k['depth'], 1)} mm. " if k["angle"] is not None else "")
                + FILL.format("frågan, huvudresultatet och varför det spelar roll") + ".")
    items, warnings = report_limitations(f, bool(ai))
    lim = " ".join(warnings[:1] + [x["short"] for x in items[:2]])
    return [title, h(1, "Abstract"), _ai(ai, "conference_abstract", fallback),
            p(("Limitations (in Swedish): " if en else "Begränsningar: ") + lim),
            p(("Keywords: " if en else "Nyckelord: ") + (ai.get("keywords") or FILL.format("4–6 nyckelord")),
              ai=bool(ai.get("keywords")))] + note


def _poster(title, s, note, f, ai, opt):
    k = key_numbers(f)
    res = [f"{k['n_slices']} tvärsnitt mätta automatiskt" + (f" i {k['n_runes']} runor" if k.get("n_runes") else "")]
    if k["angle"] is not None:
        res += [f"V-vinkel {fmt(k['angle'], 0)}° (SD {fmt(k['angle_sd'], 0)}°)", f"Spårdjup {fmt(k['depth'], 1)} mm, bredd {fmt(k['width'], 1)} mm"]
    out = [title,
           h(1, "Bakgrund"), bullets([f"{k['signum']}{', ' + k['place'] if k['place'] else ''}"
                                      + (f" – {k['carver_names']} enligt Rundata" if k["carver_names"] else ""),
                                      FILL.format("frågan i en mening")]),
           h(1, "Metod"), bullets(["3D-skanning av den ristade ytan",
                                   "Automatisk igenkänning av runorna; ornamentik och sprickor sorteras bort",
                                   "V-vinkel, djup och bredd mätta i tvärsnitt genom skanningen",
                                   "Medelvärden med runan som enhet"]),
           h(1, "Resultat"), bullets(res)]
    out += _figures(s, ["snittpositioner", "strykljus", "tvarsnitt", "jamforelse-korpus"], 3)
    out += [h(1, "Slutsats"), bullets(_lines(ai.get("poster_conclusion")) or [FILL.format("2–3 slutsatspunkter")])]
    if ai.get("poster_conclusion"):
        out[-1]["ai"] = True
    out += [h(1, "Begränsningar"), bullets(_limits(f, ai, popular=True, top=3))]
    out += [h(1, "Data och kontakt"), p(FILL.format("DOI eller länk till data, e-post, QR-kod"))]
    return out + note


def _blog(title, s, note, f, ai, opt):
    k = key_numbers(f)
    out = [{**title, "text": ai.get("blog_title") or f"Vad huggspåren på {k['signum']} berättar"}]
    out.append(_ai(ai, "blog_lede", f"Med en 3D-skanning går det att mäta exakt hur runorna på {k['signum']}"
                   f"{' i ' + k['place'] if k['place'] else ''} är huggna – hur djupt, hur brett och i vilken vinkel. "
                   "Här berättar vi vad mätningarna visar."))
    out += [h(1, "Vad vi undersökte"),
            _ai(ai, "blog_what", f"{k['signum']} är en runsten" + (f" som brukar knytas till ristaren {k['carver_names']}" if k["carver_names"] else "")
                + ". Vi ville se om spåren i stenen kan säga något om hur den höggs." )]
    insc = [b for b in s.get("stone", []) if b["type"] == "inscription"]
    if k["translation"]:
        out.append(p(f"Inskriften lyder i Samnordisk runtextdatabas engelska översättning: ”{k['translation'].strip()}”"))
    elif insc:
        out.append(insc[0])
    out += [h(1, "Så mätte vi"),
            _ai(ai, "blog_how", "En 3D-skanner mäter stenens yta på bråkdelen av en millimeter när. I datorn letar ett "
                "program upp runorna – men inte sprickor och ornament – och skär tvärs genom spåren med några "
                "millimeters mellanrum. I varje snitt mäts hur djupt spåret är och hur vida väggarna öppnar sig.")]
    out += _figures(s, ["strykljus", "snittpositioner"], 2)
    out += [h(1, "Vad vi såg"),
            _ai(ai, "blog_found", (f"Vi mätte {k['n_slices']} snitt" + (f" i {k['n_runes']} runor" if k.get("n_runes") else "")
                                   + (f". Spåren är i genomsnitt {fmt(k['depth'], 1)} mm djupa och väggarna möts i en "
                                      f"vinkel på omkring {fmt(k['angle'], 0)} grader." if k["angle"] is not None else ".")))]
    out += _figures(s, ["tvarsnitt"], 1)
    out += [h(1, "Hur säkert är det?"),
            _ai(ai, "blog_certainty", "Måtten säger hur spåren är huggna, inte vem som högg dem. Vittring, bergart och "
                "skanningens skärpa påverkar resultatet, så slutsatser om ristare kräver jämförelser med många stenar."),
            p("Det här vet vi att metoden ännu inte klarar:"), bullets(_limits(f, ai, popular=True))]
    sri = sri_reference(k["signum"])
    out += [h(1, "Läs mer"), bullets([x for x in [
        "Samnordisk runtextdatabas (Rundata): stenens text och uppgifter.",
        f"Sveriges runinskrifter ({sri_short(sri)})." if sri else "",
        "Laila Kitzler Åhfeldts studier av huggteknik med 3D-skanning.",
        "Mätmetoden: Vitki, https://github.com/Precatio/runes"] if x])]
    return out + note


def _press(title, s, note, f, ai, opt):
    k = key_numbers(f)
    out = [{**title, "text": "PRESSMEDDELANDE: " + (ai.get("press_headline") or f"Ny 3D-studie av {k['signum']}")}]
    out.append(_ai(ai, "press_lede", f"Runorna på {k['signum']}{' i ' + k['place'] if k['place'] else ''} har mätts "
                   "millimeter för millimeter med 3D-skanning. " + FILL.format("huvudresultatet i en mening")))
    out.append(_ai(ai, "press_body", (f"Studien omfattar {k['n_slices']} mätta tvärsnitt"
                                      + (f" i {k['n_runes']} runor" if k.get("n_runes") else "") + ". " + FILL.format("bakgrund och betydelse"))))
    out += [p("”" + FILL.format("citat från forskaren") + "”, säger " + (title.get("author") or FILL.format("namn")) + ".")]
    facts = [x for x in [f"Signum: {k['signum']}", f"Plats: {k['place']}" if k["place"] else "",
                         f"Ristare (Rundata): {k['carver']}" if k["carver"] else "", f"Stilgrupp: {k['style']}" if k["style"] else "",
                         f"Översättning: ”{k['translation']}”" if k["translation"] else ""] if x]
    out += [h(1, "Fakta om stenen"), bullets(facts),
            h(1, "Om studien"), p(f"Mätningarna är gjorda med det öppna forskningsverktyget Vitki. "
                                  + FILL.format("publicering, finansiering, samarbetspartner")),
            h(1, "Studiens begränsningar"), bullets(_limits(f, ai, popular=True, top=3)),
            h(1, "Kontakt"), p(opt.get("contact") or FILL.format("namn, e-post och telefon"))]
    return out + note


def _antiquarian(title, s, note, f, ai, opt):
    rec = f.get("rundata") or {}
    scan = f.get("scan") or {}
    cond = f.get("condition") or {}
    k = key_numbers(f)
    pm = (f.get("provenance") or {}).get("mesh") or {}
    admin = [["Signum", k["signum"]],
             ["Fornlämningsnummer", opt.get("site_id") or FILL.format("L-nummer i Fornsök / RAÄ-nummer")],
             ["Socken, kommun", ", ".join(x for x in [rec.get("parish"), rec.get("municipality")] if x) or FILL.format("socken och kommun")],
             ["Fastighet", opt.get("property") or FILL.format("fastighetsbeteckning")],
             ["Placering", rec.get("placement") or FILL.format("placering")],
             ["Beställare", opt.get("commissioner") or FILL.format("beställare")],
             ["Diarienummer", opt.get("case_no") or FILL.format("länsstyrelsens diarienummer")],
             ["Dokumentationsdatum", scan.get("date") or FILL.format("datum")],
             ["Utförare", ", ".join(x for x in [scan.get("scanned_by"), title.get("author")] if x) or FILL.format("utförare")],
             ["Rapportdatum", title.get("date") or ""]]
    out = [{**title, "text": f"{k['signum']}: dokumentation med 3D-skanning"}, h(1, "Administrativa uppgifter"),
           table(["", ""], admin, "Administrativa uppgifter."),
           h(1, "Bakgrund och syfte"), p(FILL.format("anledning till dokumentationen, t.ex. inför konservering, "
                                                    "flytt eller som underlag för forskning")),
           h(1, "Metod")] + _subsections(_only(s.get("method", []), {"3D-dokumentation", "Mätning av huggspår"}), None)
    out += [h(1, "Resultat")] + _subsections(_only(s.get("results", []), {"Ytan", "Spårmått"}), None)
    weathering = cond.get("weathering") or (f.get("meta") or {}).get("weathering")
    state = [x for x in [f"Vittring: {weathering}." if weathering else "", "Lavpåväxt noterad." if cond.get("lichen") else "",
                         "Stenen är ommålad." if cond.get("paint") else "", cond.get("notes") or ""] if x]
    out += [h(1, "Bevarandetillstånd"), bullets(state or [FILL.format("bevarandetillstånd")]),
            p("Djupkartan och strykljusbilderna ovan visar ytans tillstånd vid dokumentationstillfället och kan "
              "användas som referens vid framtida tillsyn. " + FILL.format("bedömning av konservator eller antikvarie")),
            h(1, "Rekommendationer"), p(FILL.format("rekommendationer för vård, tillsyn och ny dokumentation"))]
    out += _limits_section(f, ai, "Kända brister i metoden")
    files = [["Modellfil", pm.get("filename") or "–"], ["Kontrollsumma (SHA-256)", pm.get("sha256") or "–"],
             ["Licens", scan.get("license") or FILL.format("licens")],
             ["Förvaring", opt.get("archive") or FILL.format("arkiv eller museum där filerna förvaras")]]
    out += [h(1, "Arkivering"), table(["", ""], files, "Arkivering av dokumentationen.")] + s.get("data", [])
    out += [h(1, "Referenser")] + s.get("refs", [])
    app = s.get("appendix", [])
    if app:
        out += [h(1, "Bilaga. Mått per tvärsnitt")] + app
    return out + note


def _data(title, s, note, f, ai, opt):
    k = key_numbers(f)
    scan = f.get("scan") or {}
    pm = (f.get("provenance") or {}).get("mesh") or {}
    prov = f.get("provenance") or {}
    out = [{**title, "text": f"Huggspårsmätningar och 3D-skanning av {k['signum']}"},
           h(1, "1 Översikt"),
           p(f"Datamängden innehåller {k['n_slices']} uppmätta tvärsnitt av huggspåren på {k['signum']}"
             + (f" ({k['n_runes']} runor)" if k.get("n_runes") else "")
             + ", med sju spårmått, snittens position och riktning och råprofilerna, samt uppgifter om skanningen."),
           p("Nyckelord: runsten, 3D-skanning, huggspår, huggteknik, " + k["signum"]),
           h(1, "2 Metod")] + _subsections(_only(s.get("method", []), {"3D-dokumentation", "Mätning av huggspår", "Statistik"}), "2")
    files = [["Mått per tvärsnitt", "CSV (UTF-8)", "en rad per tvärsnitt: sju mått, R², position, riktning"],
             ["Råprofiler", "JSON", "tvärsnittsprofilerna som x/z i mm"],
             ["Analysparametrar och proveniens", "JSON", f"Vitki {prov.get('version', '')}, mätmetod {', '.join(f.get('method_versions') or [])}"],
             ["3D-modell", "STL", (pm.get("filename") or "–") + (f", SHA-256 {pm['sha256'][:16]}…" if pm.get("sha256") else "")]]
    out += [h(1, "3 Datamängden"), table(["Fil", "Format", "Innehåll"], files, "Filer i datamängden."),
            table(["", ""], [["Licens", opt.get("license") or "CC BY 4.0"],
                             ["Arkiv och DOI", opt.get("repository") or FILL.format("t.ex. Zenodo och DOI")],
                             ["Skanningens licens", scan.get("license") or FILL.format("licens för skanningen")],
                             ["Språk", "svenska (variabelnamn), engelska (README)"]], "Licens och förvaring.")]
    out += [h(1, "4 Återanvändning"),
            _ai(ai, "reuse", "Måtten kan användas för jämförelser av huggteknik mellan stenar och ristare, för metodstudier "
                "av automatisk spårmätning och, tillsammans med skanningen, för omräkning med nya metodversioner.")]
    out += [h(1, "5 Kända begränsningar"), p(f"Förteckning version {limitations.VERSION} (METHODS.md avsnitt 18); "
                                              "den följer också med i proveniensen för varje mätning."),
            bullets(_limits(f, ai))]
    out += [h(1, "Referenser")] + s.get("refs", [])
    return out + note


BUILDERS = {"tidskrift": _journal, "uppsats": _thesis_essay, "avhandling": _thesis_chapter, "utgava": _edition,
            "konferens": _conference, "poster": _poster, "blogg": _blog, "press": _press,
            "antikvarisk": _antiquarian, "data": _data}


def apply(key: str, blocks: list[dict], facts: dict, ai: dict | None, options: dict | None = None) -> list[dict]:
    """Stenrapportens block omformade efter mallen."""
    if key not in TEMPLATES:
        raise ValueError(f"Okänd mall: {key}")
    if key == "stenrapport":
        return blocks
    title, sections, note = split_sections(blocks)
    out = BUILDERS[key](dict(title), sections, note, facts, ai or {}, options or {})
    if any(b.get("ai") for b in out) and not note:
        out.append(p("Avsnitt markerade som AI-genererade är formulerade av en språkmodell utifrån de framräknade "
                     "resultaten och ska granskas av författaren."))
    return renumber([dict(b) for b in out])
