"""
Embedding Service for RAG Implementation

Provides text embedding functionality using OpenAI's text-embedding-3-small model.
Handles single text and batch embedding with pgvector format output, cost tracking,
and error handling for the RAG knowledge hierarchy.
"""

import time
import hashlib
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import json
import logging
from dataclasses import dataclass

# Import OpenAI client
from openai import OpenAI
import openai

# Import database and config
try:
    from .config_loader import get_config
    from .db import DatabaseSession, get_engine
    from sqlalchemy import text, Column, String, Integer, DateTime, Float, Text, Boolean
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    from sqlalchemy.orm import declarative_base
    from sqlalchemy.exc import OperationalError
except ImportError:
    from config_loader import get_config
    from db import DatabaseSession, get_engine
    from sqlalchemy import text, Column, String, Integer, DateTime, Float, Text, Boolean
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    from sqlalchemy.orm import declarative_base
    from sqlalchemy.exc import OperationalError

# Configure logging
logger = logging.getLogger(__name__)


# Database model for tracking embedding usage
Base = declarative_base()


class EmbeddingUsageLog(Base):
    """Track embedding API usage for cost monitoring and analysis."""

    __tablename__ = "embedding_usage_log"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # Request metadata
    request_type = Column(String(50), nullable=False)  # single, batch, chunk_processing
    model = Column(String(100), nullable=False, default="text-embedding-3-small")

    # Input details
    text_count = Column(Integer, nullable=False)  # Number of texts processed
    total_characters = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)

    # API response
    api_latency_ms = Column(Float)
    dimensions = Column(Integer, default=1536)

    # Cost tracking
    cost_per_token = Column(Float, default=0.00000002)  # $0.02/1M tokens
    total_cost = Column(Float, nullable=False)

    # Processing details
    batch_size = Column(Integer)
    success_count = Column(Integer, nullable=False)
    error_count = Column(Integer, default=0)

    # Content hash for deduplication detection
    content_hash = Column(String(64))  # SHA-256 of input texts

    # Status and errors
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Additional metadata
    request_metadata = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))


@dataclass
class EmbeddingResult:
    """Result from embedding operation."""
    embedding: List[float]
    tokens: int
    model: str
    cost: float
    latency_ms: float
    success: bool = True
    error: Optional[str] = None


