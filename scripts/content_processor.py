#!/usr/bin/env python3
"""
Content Processor for RAG Knowledge Hierarchy

Processes existing content (videos, audio, documents, external content, social posts)
into the RAG (Retrieval-Augmented Generation) knowledge hierarchy:
- Generate document summaries using Claude Haiku (cost-effective)
- Split into sections preserving speaker turns and timing
- Chunk into ~400 token pieces with context windows
- Generate embeddings using EmbeddingService
- Populate RAG database tables

Author: Claude Sonnet 4 (Prompt 17 Implementation)
Date: 2026-01-06
"""

import os
import sys
import json
import hashlib
import logging
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from tqdm import tqdm

# Add paths for imports
sys.path.append('/Users/josephs./internal-platform/web')
sys.path.append('/Users/josephs./internal-platform')
sys.path.append('/Users/josephs./internal-platform/scripts')

# Local imports
from scripts.db import (
    DatabaseSession, RAGDocument, RAGSection, RAGChunk, CorpusSummary,
    Video, Transcript, TranscriptSegment, AudioRecording, AudioSegment,
    ExternalContent, ExternalContentSegment, Document, SocialPost
)
from scripts.embedding_service import get_embedding_service, EmbeddingService
from scripts.config_loader import get_config
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text, and_, or_
import anthropic


# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

# Processing constants
TOKEN_TARGET = 400  # Target tokens per chunk
TOKEN_MAX = 350     # Conservative max to avoid API limits
CHUNK_OVERLAP = 100  # Characters of context overlap
BATCH_SIZE = 50     # Documents per batch
EMBEDDING_BATCH_SIZE = 75  # Chunks per embedding batch

# Content type mapping
SOURCE_TYPE_MAPPING = {
    'video': {
        'model': Video,
        'segment_model': TranscriptSegment,
        'segment_fk': 'video_id',
        'rag_source_type': 'video'
    },
    'audio': {
        'model': AudioRecording,
        'segment_model': AudioSegment,
        'segment_fk': 'recording_id',
        'rag_source_type': 'audio'
    },
    'external_content': {
        'model': ExternalContent,
        'segment_model': ExternalContentSegment,
        'segment_fk': 'content_id',
        'rag_source_type': 'external_content'
    },
    'document': {
        'model': Document,
        'segment_model': None,
        'segment_fk': None,
        'rag_source_type': 'document'
    },
    'social_post': {
        'model': SocialPost,
        'segment_model': None,
        'segment_fk': None,
        'rag_source_type': 'social_post'
    }
}

# Status constants
class ProcessingStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    UPDATED = "updated"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ContentItem:
    """Represents a source content item to be processed."""
    source_type: str
    source_id: str
    title: str
    content_type: str
    author: Optional[str] = None
    content_date: Optional[datetime] = None
    content_text: Optional[str] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SectionData:
    """Represents a section within a document."""
    section_index: int
    title: Optional[str]
    section_type: str
    content_text: str
    speaker: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    confidence: Optional[float] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None


@dataclass
class ChunkData:
    """Represents a chunk within a section."""
    chunk_index: int
    section_chunk_index: int
    content_text: str
    token_count: int
    character_count: int
    content_hash: str
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None


@dataclass
class ProcessingStats:
    """Track processing statistics."""
    documents_processed: int = 0
    documents_failed: int = 0
    sections_created: int = 0
    chunks_created: int = 0
    embeddings_generated: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    start_time: datetime = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.utcnow()


# ============================================================================
# CONTENT PROCESSOR
# ============================================================================

