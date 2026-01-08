"""Database models and session management."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

try:
    from .config_loader import get_config
except ImportError:
    from config_loader import get_config

Base = declarative_base()


class Video(Base):
    """Original uploaded videos."""

    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    s3_key = Column(String(1000), nullable=False, unique=True)
    s3_bucket = Column(String(255), nullable=False, default="mv-brain")
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
    frames = relationship("VideoFrame", back_populates="video", cascade="all, delete-orphan")


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
    totp_secret = Column(String(32), nullable=True)  # 2FA secret key
    totp_enabled = Column(Integer, default=0)  # 1 = 2FA required
    temp_2fa_secret = Column(String(32), nullable=True)  # Temporary storage during setup
    email_verified = Column(Integer, default=0)  # 1 = email verified
    verification_token = Column(String(64), nullable=True)  # Email verification token
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_login = Column(DateTime(timezone=True))

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    backup_codes = relationship("BackupCode", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    """Projects group conversations with shared context and instructions."""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    custom_instructions = Column(Text)  # System prompt for AI in this project
    color = Column(String(20), default="#d97757")  # Project color for UI
    is_archived = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="projects")
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")


class Conversation(Base):
    """Chat conversations for script generation."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False, default="New Chat")
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    is_collaborative = Column(Integer, default=0)  # 1 if shared with team
    starred = Column(Boolean, default=False)  # Whether chat is starred by user
    preferred_model = Column(String(50), default="gpt-4o")  # User's preferred AI model for this conversation
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")
    project = relationship("Project", back_populates="conversations")
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
    attachments_json = Column(JSONB, default=[])  # File attachments associated with this message
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


class AILog(Base):
    """Log of all AI API calls for quality monitoring."""

    __tablename__ = "ai_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Request metadata
    request_type = Column(String(50), nullable=False)  # chat, regenerate_clip, regenerate_record, etc.
    model = Column(String(100), nullable=False)  # claude-sonnet, gpt-4o, etc.

    # Context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)

    # Request/Response content
    prompt = Column(Text, nullable=True)  # The prompt sent to AI
    context_summary = Column(Text, nullable=True)  # Summary of context provided (not full transcripts)
    response = Column(Text, nullable=True)  # Full AI response

    # Extracted results
    clips_generated = Column(Integer, default=0)  # Number of clips in response
    response_json = Column(JSONB, nullable=True)  # Parsed JSON from response (clips, etc.)

    # Performance & Status
    success = Column(Integer, default=1)  # 1 = success, 0 = failure
    error_message = Column(Text, nullable=True)  # Error message if failed
    latency_ms = Column(Float, nullable=True)  # Time taken in milliseconds
    input_tokens = Column(Integer, nullable=True)  # Token count (if available)
    output_tokens = Column(Integer, nullable=True)
    total_cost = Column(Float, nullable=True)  # Total cost in USD for this call
    input_cost = Column(Float, nullable=True)  # Cost for input tokens
    output_cost = Column(Float, nullable=True)  # Cost for output tokens

    # RAG Integration Metrics (Prompt 18)
    search_method = Column(String(20), nullable=True)  # 'rag', 'keyword', 'hybrid', 'rag_failed'
    rag_chunks_used = Column(Integer, nullable=True)  # Number of RAG chunks included in context
    rag_similarity_scores = Column(JSONB, nullable=True)  # Array of similarity scores for chunks used
    rag_embedding_cost = Column(Float, nullable=True)  # Cost of query embedding ($)
    rag_search_time_ms = Column(Float, nullable=True)  # Time for RAG search only
    context_compression_ratio = Column(Float, nullable=True)  # Old tokens / New tokens
    estimated_cost_savings = Column(Float, nullable=True)  # $ saved vs full transcript approach
    rag_fallback_reason = Column(String(100), nullable=True)  # Why fallback was used if applicable

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    conversation = relationship("Conversation")


