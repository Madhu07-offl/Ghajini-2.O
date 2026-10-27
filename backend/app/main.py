import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.models import Memory, PersonFace
from app.db.session import SessionLocal, init_db
from app.modules.chat.router import router as chat_router
from app.modules.faces.engine import face_engine
from app.modules.memory.retrieval import memory_retrieval
from app.modules.memory.router import router as memory_router
from app.modules.people.router import router as people_router
from app.modules.privacy.router import router as privacy_router
from app.modules.reminders.router import router as reminders_router
from app.modules.reminders.scheduler import start_scheduler, stop_scheduler

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
    # Startup
    logger.info("Starting Ghajini 2.0 backend...")
    settings.init_directories()
    init_db()
    preload_indices()
    start_scheduler()
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
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": "2.0.0",
        "face_engine_loaded": face_engine.app is not None or face_engine.index is not None,
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
app.include_router(reminders_router, prefix=f"{v1_prefix}/reminders", tags=["reminders"])
app.include_router(privacy_router, prefix=f"{v1_prefix}/privacy", tags=["privacy"])
