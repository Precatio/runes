"""Ortografisk stilometri över Rundatas vikingatida inskrifter."""
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from api.rundata import store
from src.orthography import OrthographyModel

router = APIRouter()


@lru_cache(maxsize=1)
def model() -> OrthographyModel:
    return OrthographyModel(store().inscriptions)


def _signum(signum: str) -> str:
    rec = store().get(signum)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.")
    if rec["signum"] not in model().index:
        raise HTTPException(
            status_code=422,
            detail="Inskriften ingår inte i den ortografiska analysen (kräver vikingatida inskrift "
                   "med minst fem läsbara ord).",
        )
    return rec["signum"]


@router.get("/evaluation")
def evaluation():
    return model().evaluate()


@router.get("/profile/{signum:path}")
def profile(signum: str):
    return model().profile(_signum(signum))


@router.get("/similar/{signum:path}")
def similar(signum: str, limit: int = Query(10, ge=1, le=50)):
    return model().similar(_signum(signum), limit)


@router.get("/carvers/{signum:path}")
def carvers(signum: str, limit: int = Query(10, ge=1, le=30)):
    return {**model().rank_carvers(_signum(signum), limit), "evaluation": model().evaluate()}
