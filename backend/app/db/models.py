from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship as orm_relationship

from app.db.session import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), default="Default Patient", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    people = orm_relationship("Person", back_populates="patient", cascade="all, delete-orphan")
    memories = orm_relationship("Memory", back_populates="patient", cascade="all, delete-orphan")
    reminders = orm_relationship("Reminder", back_populates="patient", cascade="all, delete-orphan")
    consents = orm_relationship("Consent", back_populates="patient", cascade="all, delete-orphan")
    alerts = orm_relationship("Alert", back_populates="patient", cascade="all, delete-orphan")
    audit_logs = orm_relationship("AuditLog", back_populates="patient", cascade="all, delete-orphan")
    places = orm_relationship("Place", back_populates="patient", cascade="all, delete-orphan")


class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    name = Column(String(120), nullable=False)
    relationship = Column(String(80), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = orm_relationship("Patient", back_populates="people")
    faces = orm_relationship("PersonFace", back_populates="person", cascade="all, delete-orphan")


class PersonFace(Base):
    __tablename__ = "person_faces"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    person_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(255), nullable=False)
    embedding_json = Column(Text, nullable=True)
    quality_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    person = orm_relationship("Person", back_populates="faces")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    text = Column(Text, nullable=False)
    category = Column(String(50), nullable=True, default="general")
    embedding_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = orm_relationship("Patient", back_populates="memories")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    scheduled_time = Column(String(20), nullable=False)  # e.g., "09:00"
    frequency = Column(String(50), default="daily", nullable=False)
    rrule = Column(String(200), nullable=True)  # iCal RRULE e.g. "FREQ=DAILY" or "FREQ=WEEKLY;BYDAY=MO,WE,FR"
    is_critical = Column(Boolean, default=False, nullable=False)
    escalate_after_min = Column(Integer, default=10, nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, triggered, acknowledged, snoozed, distressed, escalated
    retry_count = Column(Integer, default=0, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = orm_relationship("Patient", back_populates="reminders")
    logs = orm_relationship("ReminderLog", back_populates="reminder", cascade="all, delete-orphan")


class ReminderLog(Base):
    __tablename__ = "reminder_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # triggered, repeated, acknowledged, snoozed, distressed, escalated
    outcome = Column(String(50), default="ignored", nullable=False)  # ignored, repeated, acknowledged, snoozed, distressed, escalated
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    reminder = orm_relationship("Reminder", back_populates="logs")


class Consent(Base):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    person_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=True)
    consent_given = Column(Boolean, nullable=False, default=True)
    consent_type = Column(String(100), default="face_recognition_and_data_storage", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = orm_relationship("Patient", back_populates="consents")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id", ondelete="SET NULL"), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False)  # "sos_button", "emergency_phrase", "reminder_escalated", "distress_response"
    message = Column(Text, nullable=False)
    status = Column(String(50), default="sent", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = orm_relationship("Patient", back_populates="alerts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    action = Column(String(50), nullable=False)  # "create_person", "delete_person", "export_data", "wipe_all_data", "alert_created", "recognition"
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = orm_relationship("Patient", back_populates="audit_logs")


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    name = Column(String(120), nullable=False)
    address = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = orm_relationship("Patient", back_populates="places")
