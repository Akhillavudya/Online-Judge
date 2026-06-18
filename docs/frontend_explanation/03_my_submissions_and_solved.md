# Feature: My Submissions Page & Solved Badges (Frontend) — Phase 3

> Surfaces the new Phase 3 backend views in the UI: a single page listing **all**
> of the user's judged attempts, plus **Solved ✓** markers on the problem list and
> problem detail pages.

---

## What & why

The backend now exposes `GET /me/submissions` and `GET /me/solved`. Phase 3's
frontend gives them a face:

- A **My Submissions** page — one table of every attempt the user has made, across
  all problems, newest first (problem, verdict, tests passed, language, runtime,
  time).
- A **Solved ✓** indicator next to each solved problem in the list, and a "Solved"
  badge in the problem header — so progress is visible at a glance.

**Analogy:** the problem list becomes a checklist you can tick off, and "My
Submissions" is your activity feed.

---

## Files involved

| File | Purpose |
| ---- | ------- |
| `src/pages/MySubmissionsPage.jsx` | **New page.** Fetches `/me/submissions` and renders the table; verdicts are color-coded; each problem links back to its detail page. |
| `src/App.jsx` | Adds the protected `/submissions` route. |
| `src/components/CompilerNavbar.jsx` | Adds the "My Submissions" nav link. |
| `src/pages/ProblemsPage.jsx` | Fetches `/me/solved` alongside `/problems` and shows a green check on solved rows. |
| `src/pages/ProblemDetailPage.jsx` | Shows a "Solved" badge in the header, derived from the attempts it already loads. |

---

## Flow

### My Submissions page (`/submissions`)
1. On mount, `GET /me/submissions`.
2. Render a table; map each verdict code (`AC`/`WA`/`TLE`/`RE`/`CE`) to a label +
   color via the same `verdictMeta` lookup used on the detail page.
3. Each problem title is a `<Link>` to `/problems/{slug}` so the user can jump
   straight back to re-attempt it.
4. Empty / loading / error states are handled like the other list pages.

### Solved badges
- **Problems list:** loads the problem list and the user's solved slugs in
  parallel (`Promise.all`), stores the slugs in a `Set`, and renders a
  `CheckCircle2` icon when `solved.has(problem.slug)`. The `/me/solved` call is
  wrapped in `.catch()` so a failure there still shows the list (just without
  badges).
- **Problem detail:** no extra request — the page already loads the user's attempts
  for that problem, so `isSolved = submissions.some(s => s.verdict === 'AC')`.
  After a successful submit, the history reloads, so an `AC` makes the badge appear
  immediately.

---

## How to extend / gotchas

- **Detail-page badge is derived, not fetched.** It reuses the already-loaded
  per-problem submissions — one fewer request, and it updates live after an `AC`.
- **Solved set is built from slugs** because that's what the list already keys on;
  no id↔slug mapping needed on the client.
- **No pagination yet** — the table shows every attempt (matches the backend).
  Phase 9 adds pagination; this table is where the frontend side would plug in.
- **Phase 4 (discovery):** the same solved `Set` will sit alongside the upcoming
  difficulty/tag filters and search box on the problems list.
