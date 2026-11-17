"""Runornas form (låst plan analysplaner/2026-11-17-runornas-form.md, sha 2fc45b76): D1 ljudbördan per runa i den yngre
futharken (svenska vikingatida runstenar) och D1b i den äldre (Rundatas urnordiska inskrifter), D2 prickarna per
stilgrupp, D3 andelen svenska runstenar efter 1066 (till artikeln om vikingatiden). Skriver resultat.json.
    PYTHONPATH=. .venv/bin/python utdata/runform/analys.py"""
import collections
import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import nordic as nd  # noqa: E402
from src import research_gaps as gaps  # noqa: E402

PLAN = "analysplaner/2026-11-17-runornas-form.md"
assert open(os.path.join(ROOT, PLAN.replace(".md", ".sha256"))).read().startswith("2fc45b76")

rd = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
SE = [r for r in rd if nd.is_runestone(r) and nd.land_of(r) == "sverige"]
PN = [r for r in rd if (r.get("flags") or {}).get("proto_norse")]

SEC = re.compile(r"§[A-Z]+")
TL_SPLIT = re.compile(r"[\s:·÷+×|¶'⁝⁞,.]+")
NO_SPLIT = re.compile(r"[\s,.;:!?]+")
BAD_TL = re.compile(r"[\[\]()\-?…<>{}/=*0-9]|[A-QS-Z]")   # uncertain/supplied runes, capitals except R
SOUND = {"á": "a", "æ": "æ", "ǽ": "æ", "é": "e", "í": "i", "ó": "o", "ô": "o", "ǫ": "o", "ú": "u", "ý": "y", "œ": "ø",
         "ǿ": "ø", "ø": "ø", "ʀ": "R", "w": "v"}


def sounds(word):
    out = []
    for c in word:
        if c == "R":
            out.append("R")
            continue
        c = c.lower()
        c = SOUND.get(c, c)
        if c.isalpha():
            out.append(c)
    return out


def sections(text):
    parts = SEC.split(text or "")
    return [p for p in parts if p.strip()]


def pairs(recs):
    """(translitteration word, normalization word) pairs from sections with the same number of words."""
    used = dropped = 0
    out = []
    for r in recs:
        tl, no = sections(r.get("transliteration")), sections(r.get("normalization"))
        if len(tl) != len(no):
            continue
        for a, b in zip(tl, no):
            tw = [w for w in TL_SPLIT.split(a.strip()) if w]
            nw = [w for w in NO_SPLIT.split(b.strip()) if w]
            if len(tw) != len(nw):
                dropped += len(nw)
                continue
            for t, n in zip(tw, nw):
                if BAD_TL.search(t) or n.startswith('"') or re.search(r"[\[\]()?…/]", n):
                    dropped += 1
                    continue
                used += 1
                out.append((t, n))
    return out, used, dropped


def rune_sounds(word_pairs):
    """{rune: Counter(sound)} from the one-to-one blocks of each word pair."""
    m = collections.defaultdict(collections.Counter)
    for t, n in word_pairs:
        a = list(t)
        b = sounds(n)
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op in ("equal", "replace") and i2 - i1 == j2 - j1:
                for x, y in zip(a[i1:i2], b[j1:j2]):
                    m[x][y] += 1
    return m


def table(m, min_n=50):
    out = {}
    for rune, c in sorted(m.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(c.values())
        if n < min_n:
            continue
        shares = [(s, round(k / n, 4)) for s, k in c.most_common()]
        out[rune] = {"n": n, "ljud_minst_5pct": sum(1 for _, p in shares if p >= 0.05), "andelar": shares[:8]}
    return out


res = {"plan": PLAN, "sha": "2fc45b76"}
wp, u, d = pairs(SE)
res["D1"] = {"ord_anvanda": u, "ord_bortfall": d, "runor": table(rune_sounds(wp))}
wp_pn, u2, dr2 = pairs(PN)
res["D1b"] = {"inskrifter": len(PN), "ord_anvanda": u2, "ord_bortfall": dr2, "runor": table(rune_sounds(wp_pn), min_n=20)}

# D2: the dots per style group
order = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
d2 = {g: collections.Counter() for g in order}
for r in SE:
    if not gaps.has_style(r) or r["style"] not in d2:
        continue
    wpr, _, _ = pairs([r])
    m = rune_sounds(wpr)
    c = d2[r["style"]]
    c["e_med_e"] += m["e"]["e"]
    c["e_med_i"] += m["i"]["e"]
    c["g_med_g"] += m["g"]["g"]
    c["g_med_k"] += m["k"]["g"]
    c["y_med_y"] += m["y"]["y"]
    c["y_med_u"] += m["u"]["y"]
    c["stenar"] += 1
res["D2"] = {}
for g in order:
    c = d2[g]
    sh = lambda a, b: round(c[a] / (c[a] + c[b]), 4) if c[a] + c[b] else None  # noqa: E731
    res["D2"][g] = {"stenar": c["stenar"], "e": [c["e_med_e"], c["e_med_e"] + c["e_med_i"], sh("e_med_e", "e_med_i")],
                    "g": [c["g_med_g"], c["g_med_g"] + c["g_med_k"], sh("g_med_g", "g_med_k")],
                    "y": [c["y_med_y"], c["y_med_y"] + c["y_med_u"], sh("y_med_y", "y_med_u")]}

# D3: after 1066
styled = [r for r in SE if gaps.has_style(r)]
cnt = collections.Counter(r["style"] for r in styled)
n = len(styled)
res["D3"] = {"stenar_med_sakert_stil": n, "per_stil": dict(cnt), "pr4_pr5": cnt["Pr4"] + cnt["Pr5"],
             "andel_pr4_pr5": round((cnt["Pr4"] + cnt["Pr5"]) / n, 4), "pr3": cnt["Pr3"], "andel_pr3": round(cnt["Pr3"] / n, 4)}

# summary of D1/D1b: the share of all aligned runes that stand for another sound than the rune's main sound
for key in ("D1", "D1b"):
    rr = res[key]["runor"]
    tot = sum(x["n"] for x in rr.values())
    main = sum(x["n"] * x["andelar"][0][1] for x in rr.values())
    res[key]["andel_annat_ljud"] = round(1 - main / tot, 4)
    res[key]["par"] = tot
res["D2_not"] = ("D2 är för tunt för att användas: Rundatas runsvenska normalisering skriver de flesta e-ljud som æ, så "
                 "klassen e har bara några tiotal fall per stilgrupp, och stilgrupperna blandar landskap. Redovisas, används inte.")
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("D1 ord", u, "bortfall", d, "| D1b ord", u2, "bortfall", dr2)
for k in ("D1", "D1b"):
    print("==", k)
    for rune, x in res[k]["runor"].items():
        print(f"  {rune}: n={x['n']:6d} ljud≥5%={x['ljud_minst_5pct']}  " + ", ".join(f"{s} {100*p:.0f}%" for s, p in x["andelar"][:5]))
print("D2", json.dumps(res["D2"], ensure_ascii=False))
print("D3", res["D3"])
