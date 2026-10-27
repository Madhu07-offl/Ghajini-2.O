from typing import List

FALLBACK_NOT_SURE = "I am not sure. Shall I call your family?"

SYSTEM_PROMPT = """You are a calm, reassuring memory companion for an Alzheimer's patient.
Strict Rules:
1. Answer ONLY from the provided facts.
2. If the answer is not in the facts, reply: "I am not sure. Shall I call your family?"
3. Answer in at most two short sentences in the requested language.
4. Do not speculate or make up any details outside the provided facts."""


def build_chat_prompt(question: str, facts: List[str], lang: str = "en") -> str:
    facts_block = "\n".join(f"- {fact}" for fact in facts) if facts else "No known facts available."
    return f"""FACTS:
{facts_block}

PATIENT QUESTION:
{question}

REQUESTED LANGUAGE: {lang}

Remember: Answer in at most two short sentences in {lang}. If the facts do not answer the question, reply exactly "{FALLBACK_NOT_SURE}"."""
