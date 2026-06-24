# Online Judge — End-to-End Implementation Plan

> A phase-by-phase roadmap to grow this project from a code runner into a real
> online judge (like Codeforces / LeetCode / GeeksforGeeks), then deploy it.
>
> **Design philosophy:** keep it simple. Every choice here is something a B.Tech
> final-year student with average React + FastAPI can build and *explain* in an
> interview. We deliberately avoid heavy architecture (microservices, Kafka,
> Kubernetes). A little complexity is fine where it's standard (Docker sandbox,
> JWT, Postgres) — those are exactly the things interviewers like to hear about.

---

## Where the project is today (Phase 0 — DONE ✅)

You already have a solid foundation:

- **Auth** — register / login / logout with hashed passwords + bearer tokens.
- **Submissions** — save / list / edit / delete code snippets per user.
- **Run code** — compile & run C++ with `g++` (5s timeout).
- **AI review** — Gemini-powered code feedback.
- **Clean layered backend** — `routers → services → repositories` (see
  `docs/backend_explanation/00_backend_overview.md`).

**What's missing to be a real "judge":** problems, hidden test cases, and an
automatic **verdict** (Accepted / Wrong Answer / TLE…). That's Phases 1–2 and the
single most important thing for impressing an interviewer.

---

## The big picture (what we're building)

```
User browses Problems  →  opens a Problem  →  writes code  →  Submits
                                                                  │
                                                                  ▼
                                                   Judge runs code against
                                                   ALL hidden test cases
                                                                  │
                                                                  ▼
                              Verdict: Accepted ✅ / Wrong Answer ❌ / TLE ⏱ / …
                                                                  │
                                                                  ▼
                          Saved to submission history + updates user's solved count
```

Everything else (tags, difficulty, search, leaderboard, contests) is polish
*around* this core loop.

---

## Phase-by-phase roadmap

Each phase is shippable on its own. Build them in order — later phases assume the
earlier ones exist. Suggested effort assumes part-time work.

| Phase | Theme | Why it matters in interviews |
| ----- | ----- | ---------------------------- |
| 1 | Problems | Turns the app into a judge; shows data modeling |
| 2 | Judging engine + verdicts | **The core.** Shows algorithms + system thinking |
| 3 | Submission history & status | Shows real product UX |
| 4 | Problem discovery (list/filter/search) | Shows pagination & query design |
| 5 | Multi-language support | Shows extensible design |
| 6 | Roles & admin panel | Shows authorization, not just authentication |
| 7 | Profiles & leaderboard | Shows aggregation queries; engagement |
| 8 | Secure sandboxed execution | **Big interview talking point** |
| 9 ✅ | Hardening (pagination, rate limit, validation) | Shows production awareness |
| 10 ✅ | Testing + CI | Shows engineering maturity |
| 11 | Deployment | Shows you can ship |
| 12 | Optional wow-features (contests, etc.) | Stretch goals |

---

### Phase 1 — Problems (the content the judge serves) ✅ DONE

**Goal:** Users can browse problems and read a problem statement.

> Implemented — see `docs/backend_explanation/01_problems.md` and
> `docs/frontend_explanation/01_problems_pages.md`. Endpoints `GET /problems`,
> `GET /problems/{slug}` (sample cases only), `POST /problems`; frontend
> `ProblemsPage` + `ProblemDetailPage`; 3 seeded problems via `seed_problems.py`.

**Data model (new tables):**
- `problems` — `id, title, slug, statement, input_format, output_format,
  constraints, difficulty (easy/medium/hard), time_limit_ms, memory_limit_mb,
  created_by, created_at`.
- `test_cases` — `id, problem_id, input, expected_output, is_sample (bool)`.
  *Sample* cases are shown to the user; the rest are hidden and used for judging.

**Backend (`backend/app/`):**
- `db/repositories/problems.py`, `db/repositories/test_cases.py` (all SQL here).
- `schemas/problem.py` — `ProblemOut`, `ProblemDetailOut`, `ProblemCreateRequest`.
- `routers/problems.py` — `GET /problems`, `GET /problems/{slug}` (returns the
  statement + **only sample** test cases).

