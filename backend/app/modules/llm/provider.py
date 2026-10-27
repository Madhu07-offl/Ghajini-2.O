import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# 1. Fixed Templates in 3 Languages (Guaranteed Fallbacks)
# -------------------------------------------------------------
TEMPLATES_PATIENT_MESSAGE = {
    "en": "I am calling {caregiver} for you. Please stay right here.",
    "hi": "मैं आपके लिए {caregiver} को फ़ोन कर रहा हूँ। कृपया यहीं रहें।",
    "pa": "ਮੈਂ ਤੁਹਾਡੇ ਲਈ {caregiver} ਨੂੰ ਫ਼ੋਨ ਕਰ ਰਿਹਾ ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਇੱਥੇ ਹੀ ਰਹੋ।",
}

TEMPLATES_CAREGIVER_BRIEFING = {
    "en": (
        "🚨 Ghajini 2.0 Alert: {patient} needs assistance.\n"
        "Reason: {reason}{help_tag}\n"
        "Time: {time}{reminder_tag}"
    ),
    "hi": (
        "🚨 गजनी 2.0 चेतावनी: {patient} को सहायता की आवश्यकता है।\n"
        "कारण: {reason}{help_tag}\n"
        "समय: {time}{reminder_tag}"
    ),
    "pa": (
        "🚨 ਗਜਨੀ 2.0 ਚੇਤਾਵਨੀ: {patient} ਨੂੰ ਮਦਦ ਦੀ ਲੋੜ ਹੈ।\n"
        "ਕਾਰਨ: {reason}{help_tag}\n"
        "ਸਮਾਂ: {time}{reminder_tag}"
    ),
}

REASON_TRANSLATIONS = {
    "hi": {
        "SOS Button pressed": "मदद (SOS) बटन दबाया गया",
        "Emergency phrase detected": "आपातकालीन आवाज़ सुनाई दी",
        "Critical reminder not acknowledged": "दवा का स्मरण अनदेखा किया गया",
        "2 missed check-ins": "दो बार हाल-चाल नहीं मिला",
        "Patient asked to call family": "परिवार से बात करने का अनुरोध",
    },
    "pa": {
        "SOS Button pressed": "ਮਦਦ (SOS) ਬਟਨ ਦਬਾਇਆ ਗਿਆ",
        "Emergency phrase detected": "ਐਮਰਜੈਂਸੀ ਆਵਾਜ਼ ਸੁਣੀ ਗਈ",
        "Critical reminder not acknowledged": "ਦਵਾਈ ਦਾ ਸੁਨੇਹਾ ਅਣਦੇਖਿਆ ਰਿਹਾ",
        "2 missed check-ins": "ਦੋ ਵਾਰੀ ਹਾਲ-ਚਾਲ ਨਹੀਂ ਮਿਲਿਆ",
        "Patient asked to call family": "ਪਰਿਵਾਰ ਨੂੰ ਫ਼ੋਨ ਕਰਨ ਦੀ ਬੇਨਤੀ",
    },
}


def get_fallback_patient_message(caregiver_name: str, lang: str = "en") -> str:
    lang = lang if lang in TEMPLATES_PATIENT_MESSAGE else "en"
    template = TEMPLATES_PATIENT_MESSAGE[lang]
    return template.format(caregiver=caregiver_name)


def get_fallback_caregiver_briefing(
    patient_name: str,
    reason: str,
    time_str: str,
    last_reminder: Optional[str] = None,
    pressed_help: bool = False,
    lang: str = "en",
) -> str:
    lang = lang if lang in TEMPLATES_CAREGIVER_BRIEFING else "en"
    translated_reason = reason
    if lang in REASON_TRANSLATIONS:
        for en_key, tr_val in REASON_TRANSLATIONS[lang].items():
            if en_key.lower() in reason.lower():
                translated_reason = tr_val
                break

    help_tag = ""
    if pressed_help:
        help_tag = " (Pressed Help)" if lang == "en" else (" (मदद बटन)" if lang == "hi" else " (ਮਦਦ ਬਟਨ)")

    reminder_tag = ""
    if last_reminder:
        reminder_tag = f" | Last Reminder: {last_reminder}" if lang == "en" else (
            f" | अंतिम स्मरण: {last_reminder}" if lang == "hi" else f" | ਆਖਰੀ ਸੁਨੇਹਾ: {last_reminder}"
        )

    template = TEMPLATES_CAREGIVER_BRIEFING[lang]
    return template.format(
        patient=patient_name,
        reason=translated_reason,
        time=time_str,
        help_tag=help_tag,
        reminder_tag=reminder_tag,
    )


