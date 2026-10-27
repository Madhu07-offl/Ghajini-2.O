import io
import json
import os
import zipfile
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import (
    Alert,
    AuditLog,
    Consent,
    Memory,
    Patient,
    Person,
    PersonFace,
    Reminder,
    ReminderLog,
)
from app.db.session import get_db
from app.modules.faces.engine import face_engine
from app.modules.memory.retrieval import memory_retrieval

router = APIRouter()


@router.get("/export", status_code=status.HTTP_200_OK)
def export_personal_data(
    patient_id: int = Query(default=1),
    db: Session = Depends(get_db),
):
    """
    Returns a ZIP archive with all patient data exported as JSON.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    people = db.query(Person).filter(Person.patient_id == patient_id).all()
    faces = db.query(PersonFace).filter(PersonFace.patient_id == patient_id).all()
    memories = db.query(Memory).filter(Memory.patient_id == patient_id).all()
    reminders = db.query(Reminder).filter(Reminder.patient_id == patient_id).all()
    logs = db.query(ReminderLog).filter(ReminderLog.patient_id == patient_id).all()
    consents = db.query(Consent).filter(Consent.patient_id == patient_id).all()
    alerts = db.query(Alert).filter(Alert.patient_id == patient_id).all()
    audits = db.query(AuditLog).filter(AuditLog.patient_id == patient_id).all()

    export_dict = {
        "export_metadata": {
            "patient_id": patient_id,
            "exported_at": datetime.utcnow().isoformat(),
            "format": "Ghajini 2.0 GDPR/HIPAA compliant archive",
        },
        "patient": {
            "id": patient.id,
            "name": patient.name,
            "created_at": patient.created_at.isoformat(),
        } if patient else None,
        "people": [
            {
                "id": p.id,
                "name": p.name,
                "relationship": p.relationship,
                "notes": p.notes,
                "created_at": p.created_at.isoformat(),
            }
            for p in people
        ],
        "faces": [
            {
                "id": f.id,
                "person_id": f.person_id,
                "file_path": f.file_path,
                "quality_score": f.quality_score,
                "created_at": f.created_at.isoformat(),
            }
            for f in faces
        ],
        "memories": [
            {
                "id": m.id,
                "text": m.text,
                "category": m.category,
                "created_at": m.created_at.isoformat(),
            }
            for m in memories
        ],
        "reminders": [
            {
                "id": r.id,
                "title": r.title,
                "message": r.message,
                "scheduled_time": r.scheduled_time,
                "frequency": r.frequency,
                "rrule": r.rrule,
                "is_critical": r.is_critical,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in reminders
        ],
        "reminder_logs": [
            {
                "id": l.id,
                "reminder_id": l.reminder_id,
                "action": l.action,
                "outcome": getattr(l, "outcome", "ignored"),
                "details": l.details,
                "timestamp": l.timestamp.isoformat(),
            }
            for l in logs
        ],
        "consents": [
            {
                "id": c.id,
                "person_id": c.person_id,
                "consent_given": c.consent_given,
                "consent_type": c.consent_type,
                "created_at": c.created_at.isoformat(),
            }
            for c in consents
        ],
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "message": a.message,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
        "audit_logs": [
            {
                "id": au.id,
                "action": au.action,
                "details": au.details,
                "timestamp": au.timestamp.isoformat(),
            }
            for au in audits
        ],
    }

    # Record export in audit log
    audit_record = AuditLog(
        patient_id=patient_id,
        action="export_data",
        details="Exported all patient data as JSON ZIP archive.",
        timestamp=datetime.utcnow(),
    )
    db.add(audit_record)
    db.commit()

    # Package into a ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("export.json", json.dumps(export_dict, indent=2))

    zip_bytes = zip_buffer.getvalue()

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=ghajini_patient_{patient_id}_export.zip"
        },
    )


@router.delete("/all", status_code=status.HTTP_200_OK)
def wipe_all_personal_data(
    patient_id: int = Query(default=1),
    db: Session = Depends(get_db),
):
    """
    Deletes all personal data for patient:
    - memories
    - reminders and reminder logs
    - people, faces, and consent records
    - alerts and audit logs
    - files on disk
    - in-memory FAISS indices
    """
    # 1. Clear FAISS indices
    face_engine.clear()
    memory_retrieval.clear()

    # 2. Delete face image files from upload directory
    faces = db.query(PersonFace).filter(PersonFace.patient_id == patient_id).all()
    for face in faces:
        if face.file_path and os.path.exists(face.file_path):
            try:
                os.remove(face.file_path)
            except Exception:
                pass

    if os.path.exists(settings.UPLOAD_DIR):
        try:
            for fname in os.listdir(settings.UPLOAD_DIR):
                fpath = os.path.join(settings.UPLOAD_DIR, fname)
                if os.path.isfile(fpath):
                    os.remove(fpath)
        except Exception:
            pass

    # 3. Delete database records
    db.query(Alert).filter(Alert.patient_id == patient_id).delete()
    db.query(ReminderLog).filter(ReminderLog.patient_id == patient_id).delete()
    db.query(Reminder).filter(Reminder.patient_id == patient_id).delete()
    db.query(Memory).filter(Memory.patient_id == patient_id).delete()
    db.query(PersonFace).filter(PersonFace.patient_id == patient_id).delete()
    db.query(Consent).filter(Consent.patient_id == patient_id).delete()
    db.query(Person).filter(Person.patient_id == patient_id).delete()
    db.query(AuditLog).filter(AuditLog.patient_id == patient_id).delete()

    db.commit()

    return {
        "cleared": True,
        "patient_id": patient_id,
        "message": "All personal data, memories, face images, and indices have been permanently erased.",
    }
