# Backend — The Big Picture

> A friendly, file-by-file tour of the Online Judge backend for anyone reading
> this code for the first time. No prior knowledge of the project required.

---

## 1. What is this backend, in one sentence?

It is a **FastAPI web server** that lets a user sign up, log in, save C++ code
snippets, **compile and run** that C++ code, and ask an **AI to review** it.

The React frontend talks to it over HTTP (JSON in, JSON out).

---

## 2. The restaurant analogy (read this first)

Think of the backend as a **restaurant**. A customer (the frontend) never walks
into the kitchen — they only talk to the waiter. Behind the scenes, lots of
specialists each do one job:

| Restaurant role            | In our code            | Job                                              |
| -------------------------- | ---------------------- | ------------------------------------------------ |
| The **waiter**             | `routers/`             | Takes your order, brings back the dish. Nothing else. |
| The **chefs**              | `services/`            | Do the real cooking (compile & run code, call the AI). |
| The **pantry/storeroom**   | `db/repositories/`     | The only people allowed to touch the food storage (the database). |
| The **storeroom door**     | `db/database.py`       | Opens a connection to the storage room.          |
| The **order slip format**  | `schemas/`             | The printed form that says exactly what a valid order looks like. |
| The **ID checker / bouncer** | `dependencies.py`    | Checks your membership card (token) before you're served. |
| The **safe / locksmith**   | `core/security.py`     | Locks away passwords; issues membership cards.   |
| The **restaurant rulebook** | `config.py`           | One binder with every address, phone number, and house rule. |
| The **restaurant manager** | `main.py`              | Opens the restaurant, assigns waiters to tables. |

**The golden rule of this restaurant:** the waiter never cooks and never enters
the storeroom. If a router (waiter) needs data, it asks a repository (storeroom);
if it needs work done, it asks a service (chef). This separation is what makes
the code easy to understand and change.

---

## 3. The layers (and the one rule that ties them together)

```
   HTTP request
        │
        ▼
   routers/         ← waiter: read request, call someone, return JSON
        │
        ├──────────────► services/        ← chefs: compile/run code, AI review
        │                     │
        ▼                     ▼
   db/repositories/      (subprocess g++, urllib → Gemini)
        │   ← storeroom: every SQL query lives here
        ▼
   db/database.py        ← the door to the SQLite file (compiler.db)
```

Helpers that sit beside the layers:

- `config.py` — the single source of settings & file paths (everyone reads it).
- `core/security.py` & `core/time.py` — tiny shared tools.
- `schemas/` — the shape of every request and response.
- `dependencies.py` — the auth check reused by every protected route.

**The rule:** *Routers never write SQL. SQL never lives outside `db/repositories/`.*
If you remember only one thing, remember that.

---

## 4. The folder map

```
backend/
├── app/                     ← all application code lives here
│   ├── main.py              ← entry point: builds & wires the app
│   ├── config.py            ← settings + paths (the rulebook)
│   ├── dependencies.py      ← get_current_user (the bouncer)
│   │
│   ├── core/                ← low-level shared tools
│   │   ├── security.py      ← hash passwords, make tokens
│   │   └── time.py          ← now_iso() timestamp
│   │
│   ├── db/                  ← everything about the database
│   │   ├── database.py      ← open a connection, create tables
│   │   └── repositories/    ← ALL SQL lives here
│   │       ├── users.py
│   │       ├── tokens.py
│   │       └── submissions.py
│   │
│   ├── schemas/             ← request/response shapes (Pydantic)
│   │   ├── auth.py
│   │   ├── submission.py
│   │   ├── run.py
│   │   └── ai.py
│   │
│   ├── routers/             ← the HTTP endpoints (the waiters)
│   │   ├── health.py
│   │   ├── auth.py
│   │   ├── submissions.py
│   │   ├── run.py
│   │   └── ai.py
│   │
│   └── services/            ← the real work (the chefs)
│       ├── file_manager.py  ← write code to a file
│       ├── executor.py      ← compile & run C++
│       └── ai_review.py     ← ask Gemini for a review
│
├── codes/                   ← (auto-created) user source files land here
├── outputs/                 ← (auto-created) compiled binaries land here
├── compiler.db              ← the SQLite database file
├── requirements.txt         ← Python dependencies
├── .env.sample              ← example environment variables
└── README.md                ← how to run it
```

