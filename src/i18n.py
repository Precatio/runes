"""Engelska rapporter: samma översättning som i webbläsaren (web/src/i18n/core.ts), för dokument som laddas ned.

Rapporterna skrivs på svenska. Med språket "en" översätts varje block mot samma mallkatalog som gränssnittet
(web/src/i18n/en.json): siffror, ristarnamn och orter byts mot platshållare före uppslaget och sätts tillbaka
efteråt (siffror i engelsk form). En mening som inte finns i katalogen förblir svensk och samlas i MISSING, så att
den kan översättas (scripts/i18n_reports.py). Inskrifter (translitterering, normalisering) översätts aldrig.

Reglerna måste vara desamma som i core.ts, annars blir mallarna olika; tests/test_i18n.py jämför dem.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "web", "src", "i18n", "en.json")
NAMES = os.path.join(ROOT, "web", "src", "i18n", "names.json")
TERMS = os.path.join(ROOT, "web", "src", "i18n", "terms.json")

PASSTHROUGH = {
    "U", "Sö", "Ög", "Öl", "Vg", "Sm", "Gs", "Hs", "Vs", "Nä", "Hr", "Ån", "Bo", "Ds", "Lp", "DR", "N", "IS", "IM", "E",
    "GR", "Or", "D", "M", "J", "G", "km", "m", "cm", "mm", "p", "q", "n", "rho", "eta", "OR", "KI", "CI", "SD", "AUC",
    "RAK", "Fp", "Pr", "KB", "MB", "GB", "STL", "OBJ", "PLY", "PNG", "JPG", "PDF", "CSV", "JSON", "ZIP", "R", "API", "AI",
    "Vitki", "GitHub", "Rundata", "Wikidata", "Zenodo", "DOI", "LinkedIn", "Claude", "Gemini", "Anthropic", "Google",
    "OpenAI", "Plotly", "Leaflet", "OpenStreetMap", "x", "y", "z", "mgcv", "Holm", "Wilcoxon", "Gräslund", "Axelson",
    "ATA", "Fv", "SD", "SB", "NOR", "IR", "KJ", "BN", "Sc", "Br", "Vr", "NIyR", "DK", "MJy", "Ka", "Kg", "RR", "SHM",
    "Sb", "SvK", "MÖLM", "RS", "Plansch",
    *"ABCDEFGHIJKLMNOPQRSTUVWXYZ",
}
NUMBER = re.compile(r"\d+(?:[   ]\d{3})*(?:,\d+)?")
LETTER = re.compile(r"[A-Za-zÅÄÖåäöÆØæøÉéÜüÞþÐð]")
UPPER = "A-ZÅÄÖÆØÉÜÞÐÁÍÓÚ"
SPLIT = re.compile(rf"(?<=[.!?])(\s+)(?=[{UPPER}\d\"”(«])|(?<=:)(\s+)(?=[{UPPER}])|(;\s+)|(\n+)")
_L, _LH = r"[^\W\d_]", r"(?:[^\W\d_]|-)"
LABEL = re.compile(rf"^({_L}{_LH}*(?: {_L}{_LH}*){{0,2}}(?: \([^)]{{1,12}}\))?:)(\s+)(?=\S)")
LEAD = re.compile(r"^[(«\"„”'“]*")
TRAIL = re.compile(r"[.,;:!?)”\"'’]+$")
TRAIL_KEEP_QUOTE = re.compile(r"[.,;:!?)”\"’]+$")
TRAIL_KEEP_PAREN = re.compile(r"[.,;:!?]+$")
MARK = re.compile("\u0000(\\d+)\u0000|\u0001([-])\u0001")

MISSING: dict[str, str] = {}


@lru_cache(maxsize=1)
def catalog() -> dict[str, str]:
    try:
        with open(CATALOG, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _load(path: str) -> list[str]:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return []


@lru_cache(maxsize=1)
def _vocab() -> tuple[frozenset[str], frozenset[str], int]:
    names, terms = _load(NAMES), _load(TERMS)
    longest = max([1] + [len(n.split()) for n in names + terms])
    return frozenset(names), frozenset(terms), longest


def mask(text: str, with_terms: bool = False) -> tuple[str, list[str], list[str]]:
    """Namn, siffror och (med with_terms) termer byts mot {0}, {1}, … i den ordning de förekommer (som mask() i
    core.ts). Returnerar mallen, de utbytta orden och deras slag (number, name, term)."""
    names, terms, max_words = _vocab()
    tokens: list[str] = []
    kinds: list[str] = []
    out = text
    if names or (with_terms and terms):
        words = re.split(r"(\s+)", out)
        res: list[str] = []
        i = 0
        while i < len(words):
            w = words[i]
            lead = LEAD.match(w).group(0)
            rest = w[len(lead):]
            capital = rest[:1].isalpha() and rest[:1].isupper()
            hit = 0
            k = min(max_words, -(-(len(words) - i) // 2))
            while k >= 1 and not hit:
                cand = "".join(words[i:i + 2 * k - 1])[len(lead):]
                for core in (cand, TRAIL.sub("", cand), TRAIL_KEEP_QUOTE.sub("", cand), TRAIL_KEEP_PAREN.sub("", cand)):
                    kind = "name" if capital and core in names else ("term" if with_terms and core in terms else None)
                    if core and kind:
                        res.append(lead + "\u0001" + chr(0xE000 + len(tokens)) + "\u0001" + cand[len(core):])
                        tokens.append(core)
                        kinds.append(kind)
                        hit = 2 * k - 1
                        break
                k -= 1
            if hit:
                i += hit
                continue
            res.append(w)
            i += 1
        out = "".join(res)

    def num(m: re.Match) -> str:
        tokens.append(m.group(0))
        kinds.append("number")
        return f"\u0000{len(tokens) - 1}\u0000"
    out = NUMBER.sub(num, out)
    order: list[int] = []

    def renumber(m: re.Match) -> str:
        order.append(int(m.group(1)) if m.group(1) is not None else ord(m.group(2)) - 0xE000)
        return "{" + str(len(order) - 1) + "}"
    out = MARK.sub(renumber, out)
    return out, [tokens[i] for i in order], [kinds[i] for i in order]


def english_number(s: str) -> str:
    if not s[:1].isdigit():
        return s
    whole, _, dec = s.partition(",")
    digits = re.sub(r"[   ]", "", whole)
    grouped = f"{int(digits):,}" if re.search(r"[   ]", whole) else digits
    return f"{grouped}.{dec}" if dec else grouped


def _unmask(template: str, tokens: list[str], kinds: list[str], cat: dict[str, str]) -> str:
    def one(m: re.Match) -> str:
        i = int(m.group(1))
        if i >= len(tokens):
            return ""
        if kinds[i] == "term":
            if tokens[i] not in cat:
                MISSING.setdefault(tokens[i], tokens[i])
            return cat.get(tokens[i], tokens[i])
        return english_number(tokens[i])
    return re.sub(r"\{(\d+)\}", one, template)


def _lookup(text: str, cat: dict[str, str]) -> str | None:
    """Först med bara namn och siffror (katalogens äldre mallar), sedan med termer."""
    for with_terms in (False, True):
        t, tk, kd = mask(text, with_terms)
        hit = _find(cat, t)
        if hit is not None:
            return _unmask(hit, tk, kd, cat)
        if _needs_nothing(t):
            return _unmask(_plain_words(t), tk, kd, cat)
    return None


# Words with a fixed translation, used only when a segment consists of nothing else (as WORDS in core.ts)
WORDS = {
    "signerad": "signed", "signerade": "signed", "attribuerad": "attributed", "försvunnen": "lost", "och": "and",
    "med": "with", "tillsammans": "together", "sn": "parish", "hd": "hundred", "nu": "now", "numera": "now",
    "kyrka": "church", "kyrkan": "the church", "kyrkogård": "churchyard", "Vid": "At", "vid": "at", "socken": "parish",
    "härad": "hundred", "ungefär": "about",
}


def _needs_nothing(template: str) -> bool:
    words = re.findall(r"(?:[^\W\d_]|²)+", re.sub(r"\{\d+\}", " ", template))
    return all(w in PASSTHROUGH or w in WORDS for w in words)


def _plain_words(template: str) -> str:
    return re.sub(r"[^\W\d_]+", lambda m: WORDS.get(m.group(0), m.group(0)), template)


def _find(cat: dict[str, str], template: str) -> str | None:
    if template in cat:
        return cat[template]
    if template.endswith(".") and not template.endswith(".."):
        hit = cat.get(template[:-1])
        if hit is not None:
            return hit if hit.endswith(".") else hit + "."
    else:
        hit = cat.get(template + ".")
        if hit is not None:
            return hit[:-1] if hit.endswith(".") else hit
    return None


def segments(text: str) -> list[str]:
    return [s for s in SPLIT.split(text) if s is not None]


def translate(text: str, lang: str = "en") -> str:
    """Texten på engelska; det som saknas i katalogen förblir svenskt (och samlas i MISSING)."""
    if lang != "en" or not text:
        return text
    cat = catalog()
    lead = re.match(r"^\s*", text).group(0)
    trail = re.search(r"\s*$", text).group(0)
    body = text[len(lead):len(text) - len(trail)]
    if not body or not LETTER.search(body):
        return lead + NUMBER.sub(lambda m: english_number(m.group(0)), body) + trail
    whole = _lookup(body, cat)
    if whole is not None:
        return lead + whole + trail

    def one(part: str) -> str:
        core = part.strip()
        if not LETTER.search(core):
            return part.replace(core, NUMBER.sub(lambda m: english_number(m.group(0)), core), 1)
        hit = _lookup(core, cat)
        if hit is not None:
            return part.replace(core, hit, 1)
        lab = LABEL.match(core)
        if lab:
            head = _lookup(lab.group(1), cat)
            if head is None:
                MISSING.setdefault(mask(lab.group(1), True)[0], lab.group(1))
            rest = one(core[lab.end():])
            return part.replace(core, (head if head is not None else lab.group(1)) + lab.group(2) + rest.strip(), 1)
        MISSING.setdefault(mask(core, True)[0], core[:300])
        return part

    parts = segments(body)
    if len(parts) == 1:
        return lead + one(body) + trail
    return lead + "".join(one(x) if LETTER.search(x) else x for x in parts) + trail


def translate_blocks(blocks: list[dict], lang: str = "en") -> list[dict]:
    """Rapportens block (src/academic.py) på engelska. Inskrifter och figurer lämnas orörda."""
    if lang != "en":
        return blocks
    out = []
    for b in blocks:
        b = dict(b)
        t = b.get("type")
        if t in ("title", "heading", "paragraph"):
            b["text"] = translate(b.get("text") or "")
            if t == "title" and b.get("institution"):
                b["institution"] = translate(b["institution"])
        elif t == "list":
            b["items"] = [translate(x) for x in b.get("items") or []]
        elif t == "table":
            b["headers"] = [translate(x) for x in b.get("headers") or []]
            b["rows"] = [[translate(str(c)) for c in row] for row in b.get("rows") or []]
            b["caption"] = translate(b.get("caption") or "")
        elif t == "figure":
            b["caption"] = translate(b.get("caption") or "")
        out.append(b)
    return out
