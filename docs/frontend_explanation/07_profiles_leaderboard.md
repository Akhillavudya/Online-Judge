# 07 — Profile & Leaderboard pages (Phase 7)

## What & why

The backend gained two summary endpoints (`GET /leaderboard`,
`GET /users/{id}/profile` — see
`docs/backend_explanation/07_profiles_leaderboard.md`). This phase puts a face on
them: two new pages that turn the raw judging data into the engagement loop every
judge has — *"how am I doing, and where do I rank?"*

- **Leaderboard** (`/leaderboard`) — a ranked table of the top solvers, with the
  signed-in user's own row highlighted.
- **Profile** (`/users/:userId`) — a stats dashboard for any one user: headline
  numbers (solved / submissions / accepted / acceptance %), a solved-by-difficulty
  breakdown, and a recent-submissions table.

## Files involved

| File | Purpose |
| ---- | ------- |
| `src/pages/LeaderboardPage.jsx` | **New.** Fetches `/leaderboard`, renders the ranked table; medals for the top 3; highlights "You". |
| `src/pages/ProfilePage.jsx` | **New.** Reads `:userId` from the route, fetches `/users/:userId/profile`, renders stat cards + difficulty breakdown + recent activity. Handles `404` (unknown user) distinctly from a network error. |
| `src/App.jsx` | Adds the `/leaderboard` and `/users/:userId` routes (both behind `ProtectedRoute`). |
| `src/components/CompilerNavbar.jsx` | Adds a **Leaderboard** nav link and a **My Profile** link (to `/users/{user.id}`) in the profile dropdown. |
| `src/components/Panel.jsx`, `src/lib/api.js`, `src/context/AuthContext.jsx` | Reused as-is (card shell, axios instance with the auth token, current user). |

## Flow — viewing the leaderboard

1. User clicks **Leaderboard** in the navbar → router renders `LeaderboardPage`.
2. On mount, `api.get('/leaderboard')` runs (the axios interceptor attaches the
   bearer token automatically).
3. While the request is in flight the page shows a "Loading…" line (`status`
   state machine: `loading → ready | error`).
4. On success it maps each entry to a row. It compares `entry.user_id` to
   `useAuth().user.id` to highlight the current user's row and tag it "You".
   Ranks 1–3 show 🥇🥈🥉; the rest show `#n`.
5. Each name links to that user's profile (`/users/:id`).

## Flow — viewing a profile

1. From the navbar dropdown **My Profile** (or any name on the leaderboard) →
   `/users/:userId`.
2. `ProfilePage` reads `userId` via `useParams()` and fetches
   `/users/:userId/profile`. The effect depends on `userId`, so navigating
   between profiles refetches.
3. Three render states beyond loading: `error` (backend down), `notfound`
   (HTTP 404 → "No such user"), and `ready`.
4. On `ready` it shows:
   - a header (name, an **Admin** badge if `role === 'admin'`, join date),
   - four headline `StatCard`s — solved, submissions, accepted, and an
     **acceptance %** computed on the client (`accepted / total`, guarded against
     divide-by-zero),
   - three difficulty cards (easy/medium/hard) from `solved_by_difficulty`,
   - a **Recent Submissions** table reusing the same verdict colour scheme as
     *My Submissions*, each row linking back to its problem.

## Analogy

If the judge is a gym, these pages are the two boards on the wall. The
**leaderboard** is the "most workouts this month" chart by the door. The
**profile** is your personal logbook — total sessions, a breakdown by exercise,
and your last few visits. The gym already recorded every visit (the submissions);
these boards just display the tallies the backend clerk added up.

## How to extend / gotchas

- **Acceptance % is a frontend calculation**, not a backend field — keep the
  divide-by-zero guard (`total_submissions > 0`) if you move or copy it.
- **404 vs error.** `ProfilePage` checks `error.response.status === 404` to show
  "No such user" instead of the generic "backend down" message. Preserve that
  branch if you refactor the fetch.
- **Reused verdict colours.** Both this page and `MySubmissionsPage` define the
  same `verdict → Tailwind classes` map. If you add or restyle a verdict, update
  both (or lift the map into a shared module).
- **The profile is public by id.** Any logged-in user can open `/users/:id`. If
  you later want private profiles, gate it on the backend, not just the UI.
- **Adding a stat card** = add the field to `ProfileOut` on the backend, then a
  `<StatCard>` here. The `StatCard` component takes `label`, `value`, and an
  optional `accent` colour.
