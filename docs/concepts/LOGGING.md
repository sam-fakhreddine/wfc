# Centralized Logging

WFC's centralized logging infrastructure provides structured, secure logging with:

- Secret sanitization
- Request/session ID tracking
- SIEM-compatible JSON output
- Environment-based configuration
- Performance monitoring

## Quick Start

```python
from wfc.shared.logging import get_logger
from wfc.shared.logging.context import request_context
from wfc.shared.logging.decorators import log_execution_time

# Get a logger
logger = get_logger(__name__)

# Basic logging
logger.info("Processing request", extra={"user_id": "123"})

# With request context
with request_context() as request_id:
    logger.info("Request started")
    # All logs in this context will include request_id

# Performance timing
@log_execution_time
def process_data():
    # Automatically logs execution time
    pass
```

## Architecture

```
wfc/shared/logging/
├── config.py          # Environment-based configuration
├── sanitizer.py       # Secret detection and redaction
├── formatters.py      # JSON and console formatters
├── context.py         # Request/session ID tracking
├── decorators.py      # Performance timing decorators
└── __init__.py        # Logger factory
```

## Configuration

### Environment Variables

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `USE_CENTRALIZED_LOGGING` | true/false | true | Enable centralized logging |
| `LOG_LEVEL` | DEBUG/INFO/WARNING/ERROR | INFO | Minimum log level |
| `LOG_FORMAT` | json/console | auto | Output format (auto = json in production, console in development) |
| `ENV` | development/production | development | Environment type |

### Examples

```bash
# Development (console output, DEBUG level)
export ENV=development
export LOG_LEVEL=DEBUG

# Production (JSON output, INFO level)
export ENV=production
export LOG_LEVEL=INFO

# Disable centralized logging (fallback to stdlib)
export USE_CENTRALIZED_LOGGING=false
```

## Usage Patterns

### Basic Logging

```python
from wfc.shared.logging import get_logger

logger = get_logger(__name__)

# Standard log levels
logger.debug("Detailed debugging information")
logger.info("General informational message")
logger.warning("Warning: something unexpected")
logger.error("Error occurred", exc_info=True)

# With extra context
logger.info(
    "User login successful",
    extra={
        "user_id": "user-123",
        "ip_address": "192.168.1.1",
        "login_method": "oauth"
    }
)
```

### Request Context Tracking

```python
from wfc.shared.logging import get_logger
from wfc.shared.logging.context import request_context, get_request_id

logger = get_logger(__name__)

# Automatic request ID generation
with request_context() as request_id:
    logger.info("Processing request")
    # Logs will include request_id automatically

    # Get current request ID
    current_id = get_request_id()
    assert current_id == request_id
```

### Performance Timing

```python
from wfc.shared.logging.decorators import log_execution_time
import logging

# Default: DEBUG level
@log_execution_time
def process_order(order_id):
    # Logs: "Executing process_order" and "Completed process_order in Xms"
    pass

# Custom log level
@log_execution_time(level=logging.INFO)
async def async_operation():
    # Works with async functions too
    await some_async_task()
```

### FastAPI Integration

```python
from fastapi import FastAPI, Request
from wfc.shared.logging import get_logger
from wfc.shared.logging.context import request_context

app = FastAPI()
logger = get_logger(__name__)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    with request_context() as request_id:
        # All logs in this request will have the same request_id
        logger.info(f"Request started", extra={
            "method": request.method,
            "path": request.url.path
        })

        response = await call_next(request)

        logger.info(f"Request completed", extra={
            "status_code": response.status_code
        })

        return response
```

## Output Formats

### JSON Format (Production)

```json
{
  "timestamp": "2026-02-22T12:34:56.789Z",
  "level": "INFO",
  "logger": "wfc.api.routes",
  "message": "Request processed successfully",
  "request_id": "abc-123-def-456",
  "module": "routes",
  "function": "process_request",
  "line_number": 42,
  "user_id": "user-123",
  "duration_ms": 15.23
}
```

### Console Format (Development)

