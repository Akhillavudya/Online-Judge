"""Compiles and runs C++ code.

Two levels of API live here:

- **Primitives** used by the judge (Phase 2): :func:`compile_source` compiles once,
  and :func:`run_executable` runs the compiled binary against one input. Splitting
  them lets the judge compile a submission a single time and then reuse the binary
  across many test cases.
- **Convenience** used by ``POST /run``: :func:`execute_cpp` compiles + runs once
  and returns stdout, raising :class:`RuntimeError` on any failure.
"""

import os
import subprocess
import time
from pathlib import Path

from app.config import settings

# Folder that holds the compiled binaries; created once at import time.
settings.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Default time limit (seconds) for the ad-hoc /run endpoint.
RUN_TIMEOUT_SECONDS = 5


class CompilationError(RuntimeError):
    """Raised when source code fails to compile; carries the compiler message."""


def compile_source(source_path: Path) -> Path:
    """Compile a C++ source file with g++ and return the executable path.

    Raises:
        CompilationError: if g++ reports an error.
    """
    job_id = source_path.stem
    # Windows produces ``.exe`` binaries; Unix-like systems use ``.out``.
    executable_name = f"{job_id}.exe" if os.name == "nt" else f"{job_id}.out"
    executable_path = settings.OUTPUTS_DIR / executable_name

    result = subprocess.run(
        ["g++", str(source_path), "-o", str(executable_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise CompilationError(result.stderr or result.stdout)
    return executable_path


def run_executable(executable_path: Path, stdin: str, timeout_seconds: float) -> dict:
    """Run a compiled binary once and report what happened.

    Never raises for program errors; instead returns a dict describing the run:
        {"timed_out": bool, "returncode": int|None, "stdout": str,
         "stderr": str, "runtime_ms": int}
    """
    start = time.perf_counter()
    try:
        result = subprocess.run(
            [str(executable_path)],
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


def execute_cpp(file_path: str, stdin: str = "") -> str:
    """Compile and run ``file_path`` once, returning stdout (used by ``POST /run``).

    Raises:
        RuntimeError: if compilation fails, the program times out, or it exits
            with a non-zero status. The message carries the relevant details.
    """
    executable_path = compile_source(Path(file_path))
    result = run_executable(executable_path, stdin, RUN_TIMEOUT_SECONDS)

    if result["timed_out"]:
        raise RuntimeError("Time limit exceeded.")
    if result["returncode"] != 0:
        raise RuntimeError(result["stderr"] or result["stdout"] or "Runtime error.")
    return result["stdout"]
