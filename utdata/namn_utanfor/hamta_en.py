"""Avvikelse från planen (före resultat, 2026-10-30): svenska Wiktionary saknar etymologi för de flesta namn (Ragnar,
Astrid, Ingvar), så engelska Wiktionarys "Swedish male/female given names" (med underkategorier) läggs till som andra
källa. Skriver wiktionary_en_namn.json med etymologiavsnittet för svenska.
    .venv/bin/python utdata/namn_utanfor/hamta_en.py"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
API = "https://en.wiktionary.org/w/api.php?"
UA = {"User-Agent": "Vitki/1.0 (runestone research; https://github.com/Precatio/runes)"}


def get(params):
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(API + urllib.parse.urlencode(params), headers=UA),
                                                    timeout=60))
        except Exception:  # noqa: BLE001
            time.sleep(3 * (i + 1))
    return {}


def members(cat, depth=1):
    pages, cont = [], {}
    while True:
        d = get({"action": "query", "list": "categorymembers", "cmtitle": cat, "cmlimit": 500, "format": "json", **cont})
        for m in d.get("query", {}).get("categorymembers", []):
            if m["ns"] == 0:
                pages.append(m["title"])
            elif m["ns"] == 14 and depth > 0:
                pages += members(m["title"], depth - 1)
        if "continue" not in d:
            return pages
        cont = {"cmcontinue": d["continue"]["cmcontinue"]}


names = {}
for sex, cat in (("M", "Category:Swedish male given names"), ("K", "Category:Swedish female given names")):
    titles = sorted(set(members(cat)))
    for i in range(0, len(titles), 50):
        d = get({"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main", "format": "json",
                 "titles": "|".join(titles[i:i + 50])})
        for p in d.get("query", {}).get("pages", {}).values():
            txt = (p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("*", "")
            m = re.search(r"==Swedish==(.*?)(?:\n==[^=]|\Z)", txt, re.S)
            sw = m.group(1) if m else ""
            ety = re.findall(r"===+Etymology[^=]*===+\n(.*?)(?=\n===|\Z)", sw, re.S)
            e = names.setdefault(p["title"], {"sex": set(), "etymology": []})
            e["sex"].add(sex)
            e["etymology"] += [x.strip() for x in ety if x.strip() and x.strip() not in e["etymology"]]
        time.sleep(0.5)
out = {n: {"sex": sorted(v["sex"]), "etymology": v["etymology"]} for n, v in sorted(names.items())}
json.dump(out, open(os.path.join(OUT, "wiktionary_en_namn.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "namn;", sum(1 for v in out.values() if v["etymology"]), "med etymologi")
