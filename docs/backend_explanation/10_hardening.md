# 10 — Hardening for the real world (Phase 9)

## What & why

Phases 1–8 made the app a working, sandboxed online judge. Phase 9 adds the
**production touches** that separate a class project from something you'd put on
the public internet. None of these change *what* the app does — they make it
**safe, observable, and well-behaved under load**:

1. **Pagination everywhere** — list endpoints return one page at a time plus a
   `total`, instead of dumping the whole table.
2. **Rate limiting** on the expensive `/run` and `/submit` endpoints so one user
   can't pin the server by hammering the compiler.
3. **Consistent error responses** — every error the client sees has the same
   `{"detail": "..."}` shape, and unexpected crashes never leak stack traces.
4. **Logging** — one access-log line per request and an audit line per judged
   submission, on a single configurable log level.
5. **CORS / env review** — the allowed browser origins are now a configurable
   list, ready for production.

This is the "I thought beyond the happy path" story for an interview.

## Files involved

| File | Purpose |
| ---- | ------- |
| `app/logging_config.py` | **New.** `configure_logging()` sets one log format + level (`LOG_LEVEL`) for the whole app. |
| `app/services/rate_limit.py` | **New.** `FixedWindowLimiter` (the counter) + `RateLimit` (a FastAPI dependency). Exposes ready-made `run_rate_limit` / `submit_rate_limit`. |
| `app/main.py` | Calls `configure_logging()`, builds CORS from a list, adds the request-logging middleware and the catch-all 500 handler. |
| `app/config.py` | New settings: `CORS_ORIGINS` (list), `LOG_LEVEL`, and the four `*_RATE_LIMIT` / `*_RATE_WINDOW_S` knobs. |
| `app/routers/run.py` | `/run` now depends on `run_rate_limit`. |
| `app/routers/problems.py` | `/submit` depends on `submit_rate_limit`, logs each verdict, and `/{slug}/submissions` is paginated. |
| `app/routers/me.py`, `app/routers/submissions.py` | List endpoints take `page`/`limit` and return `total`. |
| `app/db/repositories/judge_submissions.py`, `submissions.py` | List queries gained optional `LIMIT`/`OFFSET`; new `count_*` helpers. |
| `.env.sample` | Documents `CORS_ORIGINS`, `LOG_LEVEL`, and the rate-limit knobs. |

## End-to-end flow

**A normal request**

```
Request → access-log middleware (starts a timer)
        → CORS check (origin allowed?)
        → route dependencies (e.g. rate limit, auth)
        → endpoint runs
        → access-log middleware logs "POST /run -> 200 (12.3 ms)"
```

**A rate-limited request** (`/run`, `/submit`)

```
RateLimit dependency runs BEFORE the endpoint body:
  identity = the bearer token (per-account) or, if anonymous, the client IP
  limiter.check(identity):
    count this hit inside the current fixed time window
    if count > limit  → raise HTTP 429 + a Retry-After header
  else → continue to the endpoint
```

Because the limiter is a **dependency**, even requests that would fail validation
(empty code, bad language) still count against the limit — the gate is *in front
of* the handler.

**An unexpected crash**

```
endpoint raises some non-HTTPException
  → @app.exception_handler(Exception) catches it
  → logs the full traceback server-side (for us)
  → returns {"detail": "Internal server error."} (generic, for the client)
```

`HTTPException` and request-validation errors are still handled by FastAPI's
defaults, which already use the `{"detail": ...}` shape — so the frontend can
*always* read `error.response.data.detail`.

**A paginated list**

```
GET /me/submissions?page=2&limit=20
  offset = (page - 1) * limit = 20
  rows  = list_all_judge_submissions(user, limit=20, offset=20)
  total = count_all_judge_submissions(user)
  → { submissions: [...20...], total: 137, page: 2, limit: 20 }
```

The frontend divides `total` by `limit` to know how many pages exist (see the
matching frontend doc).

## Beginner-friendly analogy

Think of the judge as a **busy restaurant kitchen**:

- **Rate limiting** is the host at the door: one table can only send so many
  orders per minute, so a single rowdy table can't starve everyone else.
- **Pagination** is serving food in courses instead of dumping the entire menu's
  worth of plates on the table at once.
- **Consistent errors** are a polite waiter: when something goes wrong you get a
  short "sorry, kitchen issue" — never the cook's panicked shouting (the stack
  trace) from the back.
- **Logging** is the order-ticket printer: every order and every problem prints
  on one machine, in one format, so the manager can review the whole night later.

## Fixed-window rate limiting (the bit worth explaining)

`FixedWindowLimiter` keeps, per caller key, a `(window_start, count)` pair:

- The first request in a window stores "started now, count 1".
- Each later request increments the count.
- Once `window_seconds` have passed since `window_start`, the window resets.
- If the count exceeds the limit, the request is rejected with `429` and a
  `Retry-After` telling the client how long until the window rolls.

**Known trade-off (say this out loud in interviews):** the boundary burst. A user
could send `limit` requests at the very end of one window and `limit` more at the
start of the next, briefly doing ~2× the limit. That's fine for our scale. The
sliding-window or token-bucket algorithms fix it; we keep the simple version.

**Why not a library (`slowapi`)?** Keeping the dependency list tiny is a project
rule, and a counter you wrote yourself is easier to explain than a black box. The
limiter lives in process memory, so it's per-server — for a multi-server
deployment you'd move the counter into Redis, but the `RateLimit` dependency
interface wouldn't change.

## How to extend / gotchas

- **Rate-limit a new endpoint:** add `dependencies=[Depends(some_limit)]` to the
  route. Reuse `run_rate_limit` / `submit_rate_limit`, or make a new
  `RateLimit(max, window, name="...")`. Set a limit to `0` in the env to disable.
- **Paginate a new list:** add `page`/`limit` query params (`Query(ge=1)` /
  `Query(ge=1, le=100)`), give the repo a `LIMIT ? OFFSET ?` and a `count_*`
  helper, and return `{items, total, page, limit}`. The repo list functions keep
  `limit=None` as a back-compatible "return everything" default.
- **Gotcha — the limiter must be a singleton.** The shared `run_rate_limit` /
  `submit_rate_limit` instances are created once at import; a fresh limiter per
  request would never accumulate a count and so would never trip.
- **Gotcha — the catch-all handler must not leak.** Log the real error
  server-side, return a *generic* message to the client. Never put `str(exc)`
  in the response body.
- **Gotcha — restart after `.env` edits.** `load_dotenv()` and the limiter
  settings are read once at import, so config changes need a server restart.
- **Verifying the limiter locally:** real `/run` calls compile for ~2–3s each, so
  you can't reach `30/min` by hand. Test with a low limit (`RUN_RATE_LIMIT=5`)
  and fire empty-code requests (they 400 *after* the rate-limit gate, so they
  still count) — the 6th returns `429`.
```
