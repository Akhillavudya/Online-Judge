# Feature: Submission History & Solved Status (Backend) — Phase 3

> Phase 2 judged a single submission. Phase 3 turns those stored attempts into a
> **personal record**: every solution a user has ever submitted (across all
> problems) and which problems they've **solved**.

---

## What & why

Each judged attempt was already saved in `judge_submissions` (Phase 2), but the
only way to read them back was per-problem (`GET /problems/{slug}/submissions`).
Phase 3 adds two **account-wide** views scoped to the logged-in user ("me"):

| Endpoint | Returns |
| -------- | ------- |
| `GET /me/submissions` | Every judged attempt by the user, across all problems, newest first — each row carries the problem's title and slug. |
| `GET /me/solved` | The slugs of problems the user has an `AC` (Accepted) verdict on. |

A problem is considered **solved** the moment *any one* of the user's submissions
to it earns `AC`. That same idea feeds the "Solved ✓" badges in the UI and will
power the profile/leaderboard counts in Phase 7.

**Analogy:** Phase 2 stamped each exam paper with a grade. Phase 3 is the
**student's transcript** — all their papers in one list, plus a short "subjects
passed" summary.

---

## Files involved

| File | Purpose |
| ---- | ------- |
| `app/db/repositories/judge_submissions.py` | Adds `list_all_judge_submissions(user_id)` (JOINs `problems` for title/slug) and `list_solved_problem_slugs(user_id)` (distinct slugs with verdict `AC`). |
| `app/schemas/judge.py` | Adds `UserSubmissionOut` — a `JudgeSubmissionOut` plus `problem_title` and `problem_slug`. |
| `app/routers/me.py` | **New router.** `GET /me/submissions` and `GET /me/solved`, both behind `get_current_user`. |
| `app/main.py` | Registers the new `me` router. |

No new table or migration: Phase 3 only *reads* the `judge_submissions` rows that
Phase 2 already writes.

### Why a separate `/me` router?

The per-problem history belongs under `/problems/{slug}/...` because the problem
is known from the URL. These views are about *the user*, not one problem, so they
read more naturally as `/me/...`. Keeping them in their own router also gives a
clean home for future "my profile" endpoints (Phase 7).

---

## Flow

### `GET /me/submissions`
1. `get_current_user` validates the token (else `401`).
2. `list_all_judge_submissions(user_id)` runs one SQL query that JOINs
   `judge_submissions → problems` so each row already includes `problem_title`
   and `problem_slug` (no N+1 follow-up queries).
3. Rows are returned newest-first as `UserSubmissionOut`:
   `{ "submissions": [ { id, language, verdict, passed_count, total_count, runtime_ms, created_at, problem_title, problem_slug } ] }`.

### `GET /me/solved`
1. `get_current_user` validates the token.
2. `list_solved_problem_slugs(user_id)` selects `DISTINCT p.slug` where
   `verdict = 'AC'`.
3. Returns `{ "solved": ["a-b-problem", ...] }`.

The frontend turns that array into a `Set` for O(1) "is this problem solved?"
lookups while rendering the problem list.

---

## How to extend / gotchas

- **Solved = any AC, ever.** We don't track "first solve" time or re-solves; one
  `AC` flips the problem to solved. That's all Phase 7's solved-count needs.
- **No pagination yet.** `GET /me/submissions` returns every attempt. Fine for a
  student-sized history; Phase 9 adds pagination everywhere that returns lists.
- **`/me/solved` returns slugs, not ids** — deliberately, so the frontend can match
  against the slugs it already shows without an extra id↔slug lookup.
- **Phase 7 (profiles/leaderboard):** the solved-slugs query is the seed for
  `COUNT(DISTINCT problem_id)`-style aggregation; group by `user_id` for ranking.

---

## How it was verified (running server + curl)

| Check | Result |
| ----- | ------ |
| `GET /me/submissions` (new user) | `{"submissions":[]}` |
| `GET /me/solved` (new user) | `{"solved":[]}` |
| `GET /me/submissions` without token | `401` |
| Submit correct `a+b` then `GET /me/submissions` | one row, `AC` 4/4, with `problem_title: "A + B Problem"`, `problem_slug: "a-b-problem"` |
| ...then `GET /me/solved` | `{"solved":["a-b-problem"]}` |
