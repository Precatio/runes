"""Rökstenen (Ög 136) läst av sannolikhetsmodellen (textmodel-19, modellen byggd utan Rökstenen: rok_lasning_loo.json)
mot Rundatas normalisering, del för del: hur många ord modellen avgränsar rätt och läser som samma ord, och hur
kalibreringen håller på en sten som är olik allt den lärt sig på. Skriver jamforelse.json.
    PYTHONPATH=. .venv/bin/python utdata/Rok/jamfor.py"""
import json
import re
import sys

sys.path.insert(0, ".")
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

IN = sys.argv[1] if len(sys.argv) > 1 else "utdata/Rok/rok_lasning_loo.json"  # another reading (tm22: with the lexicon)
OUT = sys.argv[2] if len(sys.argv) > 2 else "utdata/Rok/jamforelse.json"
R = json.load(open(IN, encoding="utf-8"))
M = tm.bundle_loo("Ög 136")["model"]  # the same model that read the stone, for its lemma (æft = aft, varin = varinn)
same_word = lambda a, b: bool(a) and bool(b) and M.lemma(a) == M.lemma(b)  # noqa: E731
rec = next(r for r in json.load(open("data/rundata.json", encoding="utf-8"))["inscriptions"] if r["signum"] == "Ög 136")
LABEL = {"A": "A: minnesformeln och de två bytena", "B": "B: Tjodriks häst och sköld (framsidans slut)",
         "C": "C: de tjugo kungarna, de fem bröderna, chiffren", "D": "D: chiffer (Tor)", "E": "E: Sibbe viaväre"}

# the model's words with their place in the carved text
rows, at = [], 0
for x in R["reading"]:
    rows.append((at, at + len(x["runes"]), x))
    at += len(x["runes"])
carved_len = at

# Rundata's words by section, placed in the same carved text
secs_t = dict(rl.sections(rec["transliteration"]))
secs_n = dict(rl.sections(rec["normalization"]))
cursor, out, per_sec = 0, [], {}
seen = {}
for lab0, t in rl.sections(rec["transliteration"]):
    seen[lab0] = seen.get(lab0, 0) + 1
    lab = lab0 if seen[lab0] == 1 else f"{lab0}{seen[lab0]}"  # the stone has two §C sections
    norm_sec = [p_ for l_, p_ in rl.sections(rec["normalization"]) if l_ == lab0][seen[lab0] - 1]
    groups, _ = tm.text_groups(f"§{lab} {t}")
    sec_text = "".join(groups)
    sec_start, sec_end = cursor, cursor + len(sec_text)
    a, b = rl.translit_words(t), rl.norm_words(norm_sec)
    prs = list(zip(a, b)) if len(a) == len(b) else rl.align(a, b)
    stats0 = per_sec.setdefault(lab, {"rundata_words": 0, "comparable": 0, "n": 0, "span_ok": 0, "word_ok": 0, "sure": 0, "sure_ok": 0, "examples": []})
    stats0["rundata_words"] += len(b)
    stats0["comparable"] += len(prs)
    pos = sec_start
    stats = per_sec[lab]
    for rw, nw in prs:
        k = rl.runekey(rw).replace("-", "?")
        k = re.sub(r"[^a-zþðæøåöäąR?]", "", k)
        if not k:
            continue
        i = "".join(groups).find(k, pos - sec_start)
        if i < 0:
            continue
        s, e = sec_start + i, sec_start + i + len(k)
        pos = e
        hit = next((x for s_, e_, x in rows if s_ == s and e_ == e), None)
        gold = rl.normtok(nw)
        got = rl.normtok(hit["word"]) if hit else None
        same = bool(hit) and same_word(got, gold)
        stats["n"] += 1
        stats["span_ok"] += bool(hit)
        stats["word_ok"] += same
        if hit and hit["p"] >= 0.95:
            stats["sure"] += 1
            stats["sure_ok"] += same
        stats["examples"].append((rw, gold, got, round(hit["p"], 2) if hit else None))
    cursor = sec_end
from collections import Counter  # noqa: E402
ep = Counter(rl.epoch(r) for r in rl.load_rundata() if rl.viking(r) and r.get("transliteration") and r["signum"] != "Ög 136")
tot = {k: sum(v[k] for v in per_sec.values()) for k in ("rundata_words", "comparable", "n", "span_ok", "word_ok", "sure", "sure_ok")}
print("stenar per epok i träningen:", dict(ep))
json.dump({"per_section": per_sec, "total": tot, "dating": R["dating"], "carved_runes": carved_len, "epochs_in_training": dict(ep)},
          open(OUT, "w"), ensure_ascii=False, indent=1)
for lab, v in per_sec.items():
    print(f"§{lab} {LABEL.get(lab[:1], '')}: Rundata {v['rundata_words']} ord, jämförbara {v['comparable']}, placerade {v['n']} | avgränsade rätt {v['span_ok']} | samma ord {v['word_ok']} | "
          f"säkra (≥95 %) {v['sure']}, av dem rätt {v['sure_ok']}")
    print("    ", [(a, g, m, p) for a, g, m, p in v["examples"][:14]])
print("TOTALT", tot)
