-- Migration: Create RAG Knowledge Hierarchy Tables
-- Date: 2026-01-06
-- Purpose: Implement hierarchical RAG system for cost-effective AI queries
-- Dependencies: pgvector extension (Prompt 14)

-- Ensure pgvector extension is available
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable required extensions for full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

BEGIN;

-- ============================================================================
-- 1. CORPUS SUMMARY TABLE
-- ============================================================================
-- Global knowledge base metadata (single row)

CREATE TABLE corpus_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Corpus metadata
    title VARCHAR(500) NOT NULL DEFAULT 'Internal Platform Knowledge Base',
    description TEXT,

    -- Statistics (updated by triggers/batch jobs)
    total_documents INTEGER DEFAULT 0,
    total_sections INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,

    -- Version tracking
    version INTEGER DEFAULT 1,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create initial corpus summary row
INSERT INTO corpus_summary (title, description) VALUES (
    'Internal Platform Knowledge Base',
    'Hierarchical knowledge base containing videos, transcripts, audio recordings, external content, documents, and social posts for AI-powered retrieval and generation.'
);

-- ============================================================================
-- 2. RAG DOCUMENTS TABLE
-- ============================================================================
-- Document-level summaries and metadata

CREATE TABLE rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Polymorphic reference to source content
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN (
        'video', 'audio', 'external_content', 'document', 'social_post'
    )),
    source_id UUID NOT NULL,

    -- Document metadata
    title VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    author VARCHAR(255),
    content_date DATE,
    language VARCHAR(10) DEFAULT 'en',

    -- AI-generated summaries
    summary TEXT,
    summary_embedding vector(1536), -- OpenAI text-embedding-3-small dimensions

    -- Content statistics
    word_count INTEGER,
    character_count INTEGER,
    section_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,

    -- Processing metadata
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (processing_status IN (
        'pending', 'processing', 'completed', 'error', 'updated'
    )),
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT,

    -- Quality metrics
    content_quality_score NUMERIC(3,2), -- 0.00 to 1.00
    embedding_quality_score NUMERIC(3,2),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 3. RAG SECTIONS TABLE
-- ============================================================================
-- Section-level summaries and logical groupings

CREATE TABLE rag_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,

    -- Polymorphic reference to source segment/section
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN (
        'transcript_segment', 'audio_segment', 'external_content_segment',
        'logical_section', 'document_section'
    )),
    source_id UUID, -- Can be NULL for logical sections

    -- Section metadata
    section_index INTEGER NOT NULL, -- Order within document
    title VARCHAR(500),
    section_type VARCHAR(50), -- chapter, paragraph, speaker_turn, time_segment, etc.

    -- Timing information (for audio/video content)
    start_time NUMERIC(10, 3),
    end_time NUMERIC(10, 3),
    duration_seconds NUMERIC(10, 3),

    -- Position information (for text content)
    start_position INTEGER,
    end_position INTEGER,

    -- Speaker information (for transcripts)
    speaker VARCHAR(255),

    -- Content
    content_text TEXT,
    summary TEXT,
    summary_embedding vector(768), -- Smaller embedding for section summaries

    -- Content statistics
    word_count INTEGER,
    character_count INTEGER,
    chunk_count INTEGER DEFAULT 0,

    -- Quality and confidence
    confidence NUMERIC(5,4), -- For transcribed content
    content_quality_score NUMERIC(3,2),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 4. RAG CHUNKS TABLE
-- ============================================================================
-- Searchable text chunks with embeddings (~400 tokens each)

CREATE TABLE rag_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
    section_id UUID REFERENCES rag_sections(id) ON DELETE CASCADE,

    -- Chunk metadata
    chunk_index INTEGER NOT NULL, -- Global order within document
    section_chunk_index INTEGER, -- Order within section

    -- Content
    content_text TEXT NOT NULL,
    content_hash VARCHAR(64), -- SHA-256 hash for deduplication

    -- Token information
    token_count INTEGER NOT NULL CHECK (token_count > 0),
    character_count INTEGER NOT NULL,

    -- Embedding and search
    embedding vector(1536) NOT NULL, -- Must have embedding for RAG
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',

    -- Context for continuity
    context_before TEXT, -- Previous chunk text for smooth reading
    context_after TEXT,  -- Next chunk text for continuity
    context_window_size INTEGER DEFAULT 0, -- Characters of overlap

    -- Source tracking and provenance
    source_references JSONB DEFAULT '[]', -- Array of source segment references
    source_metadata JSONB DEFAULT '{}',   -- Additional metadata from source

    -- Timing/position (inherited from section)
    start_time NUMERIC(10, 3),
    end_time NUMERIC(10, 3),
    start_position INTEGER,
    end_position INTEGER,

    -- Quality and relevance scores
    content_quality_score NUMERIC(3,2),
    embedding_quality_score NUMERIC(3,2),
    information_density NUMERIC(3,2), -- How much info per token

    -- Processing metadata
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_version INTEGER DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- CONSTRAINTS AND INDEXES
-- ============================================================================

