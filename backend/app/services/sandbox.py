"""Run untrusted user code inside a locked-down Docker container (Phase 8).

Until now the judge compiled and ran submissions **directly on the host** — fine
for a class project, but it means arbitrary code from strangers executes with the
backend's own privileges. That is the one real security risk in the whole app.

This module is the fix. It mirrors the two execution primitives in
:mod:`app.services.executor` — *compile once*, then *run each test case* — but
each step happens in a throwaway container started from the ``online-judge-sandbox``
image (see ``backend/sandbox/Dockerfile``). The container is wrapped in every
isolation flag that matters:

- ``--network none``        — no internet / LAN access.
- ``--memory`` / ``--memory-swap`` — a hard RAM ceiling (swap disabled).
- ``--cpus``               — a CPU share so one submission can't peg the box.
- ``--pids-limit``         — caps processes, defusing fork bombs.
- ``--read-only`` + tmpfs  — the root filesystem can't be modified.
- ``--user nobody``        — the program runs unprivileged.
- coreutils ``timeout``    — bounds the program's own runtime precisely.

The judge loop is **unchanged**: :mod:`executor` simply delegates to the two
functions here when ``settings.USE_DOCKER_SANDBOX`` is on. Because compilation
happens *inside* the Linux container, the binary it produces is a Linux ELF — so
this works even when the backend host is Windows/macOS, as long as Docker is
available.

Design note: the per-language Linux commands live in :data:`_SANDBOX_SPECS` here,
deliberately separate from the *host* commands in :mod:`app.services.languages`.
The host and the container are different operating environments (paths, ``.exe``
vs ELF, ``python`` vs ``python3``), so they keep separate, tiny strategy tables.
Adding a language means one entry in each.
"""

import shutil
import subprocess
import time
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.services.executor import CompilationError
from app.services.languages import get_language

# Folder that holds one sub-folder per submission; bind-mounted into Docker.
settings.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# Where the per-submission folder is mounted inside every container.
_WORKDIR = "/work"

# Extra wall-clock seconds we allow on top of the program's own time limit, to
# absorb container startup. TLE itself is decided precisely by the inner
# ``timeout`` tool (exit code 124), not by this outer safety net.
_STARTUP_GRACE_S = 10


class SandboxError(RuntimeError):
    """Raised when the sandbox cannot run at all (Docker missing/daemon down).

    This is a *server configuration* problem, distinct from the user's code
    failing to compile or crashing — those are reported as normal verdicts.
    """


# Per-language commands, expressed for the Linux container and relative to
# ``/work``. ``compile`` is None for interpreted languages. ``run`` is the argv
# that executes the prepared program (a built ``solution`` binary, or the source
# file for interpreted languages).
_SANDBOX_SPECS: dict[str, dict] = {
    "cpp": {
        "compile": ["g++", "-O2", "-o", "solution", "{src}"],
        "run": ["./solution"],
    },
    "python": {
        "compile": None,
        "run": ["python3", "{src}"],
    },
}


@lru_cache(maxsize=1)
def docker_available() -> bool:
    """Return True if the ``docker`` CLI is on PATH (cached after first check)."""
    return shutil.which("docker") is not None


def _require_docker() -> None:
    if not docker_available():
        raise SandboxError(
            "USE_DOCKER_SANDBOX is enabled but the 'docker' command was not found. "
            "Install Docker and build the sandbox image, or disable the sandbox."
        )


def _spec(language: str) -> dict:
    """Look up the container command spec, validating the language first."""
    get_language(language)  # raises ValueError for unknown languages (kept in sync)
    try:
        return _SANDBOX_SPECS[language]
    except KeyError as error:
        raise SandboxError(f"No sandbox profile for language {language!r}.") from error


