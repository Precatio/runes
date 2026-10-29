"""Forskningsluckor och prioriteringar."""
import json
import os
import threading
from functools import lru_cache

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from api.cache import cached_json, dir_version, single_flight, write_json
from api.rundata import store
from api.routers.orthography import model as orthography_model
from src import findings, research_gaps as gaps

router = APIRouter()


class GapsRequest(BaseModel):
    measured_signa: list[str] = Field(default_factory=list)


@single_flight
@lru_cache(maxsize=1)
def _hypotheses() -> dict:
    m, s = orthography_model(), store()
    h = gaps.orthographic_hypotheses(m, s.inscriptions)
    for item in h["new"] + h["reconsider"]:
        item.update(findings.stone_extras(s.get(item["signum"]), item["carver"], s.inscriptions, m.names))
    return h


@lru_cache(maxsize=1)
def _open_questions() -> dict:
    return gaps.open_questions(store().inscriptions)


class QuestionRequest(BaseModel):
    a: str
    kind: str  # drag, landskap, tid or bergart
    key: str
    # p-values of the questions asked earlier in the visit, adjusted together with this one (Benjamini–Hochberg)
    earlier: list[float] = Field(default_factory=list, max_length=500)


@lru_cache(maxsize=2)
def _question_prep(_stamp: int) -> dict:
    from src import question, r_bridge as rb
    return question.prepare(rb.corpus_rows(store().inscriptions, orthography_model().names))


def _question() -> dict:
    return _question_prep(id(store().inscriptions))


@router.get("/question/options")
def question_options():
    """Det som går att välja i Pröva en egen fråga (src/question.py): dragen, landskapen, tidsgränserna och
    bergartsfamiljerna, med antal runstenar."""
    from src import question
    return question.options(_question())


@router.post("/question")
def ask_question(req: QuestionRequest):
    """Pröva en egen fråga: är draget A vanligare där B gäller? Justerat för landskap och tid, prövat i två halvor av
    socknarna och utan de flitigaste ristarna, med tidigare frågor BH-justerade tillsammans (METHODS.md 1y)."""
    from fastapi import HTTPException
    from api.routers import rstats
    from src import question
    from src import r_bridge as rb
    key = req.key if req.kind != "tid" else int(req.key)
    try:
        out = question.ask(_question(), req.a, req.kind, key, req.earlier)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    fp = rstats.fingerprint()
    # The two checks in R (r/question.R) when there is an answer to check and R is installed; without them the verdict
    # stands and the answer says that they could not be run
    if (out.get("adjusted") or {}).get("p") is not None:
        checks = None
        if rb.enabled():
            try:
                checks = rb.question(fp, question.r_rows(_question(), req.a, req.kind, key), req.kind)
            except Exception as e:  # noqa: BLE001 – R missing a package or a model that does not converge
                checks = None
                out["r_error"] = str(e)[-300:]
        out = question.apply_r(out, checks)
    # The corpus version (the same fingerprint as the R analyses), so that a saved answer says what it was computed on
    return {**out, "corpus": fp}


@router.get("/gaps/textmodel")
def textmodel_gaps():
    """Sannolikhetsmodellens öppna luckor (data/textmodel_candidates.json, scripts/textmodel_candidates.py): luckor som
    Rundata lämnat oåterställda där modellen fyller i ett känt ord med minst 50 % kalibrerad sannolikhet. Underlag att granska mot foto och
    skanning, inte ett resultat (METHODS.md 14)."""
    import json
    import os
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "textmodel_candidates.json")
    if not os.path.exists(p):
        return {"available": False, "note": "Kandidatlistan är inte byggd (scripts/textmodel_candidates.py)."}
    return {"available": True, **json.load(open(p, encoding="utf-8"))}


@router.post("/gaps")
def research_gaps(req: GapsRequest):
    s = store()
    # Normalise measured signa through Rundata (e.g. "So 113" -> "Sö 113")
    measured = {rec["signum"] for rec in (s.get(x) for x in req.measured_signa) if rec}
    return {
        "coverage": gaps.coverage(s.inscriptions, measured),
        "hypotheses": _hypotheses(),
        "open_questions": _open_questions(),
        "measurement_priorities": gaps.measurement_priorities(s.inscriptions, measured),
        "source_note": gaps.SOURCE_NOTE,
        "attribution": s.meta["attribution"],
    }


