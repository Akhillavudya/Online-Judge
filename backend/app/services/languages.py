"""The per-language strategy registry.

Everything that differs *between programming languages* lives here in one small
table — file extension, how to compile (if at all), and how to run. The executor
and the judge stay language-agnostic: they look a language up in :data:`LANGUAGES`
and follow whatever the spec tells them. Adding a new language means adding one
entry below — no change to the executor or the judge loop. (That's the
open/closed principle: open for extension, closed for modification.)

A language is one of two shapes:

- **Compiled** (e.g. C++): ``compile_cmd`` is set. We build a binary once, then
  run that binary for each test case.
- **Interpreted** (e.g. Python): ``compile_cmd`` is ``None``. There is no build
  step; we run the source file directly with an interpreter.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from app.config import settings

# The Python interpreter differs by platform: Windows ships it as ``python``,
# most Unix-like systems expose it as ``python3``.
PYTHON_CMD = "python" if os.name == "nt" else "python3"


@dataclass(frozen=True)
class LanguageSpec:
    """How to compile (optionally) and run one programming language.

    Attributes:
        name: the language key used in API requests (e.g. ``"cpp"``).
        extension: source-file extension, without the dot (e.g. ``"cpp"``).
        compile_cmd: given the source path, returns ``(argv, artifact_path)`` —
            the compiler command to run and where the built binary will land.
            ``None`` for interpreted languages (no compile step).
        run_cmd: given the path to execute (the built binary for compiled
            languages, or the source file for interpreted ones), returns the
            argv used to run the program.
    """

    name: str
    extension: str
    compile_cmd: Optional[Callable[[Path], tuple[list[str], Path]]]
    run_cmd: Callable[[Path], list[str]]


def _cpp_compile(source_path: Path) -> tuple[list[str], Path]:
    """Build the g++ command for ``source_path`` and the binary it produces."""
    # Windows produces ``.exe`` binaries; Unix-like systems use ``.out``.
    binary_name = f"{source_path.stem}.exe" if os.name == "nt" else f"{source_path.stem}.out"
    binary_path = settings.OUTPUTS_DIR / binary_name
    return ["g++", str(source_path), "-o", str(binary_path)], binary_path


# The single source of truth for which languages the judge supports. To add a
# language (Java, C, …) append one entry here — nothing else needs to change.
LANGUAGES: dict[str, LanguageSpec] = {
    "cpp": LanguageSpec(
        name="cpp",
        extension="cpp",
        compile_cmd=_cpp_compile,
        run_cmd=lambda binary_path: [str(binary_path)],
    ),
    "python": LanguageSpec(
        name="python",
        extension="py",
        compile_cmd=None,  # interpreted: no build step
        run_cmd=lambda source_path: [PYTHON_CMD, str(source_path)],
    ),
}

# Convenient set for routers to validate the requested language against.
SUPPORTED_LANGUAGES = set(LANGUAGES)


def get_language(language: str) -> LanguageSpec:
    """Return the :class:`LanguageSpec` for ``language``.

    Raises:
        ValueError: if the language is not supported. Callers (routers) should
            validate against :data:`SUPPORTED_LANGUAGES` first and return a 400.
    """
    try:
        return LANGUAGES[language]
    except KeyError as error:
        raise ValueError(f"Unsupported language: {language!r}") from error
