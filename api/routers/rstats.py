"""Statistik i R: korpusanalyser, analys av en sten, figurer och reproducerbarhetspaket."""
from __future__ import annotations

import os
import re
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Request
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
    # Only done.json: the page polls this every few seconds, and the modules' results are not needed for it
    done = rb.JOB.done(fp)
    if done is None and rb.JOB.ready(fp):
        done = {}  # being written; report as not yet ready below
    st = rb.JOB.state_of(fp)
    return {"fingerprint": fp, "n_stones": n, "ready": bool(done),
            "computed_at": done.get("computed_at") if done else None,
            "errors": done.get("errors") if done else None,
            "running": bool(st.get("running")), "module": st.get("module"),
            "done_modules": st.get("done_modules", []), "error": st.get("error"),
            "modules": [{"key": m, "label": rb.MODULE_LABELS[m]} for m in rb.MODULES]}


def autorun() -> bool:
    """Starts the corpus analyses on their own when the data or the analysis code have changed: R is available, the
    present version of the data has no results, nothing is running for it, and an earlier run of it did not fail (a
    failed run is retried with the button on the page). Returns whether a run was started."""
    if os.environ.get("R_AUTORUN", "1") in ("0", "false") or not rb.enabled():
        return False
    fp, data, _ = _corpus()
    st = rb.JOB.state_of(fp)
    if rb.JOB.ready(fp) or st.get("running") or st.get("error"):
        return False
    return rb.JOB.start(fp, data)


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
    if res.get("anonymous"):
        stone += r_findings.anonymous_findings(res["anonymous"], s.get, s.inscriptions)
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
    from src import pattern_registry
    return _with_crosscheck(stone), pattern_registry.annotate(patterns)


@router.get("/pattern-articles")
def pattern_articles():
    """Artiklarna (och utkasten) som skrivits om R-mönstren, per mönster ("ämne|nyckel", src/blog_topics.topic_key): en
    artikel hör till ett mönster när dess ämne är mönstrets nyckel, som Månadens fynd sparar det, eller när
    data/article_patterns.json kopplar dem. Statistik och Forskningsluckor märker mönstren och kan dölja dem."""
    import json
    from api.routers import blog
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data",
                        "article_patterns.json")
    try:
        extra = {k: v for k, v in json.load(open(path, encoding="utf-8")).items() if not k.startswith("_")}
    except (OSError, ValueError):
        extra = {}
    out: dict[str, list[dict]] = {}
    try:
        posts = blog._all()
    except Exception:  # noqa: BLE001 – without Firestore the patterns are simply not marked
        posts = []
    for p in posts:
        keys = set(extra.get(p.get("slug") or "", []))
        if "|" in (p.get("topic") or ""):
            keys.add(p["topic"])
        for k in keys:
            out.setdefault(k, []).append({"title": p.get("title") or "", "slug": p.get("slug") or "",
                                          "published": bool(p.get("published"))})
    return {"articles": out}


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


@router.get("/scan")
def landscape_scan():
    """Genomsökningen av landskapet (r/remains.R): varje mönster på kartan mot avståndet till varje sorts plats, med
    mönstrens och platsernas namn. Tom om korpusanalysen inte är beräknad."""
    from src import places
    from src.pattern_map import PATTERNS
    if not corpus_ready():
        return {"available": False, "reason": "Korpusanalysen i R är inte beräknad (Statistik → Beräkna)."}
    fp = fingerprint()
    res = rb.JOB.done(fp) or {}
    sc = (rb.JOB.module(fp, "remains") or {}).get("scan") or {}
    if not sc.get("available"):
        return {"available": False, "reason": sc.get("error") or "Genomsökningen saknas (lämningar och ortnamn hämtas med "
                                                               "scripts/fetch_raa_remains.py och fetch_place_names.py)."}
    return {**sc, "computed_at": res.get("computed_at"),
            "features": [{"key": k, "label": l, "group": g} for k, l, g, _ in PATTERNS],
            "kind_labels": {k: l for k, l, *_ in places.KINDS}}