class FindingsRequest(BaseModel):
    # Corpus entries ({signum, feature_type, means}) from the user's projects
    corpus: list[dict] = Field(default_factory=list)


@single_flight
@lru_cache(maxsize=1)
def _orthographic_findings() -> tuple:
    m, s = orthography_model(), store()
    return tuple(findings.add_extras(findings.orthographic_findings(m, s.inscriptions), s.get, s.inscriptions, m.names))


@router.post("/findings")
def research_findings_endpoint(req: FindingsRequest):
    """Appens resultat mot Rundata: stämmer, nytt eller motsäger – med en öppet redovisad uppskattning. Svaret sparas per
    begäran, korpusanalysernas version och avstämningarna mot Runor (api/cache.py)."""
    return cached_json(None, findings_key(req), lambda: research_findings(req))


def findings_key(req: FindingsRequest) -> str:
    import hashlib
    from api.cache import findings_version
    from src import crosscheck
    body = hashlib.sha256(req.model_dump_json().encode()).hexdigest()[:16]
    # The stone findings' input files (own findings, links, gap candidates, Runor) are part of the key, so that an edit
    # to data/stone_findings.json shows without restarting the API (the same key part as /api/r/corpus)
    return (f"findings|{body}|{_fp()}|{dir_version(crosscheck.CACHE)}|{id(store().inscriptions)}"
            f"|{findings_version()}")


def research_findings(req: FindingsRequest):
    s = store()
    technique, technique_note = findings.technique_findings(req.corpus, s.get, s.inscriptions)
    extra = findings.add_extras(technique, s.get, s.inscriptions, orthography_model().names)
    from api.routers import rstats
    r_items, r_patterns = rstats.findings()
    r_items = findings.add_extras(r_items, s.get, s.inscriptions, orthography_model().names)
    from src import stone_findings  # gap fills, Runor 2020 and our own findings: what Rundata lacks about a stone
    items = rstats._with_crosscheck(list(_orthographic_findings())) + extra + r_items + stone_findings.all_findings(s.get, s.inscriptions)
    from src.r_findings import finding_significance
    for f in items:
        f["significance"] = finding_significance(f)
    _with_levels(items)
    items.sort(key=lambda f: -f["score"])
    return {
        "r_patterns": r_patterns, "r_ready": rstats.corpus_ready(),
        "findings": items,
        "summary": findings.summarize(items),
        "technique_note": technique_note,
        "method_note": findings.__doc__.split("\n\n", 1)[1].strip(),
        "source_note": gaps.SOURCE_NOTE,
    }


def _levels_path() -> str:
    """Tolkningsnivåernas cachefil: översiktens nyckel plus koden för tolkningen och språkkontrollen."""
    import hashlib
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    code = "".join(hashlib.sha256(open(os.path.join(root, rel), "rb").read()).hexdigest()[:12]
                   for rel in ("src/interpretation.py", "src/findings.py", "src/r_findings.py"))
    key = hashlib.sha256(f"{_overview_key(_fp())}|{code}".encode()).hexdigest()[:16]
    return os.path.join(root, "data", "cache", "levels", f"{key}.json")


_levels_lock = threading.Lock()


def _with_levels(items: list[dict]) -> list[dict]:
    """Lägger tolkningens nivå (starkt, måttligt, svagt …) på varje fynd, så att listan kan visa den utan att raden
    öppnas. Samma regler som /interpret (METHODS.md 14d); nivåerna sparas på disk och räknas bara om när data eller
    koden ändras."""
    with _levels_lock:  # one at a time: the cache file is read, extended and written back
        return _add_levels(items)


