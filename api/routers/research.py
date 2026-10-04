"""Forskningsluckor och prioriteringar."""
from functools import lru_cache

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.rundata import store
from api.routers.orthography import model as orthography_model
from src import findings, research_gaps as gaps

router = APIRouter()


class GapsRequest(BaseModel):
    measured_signa: list[str] = Field(default_factory=list)


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
    # Corpus entries ({signum, feature_type, means}) and AI style assessments from the user's projects
    corpus: list[dict] = Field(default_factory=list)
    styles: list[dict] = Field(default_factory=list)


@lru_cache(maxsize=1)
def _orthographic_findings() -> tuple:
    m, s = orthography_model(), store()
    return tuple(findings.add_extras(findings.orthographic_findings(m, s.inscriptions), s.get, s.inscriptions, m.names))


@router.post("/findings")
def research_findings(req: FindingsRequest):
    """Appens resultat mot Rundata: stämmer, nytt eller motsäger – med en öppet redovisad uppskattning."""
    s = store()
    technique, technique_note = findings.technique_findings(req.corpus, s.get, s.inscriptions)
    extra = findings.add_extras(technique + findings.style_findings(req.styles, s.get, s.inscriptions),
                                s.get, s.inscriptions, orthography_model().names)
    items = list(_orthographic_findings()) + extra
    items.sort(key=lambda f: -f["score"])
    return {
        "findings": items,
        "summary": findings.summarize(items),
        "technique_note": technique_note,
        "method_note": findings.__doc__.split("\n\n", 1)[1].strip(),
        "source_note": gaps.SOURCE_NOTE,
    }


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
        out["comparison"] = compare(t, carver_profile(carver, store().inscriptions, certain_carvers, names,
                                                      exclude=rec["signum"]))
    return out


@lru_cache(maxsize=1)
def _categories() -> dict:
    from src.inscription_types import carver_categories
    from src.research_gaps import certain_carvers
    return carver_categories(store().inscriptions, certain_carvers)


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
