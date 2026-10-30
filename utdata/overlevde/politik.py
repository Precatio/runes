"""Tillägg till analysplaner/2026-10-30-namnen-och-orden-som-overlevde.md (beskrivande, INTE i den låsta planen; lagt
till 2026-10-30 på Viktors begäran): maktens titlar och de politiska områdena på runstenarna – vad heter de i dag?
Steg 1: antal svenska runstenar per titel och område (Rundatas normalisering) och belägg för den nutida formen och de
medeltida ersättarna ur svenska Wiktionary (etymologi) och svenska Wikipedia (inledningen).
    .venv/bin/python utdata/overlevde/politik.py      Skriver politik_underlag.json."""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src.research_gaps import is_runestone  # noqa: E402

# lemma, regex on the normalization, Wiktionary word, Wikipedia page ("" = none)
TITLES = [
    ("konungr", r"\bkunung\w*", "kung", "Kung"), ("jarl", r"\biarl\w*", "jarl", "Jarl"),
    ("þegn", r"\bþegn\w*", "", "Tegn"), ("drengr", r"\bdræng\w*", "dräng", "Dräng"),
    ("hersir", r"\bhærsi\w*", "", "Hersir"), ("landmaðr", r"\blandmann\w*", "", ""),
    ("húskarl", r"\bhuskarl\w*", "huskarl", "Huskarl"), ("þingalið", r"\bþingalið\w*", "", "Tingalid"),
    ("stallari", r"\bstallar\w*", "stallare", "Stallare"), ("bryti", r"\bbryti\w*|\bbrytia\b", "bryte", "Bryte"),
    ("styrimaðr", r"\bstyrimann\w*|\bstyrimænn\w*", "styrman", ""), ("skipari", r"\bskipar[ai]\w*", "skeppare", ""),
    ("liðs forungi", r"\bforungi\b", "", ""), ("dróttinn", r"\bdrottin\w*", "drott", ""),
    ("þingstaðr", r"\bþingstað\w*", "ting", "Ting (folkförsamling)"), ("hundari", r"\bhu\[?n\]?dari\w*", "hundare", "Hundare"),
]
# the medieval and modern words for power to check (no runestone form)
NEW = [("hertig", "Hertig"), ("greve", "Greve"), ("drots", "Drots"), ("marsk", "Marsk"), ("kansler", "Kansler"),
       ("fogde", "Fogde"), ("riddare", "Riddare"), ("väpnare", "Väpnare"), ("adel", "Adel"), ("frälse", "Frälse"),
       ("lagman", "Lagman"), ("härad", "Härad"), ("häradshövding", "Häradshövding"), ("länsman", "Länsman"),
       ("riksdag", "Riksdag"), ("riksråd", "Riksråd"), ("biskop", "Biskop"), ("präst", "Präst"), ("socken", "Socken"),
       ("ledung", "Ledung"), ("drottning", ""), ("tingsrätt", "Tingsrätt"), ("hövding", "Hövding"), ("län", "Län")]
# area, regex, modern Swedish name, Wikipedia page
AREAS = [
    ("Svíþjóð", r"\bSveþiuð\w*", "Sverige", "Svitjod"), ("Danmork", r"\bDanmar?k\w*|\bDanma\b", "Danmark", ""),
    ("Gotland", r"\bGutland\w*", "Gotland", ""), ("Skáney", r"\bSkanøy\b", "Skåne", ""),
    ("England", r"\bÆngland\w*|\bÆngla\b|\bÆnglandsfari\b", "England", ""),
    ("Saxland", r"\bSaxland\w*", "Tyskland (Sachsen)", ""), ("Frísar", r"\bFrisa\b", "Friesland", ""),
    ("Heiðabýr", r"\bHæiðaby\w*", "Hedeby (övergivet)", "Hedeby"), ("Bað", r"\bBaðum\b", "Bath", ""),
    ("Langbarðaland", r"\bLangbarðal\w*", "Italien", "Langbardaland"),
    ("Grikkland / Grikkir", r"\bGrikk\w*", "Bysantinska riket", "Grikkland"),
    ("Jórsalir", r"\bIorsal\w*", "Jerusalem", ""), ("Serkland", r"\bSærkl\w*", "– (kalifatet)", "Serkland"),
    ("Garðar", r"\bGarð(?:um|a|ar)\b", "Ryssland (Kievriket)", "Gårdarike"),
    ("Holmgarðr", r"\bHolmgarð\w*", "Novgorod", "Holmgård"),
    ("Eistland", r"\bÆistland\w*|\bÆistaland\w*|\bÆistfari\b", "Estland", ""),
    ("Virland", r"\bVirland\w*", "Virumaa (Estland)", "Virland"),
    ("Lífland", r"\bLifland\w*", "Livland (Lettland, Estland)", "Livland"),
    ("Semgallar", r"\bSæimgal\w*", "Zemgale (Lettland)", "Semgallen"),
    ("Domisnes", r"\bDomisnæs\b", "Kolkasrags (Lettland)", "Domesnäs"),
    ("Finnland", r"\bFinnland\w*", "Finland", ""), ("Tafeistaland", r"\bTafæist\w*", "Tavastland (Finland)", "Tavastland"),
]

s = store()
recs = [r for r in s.inscriptions if is_runestone(r)]


def stones(rx):
    rg = re.compile(rx)
    return sorted(r["signum"] for r in recs if rg.search(r.get("normalization") or ""))


UA = {"User-Agent": "Vitki/1.0 (runestone research; https://github.com/Precatio/runes)"}


def get(url):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
    except Exception:  # noqa: BLE001
        return None


def wikt(word):
    d = get("https://sv.wiktionary.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "page": word, "prop": "wikitext", "format": "json"}))
    if not d or "error" in d:
        return None
    t = d["parse"]["wikitext"]["*"]
    m = re.search(r"==Svenska==(.*?)(?:\n==[^=]|\Z)", t, re.S)
    return m.group(1).strip()[:3000] if m else None


def wiki(page):
    d = get("https://sv.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1, "titles": page, "format": "json"}))
    if not d:
        return None
    p = next(iter(d["query"]["pages"].values()))
    return {"title": p.get("title"), "text": (p.get("extract") or "")[:2500]} if p.get("extract") else None


out = {"titles": [], "new": [], "areas": []}
for lem, rx, w, wp in TITLES:
    out["titles"].append({"lemma": lem, "stones": stones(rx), "wiktionary_word": w, "wiktionary": wikt(w) if w else None,
                          "wikipedia": wiki(wp) if wp else None})
    time.sleep(0.3)
for w, wp in NEW:
    out["new"].append({"word": w, "wiktionary": wikt(w), "wikipedia": wiki(wp) if wp else None})
    time.sleep(0.3)
for area, rx, modern, wp in AREAS:
    out["areas"].append({"area": area, "stones": stones(rx), "modern": modern, "wikipedia": wiki(wp) if wp else None})
    time.sleep(0.3)
json.dump(out, open(os.path.join(OUT, "politik_underlag.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for x in out["titles"]:
    print(x["lemma"], len(x["stones"]), x["stones"][:6], bool(x["wiktionary"]), bool(x["wikipedia"]))
for x in out["areas"]:
    print(x["area"], len(x["stones"]), x["stones"][:6], bool(x["wikipedia"]))
print("utan belägg:", [x["word"] for x in out["new"] if not x["wiktionary"]])
