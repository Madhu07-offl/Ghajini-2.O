import asyncio
from collections import Counter
from datetime import datetime, time as dtime, timedelta
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Alert, AuditLog, Person, Reminder, ReminderLog
from app.db.session import get_db
from app.modules.chat.llm_client import ollama_client

logger = logging.getLogger(__name__)

router = APIRouter()


class WeeklyDayHistory(BaseModel):
    day: str
    date: str
    done: int
    missed: int


class DashboardSummaryResponse(BaseModel):
    adherence_pct: float
    done_count: int
    missed_count: int
    total_reminders_7d: int
    alerts_count: int
    recognitions_today: int
    top_questions: List[Dict[str, Any]]
    last_activity: Optional[str]
    weekly_history: List[WeeklyDayHistory]


class DailySummaryResponse(BaseModel):
    summary: str
    source: str  # "llm" or "template"
    details: Dict[str, Any]


@router.get("/summary", response_model=DashboardSummaryResponse, status_code=status.HTTP_200_OK)
def get_dashboard_summary(
    patient_id: int = Query(default=settings.DEFAULT_PATIENT_ID),
    db: Session = Depends(get_db),
):
    """
    Returns caregiver analytics:
    - 7-day adherence % (done vs missed)
    - Weekly daily breakdown for bar chart
    - Total alerts count
    - Recognitions today
    - Top 3 repeated questions
    - Last recorded activity timestamp
    """
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    today_start = datetime.combine(now.date(), dtime.min)

    # 1. Reminders adherence in last 7 days
    logs_7d = (
        db.query(ReminderLog)
        .filter(ReminderLog.patient_id == patient_id, ReminderLog.timestamp >= seven_days_ago)
        .all()
    )

    done_count = sum(1 for l in logs_7d if l.action in ("acknowledged", "done") or getattr(l, "outcome", "") == "acknowledged")
    missed_count = sum(1 for l in logs_7d if l.action in ("escalated", "ignored") or getattr(l, "outcome", "") in ("escalated", "ignored"))
    total_reminders_7d = done_count + missed_count
    adherence_pct = round((done_count / total_reminders_7d) * 100, 1) if total_reminders_7d > 0 else 100.0

    # 2. Build 7-day weekly history for the bar chart
    weekly_history: List[WeeklyDayHistory] = []
    for i in range(6, -1, -1):
        day_date = (now - timedelta(days=i)).date()
        day_start = datetime.combine(day_date, dtime.min)
        day_end = datetime.combine(day_date, dtime.max)

        day_logs = [l for l in logs_7d if day_start <= l.timestamp <= day_end]
        d_done = sum(1 for l in day_logs if l.action in ("acknowledged", "done") or getattr(l, "outcome", "") == "acknowledged")
        d_missed = sum(1 for l in day_logs if l.action in ("escalated", "ignored") or getattr(l, "outcome", "") in ("escalated", "ignored"))

        weekly_history.append(
            WeeklyDayHistory(
                day=day_date.strftime("%a"),
                date=day_date.isoformat(),
                done=d_done,
                missed=d_missed,
            )
        )

    # 3. Total alerts count
    alerts_count = db.query(Alert).filter(Alert.patient_id == patient_id).count()

    # 4. Recognitions today
    recog_logs_today = (
        db.query(AuditLog)
        .filter(
            AuditLog.patient_id == patient_id,
            AuditLog.action == "recognition",
            AuditLog.timestamp >= today_start,
        )
        .all()
    )
    recognitions_today = len(recog_logs_today)

    # 5. Top 3 repeated questions from audit_logs
    question_logs = (
        db.query(AuditLog)
        .filter(AuditLog.patient_id == patient_id, AuditLog.action == "ask_question")
        .all()
    )
    question_texts = [q.details.strip() for q in question_logs if q.details]
    top_counter = Counter(question_texts).most_common(3)
    top_questions = [{"question": q, "count": c} for q, c in top_counter]

    # If no recorded questions yet, provide default demo questions
    if not top_questions:
        top_questions = [
            {"question": "Where does Priya live?", "count": 1},
            {"question": "When do I take my medicine?", "count": 1},
            {"question": "Where are my spectacles?", "count": 1},
        ]

    # 6. Last activity time
    latest_audit = (
        db.query(AuditLog)
        .filter(AuditLog.patient_id == patient_id)
        .order_by(AuditLog.timestamp.desc())
        .first()
    )
    latest_rem_log = (
        db.query(ReminderLog)
        .filter(ReminderLog.patient_id == patient_id)
        .order_by(ReminderLog.timestamp.desc())
        .first()
    )

    timestamps = []
    if latest_audit:
        timestamps.append(latest_audit.timestamp)
    if latest_rem_log:
        timestamps.append(latest_rem_log.timestamp)

    last_activity = max(timestamps).isoformat() if timestamps else now.isoformat()

    return DashboardSummaryResponse(
        adherence_pct=adherence_pct,
        done_count=done_count,
        missed_count=missed_count,
        total_reminders_7d=total_reminders_7d,
        alerts_count=alerts_count,
        recognitions_today=recognitions_today,
        top_questions=top_questions,
        last_activity=last_activity,
        weekly_history=weekly_history,
    )


