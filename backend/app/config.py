"""Central configuration for the backend.

Every environment variable and important file path is defined here exactly once.
Other modules import ``settings`` instead of calling ``os.getenv`` themselves, so
there is a single, easy-to-find place to see how the app is configured.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Loads variables from a local ``.env`` file when one is present. This lets the
# backend pick up PORT / CORS_ORIGIN / GEMINI_* locally without hard-coding them.
load_dotenv()


# The backend root directory (the folder that contains this ``app`` package).
# Two ``.parent`` hops: config.py -> app/ -> backend/.
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """Holds all runtime configuration as plain attributes.

    A simple class (instead of pydantic-settings) keeps the dependency list small
    while still giving us one tidy object to import everywhere.
    """

    # --- Web / CORS -------------------------------------------------------
    # The frontend origin allowed to call this API from the browser.
    CORS_ORIGIN: str = os.getenv("CORS_ORIGIN", "http://localhost:5173")

    # --- Database ---------------------------------------------------------
    # SQLite file lives in the backend root so it survives across restarts.
    DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_NAME", "compiler.db")

    # --- Filesystem workspace for the compiler ---------------------------
    # User-submitted source files and the compiled binaries each get their own
    # folder under the backend root. Centralising the paths here means the
    # services do not depend on their own location on disk.
    CODES_DIR: Path = BASE_DIR / "codes"
    OUTPUTS_DIR: Path = BASE_DIR / "outputs"

    # --- Password hashing / auth tokens ----------------------------------
    # PBKDF2 iteration count and the number of random bytes used per token.
    PASSWORD_ITERATIONS: int = 260_000
    TOKEN_BYTES: int = 32

    # --- AI code review (Google Gemini) ----------------------------------
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


# Importable singleton used throughout the codebase: ``from app.config import settings``.
settings = Settings()
