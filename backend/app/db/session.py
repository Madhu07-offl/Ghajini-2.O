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
