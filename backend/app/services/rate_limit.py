"""A tiny in-process rate limiter for the expensive endpoints.

``/run`` and ``/problems/{slug}/submit`` both spin up a compiler (and, with the
Phase 8 sandbox on, a Docker container). Without a guard, one user hammering
"Run" in a loop could pin the box. This module enforces a simple **fixed-window**
limit: "at most N requests per W seconds" per caller.

Why a hand-rolled limiter instead of a library like ``slowapi``? Keeping the
dependency list tiny is a project rule, and a fixed-window counter is easy to
explain in an interview:

    * Bucket time into fixed windows of ``window_seconds``.
    * Count requests in the current window per caller key.
    * If the count exceeds the limit, reject with HTTP 429 until the window rolls.

The trade-off (the "boundary burst": up to 2x the limit can slip through right at
a window edge) is fine here and is exactly the kind of nuance worth mentioning.
For a multi-process / multi-server deployment you'd move the counter into Redis;
the dependency interface below would not change.
"""

import logging
import threading
import time

from fastapi import HTTPException, Request, status

from app.config import settings

logger = logging.getLogger(__name__)

# If the counter dict ever grows past this many distinct callers, we prune the
# windows that have already expired. Keeps memory bounded without a background
# thread — the cleanup just piggybacks on the next request.
_PRUNE_THRESHOLD = 10_000


class FixedWindowLimiter:
    """Counts requests per key inside fixed time windows. Thread-safe."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key -> (window_start_monotonic, count_in_window)
        self._hits: dict[str, tuple[float, int]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int]:
        """Register one hit for ``key``.

        Returns ``(allowed, retry_after_seconds)``. When ``allowed`` is False the
        caller is over the limit and ``retry_after`` says how long until the
        current window resets.
        """
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > _PRUNE_THRESHOLD:
                self._prune(now)

            window_start, count = self._hits.get(key, (now, 0))
            if now - window_start >= self.window_seconds:
                # Previous window expired — start a fresh one.
                window_start, count = now, 0

            count += 1
            self._hits[key] = (window_start, count)

            if count > self.max_requests:
                retry_after = int(self.window_seconds - (now - window_start)) + 1
                return False, retry_after
            return True, 0

    def _prune(self, now: float) -> None:
        """Drop entries whose window has already elapsed (caller holds the lock)."""
        expired = [
            key
            for key, (start, _) in self._hits.items()
            if now - start >= self.window_seconds
        ]
        for key in expired:
            del self._hits[key]


class RateLimit:
    """A FastAPI dependency that enforces one :class:`FixedWindowLimiter`.

    Use it per endpoint::

        @router.post("/run", dependencies=[Depends(run_rate_limit)])

    The caller is identified by their auth token when present (so the limit is
    per-account), falling back to the client IP for anonymous endpoints like
    ``/run``. A limit of ``0`` disables the check (handy for tests / local dev).
    """

    def __init__(self, max_requests: int, window_seconds: int, name: str) -> None:
        self.name = name
        self.enabled = max_requests > 0
        self.limiter = FixedWindowLimiter(max_requests, window_seconds)

    def __call__(self, request: Request) -> None:
        if not self.enabled:
            return

        key = f"{self.name}:{self._identity(request)}"
        allowed, retry_after = self.limiter.check(key)
        if not allowed:
            logger.warning("Rate limit hit on %s by %s", self.name, key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down and try again shortly.",
                headers={"Retry-After": str(retry_after)},
            )

    @staticmethod
    def _identity(request: Request) -> str:
        """Per-account key from the bearer token, else the client IP."""
        authorization = request.headers.get("authorization", "")
        if authorization.startswith("Bearer "):
            return "user:" + authorization.removeprefix("Bearer ").strip()
        client = request.client
        return "ip:" + (client.host if client else "unknown")


# Shared limiter instances, one per protected endpoint. They are created once at
# import time from the configured limits and reused across all requests so the
# counters actually accumulate (a fresh limiter per request would never trip).
run_rate_limit = RateLimit(
    settings.RUN_RATE_LIMIT, settings.RUN_RATE_WINDOW_S, name="run"
)
submit_rate_limit = RateLimit(
    settings.SUBMIT_RATE_LIMIT, settings.SUBMIT_RATE_WINDOW_S, name="submit"
)
