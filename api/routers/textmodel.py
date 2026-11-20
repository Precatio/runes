"""Sannolikhetsmodellen för en inskrift (src/textmodel.py): läsning, ifyllning av förlorade runor, datering ur
språket och översättningsutkast."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import require_admin

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


@router.get("/candidates/{signum:path}")
def gap_candidates(signum: str, gap: int = 0, n: int | None = None, kind: str = "gap", limit: int = 200):
    """Alla kandidater som modellen prövar i en lucka (src/textmodel_overview.py), inte bara de bästa: fyllningen,
    ordet, sannolikheten i sammanhanget (kalibrerad som appens förslag), beläggen i korpusen och varifrån kandidaten
    kom. n: ett annat antal förlorade runor än Rundatas; kind 'open': en av de längre luckor som läsningen lämnar
    öppna. Första beräkningen tar några sekunder, sedan sparas den."""
    from src import textmodel_overview
    signum = canonical(signum)
    try:
        return textmodel_overview.overview(signum, gap, n=n, kind=kind, limit=limit)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.") from None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None
    except Exception as e:
        raise server_error(e, "Sannolikhetsmodellen kunde inte pröva luckans kandidater.") from e


class Evidence(BaseModel):
    kind: str  # sri, skanning, runor2020, annat
    ref: str = Field(max_length=500)


class NewFill(BaseModel):
    signum: str
    gap: int
    kind: str = "gap"
    n: int | None = None
    fill: str = Field(max_length=12)
    method: str = "sannolikhetsmodellen"
    status: str = "förslag"
    comment: str = Field(max_length=2000)
    evidence: list[Evidence] = []


class FillStatus(BaseModel):
    status: str
    comment: str = Field(max_length=2000)
    evidence: list[Evidence] = []


@router.get("/fills")
def list_fills(signum: str | None = None):
    """Vitkis ifyllningar (src/vitki_fills.py, data/vitki_ifyllningar.json): förslag och bekräftade, för en sten
    eller alla. Ett eget lager ovanpå Rundata, som inte ändras."""
    from src import vitki_fills as vf
    data = vf.load()
    sig = canonical(signum) if signum else None
    xs = [x for x in data["fills"] if x["status"] in vf.SHOWN and (sig is None or x["signum"] == sig)]
    return {"license": data.get("licens", vf.LICENSE), "fills": [{**x, "label": vf.label(x)} for x in xs]}


@router.post("/fills")
def save_fill(body: NewFill, user: dict = Depends(require_admin)):
    """Sparar en ifyllning som förslag eller bekräftad (bara admin). Luckan och sannolikheten hämtas på servern ur
    modellens överblick, så att proveniensen inte kan skrivas om av anropet."""
    from src import textmodel_overview as ov
    from src import vitki_fills as vf
    signum = canonical(body.signum)
    try:
        gap = ov.locate(signum, body.gap, n=body.n, kind=body.kind)
        row = ov.candidate(signum, body.gap, body.fill, n=body.n, kind=body.kind)
        if body.method == "sannolikhetsmodellen" and row is None:
            raise ValueError("Modellen prövade inte den ifyllningen i luckan.")
        entry = {"signum": signum, "gap": gap, "fill": body.fill, "method": body.method, "status": body.status,
                 "comment": body.comment, "evidence": [e.model_dump() for e in body.evidence],
                 "word": row["word"] if row else None, "name": bool(row and row["name"]),
                 "model_version": textmodel.VERSION if body.method == "sannolikhetsmodellen" else None,
                 "p": row["p_word"] if (row and body.method == "sannolikhetsmodellen") else None,
                 "p_model": row["p_model"] if (row and body.method == "sannolikhetsmodellen") else None}
        rec = vf.add(entry, user)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.") from None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None
    return {**rec, "label": vf.label(rec)}


@router.post("/fills/{fill_id}/status")
def fill_status(fill_id: str, body: FillStatus, user: dict = Depends(require_admin)):
    """Byter status på en ifyllning (förslag, bekräftad, avvisad) med kommentar; historiken sparas (bara admin)."""
    from src import vitki_fills as vf
    try:
        rec = vf.set_status(fill_id, body.status, user, body.comment, [e.model_dump() for e in body.evidence])
    except KeyError:
        raise HTTPException(status_code=404, detail="Ifyllningen finns inte.") from None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None
    return {**rec, "label": vf.label(rec)}


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
