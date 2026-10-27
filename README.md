# Ghajini 2.0 - AI Memory Companion for Alzheimer's Patients

A full-stack, local-first AI memory companion designed specifically for Alzheimer's patients and their caregivers. It features high-accuracy face recognition, grounded semantic memory retrieval, Ollama LLM integration, offline voice transcription with faster-whisper, automated medication reminders with iCal RRULE escalation, emergency phrase interception, caregiver alerts, Caregiver Analytics Dashboard, and a high-contrast elderly-friendly UI.

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.11), SQLAlchemy 2.x, SQLite, Pydantic v2
- **Voice Transcription**: `faster-whisper` (model `small`, int8, CPU) with VAD filtering and language detection (`en`, `hi`, `pa`)
- **Face Engine**: InsightFace (`buffalo_l`) + FAISS (`IndexFlatIP` on 512-d L2 normalized embeddings)
- **Memory Retrieval**: SentenceTransformers (`paraphrase-multilingual-MiniLM-L12-v2`) + FAISS (`IndexFlatIP` on 384-d L2 normalized vectors)
- **Chat / LLM**: Local Ollama (`llama3.2:3b`) with strict grounding prompts, multilingual fallback ("I am not sure" in English, Hindi, Punjabi), and emergency phrase interception
- **Caregiver Dashboard**: 7-day adherence metrics, weekly dose bar chart, top repeated questions tracking, and template-based daily activity summary smoothed by Ollama
- **Reminders & Escalation**: APScheduler + `python-dateutil` RRULE recurrence. 15-second frontend polling, 5-minute unacknowledged repeat, quiet hours suppression (22:00-06:00), and caregiver alert escalation via Twilio SMS stub
- **Demo Mode**: Instant reset (`POST /v1/demo/reset`), live 1-minute reminder trigger, and hidden Demo Tools screen
- **Privacy & Audit**: Strict face consent validation, complete data wipe, audit log (`audit_logs`), and GDPR/HIPAA compliant JSON export archive (ZIP)
- **Frontend**: Flutter (Android + Web), Riverpod, GoRouter, Push-to-Talk audio recording (`record`), TTS (`flutter_tts` at rate 0.8), local notifications (`flutter_local_notifications`), emergency phone dialer (`url_launcher`), and high-contrast elderly-friendly UI (20sp+ typography, 64dp+ touch targets)

---

## Repo Structure

```
ghajini_2.0/
  backend/
    app/
      main.py                   (Preloads models, warm-up timer, /health)
      core/config.py            (Settings from .env using pydantic-settings)
      db/session.py, models.py  (SQLAlchemy 2.x, SQLite auto-migration, Place model)
      modules/
        people/router.py        (Registration, consent, face vectors, recognition)
        faces/engine.py         (InsightFace buffalo_l + FAISS IndexFlatIP)
        memory/router.py, retrieval.py (SentenceTransformers + FAISS)
        chat/router.py, prompts.py, llm_client.py (Emergency interception, Ollama)
        voice/router.py, transcriber.py (faster-whisper small int8 CPU + VAD)
        alerts/router.py, service.py    (Caregiver alert dispatcher + Twilio SMS)
        dashboard/router.py     (Adherence %, daily summary, top questions)
        demo/router.py          (Demo reset, live reminder trigger)
        reminders/router.py, scheduler.py (APScheduler + RRULE + escalation)
        privacy/router.py       (ZIP export, complete data wipe, audit log)
    scripts/
      seed_demo_data.py
      eval_faces.py             (TAR, FAR, FACE_T_HIGH/LOW threshold sweep)
      eval_qa.py                (20 questions, accuracy, hallucination count)
    tests/test_api.py           (14 pytest tests covering all critical paths)
    eval_data/                  (Evaluation dataset for faces and Q&A)
    eval_results/               (Output JSON reports for evaluations)
    demo_assets/                (Sample photos for Priya, Dr. Sharma, Arun)
    requirements.txt, .env.example, Dockerfile
  frontend/
    lib/
      main.dart
      core/constants.dart, theme.dart, api_client.dart
      models/person.dart, recognition_result.dart, memory.dart, reminder.dart, alert_model.dart, dashboard_summary.dart
      services/api_service.dart, tts_service.dart
      providers/app_providers.dart
      router/app_router.dart
      screens/
        home_screen.dart        (Greeting, due reminder card, SOS, Call Family, Demo Tools)
        recognize_screen.dart   (Camera capture / photo pick, voice output, confirm card)
        ask_screen.dart         (Push-to-talk mic, 15s timeout, calm loading, lang switch)
        caregiver_screen.dart   (Reminders manager, recent alerts feed)
        dashboard_screen.dart   (Adherence gauge, custom weekly bar chart, top questions)
        privacy_screen.dart     (GDPR export, person delete, wipe everything)
        add_person_screen.dart  (Caregiver: name, relationship, notes, consent, photos)
    pubspec.yaml
  scripts/
    start_tunnel.py             (Public Cloudflare Tunnel / ngrok launcher)
  DEMO_CHECKLIST.md             (1-page demo script, steps & fallback plan)
  docker-compose.yml            (FastAPI + Ollama + MongoDB)
  README.md
```

