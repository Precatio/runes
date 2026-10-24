"""Automatisk körning: alla nedladdade öppna skanningar mäts, får syntes och attribuering och sparas som projekt.

Samma arbetsgång som sidan Stenanalys (upplänkning, spåranalys med Vitki-protokollet, syntes mot den delade
mätkorpusen), men utan AI-text, utan rapport och utan R, en sten i taget (minnet räcker inte till fler samtidigt):

  1. mät   – varje fil i data/scan_files.json som finns på disken mäts en gång; resultatet sparas i
             utdata/automatisk_korning/<serie>/<fil>.json (samma form som utdata/Rak/referenser_g5), och körningen
             kan avbrytas och fortsätta. Södermanlands stenar får samma normal som referensmätningarna i korpusen;
             övriga får stenens tunnaste riktning, som sidan använder när ingen normal anges.
  2. korpus – Medelpads runstenar läggs in i den delade mätkorpusen (Firestore `corpus`), med Henrik Zedigs
             skanningar krediterade som METHODS 17 kräver. Södermanland finns där redan (scripts/corpus_seed_ka.py).
  3. syntes – varje sten får syntes och attribuering mot korpusen (use_ai = false: texterna är framräknade).
  4. projekt – varje sten sparas som projekt hos grundaren, users/<uid>/projects/auto_<signum>, med fältet autoRun
             (etiketten "automatisk körning"), så att appen kan skilja dem från egna projekt och aldrig lägger egna
             analyser i dem. Gravhällar och andra föremål än runstenar märks separat och kommer inte in i korpusen
             (METHODS 17, runstenar som standard).

Kräver att analysmotorn körs (uvicorn api.main:app på port 8000).
    .venv/bin/python -m scripts.batch_scans                     # mäter det som saknas, visar resten
    .venv/bin/python -m scripts.batch_scans --skriv             # och skriver korpus och projekt till Firestore
    .venv/bin/python -m scripts.batch_scans --serier medelpad   # bara vissa serier (kommaseparerade)
    .venv/bin/python -m scripts.batch_scans --max-mb 500        # stora filer sist (kräver höjd MAX_MESH_UPLOAD_MB)
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import os
import re
import sys
import time

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from dotenv import dotenv_values  # noqa: E402

for f in (".env", "api/.env"):
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        for k, v in dotenv_values(p).items():
            os.environ.setdefault(k, v or "")

from api.config import APP_VERSION, METHOD_VERSION  # noqa: E402
from api.rundata import store  # noqa: E402
from scripts.corpus_seed_ka import FOUNDER_EMAIL, entry as corpus_entry  # noqa: E402
from scripts.download_open_scans import local_path  # noqa: E402
from src.scan_sources import DATASETS, file_credit_text, file_signa  # noqa: E402
from src.stats import METRICS  # noqa: E402

OUT = os.path.join(ROOT, "utdata", "automatisk_korning")
REF_G5 = os.path.join(ROOT, "utdata", "Rak", "referenser_g5")
ORDER = ["sodermanland", "medelpad", "gravmonument_og_sm", "asmund", "halsingland", "vastergotland"]
CORPUS_SERIES = {"medelpad"}  # the series this run adds to the shared corpus (Viktor 2026-10-24)
LABEL = "automatisk körning"
FIRESTORE_DOC_LIMIT = 900_000  # as web/src/lib/db.ts
BY_KEY = {ds["key"]: ds for ds in DATASETS}


def log(msg: str):
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def slug(text: str) -> str:
    return re.sub(r"[^\w]+", "_", text).strip("_")


def stone_type(rec: dict | None) -> str:
    """The app's rock types from Rundata's material ("ljusgrå granit" → Granit); Okänd when Rundata does not say."""
    m = ((rec or {}).get("material") or "").lower()
    for word, name in (("sandsten", "Sandsten"), ("kalksten", "Kalksten"), ("granit", "Granit"), ("gnejs", "Gnejs")):
        if word in m:
            return name
    return "Okänd"


def known_normals() -> dict[str, list[float]]:
    """The normals of the reference measurements already in the corpus, by file name (Södermanland)."""
    out = {}
    if os.path.isdir(REF_G5):
        for f in os.listdir(REF_G5):
            if f.endswith(".json"):
                d = json.load(open(os.path.join(REF_G5, f), encoding="utf-8"))
                n = (d.get("parameters") or {}).get("normal")
                if d.get("file") and n:
                    out[d["file"]] = n
    return out


def files(series: list[str]) -> list[tuple[str, dict, str]]:
    data = json.load(open(os.path.join(ROOT, "data", "scan_files.json"), encoding="utf-8"))["datasets"]
    out = []
    for key in series:
        for f in data.get(key, {}).get("files", []):
            path = local_path(key, f["name"])
            if f.get("sha256") and path:
                out.append((key, f, path))
    return out


def result_path(key: str, f: dict) -> str:
    return os.path.join(OUT, key, slug(os.path.splitext(f["name"])[0]) + ".json")


# ---- 1. measuring ---------------------------------------------------------------------------------------------------

def measure(api: str, key: str, f: dict, path: str, normals: dict) -> dict:
    s = store()
    signa = file_signa(f)
    rec = s.get(signa[0]) if signa else None
    stone = stone_type(rec)
    t0 = time.time()
    with open(path, "rb") as fh:
        r = requests.post(f"{api}/api/3d/upload", files={"file": (f["name"], fh)}, timeout=3600)
    r.raise_for_status()
    mid = r.json()["mesh_id"]
    normal, normal_source = normals.get(f["name"]), "referensmätningen i korpusen (utdata/Rak/referenser_g5)"
    if not normal:
        rel = requests.post(f"{api}/api/3d/render_relief", data={"mesh_id": mid}, timeout=1800)
        rel.raise_for_status()
        normal, normal_source = rel.json()["normal"], "stenens tunnaste riktning (uppskattad, som på sidan)"
    data = {"mesh_id": mid, "normal_x": normal[0], "normal_y": normal[1], "normal_z": normal[2], "sensitivity": 3,
            "meta_stone": stone, "meta_weathering": "Okänd", "runes_only": True, "protocol": True}
    d = requests.post(f"{api}/api/3d/auto_analyze", data=data, timeout=3600).json()
    base = {"signum": signa[0] if signa else None, "signa": signa, "file": f["name"], "sha256": f["sha256"],
            "series": key, "stone_type": stone, "object": (rec or {}).get("object"), "normal": normal,
            "normal_source": normal_source, "seconds": round(time.time() - t0)}
    if "summary" not in d:
        return {**base, "error": d.get("detail") or "inga godkända snitt"}
    acc = [x for x in d["slices"] if x["accepted"]]
    png = os.path.splitext(result_path(key, f))[0] + "_granskning.png"
    open(png, "wb").write(base64.b64decode(d["image_base64"].split(",", 1)[1]))
    return {**base, "summary": d["summary"], "counts": d["counts"], "parameters": d["parameters"],
            "protocol": (d.get("provenance") or {}).get("protocol"), "provenance": d["provenance"],
            "means": {m: d["summary"][m]["mean"] for m in METRICS}, "rune_summary": d.get("rune_summary"),
            "slices": [{**{m: x[m] for m in METRICS}, "position_mm": x["position_mm"], "fit_r2": x.get("fit_r2"),
                        "rune_id": x.get("rune_id"), "profile": x.get("profile"), "point": x.get("point"),
                        "direction": x.get("direction"), "up": x.get("up")} for x in acc],
            "review_png": os.path.relpath(png, ROOT)}


# ---- 2.–4. corpus, synthesis, projects ------------------------------------------------------------------------------

def is_runestone(d: dict) -> bool:
    """Runestones only by default (METHODS 17): grave slabs, the grave-monument series and stones without a Rundata
    record are kept apart."""
    return d["series"] != "gravmonument_og_sm" and d.get("object") == "runsten"


def corpus_rows(results: list[dict], uid: str, name: str, now: str) -> list[dict]:
    """One corpus entry per stone (the file with the most accepted slices), with the scanner credited."""
    best: dict[str, dict] = {}
    for d in results:
        if d["series"] in CORPUS_SERIES and is_runestone(d) and "error" not in d and d.get("signum"):
            if d["signum"] not in best or d["counts"]["accepted"] > best[d["signum"]]["counts"]["accepted"]:
                best[d["signum"]] = d
    rows = []
    for d in best.values():
        ds = BY_KEY[d["series"]]
        e = corpus_entry(d, uid, name, now)
        n_runes = (d.get("rune_summary") or {}).get("n_runes")
        n_all = len(d["slices"])
        e.update({
            "id": f"c_auto_{METHOD_VERSION}_{slug(d['signum'])}",
            "scanner": ds.get("scanned_by") or ds["creator"],
            "scan": {"scanned_by": ds.get("scanned_by") or ds["creator"], "url": ds["url"], "license": ds["license"],
                     "device": ds["device"], "citation": ds["citation"],
                     "resolution_mm": (d.get("parameters") or {}).get("mesh_point_spacing_mm")},
            "notes": (file_credit_text(ds, {"name": d["file"], "signum": d["signum"]}) + f" Mätt i Vitki med "
                      f"protokollet ({METHOD_VERSION}, bara runor): {n_all} snitt i {n_runes} igenkända runor"
                      + ("; 200 av snitten lagrade här, alla i utdata/automatisk_korning" if n_all > 200 else "")
                      + ". Inlagd av scripts/batch_scans.py (automatisk körning)."),
        })
        rows.append(e)
    return rows


def record(d: dict) -> dict:
    """The groove analysis as the app saves it (GrooveAnalysisRecord in web/src/lib/db.ts)."""
    return {"id": f"auto-{slug(os.path.splitext(d['file'])[0])}", "feature_type": "rune", "summary": d["summary"],
            "slices": d["slices"], "provenance": {**d["provenance"], "feature_type": "rune"},
            "savedAt": d["provenance"]["timestamp"]}


def synthesize(api: str, signum: str, stone: str, records: list[dict], main_id: str, corpus: list[dict]) -> dict:
    body = {"signum": signum, "stoneType": stone, "weathering": "Okänd",
            "analyses": [{"id": a["id"], "feature_type": "rune", "savedAt": a["savedAt"],
                          "slices": [{m: s[m] for m in METRICS} | {"position_mm": s["position_mm"]} for s in a["slices"]]}
                         for a in records],
            "analysis_id": main_id,
            "corpus": [{"signum": e["signum"], "feature_type": e.get("feature_type"), "means": e.get("means"),
                        "slices": [{m: s.get(m) for m in METRICS} | {"position_mm": s.get("position_mm")}
                                   for s in e.get("slices") or []]} for e in corpus],
            "corpus_note": None, "include_geology": True, "use_ai": False}
    r = requests.post(f"{api}/api/synthesis/analyze", json=body, timeout=900)
    r.raise_for_status()
    return r.json()


def slim(project: dict) -> dict:
    """Without raw profiles and positions when the document would pass Firestore's limit (withoutSliceDetail)."""
    if len(json.dumps(project, ensure_ascii=False)) <= FIRESTORE_DOC_LIMIT:
        return project
    drop = {"profile", "point", "direction", "up"}
    return {**project, "grooveAnalyses": [{**a, "slices": [{k: v for k, v in s.items() if k not in drop}
                                                           for s in a["slices"]]} for a in project["grooveAnalyses"]]}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default=os.environ.get("RUNFORSKNING_API", "http://localhost:8000"))
    ap.add_argument("--serier", default=",".join(ORDER))
    ap.add_argument("--skriv", action="store_true", help="skriv korpus och projekt till Firestore")
    ap.add_argument("--igen", action="store_true", help="mät om filer som misslyckades förra gången")
    ap.add_argument("--max-mb", type=float, default=None,
                    help="hoppa över större filer (analysmotorn tar som standard emot högst 500 MB, MAX_MESH_UPLOAD_MB)")
    a = ap.parse_args(argv)
    api, series = a.api.rstrip("/"), [s for s in a.serier.split(",") if s]

    # 1. Measure what has not been measured
    normals = known_normals()
    todo = files(series)
    if a.max_mb:
        skipped = [f["name"] for _, f, _ in todo if f["size"] > a.max_mb * 2**20]
        todo = [t for t in todo if t[1]["size"] <= a.max_mb * 2**20]
        if skipped:
            log(f"{len(skipped)} filer över {a.max_mb:g} MB väntar: {', '.join(skipped)}")
    log(f"{len(todo)} skanningar på disken i {', '.join(series)}")
    for i, (key, f, path) in enumerate(todo, 1):
        out = result_path(key, f)
        if os.path.exists(out):
            old = json.load(open(out, encoding="utf-8"))
            if "error" not in old or not a.igen:
                continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        log(f"{i}/{len(todo)} mäter {f['name']} ({f['size'] / 1e6:.0f} MB)")
        try:
            d = measure(api, key, f, path, normals)
        except (requests.RequestException, ValueError, KeyError) as e:
            log(f"   misslyckades: {e!r}")  # not saved: tried again on the next run
            continue
        json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False)
        log(f"   {d.get('error') or str(d['counts']['accepted']) + ' snitt i ' + str((d.get('rune_summary') or {}).get('n_runes')) + ' runor'} ({d['seconds']} s)")

    results = [json.load(open(result_path(k, f), encoding="utf-8")) for k, f, _ in todo if os.path.exists(result_path(k, f))]
    ok = [d for d in results if "error" not in d]
    log(f"mätta: {len(ok)} med godkända snitt, {len(results) - len(ok)} utan")
    if not a.skriv:
        log("utan --skriv: korpus, syntes och projekt väntar")
        return

    from api.auth import firebase_app, firestore
    from firebase_admin import auth
    user = auth.get_user_by_email(FOUNDER_EMAIL, app=firebase_app())
    name = user.display_name or "Viktor Kvant"
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    db = firestore()

    # 2. Corpus (before the syntheses, so that they compare against it)
    col = db.collection("corpus")
    for e in corpus_rows(ok, user.uid, name, now):
        col.document(e["id"]).set(e)
        log(f"korpus: {e['signum']} ({len(e['slices'])} snitt)")
    corpus = [x.to_dict() for x in col.stream()]
    log(f"korpusen har {len(corpus)} poster")

    # 3.–4. One project per stone (files without a signum: one per file), synthesis on the file with most slices
    stones: dict[str, list[dict]] = {}
    for d in ok:
        stones.setdefault(d.get("signum") or os.path.splitext(d["file"])[0], []).append(d)
    projects = db.collection(f"users/{user.uid}/projects")
    summary = []
    for key, ds in stones.items():
        ds.sort(key=lambda d: -d["counts"]["accepted"])
        recs = [record(d) for d in ds]
        main_d, signum = ds[0], ds[0].get("signum")
        separate = not is_runestone(main_d)
        syn = None
        if signum:
            try:
                syn = synthesize(api, signum, main_d["stone_type"], recs, recs[0]["id"], corpus)
            except requests.RequestException as e:
                log(f"   syntesen för {signum} misslyckades: {e!r}")
        rec = store().get(signum) if signum else None
        label = LABEL + (" – " + (main_d.get("object") or "föremål utan Rundatapost") if separate else "")
        pid = f"auto_{slug(key)}"
        old = projects.document(pid).get()
        doc = {
            "id": pid, "name": f"{' / '.join(main_d.get('signa') or [key])} ({label})",
            "fileName": main_d["file"], "metaText": signum or "", "metaStone": main_d["stone_type"],
            "metaWeathering": "Okänd", "slices": [], "grooveAnalyses": recs,
            "location": ", ".join(x for x in ((rec or {}).get("place"), (rec or {}).get("parish")) if x) or None,
            "autoRun": {"label": LABEL, "separate": separate, "object": main_d.get("object"), "series": main_d["series"],
                        "files": [d["file"] for d in ds], "normal_source": main_d["normal_source"],
                        "script": "scripts/batch_scans.py", "version": APP_VERSION, "date": now[:10],
                        "ai": False},
            "createdAt": old.to_dict().get("createdAt", now) if old.exists else now, "updatedAt": now,
        }
        if syn:
            doc["synthesis"] = {"result": syn, "analysisId": recs[0]["id"], "featureType": "rune", "savedAt": now}
        doc = json.loads(json.dumps(slim({k: v for k, v in doc.items() if v is not None}), ensure_ascii=False))
        projects.document(pid).set(doc)
        top = (syn or {}).get("candidates") or []
        summary.append({"project": pid, "signum": signum, "separate": separate, "files": len(ds),
                        "accepted": main_d["counts"]["accepted"], "outcome": ((syn or {}).get("outcome") or {}).get("text"),
                        "candidates": [c["name"] for c in top[:3]]})
        log(f"projekt {pid}: {summary[-1]['outcome'] or 'ingen syntes (inget signum)'}")
    json.dump(summary, open(os.path.join(OUT, "sammanfattning.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"klart: {len(summary)} projekt, sammanfattning i utdata/automatisk_korning/sammanfattning.json")


if __name__ == "__main__":
    main()
