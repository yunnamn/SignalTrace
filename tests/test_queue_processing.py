import importlib
import sys
import asyncio


def test_queue_save_persists_canonical_url_and_identifiers(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'queue.db'}")
    for name in list(sys.modules):
        if name.startswith("backend.app"):
            sys.modules.pop(name)

    database = importlib.import_module("backend.app.database")
    models = importlib.import_module("backend.app.models")
    url_queue = importlib.import_module("backend.app.url_queue")
    models.Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()
    profile = models.Profile(name="standard", thresholds={
        "casino": 0.35,
        "pyramid": 0.35,
        "guaranteed_income": 0.40,
        "referral": 0.45,
        "investment_scam": 0.35,
        "block_threshold": 0.55,
        "flag_threshold": 0.30,
        "hard_block": 0.95,
    })
    db.add(profile)
    db.commit()
    db.refresh(profile)
    db.close()

    queue = url_queue.URLQueue()
    queue._save_to_db(
        "https://www.youtube.com/watch?v=abc123&t=10",
        profile.id,
        {
            "scores": {
                "casino": 0.0,
                "pyramid": 0.0,
                "guaranteed_income": 0.0,
                "referral": 0.0,
                "investment_scam": 0.0,
            },
            "transcription": "use promo SAVE10",
        },
        text="",
        title="Safe finance video",
        platform="youtube",
        author_handle="same_name",
        author_url="https://youtube.com/@same_name",
    )

    db = database.SessionLocal()
    log = db.query(models.ContentLog).one()
    db.close()

    assert "https://www.youtube.com/watch?v=abc123&t=10" in log.content_preview
    assert {"type": "promo", "value": "SAVE10"} in log.extracted_identifiers
    assert log.transcription_text == "use promo SAVE10"
    assert log.source_id == "youtube:abc123"
    assert not any("transcription" in item for item in log.explanation)


def test_auto_crawler_queues_same_discovery_once_before_db_save(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'crawler.db'}")
    for name in list(sys.modules):
        if name.startswith("backend.app"):
            sys.modules.pop(name)

    database = importlib.import_module("backend.app.database")
    models = importlib.import_module("backend.app.models")
    auto_crawler = importlib.import_module("backend.app.auto_crawler")
    models.Base.metadata.create_all(bind=database.engine)

    class FakeQueue:
        def __init__(self):
            self.items = []

        async def add(self, **kwargs):
            self.items.append(kwargs)

    crawler = auto_crawler.AutoCrawler()
    crawler.profile_id = 1
    queue = FakeQueue()
    posts = [
        {
            "platform": "youtube",
            "post_url": "https://youtube.com/watch?v=abc123",
            "caption_text": "same",
            "author_handle": "channel",
            "author_url": "https://youtube.com/@channel",
            "media_url": None,
        },
        {
            "platform": "youtube",
            "post_url": "https://youtu.be/abc123",
            "caption_text": "same duplicate",
            "author_handle": "channel",
            "author_url": "https://youtube.com/@channel",
            "media_url": None,
        },
    ]

    added = asyncio.run(crawler._queue_posts(posts, queue))

    assert added == 1
    assert len(queue.items) == 1
    assert ("youtube:abc123", 1) in crawler.pending_keys
    queue.items[0]["on_complete"](queue.items[0]["dedupe_key"])
    assert ("youtube:abc123", 1) not in crawler.pending_keys


def test_auto_crawler_skips_same_profile_already_analyzed(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'crawler_same_profile.db'}")
    for name in list(sys.modules):
        if name.startswith("backend.app"):
            sys.modules.pop(name)

    database = importlib.import_module("backend.app.database")
    models = importlib.import_module("backend.app.models")
    auto_crawler = importlib.import_module("backend.app.auto_crawler")
    models.Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()
    db.add(models.ContentLog(
        content_type="video_url",
        content_preview="Stored title ||| https://www.youtube.com/watch?v=abc123&t=10",
        source_id="youtube:abc123",
        scores={},
        profile_id=1,
        decision="allow",
        explanation=[],
        risk_score=0.0,
    ))
    db.add(models.ContentLog(
        content_type="video_url",
        content_preview="Older raw row ||| https://www.youtube.com/watch?v=legacy001&t=99",
        source_id=None,
        scores={},
        profile_id=1,
        decision="allow",
        explanation=[],
        risk_score=0.0,
    ))
    db.commit()
    db.close()

    class FakeQueue:
        def __init__(self):
            self.items = []

        async def add(self, **kwargs):
            self.items.append(kwargs)

    crawler = auto_crawler.AutoCrawler()
    crawler.profile_id = 1
    assert crawler._is_duplicate("https://youtu.be/legacy001") is True
    queue = FakeQueue()
    posts = [
        {
            "platform": "youtube",
            "post_url": "https://youtube.com/watch?v=abc123",
            "caption_text": "same",
            "author_handle": "channel",
            "author_url": "https://youtube.com/@channel",
            "media_url": None,
        },
        {
            "platform": "youtube",
            "post_url": "https://youtube.com/watch?v=xyz789",
            "caption_text": "new",
            "author_handle": "channel",
            "author_url": "https://youtube.com/@channel",
            "media_url": None,
        },
    ]

    added = asyncio.run(crawler._queue_posts(posts, queue))

    assert added == 1
    assert len(queue.items) == 1
    assert queue.items[0]["url"] == "https://youtube.com/watch?v=xyz789"


def test_auto_crawler_allows_same_source_for_different_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'crawler_other_profile.db'}")
    for name in list(sys.modules):
        if name.startswith("backend.app"):
            sys.modules.pop(name)

    database = importlib.import_module("backend.app.database")
    models = importlib.import_module("backend.app.models")
    auto_crawler = importlib.import_module("backend.app.auto_crawler")
    models.Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()
    db.add(models.ContentLog(
        content_type="video_url",
        content_preview="Stored title ||| https://www.youtube.com/watch?v=abc123",
        source_id="youtube:abc123",
        scores={},
        profile_id=1,
        decision="allow",
        explanation=[],
        risk_score=0.0,
    ))
    db.commit()
    db.close()

    class FakeQueue:
        def __init__(self):
            self.items = []

        async def add(self, **kwargs):
            self.items.append(kwargs)

    crawler = auto_crawler.AutoCrawler()
    crawler.profile_id = 2
    queue = FakeQueue()
    posts = [{
        "platform": "youtube",
        "post_url": "https://youtu.be/abc123",
        "caption_text": "same source, new profile",
        "author_handle": "channel",
        "author_url": "https://youtube.com/@channel",
        "media_url": None,
    }]

    added = asyncio.run(crawler._queue_posts(posts, queue))

    assert added == 1
    assert len(queue.items) == 1
    assert queue.items[0]["profile_id"] == 2
