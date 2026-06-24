# 08 — AI code review (Google Gemini)

## What & why

The editor has an **"Ask AI"** button that sends the user's code to Google
Gemini and shows a short review — correctness risks, edge cases, time/space
complexity, readability, and the occasional improved snippet. It's a study aid,
not part of judging: it never touches the verdict.

This endpoint has existed since the early days, but it only *truly works* once a
**Gemini API key** is configured. Without one it fails cleanly (the UI shows the
reason); with one it returns a real, language-aware review.

## Files involved

| File | Purpose |
| ---- | ------- |
| `app/services/ai_review.py` | The Gemini call. Builds a **language-aware** prompt, POSTs to the Gemini REST API, extracts the text. Knows nothing about FastAPI; on failure it raises `AIReviewError(status_code, detail)`. |
| `app/routers/ai.py` | `POST /ai/review` — validates the language against `SUPPORTED_LANGUAGES`, calls the service, and maps `AIReviewError` to the right HTTP status. Requires a logged-in user. |
| `app/schemas/ai.py` | `AIReviewRequest` — `{language, code, input?, output?}`. |
| `app/config.py` | `GEMINI_API_KEY` and `GEMINI_MODEL` (default `gemini-2.5-flash-lite`), read from the environment / `.env`. |
| `backend/.env` | **Where the secret lives.** Holds the real `GEMINI_API_KEY` (and an optional `GEMINI_MODEL`). Gitignored — never committed. Copy `backend/.env.sample` and fill in the key. |

## Flow — one review

1. The frontend `POST`s `/ai/review` with `{language, code, input, output}` and the
   bearer token.
2. `get_current_user` authenticates (401 if missing/invalid).
3. The router rejects unknown languages (400) — only the languages in
   `SUPPORTED_LANGUAGES` are allowed.
4. `review_code()`:
   - If `GEMINI_API_KEY` is unset → raises `AIReviewError(503, "GEMINI_API_KEY is
     not configured…")`.
   - Otherwise builds the prompt (parameterised by `language`, so a Python
     submission is reviewed *as Python*, with a ```` ```python ```` fence, and the
     answer is requested as short markdown), and POSTs to
     `…/models/{GEMINI_MODEL}:generateContent?key=…` with a 30s timeout.
   - On an HTTP/network error from Gemini → `AIReviewError(502, "Gemini review
     failed: …")`. On an empty answer → `AIReviewError(502, "…empty review")`.
5. The router returns `{review, model, reviewed_by}`. The frontend renders the
   `review` markdown (see `docs/frontend_explanation/08_ai_review_and_compiler_layout.md`).

## Analogy

Think of the service as a **courier to an outside expert**. The router writes the
question (your code + a note saying "review this *Python*"), the courier
(`urllib`) carries it to Gemini and brings the reply back. If the courier has no
address (no API key) or the expert's office is closed (Gemini error), the courier
returns with a clear "couldn't deliver, here's why" note rather than making up an
answer — that note is the `AIReviewError`, shown to the user as-is.

## How to extend / gotchas

- **You must supply a key.** Create `backend/.env` from `.env.sample` and set
  `GEMINI_API_KEY=...`. Restart the backend — `load_dotenv()` reads the file once
  at import, so a running server won't pick up edits until you restart.
- **Model names go stale.** `gemini-1.5-flash` (an older default) now returns
  **404 NOT_FOUND** on the free tier; the default is `gemini-2.5-flash-lite`. If a
  call 404s, list available models with
  `GET https://generativelanguage.googleapis.com/v1beta/models?key=…` and set
  `GEMINI_MODEL` to one that lists `generateContent`.
- **Free-tier quota is per-model-per-day (and per-minute).** A `429
  RESOURCE_EXHAUSTED` means you've hit a limit; the error includes a `retryDelay`.
  Each model has its own bucket, so switching models (e.g. to `…-flash-lite`) can
  unblock you. The UI surfaces the 429 message verbatim.
- **The error contract is the service's job.** The service chooses the status
  code (503 = config problem, 502 = upstream/Gemini problem) and the router just
  forwards it. Keep that split if you add more failure cases.
- **No streaming / no storage.** Reviews aren't saved; each click is a fresh call.
  If you later want history, add a table + repository (don't put SQL in the
  service or router).
