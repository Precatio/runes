"""Den blinda AI-läsningen (Språk & Fonetik, steg 1 i api/routers/phonetics.py – samma instruktion, schema och temperatur)
prövad mot Rundatas translitterering, med minneskontroll.

Stenar: de som redan är hämtade till bilder/ (stiltestet) och har en translitterering i Rundata; slumpat urval med fast frö.
  normal     bilden som den är
  spegel     bilden spegelvänd – runorna blir bakvända och ordningen omvänd; läser modellen på riktigt sjunker träffen,
             minns den stenen är den oförändrad
  halv       bara vänstra halvan – täckningen ska ungefär halveras om modellen läser bilden
Mått: appens eget (src/reading.compare): andel av våra runor som återfinns i Rundatas läsning i följder om minst tre
(char_agreement) och hur stor del av Rundatas text vi fått med (coverage). Svaren sparas rad för rad; körs om utan att
betala för färdiga rader; stoppar när nyckeln eller krediten tar slut.
    ANTHROPIC_API_KEY=… .venv/bin/python utdata/stilgrupp_ai/lastest.py [--normal 30 --spegel 8 --halv 4]
    .venv/bin/python utdata/stilgrupp_ai/lastest.py --utvardera
"""
import argparse
import json
import os
import random
import re
import sys
import time
from io import BytesIO
from statistics import mean, median

from PIL import Image, ImageOps

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
HERE = os.path.dirname(os.path.abspath(__file__))
BILDER = os.path.join(HERE, "bilder")
RES = os.path.join(HERE, "lastest.jsonl")

from api.rundata import store  # noqa: E402
from src import reading  # noqa: E402

SRC = open(os.path.join(ROOT, "api", "routers", "phonetics.py"), encoding="utf-8").read()
INSTRUKTION = SRC.split('step1_instruction = """', 1)[1].split('"""', 1)[0]
assert "dum OCR-skanner" in INSTRUKTION and "raw_transliteration" in INSTRUKTION
from api.routers.phonetics import BLIND_READING_SCHEMA  # noqa: E402


def urval(n_normal: int, n_spegel: int, n_halv: int, fro: int = 20261020) -> list[tuple[str, str]]:
    s = store()
    kand = []
    for f in sorted(os.listdir(BILDER)):
        sg = f[:-4].replace("_", " ")
        rec = s.get(sg)
        if rec and len((rec.get("transliteration") or "").strip()) >= 15:
            kand.append(rec["signum"])
    rng = random.Random(fro)
    rng.shuffle(kand)
    normal = kand[:n_normal]
    return [(sg, "normal") for sg in normal] + [(sg, "spegel") for sg in normal[:n_spegel]] + [(sg, "halv") for sg in normal[:n_halv]]


def bild(signum: str, variant: str) -> tuple[bytes, str]:
    path = os.path.join(BILDER, re.sub(r"[^\w]+", "_", signum) + ".jpg")
    im = Image.open(path).convert("RGB")
    if variant == "spegel":
        im = ImageOps.mirror(im)
    elif variant == "halv":
        im = im.crop((0, 0, im.width // 2, im.height))
    out = BytesIO()
    im.save(out, "JPEG", quality=90)
    return out.getvalue(), "image/jpeg"


def kor(a):
    from api import llm
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    assert key, "Sätt ANTHROPIC_API_KEY"
    ctx = llm.AIContext("claude", key)
    s = store()
    done = {(json.loads(l)["signum"], json.loads(l)["variant"]) for l in open(RES) if json.loads(l).get("raw") is not None} if os.path.exists(RES) else set()
    rows = urval(a.normal, a.spegel, a.halv)
    print(f"{len(rows)} anrop i urvalet, {len(done)} redan gjorda")
    fel_i_rad = 0
    with open(RES, "a") as out:
        for i, (sg, variant) in enumerate(rows):
            if (sg, variant) in done:
                continue
            rec = s.get(sg)
            data, mime = bild(sg, variant)
            try:
                r = llm.generate(ctx, "Translitterera de runor som syns i bilden.", system=INSTRUKTION, images=[(data, mime)],
                                 schema=BLIND_READING_SCHEMA, tier="pro", temperature=0.0)
                raw = (r.data or {}).get("raw_transliteration", "") or ""
                cmp = reading.compare(raw, rec["transliteration"])
                row = {"signum": sg, "variant": variant, "raw": raw, "rundata": rec["transliteration"],
                       "char_agreement": cmp["char_agreement"], "coverage": cmp["coverage"], "word_agreement": cmp["word_agreement"],
                       "same_words": cmp["same_words"], "words_ours": cmp["words_ours"], "words_rundata": cmp["words_rundata"],
                       "tokens": r.tokens, "model": r.model}
                fel_i_rad = 0
            except Exception as e:
                row = {"signum": sg, "variant": variant, "error": str(e)[:300]}
                fel_i_rad += 1
                text = str(e).lower()
                if fel_i_rad >= 3 or any(k in text for k in ("credit", "billing", "insufficient", "401", "402", "authentication")):
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
                    print("stoppar:", str(e)[:200])
                    break
                time.sleep(5)
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            print(f"{i + 1}/{len(rows)} {sg} {variant}: träff {row.get('char_agreement')} täckning {row.get('coverage')} | {row.get('raw', row.get('error', ''))[:80]}")


def utvardera():
    rows = [json.loads(l) for l in open(RES)]
    ok = [r for r in rows if r.get("raw") is not None]
    out = {"n": len(ok), "fel": len(rows) - len(ok), "tokens_medel": mean(r["tokens"] for r in ok) if ok else None}
    for v in ("normal", "spegel", "halv"):
        g = [r for r in ok if r["variant"] == v]
        if not g:
            continue
        out[v] = {"n": len(g), "traff_medel": round(mean(r["char_agreement"] for r in g), 3),
                  "traff_median": round(median(r["char_agreement"] for r in g), 3),
                  "tackning_medel": round(mean(r["coverage"] for r in g), 3),
                  "andel_traff_over_0_6": round(mean(r["char_agreement"] >= 0.6 for r in g), 3),
                  "andel_traff_over_0_9": round(mean(r["char_agreement"] >= 0.9 for r in g), 3),
                  "ord_ratt_andel": round(sum(r["same_words"] for r in g) / max(1, sum(r["words_rundata"] for r in g)), 3)}
    # samma sten normal mot spegel: hur mycket faller träffen när runorna är bakvända?
    par = {}
    for r in ok:
        par.setdefault(r["signum"], {})[r["variant"]] = r["char_agreement"]
    diffs = [p["normal"] - p["spegel"] for p in par.values() if "normal" in p and "spegel" in p]
    if diffs:
        out["spegel_fall_per_sten"] = {"n": len(diffs), "medel": round(mean(diffs), 3),
                                       "andel_stenar_dar_spegeln_laser_lika_bra": round(mean(d <= 0.1 for d in diffs), 3)}
    json.dump(out, open(os.path.join(HERE, "lastest_utvardering.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--normal", type=int, default=30)
    ap.add_argument("--spegel", type=int, default=8)
    ap.add_argument("--halv", type=int, default=4)
    ap.add_argument("--utvardera", action="store_true")
    a = ap.parse_args()
    if not a.utvardera:
        kor(a)
    utvardera()
