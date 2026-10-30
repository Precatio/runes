"""Steg 1 i analysplaner/2026-10-30-namnen-utanfor-runstenarna.md: svenska Wiktionarys mans- och kvinnonamn med
etymologi (Kategori:Svenska/Mansnamn, Kategori:Svenska/Kvinnonamn). Skriver wiktionary_namn.json.
    .venv/bin/python utdata/namn_utanfor/hamta.py"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
API = "https://sv.wiktionary.org/w/api.php?"
UA = {"User-Agent": "Vitki/1.0 (runestone research; https://github.com/Precatio/runes)"}


def get(params):
    for _ in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(API + urllib.parse.urlencode(params), headers=UA),
                                                    timeout=60))
        except Exception:  # noqa: BLE001
            time.sleep(2)
    return {}


def members(cat):
    out, cont = [], {}
    while True:
        d = get({"action": "query", "list": "categorymembers", "cmtitle": cat, "cmlimit": 500, "format": "json", **cont})
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", []) if m["ns"] == 0]
        if "continue" not in d:
            return out
        cont = {"cmcontinue": d["continue"]["cmcontinue"]}


names = {}
for sex, cat in (("M", "Kategori:Svenska/Mansnamn"), ("K", "Kategori:Svenska/Kvinnonamn")):
    titles = members(cat)
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        d = get({"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main", "format": "json",
                 "titles": "|".join(batch)})
        for p in d.get("query", {}).get("pages", {}).values():
            txt = (p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("*", "")
            m = re.search(r"==Svenska==(.*?)(?:\n==[^=]|\Z)", txt, re.S)
            sv = m.group(1) if m else ""
            ety = re.findall(r"\{\{etymologi\|(.*?)\}\}\s*$", sv, re.M | re.S) or re.findall(r"etymologi\|([^\n]*)", sv)
            names.setdefault(p["title"], {"sex": set(), "etymology": []})
            names[p["title"]]["sex"].add(sex)
            names[p["title"]]["etymology"] += [e.strip() for e in ety if e.strip() not in names[p["title"]]["etymology"]]
        time.sleep(0.3)
out = {n: {"sex": sorted(v["sex"]), "etymology": v["etymology"]} for n, v in sorted(names.items())}
json.dump(out, open(os.path.join(OUT, "wiktionary_namn.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "namn;", sum(1 for v in out.values() if v["etymology"]), "med etymologi")
