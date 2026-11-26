"""Kontrollurvalet: Viktor Kvants blinda handkodning av 40 stenar mot läsarnas konsensus (orn_koder.json).

    .venv/bin/python utdata/nya_ristare/ornamentik/kontroll_jamfor.py ~/Downloads/kontroll_viktor.json
Skriver utdata/nya_ristare/ornamentik/kontroll.json: per fält andel lika, kappa och felriktning (särskilt antal djur:
räknade läsarna fler djur än människan?), separat för riskurvalet (läsarna angav ≥ 2 djur) och slumpurvalet.
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.ornamentik.overens import kappa, norm  # noqa: E402

C = os.path.join(ROOT, "data", "cache", "hander", "ornamentik")
human = json.load(open(os.path.expanduser(sys.argv[1]), encoding="utf-8"))["svar"]
model = json.load(open(os.path.join(C, "orn_koder.json"), encoding="utf-8"))
urval = json.load(open(os.path.join(C, "kontroll", "urval.json"), encoding="utf-8"))
risk = set(urval["risk"])
F = ["djurhuvud", "antal_djur", "huvud_vy", "oga", "nackflik", "lappflik", "svans", "koppel"]
ORD = {"0": 0, "1": 1, "2": 2, "3+": 3}


def compare(stones):
    out = {}
    for f in F:
        pairs = [(norm(human[s].get(f)), model[s][f]) for s in stones if s in human and norm(human[s].get(f)) and f in model.get(s, {})]
        k = kappa(pairs)
        res = {"jämförbara": len(pairs), "lika": round(sum(a == b for a, b in pairs) / len(pairs), 2) if pairs else None,
               "kappa": round(k, 2) if k is not None else None,
               "människan_kodade": sum(1 for s in stones if s in human and norm(human[s].get(f))),
               "läsarna_kodade": sum(1 for s in stones if f in model.get(s, {}))}
        if f == "antal_djur":
            d = Counter("läsarna fler" if ORD[b] > ORD[a] else "läsarna färre" if ORD[b] < ORD[a] else "lika"
                        for a, b in pairs if a in ORD and b in ORD)
            res["riktning"] = dict(d)
        out[f] = res
    return out


coded = [s for s in urval["urval"] if s in human]
out = {"kodade_av_människan": len(coded), "alla": compare(coded), "riskurvalet": compare([s for s in coded if s in risk]),
       "slumpurvalet": compare([s for s in coded if s not in risk]),
       "olika_antal_djur": [{"sten": s, "människan": human[s].get("antal_djur"), "läsarna": model[s].get("antal_djur"),
                             "kommentar": human[s].get("kommentar")} for s in coded
                            if norm(human[s].get("antal_djur")) and model[s].get("antal_djur")
                            and norm(human[s].get("antal_djur")) != model[s]["antal_djur"]]}
json.dump(out, open(os.path.join(HERE, "kontroll.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
