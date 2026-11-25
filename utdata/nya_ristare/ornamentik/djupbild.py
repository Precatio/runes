"""Bilder ur 3D-skanningarnas djupkartor (/Volumes/2TB/cache/runmodell/djup/<serie>/*.npz) för ornamentkodning:
lokal relief = djup minus utjämnat djup (σ = 12 mm), klippt vid percentil 2–98, spåren mörka – som en sten i släpljus.
Skanningarna är CC BY 4.0 (Kitzler Åhfeldt & Zedig, Zenodo); bilderna beräknas i Vitki och ligger i cachen.

    .venv/bin/python utdata/nya_ristare/ornamentik/djupbild.py SERIE [SERIE ...]
Skriver data/cache/hander/plansch/djupbild/<signum>__<fil>.jpg och djupbild.json {signum: [fil, ...]}.
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = "/Volumes/2TB/cache/runmodell/djup"
OUT = os.path.join(ROOT, "data", "cache", "hander", "plansch", "djupbild")
SIGMA_MM = 12.0
MAX_PX = 2600


def render(npz):
    z = np.load(npz)
    d = z["depth"].astype(np.float32)
    m = z["region"] if "region" in z.files else np.isfinite(d)  # stenytan (mask = bara spåren)
    res = float(z["res"]) or 0.6
    dd = np.where(m, d, np.nanmean(d[m]))  # utanför stenen: medeldjup
    rel = dd - gaussian_filter(dd, SIGMA_MM / res)
    lo, hi = np.percentile(rel[m], [2, 98])
    g = 1 - np.clip((rel - lo) / (hi - lo + 1e-9), 0, 1)  # spåren mörka
    img = (g * 255).astype(np.uint8)
    img[~m] = 255
    im = Image.fromarray(img)
    if max(im.size) > MAX_PX:
        f = MAX_PX / max(im.size)
        im = im.resize((int(im.size[0] * f), int(im.size[1] * f)), Image.LANCZOS)
    return im


def main(series):
    os.makedirs(OUT, exist_ok=True)
    idx_path = os.path.join(OUT, "djupbild.json")
    idx = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {}
    for s in series:
        for npz in sorted(glob.glob(os.path.join(SRC, s, "*.npz"))):
            meta = json.load(open(npz[:-4] + ".json", encoding="utf-8"))
            sig = meta.get("signum")
            if not sig:
                continue
            name = f"{sig.replace(' ', '_')}__{os.path.basename(npz)[:-4]}.jpg"
            path = os.path.join(OUT, name)
            if not os.path.exists(path):
                render(npz).save(path, quality=88)
            idx.setdefault(sig, [])
            if path not in idx[sig]:
                idx[sig].append(path)
        print(s, "klar", flush=True)
    json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(idx), "stenar med djupbild")


if __name__ == "__main__":
    main(sys.argv[1:])
