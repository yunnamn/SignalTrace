import base64
import io
import asyncio
import os
from PIL import Image
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from backend.app.database import engine, get_db, Base
from backend.app import models, schemas
from backend.app.settings import CORS_ORIGINS, MAX_AUDIO_BYTES, MAX_IMAGE_BYTES
from backend.app.url_utils import URLValidationError, canonicalize_url, validate_public_url
from ml_pipeline.classifier import MLPipeline

BUILTIN_PROFILE_NAMES = {"strict", "standard", "soft"}

# Create tables if not using migrations (but we will use alembic, so this is just fallback)
# Base.metadata.create_all(bind=engine)

# Global instance of ML Pipeline
ml_classifier = MLPipeline()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed default profiles
    db = next(get_db())
    default_profiles = [
        {
            "name": "strict",
            "thresholds": {
                "casino": 0.15,
                "pyramid": 0.15,
                "guaranteed_income": 0.15,
                "referral": 0.20,
                "investment_scam": 0.15,
                "block_threshold": 0.40,
                "flag_threshold": 0.20,
                "hard_block": 0.90
            }
        },
        {
            "name": "standard",
            "thresholds": {
                "casino": 0.35,
                "pyramid": 0.35,
                "guaranteed_income": 0.40,
                "referral": 0.45,
                "investment_scam": 0.35,
                "block_threshold": 0.55,
                "flag_threshold": 0.30,
                "hard_block": 0.95
            }
        },
        {
            "name": "soft",
            "thresholds": {
                "casino": 0.60,
                "pyramid": 0.60,
                "guaranteed_income": 0.65,
                "referral": 0.70,
                "investment_scam": 0.60,
                "block_threshold": 0.75,
                "flag_threshold": 0.50,
                "hard_block": 0.98
            }
        }
    ]
    
    # Cleanup old profiles
    old_names = ["parent", "corporate", "government", "personal"]
    db.query(models.Profile).filter(models.Profile.name.in_(old_names)).delete(synchronize_session=False)
    
    for p in default_profiles:
        existing = db.query(models.Profile).filter(models.Profile.name == p["name"]).first()
        if not existing:
            new_p = models.Profile(name=p["name"], thresholds=p["thresholds"])
            db.add(new_p)
    db.commit()
    
    # Seed default watch_targets if none exist
    existing_targets = db.query(models.WatchTarget).count()
    if existing_targets == 0:
        default_targets = [
            {"platform": "youtube", "target": "ytsearch5:онлайн казино занос"},
            {"platform": "youtube", "target": "ytsearch5:заработок тенге без вложений"},
            {"platform": "youtube", "target": "ytsearch5:онлайн казино ұтыс"},
            {"platform": "youtube", "target": "ytsearch5:тез ақша табу тәсілдері"},
        ]
        for t in default_targets:
            wt = models.WatchTarget(platform=t["platform"], target=t["target"])
            db.add(wt)
        db.commit()
        print(f"Seeded {len(default_targets)} default watch targets.")
    
    # Pre-load ML models unless disabled for lightweight tests/smoke runs.
    if os.getenv("LOAD_MODELS_ON_STARTUP", "true").lower() == "true":
        ml_classifier.load_models()
    
    yield
    # Shutdown logic if any

app = FastAPI(title="AI Media Watch API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/profiles", response_model=list[schemas.ProfileResponse])
def get_profiles(db: Session = Depends(get_db)):
    return db.query(models.Profile).all()

@app.post("/profiles", response_model=schemas.ProfileResponse)
def create_profile(profile: schemas.ProfileCreate, db: Session = Depends(get_db)):
    db_profile = models.Profile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@app.put("/profiles/{profile_id}", response_model=schemas.ProfileResponse)
def update_profile(profile_id: int, profile: schemas.ProfileCreate, db: Session = Depends(get_db)):
    db_profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if db_profile.name in BUILTIN_PROFILE_NAMES and profile.name != db_profile.name:
        raise HTTPException(status_code=400, detail="Built-in profile names cannot be changed")
    
    db_profile.name = profile.name
    db_profile.thresholds = profile.thresholds
    db.commit()
    db.refresh(db_profile)
    return db_profile