```
[2026-02-22 12:34:56] INFO     wfc.api.routes: Request processed successfully
```

## Secret Sanitization

### Protected Patterns

The sanitizer automatically redacts:

1. **API Keys**: `wfc_*`, `sk_*`
2. **Bearer Tokens**: `Bearer <token>`
3. **JWT Tokens**: `eyJhbGc...` (3-segment format)
4. **WFC Paths**: `/path/to/.wfc/secret.json`
5. **Control Characters**: `\n`, `\r`, etc. (prevents log injection)

### Examples

```python
logger.info("API key: wfc_abc123")
# Logs: "API key: [REDACTED]"

logger.info("Token: Bearer xyz789")
# Logs: "Token: [REDACTED]"

logger.info("Config: /home/user/.wfc/config.json")
# Logs: "Config: [REDACTED_PATH]"

logger.info("User input: line1\nline2")
# Logs: "User input: line1\\nline2"
```

## SIEM Schema

All JSON logs conform to this schema for SIEM compatibility:

```typescript
interface LogEntry {
  timestamp: string;        // ISO 8601 format
  level: string;            // DEBUG | INFO | WARNING | ERROR
  logger: string;           // Logger name (wfc.*)
  message: string;          // Sanitized message
  request_id?: string;      // Request/session tracking
  module: string;           // Source module
  function: string;         // Source function
  line_number: number;      // Source line
  [key: string]: any;       // Extra context fields
}
```

### SIEM Integration

```bash
# Splunk
# Forward logs to Splunk HTTP Event Collector
export LOG_FORMAT=json
python app.py | splunk-forwarder

# Elasticsearch
# Use Filebeat to ship logs
filebeat -e -c filebeat.yml

# CloudWatch
# Use AWS CloudWatch agent
aws logs put-log-events --log-stream-name app
```

## Performance

### Overhead Measurements

- Logger creation: <5ms (cached after first creation)
- Log call overhead: <0.1ms per call
- Decorator overhead: <1ms per function call
- Secret sanitization: <0.01ms per message

### Best Practices

1. **Use appropriate log levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General operational events
   - WARNING: Unexpected but handled situations
   - ERROR: Errors that need attention

2. **Avoid logging in tight loops**:

   ```python
   # Bad
   for item in large_list:
       logger.debug(f"Processing {item}")

   # Good
   logger.info(f"Processing {len(large_list)} items")
   for item in large_list:
       process(item)
   logger.info("Processing complete")
   ```

3. **Use extra fields for structured data**:

   ```python
   # Good
   logger.info("Order placed", extra={
       "order_id": order.id,
       "total": order.total,
       "items": len(order.items)
   })
   ```

4. **Let sanitizer handle secrets**:

   ```python
   # Don't worry about manual redaction
   logger.info(f"Using API key: {api_key}")  # Automatically redacted
   ```

## Troubleshooting

### Logs not appearing

Check:

1. `USE_CENTRALIZED_LOGGING` is true
2. `LOG_LEVEL` is appropriate (DEBUG shows everything)
3. Logger name starts with `wfc.`
4. No handler is swallowing logs

### Secrets appearing in logs

1. Check sanitizer patterns in `wfc/shared/logging/sanitizer.py`
2. Add new patterns if needed
3. Run `pre-commit run detect-secrets --all-files` to scan for leaks

### Performance issues

1. Reduce log verbosity (INFO instead of DEBUG)
2. Use conditional logging:

   ```python
   if logger.isEnabledFor(logging.DEBUG):
       logger.debug(f"Expensive computation: {expensive_func()}")
   ```

3. Check for logging in hot paths

## Migration from stdlib

See [LOGGING_MIGRATION.md](../migration/LOGGING_MIGRATION.md) for detailed migration guide.

## Related

- [Secret Sanitization Patterns](../../wfc/shared/logging/sanitizer.py)
- [Request Context API](../../wfc/shared/logging/context.py)
- [Performance Decorators](../../wfc/shared/logging/decorators.py)
