# Feature: Judging Engine & Verdicts (Backend) — Phase 2

> The heart of the online judge. A user submits a solution, and the server runs it
> against **every** test case (sample + hidden) and returns a **verdict**.

---

## What & why

Phase 1 gave us problems and test cases. Phase 2 makes them mean something: when a
user submits code, the judge compiles it, runs it against all test cases, compares
the output to the expected answer, and decides one of five verdicts:

| Code | Meaning | When |
| ---- | ------- | ---- |
| `AC` | Accepted | Every test case passed |
| `WA` | Wrong Answer | Output differed on some test case |
| `TLE` | Time Limit Exceeded | A test case ran longer than the problem's limit |
| `RE` | Runtime Error | The program crashed / exited non-zero |
| `CE` | Compilation Error | The code did not compile |

Each attempt is **stored** so the user can see their history.

**Analogy:** the judge is an *examiner with the answer key*. It compiles your
answer sheet (CE if it's unreadable), then checks it question by question. The
moment it finds a wrong answer it stops and tells you the verdict and how far you
got — exactly like Codeforces.

---

## Files involved

| File | Purpose |
| ---- | ------- |
| `app/db/database.py` | Adds the `judge_submissions` table (kept separate from the snippet `submissions` table). |
| `app/db/repositories/judge_submissions.py` | SQL: `create_judge_submission`, `list_judge_submissions`. |
| `app/services/executor.py` | **Refactored** into primitives: `compile_source` (compile once) and `run_executable` (run one input, never throws, reports timeout/crash). `execute_cpp` for `/run` still works, built on top. |
| `app/services/judge.py` | **The engine.** `judge_submission()` ties it together and `_normalize()` makes output comparison forgiving of trailing whitespace. |
| `app/schemas/judge.py` | `SubmitRequest`, `JudgeSubmissionOut`, `JudgeResultOut`. |
| `app/routers/problems.py` | Adds `POST /problems/{slug}/submit` and `GET /problems/{slug}/submissions`. |

### Why split `executor.py`?

A real judge compiles the code **once** and reuses the binary for every test case
(compiling per case would be slow). So `compile_source` and `run_executable` are
now separate, and `run_executable` *returns* what happened (timed out? crashed?
runtime in ms?) instead of throwing — the judge needs to inspect each result to
pick a verdict.

### The `judge_submissions` table

```
judge_submissions
  id, user_id  →  users.id,  problem_id  →  problems.id,
  language, code,
  verdict, passed_count, total_count, runtime_ms,
  created_at
```

> It is created automatically on server startup (`CREATE TABLE IF NOT EXISTS`), so
> your existing `compiler.db` gains the table the next time you launch the app — no
> manual migration needed.

---

## Flow: `POST /problems/{slug}/submit`

1. `get_current_user` checks the token (else `401`).
2. Look up the problem by slug (`404` if missing); reject non-C++ (`400`); reject a
   problem with no test cases (`400`).
3. Load **all** test cases via `test_cases.list_all_test_cases()` (sample + hidden).
4. `judge_submission(...)` does the work:
   - writes the code to a file and **compiles once** → on failure, returns `CE`
     (with the compiler message, server path stripped to `solution.cpp`);
   - runs each test case with the problem's time limit:
     - timed out → `TLE`, stop;
     - non-zero exit → `RE`, stop;
     - `_normalize(stdout) != _normalize(expected)` → `WA`, stop;
     - otherwise count it passed;
   - all passed → `AC`.
5. Store the attempt in `judge_submissions`.
6. Return `{ "result": { verdict, passed_count, total_count, runtime_ms, detail } }`.

`GET /problems/{slug}/submissions` simply returns the current user's past attempts
for that problem, newest first.

---

## Output comparison (`_normalize`)

Judges shouldn't fail you over a stray trailing newline. `_normalize` strips
trailing whitespace from each line and drops trailing blank lines before comparing.
So `"12\n"` and `"12"` are treated as equal, but `"12"` vs `"13"` is a `WA`.

---

## How to extend / gotchas

- **Stops at first failure** — matches real judges and avoids wasted work. If you
  later want "X/Y passed" across *all* cases, remove the early `return` on `WA`.
- **Phase 5 (languages):** the judge already takes `language`; when Python/Java are
  added, give `executor.py` a per-language compile/run strategy and the judge loop
  is unchanged.
- **Phase 8 (sandbox):** `run_executable` runs the binary directly on the host —
  the place to wrap each run in a Docker container with CPU/memory/network limits.
- **Time limit:** comes from the problem's `time_limit_ms`. The measured
  `runtime_ms` is wall-clock and includes small process-startup overhead, so it
  sits a bit above pure CPU time (fine for display).

---

## How it was verified (with real g++)

| Submission | Verdict |
| ---------- | ------- |
| Correct `a+b` | `AC` 4/4 |
| Prints `a-b` | `WA` 0/4 (test case 1) |
| Syntax error | `CE` (clean `solution.cpp:` message, no server path) |
| Divide by zero | `RE` 0/4 |
| `while(true){}` | `TLE` 0/4 (~2 s limit) |

Plus: history endpoint lists all attempts newest-first; `401` without token,
`404` for unknown slug, `400` for non-C++.
