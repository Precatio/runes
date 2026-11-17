"""Not 8: indata till den blinda kontrolläsningen – de 10 lottade kontrollstenarna (rapportens "viktor"-lista) med de fem
fält som kontrollen gäller. Utdata utanför repot (SRI-text): granskning/<enhet>_kontroll3_indata.jsonl
    .venv/bin/python scripts/sri_kontroll3_indata.py got vg2 og2 msv2
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = "/Volumes/2TB/Antigrvity/Runes/downloads/sri_fakta/granskning"
F = ["lage_vid_utgavan", "ursprunglig_plats_text", "inmurad", "forsvunnen", "aterfunnen"]

for e in sys.argv[1:]:
    rap = json.load(open(os.path.join(ROOT, "utdata", "sri_fakta", f"{e}_kontroll.json"), encoding="utf-8"))
    S = {json.loads(l)["signum"]: json.loads(l) for l in open(os.path.join(G, f"{e}_stickprov.jsonl"), encoding="utf-8")}
    with open(os.path.join(G, f"{e}_kontroll3_indata.jsonl"), "w", encoding="utf-8") as fh:
        for s in rap["viktor"]:
            r = S[s]
            fh.write(json.dumps({"signum": s, "pages": r["pages"], "omfattar": r.get("omfattar"), "text": r["text"],
                                 "utplockning": {k: r["utplockning"].get(k) for k in F}}, ensure_ascii=False) + "\n")
    print(e, rap["viktor"])