@app.post("/moderate", response_model=schemas.ModerationResponse)
def moderate_content(request: schemas.ModerationRequest, db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter(models.Profile.id == request.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    image = None
    if request.image_base64:
        # Decode base64 to PIL Image
        try:
            image_data = base64.b64decode(request.image_base64)
            if len(image_data) > MAX_IMAGE_BYTES:
                raise HTTPException(status_code=413, detail="Image is too large")
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail="Invalid image base64")

    if not request.text and not image and not request.url:
        raise HTTPException(status_code=400, detail="Must provide text, image_base64, or url")

    safe_url = None
    if request.url:
        try:
            safe_url = validate_public_url(request.url)
        except URLValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    # Run ML pipeline
    result = ml_classifier.classify_content(text=request.text, image=image, url=safe_url)
    scores = result["scores"]
    transcription = result["transcription"]
    
    # Evaluate decision
    from backend.app.scoring import evaluate
    evaluation = evaluate(scores, profile.thresholds)
    decision = evaluation["decision"]
    explanation = evaluation["explanation"]
    risk_score = evaluation["risk_score"]

    # Log the content
    content_preview = ""
    content_type = ""
    if safe_url:
        content_preview = safe_url
        content_type = "video_url"
    elif request.text:
        content_preview = request.text[:100]
        content_type = "text"
    elif image:
        content_preview = "[IMAGE]"
        content_type = "image"
        
    log_entry = models.ContentLog(
        content_type=content_type,
        content_preview=content_preview,
        scores=scores,
        profile_id=profile.id,
        decision=decision,
        explanation=explanation,
        risk_score=risk_score,
        source_id=canonicalize_url(safe_url) if safe_url else None,
        transcription_text=transcription
    )
    db.add(log_entry)
    db.commit()
    
    return schemas.ModerationResponse(
        decision=decision,
        explanation=explanation,
        scores=scores,
        transcription=transcription,
        risk_score=risk_score
    )

from pydantic import BaseModel

class QueueAddRequest(BaseModel):
    url: str
    profile_id: int

from backend.app.url_queue import url_queue_instance
from backend.app.auto_crawler import auto_crawler_instance

class QueueStartRequest(BaseModel):
    profile_id: int

@app.post("/queue/add")
async def add_to_queue(req: QueueAddRequest, db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter(models.Profile.id == req.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    try:
        safe_url = validate_public_url(req.url)
    except URLValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await url_queue_instance.add(safe_url, req.profile_id, priority=0)
    if not url_queue_instance.is_running:
        url_queue_instance.start(ml_classifier)
    return {"status": "queued", "queue_size": url_queue_instance.queue_size}

@app.post("/queue/start")
async def start_queue(req: QueueStartRequest, db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter(models.Profile.id == req.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    url_queue_instance.start(ml_classifier)
    auto_crawler_instance.start(url_queue_instance, req.profile_id)
    return {"status": "started"}

@app.post("/queue/stop")
async def stop_queue():
    url_queue_instance.stop()
    auto_crawler_instance.stop()
    return {"status": "stopped"}

@app.get("/queue/status")
def get_queue_status():
    return {
        "is_running": url_queue_instance.is_running,
        "is_autopilot_running": auto_crawler_instance.is_running,
        "queue_size": url_queue_instance.queue_size,
        "last_processed_url": url_queue_instance.last_processed_url
    }

@app.get("/logs", response_model=list[schemas.ContentLogResponse])
def get_logs(db: Session = Depends(get_db), limit: int = 50):
    return db.query(models.ContentLog).order_by(models.ContentLog.created_at.desc()).limit(limit).all()

@app.delete("/logs")
def clear_logs(db: Session = Depends(get_db)):
    db.query(models.ContentLog).delete()
    db.commit()
    url_queue_instance.clear()
    return {"status": "cleared"}

import tempfile
from fastapi import UploadFile, File
import networkx as nx

@app.post("/profile/analyze", response_model=schemas.ProfileAnalyzeResponse)
async def analyze_profile(req: schemas.ProfileAnalyzeRequest, db: Session = Depends(get_db)):
    from backend.app.connectors.youtube import YouTubeConnector
    from backend.app.connectors.vk import VKConnector
    from backend.app.connectors.telegram import TelegramConnector
    from backend.app.scoring import evaluate
    from backend.app.identifiers import extract
    
    connectors = {
        "youtube": YouTubeConnector(),
        "vk": VKConnector(),
        "telegram": TelegramConnector()
    }
    
    connector = connectors.get(req.platform)
    if not connector:
        raise HTTPException(status_code=400, detail="Invalid platform")
        
    profile = db.query(models.Profile).filter(models.Profile.id == req.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    posts = await asyncio.to_thread(connector.fetch_account, req.target, 15)
    
    items = []
    total_risk = 0.0
    
    for post in posts:
        media_url = post.get("media_url") or post.get("post_url")
        try:
            safe_media_url = validate_public_url(media_url) if media_url else None
            result = await asyncio.to_thread(
                ml_classifier.classify_content,
                text=post.get("caption_text"),
                image=None,
                url=safe_media_url,
            )
        except Exception as exc:
            print(f"Media analysis unavailable for {media_url}: {exc}")
            result = await asyncio.to_thread(
                ml_classifier.classify_content,
                text=post.get("caption_text"),
                image=None,
                url=None,
            )
        scores = result.get("scores", {})
        transcription = result.get("transcription", "")
        
        evaluation = evaluate(scores, profile.thresholds)
        decision = evaluation["decision"]
        explanation = evaluation["explanation"]
        risk_score = evaluation["risk_score"]
        
        all_text = (post.get("caption_text") or "") + "\n" + transcription
        identifiers = extract(all_text)
        
        log_entry = models.ContentLog(
            content_type="text" if req.platform in ["vk", "telegram"] else "video_url",
            content_preview=post["post_url"],
            scores=scores,
            profile_id=profile.id,
            decision=decision,
            explanation=explanation,
            risk_score=risk_score,
            source_id=post.get("source_id") or canonicalize_url(post["post_url"]),
            source_platform=post["platform"],
            author_handle=post["author_handle"],
            author_url=post["author_url"],
            caption_text=post["caption_text"],
            transcription_text=transcription,
            extracted_identifiers=identifiers
        )
            
        db.add(log_entry)
        
        items.append({
            "post": post,
            "risk_score": risk_score,
            "decision": decision,
            "scores": scores,
            "explanation": explanation,
            "transcription": transcription
        })
        total_risk += risk_score
        
    db.commit()
    
    items.sort(key=lambda x: x["risk_score"], reverse=True)
    
    avg_risk = total_risk / len(items) if items else 0.0
    account_info = {
        "handle": req.target,
        "platform": req.platform,
        "url": posts[0]["author_url"] if posts else "",
        "avg_risk": avg_risk,
        "total_analyzed": len(items)
    }
    
    return {"account": account_info, "items": items[:10]}

@app.post("/moderate/audio", response_model=schemas.ModerationResponse)
async def moderate_audio(profile_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    content = await file.read()
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio file is too large")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(content)
        tmp_path = tmp.name
        
    try:
        transcription = await asyncio.to_thread(ml_classifier.transcribe_audio, tmp_path)
        result = await asyncio.to_thread(ml_classifier.classify_content, text=transcription, image=None, url=None)
        
        from backend.app.scoring import evaluate
        from backend.app.identifiers import extract
        
        scores = result.get("scores", {})
        evaluation = evaluate(scores, profile.thresholds)
        decision = evaluation["decision"]
        explanation = evaluation["explanation"]
        risk_score = evaluation["risk_score"]
        
        identifiers = extract(transcription)
        
        log_entry = models.ContentLog(
            content_type="audio",
            content_preview="[AUDIO] " + (file.filename or ""),
            scores=scores,
            profile_id=profile.id,
            decision=decision,
            explanation=explanation,
            risk_score=risk_score,
            source_platform="audio",
            transcription_text=transcription,
            extracted_identifiers=identifiers
        )
        db.add(log_entry)
        db.commit()
        
        return schemas.ModerationResponse(
            decision=decision,
            explanation=explanation,
            scores=scores,
            transcription=transcription,
            risk_score=risk_score
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.get("/graph")
def get_graph(min_degree: int = 1, db: Session = Depends(get_db)):
    logs = db.query(models.ContentLog).filter(models.ContentLog.author_handle != None).all()
    
    G = nx.Graph()
    account_stats = {}
    
    for log in logs:
        if not log.author_handle:
            continue
        handle = f"{log.source_platform or 'unknown'}:{log.author_handle}"
            
        if handle not in account_stats:
            account_stats[handle] = {"platform": log.source_platform, "risks": [], "count": 0, "identifiers": set()}
            G.add_node(handle)
            
        account_stats[handle]["risks"].append(log.risk_score or 0.0)
        account_stats[handle]["count"] += 1
        
        if log.extracted_identifiers:
            for idf in log.extracted_identifiers:
                val = f"{idf['type']}:{idf['value']}"
                account_stats[handle]["identifiers"].add(val)
                
    handles = list(account_stats.keys())
    for i in range(len(handles)):
        for j in range(i+1, len(handles)):
            h1 = handles[i]
            h2 = handles[j]
            shared = account_stats[h1]["identifiers"].intersection(account_stats[h2]["identifiers"])
            if shared:
                G.add_edge(h1, h2, shared=list(shared))
                
    components = list(nx.connected_components(G))
    
    nodes = []
    for h in handles:
        degree = G.degree[h] if h in G else 0
        if min_degree > 0 and degree < min_degree:
            continue
            
        avg_risk = sum(account_stats[h]["risks"]) / account_stats[h]["count"]
        
        cluster_id = -1
        for idx, comp in enumerate(components):
            if h in comp:
                cluster_id = idx
                break
                
        nodes.append({
            "id": h,
            "label": h.split(":", 1)[1] if ":" in h else h,
            "platform": account_stats[h]["platform"],
            "avg_risk": avg_risk,
            "post_count": account_stats[h]["count"],
            "cluster": cluster_id
        })
        
    edges = []
    for u, v, d in G.edges(data=True):
        if min_degree > 0 and (G.degree[u] < min_degree or G.degree[v] < min_degree):
            continue
        edges.append({
            "source": u,
            "target": v,
            "shared": d["shared"]
        })
        
    return {"nodes": nodes, "edges": edges}

class WatchlistCreateRequest(BaseModel):
    platform: str
    target: str

@app.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    return db.query(models.WatchTarget).all()
    
@app.post("/watchlist")
def add_watchlist(req: WatchlistCreateRequest, db: Session = Depends(get_db)):
    wt = models.WatchTarget(platform=req.platform, target=req.target)
    db.add(wt)
    db.commit()
    db.refresh(wt)
    return wt

@app.delete("/watchlist/{id}")
def delete_watchlist(id: int, db: Session = Depends(get_db)):
    db.query(models.WatchTarget).filter(models.WatchTarget.id == id).delete()
    db.commit()
    return {"status": "deleted"}
