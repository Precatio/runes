import os
import requests

api_key = os.environ["GEMINI_API_KEY"]

def test_endpoint(url):
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts":[{"text": "Hej"}]}]
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"{url.split('?')[0]}:", response.status_code, response.text[:200])

test_endpoint(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}")
test_endpoint(f"https://generativelanguage.googleapis.com/v1/models/gemini-flash-latest:generateContent?key={api_key}")
test_endpoint(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-latest:generateContent?key={api_key}")
test_endpoint(f"https://generativelanguage.googleapis.com/v1/models/gemini-pro-latest:generateContent?key={api_key}")
test_endpoint(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}")
test_endpoint(f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}")
test_endpoint(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}")

