import os
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
try:
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents='Hej'
    )
    print("Response:", response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
