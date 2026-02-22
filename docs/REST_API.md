# WFC REST API

Multi-tenant code review and project management API.

## Quick Start

### 1. Start the Server

```bash
uv run uvicorn wfc.servers.rest_api.main:app --host 0.0.0.0 --port 9950
```

Or with Docker:

```bash
docker compose -f docker-compose.rest-api.yml up
```

### 2. Create a Project

```bash
curl -X POST http://localhost:9950/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-project",
    "developer_id": "alice",
    "repo_path": "/absolute/path/to/repo"
  }'
```

Response (201 Created):

```json
{
  "project_id": "my-project",
  "api_key": "generated-api-key-here",
  "created_at": "2026-02-21T14:00:00Z"
}
```

**IMPORTANT**: Store the API key securely. It cannot be retrieved later.

### 3. Submit a Code Review

```bash
curl -X POST http://localhost:9950/v1/reviews/ \
  -H "Content-Type: application/json" \
  -H "X-Project-ID: my-project" \
  -H "Authorization: Bearer <api-key>" \
  -d '{
    "diff_content": "diff content here",
    "files": ["file1.py", "file2.py"]
  }'
```

Response (202 Accepted):

```json
{
  "review_id": "uuid-here",
  "status": "pending",
  "submitted_at": "2026-02-21T14:00:00Z",
  "project_id": "my-project"
}
```

### 4. Check Review Status

```bash
curl -X GET http://localhost:9950/v1/reviews/<review-id> \
  -H "X-Project-ID: my-project" \
  -H "Authorization: Bearer <api-key>"
```

Response (200 OK):

```json
{
  "review_id": "uuid",
  "status": "completed",
  "project_id": "my-project",
  "developer_id": "alice",
  "submitted_at": "2026-02-21T14:00:00Z",
  "completed_at": "2026-02-21T14:05:00Z",
  "consensus_score": 8.5,
  "passed": true,
  "findings": [...]
}
```

## Endpoints

### Projects

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/v1/projects/` | Create new project | No |
| GET | `/v1/projects/` | List all projects | No |

### Reviews

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/v1/reviews/` | Submit code for review | Yes |
| GET | `/v1/reviews/{review_id}` | Get review status | Yes |

### Resources

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/v1/resources/pool` | Worktree pool status | Yes |
| GET | `/v1/resources/rate-limit` | Rate limit status | Yes |

### Health

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/` | Health check | No |

## Authentication

All endpoints marked "Auth Required" need two headers:

- `X-Project-ID`: Your project ID
- `Authorization`: `Bearer <api-key>`

API keys are generated when creating a project and stored as SHA-256 hashes.
They cannot be retrieved after creation -- store them securely.

## Rate Limiting

- **Capacity**: 10 requests per burst
- **Refill rate**: 10 tokens/second
- Returns `429 Too Many Requests` when exceeded

## Review Lifecycle

```text
PENDING --> IN_PROGRESS --> COMPLETED (with consensus_score + findings)
                       \-> FAILED (with error_message)
```

Reviews execute asynchronously via 5-agent consensus review.
Poll `GET /v1/reviews/{review_id}` to check progress.

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "detail": "Additional details",
  "timestamp": "2026-02-21T14:00:00Z"
}
```

| Status Code | Meaning |
|-------------|---------|
| 401 | Invalid or missing API key |
| 403 | Accessing another project's resources |
| 404 | Resource not found |
| 409 | Duplicate project |
| 413 | Request body too large (>1MB) |
| 422 | Validation error (invalid input) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## OpenAPI Documentation

Interactive API docs are available at:

- Swagger UI: `http://localhost:9950/docs`
- ReDoc: `http://localhost:9950/redoc`
- OpenAPI JSON: `http://localhost:9950/openapi.json`
