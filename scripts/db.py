"""Database models and session management."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from .config_loader import get_config

Base = declarative_base()


class Video(Base):
    """Original uploaded videos."""

    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    s3_key = Column(String(1000), nullable=False, unique=True)
    s3_bucket = Column(String(255), nullable=False, default="per-aspera-brain")
    file_size_bytes = Column(BigInteger)
    duration_seconds = Column(Numeric(10, 2))
    resolution = Column(String(50))
    format = Column(String(20))
    status = Column(String(50), default="uploaded")
    uploaded_by = Column(String(255))
    extra_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata fields
    speaker = Column(String(255))
    event_name = Column(String(255))
    event_date = Column(Date)
    description = Column(Text)
    thumbnail_s3_key = Column(String(1000))  # Pre-generated thumbnail

    # Relationships
    transcripts = relationship("Transcript", back_populates="video", cascade="all, delete-orphan")
    clips = relationship("Clip", back_populates="source_video", cascade="all, delete-orphan")


class Transcript(Base):
    """Transcriptions of videos."""

    __tablename__ = "transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    s3_key = Column(String(1000), nullable=False, unique=True)
    provider = Column(String(50), default="aws")
    language = Column(String(20), default="en-US")
    full_text = Column(Text)
    word_count = Column(Integer)
    status = Column(String(50), default="pending")
    error_message = Column(Text)
    extra_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="transcripts")
    segments = relationship("TranscriptSegment", back_populates="transcript", cascade="all, delete-orphan")


class TranscriptSegment(Base):
    """Individual timestamped segments of transcripts."""

    __tablename__ = "transcript_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transcript_id = Column(UUID(as_uuid=True), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    segment_index = Column(Integer, nullable=False)
    start_time = Column(Numeric(10, 3), nullable=False)
    end_time = Column(Numeric(10, 3), nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Numeric(5, 4))
    speaker = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    transcript = relationship("Transcript", back_populates="segments")


class Clip(Base):
    """Segments cut from source videos."""

    __tablename__ = "clips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    clip_name = Column(String(500), nullable=False)
    s3_key = Column(String(1000), unique=True)
    start_time = Column(Numeric(10, 3), nullable=False)
    end_time = Column(Numeric(10, 3), nullable=False)
    status = Column(String(50), default="pending")
    file_size_bytes = Column(BigInteger)
    notes = Column(Text)
    created_by = Column(String(255))
    extra_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source_video = relationship("Video", back_populates="clips")
    compiled_video_clips = relationship("CompiledVideoClip", back_populates="clip")

    @property
    def duration_seconds(self) -> Decimal:
        return self.end_time - self.start_time


class CompiledVideo(Base):
    """Final videos assembled from clips."""

    __tablename__ = "compiled_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    s3_key = Column(String(1000), unique=True)
    total_duration_seconds = Column(Numeric(10, 2))
    file_size_bytes = Column(BigInteger)
    resolution = Column(String(50))
    status = Column(String(50), default="pending")
    created_by = Column(String(255))
    extra_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    compiled_video_clips = relationship(
        "CompiledVideoClip", back_populates="compiled_video", cascade="all, delete-orphan"
    )


class CompiledVideoClip(Base):
    """Junction table: clips in compiled videos with ordering."""

    __tablename__ = "compiled_video_clips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    compiled_video_id = Column(
        UUID(as_uuid=True), ForeignKey("compiled_videos.id", ondelete="CASCADE"), nullable=False
    )
    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id", ondelete="CASCADE"), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    transition_type = Column(String(50), default="cut")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("compiled_video_id", "sequence_order"),)

    # Relationships
    compiled_video = relationship("CompiledVideo", back_populates="compiled_video_clips")
    clip = relationship("Clip", back_populates="compiled_video_clips")


class ProcessingJob(Base):
    """Track async processing operations."""

    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)
    reference_id = Column(UUID(as_uuid=True), nullable=False)
    reference_type = Column(String(50), nullable=False)
    aws_job_id = Column(String(500))
    status = Column(String(50), default="queued")
    progress = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ScriptFeedback(Base):
    """Store user feedback on generated scripts for few-shot learning."""

    __tablename__ = "script_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)  # What the user asked for
    script = Column(Text, nullable=False)  # The generated script
    clips_json = Column(JSONB, default=[])  # The clips used
    rating = Column(Integer, nullable=False)  # 1 = good (thumbs up), -1 = bad (thumbs down)
    model = Column(String(50))  # Which model generated it
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class User(Base):
    """Team members who can use the system."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_login = Column(DateTime(timezone=True))

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Chat conversations for script generation."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False, default="New Chat")
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    is_collaborative = Column(Integer, default=0)  # 1 if shared with team
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    video = relationship("Video")
    participants = relationship("ChatParticipant", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Individual messages within a conversation."""

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Who sent it
    role = Column(String(20), nullable=False)  # 'user', 'assistant', or 'system'
    content = Column(Text, nullable=False)
    clips_json = Column(JSONB, default=[])  # Clips associated with this message (for assistant messages)
    mentions = Column(JSONB, default=[])  # List of user IDs or 'mv-video' mentioned
    model = Column(String(50))  # Which model generated it (for assistant messages)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[user_id])


class ChatParticipant(Base):
    """Users invited to collaborate on a conversation."""

    __tablename__ = "chat_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default="member")  # 'owner', 'member'
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("conversation_id", "user_id"),)

    # Relationships
    conversation = relationship("Conversation")
    user = relationship("User", foreign_keys=[user_id])


class ClipComment(Base):
    """Comments on specific clips within a conversation."""

    __tablename__ = "clip_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    clip_index = Column(Integer, nullable=False)  # Which clip in the message's clips_json
    content = Column(Text, nullable=False)
    mentions = Column(JSONB, default=[])  # @mentions in comment
    is_regenerate_request = Column(Integer, default=0)  # 1 if this is a request to regenerate the clip
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation")
    message = relationship("ChatMessage")
    user = relationship("User")


class VoiceAvatar(Base):
    """AI voice clones for speakers."""

    __tablename__ = "voice_avatars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    speaker_name = Column(String(255), nullable=False, unique=True)
    provider = Column(String(50), default="elevenlabs")  # elevenlabs, playht, etc.
    external_voice_id = Column(String(255))  # Voice ID from the provider
    sample_video_ids = Column(JSONB, default=[])  # Video IDs used to train the voice
    status = Column(String(50), default="pending")  # pending, training, ready, failed
    settings = Column(JSONB, default={})  # Provider-specific settings
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User")


# Database session management
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        config = get_config()
        _engine = create_engine(config.db_connection_string, pool_pre_ping=True)
    return _engine


def get_session_factory():
    """Get the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_session() -> Session:
    """Get a new database session."""
    SessionLocal = get_session_factory()
    return SessionLocal()


class DatabaseSession:
    """Context manager for database sessions."""

    def __init__(self):
        self.session: Optional[Session] = None

    def __enter__(self) -> Session:
        self.session = get_session()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()


def init_db():
    """Initialize database tables (use SQL script for production)."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
