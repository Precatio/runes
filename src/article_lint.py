"""Granskning av en artikel före godkännandet: de fel som granskarna hittade gång på gång 2026-11-18.

Kontrollerar en artikels text på svenska och engelska (rubrik, ingress, söktitel och brödtext) och ger en lista med fynd,
vart och ett FEL eller VARNING:

- platshållare som står kvar ({COVER}, {FIG_1} …)                                    FEL
- ordet "AI" (husregeln: namnge modellen)                                             FEL
- han/hans/honom (he/his/him) om en ristare (carver) i samma mening                   FEL; i nästa mening VARNING
- "visar", "bevisar", "beror på", "orsakade" (shows, proves, due to, caused) i en
  mening med statistik (procent, p-värde, samband, slumpen …)                          VARNING
- rutan "Det viktigaste i korthet" saknas i en längre artikel, eller har tal som
  inte står i brödtexten                                                              FEL
- seo_title eller seo_title_en över 52 tecken                                         FEL; utan söktitel och med en
                                                                                     rubrik över 52 tecken VARNING
- länkar till artiklar eller rapporter som inte finns, inte är publicerade eller
  publiceras först efter den här artikeln                                             FEL
- citat ur Fornvännen och Futhark: årgång och år som inte går ihop, och tryckt sida
  som inte stämmer med var citatet står (sidhuvudets tryckta sida, inte pdf-sidan)    FEL; ett citat som inte går att
                                                                                     hitta i tidskriftstexten VARNING

Källkontrollen läser den lokala tidskriftsdatabasen (sok.sqlite, Fornvännen 1906– och Futhark 1–15, pdf-sida för pdf-
sida) och jämför bokstäverna (utdata/norge/citat.py letters: gemener, utan diakritiska tecken och mellanrum, så att OCR-
avstavningar inte stör). Den tryckta sidan räknas ut per artikel: ur sidhuvudenas sidnummer (det vanligaste avståndet
mellan tryckt sida och pdf-sida) och annars ur nyckeln (Fornvännen ÅÅÅÅ_START har ett försättsblad, Futhark
futhark_VOL_START börjar på sin första sida). Saknas databasen (som i GitHub Actions) blir det en enda varning.

Samma kontroller utom källkontrollen finns i webbläsaren för /redaktion (web/src/lib/articleLint.ts); de prövas mot samma
fall (tests/fixtures/article_lint_cases.json) i tests/test_article_lint.py och web/scripts/article_lint.test.mjs.

    .venv/bin/python -m src.article_lint posts.json [id ...]     # granskar artiklar ur en ögonblicksbild (bara läsning)
"""
from __future__ import annotations

import datetime as dt
import difflib
import functools
import importlib.util
import os
import re
import sqlite3
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOK = os.environ.get("VITKI_SOK", "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite")
FUTHARK_INDEX = os.path.join(os.path.dirname(SOK), "futhark", "index.jsonl")

FEL, VARNING = "FEL", "VARNING"
SEO_MAX = 52
# A "substantive" article (korthet-rule): shorter texts, the series De gamla landen and personal essays need no box
KORTHET_MIN_CHARS = 3000
BOX = {"sv": "Det viktigaste i korthet", "en": "The essentials in brief"}
SITE_ROUTES = {"artiklar": {"rss.xml"}, "forskningsrapporter": {"begrepp"}}


