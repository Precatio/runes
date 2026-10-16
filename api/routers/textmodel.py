"""Sannolikhetsmodellen för en inskrift (src/textmodel.py): läsning, ifyllning av förlorade runor, datering ur
språket och översättningsutkast."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.errors import server_error
from src import textmodel

router = APIRouter()


class Traces(BaseModel):
    # gap number → for each lost rune of the gap the runes its visible remains allow ("" or null: nothing visible)
    allowed: dict[int, list[str | None]]


@router.post("/traces/{signum:path}")
def read_with_traces(signum: str, body: Traces):
    """Läser om inskriften med det som syns av de förlorade runorna (sparas inte)."""
    return _read(signum, {k: v for k, v in body.allowed.items()})


@router.get("/{signum:path}")
def read(signum: str):
    """Modellens läsning av inskriften; den första beräkningen tar upp till en minut, sedan sparas den."""
    return _read(signum, None)


def _read(signum: str, allowed):
    try:
        return textmodel.analyze(signum, allowed)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.")
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(e, "Sannolikhetsmodellen kunde inte läsa inskriften.")
