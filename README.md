# Ghajini 2.0 - AI Memory Companion for Alzheimer's Patients

A full-stack, local-first AI memory companion designed specifically for Alzheimer's patients and their caregivers. It features high-accuracy face recognition, grounded semantic memory retrieval, Ollama LLM integration, automated medication reminders with escalation policies, and a high-contrast elderly-friendly UI.

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.11), SQLAlchemy 2.x, SQLite, Pydantic v2
- **Face Engine**: InsightFace (`buffalo_l`) + FAISS (`IndexFlatIP` on 512-d L2 normalized embeddings)
- **Memory Retrieval**: SentenceTransformers (`paraphrase-multilingual-MiniLM-L12-v2`) + FAISS (`IndexFlatIP` on 384-d L2 normalized vectors)
- **Chat / LLM**: Local Ollama (`llama3.2:3b`) with strict grounding prompts and graceful template fallback
- **Reminders**: APScheduler with a 5-minute unacknowledged repetition and caregiver alert escalation
- **Frontend**: Flutter (Android + Web), Riverpod, GoRouter, TTS, Camera, High-contrast elderly-friendly UI (20sp+ typography, 64dp+ touch targets)

---

## Repo Structure

```
ghajini_2.0/
  backend/
    app/
      main.py
      core/config.py
      db/session.py, models.py
      modules/
        people/router.py
        faces/engine.py
        memory/router.py, retrieval.py
        chat/router.py, prompts.py, llm_client.py
        reminders/router.py, scheduler.py
        privacy/router.py
    scripts/seed_demo_data.py
    tests/test_api.py
    requirements.txt, .env.example, Dockerfile
  frontend/
    lib/
      main.dart
      core/constants.dart, theme.dart, api_client.dart
      models/person.dart, recognition_result.dart, memory.dart, reminder.dart
      services/api_service.dart, tts_service.dart
      providers/app_providers.dart
      router/app_router.dart
      screens/home_screen.dart, recognize_screen.dart, ask_screen.dart, add_person_screen.dart
    pubspec.yaml
  docker-compose.yml
  README.md
```

---

## 1. Quickstart with Docker Compose

To run the entire system (FastAPI API + Ollama LLM service) with Docker:

```bash
# Start backend and ollama containers
docker-compose up -d

# Pull the default Ollama model
docker exec -it ghajini_ollama ollama pull llama3.2:3b

# Seed demo data inside the API container
docker exec -it ghajini_api python scripts/seed_demo_data.py
```

The API will be available at `http://localhost:8000/v1` with documentation at `http://localhost:8000/docs`.

---

## 2. Local Setup & Installation

### Step A: Pull the Ollama Model

If you have [Ollama](https://ollama.com) installed locally:

```bash
# 1. Start Ollama service (if not already running)
ollama serve

# 2. Pull the default 3B model
ollama pull llama3.2:3b
```

### Step B: Backend Setup

```bash
cd backend

# Create Python 3.11 virtual environment
python -m venv .venv

# Activate venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

### Step C: Seed Demo Data

Seeds 3 people (Priya - daughter, Dr. Sharma - doctor, Arun - son), 10 memories, and one daily 9:00 AM blood pressure reminder:

```bash
# From the backend directory (or workspace root)
python scripts/seed_demo_data.py
```

### Step D: Run Pytest Tests

Runs the 5 verification tests (health, create person, ask known fact, ask unknown fact with fallback, delete person):

```bash
# Run tests
pytest tests/ -v
```

### Step E: Run the Backend Server

```bash
# Start FastAPI backend with Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check is accessible at `http://localhost:8000/health` and `http://localhost:8000/v1/health`.

---

## 3. Frontend Setup (Flutter)

```bash
cd frontend

# Install Flutter dependencies
flutter pub get

# Run on Web (Chrome)
flutter run -d chrome --dart-define=API_URL=http://localhost:8000/v1

# Run on Android Device / Emulator
flutter run -d android --dart-define=API_URL=http://10.0.2.2:8000/v1
```

---

## 4. API Endpoints Reference

All endpoints are prefixed with `/v1` and return JSON:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check & engine status |
| `POST` | `/people` | Register person (requires consent=true) |
| `GET` | `/people` | List registered people & face count |
| `POST` | `/people/{id}/faces` | Upload multipart face photo |
| `DELETE` | `/people/{id}` | Delete person, files, and FAISS vectors |
| `POST` | `/recognize` | Multipart image -> status (`match`, `uncertain`, `unknown`, `no_face`) |
| `POST` | `/memories` | Create memory note (auto-embedded into FAISS) |
| `GET` | `/memories` | List patient memories |
| `POST` | `/ask` | Semantic retrieval + Ollama response (`answer`, `grounded`, `sources`) |
| `POST` | `/reminders` | Create scheduled reminder |
| `GET` | `/reminders/upcoming` | List upcoming reminders |
| `POST` | `/reminders/{id}/respond` | Respond (`acknowledged`, `snoozed`, `distressed`) |
| `DELETE` | `/privacy/all` | Wipe all personal data, memories, images, and FAISS indices |

---

## 5. Security & Privacy

- Every data table includes `patient_id` for multi-tenant / JWT extensibility.
- Strict consent requirement on person registration.
- Complete right-to-be-forgotten endpoint (`DELETE /v1/privacy/all`) purges SQLite records, uploaded photo files, and in-memory FAISS vector indices.
