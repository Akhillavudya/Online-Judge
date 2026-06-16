"""Small time helper so every table stores timestamps in the same format."""

from datetime import datetime, timezone


def now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string (e.g. ``2026-06-17T...``)."""
    return datetime.now(timezone.utc).isoformat()
