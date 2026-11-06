"""Hur träffsäker är runigenkänningen? Utvärdering mot handmärkta facit (METHODS.md, 2c steg 5; IMPLEMENTATIONSPLAN 1.1).

Facit skapas i 3D-vyn i facit-läge: alla spår mäts, inget är förmärkt, och forskaren märker punkterna som runa,
ornamentik (slinglinje eller ornament) eller utesluten (spricka, vittring). Facitfilen innehåller bara positioner
och märkning, så samma facit kan användas när reglerna ändras: skriptet kör den automatiska analysen på nytt med
facitets parametrar, paras ihop varje facitpunkt med närmaste snitt (högst 2 mm) och jämför.

Facit av version 2 har dessutom Runa för runa (src/rune_links.py): ett klick per runa, kopplat till runan i Rundatas
translitterering. Då redovisas också, per sten, samlat och per bergart (Rundatas material):
  * runor hittade (recall): andel länkade runor med minst ett godkänt snitt som analysen kallar runa och som hör till
    runan, det vill säga ligger närmare dess klick än något annat klick och inom räckvidden;
  * mätt som är runor (precision): andel av analysens godkända runsnitt som hör till någon länkad runa;
  * en-till-en: andel länkade runor där alla runsnitt som hör till runan kommer från en och samma av analysens
    runor (rune_id), och den runans snitt inte hör till något annat klick.
Räckvidden är densamma som appens Markera runorna (web/src/lib/mesh.ts withMarkedRunes): MARK_REACH = 1,5 gånger
mediandistansen mellan två på varandra följande klick på stenen, mätt i stenytans plan. Den är bestämd innan
några facit finns och ändras inte efter resultatet.

Reglerna får inte justeras på facitstenarna. RULES_SHA256 är ett fingeravtryck av runigenkänningens regler
(rules_fingerprint: classify_strokes, runslingornas klassning, uppdelningen längs slingan, deras konstanter och
analysens standardvärden); tests/test_auto_grooves.py låser det, och skriptet skriver det i resultatet och varnar om
det inte stämmer. Ändras reglerna ändras fingeravtrycket: då skrivs en ny låsning med datum och skäl, och facit som
redan utvärderats redovisas som utvecklingsstenar för den nya versionen.

    .venv/bin/python -m scripts.evaluate_rune_detection utdata/facit/*.json --out utdata/rune_facit

Skanningen hittas via filnamnet i facitet (i skanningar/ eller projektroten) och kontrolleras mot dess SHA-256.
Utvecklingsstenar (de reglerna justerades på) redovisas för sig: --dev "Sö 113,Sö 128".
"""
import argparse
import hashlib
import inspect
import json
import os

import numpy as np
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATCH_MM = 2.0
MARK_REACH = 1.5  # as web/src/lib/mesh.ts MARK_REACH: decided before any facit existed
# The fingerprint of the rune-detection rules when the facit evaluation was locked (2026-11-06); see rules_fingerprint
RULES_SHA256 = "2aa957fd68c455ffcfd978e6cc9893ed57f61f6a0b0822f500804efed1ece9c0"


