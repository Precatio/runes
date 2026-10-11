from api import llm
from api.errors import ai_error, server_error
from api.uploads import read_image_upload, decode_base64_image
from src import graphemes
from src.styles import STYLE_GROUPS
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Literal
from dotenv import load_dotenv

load_dotenv()  # .env for local development; the server's own environment wins

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


class RuneBox(BaseModel):
    translit: str
    box_2d: list[int]
    confidence: int


class RuneDetection(BaseModel):
    """Schema for the automatic search for the individual runes in an image."""
    runes: list[RuneBox]
    note: str


class RuneDetectionResponse(RuneDetection):
    tokens_used: int = 0
    model: str = ""


RUNE_DETECTION_INSTRUCTION = """
Du är en runolog som markerar runorna i en bild av en runsten (foto, relief eller ristningskarta).

Uppgift: hitta VARJE enskild runa i ristningen och ange en tät ruta runt den.
- En ruta per runa, i den ordning runorna läses (följ runslingan).
- Rutan ska omsluta hela runan – huvudstaven och alla bistavar – men så lite som möjligt utanför.
- Ta INTE med ornamentik (rundjurets kropp, huvud, svans, ormöglor), kors, ramlinjer eller skiljetecken.
- Ange rutan som box_2d = [ymin, xmin, ymax, xmax], normaliserad till 0–1000 i förhållande till hela bilden.
- translit: runan translittererad som i Samnordisk runtextdatabas (f u þ o r k h n i a s t b m l R; stungna runor e g d y p).
  Skriv ? om runan inte går att bestämma.
- confidence: 0–100, hur säker du är på att rutan är en runa och på translittereringen. Var försiktig: en skadad eller
  otydlig runa ska ha låg säkerhet.
- note: en kort kommentar om bilden (t.ex. vilka delar som inte går att läsa).

Hitta hellre färre runor med rätt rutor än många osäkra. Svara EXAKT enligt det angivna JSON-schemat.
"""


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
def analyze_2d_image(file: UploadFile = File(...), ai: llm.AIContext = Depends(llm.ai_context)):
    contents = read_image_upload(file)
    try:
        r = llm.generate(ai, "Analysera denna runsten paleografiskt och epigrafiskt.", system=SYSTEM_INSTRUCTION,
                         images=[(contents, file.content_type or "image/jpeg")], schema=TwoDAIResult, tier="pro")
        return TwoDAnalysisResponse(**r.data, tokens_used=r.tokens, model=r.model)
    except HTTPException:
        raise
    except Exception as e:
        raise ai_error(e)


@router.post("/detect_runes", response_model=RuneDetectionResponse)
def detect_runes(file: UploadFile = File(...), ai: llm.AIContext = Depends(llm.ai_context)):
    """Rutor runt de enskilda runorna i bilden (AI-bedömning), för att spara dem som runutsnitt. Rutorna är okalibrerade
    och ska granskas; för ristningskartor från 3D-analysen används i stället de runor analysen själv känt igen."""
    contents = read_image_upload(file)
    try:
        r = llm.generate(ai, "Markera de enskilda runorna i bilden.", system=RUNE_DETECTION_INSTRUCTION,
                         images=[(contents, file.content_type or "image/jpeg")], schema=RuneDetection, tier="pro")
        runes = [x for x in r.data.get("runes", []) if len(x.get("box_2d") or []) == 4]
        for x in runes:  # keep the boxes inside the image and in order
            y0, x0, y1, x1 = (max(0, min(1000, int(v))) for v in x["box_2d"])
            x["box_2d"] = [min(y0, y1), min(x0, x1), max(y0, y1), max(x0, x1)]
        runes = [x for x in runes if x["box_2d"][2] - x["box_2d"][0] >= 5 and x["box_2d"][3] - x["box_2d"][1] >= 3]
        return RuneDetectionResponse(runes=runes, note=r.data.get("note", ""), tokens_used=r.tokens, model=r.model)
    except HTTPException:
        raise
    except Exception as e:
        raise ai_error(e, "Kunde inte hitta runorna i bilden.")


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
