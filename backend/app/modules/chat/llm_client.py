import logging
from typing import List, Optional, Tuple
import httpx

from app.core.config import settings
from app.modules.chat.prompts import (
    FALLBACK_NOT_SURE,
    SYSTEM_PROMPT,
    build_chat_prompt,
    get_fallback_not_sure,
)

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.temperature = settings.OLLAMA_TEMPERATURE
        self.max_tokens = settings.OLLAMA_MAX_TOKENS
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    async def generate_answer(
        self, question: str, facts: List[str], lang: str = "en"
    ) -> Tuple[str, bool]:
        """
        Calls Ollama to answer based strictly on facts.
        Returns: (answer_text, is_grounded)
        If Ollama fails, falls back to top retrieved fact template.
        """
        if not facts:
            return get_fallback_not_sure(lang), False

        prompt = build_chat_prompt(question, facts, lang)
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT.format(lang=lang),
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("response", "").strip()
                    if answer:
                        fallback_phrase = get_fallback_not_sure(lang).lower()
                        is_grounded = fallback_phrase not in answer.lower()
                        return answer, is_grounded
        except Exception as e:
            logger.warning(f"Ollama call failed ({e}). Falling back to top retrieved fact template.")

        # Fallback from top retrieved fact using template
        top_fact = facts[0] if facts else ""
        return self._template_fallback(question, top_fact, lang)

    def _template_fallback(self, question: str, top_fact: str, lang: str) -> Tuple[str, bool]:
        if not top_fact:
            return get_fallback_not_sure(lang), False

        # Check simple relevance between question words and top fact
        q_words = set(w.lower() for w in question.split() if len(w) > 3)
        fact_words = set(w.lower() for w in top_fact.split())
        overlap = q_words.intersection(fact_words)

        if not overlap and len(q_words) > 0:
            return get_fallback_not_sure(lang), False

        # Template answer in requested language
        if lang.lower().startswith("hi"):
            return f"आपकी स्मृति के अनुसार: {top_fact}", True
        elif lang.lower().startswith("pa"):
            return f"ਤੁਹਾਡੀ ਯਾਦ ਦੇ ਅਨੁਸਾਰ: {top_fact}", True
        return f"{top_fact}", True


ollama_client = OllamaClient()