# -------------------------------------------------------------
# 2. PII Sanitization for OpenRouter (No names, phones, details)
# -------------------------------------------------------------
def sanitize_prompt_for_openrouter(
    prompt: str,
    patient_name: str,
    caregiver_name: str,
    phone_number: Optional[str] = None,
) -> Tuple[str, Dict[str, str]]:
    """
    Replaces real personal names, numbers, and addresses with placeholders
    before sending to external OpenRouter API.
    """
    replacements = {
        patient_name: "[PATIENT]",
        caregiver_name: "[CAREGIVER]",
    }
    if phone_number:
        replacements[phone_number] = "[PHONE]"

    sanitized = prompt
    for real_val, placeholder in replacements.items():
        if real_val:
            sanitized = re.sub(re.escape(real_val), placeholder, sanitized, flags=re.IGNORECASE)

    # Strip any phone number patterns e.g. +919876543210 or 10-digit numbers
    sanitized = re.sub(r"\+?\d{10,13}", "[PHONE]", sanitized)

    return sanitized, replacements


def desanitize_text_from_openrouter(
    text: str,
    patient_name: str,
    caregiver_name: str,
) -> str:
    """Restores real names back from placeholders."""
    desanitized = text.replace("[PATIENT]", patient_name).replace("PATIENT", patient_name)
    desanitized = desanitized.replace("[CAREGIVER]", caregiver_name).replace("CAREGIVER", caregiver_name)
    desanitized = desanitized.replace("[PHONE]", "").replace("PHONE", "")
    return desanitized.strip()


# -------------------------------------------------------------
# 3. Guardrail: Hallucination & Fact Check
# -------------------------------------------------------------
def validate_generated_wording(
    text: str,
    allowed_facts: list,
    patient_name: str,
    caregiver_name: str,
) -> bool:
    """
    Checks that the text does not invent foreign names, numbers or facts
    not in the allowed facts.
    """
    if not text or len(text.strip()) < 5:
        return False

    # Extract all capitalized words that might be names
    words = re.findall(r"\b[A-Z][a-z]+\b", text)
    allowed_words = {patient_name.lower(), caregiver_name.lower(), "ghajini", "alert", "reason", "time", "last", "reminder"}
    for f in allowed_facts:
        for w in re.findall(r"\b[a-zA-Z]+\b", str(f).lower()):
            allowed_words.add(w)

    for w in words:
        if len(w) > 3 and w.lower() not in allowed_words:
            # Check common English sentence starter words
            if w.lower() in {"please", "stay", "here", "help", "calling", "assistance", "your", "today"}:
                continue
            logger.warning(f"[GUARDRAIL FAIL] Invented word '{w}' not in allowed facts.")
            return False

    return True