**Frontend (`frontend/src/`):**
- `pages/Problems.jsx` — list of problems (title, difficulty).
- `pages/ProblemDetail.jsx` — statement + sample cases + the existing code editor.

**Interview value:** clean relational modeling; the sample-vs-hidden test-case
distinction is exactly how real judges work.

---

### Phase 2 — Judging engine & verdicts (⭐ the heart of the project) ✅ DONE

**Goal:** A user submits code to a problem and gets an automatic verdict.

> Implemented — see `docs/backend_explanation/02_judging_engine.md` and
> `docs/frontend_explanation/02_submit_and_verdict.md`. `judge_submissions` table,
> `services/judge.py` (compile-once + run all cases), `POST /problems/{slug}/submit`
> and `GET /problems/{slug}/submissions`; frontend Submit button + color-coded
> verdict card + history. All five verdicts (AC/WA/TLE/RE/CE) verified with g++.

**Concept:** Reuse your existing `services/executor.py`, but instead of returning
raw output, **run the code against every test case** and compare output to the
expected output.

**Verdicts (keep this exact set — it mirrors Codeforces):**
| Verdict | Meaning |
| ------- | ------- |
| `AC` Accepted | All test cases passed |
| `WA` Wrong Answer | Output differs on some case |
| `TLE` Time Limit Exceeded | A case exceeded the problem's time limit |
| `RE` Runtime Error | Program crashed / non-zero exit |
| `CE` Compilation Error | Code didn't compile |

**Data model:**
- Extend `submissions` (or add a new `judge_submissions` table) with:
  `problem_id, verdict, passed_count, total_count, runtime_ms, language`.

**Backend:**
- `services/judge.py` — new service:
  1. compile once (CE if it fails),
  2. loop over test cases, run with the problem's time limit,
  3. compare trimmed output → decide verdict (stop early on first failure),
  4. return verdict + how many cases passed.
- `routers/submissions.py` (or new `routers/judge.py`) — `POST /problems/{slug}/submit`.

**Frontend:**
- "Submit" button beside "Run". Show a result card: verdict badge, `passed/total`,
  runtime. Color-code (green AC, red WA, etc.).

**Keep it simple:** judge **synchronously** at first (request waits for the
result). Mention in interviews that a production judge would use a **queue +
worker** (see Phase 12) — knowing *why* is enough; you don't have to build it.

**Interview value:** This is the story you tell. Output comparison, time limits,
early-exit, verdict logic = real problem-solving.

---

### Phase 3 — Submission history & status ✅ DONE

**Goal:** Every submission is recorded and viewable.

> Implemented — see `docs/backend_explanation/03_submission_history.md` and
> `docs/frontend_explanation/03_my_submissions_and_solved.md`. New `me` router:
> `GET /me/submissions` (all attempts across problems, JOINed with the problem
> title/slug) and `GET /me/solved` (slugs with an `AC`). Frontend `MySubmissions`
> page at `/submissions` + nav link, and "Solved ✓" markers on the problem list
> and problem-detail header. Per-problem history already shipped in Phase 2.

