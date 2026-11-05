"""Kontroll för rapportversion 3 av metodrapporten om spårläsaren (2026-11-05, granskning inför arkiveringen i Zenodo).
Kör ingenting om: räknar bara i de sparade raderna (led_f_Sö_*.json, led_f.json, led_g.json, led_f_summering.json) och
läser koden vid provets commits (a71c134, f3b8f01) och i arbetskatalogen, så att varje nytt tal i rapporten kan
asserteras mot en fil. Skriver kontroll_v3.json.
    .venv/bin/python utdata/sparlasare/kontroll_v3.py"""
import glob
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
C = ("utan", "skanner", "omflyttad")
COMMIT_F, COMMIT_G, COMMIT_G7 = "a71c134", "f3b8f01", "add12ef"


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, check=True).stdout


def grab(pattern: str, text: str):
    m = re.search(pattern, text, re.M)
    return m.group(1) if m else None


def is_ancestor(a: str, b: str) -> bool:
    return subprocess.run(["git", "-C", ROOT, "merge-base", "--is-ancestor", a, b]).returncode == 0


# ---- 1. the main test (led F): the saved rows of the final run, one file per stone ----------------------------------
rows = []
for f in sorted(glob.glob(os.path.join(HERE, "led_f_Sö_*.json"))):
    rows += json.load(open(f, encoding="utf-8"))["rows"]
both = [r for r in rows if all(r.get(c) for c in C)]


def flips(a: str, b: str, rs=None) -> dict:
    rs = both if rs is None else rs
    return {"wrong_to_right": sum(1 for r in rs if not r[a]["word_ok"] and r[b]["word_ok"]),
            "right_to_wrong": sum(1 for r in rs if r[a]["word_ok"] and not r[b]["word_ok"])}


s134 = [r for r in both if r["sig"] == "Sö 134"]
main = {"positions": len(rows), "n": len(both), "stones": len({r["sig"] for r in both}),
        "right_words": {c: sum(r[c]["word_ok"] for r in both) for c in C},
        "utan_to_skanner": flips("utan", "skanner"), "utan_to_omflyttad": flips("utan", "omflyttad"),
        "omflyttad_to_skanner": flips("omflyttad", "skanner"),
        # what was saved per word and condition: the probability of the right word, not of the model's first choice
        "row_keys": sorted({k for r in both for c in C for k in r[c]}),
        "so134": {"n": len(s134), "right_words": {c: sum(r[c]["word_ok"] for r in s134) for c in C},
                  "utan_to_skanner": flips("utan", "skanner", s134),
                  "words_changing": sum(len({r[c]["word_ok"] for c in C}) > 1 for r in s134)}}

# ---- 2. the pairing's own check (led_f_summering.py: coverage at least two sd above a shuffled text's) -------------
S = json.load(open(os.path.join(HERE, "led_f_summering.json"), encoding="utf-8"))
z = {s: (q["coverage"] - q["null"]) / max(q["null_sd"], 1e-9) for s, q in S["stones"].items()}
pairing = {"stones": len(z), "reliable": sorted(s for s, v in z.items() if v >= 2.0), "z": z}

# ---- 3. the answer reached the pairing: led_f.py at the test's commit -------------------------------------------------
src_f = git("show", f"{COMMIT_F}:utdata/sparlasare/led_f.py")
leak = {
    # the scan's runes are paired with the stone's full text once per stone, before any word is masked
    "pairs_with_full_text": 'full = "".join(groups)\n        pos_sets, quality = scan_sets(signum, full)' in src_f,
    "masked_after_pairing": src_f.index("pos_sets, quality = scan_sets(signum, full)") < src_f.index('masked[gi] = '),
    # the alignment costs nothing where the text's rune is in the scan's set
    "free_when_in_set": "(0.0 if seq[j - 1][1] in sets[i - 1] else 1.0)" in src_f,
    "trace_eps": float(grab(r"^TRACE_EPS = ([\d.]+)", src_f)),
}

# ---- 4. the earlier run the same day (led_f.json: Sö 113 and Sö 134 in one call, older format: a bare list) ---------
old = json.load(open(os.path.join(HERE, "led_f.json"), encoding="utf-8"))
new = []
for s in ("Sö_113", "Sö_134"):
    new += json.load(open(os.path.join(HERE, f"led_f_{s}.json"), encoding="utf-8"))["rows"]
assert isinstance(old, list) and [(o["sig"], o["truth"]) for o in old] == [(n["sig"], n["truth"]) for n in new]
earlier = {"words": len(old), "stones": sorted({o["sig"] for o in old})}
for c in C:
    earlier[c] = {"top_differs": sum(o[c]["top"] != n[c]["top"] for o, n in zip(old, new)),
                  "word_ok_differs": sum(o[c]["word_ok"] != n[c]["word_ok"] for o, n in zip(old, new)),
                  "any_differs": sum(any((abs(o[c][k] - n[c][k]) > 1e-9) if k == "p_truth" else o[c][k] != n[c][k]
                                         for k in ("top", "right", "word_ok", "p_truth", "traced"))
                                     for o, n in zip(old, new)),
                  "right_in_final_not_earlier": sum(n[c]["word_ok"] and not o[c]["word_ok"] for o, n in zip(old, new)),
                  "stones_differing": sorted({o["sig"] for o, n in zip(old, new) if o[c]["top"] != n[c]["top"]})}

