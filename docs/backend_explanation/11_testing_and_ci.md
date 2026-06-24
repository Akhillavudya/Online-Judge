# 11 — Automated Testing & Continuous Integration (Phase 10)

## What & why

Up to now we verified the backend by hand: start the server, run some `curl`
commands, eyeball the responses. That works once, but it doesn't *stay* working —
the next change could quietly break login or the judge and nobody would notice
until a user did.

Phase 10 fixes that with two things:

1. **An automated test suite** (`pytest`) that spins up the real FastAPI app
   against a throwaway database and asserts the important behaviours: you can
   register and log in, only admins can create problems, hidden test cases never
   leak, and a submission gets the right verdict (Accepted vs Wrong Answer).
2. **Continuous Integration (CI)** — a GitHub Actions workflow that runs that
   suite automatically on every push and pull request. If a test fails, the
   commit is flagged red before it can cause trouble.

Together they're the difference between "it worked on my machine that one time"
and "the app is provably still working after every change."

## Files involved

| File | Purpose |
| ---- | ------- |
| `backend/requirements-dev.txt` | Test-only dependencies: `pytest` and `httpx` (the HTTP client FastAPI's `TestClient` uses under the hood). Kept separate from `requirements.txt` so production installs stay lean. |
| `backend/pytest.ini` | pytest configuration: adds the backend folder to the import path (so `import app...` works), points at the `tests/` folder, and sets quiet output. |
| `backend/tests/conftest.py` | Shared **fixtures**. The `client` fixture gives every test a `TestClient` wired to a brand-new SQLite database in a temp folder. Helper fixtures `register`, `admin`, and `make_problem` let each test set up users and problems in one line. |
| `backend/tests/test_auth.py` | Auth tests: register returns a token, duplicate email → 409, short password → 422, login success/failure, `/auth/me` needs a token. |
| `backend/tests/test_problems.py` | Problem + authorization tests: listing, non-admin create → 403, admin create works, and the key safety check that **only sample** test cases are exposed. |
| `backend/tests/test_judge.py` | The judge end-to-end: a correct Python solution → `AC`, a wrong one → `WA`, submitting without a token → 401, an unsupported language → 400, and that a submission shows up in history. |
| `.github/workflows/ci.yml` | The GitHub Actions workflow that installs the deps and runs `pytest` on Ubuntu for every push to `main` and every pull request. |

## How a test runs (end-to-end flow)

Take `test_correct_solution_gets_accepted` as the example:

1. **Isolation first.** The `client` fixture (in `conftest.py`) creates a temp
   directory and repoints `settings.DATABASE_PATH`, `CODES_DIR`, and
   `OUTPUTS_DIR` at it, then calls `init_database()`. The test gets an empty
   schema that no other test can see. It also disables the rate limiter so a test
   can submit freely.
2. **Seed data.** The `make_problem` fixture (which depends on the `admin`
   fixture) registers a user, promotes them to admin via the repository, and
   `POST`s to `/admin/problems` to create an "add two numbers" problem with one
   sample and one hidden test case. It returns the slug.
3. **Act.** The test registers an ordinary solver, then `POST`s a correct Python
   solution to `/problems/{slug}/submit`.
4. **The real judge runs.** This isn't mocked — `judge_submission` compiles
   (a no-op for Python), runs the code against *both* test cases, and compares
   output. The verdict comes back as `AC`.
5. **Assert.** The test checks `verdict == "AC"` and `passed_count ==
   total_count == 2`.

When the test finishes, `monkeypatch` (built into pytest) automatically restores
the original settings, and the temp folder is discarded.

In CI the exact same thing happens on a fresh Ubuntu machine: GitHub checks out
the code, installs Python 3.11 and the dependencies, and runs `pytest`. A green
check means all 18 tests passed; a red X blocks the change.

## Analogy

Think of the test suite as a **restaurant health inspector who visits after every
change to the kitchen.** Each fixture sets up a clean, disposable kitchen (the
temp database) so one test's mess never affects the next. The inspector then runs
through a checklist — "Can a guest be seated? Can only the manager change the
menu? Does the kitchen actually cook the dish correctly?" — and writes PASS or
FAIL next to each item. CI is the rule that says *the kitchen can't reopen
(merge) until every box on the checklist is ticked.*

## How to extend / gotchas

- **Add a test for every new feature.** When you add an endpoint, add a test in
  the matching `test_*.py` (or a new one). Reuse the `register` / `admin` /
  `make_problem` fixtures — they keep tests short.
- **Tests use Python, not C++, on purpose.** The judge is language-agnostic, so
  testing through Python means the suite needs only a Python interpreter — no
  fragile g++ setup. (CI's Ubuntu image *does* have g++ if you ever want a C++
  test.)
- **Isolation depends on reading `settings` live.** The repositories call
  `settings.DATABASE_PATH` on each query, which is why repointing it in the
  fixture works. If you ever cache a path at import time, the tests would hit the
  real `compiler.db` — don't.
- **Rate limiting is disabled in tests** by flipping `run_rate_limit.enabled` /
  `submit_rate_limit.enabled` off in the `client` fixture. Without that, a test
  that submits many times could hit a 429.
- **Run locally before pushing:** from `backend/`, `pip install -r
  requirements.txt -r requirements-dev.txt` once, then `pytest`. Same command CI
  runs, so green locally ≈ green in CI.
- **The CI workflow triggers on push to `main` and on every PR.** If you add a
  long-lived branch, add it under `on.push.branches`.
