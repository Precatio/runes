import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()

class TwoDAnalysisResponse(BaseModel):
    predicted_style: str
    confidence: int
    reasoning: str
    transcription: str

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents="Hello",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TwoDAnalysisResponse,
        )
    )
    print(response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
