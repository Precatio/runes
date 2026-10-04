from functools import lru_cache

from api.config import GEMINI_PRO_MODEL
from api.errors import ai_error
from api.rundata import store
from api.routers.orthography import model as orthography_model
from api.uploads import decode_base64_image
from src.reading import Lexicon, compare
from src.synthesis import smoothed_precision
from fastapi import APIRouter, HTTPException, Header, Response
from pydantic import BaseModel
from typing import Optional
from google import genai
from google.genai import types
from openai import OpenAI
import os
import json

router = APIRouter()

class PhoneticsRequest(BaseModel):
    image_base64: str
    signum: str = "Okänd"
    region: Optional[str] = None
    epoch: Optional[str] = None
    
class Marker(BaseModel):
    label: str
    description: str
    polygon: list[list[int]]

class LinguisticAI(BaseModel):
    """Det språkmodellen får fylla i. Rundata och jämförelsen läggs till av servern."""
    transliteration: str
    normalization: str
    phonetic_ipa: str
    translation: str
    linguistic_analysis: str
    sound_laws_applied: Optional[list[str]] = None


class PhoneticsResponse(LinguisticAI):
    # Rundatas läsning (fakta ur databasen, inte AI) och den framräknade jämförelsen
    academic_reading: Optional[str] = None
    comparison: Optional[str] = None
    rundata: Optional[dict] = None
    reading_comparison: Optional[dict] = None
    form_check: Optional[dict] = None
    orthography: Optional[dict] = None
    markers: Optional[list[Marker]] = None
    tokens_used: int = 0


@lru_cache(maxsize=1)
def lexicon() -> Lexicon:
    return Lexicon(store().inscriptions)


def reference_checks(signum: str, transliteration: str, normalization: str) -> dict:
    """Allt som räknas fram utan AI: Rundatas läsning, jämförelsen, ordformerna och ortografin."""
    rec = store().get(signum) if signum and signum.lower() not in ("okänd", "okänt") else None
    out: dict = {"rundata": None, "reading_comparison": None, "academic_reading": None, "comparison": None}
    if rec and rec.get("transliteration"):
        out["rundata"] = {k: rec.get(k, "") for k in ("signum", "place", "parish", "transliteration", "normalization",
                                                      "normalization_ows", "translation_en", "style", "dating")}
        out["rundata"]["carvers"] = rec["carvers"]
        out["academic_reading"] = (f"Rundata ({rec['signum']}): {rec['transliteration']} – "
                                   f"{rec.get('normalization', '').replace(chr(34), '')} – ”{rec.get('translation_en', '')}”")
        if transliteration:
            c = compare(transliteration, rec["transliteration"], normalization, rec.get("normalization", ""))
            out["reading_comparison"] = c
            out["comparison"] = c["summary"]
    elif signum and signum.lower() not in ("okänd", "okänt"):
        out["comparison"] = f"Signumet {signum} finns inte i Rundata, eller saknar translitterering – läsningen kan inte jämföras."
    out["form_check"] = lexicon().check(normalization) if normalization else None
    if transliteration:
        m = orthography_model()
        rk = m.rank_text(transliteration, normalization, 5, exclude_signum=rec["signum"] if rec else None)
        per = (m.evaluate() or {}).get("per_carver", {})
        out["orthography"] = {
            "n_words": rk["n_words"], "usable": rk["n_words"] >= 8,
            "ranking": [{**r, "precision": smoothed_precision(per.get(r["carver"]))} for r in rk["ranking"]],
            "note": "Vår läsning jämförd med ristarnas stavning i Rundata (stenen själv utesluten).",
        }
    return out


class CompareRequest(BaseModel):
    signum: str = ""
    transliteration: str = ""
    normalization: str = ""


@router.post("/compare")
def compare_reading(req: CompareRequest):
    """Jämför en (t.ex. manuellt rättad) läsning med Rundata – utan AI."""
    return reference_checks(req.signum, req.transliteration, req.normalization)

