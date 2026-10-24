"""Besöksstatistik för den publika webbplatsen (vitkirunor.se), sammanfattad för Admin.

Webbplatsen skriver en rad per visad sida och en per avsnitt på startsidan som besökaren har scrollat till
(web/src/components/SiteTracker.tsx, samlingen site_views i Firestore), och dessutom en rad per sökning i artikelsökningen
(sökorden och antalet träffar), per klick på en delningsknapp, en utgående länk eller en språklänk (web/src/lib/track.ts).
En sidvisning bär också sidan besökaren kom från inne på webbplatsen (`prev`, bara ur minnet, aldrig sparad på enheten) och,
för ett besök som började i en delad länk, delningskanalen (`via`). Raderna har ingen identifierare, ingen kaka och ingen
IP-adress, så *besök* räknas som sidvisningar där besökaren kom utifrån (eller utan hänvisning) – inte som unika personer.
Landet är ungefärligt: det läses ur webbläsarens tidszon, och en stad går inte att få fram utan IP-adress.
"""
from __future__ import annotations

import datetime as dt
import re
from collections import Counter

# Time zone -> country; the zones the Nordic countries and their neighbours use, other zones by continent
COUNTRIES = {
    "Europe/Stockholm": "Sverige", "Europe/Oslo": "Norge", "Arctic/Longyearbyen": "Norge", "Europe/Copenhagen": "Danmark",
    "Atlantic/Faroe": "Färöarna", "America/Nuuk": "Grönland", "Europe/Helsinki": "Finland", "Europe/Mariehamn": "Åland",
    "Atlantic/Reykjavik": "Island", "Europe/Berlin": "Tyskland", "Europe/London": "Storbritannien",
    "Europe/Dublin": "Irland", "Europe/Amsterdam": "Nederländerna", "Europe/Brussels": "Belgien", "Europe/Paris": "Frankrike",
    "Europe/Zurich": "Schweiz", "Europe/Vienna": "Österrike", "Europe/Warsaw": "Polen", "Europe/Prague": "Tjeckien",
    "Europe/Tallinn": "Estland", "Europe/Riga": "Lettland", "Europe/Vilnius": "Litauen", "Europe/Rome": "Italien",
    "Europe/Madrid": "Spanien", "Europe/Lisbon": "Portugal", "Europe/Kyiv": "Ukraina", "Europe/Kiev": "Ukraina",
    "America/New_York": "USA", "America/Chicago": "USA", "America/Denver": "USA", "America/Los_Angeles": "USA",
    "America/Phoenix": "USA", "America/Anchorage": "USA", "Pacific/Honolulu": "USA", "America/Toronto": "Kanada",
    "America/Vancouver": "Kanada", "Australia/Sydney": "Australien", "Australia/Melbourne": "Australien",
    "Asia/Tokyo": "Japan",
}
CONTINENTS = {"Europe": "övriga Europa", "America": "övriga Amerika", "Asia": "Asien", "Africa": "Afrika",
              "Australia": "Oceanien", "Pacific": "Oceanien", "Atlantic": "övriga världen", "Indian": "övriga världen"}
LANGUAGES = {"sv": "svenska", "en": "engelska", "nb": "norska", "nn": "norska", "no": "norska", "da": "danska",
             "fi": "finska", "is": "isländska", "de": "tyska", "fr": "franska", "nl": "nederländska", "es": "spanska",
             "it": "italienska", "pl": "polska"}
TOP = 15
SHARE_CHANNELS = {"lank": "Kopiera länk", "enhet": "Enhetens delning", "bluesky": "Bluesky", "x": "X", "facebook": "Facebook",
                  "linkedin": "LinkedIn", "epost": "E-post"}
LANGUAGE_CLICKS = {"en": "Till engelska versionen", "sv": "Till svenska versionen"}
# The topics in the vote on the articles page (web/src/components/ContentVote.tsx, label "rost:<key>"; same keys there)
VOTE_TOPICS = {"ristare": "Ristarna och deras händer", "tro": "Tro – från Tor till Kristus",
               "kvinnor": "Kvinnor och barn på stenarna", "fard": "Vikingafärder: England, Grekland, Ingvar",
               "sprak": "Språket och stavningen", "lasning": "Skadade och olästa inskrifter",
               "landskap": "Stenarna i landskapet", "magi": "Magi, förbannelser och skydd",
               "eddan": "Eddan och fornnordisk dikt", "norden": "Danmark, Norge och gränserna",
               "metod": "Hur metoderna fungerar – statistik och 3D", "guider": "Guider till Vitki, steg för steg"}


def country(tz: str | None) -> str:
    if not tz:
        return "okänt"
    return COUNTRIES.get(tz) or CONTINENTS.get(tz.split("/")[0], "okänt")


def language(code: str | None) -> str:
    base = (code or "").split("-")[0].lower()
    return LANGUAGES.get(base, base or "okänt")


