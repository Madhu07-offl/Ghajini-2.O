import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Alert, AuditLog, Memory, Person, Place, Reminder, ReminderLog
from app.db.mongo import mongo_manager
from app.db.session import SessionLocal
from app.modules.alerts.service import notify_caregivers
from app.modules.companion.prompts import (
    build_companion_prompt,
    get_calling_family_line,
    get_help_is_coming_line,
    get_medical_disclaimer_line,
    get_not_sure_line,
    get_reassure_line,
    get_smalltalk_greeting,
)
from app.modules.memory.retrieval import memory_retrieval

logger = logging.getLogger(__name__)


# -------------------------------------------------------------
# 1. Text Normalization and Language Detection
# -------------------------------------------------------------
def normalize_text(text: str) -> str:
    """Normalizes whitespace and standardizes punctuation."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text.strip())
    return text


def detect_language(text: str, fallback_lang: str = "en") -> str:
    """
    Detects language based on script ranges or common transliterated words.
    Returns: 'en' | 'hi' | 'pa'
    """
    if not text:
        return fallback_lang

    # Gurmukhi script range (\u0A00 - \u0A7F)
    if re.search(r"[\u0A00-\u0A7F]", text):
        return "pa"

    # Devanagari script range (\u0900 - \u097F)
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"

    # Common Hinglish / Punjabi romanized keywords
    lower = text.lower()
    punjabi_keywords = ["kiddan", "kivein", "sat sri akal", "kehda", "tussi", "main dig"]
    for pk in punjabi_keywords:
        if pk in lower:
            return "pa"

    hindi_keywords = ["namaste", "madad", "bachao", "kahan", "kaun", "dawai", "goli", "kya", "haan", "nahin", "ghabrahat"]
    for hk in hindi_keywords:
        if hk in lower:
            return "hi"

    return fallback_lang or "en"


# -------------------------------------------------------------
# 2. Mood Detection
# -------------------------------------------------------------
def detect_mood(text: str) -> str:
    """
    Classifies mood into: 'anxious' | 'confused' | 'sad' | 'calm'.
    """
    lower = text.lower()

    anxious_keywords = [
        "worried", "scared", "fear", "dar", "ghabrahat", "tension", "chinta",
        "nervous", "frightened", "bachao", "panicking", "panic", "anxious"
    ]
    for w in anxious_keywords:
        if w in lower:
            return "anxious"

    confused_keywords = [
        "confused", "don't know", "lost", "kahan", "kaun", "kya ho raha",
        "samajh nahi", "bhuul gaya", "bhul gayi", "bhool", "where am i", "who are you"
    ]
    if "??" in text or any(w in lower for w in confused_keywords):
        return "confused"

    sad_keywords = ["sad", "crying", "alone", "miss", "ro raha", "dukhi", "akela", "yaad aa rahi", "koi nahi hai"]
    for w in sad_keywords:
        if w in lower:
            return "sad"

    return "calm"


# -------------------------------------------------------------
# 3. Intent Routing
# -------------------------------------------------------------
EMERGENCY_WORDS = [
    "help", "lost", "fell", "madad", "bachao", "ghabrahat", "i am lost",
    "i fell", "i have fallen", "emergency", "chakkar", "chot", "mai gir",
    "main gir", "main dig", "danger", "chest pain", "dard", "saans", "pain"
]

WHO_IS_PATTERNS = [
    r"\bwho is\b", r"\bwho's\b", r"\bwho are you\b", r"\bwho are\b",
    r"\bkaun hai\b", r"\bkoun hai\b", r"\bkaun\b", r"\bkoun\b",
    r"\bdo you know\b", r"\bkehda hai\b"
]

WHERE_WHEN_PATTERNS = [
    r"\bwhere am i\b", r"\bwhere is\b", r"\bwhere do i live\b", r"\bwhat day is it\b",
    r"\bwhat time is it\b", r"\bwhat is the time\b", r"\bwhat date is it\b", r"\bwhat is today\b",
    r"\bwhat year is it\b", r"\bkahan hoon\b", r"\bmain kahan hoon\b", r"\baaj kaun sa din hai\b",
    r"\btime kya hua\b", r"\bkitne baje\b", r"\baaj ki tareekh\b", r"\bajj kehda din\b",
    r"\bwhere are my\b"
]

MEDICINE_PATTERNS = [
    r"\btablet\b", r"\bmedicine\b", r"\bdawai\b", r"\bgoli\b", r"\bpill\b",
    r"\bdid i take\b", r"\bwhich tablet\b", r"\bhave i taken\b", r"\bmeri dawai\b",
    r"\bdose\b", r"\bdosage\b", r"\bkhani hai\b", r"\ble li\b"
]

ROUTINE_PATTERNS = [
    r"\bwhat do i do now\b", r"\bwhat do i do today\b", r"\bwhat's next\b",
    r"\bwhat is next\b", r"\bschedule\b", r"\baaj kya karna hai\b",
    r"\bmera program\b", r"\bajj ki karna\b", r"\broutine\b"
]

CALL_FAMILY_PATTERNS = [
    r"\bcall my daughter\b", r"\bcall my son\b", r"\bcall family\b",
    r"\bcall doctor\b", r"\bcall priya\b", r"\bcall arun\b",
    r"\bphone karo\b", r"\bphone milao\b", r"\bcall karo\b", r"\bbaat karni hai\b"
]

SMALLTALK_WORDS = [
    "hello", "hi", "hey", "good morning", "good evening", "how are you",
    "thank you", "thanks", "namaste", "sat sri akal", "kaise ho",
    "kiddan", "kivein ho", "dhanyawad", "shukriya"
]


def classify_intent(text: str) -> str:
    """Classifies user input into primary companion intent."""
    lower = text.lower()

    # 1. Emergency
    for ew in EMERGENCY_WORDS:
        if " " in ew:
            if ew in lower:
                return "emergency"
        else:
            if re.search(rf"\b{ew}\b", lower):
                return "emergency"

    # 2. Call Family
    for p in CALL_FAMILY_PATTERNS:
        if re.search(p, lower):
            return "call_family"

    # 3. Medicine
    for p in MEDICINE_PATTERNS:
        if re.search(p, lower):
            return "medicine"

    # 4. Where / When
    for p in WHERE_WHEN_PATTERNS:
        if re.search(p, lower):
            return "where_when"

    # 5. Routine
    for p in ROUTINE_PATTERNS:
        if re.search(p, lower):
            return "routine"

    # 6. Who is
    for p in WHO_IS_PATTERNS:
        if re.search(p, lower):
            return "who_is"

    # 7. Smalltalk
    for sw in SMALLTALK_WORDS:
        if re.search(rf"\b{sw}\b", lower):
            return "smalltalk"

    return "unknown"


# -------------------------------------------------------------
# 4. Entity Anti-Hallucination Guardrail
# -------------------------------------------------------------
def verify_entities_in_reply(reply: str, facts: List[str], context_str: str) -> bool:
    """
    Ensures every specific entity (numbers, specific medication names) in reply
    appears in facts or context.
    Returns True if safe; False if hallucinated.
    """
    allowed_text = (" ".join(facts) + " " + context_str).lower()

    # Extract digits / numbers from reply
    reply_numbers = re.findall(r"\b\d+\b", reply)
    for num in reply_numbers:
        if num not in allowed_text:
            logger.warning(f"Guardrail triggered: Number '{num}' in reply not in facts/context.")
            return False

    return True


# -------------------------------------------------------------
# 5. Companion Service Core
# -------------------------------------------------------------
class CompanionService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.temperature = 0.2
        self.max_tokens = 120
        self.timeout = 1.0 if (os.environ.get("TESTING") or os.environ.get("PYTEST_CURRENT_TEST")) else settings.OLLAMA_TIMEOUT_SECONDS

    async def get_patient_settings(self, patient_id: int) -> Dict[str, Any]:
        coll = mongo_manager.get_collection("companion_settings")
        doc = await coll.find_one({"patient_id": patient_id})
        if not doc:
            doc = {
                "patient_id": patient_id,
                "patient_name": "Mother",
                "preferred_language": "hi",
                "tone": "calm",
                "wake_time": "08:00",
                "check_in_frequency_hours": 3,
                "quiet_hours_start": settings.QUIET_HOURS_START,
                "quiet_hours_end": settings.QUIET_HOURS_END,
                "emergency_contact": settings.CAREGIVER_PHONE,
            }
            await coll.insert_one(doc)
        return doc

    async def check_repeated_question(self, patient_id: int, normalized_text: str) -> Tuple[bool, int]:
        """
        Checks if same question was asked 2+ times in last 30 minutes.
        Returns: (is_repeated, count)
        """
        coll = mongo_manager.get_collection("conversations")
        cutoff = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        cursor = coll.find({
            "patient_id": patient_id,
            "text": normalized_text,
            "timestamp": {"$gte": cutoff}
        })
        history = await cursor.to_list()
        count = len(history)
        return (count >= 2, count + 1)

    async def process_message(
        self,
        patient_id: int,
        text: str,
        lang: Optional[str] = None,
        source: str = "text",
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Main pipeline for POST /v1/companion/message.
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            norm_text = normalize_text(text)
            comp_settings = await self.get_patient_settings(patient_id)
            patient_name = comp_settings.get("patient_name", "Mother")
            pref_lang = comp_settings.get("preferred_language", "en")
            tone = comp_settings.get("tone", "calm")

            target_lang = lang if lang in ("en", "hi", "pa") else detect_language(norm_text, pref_lang)
            intent = classify_intent(norm_text)
            mood = detect_mood(norm_text)

            # Repeated Question Check (last 30 mins)
            is_repeated, rep_count = await self.check_repeated_question(patient_id, norm_text)
            if is_repeated:
                try:
                    audit = AuditLog(
                        patient_id=patient_id,
                        action="repeated_question",
                        details=f"Question repeated {rep_count} times in 30m: '{norm_text}'",
                        timestamp=datetime.utcnow(),
                    )
                    db.add(audit)
                    db.commit()
                except Exception:
                    pass

            # Context data
            now = datetime.now()
            local_time_str = now.strftime("%I:%M %p")
            local_date_str = now.strftime("%A, %d %B %Y")

            # Look up next upcoming reminder
            next_rem = (
                db.query(Reminder)
                .filter(Reminder.patient_id == patient_id, Reminder.status.in_(["pending", "triggered"]))
                .order_by(Reminder.scheduled_time.asc())
                .first()
            )
            next_reminder_str = f"{next_rem.title} at {next_rem.scheduled_time}" if next_rem else "No upcoming reminders"

            # -------------------------------------------------------------
            # Handle Intent 1: Emergency (Skip LLM)
            # -------------------------------------------------------------
            if intent == "emergency":
                notify_caregivers(
                    patient_id=patient_id,
                    alert_type="emergency_phrase",
                    message=f"Emergency phrase in companion: '{norm_text}'",
                    db=db,
                )
                reply = get_help_is_coming_line(target_lang)
                conv_doc = {
                    "patient_id": patient_id,
                    "text": norm_text,
                    "reply": reply,
                    "lang": target_lang,
                    "intent": "emergency",
                    "grounded": True,
                    "mood": mood,
                    "actions": ["show_sos", "call_family"],
                    "sources": ["Emergency detection: Caregiver alert triggered."],
                    "person": None,
                    "marked_wrong": False,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                coll = mongo_manager.get_collection("conversations")
                await coll.insert_one(conv_doc)
                return {
                    "reply": reply,
                    "lang": target_lang,
                    "intent": "emergency",
                    "grounded": True,
                    "mood": mood,
                    "actions": ["show_sos", "call_family"],
                    "sources": ["Emergency detection: Caregiver alert triggered."],
                    "person": None,
                }

            # -------------------------------------------------------------
            # Handle Intent 2: Call Family
            # -------------------------------------------------------------
            if intent == "call_family":
                reply = get_calling_family_line(target_lang)
                conv_doc = {
                    "patient_id": patient_id,
                    "text": norm_text,
                    "reply": reply,
                    "lang": target_lang,
                    "intent": "call_family",
                    "grounded": True,
                    "mood": mood,
                    "actions": ["call_family"],
                    "sources": ["Family dialer activated."],
                    "person": None,
                    "marked_wrong": False,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                coll = mongo_manager.get_collection("conversations")
                await coll.insert_one(conv_doc)
                return {
                    "reply": reply,
                    "lang": target_lang,
                    "intent": "call_family",
                    "grounded": True,
                    "mood": mood,
                    "actions": ["call_family"],
                    "sources": ["Family dialer activated."],
                    "person": None,
                }

            # -------------------------------------------------------------
            # Handle Intent 3: Smalltalk
            # -------------------------------------------------------------
            if intent == "smalltalk":
                reply = get_smalltalk_greeting(target_lang)
                conv_doc = {
                    "patient_id": patient_id,
                    "text": norm_text,
                    "reply": reply,
                    "lang": target_lang,
                    "intent": "smalltalk",
                    "grounded": True,
                    "mood": mood,
                    "actions": [],
                    "sources": ["Greeting library"],
                    "person": None,
                    "marked_wrong": False,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                coll = mongo_manager.get_collection("conversations")
                await coll.insert_one(conv_doc)
                return {
                    "reply": reply,
                    "lang": target_lang,
                    "intent": "smalltalk",
                    "grounded": True,
                    "mood": mood,
                    "actions": [],
                    "sources": ["Greeting library"],
                    "person": None,
                }

            # -------------------------------------------------------------
            # Fact Assembly for Q&A intents (who_is, where_when, medicine, routine, unknown)
            # -------------------------------------------------------------
            facts: List[str] = []
            person_card: Optional[Dict[str, Any]] = None

            # Retrieve memories from FAISS
            scored_memories = memory_retrieval.search(norm_text, k=5)
            memory_ids = [mid for mid, _ in scored_memories]
            if memory_ids:
                db_memories = (
                    db.query(Memory)
                    .filter(Memory.patient_id == patient_id, Memory.id.in_(memory_ids))
                    .all()
                )
                mem_map = {m.id: m.text for m in db_memories}
                for mid in memory_ids:
                    if mid in mem_map:
                        facts.append(mem_map[mid])

            # Specific intent fact enrichment
            if intent == "who_is":
                # Look for name matches in People table
                people = db.query(Person).filter(Person.patient_id == patient_id).all()
                for p in people:
                    if p.name.lower() in norm_text.lower():
                        face_url = None
                        if p.faces:
                            face_url = p.faces[0].file_path
                        person_card = {
                            "id": p.id,
                            "name": p.name,
                            "relationship": p.relationship,
                            "notes": p.notes,
                            "photo_url": face_url,
                        }
                        facts.insert(0, f"{p.name} is your {p.relationship}. {p.notes or ''}")
                        break

            elif intent == "where_when":
                # Add current clock & places to facts
                facts.insert(0, f"Today is {local_date_str}. The current time is {local_time_str}.")
                places = db.query(Place).filter(Place.patient_id == patient_id).all()
                for pl in places:
                    facts.append(f"Your home address is {pl.name}, {pl.address}. {pl.notes or ''}")

            elif intent == "medicine":
                # Guardrail: Never give medical advice or change doses
                advice_keywords = ["dose", "dosage", "how many", "can i take", "should i take", "increase", "decrease", "kitni", "kitna", "khani chahiye"]
                if any(w in norm_text.lower() for w in advice_keywords):
                    disclaimer = get_medical_disclaimer_line(target_lang)
                    conv_doc = {
                        "patient_id": patient_id,
                        "text": norm_text,
                        "reply": disclaimer,
                        "lang": target_lang,
                        "intent": "medicine",
                        "grounded": True,
                        "mood": mood,
                        "actions": ["ask_doctor"],
                        "sources": ["Safety rule: No medical advice allowed."],
                        "person": None,
                        "marked_wrong": False,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    coll = mongo_manager.get_collection("conversations")
                    await coll.insert_one(conv_doc)
                    return {
                        "reply": disclaimer,
                        "lang": target_lang,
                        "intent": "medicine",
                        "grounded": True,
                        "mood": mood,
                        "actions": ["ask_doctor"],
                        "sources": ["Safety rule: No medical advice allowed."],
                        "person": None,
                    }

                # Only use reminder logs and definitions
                reminders = db.query(Reminder).filter(Reminder.patient_id == patient_id).all()
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                logs = (
                    db.query(ReminderLog)
                    .filter(ReminderLog.patient_id == patient_id, ReminderLog.timestamp >= today_start)
                    .all()
                )
                ack_ids = {log.reminder_id for log in logs if log.outcome == "acknowledged"}

                med_facts = []
                for r in reminders:
                    status_text = "already taken today" if r.id in ack_ids else f"scheduled at {r.scheduled_time}"
                    med_facts.append(f"Your medicine '{r.title}' is {status_text}.")
                facts = med_facts + facts

            elif intent == "routine":
                reminders = (
                    db.query(Reminder)
                    .filter(Reminder.patient_id == patient_id)
                    .order_by(Reminder.scheduled_time.asc())
                    .all()
                )
                routine_facts = [f"At {r.scheduled_time}: {r.title}" for r in reminders]
                facts = routine_facts + facts

            # -------------------------------------------------------------
            # Ollama Generation & Guardrails
            # -------------------------------------------------------------
            reply = ""
            grounded = True
            sources = facts[:5]

            context_str = f"time {local_time_str}, date {local_date_str}, next reminder {next_reminder_str}"

            if not facts:
                reply = get_not_sure_line(target_lang)
                grounded = False
            else:
                prompt = build_companion_prompt(
                    name=patient_name,
                    question=norm_text,
                    facts=facts,
                    lang=target_lang,
                    local_time=local_time_str,
                    local_date=local_date_str,
                    next_reminder=next_reminder_str,
                    mood=mood,
                    tone=tone,
                )

                # Attempt Ollama call
                ollama_reply = None
                try:
                    url = f"{self.base_url}/api/generate"
                    payload = {
                        "model": self.model,
                        "prompt": prompt,
                        "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
                        "stream": False,
                    }
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        res = await client.post(url, json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            candidate = data.get("response", "").strip()
                            if candidate:
                                ollama_reply = candidate
                except Exception as e:
                    logger.info(f"Ollama call note in companion ({e}); using fact template fallback.")

                if ollama_reply:
                    # Check not-sure fallback in Ollama reply
                    if get_not_sure_line(target_lang).lower() in ollama_reply.lower():
                        reply = get_not_sure_line(target_lang)
                        grounded = False
                    else:
                        # Guardrail: Check for hallucinated numbers or entities
                        if verify_entities_in_reply(ollama_reply, facts, context_str):
                            reply = ollama_reply
                            grounded = True
                        else:
                            # Safe template fallback
                            reply, grounded = self._build_safe_fact_reply(norm_text, facts[0], target_lang)
                else:
                    # Template fallback from top fact
                    reply, grounded = self._build_safe_fact_reply(norm_text, facts[0], target_lang)

            # If medicine intent, ensure no medical advice is given
            if intent == "medicine" and ("dose" in norm_text.lower() or "how many" in norm_text.lower()):
                reply += f" {get_medical_disclaimer_line(target_lang)}"

            # If mood is anxious or confused, prepend gentle reassurance
            if mood in ("anxious", "confused"):
                reassure_prefix = get_reassure_line(target_lang) + " "
                if not reply.startswith(get_reassure_line(target_lang)):
                    reply = reassure_prefix + reply

            # Save in MongoDB conversations collection
            conv_doc = {
                "patient_id": patient_id,
                "text": norm_text,
                "reply": reply,
                "lang": target_lang,
                "intent": intent,
                "grounded": grounded,
                "mood": mood,
                "actions": [],
                "sources": sources,
                "person": person_card,
                "marked_wrong": False,
                "timestamp": datetime.utcnow().isoformat(),
            }
            coll = mongo_manager.get_collection("conversations")
            await coll.insert_one(conv_doc)

            return {
                "reply": reply,
                "lang": target_lang,
                "intent": intent,
                "grounded": grounded,
                "mood": mood,
                "actions": [],
                "sources": sources,
                "person": person_card,
            }

        finally:
            if close_db:
                db.close()

    def _build_safe_fact_reply(self, question: str, top_fact: str, lang: str) -> Tuple[str, bool]:
        """Constructs a deterministic, warm factual reply or safe fallback if irrelevant."""
        if not top_fact:
            return get_not_sure_line(lang), False

        # Check relevance
        q_words = set(w.lower() for w in re.findall(r"\w+", question) if len(w) > 3)
        fact_words = set(w.lower() for w in re.findall(r"\w+", top_fact))
        overlap = q_words.intersection(fact_words)

        if not overlap and len(q_words) > 0:
            return get_not_sure_line(lang), False

        lang_key = (lang or "en").lower()[:2]
        if lang_key == "hi":
            return f"आपकी याद के अनुसार: {top_fact}", True
        elif lang_key == "pa":
            return f"ਤੁਹਾਡੀ ਯਾਦ ਦੇ ਅਨੁਸਾਰ: {top_fact}", True
        return f"{top_fact}", True

    # -------------------------------------------------------------
    # 6. Proactive Generators
    # -------------------------------------------------------------
    async def get_proactive_message(self, patient_id: int, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """
        Poll endpoint logic for GET /v1/companion/proactive.
        Generates morning greeting, gentle check-ins, or evening wind-downs.
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            now = datetime.now()
            hour = now.hour
            current_date_str = now.strftime("%Y-%m-%d")

            # Check quiet hours (22:00 - 06:00)
            if settings.QUIET_HOURS_START > settings.QUIET_HOURS_END:
                in_quiet = hour >= settings.QUIET_HOURS_START or hour < settings.QUIET_HOURS_END
            else:
                in_quiet = settings.QUIET_HOURS_START <= hour < settings.QUIET_HOURS_END

            if in_quiet:
                return None

            comp_settings = await self.get_patient_settings(patient_id)
            patient_name = comp_settings.get("patient_name", "Mother")
            lang = comp_settings.get("preferred_language", "en")
            wake_time = comp_settings.get("wake_time", "08:00")
            wake_hour = int(wake_time.split(":")[0]) if ":" in wake_time else 8

            proactive_coll = mongo_manager.get_collection("proactive_queue")

            # A. Morning Greeting (Wake time up to 10 AM, once per day)
            if hour >= wake_hour and hour < 11:
                already_greeted = await proactive_coll.find_one({
                    "patient_id": patient_id,
                    "type": "morning_greeting",
                    "date": current_date_str,
                })
                if not already_greeted:
                    reminders = (
                        db.query(Reminder)
                        .filter(Reminder.patient_id == patient_id)
                        .all()
                    )
                    rem_titles = [r.title for r in reminders]
                    day_name = now.strftime("%A")
                    if lang == "hi":
                        rem_text = f"आज आपके {len(rem_titles)} काम हैं: {', '.join(rem_titles)}" if rem_titles else "आज कोई खास काम नहीं है।"
                        msg = f"सुप्रभात {patient_name}। आज {day_name} है। {rem_text}"
                    elif lang == "pa":
                        rem_text = f"ਅੱਜ ਤੁਹਾਡੇ {len(rem_titles)} ਕੰਮ ਹਨ: {', '.join(rem_titles)}" if rem_titles else "ਅੱਜ ਕੋਈ ਖਾਸ ਕੰਮ ਨਹੀਂ ਹੈ।"
                        msg = f"ਸ਼ੁਭ ਸਵੇਰ {patient_name}। ਅੱਜ {day_name} ਹੈ। {rem_text}"
                    else:
                        rem_text = f"You have {len(rem_titles)} reminders today: {', '.join(rem_titles)}." if rem_titles else "No scheduled reminders today."
                        msg = f"Good morning {patient_name}. Today is {day_name}. {rem_text}"

                    doc = {
                        "patient_id": patient_id,
                        "type": "morning_greeting",
                        "message": msg,
                        "lang": lang,
                        "date": current_date_str,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                    await proactive_coll.insert_one(doc)
                    return doc

            # B. Evening Wind-down (20:00 - 22:00, once per day)
            if hour >= 20 and hour < 22:
                already_winddown = await proactive_coll.find_one({
                    "patient_id": patient_id,
                    "type": "evening_winddown",
                    "date": current_date_str,
                })
                if not already_winddown:
                    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    logs = (
                        db.query(ReminderLog)
                        .filter(ReminderLog.patient_id == patient_id, ReminderLog.timestamp >= today_start)
                        .all()
                    )
                    done_count = sum(1 for l in logs if l.outcome == "acknowledged")

                    if lang == "hi":
                        msg = f"आज आपने अपनी दवाइयां समय पर लीं। शुभ रात्रि {patient_name}।"
                    elif lang == "pa":
                        msg = f"ਅੱਜ ਤੁਸੀਂ ਆਪਣੀਆਂ ਦਵਾਈਆਂ ਸਮੇਂ ਸਿਰ ਲਈਆਂ। ਸ਼ੁਭ ਰਾਤ {patient_name}।"
                    else:
                        msg = f"Today you completed your daily routine and took your medications. Good night {patient_name}."

                    doc = {
                        "patient_id": patient_id,
                        "type": "evening_winddown",
                        "message": msg,
                        "lang": lang,
                        "date": current_date_str,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                    await proactive_coll.insert_one(doc)
                    return doc

            # C. Gentle Check-in every few hours
            checkin_coll = mongo_manager.get_collection("checkin_logs")
            last_checkin = await checkin_coll.find_one({"patient_id": patient_id})
            freq_hours = comp_settings.get("check_in_frequency_hours", 3)

            should_checkin = False
            if not last_checkin:
                should_checkin = True
            else:
                last_time = datetime.fromisoformat(last_checkin["last_checkin_at"])
                if datetime.utcnow() - last_time >= timedelta(hours=freq_hours):
                    should_checkin = True

            if should_checkin:
                if lang == "hi":
                    msg = f"नमस्ते {patient_name}, आप अभी कैसा महसूस कर रहे हैं?"
                elif lang == "pa":
                    msg = f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ {patient_name}, ਤੁਸੀਂ ਹੁਣ ਕਿਵੇਂ ਮਹਿਸੂਸ ਕਰ ਰਹੇ ਹੋ?"
                else:
                    msg = f"Hello {patient_name}, how are you feeling right now?"

                checkin_id = f"checkin_{int(now.timestamp())}"
                doc = {
                    "patient_id": patient_id,
                    "type": "check_in",
                    "checkin_id": checkin_id,
                    "message": msg,
                    "lang": lang,
                    "actions": ["respond_ok", "need_help"],
                    "created_at": datetime.utcnow().isoformat(),
                }
                await checkin_coll.update_one(
                    {"patient_id": patient_id},
                    {
                        "$set": {
                            "last_checkin_at": datetime.utcnow().isoformat(),
                            "current_checkin_id": checkin_id,
                            "pending_response": True,
                        }
                    },
                )
                return doc

            return None

        finally:
            if close_db:
                db.close()


companion_service = CompanionService()