class ContentProcessor:
    """Main content processor for RAG knowledge hierarchy."""

    def __init__(self, checkpoint_dir: str = "/tmp/rag_checkpoints"):
        """Initialize the content processor."""
        self.checkpoint_dir = checkpoint_dir
        self.stats = ProcessingStats()
        self.embedding_service = None
        self.anthropic_client = None

        # Create checkpoint directory
        os.makedirs(checkpoint_dir, exist_ok=True)

        # Setup logging
        self.logger = self._setup_logging()

        # Initialize services
        self._init_services()

        self.logger.info("ContentProcessor initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('content_processor')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # File handler
            log_file = os.path.join(self.checkpoint_dir, 'content_processor.log')
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def _init_services(self):
        """Initialize external services."""
        try:
            # Initialize embedding service
            self.embedding_service = get_embedding_service()
            self.logger.info("Embedding service initialized")

            # Initialize Anthropic client for Claude Haiku summaries
            config = get_config()
            api_key = config.secrets.get("anthropic", {}).get("api_key")
            if not api_key:
                api_key = config.credentials.get("apis", {}).get("anthropic", {}).get("api_key")

            if api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                self.logger.info("Anthropic client initialized")
            else:
                self.logger.warning("Anthropic API key not found - summaries will be skipped")

        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using simple heuristic."""
        return max(1, len(text) // 4)  # Rough approximation: 4 chars per token

    def _compute_content_hash(self, text: str) -> str:
        """Compute SHA-256 hash of content for deduplication."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _calculate_quality_score(self, text: str, source_type: str, confidence: Optional[float] = None) -> float:
        """Calculate content quality score (0.0-1.0)."""
        score = 0.0

        # Minimum length check
        if len(text) < 100:
            return 0.1  # Too short

        # Base score
        score = 0.7

        # Confidence bonus for transcribed content
        if confidence and source_type in ['video', 'audio']:
            score += confidence * 0.2

        # Whitespace quality check
        whitespace_ratio = sum(1 for c in text if c.isspace()) / len(text)
        if whitespace_ratio > 0.5:
            score -= 0.3

        # Length penalty for extremely long content
        if len(text) > 50000:
            score -= 0.1

        return min(1.0, max(0.0, score))

    def _save_checkpoint(self, checkpoint_data: Dict[str, Any]):
        """Save processing checkpoint."""
        checkpoint_file = os.path.join(self.checkpoint_dir, 'processing_checkpoint.json')
        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
            self.logger.debug(f"Checkpoint saved: {checkpoint_data.get('processed_count', 0)} documents")
        except Exception as e:
            self.logger.warning(f"Failed to save checkpoint: {e}")

    def _load_checkpoint(self) -> Dict[str, Any]:
        """Load processing checkpoint."""
        checkpoint_file = os.path.join(self.checkpoint_dir, 'processing_checkpoint.json')
        try:
            if os.path.exists(checkpoint_file):
                with open(checkpoint_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load checkpoint: {e}")
        return {}

    # ========================================================================
    # CONTENT ITERATION
    # ========================================================================

    def _get_content_items(self, content_type: str, limit: Optional[int] = None,
                          since: Optional[datetime] = None) -> List[ContentItem]:
        """Get content items of specified type for processing."""
        items = []

        try:
            with DatabaseSession() as session:
                # Get model configuration
                config = SOURCE_TYPE_MAPPING.get(content_type)
                if not config:
                    self.logger.error(f"Unknown content type: {content_type}")
                    return items

                model_class = config['model']

                # Base query
                query = session.query(model_class)

                # Filter by date if specified
                if since:
                    if hasattr(model_class, 'updated_at'):
                        query = query.filter(model_class.updated_at >= since)
                    elif hasattr(model_class, 'created_at'):
                        query = query.filter(model_class.created_at >= since)

                # Exclude already processed items
                existing_docs = session.query(RAGDocument.source_id).filter(
                    RAGDocument.source_type == config['rag_source_type']
                )
                query = query.filter(~model_class.id.in_(existing_docs))

                # Apply limit
                if limit:
                    query = query.limit(limit)

                # Execute query
                records = query.all()

                # Convert to ContentItem objects
                for record in records:
                    item = self._convert_to_content_item(record, content_type)
                    if item:
                        items.append(item)

                self.logger.info(f"Found {len(items)} {content_type} items to process")

        except Exception as e:
            self.logger.error(f"Failed to get {content_type} items: {e}")

        return items

    def _convert_to_content_item(self, record, content_type: str) -> Optional[ContentItem]:
        """Convert database record to ContentItem."""
        try:
            if content_type == 'video':
                return ContentItem(
                    source_type='video',
                    source_id=str(record.id),
                    title=record.filename or f"Video {record.id}",
                    content_type='video',
                    author=record.speaker,
                    content_date=record.event_date,
                    metadata={
                        'event_name': record.event_name,
                        'duration_seconds': float(record.duration_seconds or 0),
                        'description': record.description
                    }
                )

            elif content_type == 'audio':
                return ContentItem(
                    source_type='audio',
                    source_id=str(record.id),
                    title=record.title or record.filename or f"Audio {record.id}",
                    content_type='audio',
                    author=record.speakers[0] if record.speakers else None,
                    content_date=record.recording_date,
                    metadata={
                        'speakers': record.speakers or [],
                        'duration_seconds': float(record.duration_seconds or 0),
                        'source': record.source,
                        'keywords': record.keywords or []
                    }
                )

            elif content_type == 'external_content':
                return ContentItem(
                    source_type='external_content',
                    source_id=str(record.id),
                    title=record.title,
                    content_type=record.content_type,
                    author=record.author,
                    content_date=record.content_date,
                    content_text=record.content_text,
                    word_count=record.word_count,
                    character_count=len(record.content_text or ""),
                    metadata={
                        'description': record.description,
                        'source_url': record.source_url,
                        'tags': record.tags or [],
                        'keywords': record.keywords or []
                    }
                )

            elif content_type == 'document':
                return ContentItem(
                    source_type='document',
                    source_id=str(record.id),
                    title=record.title,
                    content_type=record.doc_type,
                    content_text=record.content_text,
                    word_count=record.word_count,
                    character_count=len(record.content_text or ""),
                    content_date=record.document_date,
                    metadata={
                        'persona_id': str(record.persona_id) if record.persona_id else None,
                        'source_filename': record.source_filename,
                        'duration_seconds': float(record.duration_seconds or 0),
                        'tags': record.tags or []
                    }
                )

            elif content_type == 'social_post':
                return ContentItem(
                    source_type='social_post',
                    source_id=str(record.id),
                    title=f"{record.platform} post",
                    content_type='social_post',
                    content_text=record.content,
                    word_count=len(record.content.split()) if record.content else 0,
                    character_count=len(record.content or ""),
                    content_date=record.posted_at,
                    metadata={
                        'platform': record.platform,
                        'persona_id': str(record.persona_id) if record.persona_id else None,
                        'hashtags': record.hashtags or [],
                        'mentions': record.mentions or [],
                        'engagement': {
                            'likes': record.likes or 0,
                            'comments': record.comments or 0,
                            'shares': record.shares or 0
                        }
                    }
                )

        except Exception as e:
            self.logger.warning(f"Failed to convert {content_type} record {record.id}: {e}")

        return None

    def get_all_content_items(self, limit: Optional[int] = None,
                             since: Optional[datetime] = None) -> List[ContentItem]:
        """Get all content items from all source types."""
        all_items = []

        for content_type in SOURCE_TYPE_MAPPING.keys():
            items = self._get_content_items(content_type, limit, since)
            all_items.extend(items)

        self.logger.info(f"Found {len(all_items)} total items across all content types")
        return all_items

    # ========================================================================
    # SECTION PROCESSING
    # ========================================================================

    def _get_segments_for_content(self, content_item: ContentItem) -> List[Dict[str, Any]]:
        """Get existing segments for content item (video/audio/external only)."""
        segments = []

        try:
            with DatabaseSession() as session:
                config = SOURCE_TYPE_MAPPING.get(content_item.source_type)
                if not config or not config['segment_model']:
                    return segments

                segment_model = config['segment_model']
                fk_field = config['segment_fk']

                # Build query dynamically
                query = session.query(segment_model)
                query = query.filter(getattr(segment_model, fk_field) == content_item.source_id)
                query = query.order_by(segment_model.segment_index)

                records = query.all()

                for record in records:
                    segment_data = {
                        'segment_index': record.segment_index,
                        'text': record.text,
                        'start_time': float(record.start_time) if hasattr(record, 'start_time') and record.start_time else None,
                        'end_time': float(record.end_time) if hasattr(record, 'end_time') and record.end_time else None,
                        'speaker': getattr(record, 'speaker', None),
                        'confidence': float(record.confidence) if hasattr(record, 'confidence') and record.confidence else None,
                        'source_id': str(record.id),
                        'source_type': f"{content_item.source_type}_segment"
                    }

                    # Handle position-based segments (external content)
                    if hasattr(record, 'start_position'):
                        segment_data['start_position'] = record.start_position
                        segment_data['end_position'] = record.end_position

                    # Handle section titles
                    if hasattr(record, 'section_title'):
                        segment_data['section_title'] = record.section_title

                    segments.append(segment_data)

                self.logger.debug(f"Found {len(segments)} segments for {content_item.source_type} {content_item.source_id}")

        except Exception as e:
            self.logger.error(f"Failed to get segments for {content_item.source_type} {content_item.source_id}: {e}")

        return segments

    def create_sections_from_content(self, content_item: ContentItem) -> List[SectionData]:
        """Create sections from content item using intelligent splitting."""
        sections = []

        try:
            if content_item.source_type in ['video', 'audio', 'external_content']:
                # Use existing segments with speaker/timing preservation
                sections = self._create_sections_from_segments(content_item)
            else:
                # Use text-based logical splitting for documents and social posts
                sections = self._create_sections_from_text(content_item)

            self.logger.debug(f"Created {len(sections)} sections for {content_item.title}")

        except Exception as e:
            self.logger.error(f"Failed to create sections for {content_item.title}: {e}")

        return sections

    def _create_sections_from_segments(self, content_item: ContentItem) -> List[SectionData]:
        """Create sections from existing segments, preserving speaker turns and timing."""
        sections = []
        segments = self._get_segments_for_content(content_item)

        if not segments:
            self.logger.warning(f"No segments found for {content_item.source_type} {content_item.source_id}")
            return sections

        # Group segments by speaker turns or time windows
        current_section = None
        section_index = 0

        for segment in segments:
            segment_text = (segment['text'] or "").strip()
            if not segment_text:
                continue

            # Check if we need to start a new section
            should_split = self._should_split_section(current_section, segment, content_item.source_type)

            if should_split or current_section is None:
                # Save previous section
                if current_section:
                    sections.append(self._finalize_section(current_section, section_index))
                    section_index += 1

                # Start new section
                current_section = {
                    'text_parts': [segment_text],
                    'speaker': segment['speaker'],
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'start_position': segment.get('start_position'),
                    'end_position': segment.get('end_position'),
                    'source_segments': [segment],
                    'confidence_scores': [segment['confidence']] if segment['confidence'] else [],
                    'section_title': segment.get('section_title')
                }
            else:
                # Extend current section
                current_section['text_parts'].append(segment_text)
                current_section['end_time'] = segment['end_time']
                current_section['end_position'] = segment.get('end_position')
                current_section['source_segments'].append(segment)
                if segment['confidence']:
                    current_section['confidence_scores'].append(segment['confidence'])

        # Don't forget the last section
        if current_section:
            sections.append(self._finalize_section(current_section, section_index))

        return sections

    def _should_split_section(self, current_section: Optional[Dict], segment: Dict, source_type: str) -> bool:
        """Determine if we should split into a new section."""
        if not current_section:
            return True

        # Split on speaker changes (for video/audio)
        if source_type in ['video', 'audio'] and segment['speaker'] != current_section['speaker']:
            return True

        # Split on section title changes (for external content)
        if (source_type == 'external_content' and
            segment.get('section_title') and
            segment.get('section_title') != current_section.get('section_title')):
            return True

        # Split on time gaps > 5 minutes (for video/audio)
        if (source_type in ['video', 'audio'] and
            segment['start_time'] and current_section['end_time']):
            time_gap = segment['start_time'] - current_section['end_time']
            if time_gap > 300:  # 5 minutes
                return True

        # Split if section getting too long (>2000 characters)
        current_text = ' '.join(current_section['text_parts'])
        if len(current_text) > 2000:
            return True

        return False

    def _finalize_section(self, section_data: Dict, section_index: int) -> SectionData:
        """Convert section data dict to SectionData object."""
        # Combine all text parts
        content_text = ' '.join(section_data['text_parts'])

        # Calculate average confidence
        confidence = None
        if section_data['confidence_scores']:
            confidence = sum(section_data['confidence_scores']) / len(section_data['confidence_scores'])

        # Determine section type
        section_type = "logical_section"
        if section_data['speaker']:
            section_type = "speaker_turn"
        elif section_data.get('section_title'):
            section_type = "titled_section"

        # Create source references for RAG chunks
        source_segments = section_data['source_segments']
        source_type = f"{source_segments[0]['source_type']}" if source_segments else "logical_section"
        source_id = source_segments[0]['source_id'] if len(source_segments) == 1 else None

        return SectionData(
            section_index=section_index,
            title=section_data.get('section_title'),
            section_type=section_type,
            content_text=content_text,
            speaker=section_data['speaker'],
            start_time=section_data['start_time'],
            end_time=section_data['end_time'],
            start_position=section_data.get('start_position'),
            end_position=section_data.get('end_position'),
            source_type=source_type,
            source_id=source_id,
            confidence=confidence,
            word_count=len(content_text.split()),
            character_count=len(content_text)
        )

    def _create_sections_from_text(self, content_item: ContentItem) -> List[SectionData]:
        """Create sections from text content using logical boundaries."""
        sections = []

        if not content_item.content_text:
            return sections

        text = content_item.content_text.strip()
        if not text:
            return sections

        # For social posts, treat as single section
        if content_item.source_type == 'social_post':
            sections.append(SectionData(
                section_index=0,
                title=None,
                section_type="social_post",
                content_text=text,
                word_count=len(text.split()),
                character_count=len(text),
                source_type="logical_section"
            ))
            return sections

        # For documents, split by logical boundaries
        return self._split_text_by_boundaries(text, content_item)

    def _split_text_by_boundaries(self, text: str, content_item: ContentItem) -> List[SectionData]:
        """Split text by logical boundaries (paragraphs, headers)."""
        sections = []

        # Try to split by double newlines (paragraph breaks)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        if not paragraphs:
            # Fallback: split by single newlines
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

        current_section_text = ""
        section_index = 0

        for paragraph in paragraphs:
            # Check if adding this paragraph would make section too long
            potential_text = current_section_text + "\n\n" + paragraph if current_section_text else paragraph

            if len(potential_text) > 1200 and current_section_text:
                # Create section with current content
                sections.append(SectionData(
                    section_index=section_index,
                    title=self._extract_section_title(current_section_text),
                    section_type="document_section",
                    content_text=current_section_text,
                    word_count=len(current_section_text.split()),
                    character_count=len(current_section_text),
                    source_type="logical_section"
                ))
                section_index += 1
                current_section_text = paragraph
            else:
                current_section_text = potential_text

        # Add final section
        if current_section_text:
            sections.append(SectionData(
                section_index=section_index,
                title=self._extract_section_title(current_section_text),
                section_type="document_section",
                content_text=current_section_text,
                word_count=len(current_section_text.split()),
                character_count=len(current_section_text),
                source_type="logical_section"
            ))

        return sections

    def _extract_section_title(self, text: str) -> Optional[str]:
        """Try to extract a title from the first line of text."""
        lines = text.split('\n')
        first_line = lines[0].strip()

        # If first line is short and looks like a title
        if len(first_line) < 100 and len(lines) > 1:
            # Check for title indicators
            if (first_line.isupper() or
                first_line.startswith('#') or
                first_line.endswith(':') or
                len(first_line.split()) <= 8):
                return first_line

        return None

    # ========================================================================
    # CHUNKING PROCESSING
    # ========================================================================

    def create_chunks_from_sections(self, sections: List[SectionData], content_item: ContentItem) -> List[ChunkData]:
        """Create chunks from sections using intelligent token-based splitting."""
        all_chunks = []
        global_chunk_index = 0

        for section in sections:
            section_chunks = self._create_chunks_from_section(section, global_chunk_index)
            for chunk in section_chunks:
                all_chunks.append(chunk)
                global_chunk_index += 1

        # Add context windows between chunks
        self._add_context_windows(all_chunks)

        self.logger.debug(f"Created {len(all_chunks)} chunks for {content_item.title}")
        return all_chunks

    def _create_chunks_from_section(self, section: SectionData, start_chunk_index: int) -> List[ChunkData]:
        """Split a section into ~400 token chunks on sentence boundaries."""
        chunks = []

        if not section.content_text or not section.content_text.strip():
            return chunks

        text = section.content_text.strip()
        estimated_tokens = self._estimate_tokens(text)

        # If section is already small enough, use as single chunk
        if estimated_tokens <= TOKEN_MAX:
            chunk = ChunkData(
                chunk_index=start_chunk_index,
                section_chunk_index=0,
                content_text=text,
                token_count=estimated_tokens,
                character_count=len(text),
                content_hash=self._compute_content_hash(text),
                start_time=section.start_time,
                end_time=section.end_time,
                start_position=section.start_position,
                end_position=section.end_position
            )
            chunks.append(chunk)
            return chunks

        # Split into multiple chunks
        return self._split_text_into_chunks(text, section, start_chunk_index)

    def _split_text_into_chunks(self, text: str, section: SectionData, start_index: int) -> List[ChunkData]:
        """Split text into chunks on sentence boundaries."""
        chunks = []

        # Split text into sentences
        sentences = self._split_into_sentences(text)
        if not sentences:
            return chunks

        current_chunk_text = ""
        chunk_sentences = []
        section_chunk_index = 0

        for sentence in sentences:
            # Check if adding this sentence would exceed token limit
            potential_text = current_chunk_text + " " + sentence if current_chunk_text else sentence
            potential_tokens = self._estimate_tokens(potential_text)

            if potential_tokens <= TOKEN_MAX:
                # Add sentence to current chunk
                current_chunk_text = potential_text
                chunk_sentences.append(sentence)
            else:
                # Create chunk with current content (if any)
                if current_chunk_text:
                    chunk = self._create_chunk_from_text(
                        current_chunk_text, chunk_sentences,
                        start_index + section_chunk_index, section_chunk_index, section
                    )
                    chunks.append(chunk)
                    section_chunk_index += 1

                # Start new chunk with current sentence
                current_chunk_text = sentence
                chunk_sentences = [sentence]

                # Handle edge case: single sentence too long
                if self._estimate_tokens(sentence) > TOKEN_MAX:
                    # Truncate sentence to fit token limit
                    truncated = self._truncate_to_token_limit(sentence)
                    chunk = self._create_chunk_from_text(
                        truncated, [truncated],
                        start_index + section_chunk_index, section_chunk_index, section
                    )
                    chunks.append(chunk)
                    section_chunk_index += 1
                    current_chunk_text = ""
                    chunk_sentences = []

        # Don't forget the last chunk
        if current_chunk_text:
            chunk = self._create_chunk_from_text(
                current_chunk_text, chunk_sentences,
                start_index + section_chunk_index, section_chunk_index, section
            )
            chunks.append(chunk)

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using simple heuristics."""
        # Simple sentence splitting on period, exclamation, question mark
        # followed by space and capital letter or end of string
        import re

        # Split on sentence boundaries
        sentence_endings = re.compile(r'[.!?]+\s+(?=[A-Z])|[.!?]+$')
        sentences = sentence_endings.split(text)

        # Clean up and filter empty sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                cleaned_sentences.append(sentence)

        # If no sentence boundaries found, split by length
        if len(cleaned_sentences) <= 1:
            return self._split_by_length(text, 800)  # ~200 tokens per piece

        return cleaned_sentences

    def _split_by_length(self, text: str, max_chars: int) -> List[str]:
        """Split text by character length, trying to break on word boundaries."""
        pieces = []
        start = 0

        while start < len(text):
            end = start + max_chars

            if end >= len(text):
                pieces.append(text[start:].strip())
                break

            # Try to break on word boundary
            break_point = text.rfind(' ', start, end)
            if break_point > start:
                pieces.append(text[start:break_point].strip())
                start = break_point + 1
            else:
                # No word boundary found, hard break
                pieces.append(text[start:end].strip())
                start = end

        return [p for p in pieces if p]

    def _truncate_to_token_limit(self, text: str) -> str:
        """Truncate text to fit within token limit."""
        target_chars = TOKEN_MAX * 4  # Conservative approximation
        if len(text) <= target_chars:
            return text

        # Truncate and try to end on word boundary
        truncated = text[:target_chars]
        last_space = truncated.rfind(' ')
        if last_space > target_chars * 0.8:  # If word boundary is not too far back
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."

    def _create_chunk_from_text(self, text: str, sentences: List[str],
                               chunk_index: int, section_chunk_index: int,
                               section: SectionData) -> ChunkData:
        """Create a ChunkData object from text and metadata."""

        # Calculate timing for chunk (interpolate within section)
        start_time = None
        end_time = None

        if section.start_time is not None and section.end_time is not None:
            section_duration = section.end_time - section.start_time
            if section_duration > 0:
                # Estimate chunk position within section
                chunk_ratio_start = len(' '.join(sentences[:1])) / len(section.content_text) if sentences else 0
                chunk_ratio_end = len(text) / len(section.content_text)

                start_time = section.start_time + (chunk_ratio_start * section_duration)
                end_time = section.start_time + (chunk_ratio_end * section_duration)

        # Calculate position for text-based content
        start_position = None
        end_position = None

        if section.start_position is not None:
            # Find chunk position within section text
            chunk_start_in_section = section.content_text.find(text)
            if chunk_start_in_section >= 0:
                start_position = section.start_position + chunk_start_in_section
                end_position = start_position + len(text)

        return ChunkData(
            chunk_index=chunk_index,
            section_chunk_index=section_chunk_index,
            content_text=text,
            token_count=self._estimate_tokens(text),
            character_count=len(text),
            content_hash=self._compute_content_hash(text),
            start_time=start_time,
            end_time=end_time,
            start_position=start_position,
            end_position=end_position
        )

    def _add_context_windows(self, chunks: List[ChunkData]):
        """Add context windows (before/after text) to chunks for continuity."""
        for i, chunk in enumerate(chunks):
            # Add context before
            if i > 0:
                prev_chunk = chunks[i-1]
                context_text = prev_chunk.content_text[-CHUNK_OVERLAP:] if len(prev_chunk.content_text) > CHUNK_OVERLAP else prev_chunk.content_text
                chunk.context_before = context_text.strip()

            # Add context after
            if i < len(chunks) - 1:
                next_chunk = chunks[i+1]
                context_text = next_chunk.content_text[:CHUNK_OVERLAP] if len(next_chunk.content_text) > CHUNK_OVERLAP else next_chunk.content_text
                chunk.context_after = context_text.strip()

    # ========================================================================
    # SUMMARY GENERATION
    # ========================================================================

    def generate_section_summaries(self, sections: List[SectionData]) -> List[SectionData]:
        """Generate summaries for sections using Claude Haiku (cost-effective)."""
        if not self.anthropic_client:
            self.logger.warning("Anthropic client not available - skipping summary generation")
            return sections

        sections_to_process = [s for s in sections if not hasattr(s, 'summary') or not s.summary]

        if not sections_to_process:
            self.logger.debug("All sections already have summaries")
            return sections

        self.logger.info(f"Generating summaries for {len(sections_to_process)} sections using Claude Haiku")

        # Process sections in small batches to avoid rate limits
        batch_size = 10
        for i in range(0, len(sections_to_process), batch_size):
            batch = sections_to_process[i:i + batch_size]

            for section in batch:
                try:
                    summary = self._generate_single_summary(section)
                    section.summary = summary
                    self.stats.total_cost += 0.00008  # Rough estimate for Claude Haiku
                    time.sleep(0.1)  # Small delay to be respectful to API

                except Exception as e:
                    self.logger.warning(f"Failed to generate summary for section {section.section_index}: {e}")
                    section.summary = self._generate_fallback_summary(section)

            # Small delay between batches
            if i + batch_size < len(sections_to_process):
                time.sleep(1)

        return sections

    def _generate_single_summary(self, section: SectionData) -> str:
        """Generate summary for a single section using Claude Haiku."""
        content = section.content_text.strip()

        if len(content) < 200:
            # For very short content, just return first sentence or truncated version
            sentences = content.split('.')
            return sentences[0] + '.' if sentences else content[:100] + '...'

        # Prepare system prompt
        system_prompt = (
            "You are a technical summarizer. Create a concise 1-2 sentence summary "
            "that captures the main point or key information. Be specific and factual."
        )

        # Add context based on section type
        if section.speaker:
            user_prompt = f"Summarize this speaker segment from {section.speaker}:\n\n{content}"
        elif section.section_type == "social_post":
            user_prompt = f"Summarize this social media post:\n\n{content}"
        else:
            user_prompt = f"Summarize this text content:\n\n{content}"

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-haiku-20241022",  # Latest Haiku model
                max_tokens=100,  # Keep summaries short
                temperature=0.3,  # Slightly creative but focused
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }]
            )

            summary = response.content[0].text.strip()

            # Ensure summary is reasonable length
            if len(summary) > 300:
                summary = summary[:297] + "..."

            return summary

        except Exception as e:
            self.logger.warning(f"Claude API error: {e}")
            raise

    def _generate_fallback_summary(self, section: SectionData) -> str:
        """Generate a simple fallback summary without AI."""
        content = section.content_text.strip()

        # Extract first sentence or first 100 characters
        sentences = content.split('.')
        if len(sentences) > 1 and len(sentences[0]) < 200:
            return sentences[0].strip() + '.'
        else:
            # Take first 150 characters and try to end on word boundary
            if len(content) <= 150:
                return content

            truncated = content[:150]
            last_space = truncated.rfind(' ')
            if last_space > 100:
                return truncated[:last_space] + "..."
            else:
                return truncated + "..."

    def generate_document_summary(self, content_item: ContentItem, sections: List[SectionData]) -> str:
        """Generate document-level summary from section summaries."""
        if not self.anthropic_client:
            # Fallback: combine section summaries
            section_summaries = [s.summary for s in sections if hasattr(s, 'summary') and s.summary]
            if section_summaries:
                combined = ' '.join(section_summaries[:3])  # First 3 section summaries
                return combined[:500] + "..." if len(combined) > 500 else combined
            else:
                return f"Document containing {len(sections)} sections from {content_item.source_type}"

        # Use section summaries to create document summary
        section_summaries = [s.summary for s in sections if hasattr(s, 'summary') and s.summary]

        if not section_summaries:
            return f"Document with {len(sections)} sections covering content from {content_item.source_type}"

        # Combine section summaries for document-level summary
        combined_summaries = '\n'.join(section_summaries)

        if len(combined_summaries) < 300:
            # If combined summaries are short, use as-is
            return combined_summaries

        try:
            system_prompt = (
                "You are a document summarizer. Create a comprehensive 2-3 sentence summary "
                "that captures the main themes and key points from the section summaries provided."
            )

            user_prompt = (
                f"Create a document summary from these section summaries:\n\n{combined_summaries}"
            )

            response = self.anthropic_client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=150,
                temperature=0.3,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }]
            )

            document_summary = response.content[0].text.strip()
            self.stats.total_cost += 0.00008  # Rough estimate

            return document_summary

        except Exception as e:
            self.logger.warning(f"Failed to generate document summary: {e}")
            # Fallback to first few section summaries
            return ' '.join(section_summaries[:3])

    # ========================================================================
    # EMBEDDING PROCESSING
    # ========================================================================

    def generate_embeddings_for_chunks(self, chunks: List[ChunkData]) -> List[ChunkData]:
        """Generate embeddings for chunks using batch processing."""
        if not self.embedding_service:
            self.logger.error("Embedding service not available")
            return chunks

        chunks_to_process = [c for c in chunks if not hasattr(c, 'embedding') or not c.embedding]

        if not chunks_to_process:
            self.logger.debug("All chunks already have embeddings")
            return chunks

        self.logger.info(f"Generating embeddings for {len(chunks_to_process)} chunks")

        # Process in batches for efficiency
        batch_size = EMBEDDING_BATCH_SIZE
        processed_count = 0

        for i in range(0, len(chunks_to_process), batch_size):
            batch = chunks_to_process[i:i + batch_size]
            self.logger.debug(f"Processing embedding batch {i//batch_size + 1}/{(len(chunks_to_process) + batch_size - 1)//batch_size}")

            try:
                # Extract texts for embedding
                batch_texts = [chunk.content_text for chunk in batch]

                # Generate embeddings using batch API
                pgvector_embeddings, result = self.embedding_service.embed_batch_for_pgvector(
                    batch_texts,
                    batch_size=batch_size,
                    metadata={
                        'request_type': 'content_processor_chunks',
                        'batch_index': i // batch_size
                    }
                )

                # Assign embeddings back to chunks
                for j, chunk in enumerate(batch):
                    if j < len(pgvector_embeddings) and pgvector_embeddings[j]:
                        chunk.embedding = pgvector_embeddings[j]
                        chunk.embedding_model = 'text-embedding-3-small'
                        processed_count += 1
                    else:
                        self.logger.warning(f"Failed to generate embedding for chunk {chunk.chunk_index}")
                        chunk.embedding = None  # Mark as failed

                # Update statistics
                if hasattr(result, 'total_cost'):
                    self.stats.total_cost += result.total_cost
                if hasattr(result, 'success_count'):
                    self.stats.embeddings_generated += result.success_count
                if hasattr(result, 'total_tokens'):
                    self.stats.total_tokens += result.total_tokens

                self.logger.debug(f"Successfully generated {result.success_count if hasattr(result, 'success_count') else len(batch)} embeddings")

            except Exception as e:
                self.logger.error(f"Failed to process embedding batch {i//batch_size + 1}: {e}")
                # Mark batch as failed
                for chunk in batch:
                    chunk.embedding = None

            # Small delay between batches to respect rate limits
            if i + batch_size < len(chunks_to_process):
                time.sleep(0.5)

        self.logger.info(f"Embedding generation complete: {processed_count}/{len(chunks_to_process)} successful")
        return chunks

    def generate_section_embeddings(self, sections: List[SectionData]) -> List[SectionData]:
        """Generate embeddings for section summaries (optional, for section-level search)."""
        if not self.embedding_service:
            return sections

        sections_with_summaries = [s for s in sections if hasattr(s, 'summary') and s.summary]
        sections_to_process = [s for s in sections_with_summaries if not hasattr(s, 'summary_embedding') or not s.summary_embedding]

        if not sections_to_process:
            return sections

        self.logger.info(f"Generating section embeddings for {len(sections_to_process)} sections")

        try:
            # Extract summaries for embedding
            summary_texts = [section.summary for section in sections_to_process]

            # Use smaller batch size for section embeddings
            batch_size = min(25, len(summary_texts))

            for i in range(0, len(sections_to_process), batch_size):
                batch = sections_to_process[i:i + batch_size]
                batch_summaries = summary_texts[i:i + batch_size]

                # Generate embeddings
                pgvector_embeddings, result = self.embedding_service.embed_batch_for_pgvector(
                    batch_summaries,
                    batch_size=batch_size,
                    metadata={'request_type': 'section_summaries'}
                )

                # Assign embeddings to sections
                for j, section in enumerate(batch):
                    if j < len(pgvector_embeddings) and pgvector_embeddings[j]:
                        section.summary_embedding = pgvector_embeddings[j]

                # Update cost tracking
                if hasattr(result, 'total_cost'):
                    self.stats.total_cost += result.total_cost

                time.sleep(0.3)  # Small delay

        except Exception as e:
            self.logger.warning(f"Failed to generate section embeddings: {e}")

        return sections

    def validate_embeddings(self, chunks: List[ChunkData]) -> Tuple[List[ChunkData], int]:
        """Validate that all chunks have valid embeddings."""
        valid_chunks = []
        failed_count = 0

        for chunk in chunks:
            if hasattr(chunk, 'embedding') and chunk.embedding:
                # Basic validation: check if embedding looks like pgvector format
                if isinstance(chunk.embedding, str) and '[' in chunk.embedding and ']' in chunk.embedding:
                    valid_chunks.append(chunk)
                else:
                    failed_count += 1
                    self.logger.warning(f"Invalid embedding format for chunk {chunk.chunk_index}")
            else:
                failed_count += 1
                self.logger.warning(f"Missing embedding for chunk {chunk.chunk_index}")

        if failed_count > 0:
            self.logger.warning(f"Validation failed for {failed_count} chunks")

        return valid_chunks, failed_count

    # ========================================================================
    # RAG DATABASE POPULATION
    # ========================================================================

    def process_single_content_item(self, content_item: ContentItem) -> bool:
        """Process a single content item through the entire pipeline."""
        try:
            self.logger.info(f"Processing {content_item.source_type}: {content_item.title}")

            # Step 1: Create sections
            sections = self.create_sections_from_content(content_item)
            if not sections:
                self.logger.warning(f"No sections created for {content_item.title}")
                return False

            # Step 2: Generate section summaries
            sections = self.generate_section_summaries(sections)

            # Step 3: Create chunks
            chunks = self.create_chunks_from_sections(sections, content_item)
            if not chunks:
                self.logger.warning(f"No chunks created for {content_item.title}")
                return False

            # Step 4: Generate embeddings
            chunks = self.generate_embeddings_for_chunks(chunks)

            # Step 5: Validate embeddings
            valid_chunks, failed_count = self.validate_embeddings(chunks)
            if failed_count > 0:
                self.logger.warning(f"{failed_count} chunks failed embedding validation")

            if not valid_chunks:
                self.logger.error(f"No valid chunks with embeddings for {content_item.title}")
                return False

            # Step 6: Generate document summary
            document_summary = self.generate_document_summary(content_item, sections)

            # Step 7: Save to database
            success = self._save_to_database(content_item, sections, valid_chunks, document_summary)

            if success:
                self.stats.documents_processed += 1
                self.stats.sections_created += len(sections)
                self.stats.chunks_created += len(valid_chunks)
                self.logger.info(f"Successfully processed {content_item.title}: {len(sections)} sections, {len(valid_chunks)} chunks")
            else:
                self.stats.documents_failed += 1

            return success

        except Exception as e:
            self.logger.error(f"Failed to process {content_item.title}: {e}")
            self.stats.documents_failed += 1
            return False

    def _save_to_database(self, content_item: ContentItem, sections: List[SectionData],
                         chunks: List[ChunkData], document_summary: str) -> bool:
        """Save processed content to RAG database with transaction safety."""
        try:
            with DatabaseSession() as session:
                # Check for existing document (duplicate prevention)
                existing_doc = session.query(RAGDocument).filter(
                    RAGDocument.source_type == content_item.source_type,
                    RAGDocument.source_id == content_item.source_id
                ).first()

                if existing_doc:
                    self.logger.info(f"Document already exists, skipping: {content_item.title}")
                    return True

                # Create RAG document
                rag_document = self._create_rag_document(content_item, document_summary, len(sections), len(chunks))
                session.add(rag_document)
                session.flush()  # Get document ID for foreign keys

                # Create RAG sections
                rag_sections = []
                for section in sections:
                    rag_section = self._create_rag_section(section, rag_document.id)
                    session.add(rag_section)
                    rag_sections.append(rag_section)

                session.flush()  # Get section IDs

                # Create RAG chunks
                for chunk in chunks:
                    # Find corresponding section
                    section_id = None
                    if chunk.section_chunk_index is not None:
                        # Calculate which section this chunk belongs to
                        section_idx = self._find_section_for_chunk(chunk, sections)
                        if section_idx < len(rag_sections):
                            section_id = rag_sections[section_idx].id

                    rag_chunk = self._create_rag_chunk(chunk, rag_document.id, section_id)
                    session.add(rag_chunk)

                # Commit transaction
                session.commit()
                self.logger.debug(f"Saved to database: {rag_document.id}")

                return True

        except IntegrityError as e:
            self.logger.warning(f"Integrity constraint violation (likely duplicate): {e}")
            return False
        except Exception as e:
            self.logger.error(f"Database error saving {content_item.title}: {e}")
            return False

    def _create_rag_document(self, content_item: ContentItem, summary: str,
                            section_count: int, chunk_count: int) -> RAGDocument:
        """Create RAGDocument from ContentItem."""
        # Calculate content quality score
        quality_score = self._calculate_quality_score(
            content_item.content_text or summary,
            content_item.source_type
        )

        return RAGDocument(
            source_type=content_item.source_type,
            source_id=content_item.source_id,
            title=content_item.title,
            content_type=content_item.content_type,
            author=content_item.author,
            content_date=content_item.content_date,
            language='en',  # Default to English
            summary=summary,
            word_count=content_item.word_count,
            character_count=content_item.character_count,
            section_count=section_count,
            chunk_count=chunk_count,
            processing_status=ProcessingStatus.COMPLETED,
            embedding_model='text-embedding-3-small',
            processed_at=datetime.utcnow(),
            content_quality_score=quality_score,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    def _create_rag_section(self, section: SectionData, document_id: str) -> RAGSection:
        """Create RAGSection from SectionData."""
        # Calculate duration if timing available
        duration = None
        if section.start_time is not None and section.end_time is not None:
            duration = section.end_time - section.start_time

        # Calculate content quality
        quality_score = self._calculate_quality_score(
            section.content_text,
            'section',
            section.confidence
        )

        rag_section = RAGSection(
            document_id=document_id,
            source_type=section.source_type or 'logical_section',
            source_id=section.source_id,
            section_index=section.section_index,
            title=section.title,
            section_type=section.section_type,
            start_time=section.start_time,
            end_time=section.end_time,
            duration_seconds=duration,
            start_position=section.start_position,
            end_position=section.end_position,
            speaker=section.speaker,
            content_text=section.content_text,
            summary=getattr(section, 'summary', None),
            word_count=section.word_count,
            character_count=section.character_count,
            chunk_count=0,  # Will be updated by triggers
            confidence=section.confidence,
            content_quality_score=quality_score,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Add section summary embedding if available
        if hasattr(section, 'summary_embedding') and section.summary_embedding:
            rag_section.summary_embedding = section.summary_embedding

        return rag_section

    def _create_rag_chunk(self, chunk: ChunkData, document_id: str, section_id: str = None) -> RAGChunk:
        """Create RAGChunk from ChunkData."""
        # Calculate quality scores
        quality_score = self._calculate_quality_score(chunk.content_text, 'chunk')

        # Simple embedding quality check
        embedding_quality = 1.0 if chunk.embedding else 0.0

        # Calculate information density (rough approximation)
        info_density = min(1.0, chunk.token_count / 400.0)  # Normalize to target size

        # Convert embedding string to array format for PostgreSQL
        embedding_array = self._convert_pgvector_to_array(chunk.embedding) if chunk.embedding else None

        if not embedding_array:
            raise ValueError(f"Invalid or missing embedding for chunk {chunk.chunk_index}")

        return RAGChunk(
            document_id=document_id,
            section_id=section_id,
            chunk_index=chunk.chunk_index,
            section_chunk_index=chunk.section_chunk_index,
            content_text=chunk.content_text,
            content_hash=chunk.content_hash,
            token_count=chunk.token_count,
            character_count=chunk.character_count,
            embedding=embedding_array,  # Convert to array for PostgreSQL
            embedding_model=getattr(chunk, 'embedding_model', 'text-embedding-3-small'),
            context_before=chunk.context_before,
            context_after=chunk.context_after,
            context_window_size=len(chunk.context_before or "") + len(chunk.context_after or ""),
            source_references='[]',  # TODO: Add actual source references
            source_metadata='{}',    # TODO: Add metadata
            start_time=chunk.start_time,
            end_time=chunk.end_time,
            start_position=chunk.start_position,
            end_position=chunk.end_position,
            content_quality_score=quality_score,
            embedding_quality_score=embedding_quality,
            information_density=info_density,
            processed_at=datetime.utcnow(),
            processing_version=1,
            created_at=datetime.utcnow()
        )

    def _find_section_for_chunk(self, chunk: ChunkData, sections: List[SectionData]) -> int:
        """Find which section a chunk belongs to based on timing or position."""
        # Simple approach: use chunk timing or position to find section
        for i, section in enumerate(sections):
            # Check timing overlap
            if (chunk.start_time is not None and section.start_time is not None and
                section.start_time <= chunk.start_time <= section.end_time):
                return i

            # Check position overlap
            if (chunk.start_position is not None and section.start_position is not None and
                section.start_position <= chunk.start_position <= section.end_position):
                return i

        # Fallback: estimate section based on chunk index
        chunks_per_section = max(1, len(sections))
        estimated_section = min(chunk.chunk_index // chunks_per_section, len(sections) - 1)
        return estimated_section

    def _convert_pgvector_to_array(self, pgvector_str: str) -> List[float]:
        """Convert pgvector string format to array for PostgreSQL storage."""
        if not pgvector_str:
            return None

        try:
            # Parse the string representation of the array
            if pgvector_str.startswith('[') and pgvector_str.endswith(']'):
                # Remove brackets and split by comma
                numbers_str = pgvector_str[1:-1]
                return [float(x.strip()) for x in numbers_str.split(',')]
            else:
                # Try to evaluate as Python literal
                return eval(pgvector_str)
        except Exception as e:
            self.logger.error(f"Failed to convert pgvector string: {pgvector_str[:100]}... Error: {e}")
            return None

    # ========================================================================
    # MAIN PROCESSING PIPELINE
    # ========================================================================

    def process_all_content(self, content_items: List[ContentItem], resume: bool = False) -> ProcessingStats:
        """Process all content items with checkpointing and error recovery."""
        if not content_items:
            self.logger.info("No content items to process")
            return self.stats

        # Load checkpoint if resuming
        checkpoint = {}
        start_index = 0

        if resume:
            checkpoint = self._load_checkpoint()
            start_index = checkpoint.get('last_processed_index', 0) + 1
            self.logger.info(f"Resuming from checkpoint: starting at item {start_index}")

        # Filter content items if resuming
        if start_index > 0:
            content_items = content_items[start_index:]

        self.logger.info(f"Processing {len(content_items)} content items")

        # Process items with progress tracking
        with tqdm(total=len(content_items), desc="Processing content") as pbar:
            for i, content_item in enumerate(content_items):
                actual_index = start_index + i

                try:
                    success = self.process_single_content_item(content_item)

                    if success:
                        pbar.set_postfix({
                            'success': self.stats.documents_processed,
                            'failed': self.stats.documents_failed,
                            'cost': f'${self.stats.total_cost:.4f}'
                        })
                    else:
                        self.logger.warning(f"Failed to process item {actual_index}: {content_item.title}")

                    # Save checkpoint every 10 documents
                    if (i + 1) % 10 == 0:
                        checkpoint_data = {
                            'last_processed_index': actual_index,
                            'processed_count': self.stats.documents_processed,
                            'failed_count': self.stats.documents_failed,
                            'sections_created': self.stats.sections_created,
                            'chunks_created': self.stats.chunks_created,
                            'total_cost': self.stats.total_cost,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        self._save_checkpoint(checkpoint_data)

                    pbar.update(1)

                except KeyboardInterrupt:
                    self.logger.info("Processing interrupted by user")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected error processing item {actual_index}: {e}")
                    self.stats.documents_failed += 1
                    continue

        # Final statistics
        self._log_final_statistics()

        return self.stats

    def _log_final_statistics(self):
        """Log final processing statistics."""
        elapsed_time = datetime.utcnow() - self.stats.start_time

        self.logger.info("=" * 60)
        self.logger.info("CONTENT PROCESSING COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Documents processed: {self.stats.documents_processed}")
        self.logger.info(f"Documents failed: {self.stats.documents_failed}")
        self.logger.info(f"Sections created: {self.stats.sections_created}")
        self.logger.info(f"Chunks created: {self.stats.chunks_created}")
        self.logger.info(f"Embeddings generated: {self.stats.embeddings_generated}")
        self.logger.info(f"Total tokens processed: {self.stats.total_tokens:,}")
        self.logger.info(f"Total cost: ${self.stats.total_cost:.6f}")
        self.logger.info(f"Processing time: {elapsed_time}")

        if self.stats.documents_processed > 0:
            avg_sections = self.stats.sections_created / self.stats.documents_processed
            avg_chunks = self.stats.chunks_created / self.stats.documents_processed
            cost_per_doc = self.stats.total_cost / self.stats.documents_processed

            self.logger.info(f"Average sections per document: {avg_sections:.1f}")
            self.logger.info(f"Average chunks per document: {avg_chunks:.1f}")
            self.logger.info(f"Average cost per document: ${cost_per_doc:.6f}")

        # Check corpus summary statistics
        try:
            with DatabaseSession() as session:
                corpus = session.query(CorpusSummary).first()
                if corpus:
                    self.logger.info("=" * 60)
                    self.logger.info("RAG DATABASE STATISTICS")
                    self.logger.info("=" * 60)
                    self.logger.info(f"Total documents in corpus: {corpus.total_documents}")
                    self.logger.info(f"Total sections in corpus: {corpus.total_sections}")
                    self.logger.info(f"Total chunks in corpus: {corpus.total_chunks}")
                    self.logger.info(f"Total tokens in corpus: {corpus.total_tokens:,}")
        except Exception as e:
            self.logger.warning(f"Could not retrieve corpus statistics: {e}")

        self.logger.info("=" * 60)

    def get_processing_summary(self) -> Dict[str, Any]:
        """Get a summary of processing results."""
        return {
            'documents_processed': self.stats.documents_processed,
            'documents_failed': self.stats.documents_failed,
            'sections_created': self.stats.sections_created,
            'chunks_created': self.stats.chunks_created,
            'embeddings_generated': self.stats.embeddings_generated,
            'total_tokens': self.stats.total_tokens,
            'total_cost': self.stats.total_cost,
            'processing_time_seconds': (datetime.utcnow() - self.stats.start_time).total_seconds(),
            'success_rate': self.stats.documents_processed / (self.stats.documents_processed + self.stats.documents_failed) if (self.stats.documents_processed + self.stats.documents_failed) > 0 else 0
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Process content into RAG knowledge hierarchy")
    parser.add_argument('--mode', choices=['batch', 'incremental', 'test'],
                       default='batch', help='Processing mode')
    parser.add_argument('--content-type', choices=list(SOURCE_TYPE_MAPPING.keys()),
                       help='Process only specific content type')
    parser.add_argument('--limit', type=int, help='Limit number of documents to process')
    parser.add_argument('--since', type=str, help='Process only content updated since date (YYYY-MM-DD)')
    parser.add_argument('--checkpoint-dir', default='/tmp/rag_checkpoints',
                       help='Directory for checkpoints')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    # Parse since date
    since = None
    if args.since:
        try:
            since = datetime.strptime(args.since, '%Y-%m-%d')
        except ValueError:
            print(f"Invalid date format: {args.since}. Use YYYY-MM-DD")
            return 1

    try:
        # Initialize processor
        processor = ContentProcessor(checkpoint_dir=args.checkpoint_dir)

        if args.verbose:
            processor.logger.setLevel(logging.DEBUG)

        # Get content items
        if args.content_type:
            content_items = processor._get_content_items(args.content_type, args.limit, since)
        else:
            content_items = processor.get_all_content_items(args.limit, since)

        if not content_items:
            processor.logger.info("No content items found to process")
            return 0

        processor.logger.info(f"Starting {args.mode} processing of {len(content_items)} items")

        # Run the complete processing pipeline
        stats = processor.process_all_content(content_items, resume=args.resume)

        # Print final summary
        if args.mode == 'test':
            # For test mode, show detailed results
            summary = processor.get_processing_summary()
            print(f"\n{'='*60}")
            print("PROCESSING SUMMARY")
            print(f"{'='*60}")
            print(f"Success Rate: {summary['success_rate']*100:.1f}%")
            print(f"Documents: {summary['documents_processed']} processed, {summary['documents_failed']} failed")
            print(f"Sections: {summary['sections_created']} created")
            print(f"Chunks: {summary['chunks_created']} created")
            print(f"Total Cost: ${summary['total_cost']:.6f}")
            print(f"Processing Time: {summary['processing_time_seconds']:.1f} seconds")

        # Return appropriate exit code
        if stats.documents_failed > 0 and stats.documents_processed == 0:
            processor.logger.error("All documents failed to process")
            return 1
        elif stats.documents_failed > stats.documents_processed:
            processor.logger.warning("More documents failed than succeeded")
            return 1
        else:
            processor.logger.info("Processing completed successfully")
            return 0

    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        # Save final checkpoint
        try:
            if 'processor' in locals():
                checkpoint_data = {
                    'interrupted': True,
                    'processed_count': processor.stats.documents_processed,
                    'failed_count': processor.stats.documents_failed,
                    'timestamp': datetime.utcnow().isoformat()
                }
                processor._save_checkpoint(checkpoint_data)
                print(f"Checkpoint saved. Resume with --resume flag")
        except:
            pass
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())