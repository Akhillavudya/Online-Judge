# Feature: Problems (Backend) — Phase 1

> The first step in turning the "online compiler" into an "online judge": the app
> now stores **problems** (questions to solve) and their **test cases**.

---

## What & why

An online judge needs *content* — problems for users to solve. This phase adds:

- A way to **store problems** (title, statement, difficulty, time/memory limits).
- A way to **store test cases** for each problem, split into **sample** (shown to
  the user) and **hidden** (kept secret, used by the judge in Phase 2).
- **Public read** endpoints to browse the problem set and open one problem.
- An **authenticated create** endpoint to add a problem together with its test
  cases (this will be locked down to admins only in Phase 6).

The crucial idea is the **sample vs hidden** split. If users could see every test
case, they could hard-code the answers. So the problem page only ever returns the
*sample* cases; the hidden ones never leave the server.

**Analogy:** A problem is an *exam question*; test cases are the *answer key*. You
hand the student a couple of **worked examples** (sample cases) but keep the full
**marking scheme** (hidden cases) locked in the staff room.

---

## Files involved

Following the project's layering (`routers → repositories`, see
[`00_backend_overview.md`](00_backend_overview.md)):

| File | Purpose |
| ---- | ------- |
| `app/db/database.py` | Adds two tables in `init_database()`: `problems` and `test_cases`. |
| `app/db/repositories/problems.py` | All SQL for problems: `create_problem`, `list_problems`, `get_problem_by_slug`, `slug_exists`. |
| `app/db/repositories/test_cases.py` | All SQL for test cases: `create_test_case`, `list_sample_test_cases` (public-safe), `list_all_test_cases` (judge-only, Phase 2). |
| `app/schemas/problem.py` | Request/response shapes: `ProblemCreateRequest`, `TestCaseIn`, `ProblemSummaryOut`, `ProblemDetailOut`, `TestCaseSampleOut`. Difficulty is a `Literal["easy","medium","hard"]` so bad values are auto-rejected. |
| `app/routers/problems.py` | The endpoints + a `_slugify`/`_unique_slug` helper that turns a title into a URL id like `two-sum`. |
| `app/main.py` | Registers the new router. |
| `backend/seed_problems.py` | A standalone script that inserts 3 example problems with sample + hidden cases. Safe to re-run. |

### Data model

```
problems
  id, title, slug (unique), statement,
  input_format, output_format, constraints,
  difficulty, time_limit_ms, memory_limit_mb,
  created_by (user id, nullable), created_at

test_cases
  id, problem_id  →  problems.id  (ON DELETE CASCADE),
  input, expected_output, is_sample (0/1)
```

`ON DELETE CASCADE` means deleting a problem automatically deletes its test cases.

---

## The endpoints

| Method & path | Auth | Returns |
| ------------- | ---- | ------- |
| `GET /problems` | public | `{ "problems": [summary, …] }` |
| `GET /problems/{slug}` | public | `{ "problem": {…, "sample_test_cases": [...] } }` (samples only) |
| `POST /problems` | **token required** | `201` + the created problem (samples only) |

---

## Flow: opening a problem (`GET /problems/{slug}`)

1. Browser requests `GET /problems/a-b-problem`.
2. Router (`routers/problems.py`) asks `problems.get_problem_by_slug("a-b-problem")`.
3. Not found → `404 Problem not found.`
4. Found → router asks `test_cases.list_sample_test_cases(problem_id)` — note this
   repository function has `WHERE is_sample = 1` baked in, so **hidden cases can't
   leak**.
5. `ProblemDetailOut.from_row(problem, sample_rows)` assembles the JSON and it's
   returned.

## Flow: creating a problem (`POST /problems`)

1. `get_current_user` checks the bearer token (else `401`).
2. `ProblemCreateRequest` validates the body (bad difficulty → automatic `422`).
3. `_unique_slug(title)` makes a slug, adding `-2`, `-3`… if the slug is taken.
4. `problems.create_problem(...)` inserts the row.
5. Each item in `request.test_cases` is inserted via `test_cases.create_test_case`.
6. Returns the new problem with only its sample cases.

---

## How to extend / gotchas

- **Adding a problem in practice:** either `POST /problems` with a token, or add it
  to `SEED_PROBLEMS` in `seed_problems.py` and re-run the script.
- **Phase 2 hook:** the judge will call `test_cases.list_all_test_cases()` (sample
  **and** hidden) to grade a submission. That function already exists and is
  deliberately **not** exposed through any public route.
- **Phase 6 hook:** `POST /problems` currently allows any logged-in user. When the
  `admin` role lands, swap its dependency from `get_current_user` to a
  `require_admin` check — nothing else needs to change.
- **Whitespace:** sample outputs are stored exactly as given. Phase 2's judge will
  compare **trimmed** output, so don't worry about a trailing newline here.

---

## How it was verified

- `GET /problems` returns the 3 seeded problems.
- `GET /problems/a-b-problem` returns **2** sample cases though the problem has
  **4** total — hidden cases stay hidden. ✅
- `GET /problems/does-not-exist` → `404`.
- `POST /problems` → `401` without a token, `201` with one, `422` for an invalid
  difficulty, and auto-generates a unique slug.
- Frontend builds and Vite serves the new pages (see
  [`../frontend_explanation/01_problems_pages.md`](../frontend_explanation/01_problems_pages.md)).
