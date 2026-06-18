# Feature: Problem Discovery — search, filters, tags & pagination (Backend) — Phase 4

> Turns `GET /problems` from "dump every problem" into a real, LeetCode-style
> browse experience: **search by title**, **filter by difficulty and tag**, and
> **page** through the results.

---

## What & why

As the problem set grows, returning everything in one response stops being
practical. Phase 4 adds the query tools users expect:

| Query param | Effect |
| ----------- | ------ |
| `search` | Title contains the text (`WHERE title LIKE '%…%'`). |
| `difficulty` | Exact match: `easy` / `medium` / `hard`. |
| `tag` | Only problems carrying that tag. |
| `page` | 1-based page number (default `1`). |
| `limit` | Items per page (default `20`, max `100`). |

The response now also carries a **total** so the frontend can render a pager:
`{ "problems": [...], "total": 42, "page": 1, "limit": 20 }`.

**Tags** are modelled properly (a many-to-many relationship), not crammed into a
single column — see below.

**Analogy:** Phase 1 handed you the whole library catalogue at once. Phase 4 gives
you the library's *search desk*: filter by section (difficulty), topic (tag), or
title, and get the results a shelf (page) at a time.

---

## Data model: tags (many-to-many)

```
tags(id, name UNIQUE)
problem_tags(problem_id → problems.id, tag_id → tags.id, PRIMARY KEY(problem_id, tag_id))
```

One tag (`math`) can belong to many problems, and one problem can have many tags —
the textbook **join table** pattern. Both tables are created on startup via
`CREATE TABLE IF NOT EXISTS`, so no manual migration. Tag names are stored
**lower-cased and de-duplicated** so `Array` and `array` are the same tag.

> Why a join table instead of a comma-separated `tags` column? Filtering becomes a
> clean `JOIN … WHERE t.name = ?` instead of a fragile `LIKE '%array%'` that could
> match substrings. It's also the relational-modelling answer interviewers probe for.

---

## Files involved

| File | Purpose |
| ---- | ------- |
| `app/db/database.py` | Adds the `tags` and `problem_tags` tables. |
| `app/db/repositories/tags.py` | **New.** `list_tag_names`, `get_tags_for_problem`, `get_tags_by_problem_ids` (batch, avoids N+1), `set_problem_tags` (replace-and-create). |
| `app/db/repositories/problems.py` | `list_problems(search, difficulty, tag, limit, offset)` + `count_problems(...)`, sharing one `_build_filters` helper so the count always matches the page. |
| `app/schemas/problem.py` | `ProblemSummaryOut`/`ProblemDetailOut` gain `tags`; new `ProblemListOut` (`problems, total, page, limit`); `ProblemCreateRequest` gains `tags`. |
| `app/routers/problems.py` | `GET /problems` takes the query params; new `GET /problems/tags`; detail + create now carry tags. |
| `seed_problems.py` | Seeds tags per problem and **back-fills** tags onto already-seeded problems on re-run. |

---

## Flow: `GET /problems?search=&difficulty=&tag=&page=&limit=`

1. FastAPI validates the query params (`page >= 1`, `1 <= limit <= 100`,
   `difficulty` ∈ the `Difficulty` literal).
2. `offset = (page - 1) * limit`.
3. `_build_filters(...)` assembles a shared JOIN + WHERE clause (and its params):
   - `tag` → JOIN `problem_tags`/`tags` and `WHERE t.name = ?`,
   - `difficulty` → `WHERE p.difficulty = ?`,
   - `search` → `WHERE p.title LIKE ?`.
4. `list_problems(...)` returns that page (newest first, `LIMIT/OFFSET`);
   `count_problems(...)` runs the **same** filter to get `total`.
5. `tags.get_tags_by_problem_ids([...])` fetches every row's tags in **one** query
   and they're attached to each `ProblemSummaryOut`.
6. Respond with `{ problems, total, page, limit }`.

`GET /problems/tags` returns the distinct tag names for the filter dropdown. It is
declared **before** `GET /problems/{slug}`, otherwise `/tags` would be captured as
a slug.

---

## How to extend / gotchas

- **Route order matters:** `/problems/tags` must come before `/problems/{slug}` in
  the router, or FastAPI treats "tags" as a slug. (This is the one easy-to-miss
  trap in this phase.)
- **Count mirrors the page:** `list_problems` and `count_problems` share
  `_build_filters` on purpose — if they ever drift, the pager total won't match.
- **Tag filter is single-tag** for now. Multi-tag (AND/OR) would extend
  `_build_filters` with multiple joins or a `GROUP BY … HAVING COUNT` — left for
  later to keep it simple.
- **No N+1:** tags for a whole page come from one `WHERE problem_id IN (…)` query.
- **`LIKE` is case-insensitive** for ASCII in SQLite by default; fine for titles.
- **Phase 6 (admin):** tag editing will reuse `set_problem_tags` (already
  replace-and-create, so it doubles as an "update tags" primitive).

---

## How it was verified (running server + curl)

| Check | Result |
| ----- | ------ |
| `GET /problems/tags` | `["array","implementation","math"]` |
| `?page=1&limit=2` | `total=3`, 2 rows, each with its tags |
| `?page=2&limit=2` | the remaining 1 row |
| `?search=sum` | `total=1` → `sum-of-an-array` |
| `?tag=math` | `total=2` → `sum-of-an-array`, `a-b-problem` |
| `?difficulty=hard` | `total=0` |
| `GET /problems/a-b-problem` | `tags=["implementation","math"]` |
