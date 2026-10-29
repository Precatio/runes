"""Källströms katalog över ristarformler (Mästare och minnesmärken 2007, Bilaga 1) mot Rundatas ristarfält: hur många
svenska runstenar med en ristarsignatur saknar ristare i databasen? Katalogen tas ut ur PDF-texten
(/Volumes/2TB/tmp/kallstrom2007/k.txt; boken finns inte i kodförrådet). Namnet bedöms ur Källströms normalisering: ett
namn som går att läsa (också med frågetecken) räknas som namngivet; en bortslagen början ("… högg stenen") inte.
    .venv/bin/python utdata/signaturer/jamfor.py      Skriver signaturer.json."""
import json
import os
import re
import sys
from collections import Counter

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src.research_gaps import SWEDISH  # noqa: E402
from src.signum import fold_signum  # noqa: E402

TEXT = "/Volumes/2TB/tmp/kallstrom2007/k.txt"
s = store()
RD = {fold_signum(r["signum"]): r for r in s.inscriptions}
L = open(TEXT, encoding="utf-8").read().split("\n")
pref = sorted({r["signum"].split(" ")[0] for r in s.inscriptions}, key=len, reverse=True)
HEAD = re.compile(r"^(" + "|".join(map(re.escape, pref)) + r") (\S+)\s")
OBJ = re.compile(r"^(\w+),?\s.*?\b(B(?:/[ABC]|I|/BI)?|A|C|B/C):(\d)")
CAT_START = next(i for i, l in enumerate(L) if i > 13000 and HEAD.match(l))  # the catalogue (Bilaga 1) is the last part

rows = []
for i in range(CAT_START, len(L) - 1):
    m, o = HEAD.match(L[i]), OBJ.match(L[i + 1].strip())
    if not (m and o):
        continue
    sig = f"{m.group(1)} {m.group(2)}".rstrip(",")
    if sig.split(" ")[0] not in SWEDISH:
        continue
    block = [x for x in L[i:i + 8] if x.strip()]
    norm = block[3].strip() if len(block) > 3 else ""
    r = RD.get(fold_signum(sig))
    rows.append({"signum": sig, "object": o.group(1), "type": f"{o.group(2)}:{o.group(3)}",
                 "main_type": "B" if o.group(2).startswith("B") else o.group(2), "level": int(o.group(3)),
                 "normalization": norm, "in_rundata": bool(r),
                 "rundata_carvers": [c["name"] for c in r["carvers"]] if r else None,
                 "rundata_signed": bool(r) and any(c["kind"] == "S" for c in r["carvers"])})

# The name in the signature: legible (also "Hávarðr(?)") unless the formula begins with a gap ("...", "…", "[")
for x in rows:
    x["named"] = not re.match(r"^(\.\.\.|…|\[|\|?\s*\.\.\.)", x["normalization"]) and bool(re.match(r"^\W*[A-ZÁÉÍÓÚÝÞÆÖØ]", x["normalization"]))

# Read by hand where the automatic line pick fails (checked against Källström's catalogue text 2026-10-29)
NAMED = {"G 203": (True, "Hróðbiôrn rísti – raden ovan är translittereringen"),
         "Vg 180": (True, "[F]undinn [hi]ogg – namnet till största delen bevarat"),
         "U 422": (True, "Gunnarr rísti rúnaR enligt översättningen; normaliseringsraden avbruten i utdraget"),
         "Sm 111": (False, "aku- – namnet skadat, läsningen omstridd")}
for x in rows:
    if x["signum"] in NAMED:
        x["named"], x["named_note"] = NAMED[x["signum"]]

# Runor 2020 (RAÄ), the newer edition of the same database
R = {fold_signum(r["signum"]): r for r in json.load(open(os.path.join(ROOT, "data", "raa", "runor_2020.json"),
                                                         encoding="utf-8"))["inscriptions"]}
for x in rows:
    ru = R.get(fold_signum(x["signum"]))
    x["runor_carvers"] = None if ru is None else [c.get("name") for c in ru.get("carvers") or []]

core = [x for x in rows if x["main_type"] == "B" and x["level"] <= 2 and x["object"] == "Runsten" and x["in_rundata"]]
miss = [x for x in core if not x["rundata_carvers"]]
by = lambda xs: Counter(x["signum"].split(" ")[0] for x in xs)  # noqa: E731
out = {"source": "Källström 2007, Bilaga 1; Rundata 3.1 (2018)", "n_catalogue_swedish": len(rows),
       "core_definition": "typ B:1–2 (ristarsignatur bredvid annan text), runsten, finns i Rundata",
       "n_core": len(core), "n_missing": len(miss), "n_missing_named": sum(x["named"] for x in miss),
       "by_province": {p: {"n": n, "missing": by(miss).get(p, 0)} for p, n in by(core).most_common()},
       "n_missing_also_runor": sum(1 for x in miss if x["runor_carvers"] is not None and not x["runor_carvers"]),
       "missing": [{k: x.get(k) for k in ("signum", "type", "normalization", "named", "named_note", "runor_carvers")} for x in miss]}
mu = {p: v for p, v in out["by_province"].items() if p in ("U", "Sö")}
out["outside_U_So"] = {"n": sum(v["n"] for p, v in out["by_province"].items() if p not in mu),
                       "missing": sum(v["missing"] for p, v in out["by_province"].items() if p not in mu)}
json.dump(out, open(os.path.join(OUT, "signaturer.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ("n_catalogue_swedish", "n_core", "n_missing", "n_missing_named", "n_missing_also_runor", "outside_U_So")}, ensure_ascii=False))
print(out["by_province"])
for x in miss:
    print(x["signum"], x["type"], "namn" if x["named"] else "–", "runor:", x["runor_carvers"], x["normalization"][:50])
