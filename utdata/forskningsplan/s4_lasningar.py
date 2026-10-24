"""Studie 4, resultatdelen: för varje sten i Medelpad, Hälsingland och Åsmunds serie med förlorade runor – modellens
förslag per lucka (kalibrerad sannolikhet) och vad skannern ser vid luckan, via analysmotorn (samma som appen visar).
Spåren används enligt blindprovet (s4_blindprov_sammanfattning.json). Bara förslag med kalibrerad sannolikhet ≥ 80 %
lyfts fram; allt är förslag att pröva på stenen."""
import json, os, sys, urllib.parse
import requests
HERE = os.path.dirname(os.path.abspath(__file__))
API = "http://localhost:8000/api/textmodel"
SIGNA = ["Gs 11", "Gs 13", "U 1144", "Hs 1", "Hs 2", "Hs 3", "Hs 4", "Hs 6", "Hs 9", "Hs 10", "Hs 11", "Hs 12", "Hs 14",
         "Hs 15", "Hs 16", "Hs 21", "M 1", "M 2", "M 3", "M 4", "M 5", "M 6", "M 7", "M 8", "M 10", "M 11", "M 13", "M 14",
         "M 15", "M 16"]
out = {}
for sg in SIGNA:
    q = urllib.parse.quote(sg)
    tm = requests.get(f"{API}/{q}", timeout=900).json()
    sc = requests.get(f"{API}/scantraces/{q}", timeout=900).json()
    rec = {"available": tm.get("available"), "reason": tm.get("reason"), "scan": sc.get("available"),
           "scan_reason": sc.get("reason"), "gaps": []}
    for i, g in enumerate(tm.get("gaps") or []):
        words = g.get("words") or []
        rec["gaps"].append({"gap": i, "words": words[:3], "scan": (sc.get("gaps") or {}).get(str(i)) or (sc.get("gaps") or {}).get(i)})
    out[sg] = rec
    best = [(w[0]["word"], w[0]["p"]) for w in (x["words"] for x in rec["gaps"]) if w]
    print(f"{sg:7} modell {'ja' if rec['available'] else 'nej (' + str(rec['reason'])[:50] + ')'}; luckor {len(rec['gaps'])}; "
          f"skanner {'ja' if rec['scan'] else 'nej'}; ≥80 %: {[f'{w} {p:.0%}' for w, p in best if p >= 0.8]}", flush=True)
json.dump(out, open(os.path.join(HERE, "s4_lasningar.json"), "w"), ensure_ascii=False, indent=1)
