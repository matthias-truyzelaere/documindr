# RAG API

A clean, modular, production‑ready Retrieval‑Augmented Generation (RAG) API built with FastAPI and fully containerized with Docker Compose.

The system:

- Indexes uploaded documents into PostgreSQL + pgvector
- Performs hybrid semantic/BM25 retrieval
- Streams LLM responses via Ollama in real time
- Generates document summaries with configurable length
- Is fronted by Caddy as a reverse proxy (HTTP/HTTPS)

---

## Features

- Document upload and automatic chunking
- SHA‑256 content hashing to avoid duplicate indexing
- Semantic + BM25 hybrid retrieval
- pgvector (HNSW) similarity search
- Fully streaming LLM responses via Ollama
- Document summarization with configurable length (concise, normal, comprehensive)
- Modular, domain‑driven architecture
- Centralized configuration via Pydantic Settings
- Built‑in rate limiting middleware
- Production logging with custom formatter
- Docker‑ready (FastAPI + Ollama + Postgres + Caddy)
- **API documentation endpoints (enabled for testing; disable for production)**

---

## Tech Stack

- FastAPI (backend API)
- PostgreSQL 18 + pgvector (vector store)
- Ollama (LLM chat + embeddings)
- LangChain + LangChain Ollama integration
- Pydantic Settings
- psycopg3 + pgvector
- Caddy (reverse proxy / TLS)

---

## Architecture

Docker services (from `docker-compose.yml`):

- `backend` – FastAPI RAG API
- `ollama` – Ollama LLM server
- `postgres` – PostgreSQL with pgvector extension and RAG schema (`init-db.sql`)
- `caddy` – Reverse proxy (HTTP/HTTPS, security headers, request limits)

Caddy routes all `/api` traffic to the FastAPI backend.

---

## Project Structure

```text
app/
 ├── api/           # routes, schemas, dependencies
 ├── core/          # config, CORS, logging, rate limiting
 ├── domain/        # documents, RAG, embeddings, uploads
 ├── infra/         # database connection + queries
 └── main.py        # FastAPI application entrypoint

db/
 └── init-db.sql    # PostgreSQL + pgvector schema

scripts/
 └── ollama-init.sh # optional Ollama init script

docs/
 ├── endpoint-flows.md    # detailed flow documentation for each endpoint
 └── getting-started.md   # setup and initial configuration guide

docker-compose.yml  # all services (backend, ollama, postgres, caddy)
Dockerfile          # backend build
Caddyfile           # Caddy reverse proxy config
Makefile            # helper targets: up / down / build
.env.example        # example environment configuration
```

---

## Environment Variables

Copy `.env.example` to `.env` in the project root and fill in the values.

```text
# -----------------------------------------------------------------------------
# CORS Configuration
# -----------------------------------------------------------------------------

# Allowed Origins
ALLOWED_ORIGINS=https://localhost

# -----------------------------------------------------------------------------
# Ollama Configuration
# -----------------------------------------------------------------------------

# Ollama Base URL
OLLAMA_BASE_URL=http://ollama:11434

# Ollama API Key
OLLAMA_API_KEY=

# Chat Model
CHAT_MODEL=gpt-oss:20b-cloud

# Embeddings Model
EMBEDDING_MODEL=bge-m3

# Keep Alive
KEEP_ALIVE=-1

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------

# Database User
POSTGRES_USER=

# Database Password
POSTGRES_PASSWORD=

# Database Name
POSTGRES_DB=

# Database Host
POSTGRES_HOST=

# Database Port
POSTGRES_PORT=

# -----------------------------------------------------------------------------
# Retrieval Configuration
# -----------------------------------------------------------------------------

# Chunk Size
CHUNK_SIZE=800

# Chunk Size
CHUNK_SIZE_MIN=50

# Chunk Overlap
CHUNK_OVERLAP=100

# Number Of Retrievals
RETRIEVER_K=5

# -----------------------------------------------------------------------------
# Document Upload Configuration
# -----------------------------------------------------------------------------

# Data Folder Path
DATA_PATH=/data

# Max File Size
MAX_FILE_SIZE=52428800

# -----------------------------------------------------------------------------
# Rate Limit Configuration
# -----------------------------------------------------------------------------

# Rate Limit Chat
RATE_LIMIT_CHAT=10

# Rate Limit Chat Window
RATE_LIMIT_CHAT_WINDOW=60

# Rate Limit Upload
RATE_LIMIT_UPLOAD=5

# Rate Limit Upload Window
RATE_LIMIT_UPLOAD_WINDOW=300

# Rate Limit Default
RATE_LIMIT_DEFAULT=30

# Rate Limit Default Window
RATE_LIMIT_DEFAULT_WINDOW=60
```

