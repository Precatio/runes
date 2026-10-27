"""Sannolikhetsmodellen för en inskrift (src/textmodel.py): läsning, ifyllning av förlorade runor, datering ur
språket och översättningsutkast."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.errors import server_error
from src import textmodel

router = APIRouter()


def canonical(signum: str) -> str:
    """Rundata's own form of a signum, so that "sö113" or "SÖ 113" reads Sö 113 (as the Rundata lookup does); the input
    as it is when Rundata does not have it."""
    from api.rundata import store
    rec = store().get(signum)
    return rec["signum"] if rec else signum.strip()


class Traces(BaseModel):
    # gap number → for each lost rune of the gap the runes its visible remains allow ("" or null: nothing visible)
    allowed: dict[int, list[str | None]]


@router.post("/traces/{signum:path}")
def read_with_traces(signum: str, body: Traces):
    """Läser om inskriften med det som syns av de förlorade runorna (sparas inte)."""
    return _read(signum, {k: v for k, v in body.allowed.items()})


@router.get("/scantraces/{signum:path}")
def scan_traces(signum: str):
    """Spårläsarens förslag ur 3D-skanningen för inskriftens luckor (src/trace_reader.py). Bara förslag: panelen
    visar vad skannern ser, och spåren räknas först när användaren bekräftar dem (POST /traces)."""
    from src import trace_reader
    try:
        return trace_reader.proposals(canonical(signum))
    except Exception as e:
        raise server_error(e, "Spårläsaren kunde inte läsa skanningen.") from e


@router.get("/{signum:path}")
def read(signum: str):
    """Modellens läsning av inskriften; den första beräkningen tar upp till en minut, sedan sparas den."""
    return _read(signum, None)


def _read(signum: str, allowed):
    signum = canonical(signum)
    try:
        return textmodel.analyze(signum, allowed)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.") from None
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(e, "Sannolikhetsmodellen kunde inte läsa inskriften.") from e
