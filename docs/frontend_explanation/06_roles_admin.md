# Feature: Admin panel & role-gated UI (Frontend) — Phase 6

> A minimal admin page for authoring problems, plus the plumbing to show it only
> to admins. Mirrors the backend's authentication-vs-authorization split: the UI
> *hides* admin tools from regular users, while the backend *enforces* the rule.

---

## What & why

The backend now returns a `role` on the user (see
`docs/backend_explanation/06_roles_admin.md`). The frontend uses it to:

1. show an **Admin** link in the navbar only for admins,
2. guard the `/admin` route so non-admins are redirected away, and
3. render a **create-problem form** that posts to `POST /admin/problems`.

The UI guard is purely UX — a determined non-admin can't do anything anyway,
because every admin API call is rejected with a 403 server-side.

---

## Files involved

| File | Change |
| ---- | ------ |
| `src/pages/AdminPage.jsx` | **New.** A form to create a problem: details (title, statement, formats, constraints, difficulty, limits, comma-separated tags) plus a dynamic list of test-case rows (add/remove, each flagged sample or hidden). On success it shows a link to the new problem and resets. |
| `src/components/ProtectedRoute.jsx` | Gained an `adminOnly` prop. When set, a logged-in non-admin is redirected to `/problems`. |
| `src/components/CompilerNavbar.jsx` | Shows an **Admin** link (amber) only when `user?.role === 'admin'`. |
| `src/App.jsx` | New `/admin` route wrapped in `<ProtectedRoute adminOnly>`. |
| `src/context/AuthContext.jsx` | Unchanged — it already stores the whole `user` object, which now includes `role`. |

---

## Flow

```
Admin logs in → AuthContext user = { …, role: 'admin' }
        │
        ├─ CompilerNavbar sees role === 'admin' → renders the "Admin" link
        │
        └─ Click Admin → /admin
                 ProtectedRoute(adminOnly) → role is admin → render AdminPage
                          │
                 fill form + test cases → submit
                          ▼
                 api.post('/admin/problems', payload)
                          ▼
                 201 → "Created … View problem →"
```

A regular user who types `/admin` directly hits `ProtectedRoute(adminOnly)` and is
bounced to `/problems`; they never see the Admin link in the first place.

---

## Analogy

Same keycard idea as the backend doc, from the user's side: regular staff simply
don't see the "Server room" button in the lift (`navbar`), and if they punch in
the floor number manually, the lift won't stop there (`ProtectedRoute`). The lock
on the door itself (the backend 403) is what actually keeps them out.

---

## How to extend / gotchas

- **`role` must round-trip.** The Admin link and route guard depend on
  `user.role`. That arrives via `/auth/login`, `/auth/register`, and `/auth/me`
  — all return `UserOut`, which now includes `role`. If those ever stop carrying
  it, the admin UI silently disappears.
- **Refresh after promotion.** A user promoted with `make_admin.py` while logged
  in won't see the Admin link until their `user` is reloaded (re-login, or the
  next `/auth/me` on app load).
- **The form posts everything at once.** Tags are entered comma-separated and
  split client-side; test cases are sent in the same `POST /admin/problems` body.
  Editing existing problems / managing individual test cases is supported by the
  backend (`PUT /admin/problems/{slug}`, the `test-cases` endpoints) but isn't in
  this minimal UI yet — a natural next addition.
