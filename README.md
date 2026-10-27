# Ghajini 2.0 - AI Memory Companion for Alzheimer's Patients

A full-stack, local-first AI memory companion designed specifically for Alzheimer's patients and their caregivers. It features high-accuracy face recognition, grounded semantic memory retrieval, Ollama LLM integration, offline voice transcription with faster-whisper, automated medication reminders with iCal RRULE escalation, emergency phrase interception, caregiver alerts, and a high-contrast elderly-friendly UI.

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.11), SQLAlchemy 2.x, SQLite, Pydantic v2
- **Voice Transcription**: `faster-whisper` (model `small`, int8, CPU) with VAD filtering and language detection (`en`, `hi`, `pa`)
- **Face Engine**: InsightFace (`buffalo_l`) + FAISS (`IndexFlatIP` on 512-d L2 normalized embeddings)
- **Memory Retrieval**: SentenceTransformers (`paraphrase-multilingual-MiniLM-L12-v2`) + FAISS (`IndexFlatIP` on 384-d L2 normalized vectors)
- **Chat / LLM**: Local Ollama (`llama3.2:3b`) with strict grounding prompts, multilingual fallback ("I am not sure" in English, Hindi, Punjabi), and emergency phrase interception
- **Reminders & Escalation**: APScheduler + `python-dateutil` RRULE recurrence. 15-second frontend polling, 5-minute unacknowledged repeat, quiet hours suppression (22:00-06:00), and caregiver alert escalation via Twilio SMS stub
- **Privacy & Audit**: Strict face consent validation, complete data wipe, audit log (`audit_logs`), and GDPR/HIPAA compliant JSON export archive (ZIP)
- **Frontend**: Flutter (Android + Web), Riverpod, GoRouter, Push-to-Talk audio recording (`record`), TTS (`flutter_tts` at rate 0.8), local notifications (`flutter_local_notifications`), emergency phone dialer (`url_launcher`), and high-contrast elderly-friendly UI (20sp+ typography, 64dp+ touch targets)

---

## Repo Structure

```
ghajini_2.0/
  backend/
    app/
      main.py
      core/config.py            (Settings from .env using pydantic-settings)
      db/session.py, models.py  (SQLAlchemy 2.x, SQLite auto-migration)
      modules/
        people/router.py        (Registration, consent, face vectors, recognition)
        faces/engine.py         (InsightFace buffalo_l + FAISS IndexFlatIP)
        memory/router.py, retrieval.py (SentenceTransformers + FAISS)
        chat/router.py, prompts.py, llm_client.py (Emergency interception, Ollama)
        voice/router.py, transcriber.py (faster-whisper small int8 CPU + VAD)
        alerts/router.py, service.py    (Caregiver alert dispatcher + Twilio SMS)
        reminders/router.py, scheduler.py (APScheduler + RRULE + escalation)
        privacy/router.py       (ZIP export, complete data wipe, audit log)
    scripts/seed_demo_data.py
    tests/test_api.py           (10 pytest tests covering all critical paths)
    requirements.txt, .env.example, Dockerfile
  frontend/
    lib/
      main.dart
      core/constants.dart, theme.dart, api_client.dart
      models/person.dart, recognition_result.dart, memory.dart, reminder.dart, alert_model.dart
      services/api_service.dart, tts_service.dart
      providers/app_providers.dart
      router/app_router.dart
      screens/
        home_screen.dart        (Greeting, due reminder card, SOS, Call Family)
        recognize_screen.dart   (Camera capture / photo pick, voice output)
        ask_screen.dart         (Push-to-talk mic, confirmation, replay, lang switch)
        add_person_screen.dart  (Caregiver: name, relationship, notes, consent, photos)
        caregiver_screen.dart   (Caregiver portal: reminders manager, alert feed)
    pubspec.yaml
  docker-compose.yml
  README.md
```

---

## Environment Variables (.env)

| Variable | Default | Description |
|---|---|---|
| `PROJECT_NAME` | `Ghajini 2.0` | Application name |
| `API_V1_STR` | `/v1` | Base API prefix |
| `DATABASE_URL` | `sqlite:///./ghajini.db` | SQLite database file location |
| `DEFAULT_PATIENT_ID` | `1` | Default active patient ID |
| `WHISPER_MODEL` | `small` | Faster-whisper model variant (`small`, `tiny`, `base`) |
| `FEATURE_PUSH` | `true` | Enables push notification logging stub |
| `FEATURE_SMS` | `false` | Enables Twilio SMS caregiver alerts |
| `STORE_PHOTOS` | `false` | When `false`, raw recognition photos are discarded |
| `ESCALATE_AFTER_MIN` | `10` | Minutes before unacknowledged reminder escalates |
| `QUIET_HOURS_START` | `22` | Quiet hours start hour (22 = 10 PM) |
| `QUIET_HOURS_END` | `6` | Quiet hours end hour (6 = 6 AM) |
| `FACE_T_HIGH` | `0.50` | Face recognition high confidence threshold |
| `FACE_T_LOW` | `0.38` | Face recognition low confidence threshold |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama service endpoint |
| `OLLAMA_MODEL` | `llama3.2:3b` | Default Ollama model name |
| `TWILIO_ACCOUNT_SID` | `""` | Twilio account SID for SMS alerts |
| `TWILIO_AUTH_TOKEN` | `""` | Twilio auth token |
| `TWILIO_FROM_NUMBER` | `""` | Twilio sender phone number |
| `CAREGIVER_ALERT_PHONE`| `+919876543210` | Caregiver emergency phone number |

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
# From workspace root or backend folder
python backend/scripts/seed_demo_data.py
```

### Step D: Run Pytest Tests

Runs the full 10-test test suite:

```bash
python -m pytest backend/tests -v
```

All 10 tests verify:
1. Health check & engine status
2. Create person with consent validation
3. Ask with known fact from memory
4. Ask with unknown fact (verifies exact translated fallback)
5. Delete person
6. Voice transcription of 16kHz mono WAV audio
7. Emergency phrase interception (skips LLM, generates caregiver alert)
8. Reminder scheduling, 15s `/due` polling, repetition at 5m, and escalation
9. Complete face vector purging on person deletion
10. GDPR/HIPAA privacy export returning a valid JSON ZIP archive

### Step E: Run the Backend Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 3. Frontend Setup (Flutter)

```bash
cd frontend

