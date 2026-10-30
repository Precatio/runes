"""Bilderna på runstenarna enligt analysplaner/2026-10-30-bilderna-pa-runstenarna.md: Sterns bildkatalog
(data/cache/literature/stern2013_bilder.csv) mot appens korpus, prövat med frågebyggaren (src/question.py: Mantel–
Haenszel över landskap × tid, halvprov, ristarprov). --dry kontrollerar bara kopplingen (inga prov räknas).
    PYTHONPATH=. .venv/bin/python utdata/bilder/analys.py --dry
    PYTHONPATH=. .venv/bin/python utdata/bilder/analys.py          Skriver resultat.json och resultat.md."""
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, ".")
from api.rundata import store  # noqa: E402
from src import entities, question, r_bridge  # noqa: E402
from src.signum import fold_signum  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
STERN = "data/cache/literature/stern2013_bilder.csv"
DRY = "--dry" in sys.argv
RESA = ("skepp", "ryttare")
FORKRISTEN = ("mask", "fyrfotadjur", "sigurd", "hammare", "orm_som_bild")
DJURBILD = ("fyrfotadjur", "fågel", "häst", "orm_som_bild")
CLASSES = ("skepp", "ryttare", "häst", "fågel", "mask", "fyrfotadjur", "människa", "kors", "sigurd", "kristus", "tor",
           "hammare", "orm_som_bild", "vagn", "byggnad")
# the animal name elements, fixed in the plan (folded spelling: þ→th, ô/ǫ→o, accents off)
ANIMAL = re.compile(r"ulf|bi?orn|\borm|hrafn|ravn|^orn|arn", re.I)

# ---- Stern's stones -------------------------------------------------------------------------------------------------
stern = [r for r in csv.DictReader(open(STERN, encoding="utf-8")) if r["section"] in ("1.A", "1.A tillägg", "1.B")]
by_key = {}
for r in stern:
    k = fold_signum(r["signum"])
    cur = by_key.setdefault(k, {"section": r["section"], "n_entries": 0, **{c: 0 for c in CLASSES}, "known": 0})
    cur["n_entries"] += 1
    has_class = any(int(r[c]) for c in CLASSES)
    cur["known"] = max(cur["known"], int(has_class))
    for c in CLASSES:
        cur[c] = max(cur[c], int(r[c]))

# ---- the corpus rows, with the image flags and the animal names attached ---------------------------------------------
s = store()
rows = r_bridge.corpus_rows(s.inscriptions)
recs = {r["signum"]: r for r in s.inscriptions}


def flag(img, classes):
    """1 = an image of this kind, 0 = no image at all, None = an image of another kind (or of unknown kind)."""
    if img is None:
        return 0
    if not img["known"]:
        return None
    return 1 if any(img[c] for c in classes) else None


def fold_name(n):
    import unicodedata
    t = n.replace("Þ", "th").replace("þ", "th").replace("ð", "d").replace("ô", "o").replace("ǫ", "o").replace("ø", "o")
    t = unicodedata.normalize("NFKD", t)
    return "".join(ch for ch in t if not unicodedata.combining(ch)).lower()


matched = 0
for r in rows:
    img = by_key.get(fold_signum(r["signum"]))
    matched += img is not None
    r["_bild"] = 0 if img is None else 1
    r["_bild_resa"] = flag(img, RESA)
    r["_bild_forkristen"] = flag(img, FORKRISTEN)
    r["_bild_kors"] = flag(img, ("kors",))
    r["_djurbild"] = flag(img, DJURBILD)
    try:
        names = [p["name"] for p in entities.extract(recs[r["signum"]])["persons"] if p.get("name") and not p.get("uncertain")]
    except Exception:  # noqa: BLE001
        names = []
    r["_djurnamn"] = None if not names else int(any(ANIMAL.search(fold_name(n)) for n in names))
    r["_img"] = img

