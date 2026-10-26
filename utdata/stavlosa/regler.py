"""Prövar regler för gränsen mellan två runor på de sparade strecken (utdata/stavlosa/streck/). Mått: hittade runor
mot textens runor, per fil. Regeln "takt" (runornas takt längs slingan ur autokorrelationen, gräns 0,3 takter) är
bestämd i förväg ur geometrin, inte anpassad efter texterna; de andra visas som jämförelse.

  .venv/bin/python utdata/stavlosa/regler.py
"""
import glob
import json
import math
import os

import numpy as np

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streck")
F_TAKT = 0.3          # the limit in rune pitches (fixed beforehand)
LAG_RANGE = (0.2, 1.2)  # where the pitch is looked for, in band heights


def runs(items, heights, limit_of_piece):
    n, cur = 0, None
    for p, a, e in sorted(items):
        if cur is not None and p == cur[0] and a - cur[1] <= limit_of_piece(p):
            cur = (p, max(cur[1], e))
        else:
            n += 1
            cur = (p, e)
    return n


def pitch(items, heights, bin_mm=1.0):
    """The runes' pitch along the band (mm): the first strong peak of the stroke occupancy's autocorrelation, pooled
    over the band pieces (each normalised), within LAG_RANGE band heights."""
    by = {}
    for p, a, e in items:
        by.setdefault(p, []).append((a, e))
    hs = [heights[str(p)] if str(p) in heights else heights.get(p) for p in by]
    hs = [h for h in hs if h]
    if not hs:
        return None
    h_med = float(np.median(hs))
    lo, hi = int(LAG_RANGE[0] * h_med / bin_mm), int(LAG_RANGE[1] * h_med / bin_mm) + 1
    pooled = np.zeros(hi + 1)
    for p, iv in by.items():
        end = max(e for _, e in iv)
        occ = np.zeros(int(end / bin_mm) + 2)
        for a, e in iv:
            occ[int(a / bin_mm):int(e / bin_mm) + 1] = 1.0
        occ = occ - occ.mean()
        if len(occ) <= hi or not occ.any():
            continue
        ac = np.correlate(occ, occ, mode="full")[len(occ) - 1:len(occ) + hi]
        if ac[0] > 0:
            pooled[:len(ac)] += ac / ac[0]
    if not pooled[lo:hi].any():
        return None
    return float((lo + int(np.argmax(pooled[lo:hi]))) * bin_mm)


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(D, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        items = [tuple(x) for x in d["items"]]
        H = {int(k): v for k, v in d["heights"].items()}
        P = pitch(items, d["heights"])
        takt = runs(items, H, lambda p: F_TAKT * P) if P else None
        fixed = {fr: runs(items, H, lambda p, fr=fr: fr * H.get(p, 0)) for fr in (0.1, 0.15, 0.2)}
        rows.append((d["signum"], os.path.basename(f)[:-5], "stavlösa" in (d.get("rune_types") or ""), d["text_runor"],
                     len(items), P, takt, fixed))
    print(f"{'fil':30} {'st':2} {'text':>4} {'streck':>6} {'takt mm':>7} {'takt':>5} {'0.10h':>5} {'0.15h':>5} {'0.20h':>5}")
    for sg, stem, st, t, n, P, takt, fx in sorted(rows, key=lambda r: (not r[2], r[1])):
        print(f"{stem[:30]:30} {'J' if st else ' ':2} {t:4} {n:6} {P or 0:7.1f} {takt or 0:5} {fx[0.1]:5} {fx[0.15]:5} {fx[0.2]:5}")
    json.dump([{"fil": r[1], "signum": r[0], "stavlosa": r[2], "text": r[3], "streck": r[4], "takt_mm": r[5],
                "runor_takt": r[6], "runor_fast": {str(k): v for k, v in r[7].items()}} for r in rows],
              open(os.path.join(os.path.dirname(D), "regler.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
