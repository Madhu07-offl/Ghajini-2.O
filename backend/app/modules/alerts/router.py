from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Alert
from app.db.session import get_db
from app.modules.alerts.service import notify_caregivers

router = APIRouter()


class AlertResponse(BaseModel):
    id: int
    patient_id: int
    reminder_id: Optional[int] = None
    alert_type: str
    message: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SOSRequest(BaseModel):
    patient_id: Optional[int] = None
    note: Optional[str] = None


@router.post("/help", status_code=status.HTTP_200_OK)
def trigger_sos_help(
    payload: Optional[SOSRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Trigger emergency SOS alert: calls notify_caregivers() and returns reassurance message.
    """
    pid = payload.patient_id if payload and payload.patient_id else settings.DEFAULT_PATIENT_ID
    note = payload.note if payload and payload.note else "Patient pressed the SOS help button."
    message = f"EMERGENCY SOS: {note}"

    notify_caregivers(
        patient_id=pid,
        alert_type="sos_button",
        message=message,
        db=db,
    )

    return {
        "status": "alert_sent",
        "message": "Your family has been told.",
    }


@router.get("", response_model=List[AlertResponse])
def get_recent_alerts(
    patient_id: int = Query(default=1),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    alerts = (
        db.query(Alert)
        .filter(Alert.patient_id == patient_id)
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .all()
    )
    return alerts
