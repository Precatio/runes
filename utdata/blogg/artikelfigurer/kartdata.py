"""Punkterna till två artikelkartor (Viktor 2026-11-01): signerade runstenar med och utan ristare i Rundata
("Ristarna som aldrig blev ihågkomna") och de 14 runstenarna efter döttrar ("Döttrarna som runstenarna glömde").
Listorna kommer ur artiklarnas egna skript och kontrolleras mot deras resultatfiler. Skriver kartdata.json; kartorna
ritas av artikelkartor.R.
    .venv/bin/python utdata/blogg/artikelfigurer/kartdata.py"""
import json
import os

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", "..", ".."))
ins = {x["signum"]: x for x in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
SE = ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "J", "D", "Bo", "Vr")
is_stone = lambda x: "runsten" in (x.get("object") or "").lower()  # noqa: E731
pt = lambda s: {"signum": s, "lat": ins[s].get("lat"), "lon": ins[s].get("lon")}  # noqa: E731

# Ristarna: kärnan i utdata/signaturer/signaturer.json (typ B:1–2, runsten, i Rundata)
SIG = json.load(open(os.path.join(ROOT, "utdata", "signaturer", "signaturer.json"), encoding="utf-8"))
core = SIG["core"]
assert (len(core), sum(not c["rundata_carver"] for c in core), SIG["outside_U_So"]) == (177, 20, {"n": 38, "missing": 18})
rist = [dict(pt(c["signum"]), known=c["rundata_carver"], prov=c["signum"].split(" ")[0]) for c in core]

# Döttrarna: listorna i dottrar_fakta.py (handgenomgång), bara runstenar
DOT = ["Ög 113", "Ög 239", "Sö 331", "Sm 94", "Vg 17", "U 107", "U 311", "U 312", "U 313", "U 314", "U 377", "U 489", "U 821",
       "U 861", "U 867", "U 923", "U Fv1971;212B", "G 112"]
MOR = ["Ög 113", "Sö 331", "U 311", "U 313", "U 314", "U 377", "U 489", "U 821", "U Fv1971;212B"]
src = open(os.path.join(ROOT, "utdata", "blogg", "build", "dottrar_fakta.py"), encoding="utf-8").read()
assert repr(DOT).replace("'", '"').replace(", ", ",") in src.replace(", ", ",") and repr(MOR).replace("'", '"').replace(", ", ",") in src.replace(", ", ",")
DOT = [s for s in DOT if is_stone(ins[s])]
MOR = [s for s in MOR if is_stone(ins[s])]
F = json.load(open(os.path.join(ROOT, "utdata", "blogg", "build", "dottrar.json")))
assert (len(DOT), len(MOR)) == (F["n_dot"], F["mor"]) == (14, 7)
dot = [dict(pt(s), mother=s in MOR) for s in DOT]
bg = [pt(s) for s, x in ins.items() if x.get("period") == "V" and s.split(" ")[0] in SE and is_stone(x)]
out = {"ristare": rist, "dottrar": dot, "bakgrund": [b for b in bg if b["lat"] is not None]}
out["saknar_koordinater"] = {"ristare": [r["signum"] for r in rist if r["lat"] is None], "dottrar": [d["signum"] for d in dot if d["lat"] is None]}
json.dump(out, open(os.path.join(OUT, "kartdata.json"), "w"), ensure_ascii=False, indent=1)
print({k: len(v) for k, v in out.items() if isinstance(v, list)}, out["saknar_koordinater"])
