# Feature: Submit & Verdict (Frontend) — Phase 2

> The "Submit" button and the verdict UI on the problem page. Pairs with
> [`../backend_explanation/02_judging_engine.md`](../backend_explanation/02_judging_engine.md).

---

## What & why

Phase 1's problem page could only **Run** code against your own input. Phase 2 adds
**Submit**, which sends the code to the judge and shows the result:

- a **verdict card**, color-coded (green Accepted, red Wrong Answer, amber TLE,
  orange Runtime Error, violet Compilation Error), with `passed/total` and runtime;
- a **My Submissions** history panel listing previous attempts and their verdicts.

**Analogy:** Run is *checking your answer on scratch paper*; Submit is *handing the
exam to the examiner* and getting it back graded.

---

## Files involved

All changes are in one file:

| File | Change |
| ---- | ------ |
| `src/pages/ProblemDetailPage.jsx` | Adds the **Submit** button, the verdict result card, the **My Submissions** panel, and the `verdictMeta` color/label map. |

It reuses what already exists: the `api` axios client (auto-attaches the token),
the `Panel` card, and the Monaco editor — nothing new was added to the project.

---

## Flow

1. On load, the page calls `GET /problems/:slug/submissions` to fill the **My
   Submissions** history.
2. The user writes code and clicks **Submit** (`handleSubmit`).
3. It `POST`s to `/problems/:slug/submit` with `{ language, code }`.
4. The returned `result` is shown in the verdict card; the status flips to the
   verdict; the history is refreshed so the new attempt appears at the top.
5. On an HTTP error it shows a fallback `ERR` card with the server's detail message.

`verdictInfo(code)` maps a verdict code (e.g. `WA`) to its label
("Wrong Answer") and Tailwind colors, so the card and the history chips stay
consistent.

---

## How to extend / gotchas

- **Run vs Submit:** Run still posts to `/run` (custom input, no verdict); Submit
  posts to the judge. The on-page tip explains the difference to users.
- **Only C++ runs** today; submitting another language returns `400` and is shown
  in the verdict card.
- **Phase 3 hook:** a global "My Submissions" page and a per-problem "Solved ✓"
  badge build directly on the history endpoint already wired here.
- **Clicking a past submission** to reload its code into the editor would be a small,
  nice addition (the data is already in `submissions` state).
