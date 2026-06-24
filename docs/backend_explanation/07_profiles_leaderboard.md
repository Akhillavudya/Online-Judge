# 07 — Profiles & Leaderboard (Phase 7)

## What & why

Up to now every endpoint dealt with **one row at a time** — one user, one
problem, one submission. Phase 7 adds the first **summary** views, the kind that
make an online judge feel alive:

- **Leaderboard** — every user ranked by how many problems they've solved.
- **Profile** — for any one user: total solved, a breakdown by difficulty, how
  many submissions they've made, their acceptance count, and their most recent
  attempts.

Neither stores anything new. They're pure **read models** computed on the fly
from the `judge_submissions` table we already fill in during judging (Phase 2),
joined to `problems` and `users`. The whole feature is an exercise in
`GROUP BY` / `COUNT` aggregation — exactly the SQL interviewers like to probe.

Two definitions the queries lean on:

- A problem is **solved** by a user the moment *any* of their submissions on it
  earns the `AC` verdict. "Solved" is therefore always a count of **distinct
  problem ids that have an AC** — never a raw row count (re-solving the same
  problem must not count twice).
- A **submission** is one judged attempt (one `judge_submissions` row), whatever
  the verdict. "Total submissions" and "accepted submissions" are raw row counts.

## Files involved

| File | Purpose |
| ---- | ------- |
| `app/db/repositories/stats.py` | **New.** All the aggregation SQL: leaderboard ranking + the per-user profile numbers. The only place these `GROUP BY`/`COUNT` queries live. |
| `app/schemas/stats.py` | **New.** Response shapes: `LeaderboardEntryOut`, `ProfileOut`, `SolvedByDifficulty`. Reuses `UserSubmissionOut` (from `schemas/judge.py`) for the recent-activity rows. |
| `app/routers/stats.py` | **New.** Two read-only endpoints — `GET /leaderboard` and `GET /users/{id}/profile`. Assembles the response and assigns 1-based ranks. |
| `app/main.py` | Registers the new router (`app.include_router(stats.router)`). |
| `app/db/repositories/users.py` | Unchanged — reused via `get_user_by_id` to look up the profile's owner (404 if missing). |

Why a **new `stats.py` repository** instead of adding to `judge_submissions.py`?
The other repos each map to a single table and do plain CRUD. These queries
*span three tables and summarise* — keeping them together makes the "stats"
feature easy to find, and keeps the row-level repos focused.

## The endpoints

```
GET /leaderboard?limit=50        -> { "leaderboard": [ {rank, user_id, name, solved_count, submission_count}, ... ] }
GET /users/{user_id}/profile     -> { user_id, name, role, created_at,
                                       total_solved, total_submissions, accepted_submissions,
                                       solved_by_difficulty: {easy, medium, hard},
                                       recent_submissions: [ ... ] }
```

Both require a logged-in user (same as the rest of the API) but expose **public**
information: any signed-in user can view anyone's profile and the leaderboard.

## Flow — opening someone's profile

1. The browser calls `GET /users/10/profile` with the bearer token.
2. `get_current_user` validates the token (401 if missing/invalid).
3. The router looks up user `10` with `users.get_user_by_id` → **404** if there is
   no such user.
4. It makes three aggregation calls into `stats.py`:
   - `get_user_submission_stats(10)` → `{total_submissions, accepted_submissions, total_solved}`
     in one query (a `COUNT(*)`, a conditional `SUM`, and a
     `COUNT(DISTINCT … CASE WHEN verdict='AC')`).
   - `get_user_solved_by_difficulty(10)` → `{"easy": n, "medium": n, "hard": n}`,
     grouping distinct solved problems by `problems.difficulty` (missing
     difficulties filled in as `0`).
   - `get_recent_submissions(10, limit=10)` → the 10 newest attempts, joined to
     `problems` for the title/slug.
5. The router packs it all into a `ProfileOut` and returns it.

## Flow — the leaderboard ranking

`stats.get_leaderboard()` runs one query:

```sql
SELECT u.id, u.name,
       COUNT(DISTINCT CASE WHEN js.verdict='AC' THEN js.problem_id END) AS solved_count,
       COUNT(js.id) AS submission_count
FROM users u
LEFT JOIN judge_submissions js ON js.user_id = u.id
GROUP BY u.id, u.name
HAVING solved_count > 0
ORDER BY solved_count DESC, submission_count ASC, u.name ASC
LIMIT ?
```

- `LEFT JOIN` keeps every user even with no submissions, but `HAVING
  solved_count > 0` then drops anyone who hasn't solved anything (a wall of zeros
  is noise).
- Ties on solved count break by **fewer total submissions** (the more efficient
  solver ranks higher), then by name for a stable order.
- The SQL only **sorts**; the router numbers the rows 1..N with `enumerate`, so
  the rank reflects the final ordering.

## Analogy

Think of `judge_submissions` as a stack of exam answer sheets — one sheet per
attempt. Phase 7 doesn't add new sheets; it hires a **clerk** who tallies them:

- The **profile** is one student's report card — "solved 12 problems (5 easy, 4
  medium, 3 hard), 30 attempts, 12 accepted" — read off their pile of sheets.
- The **leaderboard** is the class ranking on the notice board, sorted by who
  solved the most, computed by sweeping everyone's piles at once.

The clerk (the SQL) never writes on the sheets; it only counts.

## How to extend / gotchas

- **Count distinct problems, not rows, for "solved."** Every solved metric uses
  `COUNT(DISTINCT … problem_id)`. Switching it to `COUNT(*)` would silently
  inflate scores for anyone who submits an `AC` twice.
- **`SUM`/`COUNT` over zero rows.** A user with no submissions makes `SUM(...)`
  return `NULL`. `get_user_submission_stats` normalises with `or 0` so callers
  always get plain ints.
- **`HAVING` vs `WHERE`.** The leaderboard filters on `solved_count`, which is an
  *aggregate*, so it must use `HAVING` (after grouping), not `WHERE`.
- **Performance.** SQLite scans `judge_submissions` for these. It's fine at this
  scale; if the table grows large, add an index on
  `judge_submissions(user_id, verdict)` (and consider caching the leaderboard).
- **Adding a profile stat** (e.g. a current solving streak) = add a query to
  `stats.py`, a field to `ProfileOut`, and wire it in the router. No schema
  migration — it's all derived from existing rows.
- **No new table, no migration.** Everything is computed from data Phase 2
  already records.
