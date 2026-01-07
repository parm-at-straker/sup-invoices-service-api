from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_index_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
