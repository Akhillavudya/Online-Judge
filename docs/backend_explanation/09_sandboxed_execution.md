# Feature: Secure sandboxed execution (Backend) — Phase 8

> Until now the judge compiled and ran **untrusted user code directly on the
> host**, with the backend's own privileges. That is the single real security
> risk in the project. Phase 8 moves every compile and every run into a
> throwaway, locked-down **Docker container** — no network, capped CPU/RAM/PIDs,
> non-root, read-only filesystem.

---

## What & why

A user submits arbitrary code from the internet, and we *execute* it. Without
isolation that code could read the database file, open network connections,
exhaust memory, fork-bomb the box, or delete files. Phase 8 contains it.

Each compile and each test-case run now happens inside a short-lived container
(`docker run --rm …`) started from a tiny purpose-built image. The container is
wrapped in defence-in-depth flags:

| Flag | Threat it blocks |
| ---- | ---------------- |
| `--network none` | Exfiltration / calling out / using us as a proxy |
| `--memory` + `--memory-swap` (equal) | Memory exhaustion (swap can't be used to cheat the cap) |
| `--cpus` | One submission pegging the whole CPU |
| `--pids-limit` | Fork bombs |
| `--read-only` + `--tmpfs /tmp` | Writing/altering the filesystem (only a small scratch `/tmp`) |
| `--user nobody` | Running as root inside the container |
| `-v <work>:/work:ro` (run step) | The program tampering with its own code/binary |
| inner `timeout` | A program running forever (precise per-run time limit) |

The crucial design choice: **the judge loop is unchanged.** The executor's two
primitives — *compile once*, *run each test case* — simply delegate to the
sandbox when `USE_DOCKER_SANDBOX` is on. The verdict logic, output comparison,
and early-exit in `services/judge.py` don't know or care where the code ran.

Because compilation happens *inside* a Linux container, the binary it produces is
a Linux ELF — so the sandbox works even when the backend host is Windows/macOS,
as long as Docker is available. The feature is **off by default** so local
development needs no Docker; it's switched on at deployment.

---

## Files involved

| File | Purpose |
| ---- | ------- |
| `backend/sandbox/Dockerfile` | **New.** The sandbox image: `debian-slim` + `g++` + `python3` (plus `timeout` from coreutils). Built once: `docker build -t online-judge-sandbox backend/sandbox`. Holds *no* user code. |
| `app/services/sandbox.py` | **New, the heart of Phase 8.** `compile_in_sandbox(...)` and `run_in_sandbox(...)` — Docker-backed twins of the executor primitives, returning the *same shapes*. Builds the `docker run` argv with all the isolation flags. `docker_available()` caches a PATH check; `SandboxError` flags a misconfiguration (sandbox on but Docker missing). |
| `app/services/executor.py` | `compile_source` and `run_executable` now **delegate** to `sandbox` when `settings.USE_DOCKER_SANDBOX` is true (lazy import to avoid a cycle). `run_executable` gained a `memory_mb` argument (used by the sandbox, ignored on the host path). |
| `app/services/judge.py` | `judge_submission(...)` gained `memory_limit_mb` and threads it into `run_executable`. Loop otherwise unchanged. |
| `app/routers/problems.py` | The submit handler passes the problem's `memory_limit_mb` into the judge. |
| `app/config.py` | New settings: `USE_DOCKER_SANDBOX`, `SANDBOX_IMAGE`, `SANDBOX_MEMORY_MB`, `SANDBOX_CPUS`, `SANDBOX_COMPILE_MEMORY_MB`, `SANDBOX_COMPILE_TIMEOUT_S`, `SANDBOX_DIR`. Plus an `_env_bool` helper. |
| `backend/.env.sample` | Documents the new env vars (sandbox `0`/off by default). |
| `backend/.gitignore` (+ root) | Ignore the per-submission `sandbox_work/` scratch folder. |

---

## Flow — judging a submission with the sandbox ON

```
POST /problems/{slug}/submit        (USE_DOCKER_SANDBOX=1)
        │
        ▼
judge_submission(language, code, cases, time_limit_ms, memory_limit_mb)
        │
        ├─ compile_source(...)  ──►  sandbox.compile_in_sandbox(...)
        │      • make sandbox_work/<uuid>/, write solution.<ext>
        │      • docker run (writable /work):  g++ -O2 -o solution solution.cpp
        │      • non-zero exit  → CompilationError → verdict CE
        │      • returns the Linux binary path inside that folder
        │
        └─ for each test case:
               run_executable(...)  ──►  sandbox.run_in_sandbox(...)
                  • docker run --rm -i --network none --memory … --cpus …
                      --pids-limit 64 --read-only --tmpfs /tmp
                      --user nobody -v <work>:/work:ro
                      timeout --kill-after=1 <secs> ./solution
                  • feed the test input on stdin, capture stdout
                  • exit 124  → timed_out → TLE
                  • non-zero  → RE      (incl. OOM-kill = exceeded --memory)
                  • stdout ≠ expected → WA
        ▼
Verdict (AC / WA / TLE / RE / CE)  — exactly as before
```

The host execution path (sandbox **off**) is untouched and still the default.

### Turning it on (deployment host)

```
$ docker build -t online-judge-sandbox backend/sandbox
$ export USE_DOCKER_SANDBOX=1            # or set it in backend/.env
# restart the backend
```

---

## Analogy

Before Phase 8, we handed a stranger's program the **keys to our house** and asked
it to run in the living room. The sandbox instead puts the program in a **sealed
glass booth**: no phone line out (`--network none`), a fixed amount of air
(`--memory`), a timer on the door (`timeout`), it can't repaint the walls
(`--read-only`), can't invite a crowd (`--pids-limit`), and wears a visitor badge
not the owner's (`--user nobody`). When it's done — or misbehaves — we throw the
whole booth away (`--rm`). What it does inside can't touch the house.

---

## How to extend / gotchas

- **Adding a language touches two tables.** The *host* commands live in
  `services/languages.py`; the *container* commands live in `_SANDBOX_SPECS` in
  `services/sandbox.py` (Linux paths, `python3`, no `.exe`). Add an entry to both,
  and make sure the sandbox image actually has that compiler/runtime installed
  (edit the Dockerfile and rebuild).
- **TLE vs RE come from exit codes.** The inner `timeout` exits **124** when it
  kills a slow program → that's our TLE signal. Anything else non-zero is RE —
  including an **out-of-memory kill** (the kernel SIGKILLs a program that blows
  past `--memory`). The fixed verdict set has no MLE, so memory overflow surfaces
  as RE; that's intentional and documented here.
- **Two timeouts, on purpose.** The inner coreutils `timeout` enforces the real
  per-run limit precisely; the outer `subprocess` timeout (`limit + grace`) is
  only a safety net for container startup, so reported `runtime_ms` includes a
  little startup overhead. It's a display value, not used to decide TLE.
- **Sandbox on but Docker missing = `SandboxError`.** That's a *server config*
  error (a 500), not a user CE/RE. Only set `USE_DOCKER_SANDBOX=1` where Docker is
  installed and the image is built.
- **The image holds no user code.** Code is bind-mounted per submission into
  `/work` — writable only for the compile step, read-only for runs. The
  `sandbox_work/` scratch folder is gitignored.
- **Windows bind-mount caveat.** On a Linux host the `-v <path>:/work` mount is a
  normal POSIX path. If you ever enable the sandbox on Docker Desktop for Windows,
  the host path needs Docker's `//c/...` form — not handled here because the
  intended target is a Linux deploy host.
- **Why compile as root but run as `nobody`?** Compilation needs to *write* the
  binary into the mounted `/work`; it's already isolated (no network, limits,
  `--rm`). The far riskier step — running arbitrary compiled logic — is the one
  fully dropped to `nobody` on a read-only filesystem.
