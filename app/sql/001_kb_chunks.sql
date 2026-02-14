CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS kb_chunks (
    id UUID PRIMARY KEY,
    source_type VARCHAR(64) NOT NULL,
    source_id BIGINT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(768) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_type, source_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_kb_chunks_source
    ON kb_chunks (source_type, source_id);

CREATE INDEX IF NOT EXISTS idx_kb_chunks_metadata
    ON kb_chunks USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding_ivfflat
    ON kb_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
