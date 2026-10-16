"""Sammanställer maskeringsprovet för ifyllning av förlorade runor (scripts/runlm_restore_test.py, en fil per del):
rätt ord och rätt runor efter slag av lucka och antal runor, och hur väl modellens säkerhet om ordet stämmer.
Skriver utdata/Malt/runlm_ifyllning.json.
    .venv/bin/python -m scripts.runlm_restore_report utdata/Malt/runlm_eval/final_f0.json … final_f4.json"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = sum((json.load(open(p))["rows"] for p in sys.argv[1:]), [])
out = {"n": len(rows), "files": sys.argv[1:]}
for kind in ("inne i ord", "helt ord"):
    xs = [x for x in rows if x["kind"] == kind]
    names = [x for x in xs if x.get("is_name")]
    by_n = {}
    for n in sorted({x["n"] for x in xs}):
        ys = [x for x in xs if x["n"] == n]
        by_n[n] = {"n": len(ys), "word": sum(x["word_ok"] for x in ys) / len(ys), "runes": sum(x["rank"] == 1 for x in ys) / len(ys)}
    rel = []
    for lo, hi in ((0, 0.5), (0.5, 0.8), (0.8, 0.95), (0.95, 1.01)):
        ys = [x for x in xs if lo <= x.get("p_word", 0) < hi]
        rel.append({"lo": lo, "hi": min(hi, 1), "n": len(ys), "p": sum(x["p_word"] for x in ys) / max(1, len(ys)),
                    "acc": sum(x["word_ok"] for x in ys) / max(1, len(ys))})
    out[kind] = {"n": len(xs), "word": sum(x["word_ok"] for x in xs) / len(xs), "runes": sum(x["rank"] == 1 for x in xs) / len(xs),
                 "top3": sum(1 for x in xs if x["rank"] and x["rank"] <= 3) / len(xs),
                 "missing": sum(1 for x in xs if x["rank"] is None) / len(xs),
                 "names": {"n": len(names), "word": sum(x["word_ok"] for x in names) / max(1, len(names))},
                 "others": {"n": len(xs) - len(names), "word": sum(x["word_ok"] for x in xs if not x.get("is_name")) / max(1, len(xs) - len(names))},
                 "by_n": by_n, "reliability_word": rel}
    o = out[kind]
    print(f"[{kind}] {o['n']} luckor: rätt ord {o['word']:.1%} (namn {o['names']['word']:.0%} av {o['names']['n']}, övriga {o['others']['word']:.0%}); "
          f"rätt runor {o['runes']:.1%}, bland tre första {o['top3']:.1%}; rätt fyllnad saknas bland kandidaterna {o['missing']:.1%}")
    print("   efter antal runor (ord/runor):", {n: f"{v['word']:.0%}/{v['runes']:.0%} (n={v['n']})" for n, v in by_n.items()})
    print("   ordets säkerhet → rätt ord:", [(f"{c['p']:.2f}", f"{c['acc']:.2f}", c["n"]) for c in rel])
json.dump(out, open(os.path.join(ROOT, "utdata", "Malt", "runlm_ifyllning.json"), "w"), ensure_ascii=False, indent=1)