def _top(counter: Counter, n: int = TOP) -> list[dict]:
    return [{"key": k, "n": v} for k, v in counter.most_common(n)]


# Rows that certainly come from a robot. The tracker (web/src/lib/track.ts) has left robots out since 2026-10-22 by
# their user agent; the rows written before that carry no user agent, so only the two settings no person's browser
# has are used here: a time zone the browser cannot name, and a POSIX locale such as en-US@posix (server browsers).
def known_bot(r: dict) -> bool:
    return (r.get("tz") or "") == "Etc/Unknown" or "@" in (r.get("lang") or "")


# Votes are anonymous rows anyone can write with a script (Firestore's rules cannot limit how often), so Admin counts at
# most VOTE_CAP rows per topic and day – per answer and day in site_votes, per topic or per own suggestion (the same
# text) and day in the votes on the articles page. The raw counts are kept beside the counted ones.
VOTE_CAP = 10


def capped(pairs, cap: int = VOTE_CAP) -> tuple[Counter, Counter]:
    """Räknar (nyckel, dag)-par: högst `cap` per nyckel och dag (det räknade) och alla (det råa), per nyckel."""
    counted: Counter = Counter()
    raw: Counter = Counter()
    for (key, _day), n in Counter(pairs).items():
        raw[key] += n
        counted[key] += min(n, cap)
    return counted, raw


def _capped_rows(counted: Counter, raw: Counter, names: dict[str, str] | None = None, n: int = TOP) -> list[dict]:
    # Ordered by the counted number; ties keep the order of first appearance, as Counter.most_common does
    top = sorted(counted.items(), key=lambda kv: kv[1], reverse=True)[:n]
    return [{"key": (names or {}).get(k, k), "n": c, "raw": raw[k]} for k, c in top]


def _vote_day(created) -> str | None:
    if created is None:
        return None
    if getattr(created, "tzinfo", None) is not None:
        created = created.astimezone(dt.timezone.utc)
    return created.date().isoformat()


def summarize_votes(votes: list[tuple[dict, object]], cap: int = VOTE_CAP) -> list[dict]:
    """Röstningen på startsidan (samlingen site_votes, web/src/components/SiteVote.tsx): röster per fråga och svar,
    högst `cap` per svar och dag (dagen då dokumentet skapades, UTC), och de råa talen bredvid. `votes` är par av
    dokumentets fält och dess create_time."""
    pairs: dict[str, list] = {}
    times: dict[str, list] = {}
    for v, created in votes:
        q = v.get("question", "?")
        pairs.setdefault(q, []).append((v.get("choice", "?"), _vote_day(created)))
        if created is not None:
            times.setdefault(q, []).append(created)
    out = []
    for q, p in pairs.items():
        counted, raw = capped(p, cap)
        out.append({"question": q, "total": sum(counted.values()), "raw_total": sum(raw.values()),
                    "choices": dict(counted), "raw_choices": dict(raw), "cap": cap,
                    "first": min(times[q]).isoformat() if times.get(q) else None,
                    "last": max(times[q]).isoformat() if times.get(q) else None})
    return out