class AIPromptCache(Base):
    """Cache for identical prompts to avoid duplicate API calls."""

    __tablename__ = "ai_prompt_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_hash = Column(String(64), nullable=False, unique=True)  # SHA256 of prompt+model
    model = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_cost = Column(Float, nullable=True)
    hit_count = Column(Integer, default=1)  # How many times this was reused

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_used_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class GenerationJob(Base):
    """Pipeline jobs for long-form content generation (Prompt 20)."""

    __tablename__ = "generation_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job metadata
    job_name = Column(String(255), nullable=False)  # User-friendly name
    job_type = Column(String(50), nullable=False)  # 'article', 'script', 'report', etc.
    status = Column(String(50), nullable=False, default='brief_analysis')  # Pipeline stage

    # Content specifications
    brief = Column(Text, nullable=False)  # Original user brief/request
    target_word_count = Column(Integer)  # Approximate target length
    target_audience = Column(String(255))  # Who is this for
    content_format = Column(String(100))  # 'blog_post', 'linkedin_article', 'script', etc.

    # Pipeline artifacts (JSON objects)
    outline = Column(JSONB, nullable=True)  # Section breakdown with word targets
    style_guide = Column(JSONB, nullable=True)  # Tone, voice, formatting rules
    fact_sheet = Column(JSONB, nullable=True)  # Established facts to maintain consistency
    character_bible = Column(JSONB, nullable=True)  # Character info (for scripts)

    # Generation progress
    sections_total = Column(Integer, default=0)  # Number of sections planned
    sections_completed = Column(Integer, default=0)  # Number completed
    current_section = Column(Integer, default=0)  # Current section being worked on
    sections_content = Column(JSONB, default={})  # Dict of section_num -> content

    # Final output
    assembled_content = Column(Text, nullable=True)  # Final assembled document
    word_count_actual = Column(Integer, nullable=True)  # Actual final word count

    # Quality checks
    continuity_issues = Column(JSONB, default=[])  # List of continuity problems found
    fact_conflicts = Column(JSONB, default=[])  # Contradictions with fact sheet

    # Cost tracking
    total_tokens_used = Column(Integer, default=0)  # Sum across all pipeline stages
    total_cost = Column(Float, default=0.0)  # Total $ cost for this job

    # User and timestamps
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)  # If job failed
    retry_count = Column(Integer, default=0)  # Number of retry attempts

    # Relationships
    creator = relationship("User")


class Persona(Base):
    """Voice profiles for people (Dan Goldin, etc.)."""

    __tablename__ = "personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)

    # Manual voice configuration
    description = Column(Text)  # Who is this person
    tone = Column(Text)  # e.g., "authoritative but approachable"
    style_notes = Column(Text)  # Writing style notes
    topics = Column(JSONB, default=[])  # Topics they typically discuss
    vocabulary = Column(JSONB, default=[])  # Key phrases/words they use

    # Auto-learned voice (populated by analyzing their content)
    learned_style = Column(JSONB, default={})  # AI-generated style analysis

    # Links to existing data
    speaker_name_in_videos = Column(String(255))  # Links to videos.speaker field

    # Metadata
    avatar_url = Column(Text)
    is_active = Column(Integer, default=1)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User")
    documents = relationship("Document", back_populates="persona", cascade="all, delete-orphan")
    social_posts = relationship("SocialPost", back_populates="persona", cascade="all, delete-orphan")


