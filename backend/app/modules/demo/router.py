import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Alert, AuditLog, Consent, Memory, Patient, Person, PersonFace, Place, Reminder, ReminderLog
from app.db.session import get_db
from app.modules.faces.engine import face_engine
from app.modules.memory.retrieval import memory_retrieval

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_demo_data(
    patient_id: int = Query(default=settings.DEFAULT_PATIENT_ID),
    db: Session = Depends(get_db),
):
    """
    Wipes existing demo data and re-seeds:
    - 3 people with photos from demo_assets/ (Priya, Dr. Sharma, Arun)
    - 10 memories auto-embedded into FAISS
    - 2 reminders (one due in 1 minute, one daily 9:00 AM)
    - 1 place (Home: 42 Palm Avenue, Bangalore)
    - 7 days of reminder logs for ~85% caregiver dashboard adherence
    """
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo reset is disabled when DEMO_MODE=false",
        )

    logger.info("Executing Demo Reset...")

    # 1. Clean existing patient data
    db.query(ReminderLog).filter(ReminderLog.patient_id == patient_id).delete()
    db.query(Reminder).filter(Reminder.patient_id == patient_id).delete()
    db.query(Alert).filter(Alert.patient_id == patient_id).delete()
    db.query(AuditLog).filter(AuditLog.patient_id == patient_id).delete()
    db.query(Memory).filter(Memory.patient_id == patient_id).delete()
    db.query(Place).filter(Place.patient_id == patient_id).delete()
    db.query(Consent).filter(Consent.patient_id == patient_id).delete()

    people = db.query(Person).filter(Person.patient_id == patient_id).all()
    face_ids = []
    for p in people:
        for f in p.faces:
            face_ids.append(f.id)
            if f.file_path and os.path.exists(f.file_path):
                try:
                    os.remove(f.file_path)
                except Exception:
                    pass
        db.delete(p)

    db.commit()

    # Reset FAISS indexes
    face_engine.remove_person(patient_id, face_ids)
    memory_retrieval._init_faiss_index()

    # Ensure patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        patient = Patient(id=patient_id, name="Primary Patient")
        db.add(patient)
        db.commit()

    # 2. Seed 3 People with demo photos
    demo_assets_candidates = [
        os.path.abspath("backend/demo_assets"),
        os.path.abspath("demo_assets"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "backend", "demo_assets"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "demo_assets"),
    ]
    demo_assets_dir = next((d for d in demo_assets_candidates if os.path.exists(d)), demo_assets_candidates[0])
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    people_definitions = [
        {
            "name": "Priya",
            "relationship": "daughter",
            "notes": "Lives in Bangalore. Visits on weekends with grandson Kabir.",
            "asset": "priya.jpg",
        },
        {
            "name": "Dr. Sharma",
            "relationship": "doctor",
            "notes": "Family physician at Apollo Clinic. Checks blood pressure monthly.",
            "asset": "dr_sharma.jpg",
        },
        {
            "name": "Arun",
            "relationship": "son",
            "notes": "Lives in Indiranagar, Bangalore. Calls every evening at 7:00 PM.",
            "asset": "arun.jpg",
        },
    ]

    for pdef in people_definitions:
        person = Person(
            patient_id=patient_id,
            name=pdef["name"],
            relationship=pdef["relationship"],
            notes=pdef["notes"],
        )
        db.add(person)
        db.commit()
        db.refresh(person)

        # Consent record
        consent = Consent(
            patient_id=patient_id,
            person_id=person.id,
            consent_given=True,
            consent_type="face_recognition_and_data_storage",
        )
        db.add(consent)

        # Copy photo from demo_assets
        src_asset = os.path.join(demo_assets_dir, pdef["asset"])
        dest_filename = f"face_p{person.id}_{pdef['asset']}"
        dest_path = os.path.join(settings.UPLOAD_DIR, dest_filename)

        img_bytes = b""
        if os.path.exists(src_asset):
            shutil.copyfile(src_asset, dest_path)
            with open(src_asset, "rb") as f:
                img_bytes = f.read()

        emb, quality = face_engine.extract_face_embedding(img_bytes)
        if emb is None:
            # Deterministic distinct embedding
            import numpy as np
            emb = np.zeros(512, dtype=np.float32)
            emb[hash(pdef["name"]) % 512] = 1.0
            emb = face_engine._normalize(emb)
            quality = 0.90

        face_rec = PersonFace(
            patient_id=patient_id,
            person_id=person.id,
            file_path=dest_path,
            embedding_json=json.dumps(emb.tolist()),
            quality_score=quality,
        )
        db.add(face_rec)
        db.commit()
        db.refresh(face_rec)

        face_engine.add_face(face_rec.id, person.id, emb)

    # 3. Seed 10 Memories
    memories_text = [
        "Priya is the user's daughter. She lives in Bangalore.",
        "Arun is the user's son. He lives in Indiranagar and calls every evening.",
        "Dr. Sharma is the family doctor who monitors health and blood pressure.",
        "The user takes blood pressure medication every morning at 9:00 AM with warm water.",
        "The user's home address is 42 Palm Avenue, Bangalore.",
        "Priya brings homemade vegetable soup on Sunday afternoons.",
        "The emergency contact phone number for Arun is 9876543210.",
        "The user likes drinking green tea without sugar in the evening at 5:00 PM.",
        "The reading glasses and spectacles are kept on the wooden bedside table.",
        "The walking stick is kept right next to the front door entrance umbrella stand.",
    ]

    for mtext in memories_text:
        mem = Memory(
            patient_id=patient_id,
            text=mtext,
            category="family_health",
        )
        db.add(mem)
        db.commit()
        db.refresh(mem)

        emb_list = memory_retrieval.add_memory(mem.id, mem.text)
        mem.embedding_json = json.dumps(emb_list)
        db.commit()

    # 4. Seed 2 Reminders:
    # - One due in 1 minute (for live demo testing)
    # - One daily at 09:00 AM
    now = datetime.utcnow()
    in_one_min = (now + timedelta(minutes=1)).strftime("%H:%M")

    # Reminder 1: Due in 1 minute
    demo_live_reminder = Reminder(
        patient_id=patient_id,
        title="Drink Warm Water & Hydration",
        message="Please drink one cup of warm water with lemon.",
        scheduled_time=in_one_min,
        frequency="daily",
        rrule="FREQ=DAILY",
        is_critical=True,
        escalate_after_min=2,
        status="pending",
        next_run_at=now + timedelta(minutes=1),
    )
    db.add(demo_live_reminder)

    # Reminder 2: Daily 09:00 AM BP pill
    daily_reminder = Reminder(
        patient_id=patient_id,
        title="Take Blood Pressure Medication (Amlodipine 5mg)",
        message="Take one tablet after breakfast with warm water.",
        scheduled_time="09:00",
        frequency="daily",
        rrule="FREQ=DAILY",
        is_critical=True,
        escalate_after_min=10,
        status="pending",
    )
    db.add(daily_reminder)
    db.commit()

    # 5. Seed 1 Place
    home_place = Place(
        patient_id=patient_id,
        name="Home",
        address="42 Palm Avenue, Bangalore",
        notes="Primary residence. Safe home environment.",
    )
    db.add(home_place)

    # 6. Seed 7 days of historical logs for ~85% adherence dashboard
    for i in range(7, 0, -1):
        log_dt = now - timedelta(days=i)
        outcome = "acknowledged" if i != 2 else "missed"
        action = "acknowledged" if i != 2 else "escalated"
        rlog = ReminderLog(
            patient_id=patient_id,
            reminder_id=daily_reminder.id,
            action=action,
            outcome=outcome,
            details=f"Demo 7-day adherence historical log for day {i}",
            timestamp=log_dt,
        )
        db.add(rlog)

    # Seed sample audit questions
    sample_questions = [
        "Where does Priya live?",
        "Where does Priya live?",
        "Where does Priya live?",
        "When do I take my medicine?",
        "When do I take my medicine?",
        "Where are my spectacles?",
    ]
    for q in sample_questions:
        q_audit = AuditLog(
            patient_id=patient_id,
            action="ask_question",
            details=q,
            timestamp=now - timedelta(hours=2),
        )
        db.add(q_audit)

    db.commit()

    return {
        "status": "reset_complete",
        "message": "Demo data wiped and successfully re-seeded.",
        "people": 3,
        "memories": 10,
        "reminders": 2,
        "places": 1,
        "live_reminder_time": in_one_min,
    }


@router.post("/trigger-reminder", status_code=status.HTTP_200_OK)
def trigger_reminder_now(
    patient_id: int = Query(default=settings.DEFAULT_PATIENT_ID),
    db: Session = Depends(get_db),
):
    """
    Forces the nearest pending reminder to trigger immediately.
    Used by the Flutter hidden 'Demo Tools' screen.
    """
    reminder = (
        db.query(Reminder)
        .filter(Reminder.patient_id == patient_id, Reminder.status == "pending")
        .first()
    )
    if not reminder:
        # If none pending, take any reminder
        reminder = db.query(Reminder).filter(Reminder.patient_id == patient_id).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="No reminders found to trigger")

    now = datetime.utcnow()
    reminder.status = "triggered"
    reminder.last_triggered_at = now
    reminder.retry_count = 0

    log = ReminderLog(
        patient_id=patient_id,
        reminder_id=reminder.id,
        action="triggered",
        outcome="ignored",
        details=f"Manually triggered via Demo Tools: {reminder.title}",
        timestamp=now,
    )
    db.add(log)
    db.commit()

    return {
        "status": "triggered",
        "reminder_id": reminder.id,
        "title": reminder.title,
        "message": reminder.message,
    }
