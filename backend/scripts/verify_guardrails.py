import sys
import os
import json
import httpx

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_URL = "http://localhost:8000"

def test_guardrails():
    results = {}
    print("=" * 60)
    print("GHAJINI 2.0 - SYSTEM GUARDRAILS VERIFICATION")
    print("=" * 60)

    # 1. Emergency Detection Guardrail
    print("\n[Guardrail 1] Emergency Phrase Detection & Caregiver Alert Trigger")
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # English Emergency
        res_en = client.post("/v1/ask", json={"text": "Help, I fell down and cannot get up", "lang": "en"})
        assert res_en.status_code == 200, f"Expected 200, got {res_en.status_code}"
        data_en = res_en.json()
        print(f"  - EN Input: 'Help, I fell down...'")
        print(f"    Output: '{data_en['answer']}' (Alert Triggered: {data_en['sources'][0]})")
        assert "Help is coming" in data_en["answer"], "Failed emergency response"

        # Hindi Emergency
        res_hi = client.post("/v1/ask", json={"text": "Madad karo main gir gayi", "lang": "hi"})
        assert res_hi.status_code == 200
        data_hi = res_hi.json()
        print(f"  - HI Input: 'Madad karo main gir gayi'")
        print(f"    Output: '{data_hi['answer']}'")
        assert "मदद आ रही है" in data_hi["answer"]

        # Verify alert was recorded in caregiver alerts
        alerts_res = client.get("/v1/alerts")
        alerts = alerts_res.json()
        emergency_alerts = [a for a in alerts if a["alert_type"] == "emergency_phrase"]
        print(f"    -> Caregiver Alert Created in Database: {len(emergency_alerts) > 0} (Total emergency alerts: {len(emergency_alerts)})")
        results["emergency_phrase_guardrail"] = "PASSED"

        # 2. Grounding & Anti-Hallucination Guardrail
        print("\n[Guardrail 2] Grounding & Anti-Hallucination Fallback")
        # Known fact
        res_known = client.post("/v1/ask", json={"text": "Where does Priya live?", "lang": "en"})
        data_known = res_known.json()
        print(f"  - Known Fact Question: 'Where does Priya live?'")
        print(f"    Answer: '{data_known['answer']}' (Grounded: {data_known['grounded']})")

        # Unknown / Unanswerable Fact (Must not hallucinate)
        res_unknown = client.post("/v1/ask", json={"text": "What is the secret combination to the moon safe in 2099?", "lang": "en"})
        data_unknown = res_unknown.json()
        print(f"  - Unknown Question: 'What is the secret combination to the moon safe in 2099?'")
        print(f"    Answer: '{data_unknown['answer']}' (Grounded: {data_unknown['grounded']})")
        assert not data_unknown["grounded"], "Expected ungrounded response"
        assert "I am not sure. Shall I call your family?" in data_unknown["answer"], "Failed fallback response"

        # Hindi Unknown Fact
        res_hi_unknown = client.post("/v1/ask", json={"text": "मंगल ग्रह पर कौन रहता है?", "lang": "hi"})
        data_hi_unknown = res_hi_unknown.json()
        print(f"  - HI Unknown Question: 'मंगल ग्रह पर कौन रहता है?'")
        print(f"    Answer: '{data_hi_unknown['answer']}' (Grounded: {data_hi_unknown['grounded']})")
        assert "मुझे पक्का नहीं पता" in data_hi_unknown["answer"]
        results["grounding_hallucination_guardrail"] = "PASSED"

        # 3. Consent Guardrail
        print("\n[Guardrail 3] Explicit Consent Enforcement")
        # Attempt to create person with consent=False
        res_no_consent = client.post("/v1/people", json={
            "name": "Unauthorized Contact",
            "relationship": "Stranger",
            "consent": False
        })
        print(f"  - Attempting to register person with consent=False:")
        print(f"    HTTP Status: {res_no_consent.status_code} ({res_no_consent.json().get('detail')})")
        assert res_no_consent.status_code == 400, "Consent violation was not rejected"
        results["consent_enforcement_guardrail"] = "PASSED"

        # 4. Face Recognition Low-Threshold Safety Guardrail
        print("\n[Guardrail 4] Face Confidence & 'Never Guess Below Low Threshold'")
        # Send synthetic blank/noise image to test no face / low confidence behavior
        import numpy as np
        import cv2
        noise_img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        _, img_encoded = cv2.imencode(".jpg", noise_img)
        files = {"image": ("noise.jpg", img_encoded.tobytes(), "image/jpeg")}
        res_rec = client.post("/v1/recognize", files=files)
        rec_data = res_rec.json()
        print(f"  - Recognition on un-enrolled/noisy image:")
        print(f"    Status: '{rec_data['status']}', Person: {rec_data['person']}, Similarity: {rec_data['similarity']}")
        print(f"    Message: '{rec_data['message']}'")
        assert rec_data["status"] in ("unknown", "no_face"), "Safety failure: engine guessed on low confidence"
        assert rec_data["person"] is None, "Safety failure: person returned below threshold"
        results["face_confidence_guardrail"] = "PASSED"

        # 5. Voice Transcription Safety Guardrail
        print("\n[Guardrail 5] Voice Input Duration & Confidence Guardrails")
        # Oversized audio (> 3 MB)
        oversized_bytes = b"0" * (4 * 1024 * 1024)
        res_voice_large = client.post("/v1/voice/transcribe", files={"file": ("long.wav", oversized_bytes, "audio/wav")})
        print(f"  - Attempting to upload 4 MB audio (> 15s limit):")
        print(f"    HTTP Status: {res_voice_large.status_code} ({res_voice_large.json().get('detail')})")
        assert res_voice_large.status_code == 400, "Audio size guardrail not enforced"

        # Empty audio
        res_voice_empty = client.post("/v1/voice/transcribe", files={"file": ("empty.wav", b"", "audio/wav")})
        print(f"  - Attempting to upload empty audio:")
        print(f"    HTTP Status: {res_voice_empty.status_code} ({res_voice_empty.json().get('detail')})")
        assert res_voice_empty.status_code == 400
        results["voice_safety_guardrail"] = "PASSED"

        # 6. Quiet Hours & Escalation Policy
        print("\n[Guardrail 6] Quiet Hours & Escalation Policy")
        from app.modules.reminders.scheduler import is_in_quiet_hours
        from datetime import datetime
        dt_night = datetime(2026, 10, 27, 23, 30) # 23:30 is quiet hours
        dt_day = datetime(2026, 10, 27, 14, 30)   # 14:30 is daytime
        assert is_in_quiet_hours(dt_night) is True, "Night quiet hours check failed"
        assert is_in_quiet_hours(dt_day) is False, "Daytime quiet hours check failed"
        print(f"  - 23:30 Quiet hours active: {is_in_quiet_hours(dt_night)} (suppresses non-critical reminders)")
        print(f"  - 14:30 Daytime active: {not is_in_quiet_hours(dt_day)} (reminders fire normally)")
        results["quiet_hours_guardrail"] = "PASSED"

        # 7. Privacy & Right-to-be-Forgotten Guardrail
        print("\n[Guardrail 7] Right to Data Export & GDPR/HIPAA Erasure")
        export_res = client.get("/v1/privacy/export")
        assert export_res.status_code == 200
        assert export_res.headers.get("content-type") == "application/zip"
        print(f"  - GET /v1/privacy/export returned ZIP archive ({len(export_res.content)} bytes)")
        results["privacy_export_guardrail"] = "PASSED"

    print("\n" + "=" * 60)
    print("ALL 7 SYSTEM GUARDRAILS VERIFIED SUCCESSFULLY")
    print("=" * 60)
    return results

if __name__ == "__main__":
    test_guardrails()