Notes:

- `OLLAMA_BASE_URL` should point to the Ollama container, e.g. `http://ollama:11434`.
- `POSTGRES_HOST` should be `postgres` when using Docker Compose.
- `DATA_PATH` is where uploaded files will be stored inside the backend container, e.g. `/data`.

All configuration is read via `app/core/config.py` using Pydantic Settings.

---

## Database Schema

The database is initialized automatically by Postgres using `db/init-db.sql`.

Key tables:

```sql
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
```

- `content_hash` is unique: duplicate uploads of the same file content are detected and skipped.
- Chunk embeddings use a 1024‑dimensional vector with an HNSW index for fast similarity search.

---

## Running with Docker

### Prerequisites

- Docker
- Docker Compose
- Optional: a public domain and DNS pointing to the host (for production Caddy HTTPS)

### Quick start

From the project root:

```bash
cp .env.example .env    # edit .env with your values
make up                 # or: docker compose up -d
```

This will start:

- FastAPI backend on the internal network (exposed as `backend:8000`)
- Ollama on `ollama:11434` and forwarded to host `11434:11434`
- Postgres on `postgres:5432` and forwarded to host `5432:5432`
- Caddy reverse proxy on host ports `80` and `443`

On a local dev machine using the default Caddyfile, you can reach:

- API via Caddy: `http://localhost/api`
- Health: `http://localhost/api/health`
- API Docs (Swagger UI): `http://localhost/api/docs`
- API Docs (ReDoc): `http://localhost/api/redoc`
- OpenAPI Schema: `http://localhost/api/openapi.json`

**Note:** API documentation endpoints (`/api/docs`, `/api/redoc`, `/api/openapi.json`) are currently enabled for testing purposes. For production deployments, these should be disabled by setting them to `None` in `app/main.py`.

If you want to talk directly to the backend (bypassing Caddy):

```bash
curl http://localhost:8000/api/health
```

### Stopping and rebuilding

Using the provided `Makefile`:

```bash
make down       # stop all services
make build      # rebuild and restart all services
```

Or directly:

```bash
docker compose down
docker compose up -d --build
```

---

## Ollama Setup

The `ollama` service is defined in `docker-compose.yml`:

- Image: `ollama/ollama:latest`
- Port: `11434`
- Data volume: `ollama:/root/.ollama`
- Optional `scripts/ollama-init.sh` entrypoint (for automatic model pulls, etc.)

Once the stack is up, ensure models are available inside the Ollama container, for example:

```bash
docker exec -it ollama ollama pull <your-chat-model>
docker exec -it ollama ollama pull <your-embedding-model>
```

Match the `CHAT_MODEL` and `EMBEDDING_MODEL` names in your `.env` to what you pulled.

---

## Reverse Proxy (Caddy)

Caddy is configured via `Caddyfile`.

Local development example:

- Hosts: `localhost`, `rag-chatbot.local`
- Proxies all `/api*` paths to `backend:8000`
- Adds security headers
- Sets generous timeouts for long‑running streaming requests
- Limits request body size to 200 MB for uploads

For production:

- Replace `your-domain.com` / `www.your-domain.com` with your real domain
- Point DNS to the server
- Caddy will automatically obtain TLS certificates via Let's Encrypt

---

## Local Development (without Docker)

You can still run the backend directly if you prefer:

1. Ensure Postgres + pgvector are available and reachable.
2. Ensure Ollama is running locally and has the required models pulled.
3. Create and fill `.env`.
4. Create a virtual environment and install dependencies:

    ```bash
    pip install --no-cache-dir -r requirements.txt
    ```

5. Start the API:

    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

---

## API Endpoints

Base URL (behind Caddy): `/api`

**Note:** Interactive API documentation (Swagger UI, ReDoc) is currently enabled for testing at `/api/docs` and `/api/redoc`. For production, these should be disabled (see Security section below).

For detailed flow diagrams of each endpoint, see [`docs/endpoint-flows.md`](docs/endpoint-flows.md).

### `GET /api`

API root endpoint with version information.

Response:

```json
{
    "success": true,
    "code": "API_READY",
    "message": "API is ready",
    "data": {
        "status": "ready",
        "version": "1.0.0",
        "author": "Matthias Truyzelaere"
    }
}
```

### `GET /api/health`

Simple health check for Ollama, database, and connection pool.

Response:

