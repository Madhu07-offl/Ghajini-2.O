import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

from app.core.config import settings
from app.db.models import Memory, PersonFace
from app.db.session import SessionLocal, init_db
from app.modules.alerts.router import router as alerts_router
from app.modules.chat.llm_client import ollama_client
from app.modules.chat.router import router as chat_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.demo.router import router as demo_router
from app.modules.faces.engine import face_engine
from app.modules.memory.retrieval import memory_retrieval
from app.modules.memory.router import router as memory_router
from app.modules.people.router import router as people_router
from app.modules.privacy.router import router as privacy_router
from app.modules.reminders.router import router as reminders_router
from app.modules.reminders.scheduler import start_scheduler, stop_scheduler
from app.modules.voice.router import router as voice_router
from app.modules.voice.transcriber import voice_transcriber

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def preload_indices() -> None:
    """Preloads database faces and memories into FAISS on startup."""
    db = SessionLocal()
    try:
        # Load faces into FAISS
        faces = db.query(PersonFace).all()
        face_records = [(f.id, f.person_id, f.embedding_json) for f in faces if f.embedding_json]
        face_engine.load_from_db(face_records)
        logger.info(f"Loaded {len(face_records)} faces into FAISS index.")

        # Load memories into FAISS
        memories = db.query(Memory).all()
        memory_records = [(m.id, m.text, m.embedding_json) for m in memories]
        memory_retrieval.load_from_db(memory_records)
        logger.info(f"Loaded {len(memory_records)} memories into FAISS index.")
    except Exception as e:
        logger.error(f"Error preloading indices: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup with timing and full model warm-up
    t0 = time.time()
    logger.info("Starting Ghajini 2.0 backend...")
    settings.init_directories()
    init_db()
    preload_indices()
    voice_transcriber.load()
    start_scheduler()

    # Pre-warm Ollama if not running in pytest
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        try:
            await asyncio.wait_for(ollama_client._call_ollama("hello"), timeout=2.5)
            logger.info("Ollama LLM warm-up completed successfully.")
        except Exception as e:
            logger.info(f"Ollama warm-up note: {e}")

    warmup_duration = round(time.time() - t0, 3)
    logger.info(f"All components preloaded and warmed up in {warmup_duration} seconds.")
    yield
    # Shutdown
    logger.info("Shutting down Ghajini 2.0 backend...")
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI memory companion for Alzheimer's patients",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS enabled for all origins in dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get(f"{settings.API_V1_STR}/health")
async def health_check():
    """
    Comprehensive health check reporting status of:
    - Mongo (socket check)
    - Ollama
    - Face model
    - Whisper model
    """
    # 1. MongoDB check
    mongo_status = "disconnected"
    try:
        u = urlparse(settings.MONGODB_URL)
        host = u.hostname or "localhost"
        port = u.port or 27017
        r, w = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=0.5)
        w.close()
        await w.wait_closed()
        mongo_status = "connected"
    except Exception:
        mongo_status = "disconnected"

    # 2. Ollama check
    ollama_status = "unavailable"
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if res.status_code == 200:
                ollama_status = "available"
    except Exception:
        ollama_status = "unavailable"

    # 3. Model statuses
    face_status = "loaded" if face_engine.app is not None or face_engine.index is not None else "fallback"
    whisper_status = "loaded" if voice_transcriber.model is not None else "fallback"

    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": "2.0.0",
        "mongo": mongo_status,
        "ollama": ollama_status,
        "face_model": face_status,
        "whisper_model": whisper_status,
        "face_engine_loaded": face_status == "loaded",
    }


# Include Routers under /v1
v1_prefix = settings.API_V1_STR
app.include_router(people_router, prefix=f"{v1_prefix}/people", tags=["people"])
# Direct /recognize endpoint under /v1 as specified
app.add_api_route(
    f"{v1_prefix}/recognize",
    endpoint=people_router.routes[-1].endpoint,
    methods=["POST"],
    response_model=people_router.routes[-1].response_model,
    tags=["recognition"],
)
app.include_router(memory_router, prefix=f"{v1_prefix}/memories", tags=["memory"])
app.include_router(chat_router, prefix=v1_prefix, tags=["chat"])  # contains /v1/ask
app.include_router(voice_router, prefix=f"{v1_prefix}/voice", tags=["voice"])
app.include_router(alerts_router, prefix=f"{v1_prefix}/alerts", tags=["alerts"])
app.include_router(reminders_router, prefix=f"{v1_prefix}/reminders", tags=["reminders"])
app.include_router(privacy_router, prefix=f"{v1_prefix}/privacy", tags=["privacy"])
app.include_router(dashboard_router, prefix=f"{v1_prefix}/dashboard", tags=["dashboard"])
app.include_router(demo_router, prefix=f"{v1_prefix}/demo", tags=["demo"])