class Document(Base):
    """Articles, call transcripts, notes for personas."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="SET NULL"), nullable=True)

    # Document info
    title = Column(String(500), nullable=False)
    doc_type = Column(String(50), nullable=False)  # article, call_transcript, notes, other

    # Content
    content_text = Column(Text)  # Extracted/parsed text content
    content_summary = Column(Text)  # AI-generated summary
    word_count = Column(Integer)

    # Source file (if uploaded)
    source_filename = Column(String(500))
    source_s3_key = Column(String(1000))
    source_format = Column(String(20))  # pdf, docx, txt, audio

    # For audio transcripts
    duration_seconds = Column(Numeric(10, 2))
    transcription_provider = Column(String(50))  # whisper, aws, etc.

    # Metadata
    document_date = Column(Date)
    source_url = Column(Text)
    tags = Column(JSONB, default=[])
    extra_data = Column(JSONB, default={})

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    persona = relationship("Persona", back_populates="documents")
    creator = relationship("User")


class SocialPost(Base):
    """Historical social media posts for personas."""

    __tablename__ = "social_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="SET NULL"), nullable=True)

    # Post info
    platform = Column(String(50), nullable=False)  # linkedin, x, facebook, other
    content = Column(Text, nullable=False)

    # Platform metadata
    external_post_id = Column(String(255))  # ID from the platform
    post_url = Column(Text)
    posted_at = Column(DateTime(timezone=True))

    # Engagement metrics (optional)
    likes = Column(Integer)
    comments = Column(Integer)
    shares = Column(Integer)
    impressions = Column(Integer)

    # Media attachments
    media_urls = Column(JSONB, default=[])
    screenshot_s3_key = Column(String(1000))  # For LinkedIn screenshots

    # Metadata
    is_original = Column(Integer, default=1)  # 1 = original post, 0 = repost/share
    hashtags = Column(JSONB, default=[])
    mentions = Column(JSONB, default=[])
    extra_data = Column(JSONB, default={})

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    persona = relationship("Persona", back_populates="social_posts")
    creator = relationship("User")


class AudioRecording(Base):
    """Audio recordings with transcripts (Otter AI imports, Zoom recordings, etc.)."""

    __tablename__ = "audio_recordings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # File info
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    s3_key = Column(String(1000), nullable=False, unique=True)
    s3_bucket = Column(String(255), nullable=False, default="mv-brain")
    file_size_bytes = Column(BigInteger)
    duration_seconds = Column(Numeric(10, 2))
    format = Column(String(20))  # mp3, wav, m4a, etc.

    # Recording metadata
    title = Column(String(500))
    recording_date = Column(Date)
    speakers = Column(JSONB, default=[])  # List of speaker names
    keywords = Column(JSONB, default=[])  # Otter AI keywords
    summary = Column(Text)

    # Persona association
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="SET NULL"), nullable=True)

    # Source info
    source = Column(String(50), default="otter_ai")  # otter_ai, manual, zoom, etc.
    source_url = Column(Text)

    # Processing status
    status = Column(String(50), default="uploaded")

    # Metadata
    extra_data = Column("metadata", JSONB, default={})
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    persona = relationship("Persona")
    uploader = relationship("User")
    segments = relationship("AudioSegment", back_populates="audio", cascade="all, delete-orphan")


class AudioSegment(Base):
    """Timestamped segments of audio transcripts."""

    __tablename__ = "audio_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_id = Column(UUID(as_uuid=True), ForeignKey("audio_recordings.id", ondelete="CASCADE"), nullable=False)

    # Timing
    segment_index = Column(Integer, nullable=False)
    start_time = Column(Numeric(10, 3), nullable=False)  # seconds
    end_time = Column(Numeric(10, 3), nullable=False)

    # Content
    text = Column(Text, nullable=False)
    speaker = Column(String(100))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    audio = relationship("AudioRecording", back_populates="segments")


class VideoFrame(Base):
    """Individual frames extracted from videos for AI analysis."""

    __tablename__ = "video_frames"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    frame_number = Column(Integer, nullable=False)  # Sequential frame number
    timestamp_seconds = Column(Numeric(10, 3), nullable=False)  # Time in video when frame was captured
    s3_key = Column(String(1000), nullable=False, unique=True)  # S3 path to frame image
    file_size_bytes = Column(BigInteger)
    image_format = Column(String(10), default="png")  # png, jpg, etc
    width = Column(Integer)  # Image dimensions
    height = Column(Integer)
    extraction_method = Column(String(50), default="ffmpeg")  # Tool used to extract frame
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="frames")
    analysis = relationship("FrameAnalysis", back_populates="frame", cascade="all, delete-orphan")


class FrameAnalysis(Base):
    """AI analysis results for video frames - who is doing what."""

    __tablename__ = "frame_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    frame_id = Column(UUID(as_uuid=True), ForeignKey("video_frames.id", ondelete="CASCADE"), nullable=False)

    # AI provider info
    ai_provider = Column(String(50), default="openai")  # openai, aws_rekognition, etc
    ai_model = Column(String(100), default="gpt-4o")  # Specific model used
    analysis_version = Column(String(20), default="1.0")  # Schema version for analysis format

    # Structured analysis data
    people_detected = Column(JSONB, default=[])  # List of people detected with descriptions
    actions_detected = Column(JSONB, default=[])  # List of actions/activities observed
    objects_detected = Column(JSONB, default=[])  # List of notable objects in frame
    setting_description = Column(Text)  # Description of environment/location

    # Raw AI response
    raw_analysis = Column(Text)  # Full AI response text
    confidence_score = Column(Float)  # Overall confidence in analysis (0-1)

    # Processing metadata
    processing_time_ms = Column(Integer)  # Time taken for AI analysis
    tokens_used = Column(Integer)  # API tokens consumed
    cost_cents = Column(Integer)  # Estimated cost in cents

    # Quality/status
    status = Column(String(50), default="completed")  # completed, error, pending
    error_message = Column(Text)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    frame = relationship("VideoFrame", back_populates="analysis")


class BackupCode(Base):
    """Two-factor authentication backup codes for account recovery."""

    __tablename__ = "backup_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code_hash = Column(String(255), nullable=False)  # SHA-256 hash of the backup code
    is_used = Column(Integer, default=0)  # 1 = already used, 0 = available
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="backup_codes")


class PasswordResetToken(Base):
    """Password reset tokens for secure password recovery."""

    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)  # SHA-256 hash of the reset token
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Integer, default=0)  # 1 = already used, 0 = available
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")


class ExternalContent(Base):
    """External content: articles, web clips, PDFs, external videos."""

    __tablename__ = "external_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Content identification
    title = Column(String(500), nullable=False)
    content_type = Column(String(50), nullable=False)  # article, web_clip, pdf, external_video, other
    description = Column(Text)

    # Source information
    source_url = Column(Text)  # Original URL if fetched from web
    original_filename = Column(String(500))  # If uploaded as file

    # File storage (optional - for uploaded files)
    s3_key = Column(String(1000))  # S3 path if file was uploaded/cached
    s3_bucket = Column(String(255), default="mv-brain")
    file_size_bytes = Column(BigInteger)
    file_format = Column(String(20))  # pdf, html, mp4, etc.

    # Content analysis
    content_text = Column(Text)  # Extracted/parsed text content
    content_summary = Column(Text)  # AI-generated summary
    word_count = Column(Integer)

    # For video/audio content
    duration_seconds = Column(Numeric(10, 2))
    thumbnail_s3_key = Column(String(1000))

    # Metadata
    content_date = Column(Date)  # Publication date or relevant date
    author = Column(String(255))
    tags = Column(JSONB, default=[])  # User-defined tags
    keywords = Column(JSONB, default=[])  # Auto-extracted keywords
    extra_data = Column(JSONB, default={})  # Flexible metadata

    # Status and processing
    status = Column(String(50), default="uploaded")  # uploaded, processed, transcribed, error
    processing_notes = Column(Text)

    # User and timestamps
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User")
    segments = relationship("ExternalContentSegment", back_populates="content", cascade="all, delete-orphan")


class ExternalContentSegment(Base):
    """Searchable segments of external content."""

    __tablename__ = "external_content_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey("external_content.id", ondelete="CASCADE"), nullable=False)

    # Segment identification
    segment_index = Column(Integer, nullable=False)
    section_title = Column(String(255))  # For articles: heading, For videos: chapter

    # Time-based (for video/audio) or position-based (for text)
    start_time = Column(Numeric(10, 3))  # For video/audio content
    end_time = Column(Numeric(10, 3))
    start_position = Column(Integer)  # For text content (character position)
    end_position = Column(Integer)

    # Content
    text = Column(Text, nullable=False)
    speaker = Column(String(100))  # For video/audio with multiple speakers
    confidence = Column(Numeric(5, 4))  # For transcribed content

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    content = relationship("ExternalContent", back_populates="segments")


# ============================================================================
# RAG (Retrieval-Augmented Generation) Models
# ============================================================================

class CorpusSummary(Base):
    """Global knowledge base metadata and statistics."""
    __tablename__ = "corpus_summary"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # Corpus metadata
    title = Column(String(500), nullable=False, default="Internal Platform Knowledge Base")
    description = Column(Text)

    # Statistics (updated by triggers)
    total_documents = Column(Integer, default=0)
    total_sections = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Version tracking
    version = Column(Integer, default=1)
    last_updated = Column(DateTime(timezone=True), server_default=text("NOW()"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))


class RAGDocument(Base):
    """Document-level summaries and metadata for RAG system."""
    __tablename__ = "rag_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # Polymorphic reference to source content
    source_type = Column(String(50), nullable=False)
    source_id = Column(UUID(as_uuid=True), nullable=False)

    # Document metadata
    title = Column(String(500), nullable=False)
    content_type = Column(String(50), nullable=False)
    author = Column(String(255))
    content_date = Column(Date)
    language = Column(String(10), default='en')

    # AI-generated summaries
    summary = Column(Text)
    summary_embedding = Column(ARRAY(Float))  # OpenAI text-embedding-3-small (1536 dims)

    # Content statistics
    word_count = Column(Integer)
    character_count = Column(Integer)
    section_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)

    # Processing metadata
    processing_status = Column(String(50), default='pending')
    embedding_model = Column(String(100), default='text-embedding-3-small')
    processed_at = Column(DateTime(timezone=True))
    processing_error = Column(Text)

    # Quality metrics
    content_quality_score = Column(Numeric(3,2))  # 0.00 to 1.00
    embedding_quality_score = Column(Numeric(3,2))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    # Relationships
    sections = relationship("RAGSection", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("RAGChunk", back_populates="document", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('source_type', 'source_id', name='rag_documents_source_unique'),
        CheckConstraint(
            source_type.in_(['video', 'audio', 'external_content', 'document', 'social_post']),
            name='rag_documents_source_type_check'
        ),
        CheckConstraint(
            processing_status.in_(['pending', 'processing', 'completed', 'error', 'updated']),
            name='rag_documents_status_check'
        ),
    )


class RAGSection(Base):
    """Section-level summaries and logical groupings within documents."""
    __tablename__ = "rag_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    document_id = Column(UUID(as_uuid=True), ForeignKey('rag_documents.id', ondelete='CASCADE'), nullable=False)

    # Polymorphic reference to source segment/section
    source_type = Column(String(50), nullable=False)
    source_id = Column(UUID(as_uuid=True))  # Can be NULL for logical sections

    # Section metadata
    section_index = Column(Integer, nullable=False)  # Order within document
    title = Column(String(500))
    section_type = Column(String(50))  # chapter, paragraph, speaker_turn, time_segment, etc.

    # Timing information (for audio/video content)
    start_time = Column(Numeric(10, 3))
    end_time = Column(Numeric(10, 3))
    duration_seconds = Column(Numeric(10, 3))

    # Position information (for text content)
    start_position = Column(Integer)
    end_position = Column(Integer)

    # Speaker information (for transcripts)
    speaker = Column(String(255))

    # Content
    content_text = Column(Text)
    summary = Column(Text)
    summary_embedding = Column(ARRAY(Float))  # Smaller embedding for section summaries (768 dims)

    # Content statistics
    word_count = Column(Integer)
    character_count = Column(Integer)
    chunk_count = Column(Integer, default=0)

    # Quality and confidence
    confidence = Column(Numeric(5,4))  # For transcribed content
    content_quality_score = Column(Numeric(3,2))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    # Relationships
    document = relationship("RAGDocument", back_populates="sections")
    chunks = relationship("RAGChunk", back_populates="section", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('document_id', 'section_index', name='rag_sections_document_section_unique'),
        CheckConstraint(
            source_type.in_([
                'transcript_segment', 'audio_segment', 'external_content_segment',
                'logical_section', 'document_section'
            ]),
            name='rag_sections_source_type_check'
        ),
    )


class RAGChunk(Base):
    """Searchable text chunks with embeddings (~400 tokens each)."""
    __tablename__ = "rag_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    document_id = Column(UUID(as_uuid=True), ForeignKey('rag_documents.id', ondelete='CASCADE'), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey('rag_sections.id', ondelete='CASCADE'))

    # Chunk metadata
    chunk_index = Column(Integer, nullable=False)  # Global order within document
    section_chunk_index = Column(Integer)  # Order within section

    # Content
    content_text = Column(Text, nullable=False)
    content_hash = Column(String(64))  # SHA-256 hash for deduplication

    # Token information
    token_count = Column(Integer, nullable=False)
    character_count = Column(Integer, nullable=False)

    # Embedding and search
    embedding = Column(ARRAY(Float), nullable=False)  # Must have embedding for RAG (1536 dims)
    embedding_model = Column(String(100), default='text-embedding-3-small')

    # Context for continuity
    context_before = Column(Text)  # Previous chunk text for smooth reading
    context_after = Column(Text)   # Next chunk text for continuity
    context_window_size = Column(Integer, default=0)  # Characters of overlap

    # Source tracking and provenance
    source_references = Column(JSONB, default='[]')  # Array of source segment references
    source_metadata = Column(JSONB, default='{}')    # Additional metadata from source

    # Timing/position (inherited from section)
    start_time = Column(Numeric(10, 3))
    end_time = Column(Numeric(10, 3))
    start_position = Column(Integer)
    end_position = Column(Integer)

    # Quality and relevance scores
    content_quality_score = Column(Numeric(3,2))
    embedding_quality_score = Column(Numeric(3,2))
    information_density = Column(Numeric(3,2))  # How much info per token

    # Processing metadata
    processed_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    processing_version = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    # Relationships
    document = relationship("RAGDocument", back_populates="chunks")
    section = relationship("RAGSection", back_populates="chunks")

    # Constraints
    __table_args__ = (
        UniqueConstraint('document_id', 'chunk_index', name='rag_chunks_document_chunk_unique'),
        CheckConstraint('token_count > 0', name='rag_chunks_token_count_positive'),
    )


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