def rules_fingerprint() -> str:
    """SHA-256 of the rune-detection rules: the source of the functions that decide what is a rune (stroke
    classification, band classification, the grouping along the band), their module constants and the analysis'
    default parameters. Formatting changes to these functions change it too: a re-lock is then a conscious step."""
    from src import auto_grooves, rune_bands, staveless
    parts = [inspect.getsource(f) for f in (auto_grooves.classify_strokes, rune_bands.classify, rune_bands.band_field,
                                            rune_bands.bands_for, staveless.band_coordinate, staveless.group_runes)]
    # numbers only: the modules' paths (ROOT, MODEL_PATH …) differ between machines
    consts = {m.__name__: {k: v for k, v in vars(m).items() if k.isupper() and isinstance(v, (int, float, tuple))
                           and not isinstance(v, bool)}
              for m in (rune_bands, staveless)}
    parts.append(json.dumps(consts, sort_keys=True, default=str))
    sig = inspect.signature(auto_grooves.analyze_grooves)
    parts.append(json.dumps({k: p.default for k, p in sig.parameters.items()
                             if p.default is not inspect.Parameter.empty and isinstance(p.default, (int, float, str, bool, type(None)))},
                            sort_keys=True))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def find_scan(mesh: dict, folders=()) -> str:
    name = mesh.get("filename") or ""
    for folder in (*folders, os.path.join(ROOT, "skanningar"), ROOT):
        path = os.path.join(folder, name)
        if name and os.path.exists(path):
            return path
    raise FileNotFoundError(f"Skanningen {name!r} finns inte i skanningar/ eller projektroten.")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_like_app(path: str):
    """Läser in skanningen som appen gör (api/routers/threed.py, _load_upload): facitets koordinater gäller den
    centrerade modellen."""
    import trimesh

    mesh = trimesh.load(path, force="mesh")
    mesh.apply_translation(-(mesh.bounds[0] + mesh.bounds[1]) / 2.0)
    return mesh


def _plane(P: np.ndarray, normal) -> np.ndarray:
    """Points projected onto the stone plane (2D coordinates along u and v of the analysis normal)."""
    from src.auto_grooves import basis
    u, v, _ = basis(normal)
    return np.column_stack([P @ u, P @ v])


def link_metrics(link_pts: np.ndarray, slices: list[dict], normal, reach_factor: float = MARK_REACH) -> dict:
    """The rune-link measures for one stone. link_pts: the linked runes' 3D points (one row per click, reading order);
    slices: the analysis' slices (accepted ones with a point, feature and rune_id are used); normal: the stone plane.
    A rune slice belongs to the nearest click when it lies within reach = reach_factor × the median distance between
    consecutive clicks (in the plane)."""
    L = _plane(np.asarray(link_pts, float).reshape(-1, 3), normal)
    rs = [s for s in slices if s.get("accepted") and s.get("point") is not None and s.get("feature") == "rune"]
    n_links = len(L)
    out = {"n_links": n_links, "n_rune_slices": len(rs)}
    if n_links == 0:
        return {**out, "reach_mm": None, "found": 0, "recall": None, "assigned": 0, "precision": None,
                "one_to_one": 0, "one_to_one_share": None}
    gaps = np.linalg.norm(np.diff(L, axis=0), axis=1)
    reach = reach_factor * float(np.median(gaps)) if len(gaps) else float("inf")
    owner = np.full(len(rs), -1)
    if rs:
        S = _plane(np.array([s["point"] for s in rs], float), normal)
        d, j = cKDTree(L).query(S)
        owner = np.where(d <= reach, j, -1)
    found = sorted({int(k) for k in owner if k >= 0})
    groups_of: dict[int, set] = {}
    links_of_group: dict[int, set] = {}
    for s, k in zip(rs, owner, strict=True):
        if k < 0:
            continue
        g = s.get("rune_id")
        groups_of.setdefault(int(k), set()).add(g)
        if g is not None:
            links_of_group.setdefault(g, set()).add(int(k))
    one = [k for k, gs in groups_of.items()
           if len(gs) == 1 and None not in gs and links_of_group.get(next(iter(gs))) == {k}]
    assigned = int((owner >= 0).sum())
    return {**out, "reach_mm": round(reach, 2), "found": len(found), "recall": len(found) / n_links,
            "assigned": assigned, "precision": assigned / len(rs) if rs else None,
            "one_to_one": len(one), "one_to_one_share": len(one) / n_links}