def compile_in_sandbox(language: str, source_path: Path) -> Path:
    """Prepare ``source_path`` for sandboxed execution; return the path to run.

    Creates a fresh per-submission work folder, copies the source in as
    ``solution.<ext>``, and — for compiled languages — builds it *inside* a
    container so the artifact is a Linux binary. The returned path lives in that
    work folder; :func:`run_in_sandbox` re-mounts the folder to run it.

    Raises:
        CompilationError: if a compiled language fails to compile.
        SandboxError: if Docker is unavailable.
    """
    _require_docker()
    spec = _spec(language)
    extension = get_language(language).extension

    work_dir = settings.SANDBOX_DIR / uuid4().hex
    work_dir.mkdir(parents=True, exist_ok=True)
    src_name = f"solution.{extension}"
    (work_dir / src_name).write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")

    if spec["compile"] is None:
        # Interpreted: nothing to build, run the source file directly.
        return work_dir / src_name

    compile_argv = [arg.format(src=src_name) for arg in spec["compile"]]
    result = subprocess.run(
        _docker_compile_command(work_dir, compile_argv),
        capture_output=True,
        text=True,
        timeout=settings.SANDBOX_COMPILE_TIMEOUT_S + _STARTUP_GRACE_S,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr or result.stdout or "Compilation failed."
        # Strip the container's working-dir prefix so users see "solution.cpp:…".
        clean = message.replace(f"{_WORKDIR}/", "").strip()
        raise CompilationError(clean)

    return work_dir / "solution"


def run_in_sandbox(
    language: str,
    executable_path: Path,
    stdin: str,
    timeout_seconds: float,
    memory_mb: int,
) -> dict:
    """Run a prepared program once in a locked-down container; report the result.

    ``executable_path`` is whatever :func:`compile_in_sandbox` returned. Mirrors
    :func:`app.services.executor.run_executable`'s return shape exactly so the
    judge loop doesn't care whether the sandbox is on:
        {"timed_out": bool, "returncode": int|None, "stdout": str,
         "stderr": str, "runtime_ms": int}

    Raises:
        SandboxError: if Docker is unavailable.
    """
    _require_docker()
    spec = _spec(language)
    work_dir = executable_path.parent
    run_argv = [arg.format(src=executable_path.name) for arg in spec["run"]]

    command = _docker_run_command(work_dir, run_argv, timeout_seconds, memory_mb)

    start = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            input=stdin,
            capture_output=True,
            text=True,
            # Outer net only: the inner `timeout` should fire first (exit 124).
            timeout=timeout_seconds + _STARTUP_GRACE_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        runtime_ms = int((time.perf_counter() - start) * 1000)
        return {"timed_out": True, "returncode": None, "stdout": "",
                "stderr": "", "runtime_ms": runtime_ms}

    runtime_ms = int((time.perf_counter() - start) * 1000)

    # `timeout` exits 124 when it had to kill the program for running too long.
    if result.returncode == 124:
        return {"timed_out": True, "returncode": None, "stdout": "",
                "stderr": "", "runtime_ms": runtime_ms}

    return {
        "timed_out": False,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "runtime_ms": runtime_ms,
    }


def _docker_compile_command(work_dir: Path, compile_argv: list[str]) -> list[str]:
    """Build the ``docker run`` argv for the (writable) compile step."""
    return [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", f"{settings.SANDBOX_COMPILE_MEMORY_MB}m",
        "--memory-swap", f"{settings.SANDBOX_COMPILE_MEMORY_MB}m",
        "--cpus", settings.SANDBOX_CPUS,
        "--pids-limit", "128",
        # /work is writable here so the compiler can drop the binary in it.
        "-v", f"{work_dir}:{_WORKDIR}",
        "-w", _WORKDIR,
        settings.SANDBOX_IMAGE,
        *compile_argv,
    ]


def _docker_run_command(
    work_dir: Path, run_argv: list[str], timeout_seconds: float, memory_mb: int
) -> list[str]:
    """Build the ``docker run`` argv for the locked-down execution step."""
    # `timeout` bounds the program precisely: TERM at the limit, KILL 1s later if
    # it ignores TERM. Exit 124 => the program ran too long (our TLE signal).
    inner = ["timeout", "--kill-after=1", f"{timeout_seconds}", *run_argv]
    return [
        "docker", "run", "--rm", "-i",
        "--network", "none",
        "--memory", f"{memory_mb}m",
        "--memory-swap", f"{memory_mb}m",
        "--cpus", settings.SANDBOX_CPUS,
        "--pids-limit", "64",
        "--read-only",                       # immutable root filesystem
        "--tmpfs", "/tmp:rw,size=16m",        # scratch space programs may expect
        "--user", "nobody",                  # drop privileges
        "-v", f"{work_dir}:{_WORKDIR}:ro",    # code mounted read-only
        "-w", _WORKDIR,
        settings.SANDBOX_IMAGE,
        *inner,
    ]
