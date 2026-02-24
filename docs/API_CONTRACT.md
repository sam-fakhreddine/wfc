# WFC REST API - Complete Contract Specification

**Version:** 1.0.0
**Base URL:** `https://api.wfc.example.com` (production) or `http://localhost:9950` (development)
**Protocol:** HTTP/1.1, HTTP/2
**Authentication:** API Key (Bearer token)
**Content-Type:** `application/json`

---

## Table of Contents

- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [Projects](#projects)
  - [Reviews](#reviews)
  - [Resources](#resources)
- [Data Models](#data-models)
- [Status Codes](#status-codes)
- [Examples](#examples)

---

## Authentication

### API Key Authentication

All protected endpoints require an API key obtained from creating a project.

**Header Format:**

```http
X-Project-ID: <project_id>
Authorization: Bearer <api_key>
```

**Authentication Flow:**

1. Create a project via `POST /v1/projects/` (no auth required)
2. Receive `api_key` in response (store securely, cannot be retrieved later)
3. Include `X-Project-ID` and `Authorization` headers in subsequent requests

**Example:**

```http
POST /v1/reviews/ HTTP/1.1
Host: api.wfc.example.com
Content-Type: application/json
X-Project-ID: my-project
Authorization: Bearer wfc_sk_1234567890abcdef

{
  "diff_content": "...",
  "files": ["main.py"]
}
```

---

## Error Handling

### Standard Error Response

All errors return a consistent JSON structure:

```json
{
  "error": "ErrorType",
  "detail": "Human-readable error message",
  "request_id": "uuid-v4-optional"
}
```

### Error Types

| Error | HTTP Status | Description |
|-------|-------------|-------------|
| `ValidationError` | 422 | Request body validation failed |
| `Unauthorized` | 401 | Missing or invalid API key |
| `Forbidden` | 403 | Valid credentials but insufficient permissions |
| `NotFound` | 404 | Resource does not exist |
| `Conflict` | 409 | Resource already exists |
| `PayloadTooLarge` | 413 | Request body exceeds 1MB limit |
| `TooManyRequests` | 429 | Rate limit exceeded |
| `InternalServerError` | 500 | Unexpected server error |

---

## Rate Limiting

### Limits

- **TokenBucket (application layer):** 10 requests/second per project
- **Traefik (infrastructure layer):** 100-200 requests/second per IP (production)

### Rate Limit Headers

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1645564800
```

### Rate Limit Exceeded Response

**Status:** 429 Too Many Requests

```json
{
  "error": "TooManyRequests",
  "detail": "Rate limit exceeded. Retry after 5 seconds.",
  "retry_after": 5
}
```

---

## Endpoints

### Health Check

#### `GET /`

Check API health and availability.

**Authentication:** Not required

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

**Example:**

```bash
curl https://api.wfc.example.com/
```

---

### Projects

#### `POST /v1/projects/`

Create a new project and generate an API key.

**Authentication:** Not required

**Request Body:**

```json
{
  "project_id": "string",       // Required: alphanumeric + hyphens/underscores, 1-64 chars
  "developer_id": "string",     // Required: developer identifier
  "repo_path": "string"         // Required: absolute path to repository
}
```

**Validation Rules:**

- `project_id`: Must match `^[a-zA-Z0-9_-]{1,64}$`
- `repo_path`: Must be absolute path (starts with `/`)
- Unique constraint: `project_id` must be unique

**Response:** `201 Created`

```json
{
  "project_id": "my-project",
  "api_key": "wfc_sk_1234567890abcdef",
  "created_at": "2026-02-21T20:00:00Z"
}
```

**Errors:**

- `422 Unprocessable Entity` - Validation error
- `409 Conflict` - Project ID already exists

**Example:**

```bash
curl -X POST https://api.wfc.example.com/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-project",
    "developer_id": "alice",
    "repo_path": "/Users/alice/repos/my-project"
  }'
```

**Response:**

```json
{
  "project_id": "my-project",
  "api_key": "wfc_sk_a1b2c3d4e5f6g7h8",
  "created_at": "2026-02-21T20:15:30Z"
}
```

---

#### `GET /v1/projects/`

List all projects (without exposing API keys).

**Authentication:** Not required

**Response:** `200 OK`

```json
{
  "projects": [
    {
      "project_id": "project-1",
      "developer_id": "alice",
      "created_at": "2026-02-20T10:00:00Z"
    },
    {
      "project_id": "project-2",
      "developer_id": "bob",
      "created_at": "2026-02-21T15:30:00Z"
    }
  ],
  "total": 2
}
```

**Example:**

```bash
curl https://api.wfc.example.com/v1/projects/
```

---

### Reviews

#### `POST /v1/reviews/`

Submit code for review (async operation).

**Authentication:** Required

**Request Body:**

```json
{
  "diff_content": "string",     // Required: Git diff content, min length 1
  "files": ["string"]           // Optional: List of changed files, defaults to []
}
```

**Validation Rules:**

- `diff_content`: Non-empty string
- `files`: Array of non-empty strings (no whitespace-only values)

**Response:** `202 Accepted`

```json
{
  "review_id": "uuid-v4",
  "status": "pending",
  "submitted_at": "2026-02-21T20:00:00Z",
  "project_id": "my-project"
}
```

**Errors:**

- `401 Unauthorized` - Missing or invalid API key
- `422 Unprocessable Entity` - Validation error (empty diff, invalid files)
- `429 Too Many Requests` - Rate limit exceeded

**Example:**

```bash
curl -X POST https://api.wfc.example.com/v1/reviews/ \
  -H "Content-Type: application/json" \
  -H "X-Project-ID: my-project" \
  -H "Authorization: Bearer wfc_sk_a1b2c3d4e5f6g7h8" \
  -d '{
    "diff_content": "diff --git a/main.py b/main.py\nindex 1234567..abcdefg 100644\n--- a/main.py\n+++ b/main.py\n@@ -1,3 +1,4 @@\n+import os\n def main():\n     print(\"Hello\")",
    "files": ["main.py"]
  }'
```

**Response:**

```json
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "submitted_at": "2026-02-21T20:16:45Z",
  "project_id": "my-project"
}
```

---

#### `GET /v1/reviews/{review_id}`

Get review status and results.

**Authentication:** Required

**Path Parameters:**

- `review_id` (string): UUID of the review

**Response:** `200 OK`

**Status: Pending**

```json
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "project_id": "my-project",
  "developer_id": "alice",
  "submitted_at": "2026-02-21T20:00:00Z",
  "completed_at": null,
  "consensus_score": null,
  "passed": null,
  "findings": null
}
```

**Status: In Progress**

```json
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "project_id": "my-project",
  "developer_id": "alice",
  "submitted_at": "2026-02-21T20:00:00Z",
  "completed_at": null,
  "consensus_score": null,
  "passed": null,
  "findings": null
}
```

**Status: Completed**

```json
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "project_id": "my-project",
  "developer_id": "alice",
  "submitted_at": "2026-02-21T20:00:00Z",
  "completed_at": "2026-02-21T20:05:30Z",
  "consensus_score": 8.7,
  "passed": true,
  "findings": [
    {
      "severity": "medium",
      "category": "security",
      "title": "Potential SQL injection vulnerability",
      "description": "User input is concatenated directly into SQL query without parameterization.",
      "file": "main.py",
      "line": 42,
      "suggestion": "Use parameterized queries or an ORM to prevent SQL injection.",
      "confidence": 95
    },
    {
      "severity": "low",
      "category": "style",
      "title": "Missing docstring",
      "description": "Function `process_data` lacks a docstring.",
      "file": "main.py",
      "line": 15,
      "suggestion": "Add a docstring describing parameters, return value, and purpose.",
      "confidence": 100
    }
  ]
}
```

**Status: Failed**

```json
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "project_id": "my-project",
  "developer_id": "alice",
  "submitted_at": "2026-02-21T20:00:00Z",
  "completed_at": "2026-02-21T20:01:15Z",
  "consensus_score": null,
  "passed": false,
  "error": "Review execution timeout after 10 minutes"
}
```

**Errors:**

- `401 Unauthorized` - Missing or invalid API key
- `403 Forbidden` - Review belongs to different project
- `404 Not Found` - Review does not exist

**Example:**

```bash
curl https://api.wfc.example.com/v1/reviews/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-Project-ID: my-project" \
  -H "Authorization: Bearer wfc_sk_a1b2c3d4e5f6g7h8"