@router.get("/hotspots")
def hotspots():
    """Hot spots och kluster per mönster på kartan (r/hotspots.R): Morans I, Getis-Ord Gi* och Kulldorffs scanstatistik."""
    if not corpus_ready():
        return {"available": False, "reason": "Korpusanalysen i R är inte beräknad (Statistik → Beräkna)."}
    fp = fingerprint()
    res = rb.JOB.done(fp) or {}
    h = rb.JOB.module(fp, "hotspots") or {}
    if not h.get("patterns"):
        return {"available": False, "reason": (res.get("errors") or {}).get("hotspots") or "Hot spots saknas i korpusanalysen."}
    return {"available": True, "computed_at": res.get("computed_at"), **h}


@router.get("/corpus")
def corpus_results(request: Request):
    """Resultaten av korpusanalyserna med figurernas adresser och de mönster appen ser."""
    _require_r()
    fp = fingerprint()
    if not rb.JOB.ready(fp):  # the results themselves are read only when the answer is not already cached
        raise HTTPException(status_code=409, detail=_NOT_COMPUTED)
    from api.cache import cached_json, dir_version
    from src import crosscheck
    return cached_json(request, f"corpus|{fp}|{dir_version(crosscheck.CACHE)}", lambda: _corpus_results(fp))


_NOT_COMPUTED = "Korpusanalyserna är inte beräknade än. Starta dem med POST /api/r/corpus/run."


def _corpus_results(fp: str) -> dict:
    res = rb.JOB.result(fp)
    if res is None:  # a file being written right now
        raise HTTPException(status_code=409, detail=_NOT_COMPUTED)
    stone, patterns = _findings(fp)
    from src import stone_findings  # also what Rundata lacks about a stone beyond attribution (gaps, Runor 2020, own)
    s_ = store()
    stone = _with_crosscheck(stone) + stone_findings.all_findings(s_.get, s_.inscriptions)
    from src import pattern_registry
    from src import linking
    patterns = patterns + linking.patterns(os.path.join(os.path.dirname(rb.ROOT + "/"), "data", "links.json"))
    patterns = pattern_registry.annotate(patterns)  # "Nytt" the first 30 days after a pattern appears
    html_map = (res.get("geography") or {}).get("html_map")
    from src import r_explain
    return {**res, "figure_urls": _figure_urls(fp, res), "patterns": patterns, "sections": r_explain.sections(res),
            "overview": r_explain.overview(res),
            "findings_summary": {"n": len(stone), "new": sum(f["verdict"] == "nytt" for f in stone),
                                 "contradicts": sum(f["verdict"] == "motsäger" for f in stone),
                                 "crosschecked": sum(1 for f in stone if f.get("crosscheck")),
                                 "already_known": sum(1 for f in stone if (f.get("crosscheck") or {}).get("status") == "finns redan"),
                                 "still_new": sum(1 for f in stone if f["verdict"] == "nytt" and
                                                  (f.get("crosscheck") or {}).get("status") in ("saknas", "samma som"))},
            "findings": sorted(stone, key=lambda f: -f["score"]),
            "html_map_url": f"/api/r/figure/{fp}/{html_map}" if html_map else None,
            "package_url": "/api/r/package"}


def _check_fp(fp: str) -> None:
    """The corpus version in a URL is a fingerprint (rb.fingerprint: 16 hex digits), never a path such as "..". """
    if not re.fullmatch(r"[0-9a-f]{16}", fp):
        raise HTTPException(status_code=404, detail="Figuren finns inte.")


@router.get("/figure/{fp}/{name}")
def corpus_figure(fp: str, name: str):
    _check_fp(fp)
    d = rb.JOB.directory(fp)
    if name.endswith(".html") and name == os.path.basename(name) and os.path.exists(os.path.join(d, name)):
        return FileResponse(os.path.join(d, name), media_type="text/html")
    data = rb.figure(d, name)
    if data is None:
        raise HTTPException(status_code=404, detail="Figuren finns inte.")
    return Response(data, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


@router.get("/figure/{fp}/{kind}/{key}/{name}")
def stone_figure(fp: str, kind: str, key: str, name: str):
    _check_fp(fp)
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


MAX_CANDIDATES = 10


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
    # Every new list of candidates is a new R run (about 1 GB, src/r_bridge.py): a handful of carver names, no more
    names = [c.strip() for c in candidates.split(",") if c.strip()]
    if len(names) > MAX_CANDIDATES or any(len(c) > 100 for c in names):
        raise HTTPException(status_code=422, detail=f"Högst {MAX_CANDIDATES} kandidater, med namn på högst 100 tecken.")
    res = stone_analysis(rec["signum"], names, landscape, lang)
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
