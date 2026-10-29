"""Hämtar ord med versal och fader–barn-par ur de svenskspråkiga medeltidsbreven (SDHK-SVENSKA i Språkbankens Korp),
med brev, datum och utfärdandeort, för planen analysplaner/2026-10-29-namnen-som-levde-kvar.md.
    .venv/bin/python utdata/namnarv/hamta.py      Skriver ord.csv och par.csv."""
import csv
import os

import requests

OUT = os.path.dirname(os.path.abspath(__file__))
API = "https://ws.spraakbanken.gu.se/ws/korp/v8/count"
H = {"User-Agent": "Vitki/1.0 (runestone research; https://github.com/Precatio/runes)"}
CAP = "[A-ZÅÄÖÆØÞÐ][a-zåäöæøþðéüyw]+"
PATR = CAP[:-1] + "*(son|sson|sun|ssun|søn|dotter|dottir|dotir|dottor|dotor|dottur|döttir|dotr)"
STRUCT = "text_id,text_datefrom,text_place"


def count(cqp):
    j = requests.get(API, params={"corpus": "SDHK-SVENSKA", "cqp": cqp, "group_by": "word", "group_by_struct": STRUCT},
                     headers=H, timeout=600).json()
    return j["corpora"]["SDHK-SVENSKA"]["rows"]


def rows(rs, n_words):
    for r in rs:
        v = r["value"]
        w = v["word"] if isinstance(v["word"], list) else [v["word"]]
        yield [*w[:n_words], v["text_id"], v["text_datefrom"], v["text_place"], r["absolute"]]


allt = {tuple(x[:4]): x[4] for x in rows(count(f'[word="{CAP}"]'), 1)}
inne = {tuple(x[:4]): x[4] for x in rows(count(f'[word="{CAP}" & !lbound(sentence)]'), 1)}
with open(os.path.join(OUT, "ord.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["ord", "brev", "datum", "ort", "antal", "antal_inne_i_mening"])
    for k, n in sorted(allt.items()):
        w.writerow([*k, n, inne.get(k, 0)])
with open(os.path.join(OUT, "par.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["fornamn", "patronymikon", "brev", "datum", "ort", "antal"])
    w.writerows(rows(count(f'[word="{CAP}"] [word="{PATR}"]'), 2))
print(len(allt), "ord/brev-rader", sum(allt.values()), "belägg")
