"""Runformer (METHODS.md 12): ett runutsnitt normaliseras och beskrivs med en formvektor (src/graphemes.py), så att
utsnitt kan jämföras efter form. AI-bedömningen av stilgrupp (/analyze) togs bort 2026-10-20: i ett prov på 57 stenar
med säker stilgrupp träffade den exakta gruppen i 35 % av fallen (utdata/stilgrupp_ai). AI-markeringen av runor
(/detect_runes) togs bort samma dag."""
from api.errors import server_error
from api.uploads import decode_base64_image
from src import graphemes
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ExtractFeaturesRequest(BaseModel):
    image_base64: str


class ExtractFeaturesResponse(BaseModel):
    feature_vector: list[float]
    form_png: str
    aspect: float
    feature_version: str


@router.post("/extract_features", response_model=ExtractFeaturesResponse)
def extract_features(request: ExtractFeaturesRequest):
    """Normaliserad runform och formbeskrivning för jämförelse av runutsnitt (se src/graphemes.py)."""
    image_bytes = decode_base64_image(request.image_base64)
    try:
        return ExtractFeaturesResponse(**graphemes.extract(image_bytes))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise server_error(e, "Fel vid beskrivning av runformen.") from e
