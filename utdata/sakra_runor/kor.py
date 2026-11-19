"""Mätningarna till den låsta planen analysplaner/2026-11-19-sakra-runor-skanningskvalitet.md (sha256 fb4a444a…):
Kitzler Åhfeldts skanningar av Södermanlands runstenar, mätta om med groove-7 i fyra varianter, en sten i taget.

  D0 originalet · D1 brus längs hörnpunkternas normaler (σ = 0,15 mm) · D2 analysens rutnät 1,2 mm · D3 D1 och D2

Samma väg som /api/3d/auto_analyze: meshen laddas med trimesh (force="mesh") och centreras på sin omslutande lådas mitt
som vid uppladdningen; analysen får filens SHA-256, så att de ritade slingorna hittas, och normalen, upp-riktningen och
övriga parametrar ur den sparade groove-7-mätningen i utdata/Rak/referenser_g7/. Bruset läggs på efter centreringen,
med slumpfröet int(sha[:8], 16) ur planens kontrollsumma (samma brus för D1 och D3, och samma frö för varje sten).

Tilläggsplan 1 (analysplaner/2026-11-19-sakra-runor-tillagg-1-annan-kalla.md, sha256 e7dd8b3d…), --kalla zedig: Henrik
Zedigs skanningar i skanningar/medelpad och skanningar/halsingland, bara filer med granskade ritade slingor. D0 mäts med
appens förval (Vitki-protokollet, stavlöst läge som appen slår på det ur Rundatas runtyper) och vyn rakt mot den ristade
sidan: samma vy som appen väljer för de öppna skanningarna (protokollvyn, djupbildens normal och upp-riktning, som
slingorna är ritade i; api/routers/threed._default_view). Bruset har fröet ur tilläggets kontrollsumma. Skriver
utdata/sakra_runor/matningar_zedig/<fil>_<D>.json (en fil per skanning; flera filer kan höra till samma sten).
    .venv/bin/python utdata/sakra_runor/kor.py --kalla zedig

Varje sten mäts i en egen process (minnet: en sten åt gången), och det som redan finns hoppas över.
    .venv/bin/python utdata/sakra_runor/kor.py                 # alla stenar med ritade, granskade slingor
    .venv/bin/python utdata/sakra_runor/kor.py --sten "Sö 112"  # en sten (alla fyra varianter)
    .venv/bin/python utdata/sakra_runor/kor.py --sten "Sö 112" --bara D0
Skriver utdata/sakra_runor/matningar/<Sö_112>_<D>.json."""
from __future__ import annotations

import glob
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-19-sakra-runor-skanningskvalitet.md")
SHA = hashlib.sha256(open(PLAN, "rb").read()).hexdigest()
assert SHA.startswith("fb4a444a"), SHA
SEED = int(SHA[:8], 16)
PLAN_Z = os.path.join(ROOT, "analysplaner", "2026-11-19-sakra-runor-tillagg-1-annan-kalla.md")
SHA_Z = hashlib.sha256(open(PLAN_Z, "rb").read()).hexdigest()
assert SHA_Z.startswith("e7dd8b3d"), SHA_Z
SEED_Z = int(SHA_Z[:8], 16)
ZEDIG_SERIES = ("medelpad", "halsingland")
OUT_Z = os.path.join(HERE, "matningar_zedig")
REF = os.path.join(ROOT, "utdata", "Rak", "referenser_g7")
OUT = os.path.join(HERE, "matningar")
NOISE_MM = 0.15
COARSE_MM = 1.2
VARIANTS = ("D0", "D1", "D2", "D3")
METRICS = ("apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm")


