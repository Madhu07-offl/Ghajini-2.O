import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Memory
from app.db.mongo import mongo_manager
from app.db.session import get_db
from app.modules.alerts.service import notify_caregivers
from app.modules.companion.service import companion_service
from app.modules.memory.retrieval import memory_retrieval

logger = logging.getLogger(__name__)

router = APIRouter()


# -------------------------------------------------------------
# Request & Response Schemas
# -------------------------------------------------------------
class CompanionMessageRequest(BaseModel):
    patient_id: Optional[int] = None
    text: str = Field(..., description="Message from patient (voice transcript, text, etc.)")
    lang: Optional[str] = Field(default=None, description="Optional ISO code (en, hi, pa)")
    source: str = Field(default="text", description="'voice' | 'text' | 'proactive'")


class CompanionMessageResponse(BaseModel):
    reply: str
    lang: str
    intent: str
    grounded: bool
    mood: str
    actions: List[str] = []
    sources: List[str] = []
    person: Optional[Dict[str, Any]] = None


class CheckinResponseRequest(BaseModel):
    patient_id: Optional[int] = None
    checkin_id: Optional[str] = None
    status: str = Field(..., description="'ok' | 'need_help'")


class CompanionSettingsSchema(BaseModel):
    patient_name: str = "Mother"
    preferred_language: str = "hi"
    tone: str = "calm"  # "warm" | "calm" | "cheerful"
    wake_time: str = "08:00"
    check_in_frequency_hours: int = 3
    quiet_hours_start: int = 22
    quiet_hours_end: int = 6
    emergency_contact: str = "+919876543210"


class TeachRequest(BaseModel):
    patient_id: Optional[int] = None
    text: str = Field(..., description="Plain-text memory to teach companion")
    category: str = "personal"


class FeedbackRequest(BaseModel):
    marked_wrong: bool = True
    reason: Optional[str] = "Caregiver flagged answer as inaccurate"


# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------
@router.post("/message", response_model=CompanionMessageResponse)
async def send_companion_message(
    payload: CompanionMessageRequest,
    db: Session = Depends(get_db),
):
    """
    Main communication endpoint for the Patient AI Companion.
    Processes voice or text questions, checks emergency & mood, retrieves facts,
    and returns a gentle, fact-grounded response.
    """
    pid = payload.patient_id or settings.DEFAULT_PATIENT_ID
    result = await companion_service.process_message(
        patient_id=pid,
        text=payload.text,
        lang=payload.lang,
        source=payload.source,
        db=db,
    )
    return CompanionMessageResponse(**result)


@router.get("/proactive")
async def get_proactive_companion(
    patient_id: int = Query(default=settings.DEFAULT_PATIENT_ID),
    db: Session = Depends(get_db),
):
    """
    Polled every 30s by the Flutter app.
    Returns morning greeting, gentle check-ins, or evening summaries.
    """
    msg = await companion_service.get_proactive_message(patient_id, db=db)
    return {"has_message": msg is not None, "message": msg}


@router.post("/check-in/respond")
async def respond_to_checkin(
    payload: CheckinResponseRequest,
    db: Session = Depends(get_db),
):
    """
    Records response to a proactive check-in.
    If 'need_help', immediately alerts caregivers.
    """
    pid = payload.patient_id or settings.DEFAULT_PATIENT_ID
    checkin_coll = mongo_manager.get_collection("checkin_logs")

    if payload.status == "need_help":
        notify_caregivers(
            patient_id=pid,
            alert_type="distress_response",
            message="Patient indicated distress during gentle check-in ('need_help').",
            db=db,
        )

    await checkin_coll.update_one(
        {"patient_id": pid},
        {
            "$set": {
                "pending_response": False,
                "last_response_status": payload.status,
                "last_response_at": datetime.utcnow().isoformat(),
            }
        },
    )

    return {"status": "recorded", "patient_id": pid}


