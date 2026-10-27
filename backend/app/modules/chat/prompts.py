from typing import Dict, List

# Translations for "I am not sure. Shall I call your family?"
FALLBACK_NOT_SURE_BY_LANG: Dict[str, str] = {
    "en": "I am not sure. Shall I call your family?",
    "hi": "मुझे पक्का नहीं पता। क्या मैं आपके परिवार को फोन करूं?",
    "pa": "ਮੈਨੂੰ ਪੱਕਾ ਨਹੀਂ ਪਤਾ। ਕੀ ਮੈਂ ਤੁਹਾਡੇ ਪਰਿਵਾਰ ਨੂੰ ਫ਼ੋਨ ਕਰਾਂ?",
}

FALLBACK_NOT_SURE = FALLBACK_NOT_SURE_BY_LANG["en"]

# Emergency responses
EMERGENCY_RESPONSE_BY_LANG: Dict[str, str] = {
    "en": "Help is coming. I am telling your family.",
    "hi": "मदद आ रही है। मैं आपके परिवार को बता रहा हूँ।",
    "pa": "ਮਦਦ ਆ ਰਹੀ ਹੈ। ਮੈਂ ਤੁਹਾਡੇ ਪਰਿਵਾਰ ਨੂੰ ਦੱਸ ਰਿਹਾ ਹਾਂ।",
}

# Emergency phrases in English, Hindi, and Punjabi
EMERGENCY_PHRASES = [
    "help",
    "i am lost",
    "i'm lost",
    "i fell",
    "i have fallen",
    "i hurt myself",
    "emergency",
    "madad",
    "bachao",
    "mai kho gaya",
    "main kho gaya",
    "main gir gaya",
    "main gir gayi",
    "mai gir gaya",
    "madad karo",
    "main dig paya",
    "main dig payi",
]


def is_emergency_phrase(text: str) -> bool:
    """Returns True if input text contains an emergency phrase."""
    lower_text = text.lower().strip()
    words = lower_text.split()
    for phrase in EMERGENCY_PHRASES:
        if " " in phrase:
            if phrase in lower_text:
                return True
        else:
            if phrase in words or lower_text == phrase:
                return True
    return False


def get_fallback_not_sure(lang: str = "en") -> str:
    lang_key = lang.lower()[:2]
    return FALLBACK_NOT_SURE_BY_LANG.get(lang_key, FALLBACK_NOT_SURE)


def get_emergency_response(lang: str = "en") -> str:
    lang_key = lang.lower()[:2]
    return EMERGENCY_RESPONSE_BY_LANG.get(lang_key, EMERGENCY_RESPONSE_BY_LANG["en"])


SYSTEM_PROMPT = """You are a calm, reassuring memory companion for an Alzheimer's patient.
Strict Rules:
1. Answer ONLY from the provided facts.
2. If the answer is not in the facts, reply with the exact 'not sure' phrase in {lang}:
   - en: "I am not sure. Shall I call your family?"
   - hi: "मुझे पक्का नहीं पता। क्या मैं आपके परिवार को फोन करूं?"
   - pa: "ਮੈਨੂੰ ਪੱਕਾ नहीं पता। ਕੀ ਮੈਂ ਤੁਹਾਡੇ ਪਰਿਵਾਰ ਨੂੰ ਫ਼ੋਨ ਕਰਾਂ?"
3. Answer in at most two short sentences in {lang}.
4. Do not speculate or make up any details outside the provided facts."""


def build_chat_prompt(question: str, facts: List[str], lang: str = "en") -> str:
    facts_block = "\n".join(f"- {fact}" for fact in facts) if facts else "No known facts available."
    fallback_msg = get_fallback_not_sure(lang)

    return f"""FACTS:
{facts_block}

PATIENT QUESTION:
{question}

REQUESTED LANGUAGE: {lang}

Remember: Answer in at most two short sentences strictly in {lang}.
If the facts do not answer the question, reply exactly: "{fallback_msg}"."""
