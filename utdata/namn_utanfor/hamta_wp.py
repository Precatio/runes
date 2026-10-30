"""Avvikelse från planen (före resultat, 2026-10-30): namn utan etymologi i båda Wiktionary-utgåvorna får inledningen
ur svenska Wikipedias namnartikel ("X (namn)", "X (förnamn)" eller "X"). Bara namn med minst 10 bärare 1999 eller 2020.
Skriver wikipedia_namn.json. Med --myt: i stället de fornnordiska namnen i ursprung.csv som saknar Wikipedia-text,
för myt-markeringen (avvikelse före resultat), till wikipedia_myt.json.
    .venv/bin/python utdata/namn_utanfor/hamta_wp.py [--myt]"""
import sys
import collections
import csv
import json
import os
import time
import urllib.parse
import urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
API = "https://sv.wikipedia.org/w/api.php?"
UA = {"User-Agent": "Vitki/1.0 (runestone research; https://github.com/Precatio/runes)"}
scb, s99 = collections.Counter(), collections.Counter()
for x in json.load(open(os.path.join(ROOT, "data", "namn", "scb_tilltalsnamn.json"), encoding="utf-8"))["names"]:
    scb[x["name"]] += x["n2020"] or 0
    s99[x["name"]] += x.get("n1999") or 0
MYT = "--myt" in sys.argv
unk = [r["namn"] for r in csv.DictReader(open(os.path.join(OUT, "ursprung.csv"), encoding="utf-8"))
       if (r["ursprung"] == "fornnordiskt" and r["grund"] != "wikipedia" if MYT else r["ursprung"] == "okänt")
       and (scb[r["namn"]] >= 10 or s99[r["namn"]] >= 10)]


def extracts(titles):
    q = {"action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1, "redirects": 1, "format": "json",
         "exlimit": 20, "titles": "|".join(titles)}
    for i in range(4):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(API + urllib.parse.urlencode(q), headers=UA), timeout=60))
            break
        except Exception:  # noqa: BLE001
            time.sleep(3 * (i + 1))
    else:
        return {}
    back = {}
    for r in (d["query"].get("normalized") or []) + (d["query"].get("redirects") or []):
        back[r["to"]] = back.get(r["from"], r["from"])
    out = {}
    for p in d["query"]["pages"].values():
        if p.get("extract"):
            out[back.get(p["title"], p["title"])] = p["extract"][:1200]
    return out


res = {}
for suffix in (" (namn)", " (förnamn)", ""):
    todo = [n for n in unk if n not in res]
    for i in range(0, len(todo), 20):
        got = extracts([n + suffix for n in todo[i:i + 20]])
        for t, e in got.items():
            n = t[:-len(suffix)] if suffix and t.endswith(suffix) else t
            # a page on the name itself, not on a person or a place: the name's own article or one that calls it a name
            if n in todo and (suffix or "namn" in e[:300]):
                res[n] = e
        time.sleep(0.4)
json.dump(res, open(os.path.join(OUT, "wikipedia_myt.json" if MYT else "wikipedia_namn.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(len(unk), "namn utan etymologi;", len(res), "med en namnartikel i Wikipedia")
