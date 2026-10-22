"""Mäter huggspåren på flera skanningar med samma automatiska spåranalys som stenanalysen och sparar medelvärden
och tvärsnitt per sten – underlag för att jämföra huggteknik (r/technique.R). Analysmotorn måste köras.

    .venv/bin/python -m scripts.measure_stones skanningar/*.stl --out utdata/referenser --sensitivity 3

Signum läses ur filnamnet ("So 131_…" -> "Sö 131"). Redan uppmätta stenar hoppas över.
"""
import argparse
import json
import os
import re

import requests

METRICS = ["apex_vinkel_deg", "asymmetri_deg", "spårdjup_mm", "spårbredd_mm", "djup_bredd_kvot", "bottenradie_mm", "ytråhet_mm"]
PROVINCES = {"So": "Sö", "Og": "Ög", "Ol": "Öl", "Na": "Nä", "An": "Ån"}


def signum_from(path: str) -> str:
    """"So 131_…" -> "Sö 131", "So 137A_…" -> "Sö 137A", "So Fv1948_282_…" -> "Sö Fv1948;282",
    "Og Hov 14_22_…" -> "Ög Hov14;22" (signum efter ort och sida i en sockenutgåva)."""
    name = os.path.basename(path)
    m = re.match(r"([A-Za-zÅÄÖåäö]{1,3})[ _]?Fv(\d{4})_(\d+)", name)
    if m:
        return f"{PROVINCES.get(m.group(1), m.group(1))} Fv{m.group(2)};{m.group(3)}"
    m = re.match(r"([A-Za-zÅÄÖåäö]{1,3}) ([A-ZÅÄÖ][a-zåäö]+) ?(\d+)_(\d+)(?=[_ .]|$)", name)
    if m:
        return f"{PROVINCES.get(m.group(1), m.group(1))} {m.group(2)}{m.group(3)};{m.group(4)}"
    m = re.match(r"([A-Za-zÅÄÖåäö]{1,3})[ _]?(\d+[A-Za-z]?)(?=[_ .]|$)", name)
    if not m:
        raise ValueError(f"Inget signum i filnamnet: {path}")
    return f"{PROVINCES.get(m.group(1), m.group(1))} {m.group(2)}"


def measure(path: str, api: str, sensitivity: float, resolution: float | None = None,
            harmonize: float | None = None) -> dict:
    with open(path, "rb") as fh:
        r = requests.post(f"{api}/api/3d/upload", files={"file": (os.path.basename(path), fh)}, timeout=3600)
    if not r.ok:
        raise RuntimeError(f"uppladdningen misslyckades ({r.status_code}): {r.text[:200]}")
    info = r.json()
    mid = info["mesh_id"]
    relief = requests.post(f"{api}/api/3d/render_relief", data={"mesh_id": mid}, timeout=1800).json()
    n = relief["normal"]
    d = requests.post(f"{api}/api/3d/auto_analyze", data={"mesh_id": mid, "normal_x": n[0], "normal_y": n[1],
                      "normal_z": n[2], "sensitivity": sensitivity, "meta_stone": "", "meta_weathering": ""}
                      | ({"resolution_mm": resolution} if resolution else {}) | ({"harmonize_mm": harmonize} if harmonize else {}),
                      timeout=3600).json()
    if "summary" not in d:  # the engine found nothing to measure (a small fragment) or failed
        raise RuntimeError(f"ingen mätning: {str(d.get('detail') or d)[:200]}")
    acc = [x for x in d["slices"] if x["accepted"]]
    return {"file": os.path.basename(path), "sha256": (d["provenance"].get("mesh") or {}).get("sha256"),
            "summary": d["summary"], "counts": d["counts"], "parameters": d["parameters"],
            "means": {m: d["summary"][m]["mean"] for m in METRICS},
            "slices": [{m: x[m] for m in METRICS} | {"position_mm": x["position_mm"], "rune_id": x.get("rune_id")} for x in acc],
            "relief_png": relief["relief"], "review_png": d["image_base64"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--api", default=os.environ.get("RUNFORSKNING_API", "http://localhost:8000"))
    ap.add_argument("--sensitivity", type=float, default=3)
    ap.add_argument("--resolution", type=float, help="fast rutnätsupplösning i mm (samma för alla stenar)")
    ap.add_argument("--harmonize", type=float, help="utjämna profilerna till denna effektiva upplösning i mm")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    signa = [signum_from(p) for p in a.files]
    seen: dict[str, int] = {}
    for path, signum in zip(a.files, signa, strict=False):
        # a stone in several files (M 14_020, M 14_040) gets one result per file: M_14_1.json, M_14_2.json
        seen[signum] = seen.get(signum, 0) + 1
        part = f"_{seen[signum]}" if signa.count(signum) > 1 else ""
        dest = os.path.join(a.out, f"{signum.replace(' ', '_')}{part}.json")
        if os.path.exists(dest):
            print("finns", signum)
            continue
        print("mäter", signum, flush=True)
        try:
            res = {"signum": signum, "part": part.lstrip("_") or None,
                   **measure(path, a.api, a.sensitivity, a.resolution, a.harmonize)}
        except Exception as e:  # noqa: BLE001 - one stone that cannot be measured must not stop the series
            print(f"  {signum}: misslyckades – {e}", flush=True)
            continue
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False)
        print(f"  {signum}: {res['counts']['accepted']} tvärsnitt, V {res['means']['apex_vinkel_deg']:.1f}°", flush=True)


if __name__ == "__main__":
    main()
