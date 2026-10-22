"""Vad säger ett delvis bevarat runtecken? För varje runa i den yngre futharken (långkvist) och varje del av runans
ruta som kan vara bevarad (övre/nedre halvan, vänster/höger om huvudstaven, övre/mellersta/nedre tredjedelen) räknas
ut vilka runor som ser likadana ut i just den delen: samma streck där, och inga streck där den andra saknar dem.
Runorna ritas med typsnittet Apple Symbols, skalas till samma höjd och läggs med huvudstaven i mitten; likheten mäts
med en tolerans på 5 % av runhöjden för att rymma ristningens variation. Tabellen används av
scripts/runlm_restore_test.py --trace för att pröva vad spår i en lucka är värda för ifyllningen.
Skriver data/rune_traces.json.
    .venv/bin/python -m scripts.rune_traces"""
import json
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "/System/Library/Fonts/Apple Symbols.ttf"
GLYPH = dict(zip("fuþorkhniastbmlR", "ᚠᚢᚦᚬᚱᚴᚼᚾᛁᛅᛋᛏᛒᛘᛚᛦ", strict=False))
# dotted runes and late letters drawn like their base rune (a dot is easily lost)
BASE = {"e": "i", "y": "u", "g": "k", "d": "t", "p": "b", "c": "k", "æ": "a", "ø": "o"}
H, W, TOL = 96, 80, 5


def glyph(ch):
    im = Image.new("L", (400, 400), 0)
    ImageDraw.Draw(im).text((100, 50), GLYPH[ch], font=ImageFont.truetype(FONT, 200), fill=255)
    a = np.array(im) > 127
    ys, xs = np.nonzero(a)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.uint8) * 255
    a = cv2.resize(a, (max(1, round(a.shape[1] * H / a.shape[0])), H), interpolation=cv2.INTER_AREA) > 127
    # the main stave: the column with most ink (the sun-rune s has none; its middle is used)
    col = a.sum(0)
    sx = int(col.argmax()) if col.max() > 0.8 * H else a.shape[1] // 2
    out = np.zeros((H, W), bool)
    x0 = W // 2 - sx
    for x in range(a.shape[1]):
        if 0 <= x0 + x < W:
            out[:, x0 + x] = a[:, x]
    return out


REGIONS = {
    "övre halvan": (slice(0, H // 2), slice(0, W)), "nedre halvan": (slice(H // 2, H), slice(0, W)),
    "vänster om staven": (slice(0, H), slice(0, W // 2 + 4)), "höger om staven": (slice(0, H), slice(W // 2 - 4, W)),
    "övre tredjedelen": (slice(0, H // 3), slice(0, W)), "mellersta tredjedelen": (slice(H // 3, 2 * H // 3), slice(0, W)),
    "nedre tredjedelen": (slice(2 * H // 3, H), slice(0, W)),
}


def same(a, b):
    """Does part a look like part b: a's strokes lie on b's (within the tolerance), and b's on a's."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * TOL + 1, 2 * TOL + 1))
    da, db = cv2.dilate(a.astype(np.uint8), k) > 0, cv2.dilate(b.astype(np.uint8), k) > 0
    na, nb = a.sum(), b.sum()
    if na < 20 or nb < 20:
        return na < 20 and nb < 20
    return (a & ~db).sum() / na <= 0.1 and (b & ~da).sum() / nb <= 0.1


def main():
    G = {ch: glyph(ch) for ch in GLYPH}
    table = {}
    for ch in G:
        table[ch] = {}
        for name, (ys, xs) in REGIONS.items():
            ok = sorted(c for c in G if same(G[ch][ys, xs], G[c][ys, xs]))
            ok += sorted(d for d, b in BASE.items() if b in ok)
            table[ch][name] = "".join(ok)
    for d, b in BASE.items():
        table[d] = table[b]
    json.dump({"regions": list(REGIONS), "allowed": table,
               "note": "Runor som ser likadana ut i den bevarade delen (scripts/rune_traces.py)."},
              open(os.path.join(ROOT, "data", "rune_traces.json"), "w"), ensure_ascii=False, indent=1)
    for ch in GLYPH:
        print(ch, {n: v for n, v in table[ch].items()})
    sizes = [len(v) for ch in GLYPH for v in table[ch].values()]
    print("genomsnittligt antal möjliga runor:", round(sum(sizes) / len(sizes), 1), "av", len(GLYPH) + len(BASE))


if __name__ == "__main__":
    main()
