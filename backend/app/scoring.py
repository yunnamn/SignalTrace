SCAM_CATEGORIES = {
    "casino",
    "pyramid",
    "guaranteed_income",
    "referral",
    "investment_scam",
}


def _bounded(score) -> float:
    try:
        return max(0.0, min(1.0, float(score)))
    except (TypeError, ValueError):
        return 0.0


def evaluate(scores: dict, profile_thresholds: dict) -> dict:
    clean_scores = {
        category: _bounded(score)
        for category, score in (scores or {}).items()
        if category in SCAM_CATEGORIES
    }

    hard_block = _bounded(profile_thresholds.get("hard_block", 0.95))
    block_threshold = _bounded(profile_thresholds.get("block_threshold", 0.65))
    flag_threshold = _bounded(profile_thresholds.get("flag_threshold", 0.35))

    ordered = sorted(clean_scores.items(), key=lambda item: item[1], reverse=True)
    top_score = ordered[0][1] if ordered else 0.0
    second_score = ordered[1][1] if len(ordered) > 1 else 0.0
    meaningful_scores = [score for _, score in ordered if score >= 0.20]
    meaningful_avg = sum(meaningful_scores) / len(meaningful_scores) if meaningful_scores else 0.0
    risk = min(1.0, (top_score * 0.75) + (second_score * 0.20) + (meaningful_avg * 0.05))

    explanation = []
    threshold_hits = []
    for category, score in ordered:
        threshold = _bounded(profile_thresholds.get(category, 0.5))
        if score >= threshold:
            threshold_hits.append(category)
            explanation.append({
                "category": category,
                "score": score,
                "threshold": threshold,
                "reason": "category_threshold_exceeded",
            })

    hard_hits = [category for category, score in ordered if score >= hard_block]
    if hard_hits:
        decision = "block"
        explanation.append({
            "reason": "hard_block_threshold_exceeded",
            "categories": hard_hits,
            "threshold": hard_block,
        })
    elif risk >= block_threshold and threshold_hits:
        decision = "block"
        explanation.append({
            "reason": "aggregate_risk_with_threshold_evidence",
            "risk_score": risk,
            "threshold": block_threshold,
        })
    elif risk >= flag_threshold or threshold_hits:
        decision = "flag"
        explanation.append({
            "reason": "review_recommended",
            "risk_score": risk,
            "threshold": flag_threshold,
        })
    else:
        decision = "allow"
        explanation.append({
            "reason": "below_thresholds",
            "risk_score": risk,
            "highest_score": top_score,
        })

    return {"risk_score": risk, "decision": decision, "explanation": explanation}
