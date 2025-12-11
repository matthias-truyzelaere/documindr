# API Endpoint Flow Documentation

This document provides detailed flow diagrams for each API endpoint in the RAG API.

---

## Table of Contents

1. [Root Endpoint (`GET /api`)](#root-endpoint)
2. [Health Check (`GET /api/health`)](#health-check)
3. [Upload Document (`POST /api/upload`)](#upload-document)
4. [Chat - All Documents (`POST /api/chat`)](#chat-all-documents)
5. [Chat - Single Document (`POST /api/chat/{document_id}`)](#chat-single-document)
6. [Summarize Document (`POST /api/chat/{document_id}/summary`)](#summarize-document)
7. [List Documents (`GET /api/documents`)](#list-documents)
8. [Delete Document (`DELETE /api/documents/{document_id}`)](#delete-document)

---

## Root Endpoint

**Route:** `GET /api`

**Purpose:** Provides API version and status information

### Flow

```
1. Client Request
   └─> GET /api

2. Handler (app/api/routes/root.py)
   └─> Return static API information
       ├─> status: "ready"
       ├─> version: "1.0.0"
       └─> author: "Matthias Truyzelaere"

3. Response
   └─> 200 OK with API metadata
```

### Response Schema

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

---

## Health Check

**Route:** `GET /api/health`

**Purpose:** Verifies service health (Ollama, Database, Connection Pool)

### Flow

```
1. Client Request
   └─> GET /api/health

2. Handler (app/api/routes/health.py)
   │
   ├─> Check Ollama Status
   │   └─> domain/rag/model.py: get_chat_model()
   │       └─> Invoke "ping" message
   │           ├─> Success → "healthy"
   │           └─> Failure → "unhealthy"
   │
   ├─> Check Database Status
   │   └─> infra/database/connection.py: pool.connection()
   │       └─> Execute "SELECT 1"
   │           ├─> Success → "healthy"
   │           └─> Failure → "unhealthy"
   │
   └─> Get Pool Statistics
       └─> pool.get_stats()
           ├─> pool_size
           └─> pool_available

3. Response
   └─> 200 OK (if all healthy)
   └─> 200 OK with degraded status (if any unhealthy)
```

### Response Schema

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

---

## Upload Document

**Route:** `POST /api/upload`

**Purpose:** Upload, process, chunk, embed, and index a document

### Flow

```
1. Client Request
   └─> POST /api/upload
       └─> multipart/form-data: file

2. Handler (app/api/routes/upload.py)
   └─> domain/uploads/processor.py: process_upload()

3. Validation (domain/uploads/processor.py)
   │
   ├─> Check filename exists
   ├─> Sanitize filename
   ├─> Validate extension (.pdf, .txt, .docx)
   ├─> Check file size (max: MAX_FILE_SIZE)
   └─> Check file not empty

4. Save File
   └─> aiofiles: Save to DATA_PATH

5. Hash Computation (domain/documents/hashing.py)
   └─> compute_file_hash()
       └─> SHA-256 hash of file content

6. Check for Duplicate (infra/database/queries.py)
   └─> get_document_by_hash(content_hash)
       ├─> If exists → Return existing document_id with 0 chunks
       └─> If not exists → Continue processing

7. Load Document (domain/documents/loader.py)
   │
   ├─> For PDF files
   │   └─> load_pdf(): Extract text page by page
   │
   └─> For other files
       └─> UnstructuredLoader: Extract text

8. Split into Chunks (domain/documents/splitter.py)
   │
   ├─> Filter chunks < MIN_CHARS
   ├─> Adaptive chunk sizing
   │   └─> choose_chunk_size() based on document length
   └─> RecursiveCharacterTextSplitter
       └─> Split with semantic separators

9. Index Chunks (infra/database/queries.py)
   │
   ├─> insert_document()
   │   └─> Create document record (status: "processing")
   │
   ├─> Generate Embeddings
   │   └─> domain/embeddings/provider.py
   │       └─> get_embedding_function()
   │           └─> batch_embed() in batches of 32
   │
   ├─> insert_document_chunks()
   │   └─> Store chunks with embeddings and metadata
   │
   └─> mark_document_completed()
       └─> Update status to "completed"

10. Response
    └─> 200 OK with document_id and chunk count
```

### Response Schema

```json
{
    "success": true,
    "code": "UPLOAD_SUCCESS",
    "message": "File uploaded and indexed successfully.",
    "data": {
        "filename": "document.pdf",
        "document_id": "123e4567-e89b-12d3-a456-426614174000",
        "chunks_indexed": 20
    }
}
```

---

## Chat All Documents

**Route:** `POST /api/chat`

**Purpose:** Stream RAG response using context from all indexed documents

### Flow

```
1. Client Request
   └─> POST /api/chat
       └─> JSON: {"message": "query"}

2. Validation (app/api/routes/chat.py)
   │
   ├─> Check message not empty
   └─> Check for dangerous patterns
       └─> ["<script", "javascript:", "onerror="]

3. Stream Response
   └─> domain/rag/streaming.py: stream_rag(query)

4. Hybrid Search (domain/rag/retrieval.py)
   │
   ├─> Semantic Search
   │   └─> Embed query using embedding model
   │   └─> Vector similarity search in PostgreSQL
   │       └─> SELECT ... ORDER BY embedding <-> query_vector LIMIT k
   │
   └─> BM25 Retrieval
       └─> BM25Retriever.from_documents()
           └─> Re-rank semantic results using BM25

5. Build Context (domain/rag/retrieval.py)
   └─> Format chunks into plain text with markers
       └─> "[Chunk 1]\n{content}\n\n---\n\n[Chunk 2]\n{content}"

6. Generate Response (domain/rag/model.py)
   │
   ├─> get_chat_model()
   ├─> Format prompt with context and query
   └─> Stream response from Ollama
       └─> Log performance metrics
           ├─> Time to first token (TTFT)
           ├─> Tokens per second
           └─> Total LLM time

7. Stream to Client
   └─> StreamingResponse (text/plain)
       └─> Yield chunks as UTF-8 bytes
```

### Request Schema

```json
{
    "message": "What is the main topic of the document?"
}
```

### Response

Streaming text/plain response

---

## Chat Single Document

**Route:** `POST /api/chat/{document_id}`

**Purpose:** Stream RAG response using context from a specific document only

### Flow

```
1. Client Request
   └─> POST /api/chat/{document_id}
       └─> JSON: {"message": "query"}

2. Validation (app/api/routes/chat.py)
   │
   ├─> Check message not empty
   ├─> Check for dangerous patterns
   └─> Verify document exists
       └─> infra/database/queries.py: document_exists(document_id)
           ├─> If not found → 404 DOCUMENT_NOT_FOUND
           └─> If found → Continue

3. Stream Response
   └─> domain/rag/streaming.py: stream_rag(query, document_id)

4. Hybrid Search with Document Filter (domain/rag/retrieval.py)
   │
   ├─> Semantic Search (filtered by document_id)
   │   └─> SELECT ... WHERE document_id = %s ORDER BY embedding <-> query_vector
   │
   └─> BM25 Retrieval
       └─> Re-rank filtered results

5. Build Context
   └─> Same as Chat All Documents

6. Generate Response
   └─> Same as Chat All Documents

7. Stream to Client
   └─> StreamingResponse (text/plain)
```

### Request Schema

```json
{
    "message": "What are the key findings?"
}
```

### Response

Streaming text/plain response

---

## Summarize Document

**Route:** `POST /api/chat/{document_id}/summary`

**Purpose:** Generate a streaming summary of a document with configurable length

### Flow

```
1. Client Request
   └─> POST /api/chat/{document_id}/summary?length=normal
       └─> Query parameter: length (concise | normal | comprehensive)
           └─> Default: normal

2. Validation (app/api/routes/chat.py)
   │
   └─> Verify document exists
       └─> infra/database/queries.py: document_exists(document_id)
           ├─> If not found → 404 DOCUMENT_NOT_FOUND
           └─> If found → Continue

3. Stream Summary
   └─> domain/rag/streaming.py: stream_summary(document_id, length)

4. Retrieve All Document Chunks (domain/rag/retrieval.py)
   │
   └─> get_all_document_chunks(document_id)
       └─> SELECT ... WHERE document_id = %s ORDER BY chunk_index ASC
           └─> Returns all chunks in order

5. Build Context
   └─> Format all chunks into context string
       └─> "[Chunk 1]\n{content}\n\n---\n\n[Chunk 2]\n{content}"

6. Select Summary Prompt
   └─> Based on length parameter:
       │
       ├─> concise: 3-5 sentences
       │   └─> Focus on key points only
       │
       ├─> normal: 8-12 sentences (default)
       │   └─> Balanced overview
       │
       └─> comprehensive: 15-25 sentences
           └─> Detailed coverage

7. Generate Summary (domain/rag/model.py)
   │
   ├─> get_chat_model()
   ├─> Format summary prompt with full document context
   └─> Stream response from Ollama
       └─> Log performance metrics
           ├─> TTFT
           ├─> Tokens per second
           ├─> Document chunk count
           └─> Summary length

8. Stream to Client
   └─> StreamingResponse (text/plain)
       └─> Yield summary chunks as UTF-8 bytes
```

### Query Parameters

- `length` (optional): `concise` | `normal` | `comprehensive`
    - Default: `normal`

### Summary Characteristics

| Length        | Sentences | Focus                                    |
| ------------- | --------- | ---------------------------------------- |
| concise       | 3-5       | Most important key points only           |
| normal        | 8-12      | Main points and important details        |
| comprehensive | 15-25     | All major points with supporting details |

### Response

Streaming text/plain summary

---

## List Documents

**Route:** `GET /api/documents`

**Purpose:** Retrieve all indexed documents with metadata

### Flow

```
1. Client Request
   └─> GET /api/documents

2. Handler (app/api/routes/documents.py)
   └─> infra/database/queries.py: list_all_documents()

3. Database Query
   └─> SELECT id, filename, file_type, file_size, status, created_at
       FROM documents
       ORDER BY created_at DESC

4. Format Response
   └─> Convert rows to DocumentItem objects
       └─> Build DocumentsListResponse

5. Response
   └─> 200 OK with documents array and total count
```

### Response Schema

```json
{
    "success": true,
    "code": "DOCUMENTS_LIST_SUCCESS",
    "message": "Documents retrieved successfully",
    "data": {
        "documents": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
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

---

## Delete Document

**Route:** `DELETE /api/documents/{document_id}`

**Purpose:** Delete document and all associated chunks

### Flow

```
1. Client Request
   └─> DELETE /api/documents/{document_id}

2. Handler (app/api/routes/documents.py)
   └─> infra/database/queries.py: delete_document_by_id(document_id)

3. Database Operation
   │
   └─> DELETE FROM documents WHERE id = %s
       └─> ON DELETE CASCADE automatically deletes:
           └─> All associated chunks in document_chunks

4. Check Result
   ├─> If rowcount > 0 → Document deleted
   └─> If rowcount = 0 → 404 DOCUMENT_NOT_FOUND

5. Response
   └─> 200 OK (if deleted)
   └─> 404 NOT FOUND (if not found)
```

### Response Schema

```json
{
    "success": true,
    "code": "DOCUMENT_DELETED",
    "message": "Document deleted successfully",
    "data": null
}
```

---

## Common Error Responses

### 400 Bad Request

```json
{
    "code": "CHAT_EMPTY_MESSAGE",
    "message": "Message cannot be empty."
}
```

### 404 Not Found

```json
{
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Document with id {document_id} not found."
}
```

### 413 Request Entity Too Large

```json
{
    "code": "UPLOAD_FILE_TOO_LARGE",
    "message": "File size exceeds maximum allowed size of 10.0 MB."
}
```

### 429 Too Many Requests

```json
{
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again soon."
}
```

### 500 Internal Server Error

```json
{
    "code": "UPLOAD_PROCESSING_ERROR",
    "message": "Failed to process document: {error}"
}
```

---

## Performance Logging

All endpoints that perform RAG operations log performance metrics:

### Metrics Logged

- **Retrieval time**: Time to fetch and rank chunks
- **TTFT (Time to First Token)**: Time until LLM starts streaming
- **Tokens per second**: Generation speed
- **Total LLM time**: Complete generation time
- **Query length**: Input size
- **Chunk count**: Number of chunks retrieved
- **Sources**: Document references used

### Log Format

```
INFO Query received query_length=50 retrieval_time=0.123 document_id=...
INFO First token received sources=['doc.pdf:1:0'] ttft=0.456
INFO Streaming complete retrieval_time=0.123 llm_time=2.345 tokens_per_sec=45.6 ttft=0.456
```

---

## Security Features

### Input Validation

- Empty message checks
- Dangerous pattern detection (`<script`, `javascript:`, `onerror=`)
- File extension validation
- File size limits
- Filename sanitization

### Rate Limiting

Different limits per endpoint:

- Chat: 10 requests / 60 seconds
- Upload: 5 requests / 300 seconds
- Default: 30 requests / 60 seconds

### Error Handling

Consistent error format across all endpoints with specific error codes for debugging.
