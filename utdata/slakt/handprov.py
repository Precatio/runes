"""Släktnätverket steg 1b: drar paren till det blinda handprovet enligt analysplaner/2026-11-01-slaktnatverket-steg1b.md
och skriver formuläret (utan signum) och nyckeln (utanför projektmappen). Med --resultat läses Viktors bedömningar ur
formuläret och jämförs med nyckeln.
    PYTHONPATH=. .venv/bin/python utdata/slakt/handprov.py [--resultat]"""
import hashlib
import json
import os
import random
import re
import sys

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
KEY = "/Volumes/2TB/tmp/slakt_handprov_nyckel.json"
FORM = os.path.join(OUT, "handprov_formular.md")
PLAN = "analysplaner/2026-11-01-slaktnatverket-steg1b.md"
assert open(os.path.join(ROOT, PLAN.replace(".md", ".sha256"))).read().startswith("f3ba7e78")


def draw():
    src = open(os.path.join(OUT, "steg1.py"), encoding="utf-8").read().split('res = {"plan"')[0]
    ns = {"__name__": "x", "__file__": os.path.join(OUT, "steg1.py")}
    exec(src, ns)
    ALL, W = ns["ALL"], ns["W"]
    obs, sure, _ = ns["model"](ALL, "province", (2, 10))
    gid = {}
    for gi, g in enumerate(W["groups"]):
        for m in g["members"]:
            gid.setdefault(m["rundata"], set()).add(gi)
    inw = lambda a, b: bool(gid.get(a, set()) & gid.get(b, set()))  # noqa: E731
    new = sorted((x["a"], x["b"]) for x in sure if not inw(x["a"], x["b"]))
    sure_k = {(x["a"], x["b"]) for x in sure}
    neg_pool = sorted((x["a"], x["b"]) for x in obs if (x["a"], x["b"]) not in sure_k and not inw(x["a"], x["b"]))
    pos_pool = sorted({tuple(sorted((p["a"], p["b"]))) for p in W["pairs"] if p["sure"] and p["a"] in ALL and p["b"] in ALL})
    assert (len(new), len(neg_pool), len(pos_pool)) == (5, 312, 266)  # planens 270 rader är 266 unika par (stenar i två grupper)
    rng = random.Random(2026)
    pos = rng.sample(pos_pool, 5)
    neg = rng.sample(neg_pool, 15)
    items = [(a, b, "ny") for a, b in new] + [(a, b, "känd") for a, b in pos] + [(a, b, "namn") for a, b in neg]
    rng.shuffle(items)
    return items, ALL, ns["km_of"]


def form(items, ALL, km_of):
    ins = {x["signum"]: x for x in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
    prov = {"U": "Uppland", "Sö": "Södermanland", "Ög": "Östergötland", "Vg": "Västergötland", "Sm": "Småland", "Öl": "Öland",
            "G": "Gotland", "Nä": "Närke", "Vs": "Västmanland", "Gs": "Gästrikland", "Hs": "Hälsingland", "M": "Medelpad",
            "J": "Jämtland", "D": "Dalarna", "Bo": "Bohuslän", "Vr": "Värmland"}
    clean = lambda t: re.sub(r"\s+", " ", (t or "").replace('"', "")).strip()  # noqa: E731
    L = ["# Blint handprov: samma släkt?", "",
         "Analysplan: `analysplaner/2026-11-01-slaktnatverket-steg1b.md`. 25 par runstenar. För varje par: står stenarna för "
         "**samma släkt**? Svara på raden *Bedömning* med **J** (samma släkt), **?** (kan inte avgöra) eller **N** (inte samma "
         "släkt), gärna med en kort kommentar. Slå inte upp stenarna under bedömningen; signum visas inte med avsikt.", ""]
    for i, (a, b, _) in enumerate(items, 1):
        d = km_of(ALL, a, b)
        L += [f"## Par {i}", "", f"Avstånd mellan stenarna: {('okänt' if d is None else str(round(d, 1)).replace('.', ',') + ' km')}", ""]
        for lab, s in (("Sten 1", a), ("Sten 2", b)):
            r = ins[s]
            L += [f"**{lab}** – {prov.get(s.split(' ')[0], s.split(' ')[0])}, {r.get('parish') or 'okänd socken'}; "
                  f"stilgrupp {r.get('style') or 'okänd'}", "", f"> {clean(r.get('normalization'))}", ">",
                  f"> *{clean(r.get('translation_en'))}*", ""]
        L += ["**Bedömning:** ", "", "**Kommentar:** ", "", "---", ""]
    open(FORM, "w", encoding="utf-8").write("\n".join(L))


if "--resultat" not in sys.argv:
    assert not os.path.exists(KEY), "Paren är redan dragna; dra inte om (planen)"
    items, ALL, km_of = draw()
    form(items, ALL, km_of)
    data = json.dumps({"plan": PLAN, "items": [{"par": i, "a": a, "b": b, "grupp": g} for i, (a, b, g) in enumerate(items, 1)]},
                      ensure_ascii=False, indent=1)
    open(KEY, "w", encoding="utf-8").write(data)
    sha = hashlib.sha256(data.encode("utf-8")).hexdigest()
    open(os.path.join(OUT, "handprov_nyckel.sha256"), "w").write(f"{sha}  {KEY}\n")
    print("formulär:", FORM, "| par:", len(items), "| nyckelns SHA-256:", sha[:16])
