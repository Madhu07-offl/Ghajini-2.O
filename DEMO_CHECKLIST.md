# Ghajini 2.0 - Live 5-Minute Demo Checklist & Script

A field-tested, step-by-step guide to delivering a flawless, high-impact 5-minute live demonstration of **Ghajini 2.0**.

---

## 1. Pre-Demo Setup (Do 10 Minutes Before)

1. **Start Backend & Services**:
   ```bash
   # Option A: With Docker
   docker-compose up -d

   # Option B: Local processes
   ollama serve
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. **Warm-up & Health Verification**:
   - Open in browser: `http://localhost:8000/v1/health`
   - Confirm status:
     ```json
     { "status": "healthy", "face_model": "loaded", "whisper_model": "loaded" }
     ```
3. **Reset to Clean Demo State**:
   ```bash
   curl -X POST http://localhost:8000/v1/demo/reset
   ```
   *(Or long-press the "Ghajini Companion" title in Flutter to tap "Reset Demo Data".)*
4. **Launch Flutter App**:
   ```bash
   flutter run -d chrome --dart-define=API_URL=http://localhost:8000/v1
   ```
5. **Audio / Volume Check**:
   - Ensure system speakers/headphones are at 80% volume for TTS announcements.

---

## 2. The 5-Minute Live Demo Script

```
0:00 - 0:45 | Introduction & Problem Context
0:45 - 1:30 | Face Recognition ("Who is this?")
1:30 - 2:30 | Grounded Multilingual Memory Q&A (Hindi & English)
2:30 - 3:30 | Live Medication Reminder & Escalation
3:30 - 4:15 | Caregiver Dashboard & Factual Summary
4:15 - 5:00 | Privacy, Right-to-be-Forgotten & Wrap-up
```

### [0:00 - 0:45] Intro: The Alzheimer's Challenge
- **Action**: Show the high-contrast elderly-friendly home screen with large typography and minimum 64dp touch targets.
- **Talking Point**: *"For 55 million people living with dementia, familiar faces and daily routines slip away every single day. Ghajini 2.0 is an offline-capable, local-first AI memory companion that grounds everything strictly in stored facts without hallucinating."*

### [0:45 - 1:30] Step 1: Who is this? (Face Recognition)
- **Action**: Tap **"Who is this?"** (`/recognize`). Select or capture Priya's photo from `demo_assets/priya.jpg`.
- **Result**: Instant match card:
  - *"This is Priya, your daughter. (Lives in Bangalore. Visits on weekends with grandson Kabir.)"*
  - The phone speaks the answer aloud at 0.8 speech rate.
- **Talking Point**: *"Using InsightFace buffalo_l with L2-normalized 512-dimensional embeddings stored in a FAISS index, recognition runs on CPU in milliseconds with zero cloud dependencies."*

### [1:30 - 2:30] Step 2: Multilingual Grounded Memory (Hindi & English)
- **Action**: Tap **"Ask me anything"** (`/ask`).
- **Demo Query 1 (Voice / Mic)**: Speak or type:
  `"Where does Priya live?"`
  - **Answer**: *"Priya lives in Bangalore."* (Grounded in memory, spoken in `en-IN`).
- **Demo Query 2 (Hindi / Hinglish)**: Switch language dropdown to **Hindi**:
  `"Priya kahan rehti hai?"`
  - **Answer**: *"प्रिया बैंगलोर में रहती हैं।"* (Spoken in `hi-IN`).
- **Demo Query 3 (Hallucination Prevention)**: Ask an unknown question:
  `"Who is the prime minister of Mars?"`
  - **Answer**: *"I am not sure. Shall I call your family?"* with the **Call Family** button.
- **Talking Point**: *"Ghajini never guesses. If a fact is not in the patient's verified semantic memory, it strictly returns the translated fallback and offers to dial family."*

### [2:30 - 3:30] Step 3: Live Reminder & Escalation
- **Action**: The live reminder scheduled during demo reset fires, or trigger it instantly:
  - **Option**: Long-press "Ghajini Companion" title -> Tap **"Trigger Reminder Now"**.
- **Result**: Full-screen reminder card overlays the screen:
  - *"Attention please: It is time for Drink Warm Water & Hydration."*
  - Shows 3 prominent action buttons: **Done**, **Later (Snooze 5 min)**, **I need help**.
- **Action**: Tap **"Later"** (snoozes for 5 min) or **"I need help"** (dispatches caregiver alert).
- **Talking Point**: *"Reminders support iCal RRULEs. If a dose is ignored for 5 minutes, it repeats; after 10 minutes, it automatically escalates to the family via SMS and alert feed."*

### [3:30 - 4:15] Step 4: Caregiver Dashboard & Daily Summary
- **Action**: Tap the **Caregiver Dashboard** icon in the AppBar (`/dashboard`).
- **Showcase**:
  1. **85.7% Medication Adherence Gauge**: 6 doses taken, 1 missed in the last 7 days.
  2. **Weekly Bar Chart**: Visual Monday–Sunday adherence pattern built purely in Flutter.
  3. **Daily Factual Summary**: *"Today Mother took her 9 AM tablet, asked 4 questions, and met Priya at 5 PM."* (Generated directly from database logs, smoothed by LLM).
  4. **Top Repeated Questions**: Highlights cognitive loops (*"Where does Priya live? - 3x"*).

### [4:15 - 5:00] Step 5: Privacy & Right-to-be-Forgotten
- **Action**: Navigate to **Privacy & Data Controls** (`/privacy`).
- **Showcase**:
  1. **Export My Data (ZIP)**: Tap button -> downloads complete GDPR/HIPAA JSON archive.
  2. **Delete Person**: Tap trash next to a contact -> purges DB records, image files, and removes vectors from FAISS index in real time.
  3. **Delete Everything**: Demonstrates instant cascade purge.

---

## 3. Fallback Plan (If Live Conditions Fail)

| Risk | Mitigation |
|---|---|
| **No Internet Connection** | Entire backend runs 100% locally on localhost (SQLite + FAISS + faster-whisper + Ollama). Zero internet required. |
| **Ollama Daemon Fails / Too Slow** | The backend includes automatic template fallback that extracts the top fact directly from FAISS without Ollama and responds in < 30ms. |
| **Microphone / Browser Audio Permission Blocked** | The Ask Memory screen provides both text field input and the mic button. Type the query directly if mic fails. |
| **Live Reminder Doesn't Fire in Time** | Long-press the "Ghajini Companion" title on Home -> Tap **"Trigger Reminder Now"** to instantly force the full-screen card. |
| **Missing Punjabi Voice on Device** | Flutter TTS service catches missing locales gracefully and displays on-screen text without crashing. |
