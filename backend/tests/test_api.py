import io
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import init_db
from app.main import app
from app.modules.chat.prompts import FALLBACK_NOT_SURE

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    settings.init_directories()
    init_db()
    yield


def test_1_health():
    """1. Health check test endpoint."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Ghajini 2.0"
    assert "version" in data


def test_2_create_person():
    """2. Create person with consent check."""
    # Test rejection without consent
    no_consent_payload = {
        "name": "Unauthorized Contact",
        "relationship": "stranger",
        "consent": False,
    }
    bad_res = client.post("/v1/people", json=no_consent_payload)
    assert bad_res.status_code == 400

    # Test successful creation with consent
    payload = {
        "name": "Dr. Sharma",
        "relationship": "doctor",
        "notes": "Family physician who monitors blood pressure",
        "consent": True,
    }
    response = client.post("/v1/people", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Dr. Sharma"
    assert data["relationship"] == "doctor"
    assert data["id"] > 0


def test_3_ask_known_fact():
    """3. Ask with a known fact in memory."""
    # Add known memory
    memory_payload = {
        "text": "Priya is the user's daughter. She lives in Bangalore.",
        "category": "family",
    }
    mem_res = client.post("/v1/memories", json=memory_payload)
    assert mem_res.status_code == 201

    # Ask question
    ask_payload = {
        "text": "Where does Priya live?",
        "lang": "en",
    }
    response = client.post("/v1/ask", json=ask_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True
    assert len(data["sources"]) > 0
    assert "Bangalore" in data["sources"][0] or "Bangalore" in data["answer"]


def test_4_ask_unknown_fact():
    """4. Ask with an unknown fact; must return exact fallback message."""
    ask_payload = {
        "text": "What is the secret recipe for Martian space soup on Neptune?",
        "lang": "en",
    }
    response = client.post("/v1/ask", json=ask_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is False
    assert data["answer"] == FALLBACK_NOT_SURE


def test_5_delete_person():
    """5. Create and then delete person and verify removal."""
    # Create person
    create_payload = {
        "name": "Temporary Contact",
        "relationship": "neighbor",
        "notes": "Will be deleted",
        "consent": True,
    }
    create_res = client.post("/v1/people", json=create_payload)
    assert create_res.status_code == 201
    person_id = create_res.json()["id"]

    # Delete person
    delete_res = client.delete(f"/v1/people/{person_id}")
    assert delete_res.status_code == 200
    data = delete_res.json()
    assert data["deleted"] is True
    assert data["person_id"] == person_id

    # Verify not in list
    list_res = client.get("/v1/people")
    assert list_res.status_code == 200
    remaining_ids = [p["id"] for p in list_res.json()]
    assert person_id not in remaining_ids
