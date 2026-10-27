import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Memory
from app.db.session import get_db
from app.modules.memory.retrieval import memory_retrieval

router = APIRouter()


class MemoryCreate(BaseModel):
    text: str
    category: Optional[str] = "general"
    patient_id: Optional[int] = None


class MemoryResponse(BaseModel):
    id: int
    patient_id: int
    text: str
    category: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
def create_memory(payload: MemoryCreate, db: Session = Depends(get_db)):
    pid = payload.patient_id or settings.DEFAULT_PATIENT_ID

    # Create record in DB first to get ID
    memory_record = Memory(
        patient_id=pid,
        text=payload.text.strip(),
        category=payload.category,
    )
    db.add(memory_record)
    db.commit()
    db.refresh(memory_record)

    # Embed and add to FAISS index
    embedding = memory_retrieval.add_memory(memory_record.id, memory_record.text)
    memory_record.embedding_json = json.dumps(embedding)
    db.commit()
    db.refresh(memory_record)

    return memory_record


@router.get("", response_model=List[MemoryResponse])
def get_memories(
    patient_id: int = Query(default=1),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    memories = (
        db.query(Memory)
        .filter(Memory.patient_id == patient_id)
        .order_by(Memory.created_at.desc())
        .limit(limit)
        .all()
    )
    return memories
