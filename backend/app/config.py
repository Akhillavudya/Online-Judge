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


def _env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable ("1"/"true"/"yes" are truthy)."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


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
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

    # --- Secure sandboxed execution (Phase 8) ----------------------------
    # When enabled, user code is compiled and run inside a locked-down Docker
    # container (no network, CPU/memory/PID limits, non-root, read-only fs)
    # instead of directly on the host. Default OFF so local development works
    # without Docker; turn it ON (`USE_DOCKER_SANDBOX=1`) on the deployment host
    # where Docker is installed and the sandbox image has been built.
    USE_DOCKER_SANDBOX: bool = _env_bool("USE_DOCKER_SANDBOX", False)
    # Name/tag of the prebuilt sandbox image (see backend/sandbox/Dockerfile).
    SANDBOX_IMAGE: str = os.getenv("SANDBOX_IMAGE", "online-judge-sandbox")
    # Memory ceiling (MB) for a *running* submission when the problem does not
    # specify its own limit, and the CPU share each container may use.
    SANDBOX_MEMORY_MB: int = int(os.getenv("SANDBOX_MEMORY_MB", "256"))
    SANDBOX_CPUS: str = os.getenv("SANDBOX_CPUS", "1.0")
    # More generous ceilings for the one-off compile step (g++ is hungry).
    SANDBOX_COMPILE_MEMORY_MB: int = int(os.getenv("SANDBOX_COMPILE_MEMORY_MB", "512"))
    SANDBOX_COMPILE_TIMEOUT_S: int = int(os.getenv("SANDBOX_COMPILE_TIMEOUT_S", "20"))
    # Working area for per-submission sandbox folders (bind-mounted into Docker).
    SANDBOX_DIR: Path = BASE_DIR / "sandbox_work"


# Importable singleton used throughout the codebase: ``from app.config import settings``.
settings = Settings()