question.VAR.update({
    "bild_resa": ("Resebild (skepp eller ryttare)", "Bild", "Stern 2013: skepp eller ryttare; 0 = ingen bild alls.", lambda r: r.get("_bild_resa")),
    "bild_forkristen": ("Förkristen figur", "Bild", "Stern 2013: mask, fyrfotadjur, Sigurd, hammare eller orm som bild; 0 = ingen bild.", lambda r: r.get("_bild_forkristen")),
    "bild_kors": ("Kors som bild", "Bild", "Stern 2013: kors som figurbild; 0 = ingen bild.", lambda r: r.get("_bild_kors")),
    "djurbild": ("Djurbild", "Bild", "Stern 2013: fyrfotadjur, fågel, häst eller orm som bild; 0 = ingen bild.", lambda r: r.get("_djurbild")),
    "djurnamn": ("Djurnamn", "Namn", "Någon person på stenen bär ulf-, björn-, orm-, ravn- eller örn-led.", lambda r: r.get("_djurnamn")),
})
prep = question.prepare(rows)

if DRY:
    print(f"korpus {len(rows)} stenar; Sterns svenska vikingatida runstenar i korpusen: {matched} av {len(by_key)} nycklar")
    print("inte i korpusen:", [k for k in by_key if k not in {fold_signum(r['signum']) for r in rows}])
    for key in ("_bild", "_bild_resa", "_bild_forkristen", "_bild_kors", "_djurbild", "_djurnamn"):
        c = Counter(r[key] for r in rows)
        print(f"  {key:17} 1: {c[1]:5}  0: {c[0]:5}  None: {c[None]:5}")
    for a, b in (("fard", "_bild_resa"), ("kristen", "_bild_forkristen"), ("bon", "_bild_kors")):
        av = sum(1 for r in rows if r[b] == 1 and r.get(f"pm_{a}" if a != "fard" else "cat_fard") not in ("", None))
        print(f"  {a} tillgänglig bland {b}=1: {av}")
    print("  djurnamn bland bildstenar:", Counter(r["_djurnamn"] for r in rows if r["_bild"]))
    sys.exit()

# ---- the tests -------------------------------------------------------------------------------------------------------
res = {"n_rows": len(rows), "n_image_stones": matched}
res["B1"] = question.ask(prep, "fard", "drag", "bild_resa")
res["B2a"] = question.ask(prep, "kristen", "drag", "bild_forkristen")
res["B2b"] = question.ask(prep, "bon", "drag", "bild_kors")
res["B3"] = question.ask(prep, "djurbild", "drag", "djurnamn")


def pval(x):
    return x.get("p") if isinstance(x.get("p"), (int, float)) else (x.get("adjusted") or {}).get("p")


ps = {"B1": pval(res["B1"]), "B2": max(p for p in (pval(res["B2a"]), pval(res["B2b"])) if p is not None) if any(
    pval(res[k]) is not None for k in ("B2a", "B2b")) else None, "B3": pval(res["B3"])}
ps = {k: v for k, v in ps.items() if v is not None}
run = 0
for i, k in enumerate(sorted(ps, key=ps.get)):
    run = max(run, min(1, ps[k] * (len(ps) - i)))
    res[k + "_holm"] = run
# ---- descriptive ------------------------------------------------------------------------------------------------------
img_rows = [r for r in rows if r["_bild"]]
res["describe"] = {
    "by_province": {p: dict(Counter(c for r in img_rows if r["province"] == p for c in CLASSES if r["_img"][c]))
                    for p in sorted({r["province"] for r in img_rows})},
    "by_style": {st: dict(Counter(c for r in img_rows if (r.get("style") or "?") == st for c in CLASSES if r["_img"][c]))
                 for st in sorted({r.get("style") or "?" for r in img_rows})},
    "sigurd": [{"signum": r["signum"], "province": r["province"], "style": r.get("style"), "carver": r.get("carver")}
               for r in img_rows if r["_img"]["sigurd"]],
    "images_per_stone": dict(Counter(sum(r["_img"][c] for c in CLASSES) for r in img_rows)),
}
json.dump(res, open(os.path.join(OUT, "resultat.json"), "w"), ensure_ascii=False, indent=1, default=str)
for k in ("B1", "B2a", "B2b", "B3"):
    x = res[k]
    print(k, x.get("verdict"), {kk: x.get(kk) for kk in ("n", "with_b", "without_b", "p", "adjusted", "halves", "carvers") if kk in x})
print("Holm:", {k: res.get(k + "_holm") for k in ("B1", "B2", "B3")})
