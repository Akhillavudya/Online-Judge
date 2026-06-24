"""One place to set up application logging.

Before this, the backend relied on uvicorn's default output and a stray
``print`` here and there. For a "real" service we want a single, consistent log
format and a level we can control from the environment (``LOG_LEVEL``). Every
module then just does ``logging.getLogger(__name__)`` and writes structured-ish
lines that all look the same.

Think of it like a restaurant's order ticket printer: instead of each cook
scribbling notes on random scraps, every event prints on the same machine, in
the same format, so the manager can read the day's history at a glance.
"""

import logging

from app.config import settings

# A compact, readable line: time, level, which module, and the message.
_LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    """Initialise root logging once, using the level from ``settings.LOG_LEVEL``.

    Called from ``create_app`` at import time so it runs before any request is
    served. ``force=True`` replaces any handlers uvicorn/other libraries may have
    installed first, guaranteeing our single format wins.
    """
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        force=True,
    )