# ---- 5. real gaps (led G): agreement with the editors' reading in Rundata -------------------------------------------
G = json.load(open(os.path.join(HERE, "led_g.json"), encoding="utf-8"))
# By hand: staf (a staff) is not stæin (a stone); the code's rule (lemma or runlm.same_word) counts them as the same.
NOT_SAME = {("Sö 162", "staf", "st[æin]")}
gap = {"words": sum(len(s["utan"]) for s in G)}
for c in ("utan", "skanner"):
    xs = [x for s in G for x in s[c]]
    gap[c] = {"code_agrees": sum(x["agrees"] for x in xs),
              "agrees": sum(x["agrees"] and (x["sig"], x["word"], x["rundata"]) not in NOT_SAME for x in xs),
              "words": [[x["sig"], x["rundata"], x["word"], x["p"], x["agrees"]] for x in xs]}
src_runlm_g = git("show", f"{COMMIT_G}:src/runlm.py")
gap["same_word_rule_at_g"] = "def same_word" in src_runlm_g

# ---- 6. versions: at the test's commits and in the working tree on the day of the correction ------------------------
cfg_f = git("show", f"{COMMIT_F}:api/config.py")
tm_f, tm_g = git("show", f"{COMMIT_F}:src/textmodel.py"), git("show", f"{COMMIT_G}:src/textmodel.py")
cfg_now = open(os.path.join(ROOT, "api", "config.py"), encoding="utf-8").read()
tm_now = open(os.path.join(ROOT, "src", "textmodel.py"), encoding="utf-8").read()
tr_now = open(os.path.join(ROOT, "src", "trace_reader.py"), encoding="utf-8").read()
versions = {
    "test": {"commit_f": COMMIT_F, "commit_g": COMMIT_G,
             "date_f": git("log", "-1", "--format=%ad", "--date=short", COMMIT_F).strip(),
             "date_g": git("log", "-1", "--format=%ad", "--date=short", COMMIT_G).strip(),
             "method": grab(r'^METHOD_VERSION = "([^"]+)"', cfg_f),
             "textmodel_f": grab(r'^VERSION = "([^"]+)"', tm_f), "textmodel_g": grab(r'^VERSION = "([^"]+)"', tm_g),
             "trace_eps_g": float(grab(r"trace_eps=([\d.]+)", tm_g)),
             "in_v3_0_0": is_ancestor(COMMIT_F, "v3.0.0") and is_ancestor(COMMIT_G, "v3.0.0")},
    "now": {"head": git("rev-parse", "--short", "HEAD").strip(), "date": "2026-11-05",
            "method": grab(r'^METHOD_VERSION = "([^"]+)"', cfg_now),
            "textmodel": grab(r'^VERSION = "([^"]+)"', tm_now),
            "trace_eps": float(grab(r"trace_eps=([\d.]+)", tm_now)),
            "trace_reader_refs": grab(r'^REFS = os\.path\.join\(ROOT, "utdata", "Rak", "([^"]+)"\)', tr_now),
            "traces_count_after_confirmation": "spåren räknas först när användaren har bekräftat dem" in tr_now},
    "g7_switch": {"commit": COMMIT_G7, "date": git("log", "-1", "--format=%ad", "--date=short", COMMIT_G7).strip(),
                  "trace_reader_to_g7": '+REFS = os.path.join(ROOT, "utdata", "Rak", "referenser_g7")'
                  in git("show", COMMIT_G7, "--", "src/trace_reader.py")},
}

# ---- 7. the text source: Rundata 3.1 (2018), the same file at the test's commit and now -----------------------------
rundata = {"blob_at_f": git("rev-parse", f"{COMMIT_F}:data/rundata.json").strip(),
           "blob_now": git("hash-object", os.path.join(ROOT, "data", "rundata.json")).strip(),
           "version_note": "Appen bygger på Rundata 3.1 (2018)" in open(os.path.join(ROOT, "src", "runor.py"), encoding="utf-8").read(),
           "last_change": git("log", "-1", "--format=%ad", "--date=short", "--", "data/rundata.json").strip()}

out = {"made": "2026-11-05", "main": main, "pairing": pairing, "leak": leak, "earlier_run": earlier, "real_gaps": gap,
       "versions": versions, "rundata": rundata}
json.dump(out, open(os.path.join(HERE, "kontroll_v3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ("real_gaps",)}, ensure_ascii=False, indent=1)[:4000])
print("verkliga luckor:", {c: (gap[c]["code_agrees"], gap[c]["agrees"]) for c in ("utan", "skanner")}, "av", gap["words"])
