"""Application entry point.

``create_app`` wires everything together: it configures logging and CORS,
installs the request-logging middleware and a catch-all error handler, registers
each router, and ensures the database tables exist on startup. The server runs
with::

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.database import init_database
from app.logging_config import configure_logging
from app.routers import admin, ai, auth, health, me, problems, run, stats, submissions

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Run startup/shutdown logic. On startup we make sure the DB schema exists."""
    init_database()
    logger.info("Startup complete — database ready, CORS origins: %s", settings.CORS_ORIGINS)
    yield
    # (No shutdown work needed — SQLite connections are opened per request.)


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    # Set up our single log format/level before anything else emits a line.
    configure_logging()

    app = FastAPI(title="Verdex", lifespan=lifespan)

    # Allow the React frontend(s) to call this API from the browser. The list of
    # allowed origins is configurable (comma-separated) for production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_middleware(app)
    _register_error_handlers(app)
    _register_routers(app)
    return app


def _register_middleware(app: FastAPI) -> None:
    """Install an access log: one line per request with status + duration."""

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # Let the exception handler build the 500 response; we just make sure
            # there is still an access-log line for the failed request.
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s -> 500 (%.1f ms)", request.method, request.url.path, elapsed_ms
            )
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %d (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response


def _register_error_handlers(app: FastAPI) -> None:
    """Turn any *unhandled* exception into a clean, consistent 500.

    FastAPI already returns ``{"detail": ...}`` for ``HTTPException`` and request
    validation errors, so the frontend can always read ``error.response.data.detail``.
    This handler catches everything else: it logs the full traceback server-side
    (for us) but returns a generic message to the client (so we never leak stack
    traces, file paths, or SQL to users).
    """

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error."},
        )


def _register_routers(app: FastAPI) -> None:
    """Register each feature's routes — a single, readable map of the API."""
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(problems.router)
    app.include_router(admin.router)
    app.include_router(me.router)
    app.include_router(stats.router)
    app.include_router(submissions.router)
    app.include_router(run.router)
    app.include_router(ai.router)


# The ASGI application object uvicorn looks for (``app.main:app``).
app = create_app()