# Install Flutter packages
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
| `POST` | `/people` | Register person (`consent=true` required) |
| `GET` | `/people` | List registered people & face count |
| `POST` | `/people/{id}/faces` | Upload multipart face photo (rejects without consent) |
| `DELETE` | `/people/{id}` | Delete person, files, and FAISS vectors |
| `POST` | `/recognize` | Multipart image -> status (`match`, `uncertain`, `unknown`, `no_face`) |
| `POST` | `/memories` | Create memory note (auto-embedded into FAISS) |
| `GET` | `/memories` | List patient memories |
| `POST` | `/ask` | Semantic retrieval + LLM answer / Emergency interception |
| `POST` | `/voice/transcribe` | Multipart WAV/M4A audio transcription (faster-whisper small int8) |
| `POST` | `/alerts/help` | SOS emergency trigger |
| `GET` | `/alerts` | Caregiver alerts history feed |
| `POST` | `/reminders` | Create reminder with optional iCal RRULE |
| `GET` | `/reminders/upcoming` | List upcoming reminders |
| `GET` | `/reminders/due` | Poll currently due/triggered reminders (polled every 15s) |
| `PUT` | `/reminders/{id}` | Edit an existing reminder |
| `DELETE` | `/reminders/{id}` | Delete a reminder |
| `POST` | `/reminders/{id}/respond` | Respond (`acknowledged`, `snoozed`, `distressed`) |
| `GET` | `/privacy/export` | Download full personal data as a ZIP archive containing `export.json` |
| `DELETE` | `/privacy/all` | Wipe all patient records, faces, vectors, and audit logs |

---

## 5. How to Test Voice and Reminders

### Testing Voice Transcription
1. **API Voice Transcribe**:
   ```bash
   curl -X POST "http://localhost:8000/v1/voice/transcribe" -F "file=@sample.wav"
   ```
   Returns `{ "text": "...", "language": "en", "confidence": 0.92, "needs_confirmation": false }`.
2. **Emergency Voice / Text Interception**:
   Send a query containing "help", "I fell", "bachao", or "madad":
   ```bash
   curl -X POST "http://localhost:8000/v1/ask" -H "Content-Type: application/json" -d "{\"text\": \"help me, I fell down!\", \"lang\": \"en\"}"
   ```
   Output skips the LLM immediately and replies:
   `{"answer": "Help is coming. I am telling your family.", "grounded": true, "sources": []}`
   and registers a new alert at `GET /v1/alerts`.
3. **Flutter Push-to-Talk**:
   - Open **Ask me anything** (`/ask`).
   - Hold or tap the large microphone button to record 16kHz mono audio.
   - If confidence is low, the prompt displays: `"Did you ask: ...?"` with `Yes` and `No` confirmation buttons.
   - Text is spoken aloud using `flutter_tts` at rate 0.8 according to selected language (English: `en-IN`, Hindi: `hi-IN`, Punjabi: `pa-IN`).

### Testing Reminders & Escalation
1. **Caregiver Management**:
   - Click the Admin / Caregiver icon in the top right AppBar of the Home screen (`/caregiver`).
   - Create or edit reminders with custom time, repeat frequency (daily / weekly), and critical flag.
2. **15-Second Polling & Due Card**:
   - When a reminder's time arrives, `GET /v1/reminders/due` returns it to the Home screen.
   - The Home screen automatically opens a full-screen alert dialog with large buttons: **Done**, **Later (Snooze 5 min)**, and **I need help**.
   - Offline notifications are pre-scheduled with `flutter_local_notifications` for the upcoming 24 hours.
3. **Escalation**:
   - If a reminder is ignored, it repeats after 5 minutes.
   - After `ESCALATE_AFTER_MIN` (default 10 min), its status becomes `escalated`, an alert is registered in `alerts`, and Twilio SMS is dispatched to the caregiver when `FEATURE_SMS=true`.

---

## 6. Status of Features & Limitations

| Component | Status | Details |
|---|---|---|
| **FastAPI Backend** | Fully functional | All endpoints operational under `/v1` |
| **Face Recognition** | Fully functional | InsightFace buffalo_l + FAISS IndexFlatIP |
| **Memory Retrieval** | Fully functional | Multilingual SentenceTransformers + FAISS |
| **Voice Transcription**| Fully functional | faster-whisper small int8 on CPU + VAD filter |
| **Emergency Trigger** | Fully functional | Intercepts en/hi/pa keywords, notifies caregivers |
| **Reminders & RRULE** | Fully functional | APScheduler + python-dateutil recurrence |
| **Caregiver SMS** | Stubbed / Functional | Active when `FEATURE_SMS=true` with valid Twilio keys; logs warning stub otherwise |
| **Push Notifications** | Stubbed | Active when `FEATURE_PUSH=true`; logs notification stub |
| **TTS Punjabi Voice** | Device dependent | Mapped to `pa-IN`; falls back gracefully to display text if the Punjabi TTS engine is absent on the physical device |
