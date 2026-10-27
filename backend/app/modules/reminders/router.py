from datetime import datetime, timedelta
from typing import List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Reminder, ReminderLog
from app.db.session import get_db
from app.modules.alerts.service import notify_caregivers
from app.modules.reminders.scheduler import compute_next_occurrence

router = APIRouter()


class ReminderCreate(BaseModel):
    title: str
    message: Optional[str] = None
    scheduled_time: str  # Format "HH:MM", e.g. "09:00"
    frequency: Optional[str] = "daily"
    rrule: Optional[str] = None
    is_critical: Optional[bool] = False
    escalate_after_min: Optional[int] = 10
    patient_id: Optional[int] = None


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    scheduled_time: Optional[str] = None
    frequency: Optional[str] = None
    rrule: Optional[str] = None
    is_critical: Optional[bool] = None
    escalate_after_min: Optional[int] = None


class ReminderResponse(BaseModel):
    id: int
    patient_id: int
    title: str
    message: Optional[str] = None
    scheduled_time: str
    frequency: str
    rrule: Optional[str] = None
    is_critical: bool
    escalate_after_min: int
    status: str
    retry_count: int
    last_triggered_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
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
    now = datetime.utcnow()
    next_occ = compute_next_occurrence(payload.scheduled_time.strip(), payload.rrule, now)

    reminder = Reminder(
        patient_id=pid,
        title=payload.title.strip(),
        message=payload.message.strip() if payload.message else None,
        scheduled_time=payload.scheduled_time.strip(),
        frequency=payload.frequency or "daily",
        rrule=payload.rrule,
        is_critical=payload.is_critical or False,
        escalate_after_min=payload.escalate_after_min or settings.ESCALATE_AFTER_MIN,
        status="pending",
        next_run_at=next_occ,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("", response_model=List[ReminderResponse])
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


@router.get("/due", response_model=List[ReminderResponse])
def get_due_reminders(
    patient_id: int = Query(default=1),
    db: Session = Depends(get_db),
):
    """
    Returns currently due/triggered reminders for the app to poll every 15 seconds.
    """
    due_reminders = (
        db.query(Reminder)
        .filter(
            Reminder.patient_id == patient_id,
            Reminder.status.in_(["triggered", "repeated"]),
        )
        .order_by(Reminder.last_triggered_at.desc())
        .all()
    )
    return due_reminders


@router.put("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: int,
    payload: ReminderUpdate,
    db: Session = Depends(get_db),
):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    if payload.title is not None:
        reminder.title = payload.title.strip()
    if payload.message is not None:
        reminder.message = payload.message.strip()
    if payload.scheduled_time is not None:
        reminder.scheduled_time = payload.scheduled_time.strip()
    if payload.frequency is not None:
        reminder.frequency = payload.frequency
    if payload.rrule is not None:
        reminder.rrule = payload.rrule
    if payload.is_critical is not None:
        reminder.is_critical = payload.is_critical
    if payload.escalate_after_min is not None:
        reminder.escalate_after_min = payload.escalate_after_min

    # Recompute next occurrence
    reminder.next_run_at = compute_next_occurrence(reminder.scheduled_time, reminder.rrule, datetime.utcnow())

    db.commit()
    db.refresh(reminder)
    return reminder


@router.delete("/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    db.delete(reminder)
    db.commit()
    return {"deleted": True, "reminder_id": reminder_id}


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

    # If snoozed: snooze by 5 minutes
    if payload.response == "snoozed":
        reminder.next_run_at = now + timedelta(minutes=5)
        reminder.last_triggered_at = None

    log = ReminderLog(
        patient_id=reminder.patient_id,
        reminder_id=reminder.id,
        action=payload.response,
        outcome=payload.response,
        details=f"Patient responded with: {payload.response}",
        timestamp=now,
    )
    db.add(log)

    if payload.response == "distressed":
        notify_caregivers(
            patient_id=reminder.patient_id,
            alert_type="distress_response",
            message=f"Patient responded with distress to reminder '{reminder.title}'.",
            reminder_id=reminder.id,
            db=db,
        )

    db.commit()
    db.refresh(reminder)
    return reminder
