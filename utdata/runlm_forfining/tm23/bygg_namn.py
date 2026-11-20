"""namn.json for textmodel-23 (analysplaner/2026-11-20-petersons-namn-i-textmodellen.md, sha 321c3a6d): tm22's rules
(bygg_lexikon.py, N4 Peterson) on the re-read table; leak signa = column `signa` ∪ tm22's regex over `block`."""
import csv
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LEX = os.path.join(ROOT, "data/cache/literature/lexikon")
PLAIN = re.compile(r"[a-zþðæøåöäąǫœáéíóúýęR]+")
SIG = re.compile(r"\b(U|Sö|Ög|Vg|Sm|Öl|G|Vs|Nä|Hs|Gs|M|Ds|DR|N|Bo|J|Vr|Lp|Sl)\s?([0-9]+[A-Za-z]?|[A-Z][A-Za-z]*[0-9]+[;:][0-9]+[A-Z]?)\b")


def main():
    old = os.path.join(LEX, "namn.json")
    if os.path.exists(old) and not os.path.exists(os.path.join(LEX, "namn_tm22.json")):
        shutil.copy(old, os.path.join(LEX, "namn_tm22.json"))
    pet = list(csv.DictReader(open(os.path.join(ROOT, "data/cache/literature/peterson2007_namn.csv"), encoding="utf-8")))
    names = []
    for r in pet:
        signa = {a + " " + b for a, b in SIG.findall(r["block"])}
        signa |= {s.strip() for s in re.split(r"[|;]", r.get("signa") or "") if s.strip()}
        for k in r["keys"].split("|"):
            k = k.strip()
            if PLAIN.fullmatch(k) and len(k) >= 3:
                names.append({"name": k, "gender": r["gender"], "signa": sorted(signa)})
    json.dump(names, open(old, "w"), ensure_ascii=False)
    tm22 = json.load(open(os.path.join(LEX, "namn_tm22.json")))
    print(f"{len(pet)} uppslag → {len(names)} namnformer ({len({n['name'] for n in names})} olika); "
          f"tm22: {len(tm22)} ({len({n['name'] for n in tm22})} olika); nya former {len({n['name'] for n in names} - {n['name'] for n in tm22})}")


if __name__ == "__main__":
    main()
