from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from backend.app.database import Base

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    thresholds = Column(JSON)

class ContentLog(Base):
    __tablename__ = "content_logs"

    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String)
    content_preview = Column(String)
    scores = Column(JSON)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    decision = Column(String)  # "allow", "block", "flag"
    explanation = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    risk_score = Column(Float, nullable=True)
    source_id = Column(String, nullable=True, index=True)
    source_platform = Column(String, nullable=True)
    author_handle = Column(String, nullable=True)
    author_url = Column(String, nullable=True)
    caption_text = Column(String, nullable=True)
    transcription_text = Column(String, nullable=True)
    extracted_identifiers = Column(JSON, nullable=True)

class WatchTarget(Base):
    __tablename__ = "watch_targets"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String)
    target = Column(String)
    is_active = Column(Boolean, default=True)
