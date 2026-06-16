"""Writes user-submitted source code to a temporary file on disk.

The compiler needs a real file path, so each run is written to its own uniquely
named file under ``settings.CODES_DIR`` (``backend/codes``).
"""

from pathlib import Path
from uuid import uuid4

from app.config import settings

# Make sure the destination folder exists before any request tries to write to it.
settings.CODES_DIR.mkdir(parents=True, exist_ok=True)


def generate_file(extension: str, content: str) -> str:
    """Write ``content`` to a new ``<uuid>.<extension>`` file and return its path.

    The random UUID name means two simultaneous runs never overwrite each other.
    """
    file_path = settings.CODES_DIR / f"{uuid4()}.{extension}"
    Path(file_path).write_text(content, encoding="utf-8")
    return str(file_path)
