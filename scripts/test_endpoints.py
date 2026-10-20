import os
from fastapi.testclient import TestClient

# Must set a dummy API key for testing if none is set
if "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = "dummy_key_for_testing"

# Import app
try:
    from api.main import app
    client = TestClient(app)
except Exception as e:
    print("Could not import main app:", e)
    exit(1)

def run_tests():
    print("--- STARTING TESTS ---")
    
    # 1. Test RAÄ Fetch (Note: This might fail if dummy key is used and it hits Gemini)
    # We will test the schema and structure.
    print("\n1. Testing /api/raa/fetch endpoint...")
    try:
        response = client.post("/api/raa/fetch", json={"signum": "U 11"})
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Successfully extracted data:")
            print(f" - Material: {data.get('material')}")
            print(f" - Carver: {data.get('attributed_carver')}")
            print(f" - Ornamentation: {data.get('ornamentation')}")
            print(f" - Period: {data.get('period')}")
        else:
            print("Response:", response.text)
    except Exception as e:
        print("Error during RAÄ fetch:", e)

    # 2. Test Synthesis Analyze
    print("\n2. Testing /api/synthesis/analyze endpoint...")
    try:
        payload = {
            "signum": "U 11",
            "stoneType": "Granit",
            "weathering": "Låg",
            "attributed_carver": "Öpir",
            "location": "Uppland",
            "ornamentation": "Pr4",
            "period": "Senvikingatid",
            "slices": [
                {
                    "points": [[0,0,0], [1,1,1]],
                    "angle": 75.0,
                    "asymmetry": 5.0,
                    "depth": 2.5,
                    "width": 10.0,
                    "tool": "Pikmejsel"
                }
            ]
        }
        response = client.post("/api/synthesis/analyze", json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Synthesis generated successfully:")
            print(f" - Geology Analysis: {data.get('geology_analysis')[:50]}...")
            print(f" - Dating Analysis: {data.get('dating_analysis')[:50]}...")
        else:
            print("Response:", response.text)
    except Exception as e:
        print("Error during Synthesis analyze:", e)

    # 3. Test Synthesis Report
    print("\n3. Testing /api/synthesis/report endpoint...")
    try:
        payload["geology_analysis"] = "Test Geology"
        payload["theory_analysis"] = "Test Theory"
        payload["dating_analysis"] = "Test Dating"
        payload["summary"] = "Test Summary"
        payload["candidates"] = [{"name": "Öpir", "probability": 90, "reasoning": "Test"}]
        
        response = client.post("/api/synthesis/report", json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Report generated successfully.")
            html = data.get("html_report", "")
            print(f" - HTML Length: {len(html)} chars")
            print(f" - Includes Dating: {'Datering och Kronologi' in html}")
        else:
            print("Response:", response.text)
    except Exception as e:
        print("Error during Synthesis report:", e)


if __name__ == "__main__":
    run_tests()