def _links_3d(facit: dict, result: dict, mesh) -> tuple[np.ndarray, dict]:
    """The linked clicks as 3D points: the facit's point_mm, recomputed from image_xy with the re-run analysis' frame
    when a point is missing (and compared where both exist)."""
    from src import rune_links
    links = facit.get("rune_links") or []
    fr = rune_links.frame_from_result(result)
    same_image = (facit.get("image_width"), facit.get("image_height")) == (result.get("image_width"), result.get("image_height"))
    recomputed = (rune_links.anchors(fr, [ln["image_xy"] for ln in links], mesh_vertices=mesh.vertices,
                                     slices=result["slices"]) if fr is not None and same_image and links else [None] * len(links))
    pts, diffs = [], []
    for ln, a in zip(links, recomputed, strict=True):
        p = ln.get("point_mm")
        q = a["point_mm"] if a else None
        if p is not None and q is not None:
            diffs.append(float(np.linalg.norm(np.subtract(p, q))))
        pts.append(p if p is not None else q)
    kept = np.array([p for p in pts if p is not None], float).reshape(-1, 3)
    return kept, {"n_without_point": sum(p is None for p in pts), "same_image": same_image,
                  "max_recomputed_diff_mm": round(max(diffs), 2) if diffs else None}


def evaluate(facit: dict, folders=()) -> dict:
    from src.auto_grooves import analyze_grooves
    from src.rune_links import read_facit

    facit = read_facit(facit)
    path = find_scan(facit.get("mesh") or {}, folders)
    want = (facit.get("mesh") or {}).get("sha256")
    if want and sha256(path) != want:
        raise ValueError(f"{path}: kontrollsumman stämmer inte med facitet.")
    par = facit["parameters"]
    mesh = load_like_app(path)
    r = analyze_grooves(mesh, par["normal"], up=par.get("up"),
                        spacing_mm=par.get("spacing_mm", 3.0), sensitivity=par.get("sensitivity", 3.0),
                        max_halfwidth_mm=par.get("max_halfwidth_mm", 8.0),
                        resolution_mm=par["resolution_mm"] if par.get("fixed_resolution") else None,
                        harmonize_mm=par.get("harmonize_mm"), runes_only=False, sha256=want)
    slices = [s for s in r["slices"] if s["accepted"] and s.get("point")]
    tree = cKDTree(np.array([s["point"] for s in slices]))
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "unmatched": 0}
    by_label: dict[str, dict[str, int]] = {}
    for lab in facit["labels"]:
        if lab["label"] not in ("rune", "ornament", "excluded"):
            continue
        dist, j = tree.query(lab["point"])
        if dist > MATCH_MM:
            counts["unmatched"] += 1
            continue
        truth, pred = lab["label"] == "rune", slices[j].get("feature") == "rune"
        counts[{(True, True): "tp", (False, True): "fp", (True, False): "fn", (False, False): "tn"}[(truth, pred)]] += 1
        b = by_label.setdefault(lab["label"], {})
        feat = slices[j].get("feature") or "?"
        b[feat] = b.get(feat, 0) + 1
    out = {"signum": facit.get("signum"), "labeller": facit.get("labeller"), "facit_version": facit["version"],
           **counts, **scores(counts), "by_label": by_label}
    if facit["rune_links"]:
        pts, check = _links_3d(facit, r, mesh)
        out["links"] = {**link_metrics(pts, r["slices"], par["normal"]), **check,
                        "n_skipped": len(facit.get("skipped_tokens") or []),
                        "n_bind": sum(1 for ln in facit["rune_links"] if len(ln["tokens"]) == 2)}
    return out


def scores(c: dict) -> dict:
    p = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else None
    rec = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else None
    f1 = 2 * p * rec / (p + rec) if p and rec else None
    return {"precision": p, "recall": rec, "f1": f1}


def pooled_links(rows: list[dict]) -> dict | None:
    """The rune-link measures pooled over stones (sums of counts, not means of shares)."""
    ls = [r["links"] for r in rows if r.get("links")]
    if not ls:
        return None
    n, rs = sum(x["n_links"] for x in ls), sum(x["n_rune_slices"] for x in ls)
    return {"stones": len(ls), "n_links": n, "n_rune_slices": rs,
            "recall": sum(x["found"] for x in ls) / n if n else None,
            "precision": sum(x["assigned"] for x in ls) / rs if rs else None,
            "one_to_one_share": sum(x["one_to_one"] for x in ls) / n if n else None}


