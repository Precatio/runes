"""Nya drag för attribueringsmodellen version 2 (analysplaner/2026-11-04-attribuering-v2.md):

1. Korsformen enligt Lagers typologi ur RAÄ:s Runor 2020 (data/raa/runor_2020.json): för varje kombination aspekt+form
   på minst MIN_CROSS runstenar i korpusen ett ja/nej-drag; en sten med kors men utan typologi får okänt (tomt).
2. Stavningsavtrycket: för de N_WORDS vanligaste normaliserade orden (ordparen i korpusen; namn finns inte i paren,
   skadade och osäkra ord och signaturens egna ord räknas bort) vilken stavning stenen har – de högst fyra vanligaste
   stavningarna som egna nivåer, övriga "annan", ordet saknas = tomt. Plus skiljetecknet först och sist i texten.

    .venv/bin/python -m src.attribution_features KORPUSMAPP UT.csv
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MIN_CROSS = 10
N_WORDS = 30
N_SPELL = 4
SIGNATURE = {"risti", "hiogg", "runar", "retta", "markaði", "faði", "fapi"}
DIVIDERS = [("kryss", "x+×"), ("kolon", ":"), ("punkt", "·.•"), ("apostrof", "'")]


def divider(ch: str) -> str:
    for name, chars in DIVIDERS:
        if ch in chars:
            return name
    return "inget"


def ends(translit: str) -> tuple[str | None, str | None]:
    t = (translit or "").strip()
    if not t:
        return None, None
    return divider(t[0]), divider(t[-1])


def main(corpus_dir: str, out: str) -> None:
    csv.field_size_limit(10 ** 9)
    rows = list(csv.DictReader(open(os.path.join(corpus_dir, "corpus.csv"), encoding="utf-8")))
    signa = {r["signum"] for r in rows}
    runor = json.load(open(os.path.join(ROOT, "data", "raa", "runor_2020.json"), encoding="utf-8"))["inscriptions"]
    codes = {}
    for x in runor:
        if x["signum"] in signa and x.get("crosses"):
            c = {f"{f['aspect']}{f['form']}" for cr in x["crosses"] for f in cr.get("cross_forms", []) if f.get("aspect") and f.get("form")}
            if c:
                codes[x["signum"]] = c
    freq = Counter(c for v in codes.values() for c in v)
    keep = sorted(c for c, n in freq.items() if n >= MIN_CROSS)

    rundata = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))
    recs = {r["signum"]: r for v in rundata.values() if isinstance(v, list) for r in v if isinstance(r, dict) and "signum" in r}

    def pairs(r):
        out = []
        for p in (r.get("pairs") or "").split("|"):
            if "=" not in p:
                continue
            norm, tr = p.split("=", 1)
            if not norm or not tr or "/" in norm or "?" in norm or re.search(r"[^a-zæøþðåäöy]", norm) or re.search(r"[\[\]()?…-]", tr):
                continue
            if norm in SIGNATURE:
                continue
            out.append((norm, tr))
        return out
    stone_pairs = {r["signum"]: pairs(r) for r in rows}
    wc = Counter(w for ps in stone_pairs.values() for w in {n for n, _ in ps})
    words = [w for w, _ in wc.most_common(N_WORDS)]
    spell = defaultdict(Counter)
    for ps in stone_pairs.values():
        for n, t in ps:
            if n in words:
                spell[n][t] += 1
    levels = {w: [t for t, _ in spell[w].most_common(N_SPELL)] for w in words}

    cols = ["signum"] + [f"kors_{c}" for c in keep] + ["kors_beskriven"] + [f"sp_{w}" for w in words] + ["skilj_forst", "skilj_sist"]
    with open(out, "w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(cols)
        for r in rows:
            s = r["signum"]
            has_cross = r.get("cross") == "1"
            c = codes.get(s)
            kors = [("1" if k in c else "0") if c else ("" if has_cross else "0") for k in keep]
            sp = []
            seen = defaultdict(Counter)
            for n, t in stone_pairs[s]:
                if n in levels:
                    seen[n][t] += 1
            for w in words:
                if not seen[w]:
                    sp.append("")
                else:
                    t = seen[w].most_common(1)[0][0]
                    sp.append(t if t in levels[w] else "annan")
            first, last = ends((recs.get(s) or {}).get("transliteration", ""))
            wr.writerow([s] + kors + ["1" if c else "0"] + sp + [first or "", last or ""])
    print(out, len(rows), "stenar;", len(keep), "korsformer;", len(words), "ord:", ", ".join(words))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
