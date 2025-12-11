# ---------------------------------------------------------------------------
# Builder stage: Install dependencies
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Install uv (ultra-fast Python package manager)
# ---------------------------------------------------------------------------
RUN pip install --no-cache-dir uv

# ---------------------------------------------------------------------------
# Force uv to use system Python (3.13)
# Without this, uv downloads Python 3.14 and breaks on onnxruntime.
# ---------------------------------------------------------------------------
ENV UV_NO_MANAGED_PYTHON=1

# ---------------------------------------------------------------------------
# Copy dependency files first (better layer caching)
# ---------------------------------------------------------------------------
COPY requirements.txt pyproject.toml uv.lock ./

# ---------------------------------------------------------------------------
# Install dependencies from uv.lock
# --frozen: fail if uv.lock does not match pyproject.toml
# This ensures fully reproducible builds.
# ---------------------------------------------------------------------------
RUN uv sync --frozen

# Remove unnecessary files from venv to reduce size
RUN find /app/.venv \( -type d -name "tests" -o -type d -name "test" -o -name "__pycache__" \) -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*.pyd" -o -name "*.c" -o -name "*.h" \) -delete && \
    rm -rf /app/.venv/lib/python*/site-packages/pip /app/.venv/lib/python*/site-packages/setuptools

# ---------------------------------------------------------------------------
# Runtime stage: Minimal production image
# ---------------------------------------------------------------------------
FROM python:3.13-slim

# Create non-root user first (before copying files)
RUN useradd -m -u 1000 fastapi && \
    mkdir -p /app /data && \
    chown fastapi:fastapi /app /data

WORKDIR /app

# ---------------------------------------------------------------------------
# Install system-level packages needed by "unstructured" and PDF parsing
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Switch to non-root user
USER fastapi

# ---------------------------------------------------------------------------
# Copy virtual environment from builder with correct ownership
# ---------------------------------------------------------------------------
COPY --from=builder --chown=fastapi:fastapi /app/.venv /app/.venv

# ---------------------------------------------------------------------------
# Copy application code with correct ownership
# ---------------------------------------------------------------------------
COPY --chown=fastapi:fastapi app ./app

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Don't write .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Don't buffer stdout/stderr
ENV PYTHONUNBUFFERED=1

# Expose backend port
EXPOSE 8000

# ---------------------------------------------------------------------------
# Run FastAPI using uvicorn
# ---------------------------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]