-- Unique constraints
ALTER TABLE rag_documents ADD CONSTRAINT rag_documents_source_unique
    UNIQUE (source_type, source_id);

ALTER TABLE rag_sections ADD CONSTRAINT rag_sections_document_section_unique
    UNIQUE (document_id, section_index);

ALTER TABLE rag_chunks ADD CONSTRAINT rag_chunks_document_chunk_unique
    UNIQUE (document_id, chunk_index);

-- Performance indexes
CREATE INDEX idx_rag_documents_source ON rag_documents (source_type, source_id);
CREATE INDEX idx_rag_documents_status ON rag_documents (processing_status);
CREATE INDEX idx_rag_documents_created ON rag_documents (created_at);
CREATE INDEX idx_rag_documents_updated ON rag_documents (updated_at);

CREATE INDEX idx_rag_sections_document ON rag_sections (document_id);
CREATE INDEX idx_rag_sections_source ON rag_sections (source_type, source_id);
CREATE INDEX idx_rag_sections_time ON rag_sections (start_time, end_time) WHERE start_time IS NOT NULL;
CREATE INDEX idx_rag_sections_speaker ON rag_sections (speaker) WHERE speaker IS NOT NULL;

CREATE INDEX idx_rag_chunks_document ON rag_chunks (document_id);
CREATE INDEX idx_rag_chunks_section ON rag_chunks (section_id) WHERE section_id IS NOT NULL;
CREATE INDEX idx_rag_chunks_hash ON rag_chunks (content_hash) WHERE content_hash IS NOT NULL;
CREATE INDEX idx_rag_chunks_tokens ON rag_chunks (token_count);
CREATE INDEX idx_rag_chunks_time ON rag_chunks (start_time, end_time) WHERE start_time IS NOT NULL;
CREATE INDEX idx_rag_chunks_created ON rag_chunks (created_at);

-- ============================================================================
-- VECTOR INDEXES
-- ============================================================================

-- HNSW indexes for vector similarity search (best for most use cases)
CREATE INDEX idx_rag_documents_embedding_hnsw ON rag_documents
    USING hnsw (summary_embedding vector_cosine_ops)
    WHERE summary_embedding IS NOT NULL;

CREATE INDEX idx_rag_sections_embedding_hnsw ON rag_sections
    USING hnsw (summary_embedding vector_cosine_ops)
    WHERE summary_embedding IS NOT NULL;

-- Primary embedding index for chunk similarity search
CREATE INDEX idx_rag_chunks_embedding_hnsw ON rag_chunks
    USING hnsw (embedding vector_cosine_ops);

-- IVFFlat indexes for exact search (optional - useful for smaller datasets)
-- Uncomment if needed for specific use cases
-- CREATE INDEX idx_rag_chunks_embedding_ivfflat ON rag_chunks
--     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- FULL-TEXT SEARCH INDEXES
-- ============================================================================

-- GIN indexes for full-text search (hybrid with vector search)
CREATE INDEX idx_rag_documents_summary_gin ON rag_documents
    USING gin (to_tsvector('english', summary))
    WHERE summary IS NOT NULL;

CREATE INDEX idx_rag_sections_content_gin ON rag_sections
    USING gin (to_tsvector('english', content_text))
    WHERE content_text IS NOT NULL;

-- Primary full-text search index for chunks
CREATE INDEX idx_rag_chunks_content_gin ON rag_chunks
    USING gin (to_tsvector('english', content_text));

-- Trigram indexes for fuzzy text search
CREATE INDEX idx_rag_chunks_content_trgm ON rag_chunks
    USING gin (content_text gin_trgm_ops);

-- ============================================================================
-- UPDATE TRIGGERS
-- ============================================================================

-- Function to update document statistics
CREATE OR REPLACE FUNCTION update_rag_document_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update section and chunk counts
    UPDATE rag_documents
    SET
        section_count = (
            SELECT COUNT(*) FROM rag_sections
            WHERE document_id = NEW.document_id
        ),
        chunk_count = (
            SELECT COUNT(*) FROM rag_chunks
            WHERE document_id = NEW.document_id
        ),
        updated_at = NOW()
    WHERE id = NEW.document_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update corpus summary statistics
