import json
import logging
import os
import sys

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import numpy as np
from app.core.config import settings
from app.db.models import Consent, Memory, Patient, Person, PersonFace, Reminder, ReminderLog
from app.db.session import SessionLocal, init_db
from app.modules.faces.engine import face_engine
from app.modules.memory.retrieval import memory_retrieval

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_demo_data")


def create_demo_face_image(name: str, color: tuple) -> bytes:
    """Generates a clean synthetic face bitmap for demo face registration."""
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (200, 200), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        # Head
        draw.ellipse([50, 40, 150, 150], fill=color, outline=(30, 30, 30), width=2)
        # Eyes
        draw.ellipse([70, 75, 85, 90], fill=(20, 20, 20))
        draw.ellipse([115, 75, 130, 90], fill=(20, 20, 20))
        # Smile
        draw.arc([75, 100, 125, 130], start=10, end=170, fill=(20, 20, 20), width=3)
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()
    except Exception:
        # Fallback raw byte pattern
        return b"\xFF\xD8\xFF\xE0" + bytes([hash(name) % 256]) * 1024


def seed_data() -> None:
    logger.info("Initializing database...")
    settings.init_directories()
    init_db()

    db = SessionLocal()
    pid = settings.DEFAULT_PATIENT_ID

    try:
        # 1. Ensure Patient exists
        patient = db.query(Patient).filter(Patient.id == pid).first()
        if not patient:
            patient = Patient(id=pid, name="Primary Patient")
            db.add(patient)
            db.commit()

        # 2. Seed 3 People
        people_data = [
            {
                "name": "Priya",
                "relationship": "daughter",
                "notes": "Lives in Bangalore. Visits on weekends with grandson Kabir.",
                "color": (255, 200, 210),
            },
            {
                "name": "Dr. Sharma",
                "relationship": "doctor",
                "notes": "Family physician at Apollo Clinic. Checks blood pressure monthly.",
                "color": (200, 220, 255),
            },
            {
                "name": "Arun",
                "relationship": "son",
                "notes": "Lives in Indiranagar, Bangalore. Calls every evening at 7:00 PM.",
                "color": (220, 255, 220),
            },
        ]

        logger.info("Seeding people and face embeddings...")
        for pdata in people_data:
            existing = (
                db.query(Person)
                .filter(Person.patient_id == pid, Person.name == pdata["name"])
                .first()
            )
            if not existing:
                person = Person(
                    patient_id=pid,
                    name=pdata["name"],
                    relationship=pdata["relationship"],
                    notes=pdata["notes"],
                )
                db.add(person)
                db.commit()
                db.refresh(person)

                # Consent
                consent = Consent(
                    patient_id=pid,
                    person_id=person.id,
                    consent_given=True,
                    consent_type="face_recognition_and_data_storage",
                )
                db.add(consent)

                # Create demo face file & embedding
                img_bytes = create_demo_face_image(pdata["name"], pdata["color"])
                emb, quality = face_engine.extract_face_embedding(img_bytes)
                if emb is None:
                    # Deterministic distinct vector per person
                    emb = np.zeros(512, dtype=np.float32)
                    emb[hash(pdata["name"]) % 512] = 1.0
                    emb = face_engine._normalize(emb)
                    quality = 0.85

                face_path = os.path.join(settings.UPLOAD_DIR, f"demo_{person.id}_{pdata['name']}.jpg")
                with open(face_path, "wb") as f:
                    f.write(img_bytes)

                face_record = PersonFace(
                    patient_id=pid,
                    person_id=person.id,
                    file_path=face_path,
                    embedding_json=json.dumps(emb.tolist()),
                    quality_score=quality,
                )
                db.add(face_record)
                db.commit()
                db.refresh(face_record)

                face_engine.add_face(face_record.id, person.id, emb)
                logger.info(f"Seeded person '{person.name}' (id={person.id}) with face record {face_record.id}")

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

        logger.info("Seeding 10 memories and multilingual embeddings...")
        for text in memories_text:
            existing = (
                db.query(Memory)
                .filter(Memory.patient_id == pid, Memory.text == text)
                .first()
            )
            if not existing:
                mem = Memory(
                    patient_id=pid,
                    text=text,
                    category="family_health",
                )
                db.add(mem)
                db.commit()
                db.refresh(mem)

                # Embed into FAISS
                embedding = memory_retrieval.add_memory(mem.id, mem.text)
                mem.embedding_json = json.dumps(embedding)
                db.commit()
                logger.info(f"Seeded memory {mem.id}: '{text[:40]}...'")

        # 4. Seed Daily 9:00 AM Blood Pressure Reminder
        existing_reminder = (
            db.query(Reminder)
            .filter(Reminder.patient_id == pid, Reminder.scheduled_time == "09:00")
            .first()
        )
        if not existing_reminder:
            reminder = Reminder(
                patient_id=pid,
                title="Take Blood Pressure Medication (Amlodipine 5mg)",
                scheduled_time="09:00",
                frequency="daily",
                status="pending",
            )
            db.add(reminder)
            db.commit()
            db.refresh(reminder)

            log = ReminderLog(
                patient_id=pid,
                reminder_id=reminder.id,
                action="created",
                details="Daily 9:00 AM blood pressure reminder initialized.",
            )
            db.add(log)
            db.commit()
            logger.info(f"Seeded reminder {reminder.id}: '{reminder.title}' at {reminder.scheduled_time}")

        logger.info("Demo data seeding completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
