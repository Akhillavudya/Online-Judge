"""Compiles and runs a C++ source file, returning its standard output.

Compilation and runtime failures are raised as :class:`RuntimeError` carrying the
relevant stderr/stdout, which the ``/run`` router turns into a helpful HTTP error.
"""

import os
import subprocess
from pathlib import Path

from app.config import settings

# Folder that holds the compiled binaries; created once at import time.
settings.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Hard limit (seconds) so a program with an infinite loop cannot hang the server.
RUN_TIMEOUT_SECONDS = 5


def execute_cpp(file_path: str, stdin: str = "") -> str:
    """Compile ``file_path`` with g++ and run it, returning the program's stdout.

    Raises:
        RuntimeError: if compilation fails or the program exits with a non-zero
            status; the message contains the compiler/runtime output.
    """
    source_path = Path(file_path)
    job_id = source_path.stem

    # Windows produces ``.exe`` binaries; Unix-like systems use ``.out``.
    executable_name = f"{job_id}.exe" if os.name == "nt" else f"{job_id}.out"
    executable_path = settings.OUTPUTS_DIR / executable_name

    # --- Compile ---------------------------------------------------------
    compile_result = subprocess.run(
        ["g++", str(source_path), "-o", str(executable_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if compile_result.returncode != 0:
        raise RuntimeError(compile_result.stderr or compile_result.stdout)

    # --- Run -------------------------------------------------------------
    run_result = subprocess.run(
        [str(executable_path)],
        cwd=str(settings.OUTPUTS_DIR),
        input=stdin,
        capture_output=True,
        text=True,
        timeout=RUN_TIMEOUT_SECONDS,
        check=False,
    )
    if run_result.returncode != 0:
        raise RuntimeError(run_result.stderr or run_result.stdout)

    return run_result.stdout