---

## 5. File-by-file explanation

### `app/main.py` — the manager who opens the restaurant
- **Purpose:** Build the FastAPI application and connect all the pieces.
- **What it does:** `create_app()` turns on CORS (so the browser frontend is
  allowed to call us), registers every router, and uses a **lifespan** handler to
  run `init_database()` once at startup (so the tables exist before any request).
- **Analogy:** The manager unlocks the doors each morning, makes sure the
  storeroom shelves exist, and tells each waiter which section to serve.
- **You run it with:** `uvicorn app.main:app --reload`.

### `app/config.py` — the rulebook
- **Purpose:** Read environment variables (from `.env`) **once** and expose them
  as a single `settings` object.
- **Holds:** the allowed frontend origin (`CORS_ORIGIN`), the database path, the
  `codes/` and `outputs/` folder paths, password-hashing strength, and the Gemini
  API key/model.
- **Analogy:** One binder at the front desk with every address and house rule.
  Nobody scribbles rules on sticky notes around the building.

### `app/dependencies.py` — the bouncer (`get_current_user`)
- **Purpose:** Turn an `Authorization: Bearer <token>` header into the matching
  user, or reject the request with `401`.
- **How it's used:** Any protected endpoint declares
  `current_user = Depends(get_current_user)` and FastAPI runs this *before* the
  endpoint.
- **Analogy:** The bouncer checks your membership card at the door so the waiter
  inside can assume you're allowed to be there.

