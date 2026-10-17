"""Hur språklik är en runföljd? Kryptologins logik på de vikingatida inskrifter som utgivarna inte läser som språk.

Tre mått, fastställda innan resultaten sågs (2026-10-16):
  1. Bitar per runa: hur förutsägbar runföljden är för en Kneser–Ney-modell över tre runor i följd (NLTK), tränad på
     alla tolkade vikingatida inskrifter. Lägre = mer språklik. Jämförelse: tolkade inskrifter som modellen inte har
     sett (femdelad, crc32 mod 5) och samma texter med runorna slumpvis omkastade inom texten (samma runor, ingen
     ordning).
  2. Koincidensindex (kryptologins mått på hur ojämnt tecknen är fördelade): sannolikheten att två slumpvis valda runor
     i texten är samma runa. Lika fördelning över 16 runor ger 1/16 ≈ 0,063.
  3. Runrad: den längsta följden i futharkens ordning (fuþorkhniastbmlR) i texten, och hur stor del av texten som
     följer futharkens ordning med enstaka runor överhoppade (längsta gemensamma delföljd), så att en runrad med
     avvikelser (fuþrkhainsl) också känns igen.
Jämförelsen är matchad (rättad 2026-10-16, innan bedömningarna lästes): en sönderslagen text är svårare att förutsäga
bara för att bitarna är korta. Varje inskrift jämförs därför med 200 bitar ur verkliga tolkade texter som modellen inte
har sett, klippta i exakt samma bitlängder och från samma land (Danmark, Norge, övriga; tillagt 2026-10-16, eftersom
danska och norska fragment annars mättes mot en mest svensk referens), och med samma bitar omkastade.
Bedömning:
  runrad      minst sex runor i följd i futharkens ordning, eller minst åtta runor och 70 procent av texten i
              futharkens ordning (tillagt 2026-10-16 efter att DR EM85;470C fuþrkhainsl lästs som inte språk);
  språklik    bitar per runa högst den 90:e percentilen bland de matchade verkliga bitarna;
  inte språk  över den 99:e percentilen, eller närmare medianen för de omkastade bitarna än för de verkliga;
  oklart      däremellan.
Runorna läses ur Rundatas translitterering utan skiljetecken; förlorade och oläsliga runor delar texten i bitar som
bedöms var för sig. Bara inskrifter med minst tio läsbara runor bedöms.
    .venv/bin/python -m scripts.runlm_sprakprov
Skriver utdata/sprakprov/sprakprov.json och sprakprov.csv."""
from __future__ import annotations

import csv
import json
import math
import os
import random
import re
import sys
import zlib
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import runlm as rl  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "utdata", "sprakprov")
FUTHARK = "fuþorkhniastbmlR"
ORDER = 3
MIN_RUNES = 10


def segments(translit: str) -> list[str]:
    """The readable runs of runes: dividers removed, lost or unread signs as breaks. Only the main reading counts:
    alternative sections (§..Q) are dropped and of Rundata's alternatives 'a/b' the first is kept (rättat 2026-10-17;
    before, both were counted, which doubled the runes of 16 of the 123 inscriptions and let 11 pass the ten-rune limit)."""
    parts = [re.sub(r"(\S+)/\S+", r"\1", t) for _, t in rl.sections(translit or "")]
    t = rl.clean_translit(" ".join(parts))
    t = re.sub(r"[:÷'·×+|¶\s]", "", t)
    return [s for s in re.split(r"[^a-zþæøR]+", t) if len(s) >= 2]


def interpreted(r) -> bool:
    n = re.sub(r"<[^>]*>", " ", r.get("normalization") or "")
    return sum(1 for _, p in rl.sections(n) for w in rl.norm_words(p) if not w.startswith("...")) >= 2


def train(segs):
    from nltk.lm import KneserNeyInterpolated
    from nltk.lm.preprocessing import padded_everygram_pipeline
    data, vocab = padded_everygram_pipeline(ORDER, [list(s) for s in segs])
    lm = KneserNeyInterpolated(ORDER)
    lm.fit(data, vocab)
    return lm


def bits_per_rune(lm, segs) -> float:
    """Mean bits per rune over the segments (the end of each segment counted as a symbol too)."""
    tot, n = 0.0, 0
    for s in segs:
        ss = ["<s>"] * (ORDER - 1) + list(s) + ["</s>"]
        for i in range(ORDER - 1, len(ss)):
            tot -= lm.logscore(ss[i], ss[i - ORDER + 1:i])
            n += 1
    return tot / max(1, n)


def coincidence(runes: str) -> float:
    c, n = Counter(runes), len(runes)
    return sum(v * (v - 1) for v in c.values()) / (n * (n - 1)) if n > 1 else float("nan")


def futhark_run(segs) -> int:
    """The longest stretch of runes in futhark order (fu, uþ, þo …) within a segment."""
    nxt = {a: b for a, b in zip(FUTHARK, FUTHARK[1:])}
    best = 0
    for s in segs:
        run = 1
        for a, b in zip(s, s[1:]):
            run = run + 1 if nxt.get(a) == b else 1
            best = max(best, run)
    return best


