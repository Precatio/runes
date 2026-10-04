"""Statistik över huggspårsmätningar: jämförelse, klustring och korpusbaserad attribuering."""
from typing import Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.rundata import store
from src.stats import METRICS, attribute, compare_stones, summarize_slices, ward_clustering

router = APIRouter()


class Stone(BaseModel):
    label: str
    signum: Optional[str] = None
    feature_type: Optional[str] = None
    slices: list[dict] = Field(default_factory=list)
    means: Optional[dict] = None


class CompareRequest(BaseModel):
    a: Stone
    b: Stone


class ClusterRequest(BaseModel):
    stones: list[Stone]


class AttributeRequest(BaseModel):
    query: Stone
    reference: list[Stone]
    min_per_carver: int = 2


def _means(stone: Stone) -> Optional[list[float]]:
    src = stone.means
    if not src and stone.slices:
        src = {m: float(np.mean([s[m] for s in stone.slices if s.get(m) is not None])) for m in METRICS}
    if not src or any(src.get(m) is None for m in METRICS):
        return None
    return [float(src[m]) for m in METRICS]


def carver_label(signum: Optional[str]) -> Optional[str]:
    """Ristare enligt Rundata, om exakt en säker signerad/attribuerad ristare finns."""
    if not signum:
        return None
    rec = store().get(signum)
    if not rec:
        return None
    cs = [c for c in rec["carvers"] if c["kind"] in ("S", "A") and not c["uncertain"]]
    return cs[0]["name"] if len(cs) == 1 else None


class SummarizeRequest(BaseModel):
    slices: list[dict]
    meta_stone: str = "Granit"
    meta_weathering: str = "Låg"


@router.post("/summarize")
def summarize(req: SummarizeRequest):
    """Sammanfattning (medel, SD, n, 95 % KI) och verktygsheuristik för ett urval snitt."""
    from api.routers.threed import tool_heuristic

    slices = [s for s in req.slices if all(isinstance(s.get(m), (int, float)) for m in METRICS)]
    if not slices:
        raise HTTPException(status_code=400, detail="Urvalet innehåller inga mätbara snitt.")
    summary = summarize_slices(slices)
    means = {m: summary[m]["mean"] for m in METRICS}
    return {"summary": summary, "means": means, "n": len(slices),
            "tool_heuristic": tool_heuristic(means["apex_vinkel_deg"], req.meta_stone, req.meta_weathering)}


@router.post("/compare")
def compare(req: CompareRequest):
    if len(req.a.slices) < 2 or len(req.b.slices) < 2:
        raise HTTPException(status_code=400, detail="Varje sten behöver minst två snitt för att kunna jämföras.")
    result = compare_stones(req.a.slices, req.b.slices)
    warnings = []
    if req.a.feature_type and req.b.feature_type and req.a.feature_type != req.b.feature_type:
        warnings.append("Stenarna jämförs med olika typer av spår (runa/ornamentik). "
                        "Runor och ornamentik huggs ofta olika och bör jämföras var för sig.")
    return {**result, "a": req.a.label, "b": req.b.label, "warnings": warnings}


@router.post("/cluster")
def cluster(req: ClusterRequest):
    rows, labels = [], []
    for s in req.stones:
        m = _means(s)
        if m:
            rows.append(m)
            labels.append(s.label)
    if len(rows) < 3:
        raise HTTPException(status_code=400, detail="Minst tre stenar med fullständiga mätvärden krävs.")
    return {**ward_clustering(labels, np.array(rows)),
            "method": "Ward, euklidiska avstånd på standardiserade medelvärden per sten"}


@router.post("/attribute")
def attribute_endpoint(req: AttributeRequest):
    q = _means(req.query)
    if not q:
        raise HTTPException(status_code=400, detail="Stenen saknar fullständiga mätvärden.")
    reference, skipped = [], 0
    for s in req.reference:
        # Stenen själv får inte ingå i sin egen referens
        if req.query.signum and s.signum and store().get(s.signum) is store().get(req.query.signum):
            continue
        if req.query.feature_type and s.feature_type and s.feature_type != req.query.feature_type:
            continue
        label = carver_label(s.signum)
        m = _means(s)
        if not label or not m:
            skipped += 1
            continue
        reference.append({"group": label, "label": s.label, "values": m})
    result = attribute(reference, q, min_per_group=req.min_per_carver)
    return {
        **result,
        "reference_size": len(reference),
        "skipped_unlabelled": skipped,
        "labels_from": "Rundata (endast säkra signerade/attribuerade inskrifter med en ristare)",
        "metrics": METRICS,
    }