def references() -> dict[str, dict]:
    """The saved groove-7 measurements, by signum."""
    out = {}
    for f in sorted(glob.glob(os.path.join(REF, "Sö_*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        out[d["signum"]] = d
    return out


def scan_path(name: str) -> str:
    for folder in (os.path.join(ROOT, "skanningar"), ROOT):
        p = os.path.join(folder, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def has_checked_bands(sha256: str) -> bool:
    from src import rune_bands
    e = rune_bands.depth_image_entry(sha256)
    if e is None:
        return False
    bp = os.path.join(rune_bands.BAND_DIR, e[0], e[1] + ".json")
    if not os.path.exists(bp):
        return False
    b = json.load(open(bp, encoding="utf-8"))
    return b.get("status") == "granskad" and bool(b.get("bands"))


def out_path(signum: str, variant: str) -> str:
    return os.path.join(OUT, f"{signum.replace(' ', '_')}_{variant}.json")


def zedig_items() -> dict[str, dict]:
    """Zedig's scans with checked drawn bands, by depth-image stem: signum, scan path, SHA-256 and the protocol view."""
    from src import protocol as protocol_spec
    from src import rune_bands
    out = {}
    for ser in ZEDIG_SERIES:
        for bp in sorted(glob.glob(os.path.join(rune_bands.BAND_DIR, ser, "*.json"))):
            b = json.load(open(bp, encoding="utf-8"))
            if b.get("status") != "granskad" or not b.get("bands"):
                continue
            stem = os.path.basename(bp)[:-5]
            meta = json.load(open(os.path.join(rune_bands.DEPTH_DIR, ser, stem + ".json"), encoding="utf-8"))
            t = (meta.get("rune_types") or "").strip().lower()
            staveless = t.startswith("stavlös") and not any(x in t for x in ("kvist", "+", ",", " och "))  # lib/staveless.ts
            pp = protocol_spec.PARAMETERS
            out[stem] = {"signum": meta["signum"], "file": meta["file"], "series": ser, "sha256": meta["sha256"],
                         "path": os.path.join(ROOT, "skanningar", ser, meta["file"]),
                         "parameters": {"normal": meta["normal"], "up": meta.get("up"), "spacing_mm": pp["spacing_mm"],
                                        "sensitivity": pp["sensitivity"], "max_halfwidth_mm": pp["max_halfwidth_mm"],
                                        "resolution_mm": pp["resolution_mm"], "harmonize_mm": pp["harmonize_mm"],
                                        "staveless": staveless}}
    return out


def measure_stone(signum: str, only: list[str] | None = None, source: str = "kitzler"):
    import numpy as np
    import trimesh

    from api.config import METHOD_VERSION
    from api.routers.threed import _digests
    from src.auto_grooves import analyze_grooves
    from src.stats import summarize_by_rune, summarize_slices

    zedig = source == "zedig"
    ref = zedig_items()[signum] if zedig else references()[signum]
    dst = (lambda v: os.path.join(OUT_Z, f"{signum}_{v}.json")) if zedig else (lambda v: out_path(signum, v))
    seed = SEED_Z if zedig else SEED
    todo = [v for v in (only or VARIANTS) if not os.path.exists(dst(v))]
    if not todo:
        return
    path = ref["path"] if zedig else scan_path(ref["file"])
    digest, _, _ = _digests(path)
    assert digest == ref["sha256"], signum
    mesh = trimesh.load(path, force="mesh")
    centre = (mesh.bounds[0] + mesh.bounds[1]) / 2.0
    mesh.apply_translation(-centre)
    noisy = None
    if any(v in ("D1", "D3") for v in todo):
        rng = np.random.default_rng(seed)
        shift = rng.normal(0.0, NOISE_MM, len(mesh.vertices))
        noisy = trimesh.Trimesh(vertices=mesh.vertices + mesh.vertex_normals * shift[:, None], faces=mesh.faces,
                                process=False)
    p = ref["parameters"]
    for v in todo:
        t0 = time.time()
        r = analyze_grooves(noisy if v in ("D1", "D3") else mesh, p["normal"], up=p.get("up"),
                            spacing_mm=p["spacing_mm"], sensitivity=p["sensitivity"],
                            max_halfwidth_mm=p["max_halfwidth_mm"],
                            resolution_mm=COARSE_MM if v in ("D2", "D3") else p["resolution_mm"],
                            harmonize_mm=p.get("harmonize_mm") or None, runes_only=True, measure="runes",
                            bands=True, sha256=digest, staveless=bool(p.get("staveless")))
        acc = [s for s in r["slices"] if s["accepted"]]
        keep = ("rune_id", "position_mm", "img_x", "img_y", *METRICS, "asymmetri_deg", "bottenradie_mm", "fit_r2")
        out = {"signum": ref["signum"] if zedig else signum, "file": ref["file"], "sha256": digest, "variant": v,
               "source": source, **({"stem": signum, "series": ref["series"]} if zedig else {}),
               "plan_sha256": SHA_Z if zedig else SHA,
               "method_version": METHOD_VERSION, "seconds": round(time.time() - t0),
               "noise_mm": NOISE_MM if v in ("D1", "D3") else 0.0, "seed": seed if v in ("D1", "D3") else None,
               "parameters": r["parameters"], "counts": r["counts"], "bands": r.get("bands"),
               "slices": [{k: s.get(k) for k in keep if k in s} for s in acc]}
        if acc:
            out["summary"] = summarize_slices(acc)
            out["rune_summary"] = summarize_by_rune(acc)
        json.dump(out, open(dst(v), "w", encoding="utf-8"), ensure_ascii=False)
        print(f"{signum} {v}: {len(acc)} snitt, {(out.get('rune_summary') or {}).get('n_runes')} runor, "
              f"slingor {(r.get('bands') or {}).get('source')}, {out['seconds']} s", flush=True)


def run_all():
    refs = references()
    stones = [s for s, d in refs.items() if has_checked_bands(d["sha256"])]
    skipped = sorted(set(refs) - set(stones))
    print(f"{len(stones)} stenar med granskade slingor; utan: {', '.join(skipped) or 'inga'}", flush=True)
    for i, s in enumerate(stones, 1):
        if all(os.path.exists(out_path(s, v)) for v in VARIANTS):
            continue
        print(f"[{i}/{len(stones)}] {s}", flush=True)
        subprocess.run([sys.executable, os.path.abspath(__file__), "--sten", s], cwd=ROOT,
                       env={**os.environ, "PYTHONPATH": ROOT}, check=False)
    print("klart", flush=True)


def run_zedig():
    items = zedig_items()
    print(f"{len(items)} skanningar av Zedig med granskade slingor "
          f"({', '.join(f'{s}: {sum(1 for i in items.values() if i['series'] == s)}' for s in ZEDIG_SERIES)})", flush=True)
    for i, stem in enumerate(items, 1):
        if all(os.path.exists(os.path.join(OUT_Z, f"{stem}_{v}.json")) for v in VARIANTS):
            continue
        print(f"[{i}/{len(items)}] {stem}", flush=True)
        subprocess.run([sys.executable, os.path.abspath(__file__), "--sten", stem, "--kalla", "zedig"], cwd=ROOT,
                       env={**os.environ, "PYTHONPATH": ROOT}, check=False)
    print("klart", flush=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(OUT_Z, exist_ok=True)
    source = sys.argv[sys.argv.index("--kalla") + 1] if "--kalla" in sys.argv else "kitzler"
    if "--sten" in sys.argv:
        only = sys.argv[sys.argv.index("--bara") + 1].split(",") if "--bara" in sys.argv else None
        measure_stone(sys.argv[sys.argv.index("--sten") + 1], only, source)
    elif source == "zedig":
        run_zedig()
    else:
        run_all()