- `GET /problems/{slug}/submissions` (the current user's attempts on a problem).
- `GET /me/submissions` — all attempts across problems, with verdict + problem.
- Frontend: a "My Submissions" table (problem, verdict, language, time).
- Mark a problem as **Solved** for a user once they get `AC` (used in Phase 7).

**Interview value:** product thinking + showing state over time.

---

### Phase 4 — Problem discovery (list, filter, search, pagination) ✅ DONE

**Goal:** Browse like LeetCode's problem set.

> Implemented — see `docs/backend_explanation/04_problem_discovery.md` and
> `docs/frontend_explanation/04_problem_discovery.md`. Normalized `tags` +
> `problem_tags` join tables; `GET /problems?search=&difficulty=&tag=&page=&limit=`
> returns `{problems, total, page, limit}` (each problem carries its tags, fetched
> in one batched query); new `GET /problems/tags` (declared before `/{slug}`).
> Frontend filter bar (debounced search + difficulty/tag dropdowns), pagination,
> tag chips, and the Phase 3 Solved markers. Seed back-fills tags on re-run.

- **Filters:** by difficulty and by tag (normalized `problem_tags` table).
- **Search:** by title (`WHERE title LIKE ?`).
- **Pagination:** `GET /problems?page=1&limit=20` — returns items + total count.
- Frontend: filter dropdowns, a search box, a "Solved ✓" indicator per row.

**Interview value:** pagination and query parameters are a classic interview topic.

---

### Phase 5 — Multi-language support ✅ DONE

**Goal:** Let users solve in more than C++.

> Implemented — see `docs/backend_explanation/05_multi_language.md` and
> `docs/frontend_explanation/05_multi_language.md`. New `services/languages.py`
> registry (`LanguageSpec` + `LANGUAGES` dict → `{extension, compile_cmd,
> run_cmd}`, plus `SUPPORTED_LANGUAGES`); `executor.py` refactored to be
> language-agnostic (`compile_source`/`run_executable`/`execute_code` all take a
> `language`); the judge loop is unchanged. **C++ + Python** supported; all five
> verdicts (AC/WA/TLE/RE/CE) verified for both. Routers (`run`, `submit`,
> `submissions`, `ai`) validate against `SUPPORTED_LANGUAGES`. Frontend shows the
> correct runnable-language messaging. Adding the next language = one entry in
> `LANGUAGES`.

- Start with **Python** (easiest — no compile step, just `python file.py`), then
  optionally **Java** / **C**.
- Refactor `services/executor.py` into a small per-language strategy: a dict
  mapping `language → {extension, compile_cmd, run_cmd}`. The judge loop stays the
  same.
- Frontend: language dropdown in the editor (you already send `language`).

**Interview value:** the "open/closed principle" in practice — adding a language
shouldn't change the judge.

---

### Phase 6 — Roles & admin panel ✅ DONE

**Goal:** Only admins can create problems and test cases.

> Implemented — see `docs/backend_explanation/06_roles_admin.md` and
> `docs/frontend_explanation/06_roles_admin.md`. `users.role` column added via a
> startup `ALTER TABLE` migration (`_run_migrations`/`_column_exists` in
> `database.py`); `require_admin` dependency (401→403 layering on
> `get_current_user`). New admin-gated `routers/admin.py`: create/edit problems,
> view a problem with all (incl. hidden) test cases, add/delete test cases. The
> old public `POST /problems` was removed. `make_admin.py` promotes a user by
> email (no self-promote endpoint). `get_user_by_token` now selects `role`;
> `UserOut` exposes it. Frontend: `AdminPage` create-problem form, `/admin` route
> behind `<ProtectedRoute adminOnly>`, and a role-gated Admin nav link. Full
> authorization flow (403 for users, 201 for admins) verified over HTTP.

- Add `role` (`user` / `admin`) to the `users` table.
- A `require_admin` dependency (built on your existing `get_current_user`).
- Admin endpoints: create/edit problems, add test cases (`POST /admin/problems`…).
- A minimal admin page in the frontend (a form — doesn't need to be pretty).

**Interview value:** the difference between **authentication** (who you are) and
**authorization** (what you're allowed to do) — interviewers love this distinction.

---

### Phase 7 — Profiles & leaderboard ✅ DONE

**Goal:** Engagement + showing aggregation queries.

> Implemented — see `docs/backend_explanation/07_profiles_leaderboard.md` and
> `docs/frontend_explanation/07_profiles_leaderboard.md`. New
> `db/repositories/stats.py` holds all the `GROUP BY`/`COUNT` aggregation
> (leaderboard ranking + per-user profile numbers); `schemas/stats.py`
> (`LeaderboardEntryOut`, `ProfileOut`, `SolvedByDifficulty`) and `routers/stats.py`
> expose `GET /leaderboard` and `GET /users/{id}/profile`. Solved counts use
> `COUNT(DISTINCT … problem_id WHERE verdict='AC')`; the leaderboard `LEFT
> JOIN`s users, filters `HAVING solved_count > 0`, orders by solved desc then
> fewest submissions, and the router assigns 1-based ranks. No new table/migration.
> Frontend: `LeaderboardPage` (`/leaderboard`, highlights you, medals top 3) and
> `ProfilePage` (`/users/:userId`, stat cards + difficulty breakdown + recent
> activity), plus navbar links. Verified end-to-end over HTTP (register → admin →
> create easy problem → AC submit → profile shows 1 solved / easy=1, leaderboard
> ranks the user).

- **Profile page:** total solved, solved-by-difficulty, recent submissions.
- **Leaderboard:** rank users by number of problems solved
  (`GROUP BY user_id ... ORDER BY solved DESC`).
- Optional: a simple submissions "heatmap" / streak (nice visual, low effort).

**Interview value:** `GROUP BY` / `COUNT` aggregation and a tiny bit of ranking
logic.

---

### Phase 8 — Secure sandboxed execution (⭐ big talking point) ✅ DONE

> Implemented — see `docs/backend_explanation/09_sandboxed_execution.md`. New
> `backend/sandbox/Dockerfile` (debian-slim + g++ + python3) and
> `services/sandbox.py` provide Docker-backed twins of the executor primitives:
> `compile_in_sandbox` / `run_in_sandbox` run each compile and test-case run in a
> throwaway `docker run --rm` container with `--network none`, `--memory` +
> `--memory-swap`, `--cpus`, `--pids-limit`, `--read-only` + a small `/tmp`
> tmpfs, `--user nobody`, a read-only code mount, and an inner coreutils
> `timeout` (exit 124 → TLE). `executor.py` delegates to the sandbox when
> `USE_DOCKER_SANDBOX` is set (off by default, so local dev needs no Docker); the
> judge loop is unchanged. The problem's `memory_limit_mb` is now threaded through
> the judge into the container's RAM cap. Compiling *inside* the container means
> the binary is a Linux ELF, so it works from any host with Docker.

**Goal:** Run untrusted user code safely. **Right now your judge runs code
directly on the host — that's the one real risk to call out.**

Keep it simple but correct:
- Run each submission inside a **Docker container** with:
  - no network access (`--network none`),
  - CPU/memory limits (`--memory`, `--cpus`),
  - a non-root user and a read-only filesystem,
  - the time limit you already enforce.
- The judge service shells out to `docker run …` instead of running the binary
  directly.

**Interview value:** This single feature signals you understand *security* and
*operating a judge*. Even explaining the threat model well is impressive. (If
Docker-in-deploy is too much, at minimum document the risk and the plan.)

---

### Phase 9 — Hardening for the real world ✅ DONE

> Implemented — see `docs/backend_explanation/10_hardening.md` and
> `docs/frontend_explanation/09_pagination.md`. List endpoints (`/me/submissions`,
> `/submissions`, `/problems/{slug}/submissions`) now take `page`/`limit` and
> return a `total` (repos gained optional `LIMIT`/`OFFSET` + `count_*` helpers);
> the My Submissions page got a Prev/Next pager. A hand-rolled fixed-window
> limiter (`services/rate_limit.py`, `RateLimit` dependency keyed by token or IP)
> guards `/run` and `/submit` (429 + `Retry-After`, configurable, `0` disables).
> `main.py` configures one log format/level (`logging_config.py`), logs one line
> per request + a verdict audit line per submission, and adds a catch-all
> exception handler that logs the traceback but returns a generic
> `{"detail": "Internal server error."}` (no leaks). CORS is now a configurable
> list (`CORS_ORIGINS`). Verified live: limiter 429s after the limit, paginated
> responses return `{items, total, page, limit}`, bad `limit` → 422.

Small, high-signal production touches:
- **Pagination everywhere** that returns lists.
- **Rate limiting** on `/run` and `/submit` (e.g. `slowapi`) so nobody abuses the
  compiler.
- **Consistent error responses** and input validation (Pydantic already helps).
- **Logging** of submissions and errors.
- **CORS / env config** reviewed for production (you already have `config.py`).

**Interview value:** shows you think beyond the happy path.

---

### Phase 10 — Testing + CI ✅ DONE

> Implemented — see `docs/backend_explanation/11_testing_and_ci.md`. New
> `backend/requirements-dev.txt` (`pytest` + `httpx`), `backend/pytest.ini`
> (`pythonpath=.`, `testpaths=tests`), and a `backend/tests/` suite (18 tests).
> `conftest.py` gives every test an isolated SQLite DB in a temp folder (repoints
> `settings.DATABASE_PATH`/`CODES_DIR`/`OUTPUTS_DIR` via `monkeypatch`, calls
> `init_database`, disables the rate limiters) plus `register`/`admin`/
> `make_problem` helper fixtures. `test_auth.py` (register/login/me + 409/422/401),
> `test_problems.py` (listing + admin-only 403/401 + hidden-cases-never-leak),
> `test_judge.py` (real submissions: correct→AC, wrong→WA, 401/400, history). Tests
> use **Python** so CI needs only an interpreter, not g++. `.github/workflows/ci.yml`
> runs `pytest` on Ubuntu/py3.11 for every push to `main` and every PR. All 18
> tests pass locally.

- **Backend tests** with `pytest` — auth, a problem, and a judge run (AC + WA).
  (You'll need to add `httpx` for FastAPI's `TestClient`.)
- **GitHub Actions** workflow that runs the tests on every push.
- Optional: a few frontend component tests.

**Interview value:** automated tests + green CI badge = engineering maturity.

---

### Phase 11 — Deployment (ship it 🚀)

Keep the stack cheap and simple:
- **Database:** move from SQLite to **Postgres** for production (managed free tier
  on Railway/Render/Supabase). Your repository layer means only `db/` changes.
- **Backend:** containerize with a `Dockerfile` (install `g++`/compilers), deploy
  to **Render** or **Railway**. Set env vars (`CORS_ORIGIN`, DB URL, `GEMINI_*`).
- **Frontend:** deploy the Vite build to **Vercel** or **Netlify**; point
  `VITE_API_URL` at the backend.
- **Docs:** update `README.md` with a live demo link and setup steps.

**Interview value:** "here's the live link" beats any slide. Be ready to explain
the deploy diagram (frontend host → backend host → DB).

---

### Phase 12 — Optional "wow" features (stretch goals)

Only after the core is solid. Pick 1–2 that excite you:
- **Contests** — a problem set with a start/end time and a contest leaderboard
  (simplified Codeforces rounds).
- **Async judging with a queue** — submissions go to a queue; a background worker
  judges them and updates the verdict (your interview answer to "how does this
  scale?"). Even a simple in-process background task counts.
- **Code editor upgrade** — Monaco editor (the VS Code editor) for syntax
  highlighting.
- **Discussion / editorial** per problem.
- **Partial scoring / subtasks** (GfG-style).

---

## Suggested build order (cheat sheet)

```
1  Problems  →  2  Judging+Verdicts  →  3  History  →  4  Discovery
        →  5  Languages  →  6  Admin  →  7  Profiles/Leaderboard
        →  8  Sandbox  →  9  Hardening  →  10  Tests/CI  →  11  Deploy
        →  12  (optional) Contests / async queue
```

**Minimum to call it an "Online Judge" in your resume:** Phases 1–3.
**Minimum to genuinely impress:** Phases 1–8 + 11 (deployed, sandboxed judge with
verdicts, multi-language, admin).

---

## How this maps to the existing code

| New work | Where it goes (reuse the current structure) |
| -------- | ------------------------------------------- |
| New tables | `db/database.py` (`init_database`) |
| New SQL | `db/repositories/<name>.py` |
| Request/response shapes | `schemas/<name>.py` |
| Business logic (judge, languages) | `services/<name>.py` |
| New endpoints | `routers/<name>.py` + register in `main.py` |
| Auth/role checks | extend `dependencies.py` |

**Remember the project rule:** every feature above gets its own explanation doc in
`docs/backend_explanation/` or `docs/frontend_explanation/` (see `docs/README.md`).

---

## A note on staying simple

- Keep **synchronous judging** until you actually need scale — then talk about
  queues, don't necessarily build them.
- Keep **SQLite** for development; only switch to Postgres at deployment.
- Don't add a feature you can't explain. Depth on Phases 1–2 + 8 beats a long
  shallow feature list.

*This is a living plan — tick off phases as you go and adjust freely.*