CREATE OR REPLACE FUNCTION update_corpus_summary_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE corpus_summary
    SET
        total_documents = (SELECT COUNT(*) FROM rag_documents),
        total_sections = (SELECT COUNT(*) FROM rag_sections),
        total_chunks = (SELECT COUNT(*) FROM rag_chunks),
        total_tokens = (SELECT COALESCE(SUM(token_count), 0) FROM rag_chunks),
        last_updated = NOW();

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic statistics updates
CREATE TRIGGER trigger_update_document_stats_sections
    AFTER INSERT OR DELETE ON rag_sections
    FOR EACH ROW EXECUTE FUNCTION update_rag_document_stats();

CREATE TRIGGER trigger_update_document_stats_chunks
    AFTER INSERT OR DELETE ON rag_chunks
    FOR EACH ROW EXECUTE FUNCTION update_rag_document_stats();

CREATE TRIGGER trigger_update_corpus_stats_documents
    AFTER INSERT OR UPDATE OR DELETE ON rag_documents
    FOR EACH ROW EXECUTE FUNCTION update_corpus_summary_stats();

CREATE TRIGGER trigger_update_corpus_stats_chunks
    AFTER INSERT OR DELETE ON rag_chunks
    FOR EACH ROW EXECUTE FUNCTION update_corpus_summary_stats();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get document hierarchy
CREATE OR REPLACE FUNCTION get_document_hierarchy(doc_id UUID)
RETURNS TABLE (
    document_title TEXT,
    section_count BIGINT,
    chunk_count BIGINT,
    total_tokens BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.title::TEXT,
        COUNT(DISTINCT s.id),
        COUNT(DISTINCT c.id),
        COALESCE(SUM(c.token_count), 0)
    FROM rag_documents d
    LEFT JOIN rag_sections s ON d.id = s.document_id
    LEFT JOIN rag_chunks c ON d.id = c.document_id
    WHERE d.id = doc_id
    GROUP BY d.title;
END;
$$ LANGUAGE plpgsql;

-- Function for hybrid search (vector + full-text)
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text TEXT,
    query_embedding vector(1536),
    similarity_threshold REAL DEFAULT 0.7,
    max_results INTEGER DEFAULT 20
)
RETURNS TABLE (
    chunk_id UUID,
    content_text TEXT,
    similarity_score REAL,
    text_rank REAL,
    combined_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.content_text,
        (1 - (c.embedding <=> query_embedding))::REAL as sim_score,
        ts_rank(to_tsvector('english', c.content_text), plainto_tsquery('english', query_text))::REAL as txt_rank,
        (
            (1 - (c.embedding <=> query_embedding)) * 0.7 +
            ts_rank(to_tsvector('english', c.content_text), plainto_tsquery('english', query_text)) * 0.3
        )::REAL as combined
    FROM rag_chunks c
    WHERE
        (1 - (c.embedding <=> query_embedding)) > similarity_threshold
        AND to_tsvector('english', c.content_text) @@ plainto_tsquery('english', query_text)
    ORDER BY combined DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify table creation
\echo 'Verifying RAG table creation...'

SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
    AND table_name LIKE 'corpus_summary%' OR table_name LIKE 'rag_%'
ORDER BY table_name;

-- Verify indexes
\echo 'Verifying indexes...'

SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename LIKE 'corpus_summary%' OR tablename LIKE 'rag_%'
ORDER BY tablename, indexname;

-- Verify pgvector functionality
\echo 'Testing vector operations...'

SELECT
    '[1,2,3]'::vector <-> '[1,2,4]'::vector as l2_distance,
    '[1,2,3]'::vector <=> '[1,2,4]'::vector as cosine_distance;

\echo 'RAG table migration completed successfully!'

-- ============================================================================
-- ROLLBACK SCRIPT (for reference)
-- ============================================================================

/*
-- To rollback this migration:

BEGIN;

-- Drop triggers
DROP TRIGGER IF EXISTS trigger_update_document_stats_sections ON rag_sections;
DROP TRIGGER IF EXISTS trigger_update_document_stats_chunks ON rag_chunks;
DROP TRIGGER IF EXISTS trigger_update_corpus_stats_documents ON rag_documents;
DROP TRIGGER IF EXISTS trigger_update_corpus_stats_chunks ON rag_chunks;

-- Drop functions
DROP FUNCTION IF EXISTS update_rag_document_stats();
DROP FUNCTION IF EXISTS update_corpus_summary_stats();
DROP FUNCTION IF EXISTS get_document_hierarchy(UUID);
DROP FUNCTION IF EXISTS hybrid_search(TEXT, vector(1536), REAL, INTEGER);

-- Drop tables (in dependency order)
DROP TABLE IF EXISTS rag_chunks CASCADE;
DROP TABLE IF EXISTS rag_sections CASCADE;
DROP TABLE IF EXISTS rag_documents CASCADE;
DROP TABLE IF EXISTS corpus_summary CASCADE;

COMMIT;
*/