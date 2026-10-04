import os
from google import genai

try:
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
    client = genai.Client(vertexai=True, project="proven-solstice-274610", location="us-central1")
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents='Hej'
    )
    print(response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
