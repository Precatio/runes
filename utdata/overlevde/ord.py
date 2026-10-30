"""Del B i analysplaner/2026-10-30-namnen-och-orden-som-overlevde.md: lever runstenarnas ord för makt, lag och kult kvar?
Steg 1: antal stenar per ord (Rundatas normalisering) och Wiktionarys uppslag för den moderna ättlingen (ord_wiktionary.json).
    .venv/bin/python utdata/overlevde/ord.py      Skriver ord_underlag.json."""
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

# domain, lemma, regex on the normalization (word forms), modern descendant(s) to look up ("" = none known)
WORDS = [
    # makt och rang
    ("makt", "konungr", r"\bkunung\w*", "kung|konung"), ("makt", "jarl", r"\biarls?\b|\bjarls?\b", "jarl"),
    ("makt", "þegn", r"\bþegn\w*", ""), ("makt", "drengr", r"\bdræng\w*", "dräng"),
    ("makt", "hersir", r"\bhersi\w*", ""), ("makt", "goði", r"\bgoða\b|\bgoði\b", ""),
    ("makt", "landmaðr", r"\blandmann\w*|\blandmænn\w*", ""), ("makt", "húskarl", r"\bhuskarl\w*", "huskarl"),
    ("makt", "styrimaðr", r"\bstyrimann\w*|\bstyrimænn\w*", "styrman"), ("makt", "skipari", r"\bskipar[ai]\w*", "skeppare"),
    ("makt", "lið", r"\bliði\b|\bliðs\b|\blið\b", "led"), ("makt", "dróttinn", r"\bdrottin\w*", "drott"),
    ("makt", "ríki", r"\briki\b|\brikis\b", "rike"), ("makt", "stallari", r"\bstallar\w*", "stallare"),
    ("makt", "félagi", r"\bfelag\w*", ""), ("makt", "sveinn (följesman)", r"\bsvæin(?:a|ar|aR)?\b", "sven"),
    # lag och ting
    ("lag", "þing", r"\bþing\w*", "ting"), ("lag", "lag", r"\blagh?\b|\blagha\b", "lag"),
    ("lag", "lagmaðr", r"\blagmann\w*", "lagman"), ("lag", "arfr", r"\barf\b|\barfs\b|\barfi\b", "arv"),
    ("lag", "erfa", r"\bærf\w*", "ärva"), ("lag", "eign", r"\bæign\w*", "ägo|egendom"),
    ("lag", "bú", r"\bbu\b|\bbui\b", "bo"), ("lag", "skipta", r"\bskipt\w*", "skifta"),
    ("lag", "vitni", r"\bvitni\w*", "vittne"),
    # kult och tro
    ("kult", "Guð", r"\bGuð\w*", "Gud"), ("kult", "Kristr", r"\bKrist\w*", "Krist"),
    ("kult", "sál", r"\bsal\b|\bsalu\b|\bsalua\b", "själ"), ("kult", "and (ônd)", r"\band\b|\bônd\b", "ande"),
    ("kult", "heilagr", r"\bhæilag\w*|\bhælg\w*", "helig"), ("kult", "kirkja", r"\bkirkiu\b|\bkirkia\b|\bkirkiu\w*", "kyrka"),
    ("kult", "kross", r"\bkross\w*", "kors"), ("kult", "vígja", r"\bvigi\b|\bvigði\b", "viga"),
    ("kult", "vé", r"\bve\b|\bvi\b", ""), ("kult", "Þórr", r"\bÞorr\b", "Tor"),
    ("kult", "blót", r"\bblot\w*", "blot"),
    # släkt
    ("släkt", "faðir", r"\bfaður\b|\bfeðr\w*", "fader|far"), ("släkt", "móðir", r"\bmoður\b|\bmøðr\w*", "moder|mor"),
    ("släkt", "bróðir", r"\bbroður\b|\bbrøðr\w*", "broder|bror"), ("släkt", "systir", r"\bsystur\b|\bsystir\b", "syster"),
    ("släkt", "sonr", r"\bsun\b|\bsyni\b|\bsyniR\b|\bsunu\b", "son"), ("släkt", "dóttir", r"\bdottur\b|\bdøtr\w*", "dotter"),
    ("släkt", "kona", r"\bkonu\b|\bkona\b", "kona"), ("släkt", "bóndi (make)", r"\bbonda\b|\bboanda\b", "bonde"),
    ("släkt", "fóstri", r"\bfostr\w*", "fostra"), ("släkt", "mágr", r"\bmag\b|\bmagh\b|\bmaga\b", "måg"),
    ("släkt", "frændi", r"\bfrænd\w*", "frände"), ("släkt", "barn", r"\bbarn\w*", "barn"),
    ("släkt", "erfingi", r"\bærfing\w*", "arvinge"),
    # vardag och natur
    ("vardag", "steinn", r"\bstæin\w*", "sten"), ("vardag", "brú", r"\bbro\b|\bbru\b|\bbroa\b", "bro"),
    ("vardag", "vegr", r"\bveg\w*|\bvæg\w*", "väg"), ("vardag", "land", r"\bland\w*", "land"),
    ("vardag", "skip", r"\bskip\b|\bskipi\b|\bskipa\b", "skepp"), ("vardag", "kuml", r"\bkumbl\w*", "kummel"),
    ("vardag", "hús", r"\bhus\b|\bhusi\b", "hus"), ("vardag", "bý", r"\bby\b|\bbyi\b", "by"),
    ("vardag", "garðr", r"\bgarð\w*", "gård"), ("vardag", "hestr", r"\bhæst\w*", "häst"),
    ("vardag", "haugr", r"\bhaug\w*", "hög"), ("vardag", "sjór", r"\bsio\b|\bsiau\b", "sjö"),
    ("vardag", "eyja", r"\bøy\w*|\bey\w*", "ö"), ("vardag", "dauðr", r"\bdauð\w*", "död"),
    ("vardag", "deyja", r"\bdo\b|\bdou\b", "dö"), ("vardag", "fara", r"\bfor\b|\bforu\b|\bfara\b", "fara"),
    ("vardag", "ráða", r"\bræð\w*|\braða\b|\bred\b", "råda"), ("vardag", "rísta", r"\brist\w*|\brest\b", "rista"),
    ("vardag", "hôggva", r"\bhiogg\w*|\bhioggu\b", "hugga"), ("vardag", "góðr", r"\bgoð\w*", "god"),
]