def _add_levels(items: list[dict]) -> list[dict]:
    from src import interpretation, stone_overview
    path = _levels_path()
    try:
        cache = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    s, ctx, profiles, changed = store(), None, {}, False
    for f in items:
        if interpretation.is_stone_finding(f):
            continue  # the levels are for carver suggestions; a stone finding gets its own reasoning in /interpret
        key = "|".join(str(x) for x in (f["signum"], f["method"], f.get("suggested"), f.get("score"),
                                        (f.get("crosscheck") or {}).get("status")))
        if key not in cache:
            rec = s.get(f["signum"])
            if not rec:
                continue
            if ctx is None:
                ctx, _ = _overview_context(_fp())
            if rec["signum"] not in profiles:
                profiles[rec["signum"]] = stone_overview.stone(rec, ctx, detail=True) if gaps.is_runestone(rec) else None
            it = interpretation.interpret(f, rec, ctx, profiles[rec["signum"]])
            cache[key] = {"level": it["level"], "support": it["support"], "against": it["against"]}
            changed = True
        f["interpretation"] = cache[key]
    if changed:
        write_json(path, cache)
    return items


@router.get("/geology/{signum:path}")
def stone_geology(signum: str, radius_km: float = 10.0):
    """Berggrunden där stenen står (SGU) jämförd med stenens material i Rundata."""
    from fastapi import HTTPException
    from src import geology
    rec = store().get(signum)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.")
    if rec.get("lat") is None:
        raise HTTPException(status_code=422, detail="Stenen saknar koordinater i Rundata.")
    if not 1 <= radius_km <= 25:
        raise HTTPException(status_code=400, detail="Radien ska vara 1–25 km.")
    if not geology.enabled():
        raise HTTPException(status_code=503, detail="Geologiuppslag är avstängt på servern.")
    return {"signum": rec["signum"], "place": rec["place"], **geology.bedrock(rec["lat"], rec["lon"],
                                                                                rec.get("material") or "", radius_km)}


@router.get("/literature")
def literature_catalog():
    """Litteraturregistret: verken, om de är indexerade och hur många stenar de nämner (src/literature.py)."""
    from src import literature
    return {"works": literature.catalog()}


@router.get("/literature/{signum:path}")
def stone_literature(signum: str):
    """Var avhandlingarna och utgåvorna i registret nämner stenen, med tryckt sida och korta utdrag."""
    from fastapi import HTTPException
    from src import literature
    rec = store().get(signum)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.")
    return literature.for_stone(rec["signum"])


@router.get("/language/{signum:path}")
def stone_language(signum: str, carver: str = ""):
    """Språkdrag i inskriften, och jämförda med en ristares inskrifter om en ristare anges."""
    from fastapi import HTTPException
    from src.language_profile import TRAITS, carver_profile, compare, traits
    from src.research_gaps import certain_carvers
    rec = store().get(signum)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.")
    from src.inscription_types import CATEGORIES, categories
    names = orthography_model().names
    t = traits(rec, names)
    out = {"signum": rec["signum"],
           "categories": [{"key": k, "label": CATEGORIES[k][0], "definition": CATEGORIES[k][1]} for k in categories(rec)],
           "traits": [{"trait": k, "group": TRAITS[k][0], "label": TRAITS[k][1],
                                                "definition": TRAITS[k][2], "value": v} for k, v in t.items()]}
    if carver:
        # Against the province's other stones as well as the carver (src/synthesis.language_check), so that a trait that
        # is common everywhere does not count as a match; falls back to the carver alone when the province is too small
        from src.synthesis import language_check
        out["comparison"] = (language_check(rec, carver, store().inscriptions, names)
                             or compare(t, carver_profile(carver, store().inscriptions, certain_carvers, names,
                                                          exclude=rec["signum"])))
    return out


@lru_cache(maxsize=1)
def _categories() -> dict:
    from src.inscription_types import carver_categories
    from src.research_gaps import certain_carvers
    return carver_categories(store().inscriptions, certain_carvers)


@lru_cache(maxsize=2)
def _pattern_map_for(_stamp: tuple) -> dict:
    from src import pattern_map
    return pattern_map.build(store().inscriptions, orthography_model().names)


def _pattern_map() -> dict:
    from src import places
    return _pattern_map_for(places._mtimes())