---

## Run the Demo (Exact Commands)

### 1. Start Services via Docker Compose
Starts MongoDB, Ollama, and the FastAPI backend in containers:
```bash
docker-compose up -d
docker exec -it ghajini_ollama ollama pull llama3.2:3b
docker exec -it ghajini_api python scripts/seed_demo_data.py
```

### 2. Or Start Locally (Native)
**Terminal 1 — MongoDB & Ollama**:
```bash
# Start MongoDB (if installed locally or via docker)
docker run -d -p 27017:27017 --name ghajini_mongo mongo:latest

# Start Ollama & pull model
ollama serve
ollama pull llama3.2:3b
```

**Terminal 2 — FastAPI Backend**:
```bash
cd backend
.\.venv\Scripts\activate      # On Windows
# source .venv/bin/activate   # On Linux/macOS

# Seed pristine demo data
python scripts/seed_demo_data.py

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 — Flutter Mobile or Web**:
```bash
cd frontend

# Mobile (Android Emulator / Device)
flutter run -d android --dart-define=API_URL=http://10.0.2.2:8000/v1

# Web (Chrome)
flutter run -d chrome --dart-define=API_URL=http://localhost:8000/v1
```

**Terminal 4 (Optional) — Public Web Build & Tunnel**:
To expose the backend publicly for a Vercel/Netlify web deployment:
```bash
python scripts/start_tunnel.py
# Use the printed URL in your build:
flutter build web --dart-define=API_URL=https://<your-tunnel-url>/v1
```

---

## Evaluation Scripts

### 1. Face Threshold Tuning (`eval_faces.py`)
Reads `backend/eval_data/`, enrolls the first 3 photos of each person, tests positive photos and `_unknown/` strangers, sweeps thresholds, and writes `eval_results/faces.json`:
```bash
python backend/scripts/eval_faces.py
```

### 2. Grounding & Q&A Accuracy Check (`eval_qa.py`)
Tests 20 questions in English, Hindi (Hinglish), and Punjabi. Verifies that hallucinations are 0, out-of-domain queries return fallback, and logs latency:
```bash
python backend/scripts/eval_qa.py
```

---

## Running the Automated Test Suite

Runs all 14 end-to-end integration tests:
```bash
python -m pytest backend/tests -v
```

All 14 tests verify:
1. `test_1_health`: Health check status
2. `test_2_create_person`: Person creation with consent validation
3. `test_3_ask_known_fact`: Grounded retrieval of stored memory
4. `test_4_ask_unknown_fact`: Fallback message on unknown questions
5. `test_5_delete_person`: Person deletion
6. `test_6_transcribe_wav`: Faster-whisper WAV transcription
7. `test_7_emergency_phrase_creates_alert_and_skips_llm`: Emergency keyword interception
8. `test_8_reminder_fires_and_escalates`: Scheduling, polling, 5m repetition, and escalation
9. `test_9_delete_person_removes_vectors_and_fails_recognition`: Vector purge & recognition failure
10. `test_10_privacy_export_returns_zip`: GDPR/HIPAA ZIP archive export
11. `test_11_dashboard_summary_numbers_match_seeded_logs`: 7-day adherence & daily report
12. `test_12_demo_reset_restores_seed_state`: Demo reset endpoint (`/v1/demo/reset`)
13. `test_13_health_endpoint_component_statuses`: Component checks (`mongo`, `ollama`, `face_model`, `whisper_model`)
14. `test_14_timeout_and_fallback_prompt`: Timeout & ungrounded hallucination prevention

---

## API Endpoints Reference

All endpoints are prefixed with `/v1` and return JSON:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check reporting status of Mongo, Ollama, Face, Whisper |
| `GET` | `/dashboard/summary` | 7-day adherence %, weekly history, top questions, alert count |
| `GET` | `/dashboard/daily-summary`| Factual daily activity summary for family caregivers |
| `POST` | `/demo/reset` | Resets demo data (3 people, 10 memories, 2 reminders, 1 place) |
| `POST` | `/demo/trigger-reminder`| Forces nearest reminder to trigger immediately for live demo |
| `POST` | `/people` | Register person (`consent=true` required) |
| `GET` | `/people` | List registered people & face count |
| `POST` | `/people/{id}/faces` | Upload multipart face photo (rejects without consent) |
| `DELETE` | `/people/{id}` | Delete person, files, and FAISS vectors |
| `POST` | `/recognize` | Multipart image -> status (`match`, `uncertain`, `unknown`, `no_face`) |
| `POST` | `/memories` | Create memory note (auto-embedded into FAISS) |
| `GET` | `/memories` | List patient memories |
| `POST` | `/ask` | Semantic retrieval + LLM answer / Emergency interception |
| `POST` | `/voice/transcribe` | Multipart audio transcription (faster-whisper small int8) |
| `POST` | `/alerts/help` | SOS emergency trigger |
| `GET` | `/alerts` | Caregiver alerts history feed |
| `POST` | `/reminders` | Create reminder with optional iCal RRULE |
| `GET` | `/reminders/upcoming` | List upcoming reminders |
| `GET` | `/reminders/due` | Poll currently due reminders (polled every 15s) |
| `PUT` | `/reminders/{id}` | Edit a reminder |
| `DELETE` | `/reminders/{id}` | Delete a reminder |
| `POST` | `/reminders/{id}/respond` | Respond (`acknowledged`, `snoozed`, `distressed`) |
| `GET` | `/privacy/export` | Download full personal data as a ZIP archive (`export.json`) |
| `DELETE` | `/privacy/all` | Wipe all patient records, faces, vectors, and audit logs |

---

## Status of Features & Limitations

| Component | Status | Details |
|---|---|---|
| **FastAPI Backend & Routers** | Fully functional | All endpoints operational under `/v1` |
| **Caregiver Dashboard** | Fully functional | 7-day adherence, weekly bar chart, top questions, daily summary |
| **Face Engine & FAISS** | Fully functional | InsightFace buffalo_l + normalized 512-d index |
| **Memory Retrieval** | Fully functional | Multilingual SentenceTransformers + FAISS |
| **Voice Transcription** | Fully functional | faster-whisper small int8 on CPU + VAD filter |
| **Demo Mode & Hidden Screen**| Fully functional | `/demo/reset`, `/demo/trigger-reminder`, long-press title dialog |
| **Offline Caching** | Fully functional | Local reminders & people cache prevents blank screens |
| **Emergency Alerts & SOS** | Fully functional | Intercepts keywords, creates alerts, informs family |
| **Twilio Caregiver SMS** | Stubbed / Functional | Active when `FEATURE_SMS=true` with valid Twilio keys; logs warning otherwise |
| **Push Notifications** | Stubbed | Active when `FEATURE_PUSH=true`; logs notification stub |
| **Punjabi TTS Voice** | Device dependent | Calls `pa-IN`; falls back gracefully to on-screen text display if device lacks Punjabi voice assets |
