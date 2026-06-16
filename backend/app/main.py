"""Application entry point.

``create_app`` wires everything together: it configures CORS, registers each
router, and ensures the database tables exist on startup. The server runs with::

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import init_database
from app.routers import ai, auth, health, problems, run, submissions


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Run startup/shutdown logic. On startup we make sure the DB schema exists."""
    init_database()
    yield
    # (No shutdown work needed — SQLite connections are opened per request.)


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    app = FastAPI(title="Online Compiler", lifespan=lifespan)

    # Allow the React frontend to call this API from the browser.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.CORS_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register each feature's routes. Keeping this list here gives a single,
    # readable map of everything the API exposes.
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(problems.router)
    app.include_router(submissions.router)
    app.include_router(run.router)
    app.include_router(ai.router)

    return app


# The ASGI application object uvicorn looks for (``app.main:app``).
app = create_app()
