-- =====================================================================
-- Extensions
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================================
-- RAG / documents tables
-- =====================================================================

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    filename text NOT NULL,
    file_type text NOT NULL,
    file_size bigint NOT NULL,
    content_hash char(64) NOT NULL UNIQUE,
    status text NOT NULL DEFAULT 'processing',
    created_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id uuid NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    chunk_index int NOT NULL,
    content text NOT NULL,
    embedding vector(1024) NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- =====================================================================
-- Indexes
-- =====================================================================

CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents (content_hash);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 24, ef_construction = 128);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks (document_id);

CREATE INDEX IF NOT EXISTS idx_chunks_chunk_index ON document_chunks (chunk_index);

CREATE INDEX IF NOT EXISTS idx_chunks_metadata_jsonb ON document_chunks USING gin (metadata);