def _letters_fn():
    """letters() from utdata/norge/citat.py (the project's quote check), loaded by path: utdata is not a package."""
    spec = importlib.util.spec_from_file_location("_citat", os.path.join(ROOT, "utdata", "norge", "citat.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.letters


letters = _letters_fn()


def finding(niva: str, kod: str, sprak: str, text: str, utdrag: str = "") -> dict:
    return {"niva": niva, "kod": kod, "sprak": sprak, "text": text, "utdrag": utdrag[:240]}


# ---- text helpers ------------------------------------------------------------------------------------------------------

LINK_TARGET = re.compile(r"\]\(([^)\s]*)\)")
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
SOURCES = re.compile(r"^##\s+(Källor|Källor och data|Sources|References|Litteratur|Literature)\b.*$", re.M)


def visible(text: str) -> str:
    """The text as read: images removed and link targets dropped (the link text stays)."""
    return LINK_TARGET.sub("]", IMAGE.sub("", text or ""))


def prose(text: str) -> str:
    """The running text before the sources section."""
    m = SOURCES.search(text or "")
    return visible(text[:m.start()] if m else text or "")


SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[\"”“(«*]*[A-ZÅÄÖÆØÉÜ0-9])|\n{1,}")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE.split(text) if s and s.strip()]


def excerpt(s: str, at: int = 0, width: int = 110) -> str:
    a = max(0, at - width // 2)
    out = s[a:a + width].strip()
    return ("…" if a else "") + out + ("…" if a + width < len(s) else "")


# ---- simple checks -----------------------------------------------------------------------------------------------------

PLACEHOLDER = re.compile(r"\{[^{}\n]{1,60}\}")
AI_WORD = re.compile(r"(?<![\wÅÄÖåäö])AI(?![a-zåäöA-ZÅÄÖ])")


def check_placeholders(fields: dict[str, str], sprak: str) -> list[dict]:
    out = []
    for name, text in fields.items():
        for m in PLACEHOLDER.finditer(text or ""):
            out.append(finding(FEL, "platshallare", sprak, f"Platshållaren {m.group(0)} står kvar ({name}).",
                               excerpt(text, m.start())))
    return out


def check_ai(fields: dict[str, str], sprak: str) -> list[dict]:
    out = []
    for name, text in fields.items():
        t = visible(text or "")
        for m in AI_WORD.finditer(t):
            out.append(finding(FEL, "ai", sprak, f"Ordet ”AI” ({name}); namnge modellen i stället (Anthropics språkmodell "
                                                 "Claude).", excerpt(t, m.start())))
    return out


CARVER = {"sv": re.compile(r"\b(?:\w*ristare|\w*ristaren|\w*ristarens|\w*ristares)\b", re.I),
          "en": re.compile(r"\b(?:\w*carver|\w*carver's|\w*carver’s)\b", re.I)}
PRONOUN = {"sv": re.compile(r"\b(han|hans|honom)\b"),
           "en": re.compile(r"\b(he|his|him|himself)\b")}
LEAD_PRONOUN = {"sv": re.compile(r"^[\"”“(«*]*(Han|Hans|Honom)\b"), "en": re.compile(r"^[\"”“(«*]*(He|His|Him)\b")}
PRONOUN_WINDOW = 12  # words after the carver word
# "hans eller hennes", "his or her": both genders named, nothing assumed
INCLUSIVE = re.compile(r"\b(han eller hon|hon eller han|hans eller hennes|hennes eller hans|honom eller henne|he or she|"
                       r"she or he|his or her|her or his|him or her)\b", re.I)
NAMED_CARVER = {"sv": re.compile(r"^[\"”“(«*]*[A-ZÅÄÖ][\wåäöþðæø]+(?: [A-ZÅÄÖ][\wåäöþðæø]+)?\s+(?:var|är|kallas)\s+(?:en|den)\b"),
                "en": re.compile(r"^[\"”“(«*]*[A-Z][\wåäöþðæø]+(?: [A-Z][\wåäöþðæø]+)?\s+(?:was|is)\s+(?:a|an|the)\b")}


def check_pronouns(text: str, sprak: str) -> list[dict]:
    """A gendered pronoun after a singular carver word: in the same sentence (within 12 words) an error, as the first
    word of the next sentence a warning (the next sentence may be about someone else)."""
    out = []
    ss = sentences(prose(text))
    for i, s in enumerate(ss):
        hits = list(CARVER[sprak].finditer(s))
        if not hits:
            continue
        flagged = False
        # "Balle var en flitig ristare … han": a named carver, whose name gives the pronoun; a warning, not an error
        named = NAMED_CARVER[sprak].match(s)
        for h in hits:
            after = s[h.end():]
            words = after.split()
            window = INCLUSIVE.sub("", " ".join(words[:PRONOUN_WINDOW]))
            m = PRONOUN[sprak].search(window)
            if m:
                out.append(finding(VARNING if named else FEL, "pronomen", sprak, f"”{m.group(1)}” om en ristare; skriv "
                                   "ristaren/ristarens (the carver/the carver's)" + (" – gäller en namngiven ristare"
                                   if named else "") + ".", excerpt(s, h.start())))
                flagged = True
                break
        if not flagged and i + 1 < len(ss) and (m := LEAD_PRONOUN[sprak].match(ss[i + 1])):
            out.append(finding(VARNING, "pronomen", sprak, f"Nästa mening börjar med ”{m.group(1)}” efter en ristare; "
                               "gäller det ristaren?", excerpt(ss[i + 1], 0)))
    return out


CAUSAL = {"sv": re.compile(r"\b(visar|visade|visat|bevisar|bevisade|bevisat|beror på|berodde på|berott på|orsakade|orsakar|"
                           r"orsakat)\b", re.I),
          "en": re.compile(r"\b(shows?|showed|shown|proves?|proved|proven|(?:is|was|are|were) due to|caused|causes)\b",
                           re.I)}
FIGURE_SUBJECT = {"sv": re.compile(r"\b(kartan|kartorna|bilden|bilderna|figuren|diagrammet|grafen|stapeln|staplarna|"
                                   r"tabellen|fotot|ritningen|exemplet|sidan|appen|Vitki|skärmbilden|rutan)\s+\S*\s*$", re.I),
                  "en": re.compile(r"\b(the map|maps|the picture|the figure|the chart|the graph|the bars?|the table|the "
                                   r"photo|the drawing|the example|the page|the app|Vitki|the screenshot|the box)\s+\S*\s*$",
                                   re.I)}
# "säger inte vilket som orsakade vilket", "too few to show", "what was shown": no claim is made
NOT_A_CLAIM = {"sv": re.compile(r"(\b(inte|ej|aldrig|kan|kunde|skulle)\b\s+(\S+\s+){0,4}|\bdet\s+)$", re.I),
               "en": re.compile(r"(\b(not|no|never|cannot|can|could|would)\b\s+(\S+\s+){0,4}|n't\s+(\S+\s+){0,4}|\bto\s+|"
                                r"\bwhat\s+(is|was)\s+)$", re.I)}
STATS = {"sv": re.compile(r"%|\bprocent|\bp\s*[=<≤]|\bp-värde|signifikan|\bsamband|korrelation|\boddskvot|\bodds\b|"
                          r"slumpen|konfidensintervall|osäkerhetsintervall|\bregression|gånger så|\bmedelvärde|\bmedian",
                          re.I),
         "en": re.compile(r"%|\bper ?cent|\bp\s*[=<≤]|\bp-value|significan|\bassociation|\bcorrelat|\bodds\b|by chance|"
                          r"confidence interval|uncertainty interval|\bregression|times as|\bmean\b|\bmedian", re.I)}


def check_causal(text: str, sprak: str) -> list[dict]:
    """A causal or proof word in a sentence with a statistical result: tested is only an association."""
    out = []
    for s in sentences(prose(text)):
        if not STATS[sprak].search(s):
            continue
        for m in CAUSAL[sprak].finditer(s):
            before = s[:m.start()]
            if FIGURE_SUBJECT[sprak].search(before) or NOT_A_CLAIM[sprak].search(before):
                continue
            out.append(finding(VARNING, "orsak", sprak, f"”{m.group(1)}” i en mening med statistik: prövat är ett "
                               "samband, inte en orsak eller ett bevis.", excerpt(s, m.start())))
            break
    return out


NUMBER = re.compile(r"(?<![\w,.])\d+(?:[   ]\d{3})*(?:[,.]\d+)?(?![\w])")


def normalise_number(raw: str, sprak: str) -> str:
    s = re.sub(r"[   ]", "", raw)
    if sprak == "sv":
        s = s.replace(",", ".")
    else:
        s = re.sub(r",(?=\d{3}\b)", "", s)
    return s.rstrip(".")


def numbers(text: str, sprak: str) -> set[str]:
    # en: "1,577" is one number; join thousands groups before matching
    if sprak == "en":
        text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    return {normalise_number(m.group(0), sprak) for m in NUMBER.finditer(text)}


def rounded(n: str, body: set[str]) -> bool:
    """A round number in the box ("över 1 300") that rounds one in the text (1 352): within a tenth of it."""
    try:
        v = float(n)
    except ValueError:
        return False
    if v < 100 or v % 10:
        return False
    for b in body:
        try:
            w = float(b)
        except ValueError:
            continue
        if w and abs(w - v) / w <= 0.1:
            return True
    return False


def box_of(text: str, sprak: str) -> tuple[str, str] | None:
    """(the box's text, the text without the box) or None."""
    m = re.search(rf"^:::box\s+{re.escape(BOX[sprak])}\s*$", text or "", re.M | re.I)
    if not m:
        return None
    end = re.search(r"^:::\s*$", text[m.end():], re.M)
    stop = m.end() + (end.start() if end else len(text) - m.end())
    return text[m.end():stop], text[:m.start()] + text[stop:]


def needs_box(post: dict, body: str) -> bool:
    labels = post.get("labels") or []
    title = post.get("title") or ""
    if "Personligt" in labels or "Rapport" in labels or title.startswith("De gamla landen"):
        return False
    return len(body or "") >= KORTHET_MIN_CHARS


def check_box(post: dict, body: str, sprak: str) -> list[dict]:
    got = box_of(body, sprak)
    if got is None:
        if needs_box(post, body):
            return [finding(FEL, "korthet_saknas", sprak, f"Rutan ”:::box {BOX[sprak]}” saknas.")]
        return []
    box, rest = got
    body_numbers = numbers(visible(rest), sprak)
    missing = sorted((n for n in numbers(box, sprak) - body_numbers if not rounded(n, body_numbers)),
                     key=lambda x: (len(x), x))
    if missing:
        return [finding(FEL, "korthet_tal", sprak, "Rutan ”Det viktigaste i korthet” har tal som inte står i brödtexten: "
                        + ", ".join(missing) + ".", box.strip())]
    return []


def check_seo(post: dict) -> list[dict]:
    out = []
    for key, title_key, sprak in (("seo_title", "title", "sv"), ("seo_title_en", "title_en", "en")):
        seo = (post.get(key) or "").strip()
        title = (post.get(title_key) or "").strip()
        if seo and len(seo) > SEO_MAX:
            out.append(finding(FEL, "seo_titel", sprak, f"{key} har {len(seo)} tecken; högst {SEO_MAX}.", seo))
        elif not seo and title and len(title) > SEO_MAX:
            out.append(finding(VARNING, "seo_titel", sprak, f"Ingen {key}, och rubriken har {len(title)} tecken (över "
                               f"{SEO_MAX}); sökmotorerna kortar den.", title))
    return out


# ---- links -------------------------------------------------------------------------------------------------------------

INTERNAL = re.compile(r"^(?:https?://(?:www\.)?vitkirunor\.se)?/(en/)?(artiklar|forskningsrapporter)/([A-Za-z0-9_.-]+)/?(?:[#?].*)?$")


def _when(v) -> dt.datetime | None:
    if v is None or v == "":
        return None
    if isinstance(v, dt.datetime):
        return v if v.tzinfo else v.replace(tzinfo=dt.timezone.utc)
    try:
        d = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def fmt_day(d: dt.datetime) -> str:
    from zoneinfo import ZoneInfo
    return d.astimezone(ZoneInfo("Europe/Stockholm")).date().isoformat()


def check_links(body: str, sprak: str, posts: list[dict], publish_at: dt.datetime | None, now: dt.datetime,
                self_slug: str = "") -> list[dict]:
    by_slug = {p.get("slug"): p for p in posts if p.get("slug")}
    out, seen = [], set()
    for m in LINK_TARGET.finditer(body or ""):
        target = m.group(1)
        lm = INTERNAL.match(target)
        if not lm:
            continue
        en, section, slug = lm.groups()
        if slug in SITE_ROUTES[section] or slug == self_slug or (slug, en) in seen:
            continue
        seen.add((slug, en))
        p = by_slug.get(slug)
        if not p:
            out.append(finding(FEL, "lank_okand", sprak, f"Länken går till en artikel som inte finns: {target}", target))
            continue
        live = _when(p.get("publishedAt"))
        if not p.get("published"):
            out.append(finding(FEL, "lank_opublicerad", sprak, f"Länken går till ett opublicerat utkast: {target}", target))
        elif live and live > now and (publish_at is None or live > publish_at):
            out.append(finding(FEL, "lank_opublicerad", sprak, f"Länken går till en artikel som publiceras först "
                               f"{fmt_day(live)}, efter den här: {target}", target))
        if en and not (p.get("body_en") or "").strip():
            out.append(finding(VARNING, "lank_okand", sprak, f"Länken går till den engelska utgåvan, som saknas: {target}",
                               target))
    return out


# ---- the journals ------------------------------------------------------------------------------------------------------

JOURNALS = ("Fornvännen", "Futhark")
JOURNAL = re.compile(r"\*?\b(Fornvännen|Futhark)\b\*?")
QUOTE = re.compile(r"[”“\"]([^”“\"\n]{12,600})[”“\"]")
PAGE_REF = re.compile(r"\b(?:s|p|pp|sid)\.\s*(\d{1,4})(?:\s*[–-]\s*(\d{1,4}))?")


@functools.lru_cache(maxsize=1)
def _db() -> sqlite3.Connection | None:
    if not os.path.exists(SOK):
        return None
    con = sqlite3.connect(f"file:{SOK}?mode=ro", uri=True, check_same_thread=False)
    return con


@functools.lru_cache(maxsize=1)
def futhark_years() -> dict[str, set[int]]:
    """Futhark volume → the years it may be cited by: the nominal year (volume 1 = 2010) and the year it came out."""
    import json
    out: dict[str, set[int]] = {}
    if os.path.exists(FUTHARK_INDEX):
        for line in open(FUTHARK_INDEX, encoding="utf-8"):
            d = json.loads(line)
            if str(d.get("year", "")).isdigit():
                out.setdefault(str(d.get("volume")), set()).add(int(d["year"]))
    for v in range(1, 20):
        out.setdefault(str(v), set()).add(2009 + v)
    for combo in ("9-10", "14-15"):
        a, b = (int(x) for x in combo.split("-"))
        out.setdefault(combo, set()).update({2009 + a, 2009 + b})
        out.setdefault(str(a), set()).update(out[combo])
        out.setdefault(str(b), set()).update(out[combo])
    return out


@functools.lru_cache(maxsize=1)
def _rowids() -> dict[str, list[int]]:
    """Each text's page rows (pages_content ids): the key column has no index, and reading it once is far faster than
    a scan per text."""
    out: dict[str, list[int]] = {}
    for rid, key in _db().execute("select id, c0 from pages_content"):
        out.setdefault(key, []).append(rid)
    return out


@functools.lru_cache(maxsize=4096)
def doc_pages(key: str) -> tuple[tuple[int, str], ...]:
    ids = _rowids().get(key, [])
    if not ids:
        return ()
    rows = _db().execute(f"select c1, c2 from pages_content where id in ({','.join('?' * len(ids))})", ids).fetchall()
    return tuple(sorted((int(p), t or "") for p, t in rows))


HEADER_NUMBER = re.compile(r"(?<![\d,.])(\d{1,4})(?![\d,.])")
COVER = re.compile(r"JOURNAL\s+OF|Ingår i:|kulturarvsdata\.se", re.I)


@functools.lru_cache(maxsize=4096)
def page_offset(key: str) -> int | None:
    """Printed page − pdf page for a journal text: the most common offset of the page numbers in the page headers and
    footers; when they are too few (old OCR), from the key (Fornvännen ÅÅÅÅ_START with its cover sheet,
    futhark_VOL_START_ID). The key alone is not trusted: some keys carry another start than the printed one."""
    votes: Counter = Counter()
    pages = doc_pages(key)
    for p, text in pages:
        if _cover(text, p):
            continue
        lines = [x for x in text.splitlines() if x.strip()]
        seen = set()
        for line in lines[:3] + lines[-3:]:
            # a page number stands first or last on its header or footer line ("22 • Barnes", "… Today? • 13")
            words = [w.strip("•·|.,;:()[]") for w in line.split()]
            for w in (words[0], words[-1]) if words else ():
                if w.isdigit() and 1 <= int(w) <= 1500 and int(w) - p not in seen:
                    seen.add(int(w) - p)
                    votes[int(w) - p] += 1
    prior = None
    if (m := re.fullmatch(r"(1[89]\d\d|20\d\d)_(\d{3})", key)):
        prior = int(m.group(2)) - 2
    elif (m := re.fullmatch(r"futhark_[^_]+_(\d+)_\d+", key)):
        prior = int(m.group(1)) - 1
    if votes:
        best = max(votes.values())
        if best >= max(2, len(pages) // 5):
            tied = [o for o, n in votes.items() if n == best]
            return prior if prior in tied else tied[0]
    return prior


def _edge_numbers(text: str) -> list[int]:
    """Numbers that stand first or last on a header or footer line: where page numbers stand ("22 • Barnes")."""
    lines = [x for x in text.splitlines() if x.strip()]
    out = []
    for line in lines[:3] + lines[-3:]:
        words = [w.strip("•·|.,;:()[]") for w in line.split()]
        for w in (words[0], words[-1]) if words else ():
            if w.isdigit() and 1 <= int(w) <= 1500:
                out.append(int(w))
    return out


@functools.lru_cache(maxsize=4096)
def printed_pages(key: str) -> dict[int, int]:
    """pdf page → printed page. The offset is followed page by page: a page's own number wins when it lies near the
    expected one, so that a pdf that skips pages (a review section printed in pieces) keeps the right numbers."""
    off = page_offset(key)
    if off is None:
        return {}
    out, cur = {}, off
    pages = doc_pages(key)
    edges = [[] if _cover(t, p) else _edge_numbers(t) for p, t in pages]
    # start from the first page whose number the next page continues (a text printed in parts starts on its own pages)
    for i in range(len(pages) - 1):
        hit = [n for n in edges[i] if n + 1 in edges[i + 1] or (i + 2 < len(pages) and n + 2 in edges[i + 2])]
        if hit:
            cur = hit[0] - pages[i][0]
            break
    for i, (p, _) in enumerate(pages):
        near = [n for n in edges[i] if abs(n - (p + cur)) <= 12]
        # a longer jump only when the next page carries the next number too
        far = [n for n in edges[i] if i + 1 < len(pages) and n + 1 in edges[i + 1]]
        if near or far:
            n = min(near, key=lambda n: abs(n - (p + cur))) if near else far[0]
            cur = n - p
        out[p] = p + cur
    return out


def _cover(text: str, p: int) -> bool:
    return p <= 2 and bool(COVER.search(text[:400]))


def printed_range(key: str) -> tuple[int, int] | None:
    """The first and last printed page of a text (cover sheets and issue covers not counted)."""
    pp = printed_pages(key)
    pages = doc_pages(key)
    if not pp or not pages:
        return None
    body = [p for p, t in pages if not _cover(t, p)] or [pages[0][0]]
    return pp[body[0]], max(pp.values())


@functools.lru_cache(maxsize=1)
def link_keys() -> dict[str, str]:
    """The texts' web addresses → key: Fornvännen's pub.raa.se/dokumentation/<uuid>, Futhark's diva2:<id>."""
    import json
    out: dict[str, str] = {}
    idx = os.path.join(os.path.dirname(SOK), "fornvannen", "index.jsonl")
    if os.path.exists(idx):
        for line in open(idx, encoding="utf-8"):
            d = json.loads(line)
            out[d["id"]] = d["key"]
    for key in _rowids():
        if (m := re.fullmatch(r"futhark_.+_(\d+)", key)):
            out[m.group(1)] = key
        elif re.fullmatch(r"[0-9a-f-]{36}", key):
            out[key] = key
    return out


LINKED = re.compile(r"pub\.raa\.se/dokumentation/([0-9a-f-]{36})|diva2:(\d+)")


def docs_for(journal: str, year: int | None, volume: str | None) -> list[tuple[str, str, str]]:
    """(key, title, year) of the journal texts of that year (Fornvännen) or volume (Futhark)."""
    con = _db()
    if journal == "Futhark":
        if volume:
            rows = con.execute("select key, title, year from docs where journal='futhark' and key like ?",
                               (f"futhark_{volume}_%",)).fetchall()
            if rows or not year:
                return rows
        return con.execute("select key, title, year from docs where journal='futhark' and year in (?, ?)",
                           (str(year), str(year + 1) if year else "")).fetchall()
    if year is None:
        return []
    return con.execute("select key, title, year from docs where journal='fornvannen' and year=?", (str(year),)).fetchall()


@functools.lru_cache(maxsize=4096)
def doc_letters(key: str) -> tuple[str, ...]:
    return tuple(letters(t) for _, t in doc_pages(key))


def find_quote(keys: list[str], quote: str) -> list[tuple[str, int]]:
    """(key, printed page) where the quote stands, by letters; a quote across a page break counts on both pages."""
    q = letters(quote)
    if len(q) < 12:
        return []
    hits = []
    for key in keys:
        pages = doc_pages(key)
        pp = printed_pages(key)
        lp = doc_letters(key)
        for i, (p, _) in enumerate(pages):
            joined = lp[i] + (lp[i + 1] if i + 1 < len(lp) else "")
            if q in lp[i] or (q in joined and q not in (lp[i + 1] if i + 1 < len(lp) else "")):
                hits.append((key, pp.get(p, -1)))
                if q not in lp[i] and i + 1 < len(pages):
                    hits.append((key, pp.get(pages[i + 1][0], -1)))
    return hits


def _expand(refs: list[tuple[int, int | None]]) -> set[int]:
    out = set()
    for a, b in refs:
        if b and b >= a and b - a < 200:
            out.update(range(a, b + 1))
        elif b and b < a and len(str(b)) < len(str(a)):  # "s. 137–47"
            full = int(str(a)[:len(str(a)) - len(str(b))] + str(b))
            out.update(range(a, full + 1))
        else:
            out.add(a)
    return out


def parse_citations(text: str) -> list[dict]:
    """Each mention of Fornvännen or Futhark with what follows it on its line: volume or year, page references, the
    quotes before it in the same paragraph (in-text citation) and, in a reference list, the author's year and title."""
    out = []
    for para in re.split(r"\n\s*\n|\n(?=\s*[-*] )", text or ""):
        last_end = 0  # where the previous citation in the paragraph ended: its quotes are not this one's
        for m in JOURNAL.finditer(para):
            journal = m.group(1)
            nxt = JOURNAL.search(para, m.end())
            stop = para.find("\n", m.end())
            stop = len(para) if stop < 0 else stop
            if nxt:
                stop = min(stop, nxt.start())
            tail = para[m.end():stop]
            # in running text the citation ends at the closing parenthesis
            inline = para[:m.start()].rfind("(") > para[:m.start()].rfind(")")
            if inline:
                depth, cut = 1, len(tail)
                for i, ch in enumerate(tail):
                    depth += ch == "("
                    depth -= ch == ")"
                    if depth == 0:
                        cut = i
                        break
                tail = tail[:cut]
            vm = re.match(r"\s*\]?\s*(\d{1,4}(?:-\d{1,2})?)\b", tail)
            first = vm.group(1) if vm else None
            year = volume = None
            if first and re.fullmatch(r"\d{4}", first) and int(first) > 1800:
                year = int(first)
            elif first:
                volume = first
            ym = re.search(r"\((\d{4})\b|,\s*(\d{4})\b", tail[:30])
            stated_year = int(ym.group(1) or ym.group(2)) if ym else None
            refs = [(int(a), int(b) if b else None) for a, b in PAGE_REF.findall(tail)]
            before = para[:m.start()]
            ref_line = re.match(r"\s*[-*]\s", para) is not None
            author_year = title = None
            if ref_line:
                am = re.search(r"\b(1[89]\d\d|20\d\d)[a-z]?\.\s+(.*)$", before, re.S)
                if am:
                    author_year = int(am.group(1))
                    title = re.sub(r"[”“\"*]", "", am.group(2)).strip().rstrip(".").strip()
            # the quotes of the sentence (or sentences) the in-text citation closes
            quotes = []
            if inline:
                start = max(last_end, len(before) - 700)
                quotes = [q.group(1) for q in QUOTE.finditer(before[start:])]
            last_end = m.end() + len(tail)
            lk = LINKED.search(para[m.start():stop + 200] if not inline else para[m.start():m.end() + len(tail) + 120])
            linked = (lk.group(1) or lk.group(2)) if lk else None
            out.append({"journal": journal, "year": year, "volume": volume, "stated_year": stated_year, "linked": linked,
                        "refs": refs, "quotes": quotes, "ref_line": ref_line, "author_year": author_year,
                        "title": title, "text": (para[max(0, m.start() - 60):stop + 1]).strip()})
    return out


def _title_match(docs: list[tuple[str, str, str]], title: str) -> str | None:
    t = letters(title)[:80]
    if len(t) < 6:
        return None
    best, score = None, 0.0
    for key, dtitle, _ in docs:
        d = letters(re.sub(r"<[^>]+>", "", dtitle or ""))[:80]
        s = 2.0 if t == d else 1.0 if (t[:30] in d or d[:30] in t) else difflib.SequenceMatcher(None, t, d).ratio()
        if s > score:
            best, score = key, s
    return best if score >= 0.75 else None


def check_citations(text: str, sprak: str, warn_unfound: bool = True) -> list[dict]:
    out: list[dict] = []
    cites = parse_citations(text)
    if not cites:
        return out
    if _db() is None:
        return [finding(VARNING, "kalla_ej_provad", sprak, "Källkontrollen kunde inte köras: tidskriftsdatabasen "
                         "(sok.sqlite) finns inte på den här datorn.")]
    fy = futhark_years()
    for c in cites:
        j, vol = c["journal"], c["volume"]
        # the volume and the year must agree
        year = c["year"]
        given_years = [y for y in (c["stated_year"], c["author_year"]) if y]
        if vol and j == "Fornvännen" and vol.isdigit():
            year = int(vol) + 1905
            for y in given_years:
                if y != year:
                    out.append(finding(FEL, "kalla_argang", sprak, f"Fornvännen {vol} är årgång {year}, inte {y}.",
                                       c["text"]))
                    break
        elif vol and j == "Futhark":
            ok = fy.get(vol, set())
            for y in given_years:
                if ok and all(abs(y - o) > 1 for o in ok):
                    out.append(finding(FEL, "kalla_argang", sprak, f"Futhark {vol} kom ut {'/'.join(map(str, sorted(ok)))}"
                                       f", inte {y}.", c["text"]))
                    break
            year = min(ok) if ok else None
        elif not vol and not year and c["author_year"]:
            year = c["author_year"]
        docs = docs_for(j, year, vol if j == "Futhark" else None)
        if not docs:
            if c["refs"] or c["quotes"]:
                if warn_unfound:
                    out.append(finding(VARNING, "kalla_ej_provad", sprak, f"{j} {vol or year or ''}: årgången finns inte i "
                                       "tidskriftsdatabasen; sidan kunde inte prövas.", c["text"]))
            continue
        pages = _expand(c["refs"])
        linked = link_keys().get(c["linked"] or "") if c.get("linked") and _db() is not None else None
        if linked and linked not in {k for k, _, _ in docs}:
            docs = [d for d in _db().execute("select key, title, year from docs where key=?", (linked,))] + docs
        # 1. a quote before an in-text citation: on which printed page does it stand?
        if c["quotes"] and pages:
            keys = [linked] if linked else [k for k, _, _ in docs]
            found = False
            for q in c["quotes"]:
                hits = find_quote(keys, q)
                if not hits:
                    continue
                found = True
                printed = {p for _, p in hits if p > 0}
                if printed and not printed & pages:
                    out.append(finding(FEL, "kalla_sida", sprak, f"Citatet står på s. {min(printed)} (tryckt sida), inte "
                                       f"s. {', '.join(map(str, sorted(pages)))}.", f"”{q[:120]}” – {c['text']}"))
                break
            if not found and warn_unfound:
                out.append(finding(VARNING, "kalla_ej_provad", sprak, f"Citatet hittades inte i {j} {vol or year}; "
                                   "sidan kunde inte prövas.", c["text"]))
            continue
        # 2. a reference-list entry: the article's printed range, and the quoted pages inside it
        if c["ref_line"] and c["title"]:
            key = linked or _title_match(docs, c["title"])
            if not key:
                if warn_unfound and pages:
                    out.append(finding(VARNING, "kalla_ej_provad", sprak, f"Artikeln hittades inte i {j} {vol or year}; "
                                       "sidorna kunde inte prövas.", c["text"]))
                continue
            rng = printed_range(key)
            if not rng or not c["refs"]:
                continue
            lo, hi = rng
            a, b = c["refs"][0]
            # the cited pages must lie inside the text (a pdf may hold more than the one article, e.g. a whole review
            # section, so only pages outside it are errors)
            if any(not lo <= x <= hi for x in _expand([(a, b)])):
                out.append(finding(FEL, "kalla_omfang", sprak, f"Artikeln står på s. {lo}–{hi} (tryckta sidor), inte "
                                   f"s. {a}{'–' + str(b) if b else ''}.", c["text"]))
            outside = sorted(p for p in _expand(c["refs"][1:]) if not lo <= p <= hi)
            if outside:
                out.append(finding(FEL, "kalla_sida", sprak, f"Sidan {', '.join(map(str, outside))} ligger utanför artikeln "
                                   f"(s. {lo}–{hi}).", c["text"]))
            continue
        # 3. a page without a quote or title: it must at least lie inside some text of that year
        if pages and not c["ref_line"]:
            ranges = [printed_range(k) for k, _, _ in docs]
            if not any(r and r[0] <= p <= r[1] for r in ranges for p in pages) and warn_unfound:
                out.append(finding(VARNING, "kalla_ej_provad", sprak, f"Ingen text i {j} {vol or year} täcker s. "
                                   f"{min(pages)} i tidskriftsdatabasen.", c["text"]))
    return out


# ---- the whole article -------------------------------------------------------------------------------------------------

def lint(post: dict, posts: list[dict] | None = None, publish_at: dt.datetime | None = None,
         now: dt.datetime | None = None, citations: bool = True) -> list[dict]:
    """All findings for one article (a Firestore post: title, summary, body, *_en, seo_title*, labels). posts: every
    article, for the link check (without it links are not checked); publish_at: when this article goes out."""
    now = now or dt.datetime.now(dt.timezone.utc)
    publish_at = publish_at or (_when(post.get("publishedAt")) if post.get("published") else None)
    out: list[dict] = []
    for sprak, sfx in (("sv", ""), ("en", "_en")):
        body = post.get("body" + sfx) or ""
        if sprak == "en" and not body.strip():
            continue
        fields = {"rubrik": post.get("title" + sfx) or "", "ingress": post.get("summary" + sfx) or "",
                  "söktitel": post.get("seo_title" + sfx) or "", "text": body}
        out += check_placeholders(fields, sprak)
        out += check_ai(fields, sprak)
        out += check_pronouns(body, sprak)
        out += check_causal(body, sprak)
        out += check_box(post, body, sprak)
        if posts is not None:
            out += check_links(body, sprak, posts, publish_at, now, post.get("slug") or "")
        if citations:
            # the English text repeats the Swedish citations: only its real errors are reported, not the warnings
            out += check_citations(body, sprak, warn_unfound=(sprak == "sv"))
    out += check_seo(post)
    return out


def summary(findings: list[dict]) -> dict:
    fel = sum(f["niva"] == FEL for f in findings)
    return {"fel": fel, "varningar": len(findings) - fel, "fynd": findings}


def main(argv: list[str]) -> int:
    import json
    if not argv:
        print(__doc__)
        return 2
    posts = json.load(open(argv[0], encoding="utf-8"))
    if isinstance(posts, dict):
        posts = [{"id": k, **v} for k, v in posts.items()]
    ids = argv[1:] or [p["id"] for p in posts if not p.get("published")]
    by = {p["id"]: p for p in posts}
    for i in ids:
        p = by[i]
        fs = lint(p, posts)
        s = summary(fs)
        print(f"\n== {p.get('title')} ({i}): {s['fel']} fel, {s['varningar']} varningar")
        for f in fs:
            print(f"  {f['niva']:7} {f['sprak']} {f['kod']:16} {f['text']}")
            if f["utdrag"]:
                print(f"          {f['utdrag'][:200]}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
