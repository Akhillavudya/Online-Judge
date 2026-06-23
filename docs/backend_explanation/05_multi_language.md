# Feature: Multi-language support — C++ and Python (Backend) — Phase 5

> Lets users solve problems in **more than one language**. Phase 5 adds **Python**
> alongside C++, and — more importantly — restructures the executor so adding the
> *next* language (Java, C, …) is a one-line change, not a rewrite.

---

## What & why

Until now the judge only ran C++. The interesting design problem isn't "make
Python run" (that's easy — `python file.py`); it's making the judge **not care**
which language it's running. We want adding a language to require **no change**
to the judge loop or the executor — only a new table entry.

That's the **open/closed principle**: the system is *open for extension* (drop in
a new language) but *closed for modification* (the judge code never changes).

Each language is one of two shapes:

| Shape | Example | Compile step? | What we run |
| ----- | ------- | ------------- | ----------- |
| **Compiled** | C++ | yes — `g++` builds a binary once | the built binary |
| **Interpreted** | Python | no | the source file, via `python` |

---

## Files involved

| File | Purpose |
| ---- | ------- |
| `app/services/languages.py` | **New.** The strategy registry. A `LanguageSpec` dataclass + a `LANGUAGES` dict mapping each language → `{extension, compile_cmd, run_cmd}`. This is the *single source of truth* for what's supported. |
| `app/services/executor.py` | Refactored to be language-agnostic. `compile_source(language, …)`, `run_executable(language, …)` and `execute_code(language, …)` all look the language up in the registry and follow its spec. `execute_cpp` was renamed to `execute_code`. |
| `app/services/judge.py` | Now takes any supported `language`. Writes the file with the language's real extension, compiles once (a no-op for interpreted languages), and runs each test case — the loop itself is unchanged. |
| `app/routers/run.py` | `POST /run` accepts any language in `SUPPORTED_LANGUAGES` (was C++ only). |
| `app/routers/problems.py` | `POST /problems/{slug}/submit` accepts any supported language. |
| `app/routers/submissions.py`, `app/routers/ai.py` | Saving a snippet and AI review now accept any supported language too, so Python works end-to-end (the problem page's **Save** uses `/submissions`). |

### The registry (`languages.py`) — the heart of this phase

```python
@dataclass(frozen=True)
class LanguageSpec:
    name: str
    extension: str                       # source file extension, no dot
    compile_cmd: Callable | None         # None = interpreted (no build step)
    run_cmd: Callable                    # how to run the prepared program

LANGUAGES = {
    "cpp":    LanguageSpec("cpp", "cpp", _cpp_compile, lambda exe: [str(exe)]),
    "python": LanguageSpec("python", "py", None, lambda src: [PYTHON_CMD, str(src)]),
}
SUPPORTED_LANGUAGES = set(LANGUAGES)
```

- `compile_cmd(source)` returns `(argv, artifact_path)` — the compiler command and
  where the binary lands. `None` means "interpreted; nothing to build".
- `run_cmd(path)` returns the argv to run, given whatever `compile_source`
  produced (a binary for compiled languages, the source file for interpreted).
- `PYTHON_CMD` is `python` on Windows, `python3` elsewhere.

---

## Flow — one submission, regardless of language

```
POST /problems/{slug}/submit  { language, code }
        │
        ▼
router checks language ∈ SUPPORTED_LANGUAGES  ──(no)──▶ 400 "Unsupported language…"
        │ (yes)
        ▼
judge_submission(language, code, cases, time_limit)
        │
        ├─ spec = get_language(language)
        ├─ generate_file(spec.extension, code)         # …uuid.cpp / …uuid.py
        ├─ compile_source(language, source)            # g++ build  OR  no-op (returns source)
        │       └─ compile fails? → verdict CE
        └─ for each test case:
               run_executable(language, exec_path, input, timeout)   # [binary]  OR  [python, source]
               → timed out? TLE.  non-zero exit? RE.  output mismatch? WA.
        → all passed → AC
```

The only language-specific decisions — *what extension*, *whether to compile*,
*how to run* — are answered by the spec. The verdict logic is identical for C++
and Python (and for any future language).

---

## Analogy

Think of the judge as a **kitchen** and each language as a **recipe card**. The
chef (judge loop) doesn't memorise recipes — they read the card: "needs baking?
(compile) → how to plate it? (run)". Adding a new dish means writing a new card
(`LanguageSpec`), not retraining the chef.

---

## How to extend / gotchas

- **Adding a language** = add one entry to `LANGUAGES`. For example C:
  ```python
  "c": LanguageSpec("c", "c",
      lambda src: (["gcc", str(src), "-o", str(out_for(src))], out_for(src)),
      lambda exe: [str(exe)]),
  ```
  Nothing in `executor.py`, `judge.py`, or the routers changes.
- **Interpreted languages don't produce `CE`.** A Python syntax error has no
  compile step to catch it, so it surfaces at run time as **RE** (the process
  exits non-zero). That's standard for a simple judge; if we ever want a
  Python-specific `CE`, we'd add an optional `python -m py_compile` pre-check.
- **The interpreter must be on the server's `PATH`.** `python` (Windows) /
  `python3` (Unix) and `g++` must be installed wherever the backend runs. This is
  one more reason Phase 8 moves execution into a Docker image that bundles the
  toolchains.
- **Still runs untrusted code directly on the host** — multi-language widens the
  attack surface (now arbitrary Python too). The Phase 8 sandbox is still the
  real fix; see the known risk noted in the project overview.
- **Frontend** still lists Java/JavaScript in the dropdown for the editor, but
  Run/Submit return a clear "Unsupported language" 400 for those — they're not in
  `SUPPORTED_LANGUAGES` yet.
