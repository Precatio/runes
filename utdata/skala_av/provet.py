"""Provet i analysplaner/2026-11-07-skala-av-provet.md (sha 380fccf4) för en skanningsfil: precision, slumpnivå, lyft och
täckning i Viktors granskade runslingor för A (dagens djupbild, gemensam gräns vald så att lika stor andel av ytan visas
som i B), B (avskalat, reglaget 0 mm) och C (avskalat, bara spår). En process per fil (minnet). Skriver provet/<stem>.json.
    PYTHONPATH=. .venv/bin/python utdata/skala_av/provet.py sodermanland So_206_thin03_closed_holes"""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
DEPTH = "/Volumes/2TB/cache/runmodell/djup"


def measures(shown, band, use, base_n):
    s = shown & use
    n, hit = int(s.sum()), int((s & band).sum())
    prec = hit / n if n else None
    base = base_n / int(use.sum())
    return {"shown_share": n / int(use.sum()), "precision": prec, "lift": (prec / base) if prec is not None and base else None,
            "coverage": hit / base_n if base_n else None}


def main(series, stem):
    import trimesh

    from scripts.download_open_scans import local_path
    from src import peel as P
    from src.rune_bands import drawn_labels
    from src.stone_report import Surface

    t0 = time.time()
    meta = json.load(open(os.path.join(DEPTH, series, stem + ".json"), encoding="utf-8"))
    out = {"series": series, "stem": stem, "signum": meta.get("signum"), "plan_sha": "380fccf4"}
    path = local_path(series, meta["file"])
    if not path:
        out["skipped"] = "skanningen saknas"
    else:
        mesh = trimesh.load(path, force="mesh")
        mesh.apply_translation(-(mesh.bounds[0] + mesh.bounds[1]) / 2.0)
        surf = Surface(mesh, meta["normal"], meta.get("up"), max_px=2400)
        del mesh
        hf = surf.hf
        full = drawn_labels(meta["sha256"], hf)
        if full is None:
            out["skipped"] = "slingorna gick inte att föra över"
        else:
            rows, cols = np.where(hf.region)
            r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
            step = max(1, int(math.ceil(max(r1 - r0, c1 - c0) / 2400)))
            band = (full > 0)[r0:r1:step, c0:c1:step]
            assert band.shape == surf.H.shape, (band.shape, surf.H.shape)
            pe = P.Peel(surf.H, surf.region, surf.res)
            use = pe.use
            base_n = int((band & use).sum())
            if base_n == 0 or not use.any():
                out["skipped"] = "inga slingor inom ytan"
            else:
                L = pe.layer(0.0)
                B = L["labels"] > 0
                spar = np.zeros(len(L["components"]) + 1, bool)
                for c in L["components"]:
                    spar[c["id"]] = c["kind"] == "spar"
                C = spar[L["labels"]]
                depth_a = -surf.residual
                share_b = float((B & use).sum() / use.sum())
                t = float(np.quantile(depth_a[use], 1 - share_b))
                A = depth_a > t
                # Tillägg utöver planen (deklarerat i provet.md, beskrivande): A med lika stor visad andel som C
                share_c = float((C & use).sum() / use.sum())
                t_c = float(np.quantile(depth_a[use], 1 - share_c))
                out.update({"resolution_mm": round(float(surf.res), 3), "band_share": base_n / int(use.sum()),
                            "threshold_a_mm": round(t, 3), "A": measures(A, band, use, base_n),
                            "B": measures(B, band, use, base_n), "C": measures(C, band, use, base_n),
                            "A_at_C": measures(depth_a > t_c, band, use, base_n)})
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.join(HERE, "provet"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "provet", stem + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    brief = {k: (round(out[k]["lift"], 2) if out.get(k) and out[k]["lift"] else None) for k in "ABC"}
    print(stem, out.get("skipped") or brief, out["seconds"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