def summarize(rows: list[dict], since: dt.date, days: int, titles: dict[str, str] | None = None,
              day: str | None = None, vote_cap: int = VOTE_CAP) -> dict:
    """Sammanfattar raderna från och med `since` (`days` dagar): totaler, per dag, sidor, avsnitt på startsidan,
    hänvisande webbplatser, land, språk och enhet. `titles` ger sidornas namn (sökväg -> titel). Med `day` (ÅÅÅÅ-MM-DD)
    räknas allt utom stapeldiagrammet per dag bara på den dagens rader – så att ett klick på en stapel i Admin visar
    vilka sidor, länder och sökord dagen bestod av."""
    titles = titles or {}
    rows = [r for r in rows if not known_bot(r)]
    per_day = {(since + dt.timedelta(days=i)).isoformat(): {"views": 0, "visits": 0} for i in range(days)}
    for r in rows:
        d = per_day.get(r.get("day") or "") if r.get("kind") == "view" else None
        if d is not None:
            d["views"] += 1
            d["visits"] += bool(r.get("entry"))
    if day:
        rows = [r for r in rows if r.get("day") == day]
    views = [r for r in rows if r.get("kind") == "view"]
    sections = [r for r in rows if r.get("kind") == "section"]
    searches = [r for r in rows if r.get("kind") == "search" and r.get("label")]
    clicks = [r for r in rows if r.get("kind") == "click" and r.get("label")]
    title = lambda p: titles.get(p) or p  # noqa: E731
    visits = sum(bool(r.get("entry")) for r in views)
    pages = Counter(r.get("path") or "/" for r in views)
    start_views = pages.get("/", 0)
    reached = Counter(r.get("section") for r in sections if (r.get("path") or "/") == "/" and r.get("section"))
    refs = Counter(r.get("ref") for r in views if r.get("entry") and r.get("ref"))
    direct = sum(1 for r in views if r.get("entry") and not r.get("ref"))
    shares = [r for r in clicks if r["label"].startswith("dela:")]

    def clicked(prefix: str, names: dict[str, str] | None = None) -> list[dict]:
        c = Counter(r["label"][len(prefix):] for r in clicks if r["label"].startswith(prefix))
        return [{"key": (names or {}).get(k, k), "n": n} for k, n in c.most_common(TOP)]

    # The votes on the articles page, at most `vote_cap` rows per topic (or own suggestion) and day
    def votes(prefix: str, names: dict[str, str] | None = None) -> tuple[list[dict], dict]:
        counted, raw = capped(((r["label"][len(prefix):], r.get("day")) for r in clicks if r["label"].startswith(prefix)),
                              vote_cap)
        return _capped_rows(counted, raw, names), {"counted": sum(counted.values()), "raw": sum(raw.values())}

    topic_votes, topic_totals = votes("rost:", VOTE_TOPICS)
    text_votes, text_totals = votes("rost-eget:")
    flow = Counter((r["prev"], r.get("path") or "/") for r in views if r.get("prev"))
    entries = Counter(r.get("path") or "/" for r in views if r.get("entry"))
    return {
        "since": since.isoformat(), "days": days, "day": day,
        "views": len(views), "visits": visits,
        "per_day": [{"day": k, **v} for k, v in per_day.items()],
        "pages": [{"path": p, "title": titles.get(p), "n": n} for p, n in pages.most_common(TOP)],
        # Share of the start page's views that reached each section (scrolled to the middle of the screen)
        "sections": [{"key": k, "n": n, "share": n / start_views if start_views else None} for k, n in reached.most_common()],
        "referrers": _top(refs), "direct": direct,
        "countries": _top(Counter(country(r.get("tz")) for r in views)),
        "languages": _top(Counter(language(r.get("lang")) for r in views)),
        "devices": _top(Counter(r.get("device") or "okänt" for r in views)),
        # Sökningarna i artikelsökningen: orden, och de som inte gav någon träff (luckor i innehållet)
        "searches": {"total": len(searches),
                     "top": _top(Counter(r["label"] for r in searches)),
                     "no_hits": _top(Counter(r["label"] for r in searches if r.get("hits") == 0))},
        # Klick: delningsknappar per kanal, de mest delade sidorna, utgående länkar och språklänkar
        "clicks": {"share": clicked("dela:", SHARE_CHANNELS), "outbound": clicked("ut:"),
                   "language": clicked("sprak:", LANGUAGE_CLICKS),
                   # The vote on the articles page: chosen topics and own suggestions (free text, up to 70 characters)
                   # (n = counted, at most vote_cap per topic and day; raw = every row)
                   "votes": topic_votes, "vote_texts": text_votes,
                   "vote_cap": {"per_day": vote_cap, "votes": topic_totals, "vote_texts": text_totals},
                   "shared_pages": [{"key": title(p), "n": n} for p, n in
                                    Counter(r.get("path") or "/" for r in shares).most_common(TOP)]},
        # Besök som började i en delad länk, per delningskanal
        "via": [{"key": SHARE_CHANNELS.get(k, k), "n": n} for k, n in
                Counter(r.get("via") for r in views if r.get("entry") and r.get("via")).most_common()],
        # Vägen mellan sidorna inom ett besök, och sidorna besöken börjar på
        "flow": [{"key": f"{title(a)} → {title(b)}", "n": n} for (a, b), n in flow.most_common(TOP)],
        "entries": [{"path": p, "title": titles.get(p), "n": n} for p, n in entries.most_common(TOP)],
    }


ARTICLE_PATH = re.compile(r"^/(en/)?artiklar/([^/?#]+)/?$")


def views_by_slug(rows: list[dict]) -> dict[str, int]:
    """Sidvisningar per artikel (svenska och engelska sidan räknade ihop), för sorteringen "mest lästa" på
    webbplatsen. Bara rader av slaget view; andra sidor räknas inte."""
    out: Counter = Counter()
    for r in rows:
        if r.get("kind") != "view" or known_bot(r):
            continue
        m = ARTICLE_PATH.match(r.get("path") or "")
        if m:
            out[m.group(2)] += 1
    return dict(out)


def page_titles(posts: list[dict]) -> dict[str, str]:
    """Sidornas namn: startsidan, artikellistan och varje publicerad artikel."""
    out = {"/": "Startsidan", "/artiklar": "Artiklar (listan)", "/en/artiklar": "Articles (list, English)"}
    out.update({f"/artiklar/{p['slug']}": p.get("title") or p["slug"] for p in posts if p.get("slug")})
    out.update({f"/en/artiklar/{p['slug']}": f"{p.get('title_en') or p.get('title') or p['slug']} (engelska)"
                for p in posts if p.get("slug") and p.get("title_en")})
    return out
