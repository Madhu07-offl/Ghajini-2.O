import json
import os
import re
import sys
import time
from typing import List

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.core.config import settings
from app.db.session import init_db
from app.main import app, preload_indices

# Ensure tables and demo data are initialized and indices preloaded
settings.init_directories()
init_db()
preload_indices()

client = TestClient(app)


def check_hallucination(answer: str, sources: List[str]) -> bool:
    """
    Checks if the answer contains any specific numbers or dates that are
    NOT present anywhere in the retrieved factual sources.
    Returns True if hallucination is detected.
    """
    if not sources:
        # If ungrounded fallback, not a hallucination
        if "not sure" in answer.lower() or "पक्का नहीं" in answer or "ਪੱਕਾ ਨਹੀਂ" in answer:
            return False

    sources_combined = " ".join(sources).lower()
    answer_lower = answer.lower()

    # Find numbers / years / times in answer
    nums_in_answer = re.findall(r"\b\d+[\:\.]?\d*\b", answer_lower)
    for num in nums_in_answer:
        # If number is part of common speech like "two", ignore; if digit sequence like 9876543210 or 9:00, must be in sources
        if len(num) >= 2 or num.isdigit():
            if num not in sources_combined:
                return True

    return False


def run_qa_evaluation():
    questions_file = os.path.join(backend_dir, "eval_data", "questions.jsonl")
    if not os.path.exists(questions_file):
        questions_file = os.path.abspath("eval_data/questions.jsonl")

    print(f"==================================================")
    print(f" Ghajini 2.0 Grounding & Q&A Accuracy Evaluation")
    print(f" Dataset: {questions_file}")
    print(f"==================================================")

    with open(questions_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    total_questions = len(lines)
    correct_count = 0
    not_sure_count = 0
    hallucination_count = 0
    latencies = []

    print(f"\nEvaluating {total_questions} questions across English, Hindi, Punjabi...\n")
    print(f"{'#':<3} | {'Lang':<5} | {'Question':<38} | {'Lat(ms)':<8} | {'Status':<10}")
    print("-" * 72)

    for idx, line in enumerate(lines, 1):
        item = json.loads(line)
        q = item["q"]
        expect_list = item.get("expect", [])
        lang = item.get("lang", "en")

        t0 = time.time()
        res = client.post("/v1/ask", json={"text": q, "lang": lang})
        latency_ms = round((time.time() - t0) * 1000, 1)
        latencies.append(latency_ms)

        if res.status_code != 200:
            print(f"{idx:<3} | {lang:<5} | {q[:36]:<38} | {latency_ms:<8.1f} | ERROR ({res.status_code})")
            continue

        data = res.json()
        answer = data.get("answer", "")
        grounded = data.get("grounded", False)
        sources = data.get("sources", [])

        # Check "I am not sure" count
        is_fallback = (not grounded) or any(
            phrase in answer.lower()
            for phrase in ["not sure", "call your family", "पक्का नहीं", "ਪੱਕਾ ਨਹੀਂ"]
        )
        if is_fallback:
            not_sure_count += 1

        # Check Hallucination
        has_hallucination = check_hallucination(answer, sources)
        if has_hallucination:
            hallucination_count += 1

        # Check Correctness
        is_correct = False
        expect_lower = [e.lower() for e in expect_list]

        if any("not sure" in e or "पक्का नहीं" in e for e in expect_lower):
            # Expecting fallback
            is_correct = is_fallback and not has_hallucination
        else:
            # Expecting grounded facts
            combined_context = (answer + " " + " ".join(sources)).lower()
            matches_expected = any(e in combined_context for e in expect_lower)
            is_correct = matches_expected and not has_hallucination

        if is_correct:
            correct_count += 1
            status_str = "CORRECT"
        else:
            status_str = "FAIL"

        print(f"{idx:<3} | {lang:<5} | {q[:36]:<38} | {latency_ms:<8.1f} | {status_str}")

    accuracy_pct = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0.0
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0
    slowest_latency = max(latencies) if latencies else 0.0

    print("-" * 72)
    print("\n================ EVALUATION SUMMARY ================")
    print(f"Total Questions Evaluated : {total_questions}")
    print(f"Answered Correctly       : {correct_count}/{total_questions} ({accuracy_pct}%)")
    print(f"'I am not sure' Count     : {not_sure_count}")
    print(f"Hallucination Count      : {hallucination_count} (target: 0)")
    print(f"Average Response Time    : {avg_latency:.1f} ms")
    print(f"Slowest Response Time    : {slowest_latency:.1f} ms")
    print("====================================================\n")

    # Save to eval_results/qa.json
    results_dir = os.path.join(backend_dir, "eval_results")
    os.makedirs(results_dir, exist_ok=True)
    out_file = os.path.join(results_dir, "qa.json")

    results_data = {
        "total_questions": total_questions,
        "correct_count": correct_count,
        "accuracy_pct": accuracy_pct,
        "not_sure_count": not_sure_count,
        "hallucination_count": hallucination_count,
        "average_latency_ms": avg_latency,
        "slowest_latency_ms": slowest_latency,
    }

    with open(out_file, "w") as f:
        json.dump(results_data, f, indent=2)

    return results_data


if __name__ == "__main__":
    run_qa_evaluation()
