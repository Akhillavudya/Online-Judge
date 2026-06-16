# Feature: Problems Pages (Frontend) — Phase 1

> The screens that let a user browse the problem set and open a single problem to
> read it and try a solution. Pairs with
> [`../backend_explanation/01_problems.md`](../backend_explanation/01_problems.md).

---

## What & why

The backend now serves problems; the frontend needs screens to show them:

- A **Problems list** — every problem with its difficulty, each row clickable.
- A **Problem detail** page — the statement, sample test cases, and a code editor
  where the user can write and **Run** code against custom input.

**Analogy:** the list page is the *table of contents* of a problem book; the detail
page is an *open chapter* with the question on one side and your scratch pad
(editor) on the other.

---

## Files involved

| File | Purpose |
| ---- | ------- |
| `src/pages/ProblemsPage.jsx` | Fetches `GET /problems` and renders the list with difficulty badges. Handles loading / error / empty states. |
| `src/pages/ProblemDetailPage.jsx` | Fetches `GET /problems/:slug`; shows statement, input/output format, constraints, limits, sample cases, and a Monaco editor wired to `POST /run`. |
| `src/App.jsx` | Adds two protected routes: `/problems` and `/problems/:slug`. |
| `src/components/CompilerNavbar.jsx` | Adds a **Problems** / **Compiler** nav link group next to the logo. |

These reuse existing building blocks: the shared `api` axios client
(`src/lib/api.js`, which auto-attaches the auth token), the `Panel` card, the
`CompilerNavbar`, and the `@monaco-editor/react` editor — so the new pages match
the rest of the app's look and feel.

---

## Flow

**List page:** mount → `api.get('/problems')` → store in state → render rows. Each
row is a `<Link to={'/problems/' + slug}>`.

**Detail page:** read `:slug` from the URL with `useParams` →
`api.get('/problems/' + slug)` → show the statement + sample cases. The first
sample's input is pre-filled into the "Input" box so **Run** works immediately.
**Run** posts to `/run` (the existing executor) and shows stdout; **Save** posts to
`/submissions` to store the code under the problem's title.

---

## How to extend / gotchas

- **Routes are protected.** Both pages are wrapped in `<ProtectedRoute>`, so a
  logged-out user is redirected to login — matching the rest of the app.
- **Only C++ runs today.** The language dropdown offers more, but the backend
  executor supports C++ only; the page shows a note for other languages (same
  behavior as the Compiler page).
- **Phase 2 hook:** a green **Submit** button will be added beside **Run** that
  calls the judge endpoint and shows a verdict (Accepted / Wrong Answer / …). The
  detail page already has the layout space for a result card.
- **Phase 4 hook:** the list page is where difficulty/tag **filters**, **search**,
  and **pagination** will be added.
