import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler

from app.db.models import Reminder, ReminderLog
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def stub_caregiver_alert(patient_id: int, reminder_title: str, reason: str) -> None:
    """
    Caregiver alert stub as specified in requirements.
    Logs alert and creates a caregiver alert log record.
    """
    logger.warning(
        f"[CAREGIVER ALERT STUB] Patient {patient_id} alert for '{reminder_title}'. Reason: {reason}"
    )


def process_reminders() -> None:
    """
    Periodically checks for:
    1. Due reminders that need to be triggered.
    2. Unacknowledged reminders past 5 minutes:
       - Repeats once (retry_count=0 -> 1)
       - Escalates on second expiry (retry_count>=1 -> escalated, log caregiver alert)
    """
    db = SessionLocal()
    now = datetime.utcnow()
    try:
        # Check unacknowledged reminders that were triggered or repeated
        active_reminders = (
            db.query(Reminder)
            .filter(Reminder.status.in_(["triggered", "repeated"]))
            .all()
        )

        for rem in active_reminders:
            if not rem.last_triggered_at:
                continue

            time_elapsed = now - rem.last_triggered_at
            if time_elapsed >= timedelta(minutes=5):
                if rem.retry_count == 0:
                    # Repeat once
                    rem.retry_count = 1
                    rem.status = "repeated"
                    rem.last_triggered_at = now
                    log = ReminderLog(
                        patient_id=rem.patient_id,
                        reminder_id=rem.id,
                        action="repeated",
                        details="Reminder unacknowledged after 5 minutes; repeated once.",
                        timestamp=now,
                    )
                    db.add(log)
                    logger.info(f"Reminder {rem.id} repeated.")
                else:
                    # Escalated
                    rem.status = "escalated"
                    log_esc = ReminderLog(
                        patient_id=rem.patient_id,
                        reminder_id=rem.id,
                        action="escalated",
                        details="Reminder unacknowledged after repetition; marked escalated.",
                        timestamp=now,
                    )
                    db.add(log_esc)

                    # Stub caregiver alert
                    stub_caregiver_alert(
                        rem.patient_id,
                        rem.title,
                        "Unacknowledged after retry; escalated to caregiver.",
                    )
                    log_alert = ReminderLog(
                        patient_id=rem.patient_id,
                        reminder_id=rem.id,
                        action="caregiver_alert",
                        details="[STUBBED ALERT] Caregiver notified about unacknowledged reminder.",
                        timestamp=now,
                    )
                    db.add(log_alert)
                    logger.warning(f"Reminder {rem.id} escalated to caregiver.")

        # Check pending reminders that match current time
        # For simplicity and robustness, pending reminders due can be triggered
        current_time_str = now.strftime("%H:%M")
        pending_reminders = (
            db.query(Reminder)
            .filter(Reminder.status == "pending")
            .all()
        )
        for rem in pending_reminders:
            if rem.scheduled_time == current_time_str:
                rem.status = "triggered"
                rem.last_triggered_at = now
                log_trig = ReminderLog(
                    patient_id=rem.patient_id,
                    reminder_id=rem.id,
                    action="triggered",
                    details=f"Reminder scheduled for {rem.scheduled_time} triggered.",
                    timestamp=now,
                )
                db.add(log_trig)

        db.commit()
    except Exception as e:
        logger.error(f"Error processing reminders: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(
            process_reminders,
            "interval",
            seconds=30,
            id="process_reminders_job",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("APScheduler reminder job started.")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
