# Feature: Roles & admin panel (Backend) — Phase 6

> Adds the difference between **authentication** ("who are you?") and
> **authorization** ("what are you allowed to do?"). Until now any logged-in user
> could create problems. Phase 6 introduces a `role` on each user and locks
> problem management behind an **admin-only** set of endpoints.

---

## What & why

A real judge has two kinds of people: **users** who solve problems, and **admins**
who author them. We model that with a single `role` column (`'user'` or
`'admin'`) and a `require_admin` dependency that guards the admin routes.

The key interview point: `get_current_user` proves *who* you are (authentication);
`require_admin` builds on it to check *what you may do* (authorization). They're
separate layers — a valid token that isn't an admin gets a **403**, not a 401.

There is deliberately **no endpoint to make yourself an admin** — that's done
out-of-band with the `make_admin.py` script (an operator with server access).

---

## Files involved

| File | Purpose |
| ---- | ------- |
| `app/db/database.py` | `users` table gains `role TEXT NOT NULL DEFAULT 'user'`. Existing databases are upgraded by a tiny **migration** (`_run_migrations`) that `ALTER TABLE`s the column in if it's missing — guarded by `_column_exists`. |
| `app/db/repositories/users.py` | `set_user_role(user_id, role)` — used only by the script. |
| `app/db/repositories/tokens.py` | `get_user_by_token` now also selects `users.role`, so the logged-in row carries the role everywhere. |
| `app/db/repositories/problems.py` | `update_problem(...)` (edit fields, slug stays fixed). |
| `app/db/repositories/test_cases.py` | `get_test_case`, `delete_test_case`. |
| `app/dependencies.py` | **`require_admin`** — depends on `get_current_user`, then raises 403 unless `role == 'admin'`. |
| `app/routers/admin.py` | **New, all admin-gated.** Create/edit problems, view a problem with *all* (incl. hidden) test cases, add/delete test cases. |
| `app/routers/problems.py` | The old public `POST /problems` create endpoint was **removed** — problem creation now lives in the admin router. The slug helpers (`_unique_slug`) stay here and are imported by the admin router. |
| `app/schemas/auth.py` | `UserOut` gains `role` (so the frontend can show/hide admin UI). |
| `app/schemas/problem.py` | `ProblemUpdateRequest`, `TestCaseCreateRequest`, `TestCaseFullOut` (incl. `is_sample`), `AdminProblemDetailOut` (problem + all test cases). |
| `app/main.py` | Registers `admin.router`. |
| `make_admin.py` | CLI to promote/demote a user by email. |

### Admin endpoints (all require an admin token)

| Method & path | Does |
| ------------- | ---- |
| `POST /admin/problems` | Create a problem + its test cases + tags. |
| `PUT /admin/problems/{slug}` | Edit a problem's fields and tags (slug unchanged). |
| `GET /admin/problems/{slug}` | Full problem **including hidden test cases** (for editing). |
| `POST /admin/problems/{slug}/test-cases` | Add one test case. |
| `DELETE /admin/test-cases/{id}` | Remove one test case. |

---

## Flow — creating a problem as an admin

```
POST /admin/problems  { title, statement, …, test_cases:[…] }   Authorization: Bearer <token>
        │
        ▼
require_admin
   ├─ get_current_user(token) → row   (401 if token missing/invalid)
   └─ row["role"] == "admin"?         (403 if not)
        │ yes
        ▼
create_problem handler
   ├─ _unique_slug(title)             # shared with the public problems router
   ├─ problems.create_problem(…, created_by=admin.id)   (409 if slug clash)
   ├─ test_cases.create_test_case(…)  for each case
   └─ tags.set_problem_tags(…)
        ▼
201 { problem: { …, sample_test_cases } }
```

A regular user hitting the same URL never reaches the handler — `require_admin`
stops them with a 403.

### Becoming an admin

```
$ python make_admin.py akhil@example.com
akhil@example.com is now 'admin'.
```

Then the user logs in again (or refreshes), and their token now resolves to a row
with `role = 'admin'`.

---

## Analogy

Authentication is the **ID card** that gets you in the building. Authorization is
the **keycard** that opens the server room. Everyone with a job has an ID
(`get_current_user`); only admins' cards open the problem-authoring room
(`require_admin`). You can't print yourself an admin keycard from inside — facilities
(the `make_admin.py` operator) has to do it.

---

## How to extend / gotchas

- **Migration, not a fresh table.** `CREATE TABLE IF NOT EXISTS` never alters an
  existing table, so the `role` column is added by `_run_migrations` with
  `ALTER TABLE … ADD COLUMN`. It's guarded by `_column_exists`, so it's safe to
  run on every startup and on a brand-new DB alike. This is the pattern to copy
  for any future column.
- **The token query must select new user columns.** `require_admin` reads
  `current_user["role"]`; that only works because `get_user_by_token` selects
  `users.role`. If you add another user attribute the dependencies need, add it
  to that SELECT too (this exact bug bit us during Phase 6 and showed up as a 500,
  not a 403).
- **The UI guard is not the security boundary.** The frontend hides the admin page
  from non-admins for UX, but the backend's `require_admin` is what actually
  enforces it — every admin route is protected server-side regardless of the UI.
- **No self-service promotion by design.** Granting admin is intentionally a
  server-side script, not an API call, so the privilege can't be escalated over
  the network.
- **`seed_problems.py` is unaffected** — it writes via the repositories directly
  (not the HTTP API), so it doesn't need an admin token.
