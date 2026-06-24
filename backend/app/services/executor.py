"""Compiles and runs user code for any supported language.

This module knows *how to drive a compiler/interpreter* but not the per-language
details — those live in :mod:`app.services.languages`. Given a language key, it
looks up the spec and follows it. That keeps the judge loop identical no matter
which language a user picks.

Two levels of API live here:

- **Primitives** used by the judge (Phase 2): :func:`compile_source` prepares a
  source file for execution once (compiling it for compiled languages, or just
  returning the source path for interpreted ones), and :func:`run_executable`
  runs the prepared program against one input. Splitting them lets the judge
  prepare a submission a single time and reuse it across many test cases.
- **Convenience** used by ``POST /run``: :func:`execute_code` prepares + runs
  once and returns stdout, raising :class:`RuntimeError` on any failure.
"""

import subprocess
import time
from pathlib import Path

from app.config import settings
from app.services.languages import get_language

# Folder that holds the compiled binaries; created once at import time.
settings.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Default time limit (seconds) for the ad-hoc /run endpoint.
RUN_TIMEOUT_SECONDS = 5


class CompilationError(RuntimeError):
    """Raised when source code fails to compile; carries the compiler message."""


def compile_source(language: str, source_path: Path) -> Path:
    """Prepare ``source_path`` for execution and return the path to run.

    For compiled languages (C++), this runs the compiler and returns the built
    binary. For interpreted languages (Python), there is nothing to build, so it
    returns the source path unchanged.

    Raises:
        CompilationError: if a compiled language fails to compile.
    """
    # Phase 8: when the Docker sandbox is enabled, compile inside a container
    # instead of on the host. Imported lazily to avoid a circular import
    # (sandbox imports CompilationError from this module).
    if settings.USE_DOCKER_SANDBOX:
        from app.services import sandbox

        return sandbox.compile_in_sandbox(language, source_path)

    spec = get_language(language)

    # Interpreted languages have no compile step — run the source directly.
    if spec.compile_cmd is None:
        return source_path

    argv, binary_path = spec.compile_cmd(source_path)
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise CompilationError(result.stderr or result.stdout)
    return binary_path


def run_executable(
    language: str,
    executable_path: Path,
    stdin: str,
    timeout_seconds: float,
    memory_mb: int | None = None,
) -> dict:
    """Run a prepared program once and report what happened.

    ``executable_path`` is whatever :func:`compile_source` returned: a compiled
    binary, or the source file for interpreted languages. Never raises for
    program errors; instead returns a dict describing the run:
        {"timed_out": bool, "returncode": int|None, "stdout": str,
         "stderr": str, "runtime_ms": int}

    ``memory_mb`` is the per-run RAM ceiling enforced by the Docker sandbox
    (Phase 8). It is ignored on the host path, which has no portable memory cap.
    """
    # Phase 8: delegate to the locked-down container when the sandbox is on.
    if settings.USE_DOCKER_SANDBOX:
        from app.services import sandbox

        return sandbox.run_in_sandbox(
            language,
            executable_path,
            stdin,
            timeout_seconds,
            memory_mb or settings.SANDBOX_MEMORY_MB,
        )

    argv = get_language(language).run_cmd(executable_path)

    start = time.perf_counter()
    try:
        result = subprocess.run(
            argv,
            cwd=str(settings.OUTPUTS_DIR),
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        runtime_ms = int((time.perf_counter() - start) * 1000)
        return {
            "timed_out": True,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "runtime_ms": runtime_ms,
        }

    runtime_ms = int((time.perf_counter() - start) * 1000)
    return {
        "timed_out": False,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "runtime_ms": runtime_ms,
    }


def execute_code(language: str, file_path: str, stdin: str = "") -> str:
    """Prepare and run ``file_path`` once, returning stdout (used by ``POST /run``).

    Raises:
        RuntimeError: if compilation fails, the program times out, or it exits
            with a non-zero status. The message carries the relevant details.
    """
    executable_path = compile_source(language, Path(file_path))
    result = run_executable(language, executable_path, stdin, RUN_TIMEOUT_SECONDS)

    if result["timed_out"]:
        raise RuntimeError("Time limit exceeded.")
    if result["returncode"] != 0:
        raise RuntimeError(result["stderr"] or result["stdout"] or "Runtime error.")
    return result["stdout"]