def futhark_lcs(segs) -> int:
    """How many runes of the text follow the futhark's order, runes skipped allowed (longest common subsequence)."""
    best = 0
    for s in segs:
        prev = [0] * (len(FUTHARK) + 1)
        for ch in s:
            cur = [0] * (len(FUTHARK) + 1)
            for j, f in enumerate(FUTHARK, 1):
                cur[j] = prev[j - 1] + 1 if ch == f else max(prev[j], cur[j - 1])
            prev = cur
        best = max(best, prev[-1])
    return best


def region(signum: str) -> str:
    p = signum.split()[0]
    return "DR" if p == "DR" else "N" if p == "N" else "SE" if p in SWEDISH else "övriga"


SWEDISH = {"U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "J", "Bo", "D", "Hä", "Ån"}


def shuffled(segs, rng):
    """The same runes in random order, cut into segments of the same lengths."""
    runes = list("".join(segs))
    rng.shuffle(runes)
    out, i = [], 0
    for s in segs:
        out.append("".join(runes[i:i + len(s)]))
        i += len(s)
    return out


def matched(lms, pools, segs, k, rng, n=200, group="alla"):
    """Bits per rune for n pseudo-inscriptions cut from real interpreted texts the fold-k model has not seen, with the
    same segment lengths as segs, and for the same pieces shuffled."""
    lens = [len(x) for x in segs]
    pool = [x for x in pools[(k, group)] if len(x) >= min(lens)] or [x for x in pools[(k, "alla")] if len(x) >= min(lens)]
    real, shuf = [], []
    for _ in range(n):
        pieces = []
        for L in lens:
            cand = [x for x in rng.sample(pool, min(40, len(pool))) if len(x) >= L] or [max(pool, key=len)]
            src = rng.choice(cand)
            a = rng.randrange(0, max(1, len(src) - L + 1))
            pieces.append(src[a:a + L])
        real.append(bits_per_rune(lms[k], pieces))
        shuf.append(bits_per_rune(lms[k], shuffled(pieces, rng)))
    return np.array(real), np.array(shuf)


def main():
    os.makedirs(OUT, exist_ok=True)
    recs = [r for r in rl.load_rundata() if rl.viking(r) and r.get("transliteration") and r.get("normalization")]
    ref = [r for r in recs if interpreted(r)]
    unread = [r for r in recs if not interpreted(r) and sum(map(len, segments(r["transliteration"]))) >= MIN_RUNES]
    print(f"tolkade: {len(ref)} | otolkade med minst {MIN_RUNES} runor: {len(unread)}", flush=True)
    fold = lambda r: zlib.crc32(r["signum"].encode()) % 5  # noqa: E731
    lms = {k: train([s for r in ref if fold(r) != k for s in segments(r["transliteration"])]) for k in range(5)}
    pools = {(k, g): [s for r in ref if fold(r) == k and (g == "alla" or region(r["signum"]) == g) for s in segments(r["transliteration"])]
             for k in range(5) for g in ("DR", "N", "SE", "alla")}
    rng = random.Random(2026)
    rows = []
    for i, r in enumerate(unread):
        segs = segments(r["transliteration"])
        runes = "".join(segs)
        k = fold(r)
        b = bits_per_rune(lms[k], segs)
        g = region(r["signum"])
        real, shuf = matched(lms, pools, segs, k, rng, group=g if g in ("DR", "N", "SE") else "alla")
        p90, p99, med_r, med_s = np.percentile(real, 90), np.percentile(real, 99), np.median(real), np.median(shuf)
        fr, fl = futhark_run(segs), futhark_lcs(segs)
        if fr >= 6 or (fl >= 8 and fl >= 0.7 * len(runes)):
            verdict = "runrad"
        elif b <= p90:
            verdict = "språklik"
        elif b > p99 or abs(b - med_s) < abs(b - med_r):
            verdict = "inte språk"
        else:
            verdict = "oklart"
        rows.append({"signum": r["signum"], "place": r.get("place") or "", "runes": len(runes), "segments": len(segs),
                     "bits_per_rune": round(b, 3), "real_median": round(float(med_r), 3), "real_p90": round(float(p90), 3),
                     "shuffled_median": round(float(med_s), 3), "percentile": round(float((real < b).mean() * 100), 1),
                     "coincidence": round(coincidence(runes), 4), "futhark_run": fr, "futhark_lcs": fl, "region": g, "verdict": verdict,
                     "text": re.sub(r"\s+", " ", rl.clean_translit(r["transliteration"]))[:120]})
        if i % 20 == 0:
            print(f"{i + 1} av {len(unread)}", flush=True)
    rows.sort(key=lambda x: x["percentile"])
    ic_real = [coincidence("".join(segments(r["transliteration"]))) for r in ref if sum(map(len, segments(r["transliteration"]))) >= MIN_RUNES]
    summary = {"coincidence_median_real": float(np.nanmedian(ic_real)),
               "verdicts": dict(Counter(x["verdict"] for x in rows)), "rows": rows}
    json.dump(summary, open(os.path.join(OUT, "sprakprov.json"), "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "sprakprov.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("bedömningar:", summary["verdicts"])


if __name__ == "__main__":
    main()