```

---

### Resources

#### `GET /v1/resources/pool`

Get worktree pool status and metrics.

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "max_worktrees": 10,
  "current_usage": 3,
  "available": 7,
  "in_use": [
    {
      "worktree_id": "wfc-task-001",
      "project_id": "my-project",
      "created_at": "2026-02-21T19:00:00Z",
      "last_used": "2026-02-21T20:00:00Z"
    },
    {
      "worktree_id": "wfc-task-002",
      "project_id": "other-project",
      "created_at": "2026-02-21T19:30:00Z",
      "last_used": "2026-02-21T19:45:00Z"
    },
    {
      "worktree_id": "wfc-task-003",
      "project_id": "my-project",
      "created_at": "2026-02-21T20:00:00Z",
      "last_used": "2026-02-21T20:00:00Z"
    }
  ],
  "orphaned_count": 1
}
```

**Errors:**

- `401 Unauthorized` - Missing or invalid API key

**Example:**

```bash
curl https://api.wfc.example.com/v1/resources/pool \
  -H "X-Project-ID: my-project" \
  -H "Authorization: Bearer wfc_sk_a1b2c3d4e5f6g7h8"
```

---

#### `GET /v1/resources/rate-limit`

Get rate limit status for the current project.

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "capacity": 10,
  "available_tokens": 7.5,
  "refill_rate": 10.0,
  "next_refill_at": "2026-02-21T20:00:01Z"
}
```

**Errors:**

- `401 Unauthorized` - Missing or invalid API key

**Example:**

```bash
curl https://api.wfc.example.com/v1/resources/rate-limit \
  -H "X-Project-ID: my-project" \
  -H "Authorization: Bearer wfc_sk_a1b2c3d4e5f6g7h8"
