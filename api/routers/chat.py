from api.config import GEMINI_PRO_MODEL, GEMINI_FLASH_MODEL
from api.errors import ai_error
from api.rundata import context_text, store
from api.uploads import decode_base64_image
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv(override=True) # Load from .env and overwrite any system env vars

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str
    image_base64: str = None
    image_mime: str = None

class ChatRequest(BaseModel):
    messages: List[Message]
    api_key: str = None # Can be provided from frontend, or fallback to backend env
    context_data: dict = None # Add context for 3D/NLP analyses

class ChatResponse(BaseModel):
    reply: str
    tokens_used: int = 0

# Define system instruction just like in the Streamlit app
SYSTEM_INSTRUCTION = """
Du heter Rune och är en AI-assistent i Aagaard Research-projektet. Du agerar som en objektiv och kritisk runolog och epigrafiker.
Du bistår forskare med runinskrifter, lingvistik (translitterering, normalisering, fornspråk) och 3D-huggspårsanalyser.

Regler:
1. **Källor:** När ett [RUNDATA]-block finns nedan är det uppgifter ur Samnordisk runtextdatabas (Uppsala universitet). Använd dem och hänvisa till Rundata. Finns inget sådant block för en inskrift ska du säga att du inte har verifierade uppgifter om den, i stället för att gissa signum, platser, ristare eller texter.
2. **Objektivitet:** Var vetenskaplig och tydlig med osäkerhet ("Detta tyder på...", "En möjlig tolkning är...").
3. **Inga påhittade siffror:** Ange aldrig procentuella sannolikheter för ristare eller andra påståenden som inte kommer ur underlaget. För attribuering, hänvisa till programmets syntesverktyg, som räknar fram belägg ur Rundata, ortografisk jämförelse och uppmätt huggteknik med redovisad träffsäkerhet.
4. **Huggspår:** Tröskeln 85° mellan pikmejsel (spetsigare) och bredmejsel (trubbigare) är en tumregel, inte ett kalibrerat mått. Runristare bytte ofta verktyg på samma sten, och vittring vidgar spåren.
5. **Notation:** Använd vedertagen notation för translitterering (fetstil/gemener för runtext, ʀ för R-runan) och normalisering.
6. **Struktur:** Använd Markdown-rubriker (### Rubrik) och avsluta längre svar med ### Sammanfattning.
7. **Språk:** Svara på svenska om inte användaren ber om något annat.
"""

@router.post("", response_model=ChatResponse)
def chat_with_ai(
    request: ChatRequest,
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key")
):
    # Resolve API Key
    api_key = x_gemini_api_key or request.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=401, detail="No Gemini API key found")
        
    client = genai.Client(api_key=api_key)
    
    # Format messages for Gemini and analyze complexity
    formatted_contents = []
    has_image = False
    total_length = 0
    
    for msg in request.messages:
        role = "user" if msg.role == "user" else "model"
        parts = [types.Part.from_text(text=msg.content)]
        total_length += len(msg.content)
        if msg.image_base64:
            has_image = True
            image_bytes = decode_base64_image(msg.image_base64)
            parts.insert(0, types.Part.from_bytes(data=image_bytes, mime_type=msg.image_mime or "image/jpeg"))
        
        formatted_contents.append(
            types.Content(role=role, parts=parts)
        )
        
    # Hybrid Model Router
    use_pro = False
    if request.context_data:
        use_pro = True # 3D analysis requires deep reasoning
    if has_image:
        use_pro = True # Visual analysis benefits from Pro
    if total_length > 300:
        use_pro = True # Long context/questions require Pro
        
    selected_model = GEMINI_PRO_MODEL if use_pro else GEMINI_FLASH_MODEL
    dynamic_instruction = SYSTEM_INSTRUCTION

    # Ground the answer in Rundata for every signum mentioned recently or in the analysis context
    recent_user_text = " ".join(m.content for m in request.messages[-4:] if m.role == "user")
    context_signum = str((request.context_data or {}).get("meta_text") or "")
    records = store().find_in_text(f"{context_signum} {recent_user_text}")[:5]
    if records:
        blocks = "\n\n".join(context_text(r) for r in records)
        dynamic_instruction += f"\n\n[RUNDATA – {store().meta['attribution']}]\n{blocks}"

    if request.context_data:
        dynamic_instruction += f"\n\n[SYSTEMKONTEXT: Följande är användarens aktuella analysdata som de kan ställa frågor om: {request.context_data}]"
        
    try:
        response = client.models.generate_content(
            model=selected_model,
            contents=formatted_contents,
            config=types.GenerateContentConfig(
                system_instruction=dynamic_instruction,
                temperature=0.4,
            )
        )
        return ChatResponse(
            reply=response.text,
            tokens_used=response.usage_metadata.total_token_count if getattr(response, "usage_metadata", None) else 0
        )
    except Exception as e:
        raise ai_error(e)
