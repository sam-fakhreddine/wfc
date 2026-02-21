"""
WFC REST API Server - Main application.

FastAPI application with authentication, authorization, and resource monitoring.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from wfc.servers.rest_api.models import ErrorResponse
from wfc.servers.rest_api.routes import project_router, resource_router, review_router

logger = logging.getLogger(__name__)


MAX_REQUEST_SIZE = 1_000_000


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Lifespan context manager for startup/shutdown."""
    logger.info("WFC REST API server starting up")
    yield
    logger.info("WFC REST API server shutting down")


app = FastAPI(
    title="WFC REST API",
    description="Multi-tenant code review and project management API for WFC",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router)
app.include_router(project_router)
app.include_router(resource_router)


@app.get("/", summary="Health check", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "wfc-rest-api", "version": "1.0.0"}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with sanitized headers."""
    start_time = time.time()

    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(f"Response: {response.status_code} ({duration:.3f}s)")

    return response


@app.middleware("http")
async def validate_request_size(request: Request, call_next):
    """Validate request body size."""
    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": f"Request too large. Max {MAX_REQUEST_SIZE} bytes."},
            )

    return await call_next(request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error="Internal server error",
        detail=str(exc),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode="json"),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "wfc.servers.rest_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        workers=4,
        limit_concurrency=100,
        timeout_keep_alive=5,
    )