@router.get("/pattern-map")
def pattern_map(request: Request):
    """Mönsterkartan: varje runstens plats, stilgruppens mittår, om den har varje mönster och avståndet till närmaste
    plats av varje sort (src/pattern_map.py, src/places.py)."""
    return cached_json(request, pattern_map_key(), _pattern_map)


def pattern_map_key() -> str:
    from src import places
    return f"pattern-map|{places._mtimes()}|{id(store().inscriptions)}"


@lru_cache(maxsize=2)
def _nordic_for(_stamp: int) -> dict:
    from src import nordic
    return nordic.build(store().inscriptions)


@router.get("/nordic")
def nordic(request: Request):
    """Danska, norska och svenska runstenar jämförda, och drag över gränserna: Rundatas anmärkningar, texter som
    nämner ett annat land och dansk prägel på svenska stenar och ristare (src/nordic.py)."""
    stamp = id(store().inscriptions)
    return cached_json(request, f"nordic|{stamp}", lambda: _nordic_for(stamp))


@router.get("/places")
def places_layer(kind: str):
    """En sorts platser för kartan: [lat, lon, namn, uppgift] (ortnamn, medeltida kyrkor, fornlämningar)."""
    from fastapi import HTTPException
    from src import places
    if kind not in places.KEYS:
        raise HTTPException(status_code=404, detail=f"Okänd sort: {kind}")
    label, group, help_ = next((l, g, h) for k, l, g, h in places.KINDS if k == kind)
    pts = places.places()[kind]
    return {"kind": kind, "label": label, "group": group, "help": help_,
            "points": [[round(p["lat"], 5), round(p["lon"], 5), p["name"], p["info"]] for p in pts]}


@router.get("/landscape/{signum:path}")
def stone_landscape(signum: str):
    """Närmaste ortnamn, medeltida kyrka och fornlämning av varje sort för en runsten, och om den är flyttad."""
    from fastapi import HTTPException
    from src import places
    rec = store().get(signum)
    if not rec:
        raise HTTPException(status_code=404, detail=f"'{signum}' finns inte i Rundata.")
    return places.landscape(rec)


@router.get("/place-test")
def place_test(pattern: str, kind: str, km: float = 2.0, moved: bool = False):
    """Utforskande prov: andelen stenar med mönstret nära en sorts plats mot övriga, okontrollerat och med landskapet
    konstant (Mantel–Haenszel). Flyttade stenar räknas inte om inte moved=true."""
    from fastapi import HTTPException
    from src import places
    data = _pattern_map()
    keys = [p["key"] for p in data["patterns"]]
    kinds = [k["key"] for k in data["place_kinds"]]
    if pattern not in keys or kind not in kinds:
        raise HTTPException(status_code=404, detail="Okänt mönster eller okänd sorts plats.")
    if not 0.2 <= km <= 20:
        raise HTTPException(status_code=422, detail="Radien ska vara mellan 0,2 och 20 km.")
    i, j = keys.index(pattern), kinds.index(kind)
    rows = [(st["p"], st["v"][i], st["d"][j]) for st in data["stones"]
            if st["v"][i] is not None and (moved or not st["m"])]
    return {"pattern": pattern, "kind": kind, "moved_included": moved, "result": places.near_test(rows, km)}


def _stone_size_path(mtime: float) -> str:
    """The size analysis' cache file: the measurements, Rundata and the code that computes it."""
    import hashlib
    from api.rundata import DATA_PATH
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parts = [repr(mtime), str(os.path.getmtime(DATA_PATH)) if os.path.exists(DATA_PATH) else "-"]
    for rel in ("src/stone_size.py", "src/stone_dimensions.py", "src/inscription_types.py", "src/research_gaps.py"):
        parts.append(hashlib.sha256(open(os.path.join(root, rel), "rb").read()).hexdigest()[:12])
    key = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return os.path.join(root, "data", "cache", "stone_size", f"{key}.json")