```json
{
    "success": true,
    "code": "HEALTH_OK",
    "message": "Service is healthy",
    "data": {
        "status": "healthy",
        "ollama": "healthy",
        "database": "healthy",
        "pool_size": 10,
        "pool_available": 9
    }
}
```

### `POST /api/upload`

Uploads and indexes a document.

- Body: `multipart/form-data`
    - `file`: the file to upload (`.pdf`, `.txt`, `.docx`)

Behavior:

- File is stored in `DATA_PATH`.
- SHA‑256 hash is computed.
- If a document with the same `content_hash` already exists, indexing is skipped.
- If it is new, the file is loaded, split into chunks, embedded, and stored.

Response model:

```json
{
    "success": true,
    "code": "UPLOAD_SUCCESS",
    "message": "File uploaded and indexed successfully.",
    "data": {
        "filename": "document.pdf",
        "document_id": "uuid-here",
        "chunks_indexed": 15
    }
}
```

Examples:

- First upload:

    ```json
    {
        "success": true,
        "code": "UPLOAD_SUCCESS",
        "message": "File uploaded and indexed successfully.",
        "data": {
            "filename": "mydoc.pdf",
            "document_id": "123e4567-e89b-12d3-a456-426614174000",
            "chunks_indexed": 20
        }
    }
    ```

- Duplicate upload:

    ```json
    {
        "success": true,
        "code": "UPLOAD_SUCCESS",
        "message": "File was already indexed. Skipped duplicate processing.",
        "data": {
            "filename": "mydoc.pdf",
            "document_id": "123e4567-e89b-12d3-a456-426614174000",
            "chunks_indexed": 0
        }
    }
    ```

### `POST /api/chat`

Streams an LLM response based on the indexed documents.

- Body (JSON):

    ```json
    {
        "message": "Your question here"
    }
    ```

- Response:
    - `text/plain` streaming response
    - Content streamed chunk by chunk

RAG behavior:

1. Hybrid retrieval (semantic + BM25) from `document_chunks`.
2. Builds a plain‑text context with chunk markers.
3. Sends prompt + context to the Ollama chat model.
4. Streams the generated answer back to the client.

The prompt instructs the model to:

- Answer only from provided context
- Keep the answer in the same language as the question
- Use plain text (no markdown, no formatting)
- Avoid hallucinations (otherwise say: `"I cannot find this information in the provided text."`)

### `POST /api/chat/{document_id}`

Streams an LLM response based on a **specific document** only.

- Path parameter:
    - `document_id`: UUID of the document to chat with

- Body (JSON):

    ```json
    {
        "message": "Your question here"
    }
    ```

- Response:
    - `text/plain` streaming response
    - Content streamed chunk by chunk

RAG behavior:

1. Validates that the document exists (returns 404 if not found).
2. Hybrid retrieval (semantic + BM25) from `document_chunks` **filtered by document_id**.
3. Builds a plain‑text context with chunk markers from only this document.
4. Sends prompt + context to the Ollama chat model.
5. Streams the generated answer back to the client.

The prompt instructs the model to:

- Answer only from provided context (from this specific document)
- Keep the answer in the same language as the question
- Use plain text (no markdown, no formatting)
- Avoid hallucinations (otherwise say: `"I cannot find this information in the provided text."`)

**Use case:** When you want to ask questions about a specific document without interference from other indexed documents.

Example request:

```bash
curl -X POST http://localhost/api/chat/123e4567-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the main topic of this document?"}'
```

### `POST /api/chat/{document_id}/summary`

Generate a streaming summary of a specific document with configurable length.

- Path parameter:
    - `document_id`: UUID of the document to summarize

- Query parameter (optional):
    - `length`: Summary length - one of:
        - `concise` - Brief summary (3-5 sentences, key points only)
        - `normal` - Balanced summary (8-12 sentences, main points and details) **[DEFAULT]**
        - `comprehensive` - Detailed summary (15-25 sentences, thorough coverage)

- Response:
    - `text/plain` streaming response
    - Summary streamed chunk by chunk

Summary behavior:

1. Validates that the document exists (returns 404 if not found).
2. Retrieves **all chunks** from the document (ordered by chunk_index).
3. Builds complete document context from all chunks.
4. Uses length-specific prompt to generate appropriate summary.
5. Streams the generated summary back to the client.

**Summary characteristics:**

| Length        | Sentences | Focus                                    |
| ------------- | --------- | ---------------------------------------- |
| concise       | 3-5       | Most important key points only           |
| normal        | 8-12      | Main points and important details        |
| comprehensive | 15-25     | All major points with supporting details |

