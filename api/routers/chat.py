from api import llm
from api.errors import ai_error
from api.rundata import context_text, store
from api.uploads import decode_base64_image
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
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
def chat_with_ai(request: ChatRequest, ai: llm.AIContext = Depends(llm.ai_context)):
    messages, has_image, total_length = [], False, 0
    for msg in request.messages:
        images = []
        if msg.image_base64:
            has_image = True
            images.append((decode_base64_image(msg.image_base64), msg.image_mime or "image/jpeg"))
        total_length += len(msg.content)
        messages.append(llm.Message("user" if msg.role == "user" else "assistant", msg.content, images))

    # Analysis context, images and long questions need the stronger model
    tier = "pro" if (request.context_data or has_image or total_length > 300) else "fast"
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
        r = llm.generate(ai, system=dynamic_instruction, messages=messages, tier=tier, temperature=0.4)
        return ChatResponse(reply=r.text, tokens_used=r.tokens)
    except HTTPException:
        raise
    except Exception as e:
        raise ai_error(e)