@single_flight
@lru_cache(maxsize=2)
def _stone_size(mtime: float) -> dict:
    """5000 permutations per test (about 15 s): computed once per version of the data and the code and kept on disk
    (data/cache/stone_size/), so that a restart of the server reads it instead. The answer is deterministic (a fixed
    seed), so the saved one is the same as a new computation."""
    from fastapi.encoders import jsonable_encoder
    from src import stone_dimensions, stone_size
    path = _stone_size_path(mtime)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        pass
    out = jsonable_encoder({**stone_size.analyse(store().inscriptions, stone_dimensions.load().get("stones") or {}),
                            "meta": stone_dimensions.load().get("meta"), "source": stone_dimensions.SOURCE})
    write_json(path, out)
    return out


@router.get("/stone_size")
def stone_size_analysis():
    """Runstenens storlek mot inskriftens syfte, statusord, antal personer, textens längd och ristare (METHODS.md 10b)."""
    import os
    from src import stone_dimensions
    mtime = os.path.getmtime(stone_dimensions.DATA) if os.path.exists(stone_dimensions.DATA) else 0.0
    return _stone_size(mtime)


@single_flight
@lru_cache(maxsize=2)
def _overview_context(fp: str):
    from api.routers import rstats
    from src import r_bridge, stone_overview
    d = r_bridge.JOB.directory(fp) if rstats.corpus_ready() else None
    ctx = stone_overview.context(store().inscriptions, orthography_model(), d)
    rows = {}
    if d:
        rows = {name: {r["signum"]: r for r in r_bridge.stone_rows(fp, f"{name}_stones.csv")} for name in ("chronology", "clusters")}
    return ctx, rows


def _overview_key(fp: str) -> str:
    """Översiktens nyckel: R-korpusens version, Rundata, måtten och koden som räknar fram den."""
    import hashlib
    import os
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parts = [fp]
    for rel in ("data/rundata.json", "data/stone_dimensions.json"):
        p = os.path.join(root, rel)
        parts.append(str(os.path.getmtime(p)) if os.path.exists(p) else "-")
    for rel in ("src/stone_overview.py", "src/synthesis.py", "src/orthography.py", "src/language_profile.py",
                "src/geology.py", "src/research_gaps.py"):
        parts.append(hashlib.sha256(open(os.path.join(root, rel), "rb").read()).hexdigest()[:12])
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


@single_flight
@lru_cache(maxsize=2)
def _overview(fp: str) -> dict:
    """Beräknas en gång per version av underlaget och sparas på disk (data/cache/overview/), så att en omstart av
    servern inte kostar en ny beräkning."""
    import json
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "data", "cache", "overview", f"{_overview_key(fp)}.json")
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except ValueError:
            pass
    out = _compute_overview(fp)
    write_json(path, out)
    return out


def _compute_overview(fp: str) -> dict:
    from src import stone_overview
    ctx, _ = _overview_context(fp)
    stones = [stone_overview.stone(r, ctx) for r in store().inscriptions if gaps.is_runestone(r)]
    signed = [x for x in stones if x["status"] == "signerad"]
    flagged = [x for x in signed if (x["alternative"] or {}).get("strength", 0) >= 0.4]
    return {"stones": stones,
            "counts": {s: sum(1 for x in stones if x["status"] == s) for s in stone_overview.STATUS_ORDER},
            "control": {"n_signed": len(signed), "flagged": len(flagged),
                        "would_be_misjudged": sum(1 for x in flagged if (x["support"] or 0) < 0.4)},
            "r_available": bool(ctx["oof"] or ctx["pred"]), "status_order": list(stone_overview.STATUS_ORDER)}


def _fp() -> str:
    from api.routers import rstats
    return rstats.fingerprint() if rstats.corpus_ready() else "utan-r"


@router.get("/overview")
def stones_overview(request: Request):
    """Alla runstenar med stöd för Rundatas ristare, starkaste alternativ och status (METHODS.md 14c)."""
    fp = _fp()
    return cached_json(request, overview_key(fp), lambda: _overview(fp))


def overview_key(fp: str) -> str:
    return f"overview|{fp}|{id(store().inscriptions)}"


