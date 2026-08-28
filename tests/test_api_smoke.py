import importlib
import sys

from fastapi.testclient import TestClient

VALID_THRESHOLDS = {
    "casino": 0.35,
    "pyramid": 0.35,
    "guaranteed_income": 0.40,
    "referral": 0.45,
    "investment_scam": 0.35,
    "block_threshold": 0.55,
    "flag_threshold": 0.30,
    "hard_block": 0.95,
}


def load_test_app(monkeypatch, tmp_path, name):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("LOAD_MODELS_ON_STARTUP", "false")
    for name in list(sys.modules):
        if name.startswith("backend.app"):
            sys.modules.pop(name)

    database = importlib.import_module("backend.app.database")
    models = importlib.import_module("backend.app.models")
    main = importlib.import_module("backend.app.main")
    models.Base.metadata.create_all(bind=database.engine)
    return main


def test_moderate_blocks_private_url_and_accepts_text(monkeypatch, tmp_path):
    main = load_test_app(monkeypatch, tmp_path, "moderate")

    with TestClient(main.app) as client:
        profiles = client.get("/profiles").json()
        profile_id = profiles[0]["id"]

        private_url = client.post("/moderate", json={
            "profile_id": profile_id,
            "url": "http://127.0.0.1:8000/private",
        })
        assert private_url.status_code == 400

        monkeypatch.setattr(main.ml_classifier, "classify_content", lambda **kwargs: {
            "scores": {
                "casino": 0.0,
                "pyramid": 0.0,
                "guaranteed_income": 0.0,
                "referral": 0.0,
                "investment_scam": 0.0,
            },
            "transcription": "",
        })
        response = client.post("/moderate", json={
            "profile_id": profile_id,
            "text": "Budgeting and savings education.",
        })

    assert response.status_code == 200
    assert response.json()["decision"] == "allow"


def test_queue_endpoints_reject_missing_profile(monkeypatch, tmp_path):
    main = load_test_app(monkeypatch, tmp_path, "queue")

    with TestClient(main.app) as client:
        add_response = client.post("/queue/add", json={
            "profile_id": 999999,
            "url": "https://www.youtube.com/watch?v=abc123",
        })
        start_response = client.post("/queue/start", json={"profile_id": 999999})

    assert add_response.status_code == 404
    assert start_response.status_code == 404


def test_profile_threshold_validation_and_builtin_name_lock(monkeypatch, tmp_path):
    main = load_test_app(monkeypatch, tmp_path, "profiles")

    with TestClient(main.app) as client:
        profile = client.get("/profiles").json()[0]
        profile_id = profile["id"]

        out_of_range = dict(VALID_THRESHOLDS, casino=1.5)
        response = client.put(f"/profiles/{profile_id}", json={
            "name": profile["name"],
            "thresholds": out_of_range,
        })
        assert response.status_code == 422

        unknown_key = dict(VALID_THRESHOLDS, unknown=0.1)
        response = client.put(f"/profiles/{profile_id}", json={
            "name": profile["name"],
            "thresholds": unknown_key,
        })
        assert response.status_code == 422

        response = client.put(f"/profiles/{profile_id}", json={
            "name": "renamed_builtin",
            "thresholds": VALID_THRESHOLDS,
        })
        assert response.status_code == 400
