import pytest

from backend.app.identifiers import extract
from backend.app.scoring import evaluate
from backend.app.url_utils import URLValidationError, canonicalize_url, validate_public_url


STANDARD = {
    "casino": 0.35,
    "pyramid": 0.35,
    "guaranteed_income": 0.40,
    "referral": 0.45,
    "investment_scam": 0.35,
    "block_threshold": 0.55,
    "flag_threshold": 0.30,
    "hard_block": 0.95,
}


def test_low_scores_do_not_compound_to_block():
    result = evaluate({
        "casino": 0.18,
        "pyramid": 0.17,
        "guaranteed_income": 0.16,
        "referral": 0.15,
        "investment_scam": 0.14,
    }, STANDARD)

    assert result["decision"] == "allow"
    assert result["risk_score"] < STANDARD["flag_threshold"]
    assert result["explanation"][-1]["reason"] == "below_thresholds"


def test_block_requires_clear_threshold_evidence():
    result = evaluate({
        "casino": 0.72,
        "pyramid": 0.05,
        "guaranteed_income": 0.02,
        "referral": 0.01,
        "investment_scam": 0.03,
    }, STANDARD)

    assert result["decision"] == "block"
    assert any(item.get("category") == "casino" for item in result["explanation"])
    assert any(item.get("reason") == "aggregate_risk_with_threshold_evidence" for item in result["explanation"])


def test_youtube_canonicalization_preserves_video_identity():
    first = canonicalize_url("https://www.youtube.com/watch?v=abc123&t=10")
    second = canonicalize_url("https://youtube.com/watch?v=xyz789")
    short = canonicalize_url("https://youtu.be/abc123?si=share")
    shorts = canonicalize_url("https://www.youtube.com/shorts/short123")
    embed = canonicalize_url("https://www.youtube.com/embed/embed123")

    assert first == "youtube:abc123"
    assert second == "youtube:xyz789"
    assert short == "youtube:abc123"
    assert shorts == "youtube:short123"
    assert embed == "youtube:embed123"
    assert first != second


def test_identifier_extraction_adds_canonical_url():
    ids = extract("Watch https://youtu.be/abc123 and use promo SAVE10")
    assert {"type": "canonical_url", "value": "youtube:abc123"} in ids
    assert {"type": "promo", "value": "SAVE10"} in ids


def test_url_validation_blocks_localhost():
    with pytest.raises(URLValidationError):
        validate_public_url("http://localhost:8000/admin")