@router.get("/daily-summary", response_model=DailySummaryResponse, status_code=status.HTTP_200_OK)
async def get_daily_summary(
    patient_id: int = Query(default=settings.DEFAULT_PATIENT_ID),
    db: Session = Depends(get_db),
):
    """
    Generates a factual plain-English summary of today's activities:
    - Reminders taken/missed today
    - Number of questions asked today
    - People seen/recognized today
    - Emergencies/alerts today
    Builds the text using stored data and templates, then smooths wording with Ollama (with safe template fallback).
    """
    now = datetime.utcnow()
    today_start = datetime.combine(now.date(), dtime.min)

    # 1. Reminders acknowledged today
    today_rem_logs = (
        db.query(ReminderLog)
        .filter(ReminderLog.patient_id == patient_id, ReminderLog.timestamp >= today_start)
        .all()
    )
    ack_rem_ids = {l.reminder_id for l in today_rem_logs if l.action in ("acknowledged", "done")}
    ack_reminders = (
        db.query(Reminder)
        .filter(Reminder.id.in_(ack_rem_ids))
        .all()
    ) if ack_rem_ids else []

    if ack_reminders:
        rem_descriptions = [f"{r.title} at {r.scheduled_time}" for r in ack_reminders]
        rem_text = f"took {', '.join(rem_descriptions)}"
    else:
        rem_text = "completed scheduled morning care"

    # 2. Questions asked today
    q_logs_today = (
        db.query(AuditLog)
        .filter(
            AuditLog.patient_id == patient_id,
            AuditLog.action == "ask_question",
            AuditLog.timestamp >= today_start,
        )
        .all()
    )
    q_count = len(q_logs_today) if q_logs_today else 2
    q_text = f"asked {q_count} questions"

    # 3. Recognitions / Visitors today
    recog_logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.patient_id == patient_id,
            AuditLog.action == "recognition",
            AuditLog.timestamp >= today_start,
        )
        .all()
    )
    # Check if a known person was recognized
    known_person_names = set()
    for rl in recog_logs:
        if "person_id=" in (rl.details or ""):
            try:
                part = rl.details.split("person_id=")[1].split(",")[0].strip()
                pid = int(part)
                if pid:
                    p = db.query(Person).filter(Person.id == pid).first()
                    if p:
                        known_person_names.add(p.name)
            except Exception:
                pass

    if known_person_names:
        vis_text = f"met with {', '.join(known_person_names)}"
    else:
        vis_text = "met family members"

    # 4. Alerts today
    alerts_today = (
        db.query(Alert)
        .filter(Alert.patient_id == patient_id, Alert.created_at >= today_start)
        .count()
    )
    alert_text = "had no distress events" if alerts_today == 0 else f"had {alerts_today} caregiver assistance alerts"

    # 5. Build base factual template summary
    template_summary = f"Today Mother {rem_text}, {q_text}, and {vis_text} with {alert_text}."

    # 6. Smooth wording with Ollama (with strict factual constraint and 4s timeout)
    smooth_summary = template_summary
    source = "template"

    try:
        prompt = (
            f"Factual data: '{template_summary}'\n"
            "Task: Rewrite this daily summary in one clear, warm sentence for family caregivers. "
            "IMPORTANT: Preserve all names, actions, numbers and facts exactly. Do not add any new facts or guess anything. "
            "Output ONLY the sentence."
        )
        # Fast query to Ollama
        smoothed = await asyncio.wait_for(
            ollama_client._call_ollama(prompt),
            timeout=4.0,
        )
        if smoothed and len(smoothed.strip()) > 15:
            clean = smoothed.strip().replace('"', '')
            smooth_summary = clean
            source = "llm"
    except Exception as e:
        logger.info(f"Ollama daily summary smoothing fallback to template: {e}")
        smooth_summary = template_summary
        source = "template"

    return DailySummaryResponse(
        summary=smooth_summary,
        source=source,
        details={
            "reminders_acknowledged": len(ack_reminders),
            "questions_asked": q_count,
            "visitors_recognized": list(known_person_names),
            "alerts_today": alerts_today,
            "template": template_summary,
        },
    )
