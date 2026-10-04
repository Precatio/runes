from api.config import GEMINI_PRO_MODEL
from api.errors import ai_error, server_error
from api.uploads import read_image_upload, decode_base64_image
from src.styles import STYLE_GROUPS
from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from pydantic import BaseModel
from typing import Optional
from google import genai
from google.genai import types
import os
import numpy as np
import cv2
from skimage.feature import hog
from dotenv import load_dotenv

load_dotenv(override=True)

router = APIRouter()

class Marker(BaseModel):
    label: str
    description: str
    polygon: list[list[int]]

class TwoDAnalysisResponse(BaseModel):
    predicted_style: str
    confidence: int
    reasoning: str
    rune_types: str
    markers: list[Marker]
    tokens_used: int = 0

class ExtractFeaturesRequest(BaseModel):
    image_base64: str
    
class ExtractFeaturesResponse(BaseModel):
    feature_vector: list[float]

STYLE_REFERENCE = "\n".join(
    f"- {g['code']}: {g['features']}" + (f" (ca {g['from']}–{g['to']})" if g["from"] else "")
    for g in STYLE_GROUPS if g["code"] != "KB"
)

SYSTEM_INSTRUCTION = """
Du är en expert-runolog och epigrafiker som specialiserar sig på paleografi och ornamentik på svenska runstenar.
I din stilanalys (ornamentik) utgår du ifrån Anne-Sofie Gräslunds kronologiska metoder.
Din uppgift är att analysera en uppladdad 2D-bild (ett foto eller en uppmålning) av en runsten.

Du måste identifiera vilken av Anne-Sofie Gräslunds stilgrupper (RAK, Fp, Pr1, Pr2, Pr3, Pr4, Pr5) som stenen med störst sannolikhet tillhör.
Använd koderna exakt så (RAK, Fp, Pr1–Pr5). Referens (ungefärliga dateringar som överlappar):
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
async def analyze_2d_image(
    file: UploadFile = File(...),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key")
):
    api_key = x_gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=401, detail="Gemini API Key is missing.")
        
    client = genai.Client(api_key=api_key)
    
    # Läs fil och konvertera till base64/bytes
    contents = await read_image_upload(file)
    
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
                response_schema=TwoDAnalysisResponse,
            )
        )
        # GenAI client automatically parses JSON to string if schema is provided, but since we specified response_schema it should be a JSON string we can just return (FastAPI will parse and validate via response_model).
        import json
        data = json.loads(response.text)
        data["tokens_used"] = response.usage_metadata.total_token_count if getattr(response, "usage_metadata", None) else 0
        return TwoDAnalysisResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        raise ai_error(e)

@router.post("/extract_features", response_model=ExtractFeaturesResponse)
async def extract_features(request: ExtractFeaturesRequest):
    try:
        # Strip header if present (e.g., "data:image/jpeg;base64,...")
        image_bytes = decode_base64_image(request.image_base64)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Kunde inte avkoda bilden.")
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Resize to standard size (e.g. 64x64) for consistent HOG features
        resized = cv2.resize(gray, (64, 64))
        
        # Compute HOG features
        # pixels_per_cell=(8,8), cells_per_block=(2,2), orientations=9
        features = hog(resized, orientations=9, pixels_per_cell=(8, 8),
                       cells_per_block=(2, 2), block_norm='L2-Hys', transform_sqrt=True, feature_vector=True)
                       
        # Include aspect ratio as a feature (width / height)
        aspect_ratio = img.shape[1] / max(img.shape[0], 1)
        
        # Combine HOG features with aspect ratio (weighted slightly to be significant)
        feature_vector = features.tolist()
        feature_vector.append(aspect_ratio * 0.5)
        
        return ExtractFeaturesResponse(feature_vector=feature_vector)
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(e, "Fel vid vektorisering.")