```

---

## Data Models

### Project

```typescript
interface Project {
  project_id: string;        // Unique project identifier (alphanumeric + -_)
  developer_id: string;      // Developer identifier
  created_at: string;        // ISO 8601 timestamp
}
```

### ProjectCreateRequest

```typescript
interface ProjectCreateRequest {
  project_id: string;        // Required: 1-64 chars, alphanumeric + -_
  developer_id: string;      // Required: developer identifier
  repo_path: string;         // Required: absolute path
}
```

### ProjectCreateResponse

```typescript
interface ProjectCreateResponse {
  project_id: string;        // Project identifier
  api_key: string;           // Generated API key (SHA-256 hashed before storage)
  created_at: string;        // ISO 8601 timestamp
}
```

### ReviewSubmitRequest

```typescript
interface ReviewSubmitRequest {
  diff_content: string;      // Required: Git diff content, min length 1
  files: string[];           // Optional: Changed files, defaults to []
}
```

### ReviewSubmitResponse

```typescript
interface ReviewSubmitResponse {
  review_id: string;         // UUID v4
  status: ReviewStatus;      // Always "pending" on submit
  submitted_at: string;      // ISO 8601 timestamp
  project_id: string;        // Project identifier
}
```

### ReviewStatusResponse

```typescript
interface ReviewStatusResponse {
  review_id: string;         // UUID v4
  status: ReviewStatus;      // Current status
  project_id: string;        // Project identifier
  developer_id: string;      // Developer identifier
  submitted_at: string;      // ISO 8601 timestamp
  completed_at: string | null;  // ISO 8601 timestamp or null
  consensus_score: number | null;  // 0-10 or null
  passed: boolean | null;    // true/false/null
  findings: ReviewFinding[] | null;  // Array or null
  error?: string;            // Present only if status === "failed"
}
```

### ReviewStatus

```typescript
enum ReviewStatus {
  PENDING = "pending",           // Queued, not yet started
  IN_PROGRESS = "in_progress",   // Currently being reviewed
  COMPLETED = "completed",       // Review finished successfully
  FAILED = "failed"              // Review failed (timeout, error)
}
```

### ReviewFinding

```typescript
interface ReviewFinding {
  severity: "critical" | "high" | "medium" | "low" | "info";
  category: string;              // e.g., "security", "performance", "style"
  title: string;                 // Brief title
  description: string;           // Detailed description
  file: string;                  // File path
  line: number | null;           // Line number or null
  suggestion: string;            // How to fix
  confidence: number;            // 0-100
}
```

### PoolStatusResponse

```typescript
interface PoolStatusResponse {
  max_worktrees: number;         // Maximum pool size
  current_usage: number;         // Currently active worktrees
  available: number;             // Available slots
  in_use: WorktreeInfo[];        // Active worktrees
  orphaned_count: number;        // Count of orphaned worktrees (>24h old)
}
```

### WorktreeInfo

```typescript
interface WorktreeInfo {
  worktree_id: string;           // Worktree identifier
  project_id: string;            // Associated project
  created_at: string;            // ISO 8601 timestamp
  last_used: string;             // ISO 8601 timestamp
}
```

### RateLimitStatusResponse

```typescript
interface RateLimitStatusResponse {
  capacity: number;              // Maximum bucket capacity (10)
  available_tokens: number;      // Current available tokens
  refill_rate: number;           // Tokens per second (10.0)
  next_refill_at: string;        // ISO 8601 timestamp
}
```

### ErrorResponse

```typescript
interface ErrorResponse {
  error: string;                 // Error type
  detail: string;                // Human-readable message
  request_id?: string;           // Optional request ID
  retry_after?: number;          // Seconds to wait (429 only)
}
```

---

## Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for async processing |
| 400 | Bad Request | Malformed request syntax |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource already exists |
| 413 | Payload Too Large | Request body exceeds 1MB |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Server temporarily unavailable |

---

## Examples

### Complete Workflow Example

```bash
# 1. Create a project
PROJECT_RESPONSE=$(curl -X POST https://api.wfc.example.com/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-awesome-project",
    "developer_id": "alice",
    "repo_path": "/Users/alice/repos/my-awesome-project"
  }')