### `app/core/security.py` — the safe and the locksmith
- **Purpose:** All cryptography in one place.
- **Functions:**
  - `hash_password()` — scrambles a password with PBKDF2 + a random salt so the
    real password is never stored.
  - `verify_password()` — checks a login attempt **in constant time** (so timing
    can't leak the answer).
  - `generate_token_value()` — mints a fresh random login token.
- **Analogy:** Passwords go in a one-way safe; the locksmith hands out
  membership cards (tokens).

### `app/core/time.py` — the clock
- **Purpose:** `now_iso()` returns the current UTC time as a standard string, so
  every table stores timestamps the same way.

### `app/db/database.py` — the storeroom door
- **Purpose:** `get_connection()` opens a SQLite connection (configured so rows
  can be read by column name). `init_database()` creates the `users`,
  `auth_tokens`, and `submissions` tables if they don't exist yet.
- **Analogy:** The single door into the storeroom, and the blueprint that builds
  the shelves the first time.

### `app/db/repositories/` — the storeroom staff (ALL SQL lives here)
- **`users.py`** — create a user, find a user by email or id.
- **`tokens.py`** — store a token, find the user a token belongs to, delete a
  token (logout).
- **`submissions.py`** — create / list / get / update / delete a user's saved
  code. Every query is scoped by `user_id` so you can only ever touch your own data.
- **Analogy:** The only people allowed to put things on or take things off the
  shelves. Waiters must ask them — they never reach in themselves.

### `app/schemas/` — the order slips (Pydantic models)
- **Purpose:** Describe exactly what valid JSON looks like, both incoming
  (requests) and outgoing (responses). FastAPI validates requests against these
  automatically and returns a clean `422` if the shape is wrong.
- **`auth.py`** — `RegisterRequest`, `LoginRequest`, and `UserOut` (the safe
  public view of a user — never the password).
- **`submission.py`** — create/update request shapes + `SubmissionOut`.
- **`run.py`** — `RunRequest` (language, code, optional stdin).
- **`ai.py`** — `AIReviewRequest`.
- **Analogy:** A pre-printed order form. If a field is missing or the wrong type,
  the kitchen rejects the slip before cooking begins.

### `app/routers/` — the waiters (HTTP endpoints)
Each file groups related endpoints with an `APIRouter`. Routers stay **thin**:
read the request → call a service/repository → return the result.

- **`health.py`** — `GET /` → `{"online": "compiler"}`. A heartbeat check.
- **`auth.py`** — `POST /auth/register`, `/auth/login`, `/auth/me`, `/auth/logout`.
  Handles signup/login and hands back a token.
- **`submissions.py`** — full CRUD under `/submissions` (all require a token).
- **`run.py`** — `POST /run`: validates the code, asks the file_manager to save
  it, asks the executor to compile & run it, returns the output.
- **`ai.py`** — `POST /ai/review`: validates, calls the AI service, returns the
  review.

### `app/services/` — the chefs (the real work)
- **`file_manager.py`** — `generate_file()` writes the submitted code to a
  uniquely named file in `codes/` (a random UUID name so two runs never collide).
- **`executor.py`** — `execute_cpp()` compiles the file with `g++`, then runs the
  binary with a **5-second timeout** (so an infinite loop can't hang the server).
  Compile/run errors become a `RuntimeError` carrying the compiler message.
- **`ai_review.py`** — `review_code()` builds a prompt and calls Google Gemini.
  It knows **nothing** about FastAPI: on failure it raises `AIReviewError` with a
  suggested status code, and the router decides how to show it.
- **Analogy:** The chefs. They don't greet customers; they just cook and hand the
  dish back to the waiter.

---

## 6. Follow one request end-to-end: `POST /run`

This is the heart of an online judge, so let's trace it like a story:

1. **Browser → waiter.** The frontend sends `{"language":"cpp","code":"...","input":"3 4"}`
   to `POST /run`.
2. **Order slip check.** FastAPI validates the body against `RunRequest`
   (`schemas/run.py`). Wrong shape → automatic `422`.
3. **Waiter's quick checks** (`routers/run.py`): empty code → `400 Empty code!`;
   non-C++ language → `400`.
4. **Chef #1 plates the file** (`services/file_manager.py`): the code is written
   to `codes/<uuid>.cpp`.
5. **Chef #2 cooks** (`services/executor.py`): `g++` compiles it to a binary in
   `outputs/`, then runs it, feeding `"3 4"` to standard input, with a 5s timeout.
6. **Result travels back.** The program prints `7`. The waiter returns
   `{"filePath": "...", "output": "7"}` as JSON.
7. **If cooking fails** (compile error / crash), the chef raises `RuntimeError`,
   and the waiter turns it into a `500` whose message is the compiler's own error
   text — handy to show the user.

Every other feature follows the same shape: **validate → call a
service/repository → return JSON.**

---

## 7. Why is it split up like this? (the payoff)

- **Easy to find things.** "Where do I add an endpoint?" → `routers/`. "Where's
  the SQL?" → `repositories/`. No more scrolling one giant file.
- **Safe to change.** Swapping SQLite for Postgres later means editing only the
  `db/` layer; routers don't change. Adding Python support means a new
  `services/executor` path; schemas and auth don't change.
- **Easy to test.** Services and repositories are plain functions with no HTTP
  baggage, so they can be tested in isolation.

---

## 8. How to add a new feature (the recipe)

1. Add/extend a **schema** in `schemas/` (the request/response shape).
2. Put any **database** work in a `db/repositories/` function.
3. Put any **real logic** (external calls, computation) in a `services/` module.
4. Add a thin **router** that wires steps 1–3 together and register it in
   `main.py`.
5. **Document it:** create a new `.md` in `docs/backend_explanation/` (or
   `docs/frontend_explanation/`) describing the feature — see
   `docs/README.md` for the convention.

---

*This document describes the architecture, not every line. When code and docs
disagree, the code is the source of truth — please update this file.*
