import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    tier = Column(String(50), default="free")  # "free" | "pro"
    credits = Column(Integer, default=10)      # Default 10 free credits for new users
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    transcripts = relationship("TranscriptRecord", back_populates="owner", cascade="all, delete-orphan")

class TranscriptRecord(Base):
    __tablename__ = "transcripts"

    id = Column(String(100), primary_key=True, index=True)  # task_id (UUID)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    instagram_url = Column(String(500), nullable=True)
    title = Column(String(500), nullable=True)
    uploader = Column(String(255), nullable=True)
    thumbnail = Column(String(500), nullable=True)
    duration = Column(Integer, default=0)
    duration_formatted = Column(String(50), nullable=True)
    detected_language = Column(String(50), default="en")
    language_name = Column(String(100), default="English")
    full_text = Column(Text, nullable=True)
    translated_text = Column(Text, nullable=True)
    target_language = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    key_points_json = Column(Text, nullable=True)  # JSON serialized list of key points
    segments_json = Column(Text, nullable=True)    # JSON serialized list of timestamped segments
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="transcripts")
