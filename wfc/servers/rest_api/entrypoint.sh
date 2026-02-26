#!/bin/bash
set -euo pipefail

# ==============================================================
# WFC Knowledge Server Entrypoint
#
# IMPORTANT: --workers 1 is MANDATORY.
# asyncio.Lock is per-process. Multiple workers would break the
# locking invariant for concurrent KNOWLEDGE.md writes, leading
# to silent data corruption. Do NOT change this.
# ==============================================================

# Validate WFC_KNOWLEDGE_TOKEN
if [ -z "${WFC_KNOWLEDGE_TOKEN:-}" ]; then
    echo "FATAL: WFC_KNOWLEDGE_TOKEN environment variable is required" >&2
    exit 1
fi

if [ ${#WFC_KNOWLEDGE_TOKEN} -lt 32 ]; then
    echo "FATAL: WFC_KNOWLEDGE_TOKEN must be at least 32 characters (got ${#WFC_KNOWLEDGE_TOKEN})" >&2
    exit 1
fi

# Wait for ChromaDB to be ready
echo "Waiting for ChromaDB..."
CHROMA_HOST="${CHROMA_HOST:-chroma}"
CHROMA_PORT="${CHROMA_PORT:-8000}"
MAX_RETRIES=30
RETRY=0

while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -sf "http://${CHROMA_HOST}:${CHROMA_PORT}/api/v1/heartbeat" > /dev/null 2>&1; then
        echo "ChromaDB is ready!"
        break
    fi
    RETRY=$((RETRY + 1))
    echo "ChromaDB not ready yet (attempt $RETRY/$MAX_RETRIES)..."
    sleep 2
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo "WARNING: ChromaDB not reachable after $MAX_RETRIES attempts, starting anyway..."
fi

# TLS configuration
TLS_ARGS=""
if [ -n "${WFC_KNOWLEDGE_TLS_CERT:-}" ] && [ -n "${WFC_KNOWLEDGE_TLS_KEY:-}" ]; then
    echo "TLS enabled with provided cert/key"
    TLS_ARGS="--ssl-certfile=${WFC_KNOWLEDGE_TLS_CERT} --ssl-keyfile=${WFC_KNOWLEDGE_TLS_KEY}"
fi

echo "Starting WFC Knowledge Server on port 8420 (workers=1, MANDATORY)"

# shellcheck disable=SC2086
exec uvicorn wfc.servers.rest_api.main:app \
    --host 0.0.0.0 \
    --port 8420 \
    --workers 1 \
    --log-level info \
    --timeout-keep-alive 30 \
    $TLS_ARGS
