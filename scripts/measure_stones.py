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
    """"So 131_…" -> "Sö 131", "So 137A_…" -> "Sö 137A", "So Fv1948_282_…" -> "Sö Fv1948;282"."""
    name = os.path.basename(path)
    m = re.match(r"([A-Za-zÅÄÖåäö]{1,3})[ _]?Fv(\d{4})_(\d+)", name)
    if m:
        return f"{PROVINCES.get(m.group(1), m.group(1))} Fv{m.group(2)};{m.group(3)}"
    m = re.match(r"([A-Za-zÅÄÖåäö]{1,3})[ _]?(\d+[A-Za-z]?)(?=[_ .]|$)", name)
    if not m:
        raise ValueError(f"Inget signum i filnamnet: {path}")
    return f"{PROVINCES.get(m.group(1), m.group(1))} {m.group(2)}"


def measure(path: str, api: str, sensitivity: float, resolution: float | None = None,
            harmonize: float | None = None) -> dict:
    with open(path, "rb") as fh:
        info = requests.post(f"{api}/api/3d/upload", files={"file": (os.path.basename(path), fh)}, timeout=3600).json()
    mid = info["mesh_id"]
    relief = requests.post(f"{api}/api/3d/render_relief", data={"mesh_id": mid}, timeout=1800).json()
    n = relief["normal"]
    d = requests.post(f"{api}/api/3d/auto_analyze", data={"mesh_id": mid, "normal_x": n[0], "normal_y": n[1],
                      "normal_z": n[2], "sensitivity": sensitivity, "meta_stone": "", "meta_weathering": ""}
                      | ({"resolution_mm": resolution} if resolution else {}) | ({"harmonize_mm": harmonize} if harmonize else {}),
                      timeout=3600).json()
    acc = [x for x in d["slices"] if x["accepted"]]
    return {"file": os.path.basename(path), "sha256": (d["provenance"].get("mesh") or {}).get("sha256"),
            "summary": d["summary"], "counts": d["counts"], "parameters": d["parameters"],
            "means": {m: d["summary"][m]["mean"] for m in METRICS},
            "slices": [{m: x[m] for m in METRICS} | {"position_mm": x["position_mm"]} for x in acc],
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
    for path in a.files:
        signum = signum_from(path)
        dest = os.path.join(a.out, f"{signum.replace(' ', '_')}.json")
        if os.path.exists(dest):
            print("finns", signum)
            continue
        print("mäter", signum, flush=True)
        res = {"signum": signum, **measure(path, a.api, a.sensitivity, a.resolution, a.harmonize)}
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False)
        print(f"  {signum}: {res['counts']['accepted']} tvärsnitt, V {res['means']['apex_vinkel_deg']:.1f}°", flush=True)


if __name__ == "__main__":
    main()
