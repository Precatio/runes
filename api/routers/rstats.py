"""Statistik i R: korpusanalyser, analys av en sten, figurer och reproducerbarhetspaket."""
from __future__ import annotations

import os
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from api.rundata import store
from api.routers.orthography import model as orthography_model
from src import r_bridge as rb
from src import r_findings

router = APIRouter()


@lru_cache(maxsize=1)
def _corpus() -> tuple[str, bytes, int]:
    rows = rb.corpus_rows(store().inscriptions, orthography_model().names)
    data = rb.csv_bytes(rows)
    return rb.fingerprint(data), data, len(rows)


def fingerprint() -> str:
    return _corpus()[0]


def corpus_ready() -> bool:
    return rb.enabled() and rb.JOB.ready(fingerprint())


def _state() -> dict:
    fp, _, n = _corpus()
    done = rb.JOB.result(fp) if rb.JOB.ready(fp) else None
    if done is None and rb.JOB.ready(fp):
        done = {}  # being written; report as not yet ready below
    st = rb.JOB.state_of(fp)
    return {"fingerprint": fp, "n_stones": n, "ready": bool(done),
            "computed_at": done.get("computed_at") if done else None,
            "errors": done.get("errors") if done else None,
            "running": bool(st.get("running")), "module": st.get("module"),
            "done_modules": st.get("done_modules", []), "error": st.get("error"),
            "modules": [{"key": m, "label": rb.MODULE_LABELS[m]} for m in rb.MODULES]}


@router.get("/status")
def r_status():
    """Om R finns på servern och om korpusanalyserna är beräknade."""
    out = {"r": rb.status()}
    if out["r"]["available"]:
        out["corpus"] = _state()
    return out


def _require_r():
    st = rb.status()
    if not st["available"]:
        raise HTTPException(status_code=503, detail=st.get("note") or "R är inte tillgängligt på servern.")


@router.post("/corpus/run")
def run_corpus():
    """Startar korpusanalyserna i bakgrunden (några minuter). Svarar direkt med läget."""
    _require_r()
    fp, data, _ = _corpus()
    if not rb.JOB.ready(fp):
        rb.JOB.start(fp, data)
    return _state()


def _figure_urls(fp: str, res: dict) -> dict:
    out = {}
    for m in rb.MODULES:
        figs = ((res.get(m) or {}).get("figures")) or {}
        out[m] = {k: f"/api/r/figure/{fp}/{v}" for k, v in figs.items() if v}
    return out


@lru_cache(maxsize=4)
def _findings(fp: str) -> tuple[list[dict], list[dict]]:
    res = rb.JOB.result(fp) or {}
    s = store()
    stone = []
    if res.get("attribution"):
        stone += r_findings.model_findings(res["attribution"], s.get, s.inscriptions, rb.oof_rows(fp))
    if res.get("chronology"):
        stone += r_findings.seriation_findings(res["chronology"], rb.stone_rows(fp, "chronology_stones.csv"),
                                               s.get, s.inscriptions)
    return stone, r_findings.corpus_patterns(res)


def _with_crosscheck(items: list[dict]) -> list[dict]:
    """Lägger på avstämningen mot Runor 2020 och Wikidata där den är gjord (bara ur cachen)."""
    from src import crosscheck
    out = []
    for f in items:
        cc = crosscheck.cached(f["signum"], f.get("suggested")) if f.get("suggested") else None
        out.append(crosscheck.apply(f, cc) if cc else dict(f))
    return out


def findings() -> tuple[list[dict], list[dict]]:
    """R-fynden för Forskningsluckor, eller tomma listor om korpusanalysen inte är beräknad."""
    if not corpus_ready():
        return [], []
    stone, patterns = _findings(fingerprint())
    return _with_crosscheck(stone), patterns


@router.post("/crosscheck")
def run_crosscheck(limit: int = 400):
    """Stämmer av appens förslag (nya och motsägande) mot Runor 2020 (RAÄ) och Wikidata. Hämtar det som inte är
    cachat; tar upp till någon minut första gången."""
    from src import crosscheck
    if not crosscheck.enabled():
        raise HTTPException(status_code=503, detail="Avstämning mot externa källor är avstängd på servern.")
    if not corpus_ready():
        raise HTTPException(status_code=409, detail="Korpusanalyserna i R är inte beräknade än.")
    stone, _ = _findings(fingerprint())
    from api.routers.research import _orthographic_findings
    items = [f for f in list(stone) + list(_orthographic_findings())
             if f.get("suggested") and f["verdict"] in ("nytt", "motsäger")]
    items = sorted(items, key=lambda f: -f["score"])[:limit]
    res = crosscheck.check_many([(f["signum"], f["suggested"]) for f in items])
    counts: dict[str, int] = {}
    for r in res.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"checked": len(res), "counts": counts, "sources": crosscheck.SOURCES,
            "results": sorted(res.values(), key=lambda r: r["signum"])}


