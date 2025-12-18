from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Forecast Anything Platform API"
    }

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_plan_endpoint_no_file():
    # Test that /plan requires a file
    response = client.post("/plan", data={"prompt": "test"})
    assert response.status_code == 422 # Unprocessable Entity
