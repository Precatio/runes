"""Redan känt? Appens fynd om en sten prövade mot det forskningen redan skrivit om stenen.

Tre slags källor, utöver Rundata och Runor 2020 (src/crosscheck.py):

  SRI         Sveriges runinskrifter, utgivarnas artikel om stenen (hela texten, sida för sida;
              scripts/sri_artiklar.py → downloads/sri_artiklar, sammanfattad av scripts/build_sri_mentions.py till
              data/cache/literature/sri_mentions.json)
  tidskrift   Fornvännen 1906–2023, Futhark 1–15, Namn och bygd 2010–2025 och Current Swedish Archaeology 28–, de sidor
              som nämner stenen i löptext (scripts/build_journal_index.py → data/cache/literature/journals.json)
  avhandling  utdragen ur litteraturregistrets avhandlingar och utgåvor (data/cache/literature/index.json), och
              litteraturens ristarattribueringar som Rundata saknar (data/carver_literature.json)

Ingen av filerna följer med kodförrådet (källregeln, METHODS.md §17): de innehåller korta utdrag ur upphovsrättsskyddade
texter. Saknas de, prövas fynden bara mot det som finns, och det står i svaret.

**Regeln (METHODS.md 14b, "Redan känt?").** Ett fynd som påstår något bestämt om en sten prövas mot texterna:

  ristarförslag   ristarens namn (utan Rundatas löpnummer: "Öpir 1" → Öpir) står som ristare i en av fyra fasta
                  vändningar: namnet följt av ristade, högg, risti eller hiogg ("Öpir ristade"); ristad, utförd, huggen,
                  signerad, attribuerad, tillskriven eller hänförd av, till eller åt namnet ("utförd av Öpir", "hänför den
                  … till Fot"); namnet i genitiv följt av ristningar, stenar, verk, skola, stil, hand, ornamentik,
                  runformer, signatur eller verkstad ("Gudfasts ristningar"); eller ristaren, runristaren eller mästaren
                  följt av namnet (och motsvarande på engelska: carved by, attributed to, the carver, Öpir's stones).
                  Vändningen ska stå i SRI:s artikel om stenen, på en tidskriftssida inom 300 tecken från stenens
                  signum, eller i ett utdrag ur registrets verk – och den ska gälla stenen själv: i tidskrifterna och
                  utdragen ska stenens signum vara det signum som står närmast vändningen, och i SRI:s artikel får ingen
                  annan stens signum stå inom 100 tecken från den. Dessutom räknas att SRI skriver att stenen är gjord av
                  "samme ristare (man, hand)" som en sten som Rundata ger åt samma ristare, och att litteraturens
                  attribuering (data/carver_literature.json) anger samma ristare
  släktlänk       den andra stenens signum står i SRI:s artikel om stenen, eller inom 300 tecken från stenens signum på
                  en tidskriftssida
  flyttad sten    (Runor 2020:s ursprungliga plats) SRI:s fyndhistorik säger att stenen var flyttad när bandet skrevs

Hittas påståendet blir fyndets status "nämns": nyheten sänks till högst 0,3 (samma tak som när Runor 2020 nämner
förslaget, src/crosscheck.apply), uppskattningen räknas om, och ett fynd som var "nytt" får bedömningen "Nämns redan i
litteraturen – läs där innan fyndet kallas nytt", så att det inte längre räknas som sannolikt ny kunskap. Ett fynd vars
sten bara diskuteras, utan att påståendet står där, får status "diskuteras" och behåller sin bedömning; skälen pekar ut
sidorna att läsa först. Andra fynd (seriation, skrivmiljöer, luckor i texten) har inget påstående som går att söka
efter i texten och får bara "diskuteras" eller "inte diskuterad".

Regeln är medvetet försiktig åt ett håll: en vändning räcker, också när texten avvisar attribueringen ("en
attribution som dock måste betecknas som osäker"), så att ingen läsning som redan finns räknas som ny. Den missar
attribueringar som bara säger "samme ristare som" om en sten utan ristare i Rundata, och namn som utgåvan stavar
annorlunda än Rundata. Utdragen visas, så att forskaren själv avgör.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache

from src.signum import fold_signum

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRI_MENTIONS = os.path.join(ROOT, "data", "cache", "literature", "sri_mentions.json")
JOURNAL_WINDOW = 300   # tecken på var sida om stenens signum på en tidskriftssida
NEAR = 100             # tecken: ett annat signum så nära en vändning gör att den gäller den andra stenen
EXCERPT = 110          # tecken på var sida om omnämnandet i ett utdrag (som src/literature.SNIPPET)
NOVELTY_CAP = 0.3
ASSESS_KNOWN = "Nämns redan i litteraturen – läs där innan fyndet kallas nytt"

_B = r"(?<![\wÅÄÖåäöÆØæøÞþ])"
_E = r"(?![\wÅÄÖåäöÆØæøÞþ])"
_SIGNS = r"(?i:ristade|risti|ristaði|ristat|högg|hiogg|hjó|markaði|carved)"
_BY = (r"(?i:rist(?:ad|at|ade|ningen|ningarna)|utför[dt]|huggen|hugget|signer(?:ad|at|ade)|attribu\w*|tillskriv\w*|"
       r"tilskriv\w*|hänför(?!\s+sig)\w*|carved|attributed|ascribed|signed)\b[^.;]{0,50}?\b(?:av|till|åt|by|to)\s+"
       r"(?:runristaren\s+|ristaren\s+|the\s+carver\s+)?")
_WORKS = (r"(?:s|'s|’s)\s+(?:ristningar|ristning|stenar|runstenar|verk|skola|stil|hand|ornamentik|runformer|signatur|"
          r"verkstad|krets|produktion|carvings|stones|runestones|workshop|style|oeuvre)" + _E)
_TITLE = r"(?i:runristaren|ristaren|ristare|mästaren|carver|rune-carver|runecarver)\s+"
SAME_CARVER = re.compile(r"samm?e\s+(?:ristare|man|mästare|hand)", re.I)
# Rundatas ristarnamn som inte är namn (en namnled, en runföljd): de söks inte
_NOT_NAMES = {"", "þuliR"}

STATUS_TEXT = {
    "nämns": "påståendet står redan i litteraturen",
    "diskuteras": "stenen diskuteras, men inte påståendet",
    "inte diskuterad": "ingen av källorna nämner stenen",
}


def carver_base(name: str | None) -> str | None:
    """Ristarnamnet utan Rundatas löpnummer och tillägg: "Öpir 1" → "Öpir", "Björn 2 eller -björn" → "Björn",
    "Torbjörn skald" → "Torbjörn", "Ulv i Borresta" → "Ulv"; None för namnleder och runföljder ("-fast")."""
    if not name:
        return None
    parts = name.split(" eller ")[0].split()
    n = parts[0] if parts else ""
    if n.startswith("-") or n in _NOT_NAMES or not n[:1].isupper():
        return None
    return n


def _alternatives(names: str) -> re.Pattern:
    """Regelns fyra vändningar (se överst) för ett eller flera namn, med namnet i en grupp per vändning."""
    return re.compile("|".join([
        _B + f"(?P<a>{names})" + r"(?:\s+skald|\s+\(\?\))?\s+(?:de\s+|själv\s+)?" + _SIGNS + _E,
        _BY + f"(?P<b>{names})" + r"s?" + _E,
        _B + f"(?P<c>{names})" + _WORKS,
        _B + _TITLE + f"(?P<d>{names})" + r"s?" + _E,
    ]))


@lru_cache(maxsize=512)
def name_pattern(base: str) -> re.Pattern:
    """Namnet som ristare i en av regelns fyra vändningar."""
    return _alternatives(re.escape(base))


def names_pattern(bases: list[str]) -> re.Pattern:
    """Alla namnen på en gång (snabbare än ett mönster per namn när en hel utgåva läses)."""
    return _alternatives("|".join(re.escape(b) for b in sorted(bases, key=len, reverse=True)))


def flat(text: str) -> str:
    """Löptext på en rad: avstavningar ihop, spärrad text ("Ö p i r") ihop, blanksteg utjämnade."""
    t = re.sub(r"-\s*\n\s*", "", text or "")
    t = re.sub(r"\b(?:[A-Za-zÅÄÖåäö] ){2,}[A-Za-zÅÄÖåäö]\b", lambda m: m.group(0).replace(" ", ""), t)
    return re.sub(r"\s+", " ", t).strip()


def excerpt(text: str, start: int, end: int, size: int = EXCERPT) -> str:
    a, b = max(0, start - size), min(len(text), end + size)
    return ("…" if a else "") + text[a:b].strip() + ("…" if b < len(text) else "")


def _nearest_signum(text: str, start: int, end: int, rx_signum: re.Pattern) -> tuple[str | None, int]:
    """Det signum som står närmast vändningen (start–end) i texten, och avståndet i tecken."""
    best, dist = None, 10 ** 9
    for m in rx_signum.finditer(text):
        d = max(0, start - m.end(), m.start() - end)
        if d < dist:
            best, dist = fold_signum(f"{m.group(1)} {m.group(2)}"), d
    return best, dist


def carver_mentions(text: str, names: dict[str, re.Pattern] | re.Pattern, rx_signum: re.Pattern | None = None,
                    own: str | None = None, window: bool = False) -> dict[str, str]:
    """Ristarnamnen som står som ristare i texten: namn → utdrag kring vändningen. names är antingen namn → mönster
    (name_pattern) eller ett mönster för alla namn (names_pattern).

    Med rx_signum och own (stenens vikta signum) ska vändningen gälla stenen själv: i ett utdrag eller ett fönster runt
    stenens signum (window=True) ska stenens signum vara det som står närmast vändningen; i stenens egen SRI-artikel får
    ingen annan stens signum stå inom NEAR tecken från den ("Även U 269 är säkerligen ristad av Fot" i en annan stens
    artikel gäller U 269, inte stenen)."""
    out: dict[str, str] = {}
    pats = [names] if isinstance(names, re.Pattern) else list(names.values())
    for rx in pats:
        for m in rx.finditer(text):
            base = next(g for g in (m.group(x) for x in "abcd") if g)
            if base in out:
                continue
            if rx_signum is not None and own is not None:
                near, dist = _nearest_signum(text, m.start(), m.end(), rx_signum)
                if window and near != own:
                    continue
                if not window and near is not None and near != own and dist <= NEAR:
                    continue
            out[base] = excerpt(text, m.start(), m.end())
    return out


def same_carver_refs(text: str, rx_signum: re.Pattern) -> list[tuple[str, str]]:
    """Stenarna som SRI säger är gjorda av "samme ristare (man, hand)": (vikt signum, utdrag)."""
    out = []
    for m in SAME_CARVER.finditer(text):
        tail = text[m.end(): m.end() + 100]
        sm = rx_signum.search(tail)
        if sm:
            out.append((fold_signum(f"{sm.group(1)} {sm.group(2)}"), excerpt(text, m.start(), m.end() + sm.end())))
    return out


# --- caches (built by the scripts; not in git) ---

_cache: dict[str, tuple[float, dict]] = {}


def _load(path: str) -> dict:
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return {}
    hit = _cache.get(path)
    if hit and hit[0] == mtime:
        return hit[1]
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    _cache[path] = (mtime, data)
    return data


def sri_for(signum: str) -> dict | None:
    """SRI:s artikel om stenen sammanfattad: verk, sidor, ristarnamn i ristarsammanhang, nämnda stenar."""
    return (_load(SRI_MENTIONS).get("stones") or {}).get(fold_signum(signum))


def version() -> str:
    """Källornas ändringstider, för cachenycklar."""
    from src import literature
    out = []
    for p in (SRI_MENTIONS, literature.JOURNALS, literature.INDEX):
        try:
            out.append(str(os.path.getmtime(p)))
        except OSError:
            out.append("0")
    return "|".join(out)


def available() -> dict[str, bool]:
    from src import literature
    return {"sri": os.path.exists(SRI_MENTIONS), "journals": os.path.exists(literature.JOURNALS),
            "register": os.path.exists(literature.INDEX)}


def journal_signa() -> set[str]:
    """De stenar (vikt signum) som någon tidskriftsartikel nämner i löptext, inte bara i ett register eller en lista."""
    from src import literature
    stones = _load(literature.JOURNALS).get("stones") or {}
    return {k for k, hs in stones.items() if any(not h.get("list") for h in hs)}


def _page(p: str | None) -> str | None:
    from src.literature import page_label
    return page_label(str(p)) if p else None


def _sri_work(work_id: str | None) -> dict:
    from src import literature
    works = {w["id"]: w for w in literature._load(literature.CATALOG).get("works") or []}
    w = works.get(work_id or "") or {}
    return {"work": w.get("title"), "author": (w.get("author") or "").split(",")[0] or None, "year": w.get("year"),
            "url": w.get("url")}


def _journal_articles(signum: str, limit: int = 5) -> tuple[list[dict], int]:
    """Tidskriftsartiklarna som nämner stenen i löptext, nyast först, med tryckta sidor där de går att räkna ut."""
    from src import literature
    jx = _load(literature.JOURNALS)
    arts = jx.get("articles") or {}
    by: dict[str, list[dict]] = {}
    for h in (jx.get("stones") or {}).get(fold_signum(signum)) or []:
        if not h.get("list"):
            by.setdefault(h["article"], []).append(h)
    out = []
    for key, hs in by.items():
        a = arts.get(key)
        if not a:
            continue
        out.append({"key": key, "journal": a["journal"], "year": a["year"], "title": a["title"],
                    "author": "; ".join(x.split(",")[0] for x in a["authors"][:3]) + (" m.fl." if len(a["authors"]) > 3 else ""),
                    "url": a.get("url"), "pages": [_page(h.get("printed") or h["page"]) for h in hs]})
    out.sort(key=lambda x: -int(x["year"] or 0))
    return out[:limit], len(out)


def _claim(f: dict) -> tuple[str, str] | None:
    """Vad fyndet påstår som går att söka efter: ("ristare", namn), ("länk", signum) eller ("flyttad", "")."""
    from src.stone_findings import LINK, RUNOR_PLACE
    if f.get("method") == LINK and f.get("linked"):
        return "länk", f["linked"]
    if f.get("method") == RUNOR_PLACE:
        return "flyttad", ""
    base = carver_base(f.get("suggested"))
    if base:
        return "ristare", base
    return None


def _claim_text(kind: str, value: str) -> str:
    return {"ristare": f"ristaren {value}", "länk": f"sambandet med {value}", "flyttad": "att stenen är flyttad"}[kind]


def check(f: dict, lookup=None, rundata_carvers: dict[str, set[str]] | None = None) -> dict:
    """Prövar ett fynd mot SRI, tidskrifterna och registret enligt regeln överst. Ändrar inte fyndet."""
    from src import carver_literature, literature
    signum = f["signum"]
    claim = _claim(f)
    hits: list[dict] = []
    sri = sri_for(signum)
    sri_meta = _sri_work(sri.get("work")) if sri else {}
    if claim and sri:
        kind, value = claim
        if kind == "ristare":
            m = (sri.get("carvers") or {}).get(value)
            if m:
                hits.append({"source": "SRI", **sri_meta, "page": _page(m.get("page")), "text": m.get("text")})
            elif rundata_carvers is not None:
                for ref in sri.get("same_as") or []:
                    if value in rundata_carvers.get(ref["signum"], ()):
                        hits.append({"source": "SRI", **sri_meta, "page": _page(ref.get("page")), "text": ref.get("text"),
                                     "via": ref["signum"]})
                        break
        elif kind == "länk":
            ref = (sri.get("signa") or {}).get(fold_signum(value))
            if ref:
                hits.append({"source": "SRI", **sri_meta, "page": _page(ref.get("page")), "text": ref.get("text")})
    if claim and claim[0] == "flyttad" and lookup is not None:
        from src import sri_fyndhistorik
        rec = lookup(signum)
        h = sri_fyndhistorik.for_inscription(rec) if rec else None
        pos = (h or {}).get("position") or {}
        if pos.get("value") == "flyttad":
            hits.append({"source": "SRI", "work": h.get("volume"), "author": None, "year": h.get("year"),
                         "url": h.get("url"), "page": pos.get("page") and _page(pos["page"]), "text": pos.get("quote")})
    if claim and claim[0] in ("ristare", "länk"):
        kind, value = claim
        jx = _load(literature.JOURNALS)
        arts = jx.get("articles") or {}
        for h in (jx.get("stones") or {}).get(fold_signum(signum)) or []:
            if h.get("list"):
                continue
            text = None
            if kind == "ristare":
                text = (h.get("carvers") or {}).get(value)
            elif fold_signum(value) in (h.get("co") or []):
                text = h.get("text")
            if text:
                a = arts.get(h["article"]) or {}
                hits.append({"source": "tidskrift", "work": a.get("journal"), "title": a.get("title"),
                             "author": "; ".join(x.split(",")[0] for x in (a.get("authors") or [])[:3]) or None,
                             "year": a.get("year"), "url": a.get("url"), "page": _page(h.get("printed") or h["page"]),
                             "text": text})
        idx = _load(literature.INDEX)
        works = {w["id"]: w for w in literature._load(literature.CATALOG).get("works") or []}
        for h in (idx.get("stones") or {}).get(fold_signum(signum)) or []:
            t = h.get("text")
            if h.get("list") or not t:
                continue
            ok = (kind == "ristare" and carver_mentions(t, {value: name_pattern(value)}, _signum_rx(), fold_signum(signum), True)) or \
                 (kind == "länk" and fold_signum(value) in {fold_signum(f"{m.group(1)} {m.group(2)}") for m in _signum_rx().finditer(t)})
            if ok:
                w = works.get(h["work"]) or {}
                hits.append({"source": "SRI" if (w.get("kind") == "utgåva") else "avhandling", "work": w.get("title"),
                             "author": (w.get("author") or "").split(",")[0] or None, "year": w.get("year"),
                             "url": w.get("url"), "page": _page(h["page"]), "text": t})
        if kind == "ristare":
            lit = carver_literature.carver_for(signum)
            if lit and carver_base(lit.get("carver")) == value:
                hits.append({"source": "avhandling", "work": lit.get("source_full") or lit["reference"], "author": None,
                             "year": None, "url": None, "page": None, "text": lit.get("text")})
    journals, n_journals = _journal_articles(signum)
    discussed = bool(sri or journals or (f.get("literature") or {}).get("n_works"))
    status = "nämns" if hits else ("diskuteras" if discussed else "inte diskuterad")
    # one hit per source and page is enough to read
    seen, uniq = set(), []
    for h in hits:
        k = (h["source"], h.get("work"), h.get("page"))
        if k not in seen:
            seen.add(k)
            uniq.append(h)
    # printed pages before PDF pages (a table of contents or a title page is the weakest place to read)
    uniq.sort(key=lambda h: (not h.get("page") or str(h["page"]).startswith("pdf")))
    return {"status": status, "status_text": STATUS_TEXT[status],
            "claim": _claim_text(*claim) if claim else None, "hits": uniq[:6], "n_hits": len(uniq),
            "sri": ({**sri_meta, "pages": [_page(p) for p in (sri.get("pages") or [])[:4]]} if sri else None),
            "journals": journals, "n_journals": n_journals}


@lru_cache(maxsize=1)
def _signum_rx_for(prefixes: tuple[str, ...]) -> re.Pattern:
    from src import literature
    return literature.signum_pattern(list(prefixes))


def _signum_rx() -> re.Pattern:
    return _signum_rx_for(("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Vs", "Nä", "Gs", "Hs", "M", "Ån", "J", "D", "Bo",
                           "Ds", "Vr", "Hr", "Lp", "DR", "N"))


def rundata_carver_bases(inscriptions: list[dict]) -> dict[str, set[str]]:
    """Vikt signum → Rundatas ristare (signerad eller attribuerad), som namn utan löpnummer."""
    out: dict[str, set[str]] = {}
    for r in inscriptions:
        names = {carver_base(c["name"]) for c in r.get("carvers") or [] if c.get("kind") in ("S", "A")}
        names.discard(None)
        if names:
            out[fold_signum(r["signum"])] = names  # type: ignore[assignment]
    return out


def annotate(items: list[dict], lookup=None, inscriptions: list[dict] | None = None) -> list[dict]:
    """Lägger "known" (Redan känt?) på varje fynd och tillämpar regeln: ett påstående som redan står i litteraturen
    sänker nyheten och tar fyndet ur "sannolikt ny kunskap". Fynden ändras på plats; skälen kopieras först, eftersom
    fynden kan vara delade med en cache."""
    carvers = rundata_carver_bases(inscriptions) if inscriptions is not None else None
    for f in items:
        if not f.get("signum"):
            continue
        k = check(f, lookup, carvers)
        k["changed"] = False
        f["known"] = k
        if k["status"] != "nämns" or f.get("verdict") not in ("nytt", "motsäger"):
            continue
        if (f.get("crosscheck") or {}).get("status") == "finns redan":
            continue  # already "Finns redan i nyare källa"
        f["reasons"] = {key: list(v) for key, v in (f.get("reasons") or {}).items()}
        first = k["hits"][0]
        where = " ".join(x for x in (first.get("author"), str(first.get("year") or "") or None, first.get("work"),
                                      first.get("page")) if x)
        note = f"{k['claim'][0].upper() + k['claim'][1:]} nämns redan i litteraturen ({where}" + \
               (f" och {k['n_hits'] - 1} ställen till" if k["n_hits"] > 1 else "") + ") – läs där innan fyndet kallas nytt"
        f["reasons"].setdefault("nyhet", []).append(note)
        if f.get("novelty", 0) > NOVELTY_CAP:
            f["novelty"] = NOVELTY_CAP
            f["score"] = round(f["evidence"] * f["novelty"] * f["relevance"], 3)
        if f["verdict"] == "nytt" and f.get("assessment", "").startswith(("Sannolikt ny", "Möjlig ny")):
            k["was"] = f["assessment"]
            f["assessment"] = ASSESS_KNOWN
            k["changed"] = True
    return items


def summary(items: list[dict]) -> dict:
    """Hur många fynd som fick varje status, och hur många som regeln tog ur "sannolikt ny kunskap"."""
    from collections import Counter
    c = Counter((f.get("known") or {}).get("status") for f in items if f.get("known"))
    changed = [f for f in items if (f.get("known") or {}).get("changed")]
    return {"status": dict(c), "changed": len(changed),
            "changed_likely": sum(1 for f in changed if f["known"].get("was", "").startswith("Sannolikt ny")),
            "sources": available()}
