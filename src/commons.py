"""Bilder av runstenar ur Wikimedia Commons, till Månadens fynd.

Wikidata anger vilken bild som visar en runsten (P18) för stenar med signum i Samnordisk runtextdatabas (P1261), och
Commons API ger en tumnagel och bildens upphovsperson och licens, som ska stå i bildtexten. Svaren sparas i
data/cache/commons/ i 30 dagar, så att samma sten inte hämtas igen. Bara bilder med en känd fri licens tas med.
"""
from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "cache", "commons")
TTL = 30 * 24 * 3600
UA = "Vitki/2.0 (https://vitkirunor.se; runology research)"
WDQS = "https://query.wikidata.org/sparql"
COMMONS = "https://commons.wikimedia.org/w/api.php"
WIDTH = 1200
FREE = re.compile(r"^(CC0|CC BY(-SA)? [0-9.]+( [a-z]{2})?|Public domain|PD.*)$", re.I)
# Signa as Rundata writes them ("U 344", "Sö 101", "Ög 136", "U 649B", "DR 42"), for finding the stones in a text
SIGNUM = re.compile(r"\b(?:U|Sö|Ög|Vg|Sm|Ög|Öl|Gs|Hs|Hä|Vs|Nä|Bo|Ds|Ång|M|J|G|DR|N)\s\d{1,4}[A-Z]?\b")


def _get(url: str, params: dict) -> dict:
    req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _cache_path(signum: str) -> str:
    return os.path.join(CACHE, re.sub(r"[^\w]+", "_", signum) + ".json")


def _cached(signum: str) -> dict | None:
    try:
        with open(_cache_path(signum), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if time.time() - d.get("fetched", 0) < TTL else None
    except (OSError, ValueError):
        return None


def _store(signum: str, d: dict) -> None:
    os.makedirs(CACHE, exist_ok=True)
    with open(_cache_path(signum), "w", encoding="utf-8") as fh:
        json.dump({**d, "fetched": time.time()}, fh, ensure_ascii=False)


def _url(u: str | None) -> str | None:
    """Utan Commons spårningsparametrar och med parenteser kodade, så att adressen fungerar i en markdown-länk."""
    if not u:
        return None
    parts = urllib.parse.urlsplit(u)
    query = urllib.parse.urlencode([(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if not k.startswith("utm_")])
    return urllib.parse.urlunsplit(parts._replace(query=query)).replace("(", "%28").replace(")", "%29")


def _text(v: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", v or ""))).strip()


def wikidata_files(signa: list[str]) -> dict[str, str]:
    """Signum → filnamnet på Commons för de stenar som har en bild i Wikidata."""
    if not signa:
        return {}
    values = " ".join(json.dumps(s, ensure_ascii=False) for s in signa)
    q = f"SELECT ?sig ?img WHERE {{ VALUES ?sig {{ {values} }} ?item wdt:P1261 ?sig ; wdt:P18 ?img }}"
    out = {}
    for b in _get(WDQS, {"query": q, "format": "json"})["results"]["bindings"]:
        name = urllib.parse.unquote(b["img"]["value"].rsplit("/", 1)[-1])
        out.setdefault(b["sig"]["value"], name)
    return out


def commons_info(files: list[str]) -> dict[str, dict]:
    """Filnamn → tumnagel, sida, upphovsperson och licens."""
    out = {}
    for i in range(0, len(files), 40):
        chunk = files[i:i + 40]
        d = _get(COMMONS, {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|extmetadata|size",
                           "iiurlwidth": WIDTH, "titles": "|".join("File:" + f for f in chunk)})
        norm = {n["to"]: n["from"] for n in d.get("query", {}).get("normalized", [])}
        for page in d.get("query", {}).get("pages", {}).values():
            ii = (page.get("imageinfo") or [None])[0]
            if not ii:
                continue
            meta = ii.get("extmetadata") or {}
            title = norm.get(page["title"], page["title"])
            out[title.removeprefix("File:")] = {
                "thumb": _url(ii.get("thumburl") or ii.get("url")), "page": _url(ii.get("descriptionurl")),
                "width": ii.get("thumbwidth"), "height": ii.get("thumbheight"),
                "author": _text((meta.get("Artist") or {}).get("value")) or _text((meta.get("Credit") or {}).get("value")),
                "licence": _text((meta.get("LicenseShortName") or {}).get("value")),
                "licence_url": _url((meta.get("LicenseUrl") or {}).get("value")),
                "description": _text((meta.get("ImageDescription") or {}).get("value"))[:300],
            }
    return out


def caption(img: dict, lang: str = "sv") -> str:
    """Bildtexten: stenen, fotografen och licensen, med länk till bildens sida på Commons."""
    who = img.get("author") or ("okänd" if lang == "sv" else "unknown")
    lic = f"[{img['licence']}]({img['licence_url']})" if img.get("licence_url") else img["licence"]
    photo = "Foto" if lang == "sv" else "Photo"
    return f"{img['signum']}. {photo}: {who}, {lic}, via [Wikimedia Commons]({img['page']})."


def markdown(img: dict, lang: str = "sv") -> str:
    """Bilden som block i ett blogginlägg (components/BlogBody.tsx): ![alt](url) och bildtexten på nästa rad."""
    alt = f"Runstenen {img['signum']}" if lang == "sv" else f"The runestone {img['signum']}"
    return f"![{alt}]({img['thumb']})\n{caption(img, lang)}"


def stone_images(signa: list[str]) -> list[dict]:
    """En bild per sten som har en fritt licensierad bild, i samma ordning som signa."""
    signa = list(dict.fromkeys(s.strip() for s in signa if s and s.strip()))[:20]
    got = {s: c for s in signa if (c := _cached(s)) is not None}
    todo = [s for s in signa if s not in got]
    if todo:
        files = wikidata_files(todo)
        info = commons_info(list(set(files.values()))) if files else {}
        for s in todo:
            f = files.get(s)
            d = {"signum": s, "file": f, **info[f]} if f and f in info else {"signum": s, "file": None}
            _store(s, d)
            got[s] = d
    out = []
    for s in signa:
        d = got[s]
        if not d.get("file") or not d.get("thumb") or not FREE.match(d.get("licence") or ""):
            continue
        img = {k: v for k, v in d.items() if k != "fetched"}
        out.append({**img, "markdown": markdown(img, "sv"), "markdown_en": markdown(img, "en")})
    return out


def signa_in(text: str) -> list[str]:
    """De signum som nämns i en text, i den ordning de först förekommer."""
    return list(dict.fromkeys(m.group(0) for m in SIGNUM.finditer(text or "")))
