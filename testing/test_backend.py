# test_app.py
from fastapi.testclient import TestClient

# Import the FastAPI app
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Paper Roadmap API is running"}

def test_roadmap():
    # Send a fake query
    response = client.post("/roadmap/", json={"query": "machine learning for cancer biology"})
    assert response.status_code == 200
    data = response.json()
    #print(data)
    assert "roadmap" in data
    # Roadmap is probably empty unless DB has papers
    assert isinstance(data["roadmap"], list)

def test_summary_and_jargon():
    # Replace "dummy123" with a real paper_id if you have data
    fake_id = "dummy123"

    # Summary
    response = client.get(f"/paper/{fake_id}/summary")
    if response.status_code == 404:
        assert response.json()["detail"] == "Paper not found"
    else:
        assert "summary" in response.json()

    # Jargon
    response = client.get(f"/paper/{fake_id}/jargon")
    if response.status_code == 404:
        assert response.json()["detail"] == "Paper not found"
    else:
        assert "jargon" in response.json()
