"""Sammanställning av mätningarna: per fil och läge, text_runor, runor med mått, runsnitt."""
import glob, json, os, sys
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultat")
rows = {}
for p in glob.glob(os.path.join(R, "*.json")):
    d = json.load(open(p, encoding="utf-8"))
    tag = os.path.basename(p).split("__")[1][:-5]
    rows.setdefault(d["stem"], {"signum": d["signum"], "typ": d["rune_types"] or "", "text": d["text_runor"]})[tag] = d
tags = sys.argv[1:] or ["vanligt", "stavlost"]
print(f"{'fil':32} {'signum':7} {'stavl':5} {'text':>4} | " + " | ".join(f"{t[:10]:>10} runor/snitt" for t in tags))
for stem, r in sorted(rows.items(), key=lambda kv: ("stavlösa" not in kv[1]["typ"], kv[0])):
    cells = []
    for t in tags:
        d = r.get(t)
        cells.append(f"{d['runor_matta']:>10}/{d['runsnitt']:<5}" if d else f"{'–':>16}")
    print(f"{stem[:32]:32} {r['signum']:7} {'J' if 'stavlösa' in r['typ'] else ' ':5} {r['text']:>4} | " + " | ".join(cells))
