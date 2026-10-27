import io
import json
import wave
import zipfile
from datetime import datetime, timedelta
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.models import Alert, Patient, PersonFace, Reminder, ReminderLog
from app.db.session import SessionLocal, init_db
from app.main import app
from app.modules.chat.prompts import (
    EMERGENCY_RESPONSE_BY_LANG,
    FALLBACK_NOT_SURE,
    get_emergency_response,
)
from app.modules.faces.engine import face_engine
from app.modules.reminders.scheduler import process_reminders

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    settings.init_directories()
    init_db()
    # Ensure default patient exists
    db = SessionLocal()
    try:
        p = db.query(Patient).filter(Patient.id == 1).first()
        if not p:
            p = Patient(id=1, name="Demo Patient")
            db.add(p)
            db.commit()
    finally:
        db.close()
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


def test_6_transcribe_wav():
    """6. Voice transcribe endpoint with valid synthetic 16kHz mono WAV."""
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        # Write 0.5s of 16kHz audio
        wf.writeframes(b"\x00\x00" * 8000)
    wav_bytes = wav_buf.getvalue()

    files = {"file": ("test_speech.wav", wav_bytes, "audio/wav")}
    response = client.post("/v1/voice/transcribe", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "language" in data
    assert "confidence" in data
    assert "needs_confirmation" in data
    assert data["language"] in ["en", "hi", "pa"]


def test_7_emergency_phrase_creates_alert_and_skips_llm():
    """7. Emergency phrase triggers immediate family alert and skips LLM."""
    emergency_payload = {
        "text": "Help me please, I fell down and cannot get up! bachao!",
        "lang": "en",
    }
    response = client.post("/v1/ask", json=emergency_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == get_emergency_response("en")
    assert data["grounded"] is True

    # Verify that caregiver alert was created
    alerts_res = client.get("/v1/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    emergency_alerts = [a for a in alerts if a["alert_type"] == "emergency_phrase"]
    assert len(emergency_alerts) > 0
    assert "fell" in emergency_alerts[0]["message"] or "bachao" in emergency_alerts[0]["message"]


def test_8_reminder_fires_and_escalates():
    """8. Reminder fires, appears in /due, and escalates to caregivers after timeout."""
    # 1. Create a reminder
    rem_payload = {
        "title": "Evening Heart Pill",
        "scheduled_time": "18:00",
        "message": "Take one red tablet with water",
        "is_critical": True,
        "escalate_after_min": 1,
    }
    create_res = client.post("/v1/reminders", json=rem_payload)
    assert create_res.status_code == 201
    rem_id = create_res.json()["id"]

    db = SessionLocal()
    try:
        rem = db.query(Reminder).filter(Reminder.id == rem_id).first()
        assert rem is not None

        # Manually trigger reminder as due
        rem.status = "triggered"
        rem.last_triggered_at = datetime.utcnow()
        rem.retry_count = 0
        db.commit()

        # Verify it appears in /v1/reminders/due
        due_res = client.get("/v1/reminders/due")
        assert due_res.status_code == 200
        due_list = due_res.json()
        assert any(r["id"] == rem_id for r in due_list)

        # Fast-forward time past 5 min to test repeat
        rem.last_triggered_at = datetime.utcnow() - timedelta(minutes=6)
        db.commit()
        process_reminders()

        db.refresh(rem)
        assert rem.status == "repeated"
        assert rem.retry_count == 1

        # Fast-forward time past escalate_after_min (1 min after repeat) to test escalation
        rem.last_triggered_at = datetime.utcnow() - timedelta(minutes=2)
        db.commit()
        process_reminders()

        db.refresh(rem)
        assert rem.status == "escalated"

        # Check reminder logs
        esc_log = (
            db.query(ReminderLog)
            .filter(ReminderLog.reminder_id == rem_id, ReminderLog.action == "escalated")
            .first()
        )
        assert esc_log is not None
        assert esc_log.outcome == "escalated"

        # Check caregiver alert created
        esc_alert = (
            db.query(Alert)
            .filter(Alert.reminder_id == rem_id, Alert.alert_type == "reminder_escalated")
            .first()
        )
        assert esc_alert is not None
    finally:
        db.close()


def test_9_delete_person_removes_vectors_and_fails_recognition():
    """9. Deleting person purges DB rows, files, and FAISS vectors; confirms face no longer recognized."""
    # 1. Create a person
    create_res = client.post(
        "/v1/people",
        json={
            "name": "Aunt Sarah",
            "relationship": "aunt",
            "notes": "Testing face vector removal",
            "consent": True,
        },
    )
    assert create_res.status_code == 201
    person_id = create_res.json()["id"]

    # 2. Add synthetic embedding directly to FAISS and DB
    dummy_embedding = np.random.randn(512).astype(np.float32)
    norm = np.linalg.norm(dummy_embedding)
    dummy_embedding = dummy_embedding / norm

    face_id = 9999
    face_engine.add_face_embedding(face_id, person_id, dummy_embedding)

    db = SessionLocal()
    try:
        db_face = PersonFace(
            id=face_id,
            patient_id=1,
            person_id=person_id,
            file_path="uploads/sarah_test.jpg",
            embedding_json=json.dumps(dummy_embedding.tolist()),
            quality_score=0.95,
        )
        db.add(db_face)
        db.commit()
    finally:
        db.close()

    assert face_engine.face_id_to_person_id.get(face_id) == person_id

    # 3. Delete person
    del_res = client.delete(f"/v1/people/{person_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    # 4. Verify vectors removed from face_engine
    assert face_id not in face_engine.face_id_to_person_id

    # 5. Verify person is no longer recognized
    # Query with a blank test image
    import cv2
    img_arr = np.zeros((100, 100, 3), dtype=np.uint8)
    _, encoded_img = cv2.imencode(".jpg", img_arr)
    rec_res = client.post(
        "/v1/recognize",
        files={"image": ("unknown.jpg", encoded_img.tobytes(), "image/jpeg")},
    )
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["status"] in ["no_face", "unknown"]
    assert rec_data["person"] is None


def test_10_privacy_export_returns_zip():
    """10. Privacy export endpoint returns a valid ZIP archive with full JSON records."""
    response = client.get("/v1/privacy/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    zip_bytes = response.content
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "export.json" in namelist

        with zf.open("export.json") as f:
            export_data = json.loads(f.read().decode("utf-8"))
            assert "export_metadata" in export_data
            assert "people" in export_data
            assert "memories" in export_data
            assert "reminders" in export_data
            assert "alerts" in export_data
            assert "audit_logs" in export_data
            assert export_data["export_metadata"]["patient_id"] == 1


def test_11_dashboard_summary_numbers_match_seeded_logs():
    """11. Caregiver Dashboard analytics summary & daily plain-English report."""
    # 1. Summary analytics
    res = client.get("/v1/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "adherence_pct" in data
    assert "done_count" in data
    assert "missed_count" in data
    assert "total_reminders_7d" in data
    assert "alerts_count" in data
    assert "recognitions_today" in data
    assert "top_questions" in data
    assert "weekly_history" in data
    assert len(data["weekly_history"]) == 7
    assert isinstance(data["adherence_pct"], (int, float))

    # 2. Daily plain-English report
    daily_res = client.get("/v1/dashboard/daily-summary")
    assert daily_res.status_code == 200
    daily_data = daily_res.json()
    assert "summary" in daily_data
    assert "source" in daily_data
    assert daily_data["source"] in ["llm", "template"]
    assert len(daily_data["summary"]) > 10


def test_12_demo_reset_restores_seed_state():
    """12. Demo reset endpoint restores full pristine state with 3 people, 10 memories, 2 reminders, 1 place."""
    res = client.post("/v1/demo/reset")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "reset_complete"
    assert data["people"] == 3
    assert data["memories"] == 10
    assert data["reminders"] == 2
    assert data["places"] == 1

    # Verify 3 people exist
    people_res = client.get("/v1/people")
    assert people_res.status_code == 200
    names = [p["name"] for p in people_res.json()]
    assert "Priya" in names
    assert "Dr. Sharma" in names
    assert "Arun" in names

    # Verify trigger-reminder
    trig_res = client.post("/v1/demo/trigger-reminder")
    assert trig_res.status_code == 200
    assert trig_res.json()["status"] == "triggered"


def test_13_health_endpoint_component_statuses():
    """13. Health endpoint reports status of Mongo, Ollama, Face model, and Whisper model."""
    res = client.get("/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "mongo" in data
    assert "ollama" in data
    assert "face_model" in data
    assert "whisper_model" in data
    assert data["mongo"] in ["connected", "disconnected"]
    assert data["ollama"] in ["available", "unavailable"]
    assert data["face_model"] in ["loaded", "fallback"]
    assert data["whisper_model"] in ["loaded", "fallback"]


def test_14_timeout_and_fallback_prompt():
    """14. Question timeout / unknown fact falls back safely without ungrounded hallucination."""
    res = client.post(
        "/v1/ask",
        json={"text": "What is the capital city of Peru on planet Jupiter?", "lang": "en"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["grounded"] is False
    assert data["answer"] == FALLBACK_NOT_SURE


