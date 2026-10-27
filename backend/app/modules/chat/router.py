from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Memory
from app.db.session import get_db
from app.modules.chat.llm_client import ollama_client
from app.modules.memory.retrieval import memory_retrieval

router = APIRouter()


class AskRequest(BaseModel):
    text: str
    lang: str = "en"
    patient_id: Optional[int] = None


class AskResponse(BaseModel):
    answer: str
    grounded: bool
    sources: List[str]


@router.post("/ask", response_model=AskResponse)
async def ask_memory(
    payload: AskRequest,
    db: Session = Depends(get_db),
):
    pid = payload.patient_id or settings.DEFAULT_PATIENT_ID

    # 1. Retrieve top 5 matching memories
    scored_memories = memory_retrieval.search(payload.text, k=5)
    memory_ids = [mid for mid, _ in scored_memories]

    facts: List[str] = []
    if memory_ids:
        # Preserve retrieval ranking
        records = (
            db.query(Memory)
            .filter(Memory.patient_id == pid, Memory.id.in_(memory_ids))
            .all()
        )
        record_map = {r.id: r.text for r in records}
        for mid in memory_ids:
            if mid in record_map:
                facts.append(record_map[mid])

    # 2. Query Ollama / Fallback template
    answer, grounded = await ollama_client.generate_answer(
        question=payload.text,
        facts=facts,
        lang=payload.lang,
    )

    return AskResponse(
        answer=answer,
        grounded=grounded,
        sources=facts,
    )
