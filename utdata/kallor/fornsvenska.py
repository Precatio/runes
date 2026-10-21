"""Del B i analysplan_kallor.md: hur många av runstenarnas ord (lemman, namn uteslutna) finns som uppslagsord i de
fornsvenska ordböckerna (Söderwall med supplement, Schlyter, Fornsvensk lexikalisk databas; Språkbankens Karp, hämtade
2026-10-21 till data/raa/kallor/karp/), och är engångsorden belagda mer sällan än de vanliga? Skriver
utdata/kallor/fornsvenska.json.
    PYTHONPATH=. .venv/bin/python utdata/kallor/fornsvenska.py"""
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from scipy.stats import norm  # noqa: E402

from api.rundata import store  # noqa: E402
from src import runlm as rl, textmodel as tm  # noqa: E402
from src.research_gaps import is_runestone  # noqa: E402

KARP = os.path.join(ROOT, "data", "raa", "kallor", "karp")

# ---- the dictionaries -------------------------------------------------------------------------------------------------
D, by_source = set(), {}
for res in ("soederwall", "soederwall-supp", "schlyter", "fsvm"):
    d = json.load(open(os.path.join(KARP, f"{res}.json"), encoding="utf-8"))
    forms = {(e["baseform"] or "").lower().strip() for e in d["entries"]} - {""}
    by_source[res] = len(forms)
    D |= forms
print("uppslagsord:", by_source, "| unika:", len(D))

# ---- the words on the stones --------------------------------------------------------------------------------------------
d = tm._records()
model = rl.Model(d["V"], edda_tokens=d["edda"], **tm.MODEL)  # the lemma map, learned from every Viking-age inscription
names = tm.name_keys(d["recs"])
stones = [r for r in store().inscriptions if is_runestone(r)]
freq, forms_of = Counter(), defaultdict(Counter)
for r in stones:
    for _, p in rl.sections(r.get("normalization") or ""):
        for w in rl.norm_words(p):
            if w.startswith('"'):  # a name, as Rundata marks them
                continue
            tok = rl.normtok(w)
            lem = model.lemma(tok)
            if lem in names or rl.key(tok) in names or not re.search(r"[a-zæøåäöþðʀ]", lem):
                continue
            freq[lem] += 1
            forms_of[lem][tok] += 1
print("lemman:", len(freq), "| förekomster:", sum(freq.values()))


# ---- the matching rules (fixed in the plan) ----------------------------------------------------------------------------------
def strip_length(w):
    return "".join(c for c in unicodedata.normalize("NFD", w) if unicodedata.category(c) != "Mn")


def variants(w: str) -> set[str]:
    base = strip_length(w.lower()).replace("ʀ", "r").replace("ð", "þ")
    out = {base}
    for a, bs in (("æi", ("e",)), ("ei", ("e",)), ("au", ("ö",)), ("øy", ("ö",)), ("ey", ("ö",)), ("ø", ("ö",)), ("æ", ("ä", "e")),
                  ("ǫ", ("o",)), ("ia", ("iä", "ia"))):
        out |= {v.replace(a, b) for v in out for b in bs}
    out |= {v.replace("þ", "th") for v in out} | {v.replace("þ", "dh") for v in out}
    ends = set()
    for v in out:
        if v.endswith("r") and len(v) > 2:  # masculine nominative -r: Old Swedish -er or nothing
            ends |= {v[:-1] + "er", v[:-1]}
        if v[-1:] in "iau" and len(v) > 2:  # the dictionary's own inflectional ending
            ends |= {v[:-1] + e for e in "aeiu"}
    return out | ends


def attested(lem: str) -> bool:
    cands = variants(lem) | {v for f in forms_of[lem] for v in variants(f)}
    return any(c in D for c in cands)


hit = {lem: attested(lem) for lem in freq}
classes = {"hapax": [l for l in freq if freq[l] == 1], "2–4": [l for l in freq if 2 <= freq[l] <= 4], "≥5": [l for l in freq if freq[l] >= 5]}
share = {k: (sum(hit[l] for l in v), len(v)) for k, v in classes.items()}
n_types, n_hit = len(freq), sum(hit.values())
tok_hit = sum(freq[l] for l in freq if hit[l])
# one-sided two-proportion z test: hapax attested less often than ≥5
h1, n1 = share["hapax"]
h5, n5 = share["≥5"]
p_pool = (h1 + h5) / (n1 + n5)
z = ((h5 / n5) - (h1 / n1)) / (p_pool * (1 - p_pool) * (1 / n1 + 1 / n5)) ** 0.5
p_val = float(1 - norm.cdf(z))
unattested = sorted((l for l in freq if not hit[l]), key=lambda l: -freq[l])
out = {
    "plan_sha256": open(os.path.join(ROOT, "utdata", "kallor", "analysis_plan_kallor.sha256")).read().split()[0],
    "dictionaries": by_source, "n_dictionary_forms": len(D),
    "n_stones": len(stones), "n_lemmas": n_types, "n_tokens": sum(freq.values()),
    "attested_types": n_hit, "attested_tokens": tok_hit,
    "by_class": {k: {"attested": a, "n": b, "share": a / b if b else None} for k, (a, b) in share.items()},
    "z": float(z), "p_one_sided": p_val, "answer": bool(p_val < 0.05 and h1 / n1 < h5 / n5),
    "unattested_frequent": [{"lemma": l, "n": freq[l], "forms": dict(forms_of[l].most_common(3))} for l in unattested[:40]],
    "attested_frequent": [{"lemma": l, "n": freq[l]} for l in sorted((l for l in freq if hit[l]), key=lambda l: -freq[l])[:40]],
    "unattested_hapax_sample": [{"lemma": l, "forms": dict(forms_of[l])} for l in unattested if freq[l] == 1][:40],
}
json.dump(out, open(os.path.join(ROOT, "utdata", "kallor", "fornsvenska.json"), "w"), ensure_ascii=False, indent=1)
print(f"belagda lemman: {n_hit} av {n_types} ({100 * n_hit / n_types:.0f} %), förekomster {tok_hit} av {sum(freq.values())} ({100 * tok_hit / sum(freq.values()):.0f} %)")
for k, (a, b) in share.items():
    print(f"  {k:6} {a:5} av {b:5} ({100 * a / b:.0f} %)")
print(f"hapax < ≥5: z {z:.2f}, p {p_val:.2e} | svar: {'ja' if out['answer'] else 'nej'}")
print("vanligaste obelagda:", [(x["lemma"], x["n"]) for x in out["unattested_frequent"][:25]])