@router.post("/analyze", response_model=PhoneticsResponse)
def analyze_phonetics(
    request: PhoneticsRequest,
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key")
):
    try:
        # Use provided key or fallback to env for local dev
        key_to_use = x_gemini_api_key or os.environ.get("GEMINI_API_KEY")
        if not key_to_use:
            raise HTTPException(status_code=401, detail="No Gemini API Key provided")
            
        client = genai.Client(api_key=key_to_use)

        # Extrahera base64 data utan prefixet (data:image/jpeg;base64,...)
        if "," in request.image_base64:
            base64_data = request.image_base64.split(",")[1]
            mime_type = request.image_base64.split(",")[0].split(":")[1].split(";")[0]
        else:
            base64_data = request.image_base64
            mime_type = "image/jpeg"
            
        image_bytes = decode_base64_image(base64_data)
        
        # STEG 1: Blind Läsning
        step1_instruction = """
Du är en extremt strikt epigrafiker och agerar som en "dum OCR-skanner".
Läs ENDAST de runor som är 100% synliga i den bifogade bilden.
Gissa ALDRIG vad som står utanför bildens ramar eller i skadade partier.
Om bilden visar 3 runor, svara med exakt 3 runor.

VIKTIGT: Om det finns en inritad färgstark linje (oftast röd, halvgenomskinlig) i bilden är detta en "läs-väg" från användaren. Du SKA då endast läsa de runor som ligger längs med och i direkt anslutning till denna linje. Följ linjens riktning. Om ingen linje finns, läs runorna i den ordning som är mest logisk för ristningen.

Du måste också identifiera visuellt var du hittar dessa runor/ord. Skapa en "markers"-lista. 
Var extremt noggrann och generera så många markörer som möjligt! Sätt en separat form (polygon) kring VARJE enskilt runord eller tydlig sekvens du lyckas tyda, samt kring specifika visuella detaljer (t.ex. skador, skiljetecken, särpräglade enskilda runor). Sträva efter att ge mycket detaljerade bevis.
För varje markör, ange en 'label' (t.ex. "Runord: kuþ", eller "Skiljetecken: Kors"), en mycket djupgående och detaljerad 'description' (t.ex. "Tydligt inristat i bandet, stungen k-runa (g), u-runa och stungenn th-runa (ð) indikerar ordet Guð. Runorna är djupt huggna."), och dess utbredning i 'polygon' med en lista av koordinater i formatet [[y1, x1], [y2, x2], ...] normaliserat till 0-1000. Använd fler än 4 punkter för att noggrant rama in runornas eller skadans specifika form snarare än en inexakt rektangel.

Svara EXAKT med ett JSON-objekt med två nycklar: "raw_transliteration" (sträng) och "markers" (lista av markörer).
"""
        step1_prompt = "Translitterera de runor som syns i bilden."

        gen1_resp = client.models.generate_content(
            model=GEMINI_PRO_MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                step1_prompt
            ],
            config=types.GenerateContentConfig(
                system_instruction=step1_instruction,
                temperature=0.0,
                response_mime_type="application/json"
            )
        )
        
        step1_parsed = json.loads(gen1_resp.text)
        raw_transliteration = step1_parsed.get("raw_transliteration", "")
        markers_data = step1_parsed.get("markers", [])

        # STEG 2: Lingvistisk Analys & Akademisk Jämförelse
        step2_instruction = """
Du är en specialiserad AI-agent inom svensk runologi, nordisk epigrafik och historisk filologi.
Din uppgift är att ta emot råa eller translittererade runsekvenser från alla svenska runfyndigheter (runstenar, gravhällar, träpinnar, kyrkklockor, metallföremål) och generera en vetenskapligt underbyggd, epokanpassad fonetisk avkodning och flerskiktad tolkning.

---
## 1. EPOKER OCH RUNSYSTEM I SVERIGE (IDENTIFIERINGSRUM)
När du tar emot en inskrift ska du beakta användarens angivna region och epok. Om inget är angivet, försök klassificera vilken av följande fyra huvudepoker inskriften tillhör:
A. Urnordisk tid & Äldre futharken (ca 150 - 800 e.Kr.)
B. Vikingatid & Yngre futharken (ca 800 - 1050 e.Kr.)
C. Medeltid & Stingda runor (ca 1050 - 1500 e.Kr.)
D. Eftermedeltida traditioner & Dalarunor (ca 1500 - 1900-tal)

## 2. ANALYSPIPELINE (STEG-FÖR-STEG)
Steg 1: Epok- & Typologibestämning (inklusive regional särart, e.g. Gutniska ljudlagar)
Steg 2: Ljudlagshärledning (VILKA historiska ljudlagar appliceras? ex. i-omljud, monoftongering). Fyll i listan 'sound_laws_applied'.
Steg 3: Fonetisk & Fonematisk Rekonstruktion (IPA & normalisering) baserat MÅLMEDVETET på lagarna från Steg 2.
        Normalisera vikingatida svenska inskrifter till runsvenska på samma sätt som Samnordisk runtextdatabas
        (t.ex. "En Ulfr hafiR a Ænglandi þry giald takit"), med egennamn med versal. Översätt till modern svenska.
        Hitta inte på uppgifter om tidigare forskning – den jämförelsen görs separat mot Rundata.
Steg 4: Semantisk & Grammatisk Analys
Steg 5: Kontextuell & Flerskiktad Tolkning (Juridiskt, Sakralt, Socio-Geopolitiskt, Konstnärligt)

Arbeta alltid med högsta filologiska exakthet, objektivitet och akademiska källkritik.
"""
        
        # Inkludera kontext
        region_ctx = request.region if request.region else "Okänd region"
        epoch_ctx = request.epoch if request.epoch else "Okänd epok"
        
        # The signum is NOT given to the model: it would recall the published reading from memory instead of
        # interpreting what was read on the image. The comparison with Rundata is made afterwards, without AI.
        step2_prompt = (
            f'Här är den blinda läsningen (direkt från bilden): "{raw_transliteration}"\n'
            f'Geografisk region: {region_ctx}\n'
            f'Tidsperiod/Epok: {epoch_ctx}\n\n'
            'Tolka ENDAST denna läsning. Lägg inte till ord som inte finns i läsningen och fyll inte i luckor ur '
            'kända inskrifter; markera osäkra eller ofullständiga ord. Fältet "transliteration" ska vara läsningen '
            'ovan oförändrad. Använd din analyspipeline. Börja med att identifiera ljudlagarna i '
            '"sound_laws_applied" INNAN du gör normaliseringen. Svara EXAKT med ett JSON-objekt enligt schemat.'
        )
        
        gen2_resp = client.models.generate_content(
            model=GEMINI_PRO_MODEL,
            contents=[step2_prompt],
            config=types.GenerateContentConfig(
                system_instruction=step2_instruction,
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=LinguisticAI
            )
        )
        
        raw_text = gen2_resp.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        parsed = LinguisticAI(**json.loads(raw_text.strip())).model_dump()
        # The transliteration is always the blind reading from step 1 – what was actually seen on the image
        parsed["transliteration"] = raw_transliteration
        parsed.update(reference_checks(request.signum, parsed["transliteration"], parsed["normalization"]))
        parsed["markers"] = markers_data
        
        t1 = gen1_resp.usage_metadata.total_token_count if getattr(gen1_resp, "usage_metadata", None) else 0
        t2 = gen2_resp.usage_metadata.total_token_count if getattr(gen2_resp, "usage_metadata", None) else 0
        parsed["tokens_used"] = t1 + t2
        
        return PhoneticsResponse(**parsed)
        
    except HTTPException:
        raise
    except Exception as e:
        raise ai_error(e, "Fonetisk analys misslyckades.")

class SpeakRequest(BaseModel):
    text: str

@router.post("/speak")
def generate_speech(
    request: SpeakRequest,
    x_openai_api_key: Optional[str] = Header(None, alias="X-OpenAI-Api-Key")
):
    try:
        if not x_openai_api_key:
            raise HTTPException(status_code=401, detail="No OpenAI API Key provided")
            
        openai_client = OpenAI(api_key=x_openai_api_key)
        
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=request.text
        )
        
        return Response(content=response.content, media_type="audio/mpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise ai_error(e, "Talsyntesen misslyckades.")