# Extract API key (using jq)
API_KEY=$(echo $PROJECT_RESPONSE | jq -r '.api_key')
echo "API Key: $API_KEY"  # Save this securely!

# 2. Submit code for review
REVIEW_RESPONSE=$(curl -X POST https://api.wfc.example.com/v1/reviews/ \
  -H "Content-Type: application/json" \
  -H "X-Project-ID: my-awesome-project" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "diff_content": "diff --git a/app.py b/app.py\nindex 1234567..abcdefg 100644\n--- a/app.py\n+++ b/app.py\n@@ -10,7 +10,8 @@\n def process():\n-    query = \"SELECT * FROM users WHERE id=\" + user_id\n+    query = \"SELECT * FROM users WHERE id=%s\"\n+    cursor.execute(query, (user_id,))",
    "files": ["app.py"]
  }')

# Extract review ID
REVIEW_ID=$(echo $REVIEW_RESPONSE | jq -r '.review_id')
echo "Review ID: $REVIEW_ID"

# 3. Poll for review status (every 5 seconds)
while true; do
  STATUS_RESPONSE=$(curl https://api.wfc.example.com/v1/reviews/$REVIEW_ID \
    -H "X-Project-ID: my-awesome-project" \
    -H "Authorization: Bearer $API_KEY")

  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  echo "Status: $STATUS"

  if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
    echo $STATUS_RESPONSE | jq '.'
    break
  fi

  sleep 5