@router.get("/corpus")
def corpus_results():
    """Resultaten av korpusanalyserna med figurernas adresser och de mönster appen ser."""
    _require_r()
    fp = fingerprint()
    res = rb.JOB.result(fp)
    if res is None:
        raise HTTPException(status_code=409, detail="Korpusanalyserna är inte beräknade än. Starta dem med POST /api/r/corpus/run.")
    stone, patterns = _findings(fp)
    stone = _with_crosscheck(stone)
    html_map = (res.get("geography") or {}).get("html_map")
    return {**res, "figure_urls": _figure_urls(fp, res), "patterns": patterns,
            "findings_summary": {"n": len(stone), "new": sum(f["verdict"] == "nytt" for f in stone),
                                 "contradicts": sum(f["verdict"] == "motsäger" for f in stone),
                                 "crosschecked": sum(1 for f in stone if f.get("crosscheck")),
                                 "already_known": sum(1 for f in stone if (f.get("crosscheck") or {}).get("status") == "finns redan"),
                                 "still_new": sum(1 for f in stone if f["verdict"] == "nytt" and
                                                  (f.get("crosscheck") or {}).get("status") in ("saknas", "samma som"))},
            "findings": sorted(stone, key=lambda f: -f["score"]),
            "html_map_url": f"/api/r/figure/{fp}/{html_map}" if html_map else None,
            "package_url": "/api/r/package"}


@router.get("/figure/{fp}/{name}")
def corpus_figure(fp: str, name: str):
    d = rb.JOB.directory(fp)
    if name.endswith(".html") and name == os.path.basename(name) and os.path.exists(os.path.join(d, name)):
        return FileResponse(os.path.join(d, name), media_type="text/html")
    data = rb.figure(d, name)
    if data is None:
        raise HTTPException(status_code=404, detail="Figuren finns inte.")
    return Response(data, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


@router.get("/figure/{fp}/{kind}/{key}/{name}")
def stone_figure(fp: str, kind: str, key: str, name: str):
    if kind not in ("stones", "landscape") or not key.isalnum():
        raise HTTPException(status_code=404, detail="Figuren finns inte.")
    data = rb.figure(os.path.join(rb.JOB.directory(fp), kind, key), name)
    if data is None:
        raise HTTPException(status_code=404, detail="Figuren finns inte.")
    return Response(data, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


def _urls(fp: str, res: dict) -> dict:
    rel = os.path.relpath(res["figure_dir"], rb.JOB.directory(fp)).split(os.sep)
    return {k: f"/api/r/figure/{fp}/{rel[0]}/{rel[1]}/{v}" for k, v in (res.get("figures") or {}).items() if v}


def stone_analysis(signum: str, candidates: list[str], with_landscape: bool = True, lang: str = "sv") -> dict | None:
    """R-analysen av en sten för rapporter och stenanalysen; None om R eller korpusanalysen saknas."""
    if not corpus_ready():
        return None
    rec = store().get(signum)
    if not rec:
        return None
    fp = fingerprint()
    try:
        res = rb.stone(fp, rec["signum"], candidates, lang)
    except rb.RError as e:
        return {"error": str(e)}
    res["figure_urls"] = _urls(fp, res)
    if with_landscape and rec.get("lat") is not None:
        try:
            land = rb.landscape(fp, rec["signum"], lang=lang)
            land["figure_urls"] = _urls(fp, land)
            res["landscape"] = land
        except rb.RError as e:
            res["landscape"] = {"error": str(e)}
    stone_f, _ = _findings(fp)
    res["findings"] = _with_crosscheck([f for f in stone_f if f["signum"] == rec["signum"]])
    res["fingerprint"] = fp
    return res


@router.get("/stone/{signum:path}")
def r_stone(signum: str, candidates: str = "", landscape: bool = True, lang: str = "sv"):
    """En sten mot korpusanalyserna: kandidaternas områden, grupp, modellens sannolikheter, formler, seriation
    och landskap."""
    _require_r()
    if not corpus_ready():
        raise HTTPException(status_code=409, detail="Korpusanalyserna i R är inte beräknade än. Starta dem under Statistik (R).")
    rec = store().get(signum)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.")
    from src.research_gaps import is_runestone
    if not is_runestone(rec):
        raise HTTPException(status_code=422, detail="R-analysen gäller svenska vikingatida runstenar.")
    if lang not in ("sv", "en"):
        raise HTTPException(status_code=400, detail="Språket ska vara sv eller en.")
    res = stone_analysis(rec["signum"], [c.strip() for c in candidates.split(",") if c.strip()], landscape, lang)
    if res and res.get("error"):
        raise HTTPException(status_code=500, detail=res["error"])
    return _public(res)


def _public(res: dict) -> dict:
    """Utan serverns sökvägar."""
    out = {k: v for k, v in res.items() if k != "figure_dir"}
    if isinstance(out.get("landscape"), dict):
        out["landscape"] = {k: v for k, v in out["landscape"].items() if k != "figure_dir"}
    return out


@router.get("/package")
def r_package(signum: str = "", candidates: str = ""):
    """Reproducerbarhetspaket (zip): R-skripten, korpusen, resultaten och ett skript som kör om allt."""
    _require_r()
    if not corpus_ready():
        raise HTTPException(status_code=409, detail="Korpusanalyserna är inte beräknade än.")
    rec = store().get(signum) if signum else None
    data = rb.package(fingerprint(), rec["signum"] if rec else None, [c.strip() for c in candidates.split(",") if c.strip()])
    name = f"runforskning_R_{(rec['signum'] if rec else 'korpus').replace(' ', '_')}.zip"
    return Response(data, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{name}"'})
