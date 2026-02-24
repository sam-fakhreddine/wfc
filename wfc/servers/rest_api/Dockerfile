FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
COPY wfc/ ./wfc/
RUN pip install --no-cache-dir -e ".[api]" && \
    pip install --no-cache-dir chromadb httpx sentence-transformers

# --- Runtime stage ---
FROM python:3.12-slim

RUN groupadd -r wfc && useradd -r -g wfc -m wfc

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Create data directory
RUN mkdir -p /data/wfc-knowledge && chown -R wfc:wfc /data/wfc-knowledge

COPY wfc/servers/rest_api/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER wfc

EXPOSE 8420

ENTRYPOINT ["/app/entrypoint.sh"]
