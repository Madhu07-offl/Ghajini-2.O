import logging
from datetime import datetime
from typing import Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Alert, AuditLog
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def notify_caregivers(
    patient_id: int,
    alert_type: str,
    message: str,
    reminder_id: Optional[int] = None,
    db: Optional[Session] = None,
) -> Alert:
    """
    Writes to alerts table, writes to audit log, prints log line,
    and calls Twilio SMS only if FEATURE_SMS=True and keys exist.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        now = datetime.utcnow()
        alert = Alert(
            patient_id=patient_id,
            reminder_id=reminder_id,
            alert_type=alert_type,
            message=message,
            status="sent",
            created_at=now,
        )
        db.add(alert)

        audit = AuditLog(
            patient_id=patient_id,
            action="alert_created",
            details=f"[{alert_type}] {message}",
            timestamp=now,
        )
        db.add(audit)
        db.commit()
        db.refresh(alert)

        logger.warning(f"[CAREGIVER ALERT] Patient {patient_id} - {alert_type}: {message}")

        # Send Twilio SMS if enabled and configured
        if (
            settings.FEATURE_SMS
            and settings.TWILIO_ACCOUNT_SID
            and settings.TWILIO_AUTH_TOKEN
            and settings.TWILIO_FROM_NUMBER
            and settings.CAREGIVER_PHONE
        ):
            try:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
                auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                data = {
                    "From": settings.TWILIO_FROM_NUMBER,
                    "To": settings.CAREGIVER_PHONE,
                    "Body": f"[Ghajini 2.0 Alert] {message}",
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, auth=auth, data=data)
                    if resp.status_code in (200, 201):
                        logger.info("Caregiver Twilio SMS sent successfully.")
                    else:
                        logger.warning(f"Twilio SMS response: {resp.status_code} {resp.text}")
            except Exception as e:
                logger.error(f"Failed to send Twilio SMS: {e}")

        return alert
    finally:
        if close_db:
            db.close()