done

# 4. Check resource usage
curl https://api.wfc.example.com/v1/resources/pool \
  -H "X-Project-ID: my-awesome-project" \
  -H "Authorization: Bearer $API_KEY" | jq '.'

curl https://api.wfc.example.com/v1/resources/rate-limit \
  -H "X-Project-ID: my-awesome-project" \
  -H "Authorization: Bearer $API_KEY" | jq '.'
```

### Python Client Example

```python
import requests
import time
from typing import Optional

class WFCClient:
    def __init__(self, base_url: str = "https://api.wfc.example.com"):
        self.base_url = base_url
        self.project_id: Optional[str] = None
        self.api_key: Optional[str] = None

    def create_project(self, project_id: str, developer_id: str, repo_path: str):
        """Create a new project and store credentials."""
        response = requests.post(
            f"{self.base_url}/v1/projects/",
            json={
                "project_id": project_id,
                "developer_id": developer_id,
                "repo_path": repo_path
            }
        )
        response.raise_for_status()
        data = response.json()

        self.project_id = data["project_id"]
        self.api_key = data["api_key"]
        return data

    def submit_review(self, diff_content: str, files: list[str] = None):
        """Submit code for review."""
        response = requests.post(
            f"{self.base_url}/v1/reviews/",
            headers={
                "X-Project-ID": self.project_id,
                "Authorization": f"Bearer {self.api_key}"
            },
            json={
                "diff_content": diff_content,
                "files": files or []
            }
        )
        response.raise_for_status()
        return response.json()

    def get_review_status(self, review_id: str):
        """Get review status."""
        response = requests.get(
            f"{self.base_url}/v1/reviews/{review_id}",
            headers={
                "X-Project-ID": self.project_id,
                "Authorization": f"Bearer {self.api_key}"
            }
        )
        response.raise_for_status()
        return response.json()

    def wait_for_review(self, review_id: str, poll_interval: int = 5):
        """Wait for review to complete."""
        while True:
            status = self.get_review_status(review_id)
            if status["status"] in ["completed", "failed"]:
                return status
            time.sleep(poll_interval)

# Usage
client = WFCClient()

# Create project
project = client.create_project(
    project_id="my-project",
    developer_id="alice",
    repo_path="/Users/alice/repos/my-project"
)
print(f"API Key: {project['api_key']}")  # Save securely!

# Submit review
review = client.submit_review(
    diff_content="diff --git a/main.py ...",
    files=["main.py"]
)
print(f"Review submitted: {review['review_id']}")

# Wait for completion
result = client.wait_for_review(review["review_id"])
print(f"Review completed: {result['consensus_score']}")
print(f"Findings: {len(result['findings'])}")
```

---

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:

- **Interactive docs:** `https://api.wfc.example.com/docs`
- **ReDoc:** `https://api.wfc.example.com/redoc`
- **OpenAPI JSON:** `https://api.wfc.example.com/openapi.json`

---

## Versioning

**Current Version:** 1.0.0

API versioning follows semantic versioning (semver):

- **Major version** (v1, v2): Breaking changes
- **Minor version** (1.1, 1.2): New features, backward compatible
- **Patch version** (1.0.1, 1.0.2): Bug fixes, backward compatible

Version is specified in URL path: `/v1/reviews/`

---

## Changelog

### v1.0.0 (2026-02-21)

- Initial release
- Project management endpoints
- Review submission and status
- Resource monitoring endpoints
- API key authentication
- Rate limiting (10 req/s per project)
- Multi-tenant isolation
