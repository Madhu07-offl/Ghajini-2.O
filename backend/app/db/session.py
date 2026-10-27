from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
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
    finally:
        db.close()
