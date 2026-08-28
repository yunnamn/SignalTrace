from ml_pipeline.classifier import MLPipeline


class FakeZeroShot:
    def __init__(self, scores_by_label):
        self.scores_by_label = scores_by_label

    def __call__(self, text, labels, multi_label=False):
        scores = [self.scores_by_label.get(label, 0.0) for label in labels]
        ordered = sorted(zip(labels, scores), key=lambda item: item[1], reverse=True)
        return {
            "labels": [label for label, _ in ordered],
            "scores": [score for _, score in ordered],
        }


def test_legitimate_financial_education_is_dampened():
    pipeline = MLPipeline()
    neutral = pipeline.neutral_text_labels[0]
    investment = pipeline.text_category_labels["investment_scam"]
    pipeline.text_classifier = FakeZeroShot({
        neutral: 0.82,
        investment: 0.12,
    })

    scores = pipeline._classify_text_scores(
        "How to build an emergency fund, reduce debt, and invest through diversified index funds."
    )

    assert scores["investment_scam"] < 0.10
    assert max(scores.values()) < 0.25


def test_obvious_ru_scam_gets_category_evidence():
    pipeline = MLPipeline()
    scam_label = pipeline.text_category_labels["investment_scam"]
    neutral = pipeline.neutral_text_labels[0]
    pipeline.text_classifier = FakeZeroShot({
        scam_label: 0.72,
        neutral: 0.05,
    })

    scores = pipeline._classify_text_scores(
        "Крипта даст x100, заходи до листинга, гарантирую рост депозита."
    )

    assert scores["investment_scam"] > 0.65
    assert scores["guaranteed_income"] > 0.0


def test_kazakh_safe_savings_content_stays_low():
    pipeline = MLPipeline()
    neutral = pipeline.neutral_text_labels[0]
    pipeline.text_classifier = FakeZeroShot({neutral: 0.88})

    scores = pipeline._classify_text_scores(
        "Ай сайын табыстың бір бөлігін жинап, қарызды уақытында төлеу туралы кеңес."
    )

    assert max(scores.values()) < 0.25
