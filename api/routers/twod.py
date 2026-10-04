from api.config import GEMINI_PRO_MODEL
from api.errors import ai_error, server_error
from api.uploads import read_image_upload, decode_base64_image
from src import graphemes
from src.styles import STYLE_GROUPS
from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from pydantic import BaseModel
from typing import Literal, Optional
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv(override=True)

router = APIRouter()

class Marker(BaseModel):
    label: str
    description: str
    polygon: list[list[int]]

StyleCode = Literal["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5", "Osäker"]


class TwoDAIResult(BaseModel):
    """Schema the model must follow (the style code is restricted to Gräslund's groups)."""
    predicted_style: StyleCode
    confidence: int
    reasoning: str
    rune_types: str
    markers: list[Marker]


class TwoDAnalysisResponse(TwoDAIResult):
    tokens_used: int = 0
    model: str = ""


class ExtractFeaturesRequest(BaseModel):
    image_base64: str


class ExtractFeaturesResponse(BaseModel):
    feature_vector: list[float]
    form_png: str
    aspect: float
    feature_version: str

STYLE_REFERENCE = "\n".join(
    f"- {g['code']}: {g['features']}" + (f" (ca {g['from']}–{g['to']})" if g["from"] else "")
    for g in STYLE_GROUPS if g["code"] != "KB"
)

SYSTEM_INSTRUCTION = """
Du är en expert-runolog och epigrafiker som specialiserar sig på paleografi och ornamentik på svenska runstenar.
I din stilanalys (ornamentik) utgår du ifrån Anne-Sofie Gräslunds kronologiska metoder.
Din uppgift är att analysera en uppladdad 2D-bild (ett foto eller en uppmålning) av en runsten.

Du måste identifiera vilken av Anne-Sofie Gräslunds stilgrupper (RAK, Fp, Pr1, Pr2, Pr3, Pr4, Pr5) som stenen med störst sannolikhet tillhör.
Använd koderna exakt så (RAK, Fp, Pr1–Pr5). Om bilden inte visar ornamentik som går att bedöma, svara "Osäker". Referens (ungefärliga dateringar som överlappar):
""" + STYLE_REFERENCE + """
Om bilden innehåller ett rundjur med huvud är det ALDRIG Rak. Var noggrann och variera din bedömning baserat på faktiska visuella bevis i bilden. Undvik att defaulta till Rak.

Din uppskattning genererar även en procentsats (confidence). Den visas som en okalibrerad självskattning. Ange ett realistiskt värde (t.ex. 40-90%) baserat på bildens tydlighet, var inte överdrivet säker (95%) om bilden är suddig eller svårtolkad.

I fältet "reasoning" (Epigrafisk motivering) MÅSTE du vara mycket utförlig. Analysera eventuella drakhuvuden, ögonform, fotflikar och bandens dragning grundligt, eller avsaknaden av dessa.

Du måste även identifiera runtyperna som används på stenen. I fältet "rune_types" beskriv de distinkta paleografiska dragen.

När du identifierar nyckeldetaljer (t.ex. drakhuvud, svans, rakt bandavslut, specifik runa), inkludera dessa i "markers"-listan. 
Du SKA sträva efter att inkludera så många relevanta markörer som möjligt (gärna 5-10 stycken om bilden tillåter) för att bygga ett massivt och detaljerat visuellt bevis för din bedömning. Markera ögon, öron, nosflikar, fötter, svansar, ormöglor, kors och särpräglade runor separat.
För varje markör (marker), ange en 'label' (t.ex. "Drakhuvud - Mandelformat öga"), en mycket djupgående och detaljerad 'description' (t.ex. "Ett tydligt mandelformat öga med utdragen snibb som är starkt indikativt för stil Pr3, placerat strax bakom nospartiet."), och dess utbredning i 'polygon' med en lista av koordinater i formatet [[y1, x1], [y2, x2], ...] normaliserat till 0-1000. Sätt ut tillräckligt med punkter (minst 4, men gärna fler) så att polygonen noggrant följer den visuella formen du markerar istället för att bara vara en inexakt rektangel.
Exempel på polygon: [[150, 200], [150, 400], [250, 420], [300, 400], [300, 200]] för en mer oregelbunden form.

Du måste svara EXAKT enligt det angivna JSON-schemat.
"""

@router.post("/analyze", response_model=TwoDAnalysisResponse)
def analyze_2d_image(
    file: UploadFile = File(...),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key")
):
    api_key = x_gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=401, detail="Gemini API Key is missing.")
        
    client = genai.Client(api_key=api_key)
    
    # Läs fil och konvertera till base64/bytes
    contents = read_image_upload(file)
    
    try:
        response = client.models.generate_content(
            model=GEMINI_PRO_MODEL,
            contents=[
                types.Part.from_bytes(data=contents, mime_type=file.content_type or "image/jpeg"),
                types.Part.from_text(text="Analysera denna runsten paleografiskt och epigrafiskt.")
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=TwoDAIResult,
            )
        )
        # GenAI client automatically parses JSON to string if schema is provided, but since we specified response_schema it should be a JSON string we can just return (FastAPI will parse and validate via response_model).
        import json
        data = json.loads(response.text)
        data["tokens_used"] = response.usage_metadata.total_token_count if getattr(response, "usage_metadata", None) else 0
        data["model"] = GEMINI_PRO_MODEL
        return TwoDAnalysisResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        raise ai_error(e)

@router.post("/extract_features", response_model=ExtractFeaturesResponse)
def extract_features(request: ExtractFeaturesRequest):
    """Normaliserad runform och formbeskrivning för jämförelse av runutsnitt (se src/graphemes.py)."""
    image_bytes = decode_base64_image(request.image_base64)
    try:
        return ExtractFeaturesResponse(**graphemes.extract(image_bytes))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise server_error(e, "Fel vid beskrivning av runformen.")