def material_of(signum: str | None) -> str:
    try:
        from api.rundata import material_group
        from src.rune_links import rundata_record
        rec, _ = rundata_record(signum)
        return material_group(rec) if rec else ""
    except Exception:  # noqa: BLE001 - the rock type is extra information
        return ""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("facit", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dev", default="Sö 113,Sö 128", help="stenar som reglerna justerades på (redovisas för sig)")
    ap.add_argument("--scans", action="append", default=[], help="fler mappar att leta efter skanningar i")
    a = ap.parse_args(argv)
    fingerprint = rules_fingerprint()
    if fingerprint != RULES_SHA256:
        print(f"VARNING: runigenkänningens regler har ändrats sedan låsningen ({fingerprint[:12]} ≠ {RULES_SHA256[:12]}). "
              "Redovisa resultatet som gällande de nya reglerna, med datum och skäl för ändringen.")
    dev = {x.strip() for x in a.dev.split(",") if x.strip()}
    os.makedirs(a.out, exist_ok=True)
    rows = []
    fmt = lambda v: "–" if v is None else f"{v:.2f}"  # noqa: E731
    for f in a.facit:
        res = evaluate(json.load(open(f, encoding="utf-8")), a.scans)
        res["development"] = res["signum"] in dev
        res["material"] = material_of(res["signum"])
        res["file"] = os.path.basename(f)
        rows.append(res)
        print(f"{res['signum']:16s} precision {fmt(res['precision'])}  träffsäkerhet (recall) {fmt(res['recall'])}  "
              f"F1 {fmt(res['f1'])}  (tp {res['tp']}, fp {res['fp']}, fn {res['fn']}, tn {res['tn']}, "
              f"oparade {res['unmatched']}){'  [utvecklingssten]' if res['development'] else ''}")
        if res.get("links"):
            x = res["links"]
            print(f"{'':16s} runor hittade {fmt(x['recall'])} ({x['found']} av {x['n_links']})  mätt som är runor "
                  f"{fmt(x['precision'])}  en-till-en {fmt(x['one_to_one_share'])}  räckvidd {x['reach_mm']} mm")
    summary = {"rules_sha256": fingerprint, "rules_locked": RULES_SHA256, "rules_match": fingerprint == RULES_SHA256,
               "mark_reach": MARK_REACH, "groups": {}}
    for name, group in (("Utvärderingsstenar", [r for r in rows if not r["development"]]),
                        ("Utvecklingsstenar", [r for r in rows if r["development"]])):
        if not group:
            continue
        tot = {k: sum(r[k] for r in group) for k in ("tp", "fp", "fn", "tn")}
        s = scores(tot)
        print(f"{name} ({len(group)}): precision {s['precision'] or 0:.2f}, recall {s['recall'] or 0:.2f}, F1 {s['f1'] or 0:.2f}")
        g = {"stones": len(group), **tot, **s, "links": pooled_links(group), "by_material": {}}
        if g["links"]:
            x = g["links"]
            print(f"  runa för runa ({x['stones']} stenar, {x['n_links']} runor): hittade {fmt(x['recall'])}, "
                  f"mätt som är runor {fmt(x['precision'])}, en-till-en {fmt(x['one_to_one_share'])}")
        for mat in sorted({r["material"] for r in group}):
            sub = [r for r in group if r["material"] == mat]
            pl = pooled_links(sub)
            g["by_material"][mat or "okänd"] = {"stones": len(sub), "links": pl}
            if pl:
                print(f"  {mat or 'okänd bergart'} ({len(sub)}): hittade {fmt(pl['recall'])}, mätt som är runor "
                      f"{fmt(pl['precision'])}, en-till-en {fmt(pl['one_to_one_share'])}")
        summary["groups"][name] = g
    json.dump(rows, open(os.path.join(a.out, "evaluation.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(summary, open(os.path.join(a.out, "summary.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
