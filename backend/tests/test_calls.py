import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.models import Patient, Person
from app.db.mongo import mongo_manager
from app.db.session import SessionLocal, init_db
from app.main import app
from app.modules.calls.policy import check_call_policy, is_in_quiet_hours
from app.modules.calls.telegram import send_telegram_briefing
from app.modules.llm.provider import (
    desanitize_text_from_openrouter,
    generate_call_wording,
    get_fallback_caregiver_briefing,
    get_fallback_patient_message,
    sanitize_prompt_for_openrouter,
    validate_generated_wording,
)

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_calls_test_data():
    init_db()
    db = SessionLocal()
    try:
        # Ensure default patient exists
        p = db.query(Patient).filter(Patient.id == 1).first()
        if not p:
            p = Patient(id=1, name="Mother")
            db.add(p)
            db.commit()

        # Ensure Priya is contact #1 and Arun is contact #2
        priya = db.query(Person).filter(Person.name == "Priya").first()
        if not priya:
            priya = Person(
                patient_id=1,
                name="Priya",
                relationship="daughter",
                phone="+919876543210",
                is_emergency_contact=True,
                priority=1,
            )
            db.add(priya)
        else:
            priya.phone = "+919876543210"
            priya.is_emergency_contact = True
            priya.priority = 1

        arun = db.query(Person).filter(Person.name == "Arun").first()
        if not arun:
            arun = Person(
                patient_id=1,
                name="Arun",
                relationship="son",
                phone="+919876543211",
                is_emergency_contact=True,
                priority=2,
            )
            db.add(arun)
        else:
            arun.phone = "+919876543211"
            arun.is_emergency_contact = True
            arun.priority = 2

        db.commit()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_1_openrouter_pii_sanitization():
    """Verify that OpenRouter prompts contain NO personal names or phone numbers."""
    patient_name = "Mother Lakshmi"
    caregiver_name = "Priya Sharma"
    phone = "+919876543210"

    raw_prompt = f"Please notify {caregiver_name} at {phone} that {patient_name} has fallen in the kitchen."
    sanitized, replacements = sanitize_prompt_for_openrouter(
        raw_prompt,
        patient_name=patient_name,
        caregiver_name=caregiver_name,
        phone_number=phone,
    )

    # Asserts that real sensitive names and numbers are completely stripped
    assert patient_name not in sanitized
    assert caregiver_name not in sanitized
    assert phone not in sanitized
    assert "[PATIENT]" in sanitized
    assert "[CAREGIVER]" in sanitized
    assert "[PHONE]" in sanitized

    # Asserts that desanitization correctly restores names back
    mock_llm_reply = "I am calling [CAREGIVER] for you. Please stay with [PATIENT]."
    restored = desanitize_text_from_openrouter(mock_llm_reply, patient_name, caregiver_name)
    assert patient_name in restored
    assert caregiver_name in restored
    assert "[CAREGIVER]" not in restored
    assert "[PATIENT]" not in restored


@pytest.mark.asyncio
async def test_2_template_fallback_on_llm_failure():
    """Verify guaranteed fixed templates in English, Hindi, and Punjabi."""
    # English
    en_patient = get_fallback_patient_message("Priya", lang="en")
    en_briefing = get_fallback_caregiver_briefing("Mother", "SOS Button pressed", "10:30 AM", lang="en")
    assert "Priya" in en_patient
    assert "Mother" in en_briefing

    # Hindi
    hi_patient = get_fallback_patient_message("प्रिया", lang="hi")
    hi_briefing = get_fallback_caregiver_briefing("माता जी", "SOS Button pressed", "10:30 AM", lang="hi")
    assert "प्रिया" in hi_patient
    assert "माता जी" in hi_briefing

    # Punjabi
    pa_patient = get_fallback_patient_message("ਪ੍ਰਿਆ", lang="pa")
    pa_briefing = get_fallback_caregiver_briefing("ਮਾਤਾ ਜੀ", "SOS Button pressed", "10:30 AM", lang="pa")
    assert "ਪ੍ਰਿਆ" in pa_patient
    assert "ਮਾਤਾ ਜੀ" in pa_briefing

    # Wording generation with invalid provider falls back safely
    patient_msg, briefing = await generate_call_wording(
        patient_name="Mother",
        caregiver_name="Priya",
        reason="Fell in bathroom",
        time_str="10:30 AM",
        lang="en",
    )
    assert "Priya" in patient_msg
    assert "Mother" in briefing


def test_3_guardrail_rejects_hallucinations():
    """Verify that output with invented names or entities fails guardrail."""
    allowed = ["Mother", "Priya", "Emergency", "10:30 AM"]
    valid_text = "I am calling Priya for you. Please stay here."
    assert validate_generated_wording(valid_text, allowed, "Mother", "Priya") is True

    # Invented foreign person name 'Alexander'
    hallucinated_text = "Dr Alexander told us to leave immediately."
    assert validate_generated_wording(hallucinated_text, allowed, "Mother", "Priya") is False


