# Getting Started

## Initial Setup

1. Open a terminal and go to your project folder
2. Copy `.env.example` to `.env` and fill in all required values (database credentials, model names, etc.)
3. Run `make build` or `docker compose up -d --build` if you don't have make installed
4. When everything is finished, go into the Ollama container and run `ollama signin`

## SSL Certificate Setup (for local development)

5. Run `docker compose exec caddy cat /data/caddy/pki/authorities/local/root.crt > caddy-root.crt`
6. Upload this certificate in Keychain Access (MacOS) under System
7. Do the same for your browser, you can find this setting under: Privacy and security ➡️ Managing certificates ➡️ Custom ➡️ Import

## Testing the API

Once everything is running, you can test the API endpoints:

### Basic Health and Info Checks

```bash
# Check health
curl http://localhost/api/health

# Check API info
curl http://localhost/api
```

### Document Upload

```bash
# Upload a document
curl -X POST http://localhost/api/upload \
  -F "file=@/path/to/your/document.pdf"
```

### List Documents

```bash
# Get all indexed documents
curl http://localhost/api/documents
```

### Chat with Documents

```bash
# Chat across all documents
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is this document about?"}'

# Chat with a specific document
curl -X POST http://localhost/api/chat/123e4567-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the key findings?"}'
```

### Generate Document Summaries

```bash
# Generate normal length summary (default)
curl -X POST http://localhost/api/chat/123e4567-e89b-12d3-a456-426614174000/summary

# Generate concise summary (3-5 sentences)
curl -X POST http://localhost/api/chat/123e4567-e89b-12d3-a456-426614174000/summary?length=concise

# Generate comprehensive summary (15-25 sentences)
curl -X POST http://localhost/api/chat/123e4567-e89b-12d3-a456-426614174000/summary?length=comprehensive
```

### Delete Document

```bash
# Delete a document and all its chunks
curl -X DELETE http://localhost/api/documents/123e4567-e89b-12d3-a456-426614174000
```

## Summary Feature Use Cases

The summary endpoint is useful for:

- **Quick document overview**: Get the gist of a document without reading the full text
- **Document triage**: Quickly determine which documents are relevant to your needs
- **Report generation**: Create executive summaries of technical documents
- **Content review**: Assess document quality and relevance before deeper analysis

### Summary Length Guidelines

Choose the appropriate length based on your needs:

- **Concise** (`3-5 sentences`): Use when you need the absolute minimum - just the core topic and most critical point
- **Normal** (`8-12 sentences`): Default option for a balanced overview covering main points and key details
- **Comprehensive** (`15-25 sentences`): Use when you need thorough coverage of all major topics and supporting details

## Example Workflow

Here's a typical workflow using the API:

```bash
# 1. Upload a document
RESPONSE=$(curl -s -X POST http://localhost/api/upload \
  -F "file=@research_paper.pdf")

# 2. Extract the document ID
DOC_ID=$(echo $RESPONSE | jq -r '.data.document_id')

# 3. Generate a summary to get an overview
curl -X POST http://localhost/api/chat/$DOC_ID/summary?length=normal

# 4. Ask specific questions about the document
curl -X POST http://localhost/api/chat/$DOC_ID \
  -H "Content-Type: application/json" \
  -d '{"message": "What methodology was used in this research?"}'

# 5. Get more details on interesting sections
curl -X POST http://localhost/api/chat/$DOC_ID \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain the results in more detail"}'
```

## Important Security Note

**API documentation endpoints are disabled by default** for security reasons:

- `/api/docs` (Swagger UI)
- `/api/redoc` (ReDoc)
- `/api/openapi.json` (OpenAPI schema)

This prevents unauthorized users from discovering your API structure. Refer to the README.md file for the complete list of available endpoints and their usage.

If you need to enable documentation during development, modify `app/main.py` and change:

```python
app = FastAPI(
    title="RAG API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",               # Enable Swagger UI
    redoc_url="/api/redoc",             # Enable ReDoc
    openapi_url="/api/openapi.json",    # Enable OpenAPI schema
)
```

Then rebuild the backend container:

```bash
make build
```

## Detailed Documentation

For detailed flow diagrams and technical information about each endpoint, see:

- [`docs/endpoint-flows.md`](endpoint-flows.md) - Complete flow documentation for all endpoints
- [`README.md`](../README.md) - Full API reference and configuration guide