s = store()
recs = [r for r in s.inscriptions if is_runestone(r)]
counts = {}
for dom, lem, rx, _ in WORDS:
    rg = re.compile(rx)
    counts[lem] = sum(1 for r in recs if rg.search(r.get("normalization") or ""))

UA = {"User-Agent": "Vitki/1.0 (runestone research; https://github.com/Precatio/runes)"}


def wikt(word: str) -> str | None:
    url = "https://sv.wiktionary.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "page": word, "prop": "wikitext", "format": "json"})
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
    except Exception:  # noqa: BLE001
        return None
    if "error" in d:
        return None
    t = d["parse"]["wikitext"]["*"]
    m = re.search(r"==Svenska==(.*?)(?:\n==[^=]|\Z)", t, re.S)
    return m.group(1).strip() if m else None


wk = {}
for _, lem, _, mod in WORDS:
    for w in [x for x in mod.split("|") if x]:
        if w not in wk:
            wk[w] = wikt(w)
            time.sleep(0.3)
json.dump({"counts": counts, "words": [{"domain": d, "lemma": l, "regex": r, "modern": m} for d, l, r, m in WORDS],
           "wiktionary": wk}, open(os.path.join(OUT, "ord_underlag.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({l: counts[l] for _, l, _, _ in WORDS})
print("utan Wiktionary-uppslag:", [w for w, v in wk.items() if not v])
