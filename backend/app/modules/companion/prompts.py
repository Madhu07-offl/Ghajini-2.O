from typing import Dict, List

# Core translations in English, Hindi (Devanagari), and Punjabi (Gurmukhi)
NOT_SURE_BY_LANG: Dict[str, str] = {
    "en": "I am not sure. Shall I call your family?",
    "hi": "मुझे पक्का नहीं पता। क्या मैं आपके परिवार को फोन करूं?",
    "pa": "ਮੈਨੂੰ ਪੱਕਾ ਨਹੀਂ ਪਤਾ। ਕੀ ਮੈਂ ਤੁਹਾਡੇ ਪਰਿਵਾਰ ਨੂੰ ਫ਼ੋਨ ਕਰਾਂ?",
}

REASSURE_BY_LANG: Dict[str, str] = {
    "en": "You are safe at home.",
    "hi": "आप घर पर सुरक्षित हैं।",
    "pa": "ਤੁਸੀਂ ਘਰ ਵਿੱਚ ਸੁਰੱਖਿਅਤ ਹੋ।",
}

HELP_IS_COMING_BY_LANG: Dict[str, str] = {
    "en": "Help is coming. I am telling your family.",
    "hi": "मदद आ रही है। मैं आपके परिवार को बता रहा हूँ।",
    "pa": "ਮਦਦ ਆ ਰਹੀ ਹੈ। ਮੈਂ ਤੁਹਾਡੇ ਪਰਿਵਾਰ ਨੂੰ ਦੱਸ ਰਿਹਾ ਹਾਂ।",
}

MEDICAL_ADVICE_DISCLAIMER_BY_LANG: Dict[str, str] = {
    "en": "Please ask your doctor.",
    "hi": "कृपया अपने डॉक्टर से पूछें।",
    "pa": "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਡਾਕਟਰ ਨੂੰ ਪੁੱਛੋ।",
}

CALLING_FAMILY_BY_LANG: Dict[str, str] = {
    "en": "I am calling your family now.",
    "hi": "मैं आपके परिवार को फोन मिला रहा हूँ।",
    "pa": "ਮੈਂ ਤੁਹਾਡੇ ਪਰਿਵਾਰ ਨੂੰ ਫ਼ੋਨ ਕਰ ਰਿਹਾ ਹਾਂ।",
}

GREETING_BY_LANG: Dict[str, str] = {
    "en": "Hello! I am Ghajini, always here with you. How can I help you today?",
    "hi": "नमस्ते! मैं गजनी हूँ, हमेशा आपके साथ। आज मैं आपकी क्या मदद कर सकता हूँ?",
    "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਗਜਨੀ ਹਾਂ, ਹਮੇਸ਼ਾ ਤੁਹਾਡੇ ਨਾਲ। ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
}


def get_not_sure_line(lang: str = "en") -> str:
    lang_key = (lang or "en").lower()[:2]
    return NOT_SURE_BY_LANG.get(lang_key, NOT_SURE_BY_LANG["en"])


def get_reassure_line(lang: str = "en") -> str:
    lang_key = (lang or "en").lower()[:2]
    return REASSURE_BY_LANG.get(lang_key, REASSURE_BY_LANG["en"])


def get_help_is_coming_line(lang: str = "en") -> str:
    lang_key = (lang or "en").lower()[:2]
    return HELP_IS_COMING_BY_LANG.get(lang_key, HELP_IS_COMING_BY_LANG["en"])


def get_medical_disclaimer_line(lang: str = "en") -> str:
    lang_key = (lang or "en").lower()[:2]
    return MEDICAL_ADVICE_DISCLAIMER_BY_LANG.get(lang_key, MEDICAL_ADVICE_DISCLAIMER_BY_LANG["en"])


def get_calling_family_line(lang: str = "en") -> str:
    lang_key = (lang or "en").lower()[:2]
    return CALLING_FAMILY_BY_LANG.get(lang_key, CALLING_FAMILY_BY_LANG["en"])


def get_smalltalk_greeting(lang: str = "en") -> str:
    lang_key = (lang or "en").lower()[:2]
    return GREETING_BY_LANG.get(lang_key, GREETING_BY_LANG["en"])


SYSTEM_PROMPT_TEMPLATE = """You are Ghajini, a kind, patient memory companion for {name}, who has memory difficulties.
Rules:
1. Use ONLY the FACTS and CONTEXT below. Never invent names, dates, places, medicines or doses.
2. If the answer is not in the facts, say: {not_sure_line_in_lang}
3. Reply in {language}, in at most two short, simple sentences.
4. Be warm and calm. Never argue, correct harshly, or say 'you already asked'.
5. If the person sounds confused or worried, first reassure ('You are safe at home'), then answer.
6. Give no medical advice. For health doubts say: 'Please ask your doctor.'
7. If the person is in danger or very distressed, tell them help is coming.
FACTS:
{numbered_facts}
CONTEXT: local time {time}, date {date}, next reminder {next_reminder}, mood {mood}, patient tone {tone}."""


def build_companion_prompt(
    name: str,
    question: str,
    facts: List[str],
    lang: str,
    local_time: str,
    local_date: str,
    next_reminder: str,
    mood: str,
    tone: str,
) -> str:
    lang_key = (lang or "en").lower()[:2]
    not_sure = get_not_sure_line(lang_key)

    if facts:
        numbered_facts = "\n".join(f"{i+1}. {fact}" for i, fact in enumerate(facts))
    else:
        numbered_facts = "None."

    system_filled = SYSTEM_PROMPT_TEMPLATE.format(
        name=name,
        not_sure_line_in_lang=not_sure,
        language=lang_key,
        numbered_facts=numbered_facts,
        time=local_time,
        date=local_date,
        next_reminder=next_reminder or "No reminders due",
        mood=mood,
        tone=tone or "calm",
    )

    prompt = f"""{system_filled}

PATIENT: {question}
GHAJINI:"""
    return prompt
