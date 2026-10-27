import glob
import json
import os
import sys

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import numpy as np
from app.core.config import settings
from app.modules.faces.engine import FaceEngine


def evaluate_faces():
    eval_dir = os.path.join(backend_dir, "eval_data")
    if not os.path.exists(eval_dir):
        # Fallback to workspace root
        eval_dir = os.path.abspath("eval_data")

    print(f"==================================================")
    print(f" Ghajini 2.0 Face Threshold Tuning & Evaluation")
    print(f" Reading eval directory: {eval_dir}")
    print(f"==================================================")

    # Initialize a clean standalone FaceEngine
    engine = FaceEngine()

    person_dirs = [
        d for d in os.listdir(eval_dir)
        if os.path.isdir(os.path.join(eval_dir, d)) and not d.startswith("_")
    ]
    person_dirs.sort()

    person_to_id = {}
    enrolled_count = 0
    test_positives = []  # (person_id, name, img_path)

    # 1. Enroll first 3 photos of each person, reserve rest for testing
    face_counter = 1000
    for idx, p_name in enumerate(person_dirs, 1):
        person_to_id[p_name] = idx
        p_path = os.path.join(eval_dir, p_name)
        images = sorted(glob.glob(os.path.join(p_path, "*.jpg")) + glob.glob(os.path.join(p_path, "*.png")))

        enroll_images = images[:3]
        test_images = images[3:]

        for img_p in enroll_images:
            with open(img_p, "rb") as f:
                img_bytes = f.read()
            emb, qual = engine.extract_face_embedding(img_bytes)
            if emb is None:
                # Deterministic synthetic vector
                emb = np.zeros(512, dtype=np.float32)
                emb[hash(p_name) % 512] = 1.0
                emb = engine._normalize(emb)
            face_counter += 1
            engine.add_face(face_counter, idx, emb)
            enrolled_count += 1

        for img_p in test_images:
            test_positives.append((idx, p_name, img_p))

    print(f"Enrolled {enrolled_count} face photos across {len(person_dirs)} known people.")
    print(f"Positive test images reserved: {len(test_positives)}")

    # 2. Gather unknown stranger images
    unknown_dir = os.path.join(eval_dir, "_unknown")
    unknown_images = sorted(glob.glob(os.path.join(unknown_dir, "*.jpg")) + glob.glob(os.path.join(unknown_dir, "*.png")))
    print(f"Unknown stranger images: {len(unknown_images)}")

    # 3. Test positive samples
    pos_scores = []  # (is_correct_person, score)
    for expected_id, p_name, img_p in test_positives:
        with open(img_p, "rb") as f:
            img_bytes = f.read()
        res = engine.recognize(img_bytes)
        predicted_id = res.get("person_id")
        score = float(res.get("similarity", 0.0))
        is_correct = (predicted_id == expected_id)
        pos_scores.append((is_correct, score, p_name))

    # 4. Test unknown samples
    unknown_scores = []
    for img_p in unknown_images:
        with open(img_p, "rb") as f:
            img_bytes = f.read()
        res = engine.recognize(img_bytes)
        score = float(res.get("similarity", 0.0))
        unknown_scores.append(score)

    # 5. Threshold Analysis
    thresholds = [round(t, 2) for t in np.arange(0.20, 0.72, 0.04)]
    results_table = []

    total_pos = max(len(pos_scores), 1)
    total_neg = max(len(unknown_scores), 1)

    suggested_high = 0.50
    suggested_low = 0.38
    best_f1 = -1.0

    for t in thresholds:
        # True Accept: positive correctly identified with score >= t
        true_accepts = sum(1 for is_corr, sc, _ in pos_scores if is_corr and sc >= t)
        # False Accept: stranger accepted with score >= t OR positive misclassified with score >= t
        false_accepts_unknown = sum(1 for sc in unknown_scores if sc >= t)
        false_accepts_pos = sum(1 for is_corr, sc, _ in pos_scores if not is_corr and sc >= t)
        total_fa = false_accepts_unknown + false_accepts_pos

        tar = round((true_accepts / total_pos) * 100, 1)
        far = round((total_fa / total_neg) * 100, 1)

        precision = (true_accepts / (true_accepts + total_fa)) if (true_accepts + total_fa) > 0 else 0
        recall = true_accepts / total_pos
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

        if f1 > best_f1:
            best_f1 = f1
            suggested_high = t

        results_table.append({
            "threshold": t,
            "true_accepts": true_accepts,
            "false_accepts": total_fa,
            "TAR_pct": tar,
            "FAR_pct": far,
        })

    # Suggested Low threshold: gives ~95%+ recall or ~0.12 below high
    low_candidates = [r["threshold"] for r in results_table if r["TAR_pct"] >= 90.0 and r["FAR_pct"] <= 15.0]
    if low_candidates:
        suggested_low = min(low_candidates)
    else:
        suggested_low = max(0.30, round(suggested_high - 0.12, 2))

    # Print Table
    print("\n------------------------------------------------------------")
    print(f"{'Threshold':<12} | {'True Accepts':<14} | {'False Accepts':<14} | {'TAR %':<8} | {'FAR %':<8}")
    print("------------------------------------------------------------")
    for r in results_table:
        print(f"{r['threshold']:<12.2f} | {r['true_accepts']:<14} | {r['false_accepts']:<14} | {r['TAR_pct']:<8.1f} | {r['FAR_pct']:<8.1f}")
    print("------------------------------------------------------------")
    print(f"\n>> Suggested FACE_T_HIGH : {suggested_high:.2f} (High confidence match)")
    print(f">> Suggested FACE_T_LOW  : {suggested_low:.2f} (Lower boundary / Uncertain window)")
    print("------------------------------------------------------------\n")

    # Save to eval_results/faces.json
    results_dir = os.path.join(backend_dir, "eval_results")
    os.makedirs(results_dir, exist_ok=True)
    out_file = os.path.join(results_dir, "faces.json")

    output_data = {
        "enrolled_known_people": len(person_dirs),
        "total_enrolled_faces": enrolled_count,
        "test_positive_samples": len(test_positives),
        "test_unknown_samples": len(unknown_images),
        "suggested_thresholds": {
            "FACE_T_HIGH": suggested_high,
            "FACE_T_LOW": suggested_low,
        },
        "threshold_sweep": results_table,
    }

    with open(out_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Results saved to: {out_file}")
    return output_data


if __name__ == "__main__":
    evaluate_faces()
