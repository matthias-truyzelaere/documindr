#!/bin/sh
set -e

# ---------------------------------------------------------------
# Start Ollama server
# ---------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting Ollama server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ollama serve >/dev/null 2>&1 &
SERVER_PID=$!

cleanup() {
  echo ""
  echo "🛑 Shutting down Ollama server (PID $SERVER_PID)..."
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# ---------------------------------------------------------------
# Wait for Ollama API
# ---------------------------------------------------------------
echo "🕰️ Waiting for Ollama API to be ready..."

MAX_WAIT_SECONDS=300
WAITED=0

while ! ollama list >/dev/null 2>&1; do
  if [ "$WAITED" -ge "$MAX_WAIT_SECONDS" ]; then
    echo "❌ ERROR: Ollama API did not become ready within ${MAX_WAIT_SECONDS}s"
    exit 1
  fi
  sleep 3
  WAITED=$((WAITED + 3))
done

echo "✅ Ollama API is ready"
echo ""

# ---------------------------------------------------------------
# Build model list from environment variables
# ---------------------------------------------------------------
MODELS=""

if [ -n "$CHAT_MODEL" ]; then
  MODELS="$MODELS $CHAT_MODEL"
fi

if [ -n "$EMBEDDING_MODEL" ]; then
  MODELS="$MODELS $EMBEDDING_MODEL"
fi

# Normalize whitespace
MODELS=$(echo "$MODELS" | xargs || true)

if [ -z "$MODELS" ]; then
  echo "⚠️ No models specified in CHAT_MODEL or EMBEDDING_MODEL"
  echo ""
else
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📦 Pulling models: $MODELS"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  
  for model in $MODELS; do
    echo "📥 Pulling model: $model"
    if ollama pull "$model" 2>&1 | grep -E "success|pulling|100%|already" || true; then
      echo "✅ Successfully pulled: $model"
    else
      echo "❌ Failed to pull: $model" >&2
    fi
    echo ""
  done
fi

# ---------------------------------------------------------------
# Keep server running
# ---------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ All models ready. Ollama server is running..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

wait "$SERVER_PID"