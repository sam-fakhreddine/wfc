# Logging Migration Guide

Guide for migrating from Python's stdlib `logging` to WFC's centralized logging.

## Overview

**Migration effort**: Low (simple find-and-replace in most cases)
**Breaking changes**: None (fallback to stdlib available)
**Rollout strategy**: Gradual with feature flag

## Quick Migration

### Before

```python
import logging

logger = logging.getLogger(__name__)

def process_request(request_id):
    logger.info(f"Processing request {request_id}")
```

### After

```python
from wfc.shared.logging import get_logger
from wfc.shared.logging.context import request_context

logger = get_logger(__name__)

def process_request(request_id):
    with request_context():
        logger.info("Processing request")
        # request_id automatically included
```

## Step-by-Step Migration

### Step 1: Update Imports

**Find:**

```python
import logging
```

**Replace with:**

```python
from wfc.shared.logging import get_logger
```

### Step 2: Update Logger Creation

**Find:**

```python
logger = logging.getLogger(__name__)
```

**Replace with:**

```python
logger = get_logger(__name__)
```

### Step 3: Add Request Context (Optional)

For request-scoped logging (recommended for APIs):

```python
from wfc.shared.logging.context import request_context

# In middleware or request handler
with request_context() as request_id:
    logger.info("Request started")
    # ... process request ...
    logger.info("Request completed")
```

### Step 4: Add Performance Timing (Optional)

For performance-critical functions:

```python
from wfc.shared.logging.decorators import log_execution_time

@log_execution_time
def expensive_operation():
    # Automatically logs execution time
    pass
```

## Common Patterns

### Pattern 1: Simple Logger

**Before:**

```python
import logging

logger = logging.getLogger("myapp.service")

class MyService:
    def process(self):
        logger.info("Processing")
```

**After:**

```python
from wfc.shared.logging import get_logger

logger = get_logger("myapp.service")

class MyService:
    def process(self):
        logger.info("Processing")
```

### Pattern 2: Logger with Context

**Before:**

```python
import logging

logger = logging.getLogger(__name__)

def handle_request(request_id):
    logger.info(f"[{request_id}] Processing request")
    process_data(request_id)
    logger.info(f"[{request_id}] Request complete")

def process_data(request_id):
    logger.debug(f"[{request_id}] Processing data")
```

**After:**

```python
from wfc.shared.logging import get_logger
from wfc.shared.logging.context import request_context, set_request_id

logger = get_logger(__name__)

def handle_request(request_id):
    set_request_id(request_id)  # Or use request_context() to generate
    logger.info("Processing request")
    process_data()
    logger.info("Request complete")

def process_data():
    logger.debug("Processing data")
    # request_id automatically included
```

### Pattern 3: Logger with Secrets

**Before:**

```python
import logging
import re

logger = logging.getLogger(__name__)

def authenticate(api_key):
    # Manual redaction
    safe_key = re.sub(r'wfc_[a-z0-9]+', '[REDACTED]', api_key)
    logger.info(f"Authenticating with key: {safe_key}")
```

**After:**

```python
from wfc.shared.logging import get_logger

logger = get_logger(__name__)

def authenticate(api_key):
    # Automatic redaction
    logger.info(f"Authenticating with key: {api_key}")
    # Logs: "Authenticating with key: [REDACTED]"
```

### Pattern 4: Performance Logging

**Before:**

```python
import logging
import time

logger = logging.getLogger(__name__)

def process():
    start = time.perf_counter()
    # ... do work ...
    duration = (time.perf_counter() - start) * 1000
    logger.info(f"Processing took {duration:.2f}ms")
```

**After:**

```python
from wfc.shared.logging.decorators import log_execution_time

@log_execution_time
def process():
    # ... do work ...
    # Automatically logs: "Completed process in Xms"
```

### Pattern 5: Structured Logging

**Before:**

```python
import logging
import json

logger = logging.getLogger(__name__)

def log_event(user_id, action):
    logger.info(json.dumps({
        "user_id": user_id,
        "action": action,
        "timestamp": datetime.now().isoformat()
    }))
```

**After:**

```python
from wfc.shared.logging import get_logger

logger = get_logger(__name__)

def log_event(user_id, action):
    logger.info(
        "User action",
        extra={
            "user_id": user_id,
            "action": action
        }
    )
    # timestamp automatically added in JSON format
```

## FastAPI Migration

### Before

```python
import logging
from fastapi import FastAPI

app = FastAPI()
logger = logging.getLogger(__name__)

@app.get("/users/{user_id}")
def get_user(user_id: str):
    logger.info(f"Getting user {user_id}")
    return {"user_id": user_id}
```

### After

```python
from fastapi import FastAPI
from wfc.shared.logging import get_logger
from wfc.shared.logging.context import request_context

app = FastAPI()
logger = get_logger(__name__)

@app.middleware("http")
async def logging_middleware(request, call_next):
    with request_context():
        response = await call_next(request)
        return response

@app.get("/users/{user_id}")
def get_user(user_id: str):
    logger.info("Getting user", extra={"user_id": user_id})
    return {"user_id": user_id}
```

