from api import llm
from api.errors import ai_error, server_error, logger
from api.rundata import context_text, store
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import requests
import re

router = APIRouter()

class RaaRequest(BaseModel):
    signum: str

class RaaResponse(BaseModel):
    material: str
    condition: str
    attributed_carver: str
    location: str
    ornamentation: str
    period: str
    raw_data: str
    source: str = "ksamsok-ai"  # "rundata" när uppgifterna kommer direkt från Rundata
    signum: Optional[str] = None
    attribution: Optional[str] = None

class ExtractSignumRequest(BaseModel):
    filename: str

class ExtractSignumResponse(BaseModel):
    signum: Optional[str] = None  # None when the filename has no recognisable signum


# Landskapskod (1–3 bokstäver, t.ex. U, Sö, Ög, DR, N) följd av ett nummer, eventuellt med tillägg
SIGNUM_PATTERN = re.compile(r"^[A-ZÅÄÖ][A-Za-zåäöÅÄÖ]{0,2}\s(\d+[A-Za-z]?\s?\$?|(Fv|ATA|NOR|SB|SL|SR)[\w;:\- ]+)$")

@router.post("/extract-signum", response_model=ExtractSignumResponse)
def extract_signum(
    request: ExtractSignumRequest,
    ai: llm.AIContext = Depends(llm.ai_context),
):
    # Deterministic match against Rundata first; the AI is only a fallback
    found = store().find_in_text(request.filename)
    if found:
        return ExtractSignumResponse(signum=found[0]["signum"])

    prompt = f"""
    Extrahera signumet för runstenen från detta filnamn: "{request.filename}"
    Exempel: 
    - "So 113_1_4 thin_closed holes.stl" -> "Sö 113"
    - "U_11_mesh.obj" -> "U 11"
    - "Vg59.stl" -> "Vg 59"
    Svara ENDAST med signumet. Om filnamnet inte innehåller något signum, svara INGET.
    """
    
    try:
        signum = llm.generate(ai, prompt, tier="fast", temperature=0.1).text.strip().strip('"').strip()
        # The model sometimes answers with words like "Saknas" – only accept something shaped like a signum
        return ExtractSignumResponse(signum=signum if SIGNUM_PATTERN.match(signum) else None)
    except HTTPException:
        raise
    except Exception as e:
        raise ai_error(e)

def rundata_response(rec: dict) -> RaaResponse:
    carvers = [c for c in rec["carvers"] if c["kind"] in ("S", "A")]
    carver = ", ".join(f"{c['name']}{' (osäker)' if c['uncertain'] else ''}" for c in carvers)
    location = ", ".join(x for x in (rec["place"], rec["parish"], rec["district"]) if x)
    style = rec["style"] or ""
    if style and rec["style_uncertain"]:
        style += "?"
    return RaaResponse(
        material=rec["material"] or rec["material_type"] or "Okänd",
        condition="Försvunnen" if rec["flags"]["lost"] else "Okänt",
        attributed_carver=carver or "Okänd",
        location=location or "Okänd plats",
        ornamentation=style or "Okänd",
        period=rec["dating"] or "Okänd",
        raw_data=context_text(rec),
        source="rundata",
        signum=rec["signum"],
        attribution=store().meta["attribution"],
    )


@router.post("/fetch", response_model=RaaResponse)
def fetch_raa_data(
    request: RaaRequest,
    ai: llm.AIContext = Depends(llm.ai_context),
):
    signum = request.signum

    # 1. Rundata (Samnordisk runtextdatabas): structured, citable data
    rec = store().get(signum)
    if rec:
        return rundata_response(rec)

    # 2. Fallback: K-samsök free text interpreted by the AI
    llm.require(ai)

    url = "https://kulturarvsdata.se/ksamsok/api"
    params = {
        "method": "search",
        "query": f'text="{signum}"',
        "hitsPerPage": 20
    }
    
    try:
        response = requests.get(url, params=params, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(e, "Kunde inte hämta data från K-samsök.", status_code=502)
        
    descriptions = []
    for record in data.get("result", {}).get("records", []):
        graph = record.get("record", {}).get("@graph", [])
        for node in graph:
            if "ksam:desc" in node:
                desc = node["ksam:desc"]
                if isinstance(desc, dict):
                    descriptions.append(desc.get("@value", ""))
                elif isinstance(desc, list):
                    for d in desc:
                        if isinstance(d, dict):
                            descriptions.append(d.get("@value", ""))
                        else:
                            descriptions.append(str(d))
                else:
                    descriptions.append(str(desc))
                    
    if not descriptions:
        return RaaResponse(material="", condition="", attributed_carver="", location="", ornamentation="", period="", raw_data="Ingen data hittades för detta signum i K-samsök.")
        
    joined_desc = "\n".join(descriptions[:20]) # Limit to avoid massive tokens
    
    prompt = f"""
    Här är sökresultat från Riksantikvarieämbetet (K-samsök) för runstenen med signum {signum}:
    {joined_desc}
    
    Din uppgift är att läsa igenom denna text och försöka extrahera:
    1. Material (Stenart, t.ex. 'Granit', 'Röd sandsten', 'Gnejs'). Svara med endast stenarten, eller 'Okänd' om det inte framgår.
    2. Skick / Vittringsgrad (t.ex. 'Vittrad', 'Svårt vittrad', 'Gott skick'). Svara kort, eller 'Okänt' om det inte framgår.
    3. Tillskriven ristare (t.ex. 'Åsmund Kåreson', 'Öpir', 'Balle'). Svara endast med namnet, eller 'Okänd' om ingen ristare nämns.
    4. Geografisk plats (t.ex. 'Socken', 'Län' eller koordinater). Svara kort (ex. 'Runtuna socken, Södermanland'). Om det inte framgår, svara 'Okänd plats'.
    5. Ornamentik / Stilgrupp (t.ex. 'Pr3', 'Fp', 'Ringerikestil'). Svara endast med stilen, eller 'Okänd' om det inte framgår.
    6. Datering / Tidsperiod (t.ex. '1000-tal', 'Senvikingatid'). Svara kort, eller 'Okänd' om det inte framgår.
    
    Svara EXAKT och ENDAST med ett giltigt JSON-objekt enligt följande format:
    {{"material": "...", "condition": "...", "attributed_carver": "...", "location": "...", "ornamentation": "...", "period": "..."}}
    """
    
    try:
        parsed_json = llm.generate(ai, prompt, tier="fast", json_mode=True, temperature=0.1).data or {}
        
        return RaaResponse(
            material=parsed_json.get("material", "Okänd"),
            condition=parsed_json.get("condition", "Okänt"),
            attributed_carver=parsed_json.get("attributed_carver", "Okänd"),
            location=parsed_json.get("location", "Okänd plats"),
            ornamentation=parsed_json.get("ornamentation", "Okänd"),
            period=parsed_json.get("period", "Okänd"),
            raw_data=joined_desc[:500] + "..." # Return a snippet for UI debug if needed
        )
        
    except Exception as e:
        # Fallback if Gemini fails
        logger.error("RAÄ-analys misslyckades: %r", e, exc_info=e)
        return RaaResponse(material="", condition="", attributed_carver="", location="", ornamentation="", period="", raw_data="Data hämtades men kunde inte analyseras.")
