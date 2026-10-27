from datetime import datetime
from typing import List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Reminder, ReminderLog
from app.db.session import get_db
from app.modules.reminders.scheduler import stub_caregiver_alert

router = APIRouter()


class ReminderCreate(BaseModel):
    title: str
    scheduled_time: str  # Format "HH:MM", e.g. "09:00"
    frequency: Optional[str] = "daily"
    patient_id: Optional[int] = None


class ReminderResponse(BaseModel):
    id: int
    patient_id: int
    title: str
    scheduled_time: str
    frequency: str
    status: str
    retry_count: int
    last_triggered_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReminderRespondRequest(BaseModel):
    response: Literal["acknowledged", "snoozed", "distressed"]


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
):
    pid = payload.patient_id or settings.DEFAULT_PATIENT_ID
    reminder = Reminder(
        patient_id=pid,
        title=payload.title.strip(),
        scheduled_time=payload.scheduled_time.strip(),
        frequency=payload.frequency or "daily",
        status="pending",
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("/upcoming", response_model=List[ReminderResponse])
def get_upcoming_reminders(
    patient_id: int = Query(default=1),
    db: Session = Depends(get_db),
):
    reminders = (
        db.query(Reminder)
        .filter(Reminder.patient_id == patient_id)
        .order_by(Reminder.scheduled_time.asc())
        .all()
    )
    return reminders


@router.post("/{reminder_id}/respond", response_model=ReminderResponse)
def respond_to_reminder(
    reminder_id: int,
    payload: ReminderRespondRequest,
    db: Session = Depends(get_db),
):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    now = datetime.utcnow()
    reminder.status = payload.response
    log = ReminderLog(
        patient_id=reminder.patient_id,
        reminder_id=reminder.id,
        action=payload.response,
        details=f"Patient responded with: {payload.response}",
        timestamp=now,
    )
    db.add(log)

    if payload.response == "distressed":
        stub_caregiver_alert(
            reminder.patient_id,
            reminder.title,
            "Patient responded with distress to reminder.",
        )
        distress_log = ReminderLog(
            patient_id=reminder.patient_id,
            reminder_id=reminder.id,
            action="caregiver_alert",
            details="[STUBBED ALERT] Emergency alert sent to caregiver due to patient distress.",
            timestamp=now,
        )
        db.add(distress_log)

    db.commit()
    db.refresh(reminder)
    return reminder
