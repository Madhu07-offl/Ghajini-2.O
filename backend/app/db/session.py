from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import NullPool
from app.core.config import settings

connect_args = {}
engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 20}
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models here to ensure registration
    from app.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # SQLite auto-migration for newly added columns
    try:
        with engine.connect() as conn:
            reminders_cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(reminders)").fetchall()]
            if reminders_cols:
                if "message" not in reminders_cols:
                    conn.exec_driver_sql("ALTER TABLE reminders ADD COLUMN message TEXT")
                if "rrule" not in reminders_cols:
                    conn.exec_driver_sql("ALTER TABLE reminders ADD COLUMN rrule VARCHAR(255)")
                if "is_critical" not in reminders_cols:
                    conn.exec_driver_sql("ALTER TABLE reminders ADD COLUMN is_critical BOOLEAN DEFAULT 0")
                if "escalate_after_min" not in reminders_cols:
                    conn.exec_driver_sql("ALTER TABLE reminders ADD COLUMN escalate_after_min INTEGER DEFAULT 10")
                if "next_run_at" not in reminders_cols:
                    conn.exec_driver_sql("ALTER TABLE reminders ADD COLUMN next_run_at DATETIME")

            logs_cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(reminder_logs)").fetchall()]
            if logs_cols:
                if "outcome" not in logs_cols:
                    conn.exec_driver_sql("ALTER TABLE reminder_logs ADD COLUMN outcome VARCHAR(40) DEFAULT 'ignored'")

            people_cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(people)").fetchall()]
            if people_cols:
                if "phone" not in people_cols:
                    conn.exec_driver_sql("ALTER TABLE people ADD COLUMN phone VARCHAR(50)")
                if "is_emergency_contact" not in people_cols:
                    conn.exec_driver_sql("ALTER TABLE people ADD COLUMN is_emergency_contact BOOLEAN DEFAULT 0")
                if "priority" not in people_cols:
                    conn.exec_driver_sql("ALTER TABLE people ADD COLUMN priority INTEGER DEFAULT 1")
            conn.commit()
    except Exception:
        pass

    # Ensure default patient exists
    db = SessionLocal()
    try:
        patient = db.query(models.Patient).filter(models.Patient.id == settings.DEFAULT_PATIENT_ID).first()
        if not patient:
            patient = models.Patient(id=settings.DEFAULT_PATIENT_ID, name="Default Patient")
            db.add(patient)
            db.commit()

        # Ensure demo emergency contacts are populated
        priya = db.query(models.Person).filter(models.Person.name == "Priya").first()
        if priya:
            if not priya.phone:
                priya.phone = "+919876543210"
            priya.is_emergency_contact = True
            priya.priority = 1

        arun = db.query(models.Person).filter(models.Person.name == "Arun").first()
        if arun:
            if not arun.phone:
                arun.phone = "+919876543211"
            arun.is_emergency_contact = True
            arun.priority = 2

        # Ensure initial baseline CardioLife vitals exist
        from datetime import datetime
        vital = db.query(models.VitalsReading).filter(models.VitalsReading.patient_id == settings.DEFAULT_PATIENT_ID).first()
        if not vital:
            vital = models.VitalsReading(
                patient_id=settings.DEFAULT_PATIENT_ID,
                heart_rate_bpm=72,
                blood_pressure_systolic=120,
                blood_pressure_diastolic=80,
                oxygen_saturation=98,
                hrv_ms=48,
                status="normal",
                notes="Resting baseline reading",
                recorded_at=datetime.utcnow(),
            )
            db.add(vital)
        db.commit()
    finally:
        db.close()
