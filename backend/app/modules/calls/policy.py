import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Person
from app.db.mongo import mongo_manager

logger = logging.getLogger(__name__)

# Allowed policy triggers (Rules only, never LLM)
ALLOWED_TRIGGERS = {
    "sos",
    "sos_button",
    "emergency_phrase",
    "voice_emergency",
    "reminder_escalation",
    "critical_reminder",
    "missed_checkins",
    "call_family",
    "manual",
}

EMERGENCY_TRIGGERS = {
    "sos",
    "sos_button",
    "emergency_phrase",
    "voice_emergency",
}


def is_in_quiet_hours(dt: Optional[datetime] = None) -> bool:
    """Checks if current local time is within quiet hours (e.g. 22:00 to 06:00)."""
    now = dt or datetime.now()
    hour = now.hour
    start = settings.QUIET_HOURS_START  # default 22
    end = settings.QUIET_HOURS_END      # default 6

    if start > end:  # spans midnight (22 to 6)
        return hour >= start or hour < end
    else:
        return start <= hour < end


async def check_call_policy(
    patient_id: int,
    reason: str,
    source: str,
    db: Session,
    override_now: Optional[datetime] = None,
    bypass_cooldown: bool = False,
) -> Tuple[bool, Optional[str], Optional[Person], List[Person]]:
    """
    Evaluates deterministic safety and throttling rules:
    1. Valid trigger check.
    2. Quiet hours check (only emergency triggers allowed during quiet hours).
    3. 2-minute cool-down between call attempts (bypassed if bypass_cooldown=True or manual).
    4. Max 3 call attempts per hour per patient.
    5. Resolves emergency contacts in priority order.

    Returns:
      (allowed, block_reason, primary_contact, all_emergency_contacts)
    """
    now = override_now or datetime.utcnow()
    normalized_source = source.lower().strip()

    # 1. Rule trigger whitelist check
    if normalized_source not in ALLOWED_TRIGGERS and not any(t in normalized_source for t in ALLOWED_TRIGGERS):
        logger.warning(f"Call request blocked: Invalid source trigger '{source}'")
        return False, f"Call source '{source}' is not an authorized trigger.", None, []

    is_emergency = normalized_source in EMERGENCY_TRIGGERS or "sos" in normalized_source or "emergency" in normalized_source

    # 2. Quiet hours rule
    local_now = datetime.now() if override_now is None else override_now
    if is_in_quiet_hours(local_now):
        if not is_emergency:
            logger.info("Call blocked: Non-emergency trigger during quiet hours.")
            return False, "Non-emergency calls are paused during quiet hours (10:00 PM to 6:00 AM).", None, []

    # 3. Retrieve recent calls from MongoDB `calls` collection
    calls_coll = mongo_manager.get_collection("calls")
    one_hour_ago = now - timedelta(hours=1)
    cooldown_cutoff = now - timedelta(seconds=settings.CALL_COOLDOWN_SECONDS)

    try:
        recent_cursor = calls_coll.find({
            "patient_id": patient_id,
            "created_at": {"$gte": one_hour_ago.isoformat()}
        })
        recent_calls = await recent_cursor.to_list(length=100)
    except Exception as e:
        logger.warning(f"Error querying calls collection: {e}")
        recent_calls = []

    # 4. Check 2-minute cool-down (skipped if bypass_cooldown=True or manual caretaker trigger)
    if not bypass_cooldown and normalized_source != "manual":
        for call in recent_calls:
            call_time_str = call.get("created_at")
            if call_time_str:
                try:
                    call_dt = datetime.fromisoformat(call_time_str)
                    if call_dt > cooldown_cutoff:
                        remaining_sec = int((call_dt + timedelta(seconds=settings.CALL_COOLDOWN_SECONDS) - now).total_seconds())
                        wait_str = f"{max(1, remaining_sec)} seconds" if remaining_sec < 60 else "2 minutes"
                        return False, f"Please wait {wait_str} before attempting another call.", None, []
                except Exception:
                    pass

    # 5. Check hourly limit (Max 3 per hour, skipped if manual bypass)
    if not bypass_cooldown and normalized_source != "manual" and len(recent_calls) >= settings.CALL_MAX_PER_HOUR:
        return False, f"Maximum {settings.CALL_MAX_PER_HOUR} calls per hour reached. Please wait before trying again.", None, []

    # 6. Retrieve emergency contacts
    contacts = (
        db.query(Person)
        .filter(Person.patient_id == patient_id, Person.is_emergency_contact == True)
        .order_by(Person.priority.asc(), Person.id.asc())
        .all()
    )

    # Fallback to general people if none marked as emergency contact
    if not contacts:
        contacts = (
            db.query(Person)
            .filter(Person.patient_id == patient_id)
            .order_by(Person.id.asc())
            .all()
        )

    if not contacts:
        # Emergency placeholder using configured caregiver phone
        primary = Person(
            id=0,
            patient_id=patient_id,
            name="Caregiver",
            relationship="caregiver",
            phone=settings.CAREGIVER_PHONE,
            is_emergency_contact=True,
            priority=1,
        )
        return True, None, primary, [primary]

    # Primary is the first in priority order
    primary = contacts[0]
    if not primary.phone:
        primary.phone = settings.CAREGIVER_PHONE

    return True, None, primary, contacts
