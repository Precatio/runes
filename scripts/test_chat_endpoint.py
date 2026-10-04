from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

response = client.post("/api/chat", json={
    "messages": [{"role": "user", "content": "Hej!"}]
})

print("Status:", response.status_code)
print("Response:", response.json())