@dataclass
class BatchEmbeddingResult:
    """Result from batch embedding operation."""
    embeddings: List[List[float]]
    texts: List[str]
    total_tokens: int
    model: str
    total_cost: float
    latency_ms: float
    success_count: int
    error_count: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    # Model configuration
    DEFAULT_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536
    COST_PER_TOKEN = 0.00000002  # $0.02 per 1M tokens

    # API limits and batching
    MAX_BATCH_SIZE = 2048  # OpenAI limit
    MAX_TOKENS_PER_REQUEST = 8191  # Model limit
    RATE_LIMIT_DELAY = 0.1  # Seconds between requests

    def __init__(self):
        """Initialize the embedding service."""
        self.config = get_config()
        self._client = None
        self._ensure_usage_table()

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            api_key = self.config.openai_api_key
            if not api_key or len(api_key) < 10:
                raise ValueError(
                    "OpenAI API key not configured. Please set it in credentials.yaml "
                    "or secrets.yaml under apis.openai.api_key"
                )
            self._client = OpenAI(api_key=api_key)
        return self._client

    def _ensure_usage_table(self):
        """Ensure the embedding usage log table exists."""
        try:
            engine = get_engine()
            Base.metadata.create_all(bind=engine, tables=[EmbeddingUsageLog.__table__])
            logger.debug("Embedding usage table verified/created")
        except Exception as e:
            logger.warning(f"Could not create embedding usage table: {e}")

    def _calculate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Uses rough approximation: ~4 characters per token.
        """
        # Conservative estimation - actual tokens may be lower
        return max(1, len(text) // 4)

    def _calculate_batch_tokens(self, texts: List[str]) -> int:
        """Calculate total tokens for a batch of texts."""
        return sum(self._calculate_tokens(text) for text in texts)

    def _content_hash(self, texts: Union[str, List[str]]) -> str:
        """Generate SHA-256 hash of content for deduplication tracking."""
        if isinstance(texts, str):
            content = texts
        else:
            content = "\n".join(texts)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _log_usage(self,
                   request_type: str,
                   texts: Union[str, List[str]],
                   result: Union[EmbeddingResult, BatchEmbeddingResult],
                   content_hash: str,
                   metadata: Dict[str, Any] = None) -> None:
        """Log embedding usage for cost tracking."""
        try:
            with DatabaseSession() as db_session:
                # Prepare data based on result type
                if isinstance(result, EmbeddingResult):
                    text_count = 1
                    total_chars = len(texts) if isinstance(texts, str) else len(str(texts))
                    total_tokens = result.tokens
                    success_count = 1 if result.success else 0
                    error_count = 0 if result.success else 1
                    error_message = result.error
                    total_cost = result.cost
                    latency_ms = result.latency_ms
                    batch_size = 1
                else:  # BatchEmbeddingResult
                    text_count = len(result.texts)
                    total_chars = sum(len(text) for text in result.texts)
                    total_tokens = result.total_tokens
                    success_count = result.success_count
                    error_count = result.error_count
                    error_message = "; ".join(result.errors) if result.errors else None
                    total_cost = result.total_cost
                    latency_ms = result.latency_ms
                    batch_size = len(result.texts)

                # Create log entry
                log_entry = EmbeddingUsageLog(
                    request_type=request_type,
                    model=result.model,
                    text_count=text_count,
                    total_characters=total_chars,
                    total_tokens=total_tokens,
                    api_latency_ms=latency_ms,
                    dimensions=self.EMBEDDING_DIMENSIONS,
                    cost_per_token=self.COST_PER_TOKEN,
                    total_cost=total_cost,
                    batch_size=batch_size,
                    success_count=success_count,
                    error_count=error_count,
                    content_hash=content_hash,
                    success=success_count > 0,
                    error_message=error_message,
                    request_metadata=metadata or {}
                )

                db_session.add(log_entry)
                db_session.commit()

                logger.debug(f"Logged embedding usage: {text_count} texts, {total_tokens} tokens, ${total_cost:.4f}")

        except Exception as e:
            logger.warning(f"Failed to log embedding usage: {e}")

    def _validate_text(self, text: str) -> str:
        """Validate and prepare text for embedding."""
        if not isinstance(text, str):
            raise ValueError("Text must be a string")

        if not text.strip():
            raise ValueError("Text cannot be empty")

        # Trim whitespace
        text = text.strip()

        # Check token limit (conservative estimate)
        estimated_tokens = self._calculate_tokens(text)
        if estimated_tokens > self.MAX_TOKENS_PER_REQUEST:
            logger.warning(f"Text may exceed token limit: {estimated_tokens} > {self.MAX_TOKENS_PER_REQUEST}")
            # Truncate text to approximate token limit
            max_chars = self.MAX_TOKENS_PER_REQUEST * 4
            text = text[:max_chars]

        return text

    def _format_for_pgvector(self, embedding: List[float]) -> str:
        """Format embedding for pgvector storage."""
        # pgvector expects a string representation of a list
        # Convert to string format that PostgreSQL can parse
        return str(embedding)

    def embed_text(self,
                   text: str,
                   model: str = None,
                   metadata: Dict[str, Any] = None) -> EmbeddingResult:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            model: Embedding model to use (defaults to text-embedding-3-small)
            metadata: Additional metadata for logging

        Returns:
            EmbeddingResult with embedding vector and metadata
        """
        if model is None:
            model = self.DEFAULT_MODEL

        # Validate input
        text = self._validate_text(text)
        content_hash = self._content_hash(text)

        # Calculate expected cost
        estimated_tokens = self._calculate_tokens(text)
        estimated_cost = estimated_tokens * self.COST_PER_TOKEN

        start_time = time.time()

        try:
            client = self._get_client()

            # Make API call
            response = client.embeddings.create(
                model=model,
                input=text,
                encoding_format="float"
            )

            latency_ms = (time.time() - start_time) * 1000

            # Extract results
            embedding = response.data[0].embedding
            actual_tokens = response.usage.total_tokens
            actual_cost = actual_tokens * self.COST_PER_TOKEN

            # Validate embedding dimensions
            if len(embedding) != self.EMBEDDING_DIMENSIONS:
                raise ValueError(f"Unexpected embedding dimensions: {len(embedding)} != {self.EMBEDDING_DIMENSIONS}")

            result = EmbeddingResult(
                embedding=embedding,
                tokens=actual_tokens,
                model=model,
                cost=actual_cost,
                latency_ms=latency_ms,
                success=True
            )

            # Log usage
            self._log_usage("single", text, result, content_hash, metadata)

            return result

        except openai.RateLimitError as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"Rate limit exceeded: {e}"
            logger.error(error_msg)

            result = EmbeddingResult(
                embedding=[],
                tokens=estimated_tokens,
                model=model,
                cost=estimated_cost,
                latency_ms=latency_ms,
                success=False,
                error=error_msg
            )

            self._log_usage("single", text, result, content_hash, metadata)
            return result

        except openai.APIError as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"OpenAI API error: {e}"
            logger.error(error_msg)

            result = EmbeddingResult(
                embedding=[],
                tokens=estimated_tokens,
                model=model,
                cost=estimated_cost,
                latency_ms=latency_ms,
                success=False,
                error=error_msg
            )

            self._log_usage("single", text, result, content_hash, metadata)
            return result

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"Embedding error: {e}"
            logger.error(error_msg)

            result = EmbeddingResult(
                embedding=[],
                tokens=estimated_tokens,
                model=model,
                cost=estimated_cost,
                latency_ms=latency_ms,
                success=False,
                error=error_msg
            )

            self._log_usage("single", text, result, content_hash, metadata)
            return result

    def embed_batch(self,
                    texts: List[str],
                    model: str = None,
                    batch_size: int = None,
                    metadata: Dict[str, Any] = None) -> BatchEmbeddingResult:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed
            model: Embedding model to use
            batch_size: Override default batch size
            metadata: Additional metadata for logging

        Returns:
            BatchEmbeddingResult with all embeddings and metadata
        """
        if model is None:
            model = self.DEFAULT_MODEL

        if batch_size is None:
            batch_size = min(self.MAX_BATCH_SIZE, len(texts))

        # Validate inputs
        if not texts:
            raise ValueError("No texts provided")

        # Validate and prepare texts
        validated_texts = []
        for i, text in enumerate(texts):
            try:
                validated_text = self._validate_text(text)
                validated_texts.append(validated_text)
            except ValueError as e:
                logger.warning(f"Skipping invalid text at index {i}: {e}")

        if not validated_texts:
            raise ValueError("No valid texts after validation")

        content_hash = self._content_hash(validated_texts)
        estimated_tokens = self._calculate_batch_tokens(validated_texts)
        estimated_cost = estimated_tokens * self.COST_PER_TOKEN

        start_time = time.time()

        all_embeddings = []
        total_tokens = 0
        total_cost = 0.0
        success_count = 0
        errors = []

        try:
            client = self._get_client()

            # Process in batches
            for i in range(0, len(validated_texts), batch_size):
                batch = validated_texts[i:i + batch_size]

                # Add rate limiting between batches
                if i > 0:
                    time.sleep(self.RATE_LIMIT_DELAY)

                try:
                    # Make batch API call
                    response = client.embeddings.create(
                        model=model,
                        input=batch,
                        encoding_format="float"
                    )

                    # Extract embeddings
                    batch_embeddings = [data.embedding for data in response.data]

                    # Validate embedding dimensions
                    for j, embedding in enumerate(batch_embeddings):
                        if len(embedding) != self.EMBEDDING_DIMENSIONS:
                            raise ValueError(f"Unexpected embedding dimensions at index {i+j}: {len(embedding)} != {self.EMBEDDING_DIMENSIONS}")

                    all_embeddings.extend(batch_embeddings)

                    # Track usage
                    batch_tokens = response.usage.total_tokens
                    batch_cost = batch_tokens * self.COST_PER_TOKEN
                    total_tokens += batch_tokens
                    total_cost += batch_cost
                    success_count += len(batch)

                    logger.debug(f"Processed batch {i//batch_size + 1}: {len(batch)} texts, {batch_tokens} tokens, ${batch_cost:.4f}")

                except Exception as e:
                    error_msg = f"Batch {i//batch_size + 1} failed: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)

                    # Add empty embeddings for failed batch
                    all_embeddings.extend([[] for _ in batch])

            latency_ms = (time.time() - start_time) * 1000

            result = BatchEmbeddingResult(
                embeddings=all_embeddings,
                texts=validated_texts,
                total_tokens=total_tokens,
                model=model,
                total_cost=total_cost,
                latency_ms=latency_ms,
                success_count=success_count,
                error_count=len(validated_texts) - success_count,
                errors=errors
            )

            # Log usage
            self._log_usage("batch", validated_texts, result, content_hash, metadata)

            return result

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"Batch embedding failed: {e}"
            logger.error(error_msg)

            result = BatchEmbeddingResult(
                embeddings=[[] for _ in validated_texts],
                texts=validated_texts,
                total_tokens=estimated_tokens,
                model=model,
                total_cost=estimated_cost,
                latency_ms=latency_ms,
                success_count=0,
                error_count=len(validated_texts),
                errors=[error_msg]
            )

            self._log_usage("batch", validated_texts, result, content_hash, metadata)
            return result

    def embed_for_pgvector(self,
                          text: str,
                          model: str = None,
                          metadata: Dict[str, Any] = None) -> Tuple[str, EmbeddingResult]:
        """
        Generate embedding formatted for pgvector storage.

        Args:
            text: Text to embed
            model: Embedding model to use
            metadata: Additional metadata for logging

        Returns:
            Tuple of (pgvector_formatted_string, EmbeddingResult)
        """
        result = self.embed_text(text, model, metadata)

        if result.success:
            pgvector_format = self._format_for_pgvector(result.embedding)
            return pgvector_format, result
        else:
            return None, result

    def embed_batch_for_pgvector(self,
                                texts: List[str],
                                model: str = None,
                                batch_size: int = None,
                                metadata: Dict[str, Any] = None) -> Tuple[List[str], BatchEmbeddingResult]:
        """
        Generate batch embeddings formatted for pgvector storage.

        Args:
            texts: List of texts to embed
            model: Embedding model to use
            batch_size: Override default batch size
            metadata: Additional metadata for logging

        Returns:
            Tuple of (list_of_pgvector_formatted_strings, BatchEmbeddingResult)
        """
        result = self.embed_batch(texts, model, batch_size, metadata)

        pgvector_embeddings = []
        for embedding in result.embeddings:
            if embedding:  # Non-empty embedding (successful)
                pgvector_embeddings.append(self._format_for_pgvector(embedding))
            else:  # Empty embedding (failed)
                pgvector_embeddings.append(None)

        return pgvector_embeddings, result

    def get_usage_stats(self,
                       start_date: datetime = None,
                       end_date: datetime = None) -> Dict[str, Any]:
        """
        Get embedding usage statistics for cost monitoring.

        Args:
            start_date: Start of date range (optional)
            end_date: End of date range (optional)

        Returns:
            Dictionary with usage statistics
        """
        try:
            with DatabaseSession() as db_session:
                query = db_session.query(EmbeddingUsageLog)

                # Apply date filters
                if start_date:
                    query = query.filter(EmbeddingUsageLog.created_at >= start_date)
                if end_date:
                    query = query.filter(EmbeddingUsageLog.created_at <= end_date)

                logs = query.all()

                # Calculate statistics
                total_requests = len(logs)
                total_texts = sum(log.text_count for log in logs)
                total_tokens = sum(log.total_tokens for log in logs)
                total_cost = sum(log.total_cost for log in logs)
                total_characters = sum(log.total_characters for log in logs)
                successful_requests = sum(1 for log in logs if log.success)

                avg_latency = sum(log.api_latency_ms for log in logs if log.api_latency_ms) / max(1, total_requests)
                avg_tokens_per_text = total_tokens / max(1, total_texts)

                # Group by request type
                by_request_type = {}
                for log in logs:
                    req_type = log.request_type
                    if req_type not in by_request_type:
                        by_request_type[req_type] = {
                            'requests': 0,
                            'texts': 0,
                            'tokens': 0,
                            'cost': 0.0
                        }

                    by_request_type[req_type]['requests'] += 1
                    by_request_type[req_type]['texts'] += log.text_count
                    by_request_type[req_type]['tokens'] += log.total_tokens
                    by_request_type[req_type]['cost'] += log.total_cost

                return {
                    'total_requests': total_requests,
                    'total_texts': total_texts,
                    'total_tokens': total_tokens,
                    'total_cost': total_cost,
                    'total_characters': total_characters,
                    'successful_requests': successful_requests,
                    'success_rate': successful_requests / max(1, total_requests),
                    'avg_latency_ms': avg_latency,
                    'avg_tokens_per_text': avg_tokens_per_text,
                    'by_request_type': by_request_type,
                    'date_range': {
                        'start': start_date.isoformat() if start_date else None,
                        'end': end_date.isoformat() if end_date else None
                    }
                }

        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {
                'error': str(e),
                'total_requests': 0,
                'total_cost': 0.0
            }


# Convenience function for quick access
def get_embedding_service() -> EmbeddingService:
    """Get a configured embedding service instance."""
    return EmbeddingService()


# Module-level convenience functions
def embed_text(text: str, **kwargs) -> EmbeddingResult:
    """Quick text embedding function."""
    service = get_embedding_service()
    return service.embed_text(text, **kwargs)


def embed_batch(texts: List[str], **kwargs) -> BatchEmbeddingResult:
    """Quick batch embedding function."""
    service = get_embedding_service()
    return service.embed_batch(texts, **kwargs)


def embed_for_pgvector(text: str, **kwargs) -> Tuple[str, EmbeddingResult]:
    """Quick embedding function with pgvector formatting."""
    service = get_embedding_service()
    return service.embed_for_pgvector(text, **kwargs)