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
    return rec


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
):
    return store().search(q=q, carver=carver, style=style, period=period or "", province=province,
                          has_coords=has_coords, limit=limit, offset=offset, gap=gap, signa=signa)


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


@router.get("/geo")
def geo():
    return {"fields": ["signum", "lat", "lon", "period", "style", "carvers", "lost"], "rows": store().geo()}
