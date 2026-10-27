"""Det andra perspektivet: vikingatida inskrifter i Norden som nämner resor västerut, och om någon person på de brittiska
öarnas inskrifter går igen hemma (namnpar ur kodning.csv på samma nordiska inskrift, mot slumpen givet namnens
frekvens). Skriver utdata/brittiska/hemma.json.

  .venv/bin/python utdata/brittiska/hemma.py
"""
import csv
import itertools
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from scipy.stats import fisher_exact  # noqa: E402

from analys import region  # noqa: E402
from api.rundata import store  # noqa: E402

WEST = re.compile(r"\b(england|london|bath|in the west|to the west|western route|westwards)\b", re.I)
EAST = re.compile(r"\b(in the east|to the east|eastwards|greece|greeks|serkland|garðar|ingvarr|holmgarðr|estonia|virland|"
                  r"semgall|langobard|italy|jerusalem|east)\b", re.I)
DIED = re.compile(r"\b(died|killed|fell|forfeited|drowned|lies|lie|met (his|their) end|perished|was slain|lost his life|ended)\b", re.I)


def has(names: set, n: str) -> bool:
    """A crude inflection match: the nominative's stem plus up to three letters (Ófeigr ~ Ófeig, Ófeigs; Heðinn ~ Heðin)."""
    s = re.sub(r"(nn|ir|r|i|a|l)$", lambda m: "n" if m.group(1) == "nn" else "", n) if len(n) > 4 else n
    rx = re.compile("^" + s.replace("ô", "[ôǫa]") + r"\w{0,3}$")
    return any(rx.match(t) for t in names)


def main():
    recs = [r for r in store().inscriptions if r.get("period") == "V" and region(r["signum"]) not in (None, "Brittiska öarna")]
    out = {"nordic_viking": len(recs)}
    # 1. Inscriptions at home that mention the west
    west = [r for r in recs if WEST.search(r.get("translation_en") or "")
            or re.search(r"\b(vestr|vestan|Englandi|Englands|Lundúnum|Baðum)\b", r.get("normalization_ows") or "")]
    out["west"] = [{"signum": r["signum"], "translation": r.get("translation_en")} for r in west]
    # 2. Did the travellers to the west die more often than those to the east? Runestones naming only one direction
    fate = {}
    for r in recs:
        if "runsten" not in (r.get("object") or "").lower():
            continue
        t = r.get("translation_en") or ""
        w, e = bool(WEST.search(t)), bool(EAST.search(t))
        if w != e:
            fate.setdefault("väst" if w else "öst", Counter())["död" if DIED.search(t) else "ej död"] += 1
    a, b = fate["väst"], fate["öst"]
    out["fate"] = {k: dict(v) for k, v in fate.items()}
    out["fate_p"] = fisher_exact([[a["död"], a["ej död"]], [b["död"], b["ej död"]]])[1]
    # 3. Name pairs from one British inscription found together on one Nordic inscription
    toks = [set(re.findall(r'"([^\s,.;:()\[\]!?]+)', r.get("normalization_ows") or "")) for r in recs]
    freq, pairs, expected = {}, [], 0.0
    for row in csv.DictReader(open(os.path.join(HERE, "kodning.csv"), encoding="utf-8")):
        ns = sorted({p.split(":")[0] for p in filter(None, row["namn"].split(";"))})
        for x, y in itertools.combinations(ns, 2):
            for n in (x, y):
                freq.setdefault(n, sum(has(t, n) for t in toks))
            exp = freq[x] * freq[y] / len(recs)
            expected += exp
            out.setdefault("freq", {}).update({x: freq[x], y: freq[y]})
            hits = [recs[i]["signum"] for i, t in enumerate(toks) if has(t, x) and has(t, y)]
            pairs.append({"isles": row["signum"], "names": [x, y], "expected": exp, "hits": hits})
    out["pairs_tested"], out["pairs_expected"] = len(pairs), expected
    out["pairs_found"] = [p for p in pairs if p["hits"]]
    json.dump(out, open(os.path.join(HERE, "hemma.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(west), "inskrifter om väst;", out["fate"], "p", round(out["fate_p"], 2))
    print(len(pairs), "namnpar prövade, väntat", round(expected, 2), "funna", [(p["isles"], p["names"], p["hits"]) for p in out["pairs_found"]])


if __name__ == "__main__":
    main()