# -------------------------------------------------------------
# 4. Free AI Call Wording Generator (Ollama / OpenRouter Switch)
# -------------------------------------------------------------
async def generate_call_wording(
    patient_name: str,
    caregiver_name: str,
    reason: str,
    time_str: str,
    last_reminder: Optional[str] = None,
    pressed_help: bool = False,
    lang: str = "en",
) -> Tuple[str, str]:
    """
    Generates:
      1. patient_message: One calm sentence spoken to patient.
      2. caregiver_briefing: Max 3 short lines sent to caregiver.

    Uses Ollama (local free) or OpenRouter (:free models with PII sanitization).
    Falls back to guaranteed templates if anything fails.
    """
    fallback_patient = get_fallback_patient_message(caregiver_name, lang=lang)
    fallback_briefing = get_fallback_caregiver_briefing(
        patient_name=patient_name,
        reason=reason,
        time_str=time_str,
        last_reminder=last_reminder,
        pressed_help=pressed_help,
        lang=lang,
    )

    provider = settings.LLM_PROVIDER.lower().strip()
    if provider == "openrouter" and settings.OPENROUTER_API_KEY:
        # Check that model ends with :free
        model = settings.OPENROUTER_MODEL
        if not model.endswith(":free"):
            logger.warning(f"OpenRouter model '{model}' does not end with ':free'. Appending ':free'.")
            model = f"{model}:free"

        system_instruction = (
            "You are a medical caregiver assistant. Write two outputs:\n"
            "1. PATIENT_MESSAGE: Exactly ONE short, soothing sentence telling the patient that you are calling [CAREGIVER] and to stay calm.\n"
            "2. CAREGIVER_BRIEFING: At most 3 short bullet lines summarizing who needs help, why, and the current time.\n"
            f"Language: Respond in '{lang}' (en=English, hi=Hindi, pa=Punjabi).\n"
            "Do NOT include any additional conversation or markdown fences."
        )
        user_prompt = (
            f"Patient: [PATIENT]\n"
            f"Caregiver: [CAREGIVER]\n"
            f"Reason: {reason}\n"
            f"Time: {time_str}\n"
            f"Last Reminder: {last_reminder or 'None'}\n"
            f"Pressed Help: {'Yes' if pressed_help else 'No'}\n"
        )

        sanitized_user_prompt, _ = sanitize_prompt_for_openrouter(
            user_prompt, patient_name, caregiver_name
        )

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://ghajini-memory.local",
            "X-Title": "Ghajini 2.0",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": sanitized_user_prompt},
            ],
            "max_tokens": 150,
            "temperature": 0.2,
        }

        # Attempt with at most 1 retry on 429
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
                    if resp.status_code == 429:
                        logger.warning(f"OpenRouter rate limit 429 (attempt {attempt+1}/2). Waiting 1s...")
                        if attempt == 0:
                            await asyncio.sleep(1.0)
                            continue
                        else:
                            return fallback_patient, fallback_briefing

                    if resp.status_code == 200:
                        data = resp.json()
                        raw_reply = data["choices"][0]["message"]["content"]
                        desanitized = desanitize_text_from_openrouter(raw_reply, patient_name, caregiver_name)
                        
                        # Parse patient_message and caregiver_briefing
                        parsed_patient, parsed_briefing = _parse_llm_call_output(desanitized, fallback_patient, fallback_briefing)
                        
                        # Guardrail checks
                        allowed = [patient_name, caregiver_name, reason, time_str, last_reminder]
                        if validate_generated_wording(parsed_patient, allowed, patient_name, caregiver_name):
                            return parsed_patient, parsed_briefing
                        else:
                            return fallback_patient, fallback_briefing
                    else:
                        logger.warning(f"OpenRouter returned status {resp.status_code}: {resp.text}")
                        return fallback_patient, fallback_briefing
            except Exception as e:
                logger.warning(f"OpenRouter call failed ({e}); using template fallback.")
                return fallback_patient, fallback_briefing

        return fallback_patient, fallback_briefing

    elif provider == "ollama":
        # Call local free Ollama
        prompt = (
            f"Write two short outputs in '{lang}' language:\n"
            f"1. PATIENT_MESSAGE: Exactly ONE short calm sentence telling {patient_name} that you are calling {caregiver_name} for them.\n"
            f"2. CAREGIVER_BRIEFING: Max 3 lines alert for {caregiver_name} about {patient_name}. Reason: {reason}. Time: {time_str}.\n"
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.2, "num_predict": 100},
                    },
                )
                if resp.status_code == 200:
                    raw_text = resp.json().get("response", "")
                    parsed_patient, parsed_briefing = _parse_llm_call_output(raw_text, fallback_patient, fallback_briefing)
                    allowed = [patient_name, caregiver_name, reason, time_str, last_reminder]
                    if validate_generated_wording(parsed_patient, allowed, patient_name, caregiver_name):
                        return parsed_patient, parsed_briefing
        except Exception as e:
            logger.info(f"Ollama call not available or timed out ({e}); using template fallback.")

    # Default to fixed templates
    return fallback_patient, fallback_briefing


def _parse_llm_call_output(raw: str, default_patient: str, default_briefing: str) -> Tuple[str, str]:
    """Helper to split LLM output into patient message and caregiver briefing."""
    patient_msg = default_patient
    briefing = default_briefing

    lines = [line.strip() for line in raw.split("\n") if line.strip()]
    patient_candidates = []
    briefing_candidates = []
    current_mode = None

    for line in lines:
        lower = line.lower()
        if "patient_message" in lower or "patient:" in lower:
            current_mode = "patient"
            clean = re.sub(r"^.*?patient(_message)?:?\s*", "", line, flags=re.IGNORECASE)
            if clean:
                patient_candidates.append(clean)
        elif "caregiver_briefing" in lower or "briefing:" in lower or "caregiver:" in lower:
            current_mode = "briefing"
            clean = re.sub(r"^.*?(caregiver_briefing|briefing|caregiver):?\s*", "", line, flags=re.IGNORECASE)
            if clean:
                briefing_candidates.append(clean)
        else:
            if current_mode == "patient":
                patient_candidates.append(line)
            elif current_mode == "briefing":
                briefing_candidates.append(line)
            else:
                if len(patient_candidates) == 0:
                    patient_candidates.append(line)
                else:
                    briefing_candidates.append(line)

    if patient_candidates:
        patient_msg = " ".join(patient_candidates).strip().strip('"').strip("'")
    if briefing_candidates:
        briefing = "\n".join(briefing_candidates[:3]).strip()

    return patient_msg, briefing