## MCP Server Migration

### Before

```python
import logging

logger = logging.getLogger(__name__)

class MCPServer:
    def handle_connection(self, session_id):
        logger.info(f"[{session_id}] Connection established")
```

### After

```python
from wfc.shared.logging import get_logger
from wfc.shared.logging.context import request_context

logger = get_logger(__name__)

class MCPServer:
    def handle_connection(self, session_id):
        # Use request_context for session tracking
        with request_context() as session_id:
            logger.info("Connection established")
            # session_id automatically included
```

## Testing

### Unit Tests

**Before:**

```python
import logging

def test_logging(caplog):
    logger = logging.getLogger("test")
    logger.info("Test message")
    assert "Test message" in caplog.text
```

**After:**

```python
from wfc.shared.logging import get_logger

def test_logging(caplog, monkeypatch):
    # Set LOG_LEVEL for tests
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    logger = get_logger("test")
    with caplog.at_level(logging.DEBUG, logger="wfc"):
        logger.info("Test message")
        assert "Test message" in caplog.text
```

### Integration Tests

```python
import pytest
from wfc.shared.logging import get_logger
from wfc.shared.logging.context import request_context

@pytest.fixture(autouse=True)
def clear_logger_cache(monkeypatch):
    """Clear logger cache between tests."""
    import wfc.shared.logging

    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    wfc.shared.logging._logger_cache.clear()
    yield
    wfc.shared.logging._logger_cache.clear()

def test_with_request_context(caplog):
    logger = get_logger("test")

    with caplog.at_level(logging.DEBUG, logger="wfc"):
        with request_context() as request_id:
            logger.info("Test")
            # Check request_id in logs
            assert any(r.request_id == request_id for r in caplog.records)
```

## Rollout Strategy

### Phase 1: Deploy with Feature Flag Off

```bash
# Set in environment
export USE_CENTRALIZED_LOGGING=false

# Deploy code
# No behavioral changes - uses stdlib logging
```

### Phase 2: Enable in Development

```bash
# Development environment
export USE_CENTRALIZED_LOGGING=true
export ENV=development
export LOG_LEVEL=DEBUG

# Test and validate
```

### Phase 3: Enable in Staging

```bash
# Staging environment
export USE_CENTRALIZED_LOGGING=true
export ENV=production
export LOG_FORMAT=json

# Monitor for issues
```

### Phase 4: Gradual Production Rollout

```bash
# Canary deployment (10%)
export USE_CENTRALIZED_LOGGING=true

# Monitor metrics:
# - Log volume
# - Application performance
# - Secret sanitization effectiveness

# Scale to 50%, then 100%
```

## Validation Checklist

- [ ] All `logging.getLogger()` calls replaced with `get_logger()`
- [ ] Request context added to API endpoints
- [ ] Performance decorators added to critical functions
- [ ] Tests updated to use `caplog` with `logger="wfc"`
- [ ] Environment variables configured
- [ ] Secret sanitization verified (no secrets in logs)
- [ ] Log output format verified (JSON in production)
- [ ] Performance overhead measured (<5ms)

## Troubleshooting

### Issue: Logs not appearing after migration

**Cause**: Feature flag disabled or wrong logger name

**Solution**:

```bash
# Check feature flag
echo $USE_CENTRALIZED_LOGGING

# Should be "true" (default)
export USE_CENTRALIZED_LOGGING=true

# Check logger names in code
# Should use get_logger(__name__), not logging.getLogger()
```

### Issue: Request ID not appearing in logs

**Cause**: Missing request_context

**Solution**:

```python
# Add request context wrapper
with request_context():
    logger.info("Message")  # Now includes request_id
```

### Issue: Tests failing with caplog

**Cause**: Logger cache or missing "wfc" logger filter

**Solution**:

```python
# Add to test
with caplog.at_level(logging.DEBUG, logger="wfc"):
    # Test code here
```

### Issue: Performance degradation

**Cause**: Excessive DEBUG logging in production

**Solution**:

```bash
# Set appropriate log level
export LOG_LEVEL=INFO  # or WARNING
```

## Rollback Plan

If issues arise:

```bash
# Disable centralized logging
export USE_CENTRALIZED_LOGGING=false

# Falls back to stdlib logging immediately
# No code changes needed
```

## Support

For issues or questions:

1. Check [LOGGING.md](../concepts/LOGGING.md) for usage patterns
2. Review [sanitizer.py](../../wfc/shared/logging/sanitizer.py) for secret patterns
3. See test examples in `tests/shared/logging/`

## Next Steps

After migration:

1. Add request context to all request handlers
2. Add performance decorators to slow functions
3. Review logs in SIEM for structured data
4. Set up alerts for ERROR level logs
5. Monitor secret sanitization effectiveness