@router.get("/overview/{signum:path}")
def stone_profile(signum: str):
    """En stens samlade belägg (metod för metod), alternativa ristare och övriga variabler."""
    from fastapi import HTTPException
    from src import crosscheck, stone_overview
    rec = store().get(signum)
    if not rec or not gaps.is_runestone(rec):
        raise HTTPException(status_code=404, detail=f"'{signum}' är ingen svensk vikingatida runsten i Rundata.")
    ctx, rows = _overview_context(_fp())
    out = stone_overview.stone(rec, ctx, detail=True)
    out["variables"] = stone_overview.variables(rec, store().inscriptions, rows)
    alt = (out.get("alternative") or {}).get("carver")
    out["crosscheck"] = crosscheck.cached(rec["signum"], alt) if alt else None
    return out


@lru_cache(maxsize=2)
def _archive(fp: str) -> dict:
    """Arkivets datadelar: ristarna och de kända stenarna ur Rundata, syftena ur kategorierna."""
    from collections import Counter
    from src.styles import BY_CODE
    s = store()
    carvers = []
    for c in s.carvers():
        if c["signed"] + c["attributed"] < 10:
            continue
        stones = [r for r in s.inscriptions if any(x["name"] == c["name"] and x["kind"] in ("S", "A") for x in r["carvers"])]
        provinces = Counter(gaps.province(r) for r in stones)
        styles = Counter(r["style"] for r in stones if r["style"] in BY_CODE and not r["style_uncertain"])
        # Period from the style groups that make up at least a tenth of the carver's dated stones
        n_styled = sum(styles.values())
        years = [(BY_CODE[st]["from"], BY_CODE[st]["to"]) for st, n in styles.items()
                 if BY_CODE[st].get("from") and n >= 0.1 * n_styled]
        signed = [r["signum"] for r in stones if any(x["name"] == c["name"] and x["kind"] == "S" and not x["uncertain"] for x in r["carvers"])]
        carvers.append({"name": c["name"], "signed": c["signed"], "attributed": c["attributed"],
                        "provinces": dict(provinces.most_common(4)), "styles": dict(styles.most_common(4)),
                        "span": [min(y[0] for y in years), max(y[1] for y in years)] if years else None,
                        "examples": signed[:6]})
    ov = _overview(fp)
    proposals = sorted((x for x in ov["stones"] if x["status"] == "nytt förslag"),
                       key=lambda x: -(x["alternative"] or {}).get("strength", 0))[:12]
    famous = []
    for sg, name in (("Ög 136", "Rökstenen"), ("Öl 1", "Karlevistenen"), ("Vg 119", "Sparlösastenen"),
                     ("Sö 179", "Gripsholmsstenen"), ("U 337", "Granbystenen")):
        r = s.get(sg)
        if r:
            famous.append({"signum": sg, "name": name, "place": r["place"], "carver": r["carver_raw"] or None,
                           "style": r["style"], "dating": r["dating"], "translation": r.get("translation_en") or ""})
    return {"carvers": carvers, "categories": _categories()["categories"], "famous": famous,
            "proposals": [{"signum": x["signum"], "place": x["place"], "carver": x["alternative"]["carver"],
                           "strength": x["alternative"]["strength"]} for x in proposals],
            "source": "Samnordisk runtextdatabas (Rundata), ristare och stilgrupper; perioder enligt Gräslund (1998)."}


@router.post("/interpret")
def interpret_finding(finding: dict):
    """Ett resonemang för ett fynd i Forskningsluckor: belägg, p-värde, språkdrag, bergart, nyare källor och de andra
    metodernas besked om samma ristare vägs samman (METHODS.md 14d)."""
    from fastapi import HTTPException
    from src import interpretation, stone_overview
    rec = store().get(finding.get("signum") or "")
    if not rec:
        raise HTTPException(status_code=404, detail="Stenen finns inte i Rundata.")
    ctx, _ = _overview_context(_fp())
    profile = stone_overview.stone(rec, ctx, detail=True) if gaps.is_runestone(rec) else None
    return interpretation.interpret(finding, rec, ctx, profile)


@router.get("/archive")
def archive():
    """Runologiskt arkiv: ristare, syften och kända stenar ur data (inte handskrivna sammanfattningar)."""
    return _archive(_fp())


@router.get("/categories")
def inscription_categories():
    """Inskrifternas syfte och innehåll per ristare, med test mot genomsnittet."""
    return _categories()


