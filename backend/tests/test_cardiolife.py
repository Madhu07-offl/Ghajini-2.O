import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.models import Alert, Patient, VitalsReading
from app.db.session import SessionLocal, init_db
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_cardiolife_env():
    settings.init_directories()
    init_db()
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


def test_record_vitals_normal():
    """Records a normal vitals reading and verifies auto-classification."""
    payload = {
        "patient_id": 1,
        "heart_rate_bpm": 74,
        "blood_pressure_systolic": 118,
        "blood_pressure_diastolic": 78,
        "oxygen_saturation": 99,
        "hrv_ms": 50,
        "notes": "Resting after morning tea",
    }
    res = client.post("/v1/cardiolife/readings", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["heart_rate_bpm"] == 74
    assert data["status"] == "normal"
    assert data["blood_pressure_systolic"] == 118
    assert data["blood_pressure_diastolic"] == 78
    assert data["oxygen_saturation"] == 99


def test_record_vitals_critical_triggers_alert():
    """Records a critical tachycardia reading and verifies automatic alert creation."""
    payload = {
        "patient_id": 1,
        "heart_rate_bpm": 145,
        "blood_pressure_systolic": 160,
        "blood_pressure_diastolic": 100,
        "oxygen_saturation": 91,
        "notes": "Sudden heart palpitation",
    }
    res = client.post("/v1/cardiolife/readings", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["heart_rate_bpm"] == 145
    assert data["status"] == "critical_high"

    # Verify alert was created in SQLite
    db = SessionLocal()
    try:
        latest_alert = (
            db.query(Alert)
            .filter(Alert.patient_id == 1, Alert.alert_type == "cardiac_anomaly")
            .order_by(Alert.created_at.desc())
            .first()
        )
        assert latest_alert is not None
        assert "145 BPM" in latest_alert.message
    finally:
        db.close()


def test_get_current_vitals_summary():
    """Verifies multilingual explanations for current vitals."""
    res = client.get("/v1/cardiolife/current?patient_id=1")
    assert res.status_code == 200
    data = res.json()
    assert "reading" in data
    assert "status_label" in data
    assert "human_summary" in data
    assert "en" in data["status_label"]
    assert "hi" in data["status_label"]
    assert "pa" in data["status_label"]
    assert "en" in data["human_summary"]
    assert "hi" in data["human_summary"]
    assert "pa" in data["human_summary"]


def test_get_vitals_history():
    """Verifies vitals history list."""
    res = client.get("/v1/cardiolife/history?patient_id=1&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_live_ecg_waveform():
    """Verifies synthetic P-Q-R-S-T waveform generator output."""
    res = client.get("/v1/cardiolife/ecg-live?bpm=76&samples=100")
    assert res.status_code == 200
    data = res.json()
    assert data["bpm"] == 76
    assert data["sample_interval_ms"] == 20
    assert len(data["waveform"]) == 100
    assert all(isinstance(x, (int, float)) for x in data["waveform"])


def test_simulate_scenario():
    """Verifies simulation shortcut for demo scenarios."""
    res = client.post("/v1/cardiolife/simulate?scenario=critical_tachycardia&patient_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["heart_rate_bpm"] == 144
    assert data["status"] == "critical_high"


def test_companion_vitals_query():
    """Verifies companion correctly answers heart rate/BP questions with vitals intent."""
    payload = {
        "patient_id": 1,
        "text": "How is my heart and pulse?",
        "lang": "en",
    }
    res = client.post("/v1/companion/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "vitals"
    assert "BPM" in data["reply"]
    assert "show_cardiolife" in data["actions"]