@router.get("/settings", response_model=CompanionSettingsSchema)
async def get_companion_settings(
    patient_id: int = Query(default=settings.DEFAULT_PATIENT_ID),
):
    """Returns caregiver configuration settings for the companion."""
    settings_dict = await companion_service.get_patient_settings(patient_id)
    return CompanionSettingsSchema(
        patient_name=settings_dict.get("patient_name", "Mother"),
        preferred_language=settings_dict.get("preferred_language", "hi"),
        tone=settings_dict.get("tone", "calm"),
        wake_time=settings_dict.get("wake_time", "08:00"),
        check_in_frequency_hours=settings_dict.get("check_in_frequency_hours", 3),
        quiet_hours_start=settings_dict.get("quiet_hours_start", 22),
        quiet_hours_end=settings_dict.get("quiet_hours_end", 6),
        emergency_contact=settings_dict.get("emergency_contact", settings.CAREGIVER_PHONE),
    )


@router.post("/settings", response_model=CompanionSettingsSchema)
async def update_companion_settings(
    payload: CompanionSettingsSchema,
    patient_id: int = Query(default=settings.DEFAULT_PATIENT_ID),
):
    """Updates caregiver configuration settings for the companion."""
    coll = mongo_manager.get_collection("companion_settings")
    update_data = payload.model_dump()
    update_data["patient_id"] = patient_id
    update_data["updated_at"] = datetime.utcnow().isoformat()

    await coll.update_one({"patient_id": patient_id}, {"$set": update_data})
    return payload


def sanitize_memory_text(text: str) -> str:
    """Strips malicious prompt injection phrases from memory submissions."""
    patterns = [
        r"(?i)ignore\s+(all|previous)\s+instructions?",
        r"(?i)disregard\s+(all|previous)\s+prompts?",
        r"(?i)system\s*:",
        r"(?i)you\s+are\s+now\s+a",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"(?i)jailbreak",
    ]
    sanitized = text
    for p in patterns:
        sanitized = re.sub(p, "", sanitized)
    return re.sub(r"\s+", " ", sanitized).strip()


@router.post("/teach")
def teach_companion_memory(
    payload: TeachRequest,
    db: Session = Depends(get_db),
):
    """
    Caregiver 'Teach the companion' endpoint: adds a memory in plain text,
    sanitizes prompt injections, stores it, and embeds it into FAISS instantly.
    """
    pid = payload.patient_id or settings.DEFAULT_PATIENT_ID
    clean_text = sanitize_memory_text(payload.text)

    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Memory text is empty or contained only invalid instructions.",
        )

    # 1. Embed via sentence transformer
    embedding = memory_retrieval.embed_text(clean_text)

    # 2. Store in SQL Memory table
    import json
    memory = Memory(
        patient_id=pid,
        text=clean_text,
        category=payload.category,
        embedding_json=json.dumps(embedding.tolist()) if embedding is not None else None,
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)

    # 3. Add to FAISS index immediately
    memory_retrieval.add_memory(memory.id, clean_text, memory.embedding_json)

    return {
        "id": memory.id,
        "patient_id": memory.patient_id,
        "text": memory.text,
        "category": memory.category,
        "created_at": memory.created_at.isoformat(),
        "message": "Memory taught and embedded successfully.",
    }


@router.get("/conversations")
async def list_conversations(
    patient_id: int = Query(default=settings.DEFAULT_PATIENT_ID),
    limit: int = Query(default=50),
):
    """Returns conversation history with intent, mood, and grounded flag."""
    coll = mongo_manager.get_collection("conversations")
    cursor = coll.find({"patient_id": patient_id}).sort("timestamp", -1).limit(limit)
    items = await cursor.to_list()
    return items


@router.post("/conversations/{conversation_id}/feedback")
async def mark_conversation_wrong(
    conversation_id: str,
    payload: FeedbackRequest,
):
    """
    Marks a companion reply as wrong so it can be reviewed by caregiver
    and excluded from future retrieval.
    """
    coll = mongo_manager.get_collection("conversations")
    result = await coll.update_one(
        {"_id": conversation_id},
        {
            "$set": {
                "marked_wrong": payload.marked_wrong,
                "wrong_reason": payload.reason,
                "marked_at": datetime.utcnow().isoformat(),
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found.",
        )

    return {"status": "updated", "conversation_id": conversation_id, "marked_wrong": payload.marked_wrong}
