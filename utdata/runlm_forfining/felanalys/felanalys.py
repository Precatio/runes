"""Felanalys av sannolikhetsmodellen (appens inställning, textmodel-19): var ligger felen i maskeringsprovet?
Beskrivande, inget prov. Läser app_f0–f4.json (samma luckor som tm22–tm24 jämfördes mot), bara runstenar.
    PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/felanalys/felanalys.py
Skriver felanalys.json och skriver ut en sammanfattning."""
import ast
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, ".")
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

F = "utdata/runlm_forfining/"
OUT = os.path.join(F, "felanalys")
R = tm._records()
by, G = R["by"], R["G"]


def parse(v):
    return ast.literal_eval(v) if isinstance(v, str) else v


rows = []
for k in range(5):
    for x in json.load(open(f"{F}app_f{k}.json"))["rows"]:
        if rl.object_kind(by[x["sig"]]) != "runsten":
            continue
        x["veck"] = k
        x["words"] = parse(x.get("words")) or []
        rows.append(x)

# hur vanligt det rätta ordet är i hela korpusen (normaliserade ord)
freq = Counter()
for r in rl.load_rundata():
    for w in rl.norm_words(r.get("normalization_ows") or r.get("normalization") or ""):
        freq[rl.key(w)] += 1


def lenbin(n):
    return "1–2" if n <= 2 else "3–4" if n <= 4 else "5+"


def freqbin(w):
    f = freq.get(rl.key(w or ""), 0)
    return "formelord (≥200)" if f >= 200 else "vanligt (20–199)" if f >= 20 else "ovanligt (2–19)" if f >= 2 else "unikt (0–1)"


def sure(x):
    return bool(x.get("word") and x["word"] != "<unk>" and
                tm.calibrate_gap(x["p_word"], x["word"], x["n"], G, x["kind"] == "helt ord") >= 0.95)


def kind_of_error(x):
    if x["word_ok"]:
        return "rätt"
    if not x.get("word") or x["word"] == "<unk>":
        return "inget ord (okänt)"
    if any(ok for _, _, ok in x["words"]):
        return "rätt ord bland förslagen, fel valt"
    if x.get("top") == x.get("truth"):
        return "rätt runor, fel ord (normalisering?)"
    return "rätt ord inte bland förslagen"


def table(key):
    t = defaultdict(Counter)
    for x in rows:
        t[key(x)]["n"] += 1
        t[key(x)]["fel"] += not x["word_ok"]
    return {k: {"luckor": v["n"], "fel": v["fel"], "andel_fel": round(v["fel"] / v["n"], 3)} for k, v in sorted(t.items())}


err = [x for x in rows if not x["word_ok"]]
out = {
    "luckor": len(rows), "fel": len(err), "andel_rätt": round(1 - len(err) / len(rows), 3),
    "feltyp": dict(Counter(kind_of_error(x) for x in err)),
    "per_slag": table(lambda x: x["kind"]),
    "per_längd": table(lambda x: lenbin(x["n"])),
    "per_slag_och_längd": table(lambda x: f'{x["kind"]} {lenbin(x["n"])}'),
    "namn_eller_ord": table(lambda x: "namn" if x.get("is_name") else "ord"),
    "per_frekvens": table(lambda x: freqbin(x.get("gold_word"))),
    "säkra_svar": {"antal": sum(sure(x) for x in rows), "fel": sum(sure(x) and not x["word_ok"] for x in rows)},
    "andel_av_felen": {
        "namn": round(sum(bool(x.get("is_name")) for x in err) / len(err), 3),
        "korta 1–2": round(sum(x["n"] <= 2 for x in err) / len(err), 3),
        "helt ord": round(sum(x["kind"] == "helt ord" for x in err) / len(err), 3),
    },
    "exempel_fel_valt": [{"sig": x["sig"], "rätt": x["gold_word"], "valt": x["word"], "p": round(x["p_word"], 3),
                          "förslag": [w for w, _, _ in x["words"][:4]]}
                         for x in err if kind_of_error(x) == "rätt ord bland förslagen, fel valt"][:15],
    "exempel_ej_bland_förslagen": [{"sig": x["sig"], "rätt": x["gold_word"], "valt": x["word"], "namn": x.get("is_name"),
                                    "n": x["n"]} for x in err if kind_of_error(x) == "rätt ord inte bland förslagen"][:15],
}
# bland namnfelen: nåddes namnet?
ne = [x for x in err if x.get("is_name")]
out["namnfel"] = dict(Counter(kind_of_error(x) for x in ne))
json.dump(out, open(os.path.join(OUT, "felanalys.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if not k.startswith("exempel")}, ensure_ascii=False, indent=1))