**Use case:** When you want a quick overview of a document without reading the entire content or asking specific questions.

Example requests:

```bash
# Default (normal) length summary
curl -X POST http://localhost/api/chat/123e4567-e89b-12d3-a456-426614174000/summary

# Concise summary
curl -X POST http://localhost/api/chat/123e4567-e89b-12d3-a456-426614174000/summary?length=concise

# Comprehensive summary
curl -X POST http://localhost/api/chat/123e4567-e89b-12d3-a456-426614174000/summary?length=comprehensive
```

### `GET /api/documents`

Retrieve all indexed documents with metadata.

Response:

```json
{
    "success": true,
    "code": "DOCUMENTS_LIST_SUCCESS",
    "message": "Documents retrieved successfully",
    "data": {
        "documents": [
            {
                "id": "uuid-here",
                "filename": "document.pdf",
                "file_type": "pdf",
                "file_size": 1024000,
                "status": "completed",
                "created_at": "2025-12-09T10:30:00Z"
            }
        ],
        "total": 1
    }
}
```

### `DELETE /api/documents/{document_id}`

Delete document and all associated chunks by ID.

Response:

```json
{
    "success": true,
    "code": "DOCUMENT_DELETED",
    "message": "Document deleted successfully",
    "data": null
}
```

---

## Security

### API Documentation

The following FastAPI auto-generated documentation endpoints are currently **enabled for testing purposes**:

- `/api/docs` (Swagger UI)
- `/api/redoc` (ReDoc)
- `/api/openapi.json` (OpenAPI schema)

**IMPORTANT:** For production deployments, these endpoints should be **disabled** to prevent unauthorized users from discovering your API structure. To disable documentation, modify `app/main.py`:

```python
app = FastAPI(
    title="RAG API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,          # Disable Swagger UI
    redoc_url=None,         # Disable ReDoc
    openapi_url=None,       # Disable OpenAPI schema
)
```

When disabled, all endpoints must be accessed directly using HTTP clients or your frontend application.

### Other Security Features

- CORS configuration with explicit allowed origins
- Rate limiting per endpoint (configurable via environment variables)
- Request size limits (210 MB global, 200 MB for Caddy uploads)
- Security headers via Caddy (HSTS, X-Frame-Options, CSP, etc.)
- Input validation and sanitization
- Dangerous pattern detection in chat messages

---

## Rate Limiting

File: `app/core/ratelimit.py`

- Per‑IP token bucket
- Configurable per endpoint via environment variables
- On exceeding: HTTP 429 response

Default limits (from `.env`):

```
RATE_LIMIT_CHAT=10              # requests
RATE_LIMIT_CHAT_WINDOW=60       # seconds
RATE_LIMIT_UPLOAD=5             # requests
RATE_LIMIT_UPLOAD_WINDOW=300    # seconds
RATE_LIMIT_DEFAULT=30           # requests
RATE_LIMIT_DEFAULT_WINDOW=60    # seconds
```

The middleware is registered in `app/main.py`:

```python
app.middleware("http")(rate_limit)
```

---

## Logging

File: `app/core/logger.py`

- Root logger configured with a custom formatter, printing level badges and messages.
- Uvicorn log noise is reduced (warning/error only).
- RAG pipeline logs:
    - Query
    - Sources used
    - Retrieval time
    - LLM response time
    - Time to first token
    - Tokens per second
- Summary generation logs:
    - Document ID
    - Summary length
    - Chunk count
    - Generation metrics

---

## Duplicate Upload Handling

- Each file is hashed with SHA‑256 (`compute_file_hash`).
- `documents.content_hash` is unique.
- Before indexing, the system checks for an existing document with the same hash.
- If found, indexing is skipped and a clear message is returned.
- This avoids unique constraint errors and duplicate chunk entries.

---

## Testing

The project includes unit and integration tests:

```bash
# Run all tests
docker compose exec backend pytest

# Or with uv (if installed locally)
uv run pytest
```

Test structure:

```
tests/
├── unit/              # Unit tests for individual components
│   ├── test_chunk_size.py
│   ├── test_fix_percent.py
│   ├── test_hashing.py
│   └── ...
└── integration/       # Integration tests for API endpoints
    ├── test_chat.py
    ├── test_health.py
    ├── test_root.py
    ├── test_summary.py
    └── test_upload.py
```

---

## Makefile

Helpful shortcuts:

```bash
make up      # docker compose up -d
make down    # docker compose down
make build   # docker compose up -d --build
```