@pytest.mark.asyncio
async def test_4_policy_allows_emergency_and_respects_quiet_hours():
    """Verify emergency triggers bypass quiet hours, while routine triggers are blocked."""
    db = SessionLocal()
    try:
        # Emergency at 11:30 PM (Quiet hours)
        late_night = datetime(2026, 10, 27, 23, 30, 0)
        assert is_in_quiet_hours(late_night) is True

        allowed_sos, block_reason, contact, _ = await check_call_policy(
            patient_id=109,
            reason="SOS Help button",
            source="sos",
            db=db,
            override_now=late_night,
        )
        assert allowed_sos is True
        assert block_reason is None

        # Routine trigger at 11:30 PM (Quiet hours) -> MUST BE BLOCKED
        allowed_routine, block_reason_routine, _, _ = await check_call_policy(
            patient_id=109,
            reason="Missed check-in routine",
            source="missed_checkins",
            db=db,
            override_now=late_night,
        )
        assert allowed_routine is False
        assert "quiet hours" in block_reason_routine.lower()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_5_policy_cooldown_and_hourly_limits():
    """Verify cool-down (120s) and maximum 3 attempts per hour."""
    db = SessionLocal()
    pid = 999  # Isolated test patient
    calls_coll = mongo_manager.get_collection("calls")

    try:
        # Clear test patient calls
        await calls_coll.delete_many({"patient_id": pid})
        t0 = datetime.utcnow()

        # Call 1: Allowed
        allowed1, _, _, _ = await check_call_policy(pid, "SOS 1", "sos", db, override_now=t0)
        assert allowed1 is True
        await calls_coll.insert_one({"patient_id": pid, "created_at": t0.isoformat()})

        # Call 2: Immediate retry (30s later) -> BLOCKED by cool-down
        t1 = t0 + timedelta(seconds=30)
        allowed2, reason2, _, _ = await check_call_policy(pid, "SOS 2", "sos", db, override_now=t1)
        assert allowed2 is False
        assert "wait" in reason2.lower()

        # Call 2: After 130s -> Allowed
        t2 = t0 + timedelta(seconds=130)
        allowed2_ok, _, _, _ = await check_call_policy(pid, "SOS 2", "sos", db, override_now=t2)
        assert allowed2_ok is True
        await calls_coll.insert_one({"patient_id": pid, "created_at": t2.isoformat()})

        # Call 3: After another 130s -> Allowed
        t3 = t2 + timedelta(seconds=130)
        allowed3, _, _, _ = await check_call_policy(pid, "SOS 3", "sos", db, override_now=t3)
        assert allowed3 is True
        await calls_coll.insert_one({"patient_id": pid, "created_at": t3.isoformat()})

        # Call 4: 4th attempt within 10 minutes -> BLOCKED by hourly limit (Max 3/hr)
        t4 = t3 + timedelta(seconds=130)
        allowed4, reason4, _, _ = await check_call_policy(pid, "SOS 4", "sos", db, override_now=t4)
        assert allowed4 is False
        assert "maximum" in reason4.lower() or "hour" in reason4.lower()
    finally:
        db.close()
        await calls_coll.delete_many({"patient_id": pid})


@pytest.mark.asyncio
async def test_6_telegram_failure_does_not_block():
    """Verify that Telegram Bot API failure is non-blocking."""
    # When disabled
    success, detail = await send_telegram_briefing("Test Alert", bot_token=None)
    assert success is False
    assert "disabled" in detail or "unconfigured" in detail


def test_7_api_call_request_and_result_escalation():
    """Test full endpoint POST /v1/calls/request and POST /v1/calls/{id}/result."""
    import asyncio
    coll = mongo_manager.get_collection("calls")
    asyncio.run(coll.delete_many({"patient_id": 1}))

    unique_reason = f"Test emergency alert {datetime.utcnow().timestamp()}"
    res = client.post(
        "/v1/calls/request",
        json={
            "patient_id": 1,
            "reason": unique_reason,
            "source": "sos",
            "lang": "en",
            "contact_index": 0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["allowed"] is True
    assert data["contact"]["name"] == "Priya"
    assert data["patient_message"] is not None
    assert data["has_next_contact"] is True
    call_id = data["id"]

    # Report that Priya did NOT answer -> Endpoint offers next contact (Arun)
    result_res = client.post(
        f"/v1/calls/{call_id}/result",
        json={"status": "not_answered", "note": "Ranged out"},
    )
    assert result_res.status_code == 200
    res_data = result_res.json()
    assert res_data["status"] == "not_answered"
    assert res_data["has_next_contact"] is True
    assert res_data["next_contact"]["name"] == "Arun"


def test_8_api_test_alert_endpoint():
    """Test POST /v1/calls/test-alert for Caregiver Settings screen."""
    res = client.post(
        "/v1/calls/test-alert",
        json={"patient_id": 1, "lang": "en"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "briefing" in data
    assert "Test Alert" in data["briefing"]