@lru_cache(maxsize=1)
def _coverage() -> dict:
    return {row["code"]: row for row in gaps.coverage(store().inscriptions, set())["per_province"]}


@lru_cache(maxsize=1)
def _priorities() -> list[dict]:
    return gaps.measurement_priorities(store().inscriptions, set())


def stone_context(signum: str, candidates: list[str] | None = None) -> dict | None:
    """Allt Forskningsluckor vet om en sten: landskapets täckning, stenens luckor i Rundata, om den finns bland
    hypoteserna, omprövningarna eller mätprioriteringarna, appens resultat mot forskningen, inskriftens syfte och –
    för de troligaste ristarna – hur ofta de ristade i stenens stilgrupp och inskriftstyp."""
    from src.inscription_types import CATEGORIES, categories
    from src.synthesis import carver_styles

    s = store()
    rec = s.get(signum)
    if not rec:
        return None
    code = gaps.province(rec)
    cov = _coverage().get(code)
    status = {
        "runestone": gaps.is_runestone(rec),
        "carver": gaps.has_carver(rec), "carver_text": rec.get("carver_raw") or "",
        "style": gaps.has_style(rec), "style_text": rec.get("style") or "",
        "style_uncertain": bool(rec.get("style_uncertain")) or rec.get("style") == "?",
        "uncertain_interpretation": gaps.uncertain_interpretation(rec),
        "dated_by_year": gaps.is_dated_by_year(rec), "lost": rec["flags"]["lost"],
    }
    hyp = _hypotheses()
    as_hypothesis = next((h for h in hyp["new"] if h["signum"] == rec["signum"]), None)
    as_reconsider = next((h for h in hyp["reconsider"] if h["signum"] == rec["signum"]), None)
    priorities = [{"carver": p["carver"], "inscriptions": p["inscriptions"], "measured": p["measured"]}
                  for p in _priorities() if any(x["signum"] == rec["signum"] for x in p["suggestions"])]
    findings_here = [{k: f[k] for k in ("method", "verdict", "ours", "existing", "assessment", "score", "suggested")}
                     for f in _orthographic_findings() if f["signum"] == rec["signum"]]

    cat_stats = _categories()
    base = {c["key"]: c for c in cat_stats["categories"]}
    cats = categories(rec)
    purpose = [{"key": k, "label": CATEGORIES[k][0], "definition": CATEGORIES[k][1],
                "base_rate": base[k]["base_rate"], "count": base[k]["count"]} for k in cats]

    rows = {r["carver"]: r for r in cat_stats["carvers"]}
    carvers = []
    for name in candidates or []:
        st = carver_styles(rec, name, s.inscriptions)
        n_style = sum(st["styles"].values())
        k_style = st["styles"].get(rec.get("style") or "", 0)
        row = rows.get(name)
        carvers.append({
            "carver": name, "style": rec.get("style"), "style_k": k_style, "style_n": n_style,
            "style_share": round(k_style / n_style, 3) if n_style else None, "styles": st["styles"],
            "categories": [{"key": k, "label": CATEGORIES[k][0], "k": row["counts"][k]["k"], "n": row["n"],
                            "share": row["counts"][k]["share"], "direction": row["counts"][k]["direction"],
                            "p_zero": row["counts"][k]["p_zero"]} for k in cats] if row else [],
        })
    return {
        "signum": rec["signum"], "province": {"code": code, "name": gaps.PROVINCE_NAMES.get(code, code), **(cov or {})},
        "status": status, "hypothesis": as_hypothesis, "reconsider": as_reconsider, "priorities": priorities,
        "findings": findings_here, "purpose": purpose, "carvers": carvers, "source_note": gaps.SOURCE_NOTE,
    }


@router.get("/stone/{signum:path}")
def research_stone(signum: str, candidates: str = ""):
    """Forskningsläget för en sten (Forskningsluckor), med inskriftens syfte och kandidaternas stil och inskriftstyper."""
    from fastapi import HTTPException
    ctx = stone_context(signum, [c.strip() for c in candidates.split(",") if c.strip()])
    if ctx is None:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.")
    return ctx
