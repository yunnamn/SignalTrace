import json
from pathlib import Path

from backend.app.scoring import evaluate
from ml_pipeline.classifier import MLPipeline


THRESHOLDS = {
    "casino": 0.35,
    "pyramid": 0.35,
    "guaranteed_income": 0.40,
    "referral": 0.45,
    "investment_scam": 0.35,
    "block_threshold": 0.55,
    "flag_threshold": 0.30,
    "hard_block": 0.95,
}


def main():
    dataset_path = Path(__file__).with_name("eval_dataset.jsonl")
    rows = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    pipeline = MLPipeline()
    pipeline.load_models()

    correct_label = 0
    scam_tp = scam_fp = scam_fn = 0
    results = []

    for row in rows:
        output = pipeline.classify_content(text=row["text"])
        scores = output["scores"]
        predicted_label = max(scores.items(), key=lambda item: item[1])[0]
        evaluation = evaluate(scores, THRESHOLDS)
        predicted_is_scam = evaluation["decision"] in {"flag", "block"}
        actual_is_scam = row["label"] != "safe"

        if row["label"] == "safe" and not predicted_is_scam:
            correct_label += 1
        elif predicted_label == row["label"]:
            correct_label += 1

        scam_tp += int(predicted_is_scam and actual_is_scam)
        scam_fp += int(predicted_is_scam and not actual_is_scam)
        scam_fn += int((not predicted_is_scam) and actual_is_scam)

        results.append({
            "lang": row["lang"],
            "label": row["label"],
            "predicted_label": predicted_label,
            "decision": evaluation["decision"],
            "risk_score": round(evaluation["risk_score"], 4),
            "scores": {key: round(value, 4) for key, value in scores.items()},
        })

    precision = scam_tp / (scam_tp + scam_fp) if scam_tp + scam_fp else 0.0
    recall = scam_tp / (scam_tp + scam_fn) if scam_tp + scam_fn else 0.0
    accuracy = correct_label / len(rows) if rows else 0.0

    print(json.dumps({
        "items": len(rows),
        "label_accuracy": round(accuracy, 4),
        "scam_precision": round(precision, 4),
        "scam_recall": round(recall, 4),
        "results": results,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
