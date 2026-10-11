from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.rundata import ATTRIBUTION_NOTE, store
from src.styles import SOURCE as STYLE_SOURCE, STYLE_GROUPS

router = APIRouter()


@router.get("/meta")
def meta():
    s = store()
    return {**s.meta, "note": ATTRIBUTION_NOTE}


@router.get("/inscription/{signum:path}")
def inscription(signum: str):
    rec = store().get(signum)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.")
    from src import stone_dimensions
    dims = stone_dimensions.lookup(rec["signum"])
    if dims:
        dims = {**dims, "in_province": stone_dimensions.province_percentile(rec["signum"], lambda s: s.split(" ")[0])}
    return {**rec, "dimensions": dims}


@router.get("/search")
def search(
    q: str = "",
    carver: str = "",
    style: str = "",
    period: Optional[str] = Query(None, pattern="^[UVM]$"),
    province: str = "",
    has_coords: bool = False,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    gap: str = Query("", pattern="^(|runestone|carver|no_carver|style|no_style|dated|uncertain_interpretation|lost)$"),
    signa: str = Query("", max_length=20000),  # comma-separated, e.g. the measured stones
    category: str = Query("", pattern="^(|minne|sjalvminne|bro_vag|kristen|fard|arv|ting|magisk|grans)$"),
    certain: bool = False,
):
    return store().search(q=q, carver=carver, style=style, period=period or "", province=province,
                          has_coords=has_coords, limit=limit, offset=offset, gap=gap, signa=signa,
                          category=category, certain=certain)


@router.get("/find")
def find_in_text(text: str = Query(..., max_length=2000)):
    """Hittar signum i fri text, t.ex. ett filnamn som 'U_11_mesh.obj'."""
    return [{"signum": r["signum"], "place": r["place"]} for r in store().find_in_text(text)]


@router.get("/carvers")
def carvers():
    return store().carvers()


@router.get("/styles")
def styles():
    return {"groups": STYLE_GROUPS, "source": STYLE_SOURCE, "distribution": store().style_stats()}


# Signum prefixes outside Sweden that occur on the map
OTHER_REGIONS = {"N": "Norge", "DR": "Danmark", "IS": "Island", "GR": "Grönland", "Or": "Orkney", "Sh": "Shetland",
                 "IM": "Isle of Man", "E": "England", "Sc": "Skottland", "Ir": "Irland", "FI": "Finland",
                 "By": "Bysans", "Fær": "Färöarna"}


@router.get("/geo")
def geo():
    """Inskrifter med koordinater för kartan, med etiketter för landskap, innehåll och språkdrag."""
    from src.inscription_types import CATEGORIES
    from src.language_profile import TRAITS
    from src.research_gaps import PROVINCE_NAMES
    return {"fields": ["signum", "lat", "lon", "period", "style", "carvers", "lost", "province", "object",
                       "material", "cross", "carver_status", "categories", "runestone"],
            "rows": store().geo(),
            "provinces": {**OTHER_REGIONS, **PROVINCE_NAMES},
            "categories": {k: v[0] for k, v in CATEGORIES.items()},
            "traits": {k: {"group": v[0], "label": v[1]} for k, v in TRAITS.items()}}


@router.get("/geo/trait/{key}")
def geo_trait(key: str):
    """Ett språkdrag för alla inskrifter med koordinater: värdet per signum och hur vanligt varje värde är."""
    from collections import Counter
    from api.routers.orthography import model as orthography_model
    from src.language_profile import TRAITS, traits
    if key not in TRAITS:
        raise HTTPException(status_code=404, detail=f"Okänt språkdrag: {key}")
    names = orthography_model().names
    rows = {}
    for r in store().inscriptions:
        if r["lat"] is not None:
            v = traits(r, names).get(key)
            if v:
                rows[r["signum"]] = v
    return {"key": key, "label": TRAITS[key][1], "definition": TRAITS[key][2],
            "values": dict(Counter(rows.values()).most_common()), "rows": rows}


@router.get("/geo/match")
def geo_match(q: str = Query(..., min_length=2, max_length=100)):
    """Signum för inskrifter med koordinater där texten (translitterering, normalisering, översättning), platsen
    eller socknen innehåller söktexten."""
    return {"q": q, "signa": store().text_matches(q)}
