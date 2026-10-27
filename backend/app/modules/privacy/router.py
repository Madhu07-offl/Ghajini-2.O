import os
import shutil
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Consent, Memory, Person, PersonFace, Reminder, ReminderLog
from app.db.session import get_db
from app.modules.faces.engine import face_engine
from app.modules.memory.retrieval import memory_retrieval

router = APIRouter()


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

    # Clean upload directory if possible
    if os.path.exists(settings.UPLOAD_DIR):
        try:
            for fname in os.listdir(settings.UPLOAD_DIR):
                fpath = os.path.join(settings.UPLOAD_DIR, fname)
                if os.path.isfile(fpath):
                    os.remove(fpath)
        except Exception:
            pass

    # 3. Delete database records
    db.query(ReminderLog).filter(ReminderLog.patient_id == patient_id).delete()
    db.query(Reminder).filter(Reminder.patient_id == patient_id).delete()
    db.query(Memory).filter(Memory.patient_id == patient_id).delete()
    db.query(PersonFace).filter(PersonFace.patient_id == patient_id).delete()
    db.query(Consent).filter(Consent.patient_id == patient_id).delete()
    db.query(Person).filter(Person.patient_id == patient_id).delete()

    db.commit()

    return {
        "cleared": True,
        "patient_id": patient_id,
        "message": "All personal data, memories, face images, and indices have been permanently erased.",
    }
