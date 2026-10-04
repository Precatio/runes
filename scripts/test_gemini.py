import os
from google import genai
from google.genai import types
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
resp = client.models.generate_content(model="gemini-pro-latest", contents="test", config=types.GenerateContentConfig(temperature=0.1))
print(resp.text)
