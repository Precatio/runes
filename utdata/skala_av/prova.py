"""Skala av vittringen provad på en skanning (src/peel.py, samma inställningar som POST /api/3d/peel): dagens djupbild
och den avskalade bilden med spår (rostrött) och gropar (grått) vid reglaget 0 mm, plus antal spår och gropar vid
−0,5, 0, +0,5 och +1 mm. Normal och upp-riktning ur djupbildscachen (samma vy som protokollmätningen). En process per
skanning (minnet). Skriver <stem>.png (och <stem>_en.png med engelsk text) och <stem>.json här.
    PYTHONPATH=. .venv/bin/python utdata/skala_av/prova.py sodermanland So_206_thin03_closed_holes"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
DEPTH = "/Volumes/2TB/cache/runmodell/djup"
OFFSETS = (-0.5, 0.0, 0.5, 1.0)
RUST, SLATE = np.array([0xb7, 0x41, 0x0e]) / 255, np.array([0x94, 0xa3, 0xb8]) / 255


def main(series: str, stem: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import trimesh

    from scripts.download_open_scans import local_path
    from src import peel as P
    from src import scan_sources
    from src.groove_export import relief_images
    from src.stone_report import Surface

    meta = json.load(open(os.path.join(DEPTH, series, stem + ".json"), encoding="utf-8"))
    path = local_path(series, meta["file"])
    if not path:
        raise SystemExit(f"skanningen saknas: {meta['file']}")
    t0 = time.time()
    mesh = trimesh.load(path, force="mesh")
    mesh.apply_translation(-(mesh.bounds[0] + mesh.bounds[1]) / 2.0)  # centred as the app does on upload
    t_load = time.time() - t0
    surf = Surface(mesh, meta["normal"], meta.get("up"), max_px=2400)
    del mesh
    t1 = time.time()
    pe = P.Peel(surf.H, surf.region, surf.res)
    t_peel = time.time() - t1
    layers = {}
    for off in OFFSETS:
        L = pe.layer(off)
        kinds = [c["kind"] for c in L["components"]]
        layers[off] = {"spar": kinds.count("spar"), "grop": kinds.count("grop"),
                       "spar_area_mm2": round(sum(c["area_mm2"] for c in L["components"] if c["kind"] == "spar")),
                       "left_share": round(float((L["labels"] > 0).sum() / max(1, pe.use.sum())), 4)}
    L = pe.layer(0.0)
    kind = np.array([0] + [1 if c["kind"] == "spar" else 2 for c in L["components"]])[L["labels"]]
    rgb = np.dstack([np.nan_to_num(P.background(L, surf.region), nan=1.0)] * 3)
    for code, col, a in ((1, RUST, 0.85), (2, SLATE, 0.6)):
        m = kind == code
        rgb[m] = (1 - a) * rgb[m] + a * col
    today = np.nan_to_num(relief_images(surf)["depth_img"], nan=1.0)
    ident = scan_sources.identify(os.path.basename(path), None, None, os.path.getsize(path))
    ds = (ident or {}).get("dataset") or {}
    # the person who scanned and their institution (scanner/institution), not the dataset's creators
    who = ", ".join(x for x in (ds.get("scanner") or ds.get("creator"), ds.get("institution")) if x)
    credit = (f"Skanning: {who}, {ds.get('license', '?')}, doi:{ds.get('doi', '?')}") if ds else "Skanning: källa okänd"
    h, w = kind.shape
    lv = pe.level_range()
    for en in (False, True):
        fig, ax = plt.subplots(2, 1, figsize=(14, 2 * 14 * h / w + 1.2))
        ax[0].imshow(today, cmap="gray", origin="lower", vmin=0, vmax=1)
        ax[1].imshow(rgb, origin="lower")
        if en:
            ax[0].set_title(f"{meta.get('signum')} – depth below the stone surface (today's image)", fontsize=14)
            ax[1].set_title(f"Peel away the weathering, slider 0 mm (weathering level {lv[0]:.1f}–{lv[2]:.1f} mm): "
                            f"{layers[0.0]['spar']} grooves (rust), {layers[0.0]['grop']} pits (grey)", fontsize=14)
            foot = credit.replace("Skanning:", "Scan:") + ". Image: Vitki."
        else:
            ax[0].set_title(f"{meta.get('signum')} – djup under stenytan (dagens bild)", fontsize=14)
            ax[1].set_title(f"Skala av vittringen, reglaget 0 mm (vittringsnivå {lv[0]:.1f}–{lv[2]:.1f} mm): "
                            f"{layers[0.0]['spar']} spår (rostrött), {layers[0.0]['grop']} gropar (grått)".replace(".", ","),
                            fontsize=14)
            foot = credit + ". Bild: Vitki."
        for a in ax:
            a.axis("off")
        fig.text(0.01, 0.005, foot, fontsize=9, color="#475569")
        plt.tight_layout(rect=(0, 0.02, 1, 1))
        plt.savefig(os.path.join(HERE, stem + ("_en" if en else "") + ".png"), dpi=70)
        plt.close(fig)
    out = {"series": series, "stem": stem, "signum": meta.get("signum"), "file": meta["file"], "credit": credit,
           "resolution_mm": round(float(surf.res), 3), "grid": [int(h), int(w)],
           "level_mm": {"min": round(lv[0], 2), "median": round(lv[1], 2), "max": round(lv[2], 2)},
           "layers": {str(k): v for k, v in layers.items()},
           "seconds": {"load": round(t_load, 1), "peel": round(t_peel, 1), "total": round(time.time() - t0, 1)}}
    json.dump(out, open(os.path.join(HERE, stem + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("signum", "resolution_mm", "level_mm")}, ensure_ascii=False), out["layers"]["0.0"], out["seconds"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
