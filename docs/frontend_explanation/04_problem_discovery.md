# Feature: Problem Discovery UI — search, filters & pagination (Frontend) — Phase 4

> Gives the Problems page a search box, difficulty + tag dropdowns, tag chips on
> each row, and Prev/Next paging — all driven by the new Phase 4 query params.

---

## What & why

The backend now accepts `search`, `difficulty`, `tag`, `page`, and `limit` and
returns a page of problems plus a `total`. This phase wires the UI to those:

- A **search box** (debounced) that filters by title as you type.
- **Difficulty** and **tag** dropdowns (the tag list comes from `GET /problems/tags`).
- **Tag chips** on each problem row (and the detail header).
- A **pager** ("Showing 1–20 of 42", Prev/Next).
- The Phase 3 **Solved ✓** marker still shows per row.

**Analogy:** the page goes from a printed list to a search results screen — type,
filter, flip pages.

---

## Files involved

| File | Purpose |
| ---- | ------- |
| `src/pages/ProblemsPage.jsx` | Rewritten: filter bar, debounced search, pagination, tag chips, solved markers. |
| `src/pages/ProblemDetailPage.jsx` | Shows the problem's tag chips under the title. |

---

## Flow

1. **Once on mount:** fetch `/me/solved` (→ a `Set` of solved slugs) and
   `/problems/tags` (→ the dropdown options). Both fail-soft.
2. **Search is debounced:** typing updates `search` immediately, but a 300 ms timer
   copies it into `debouncedSearch` and resets to page 1 — so we don't fire a
   request on every keystroke.
3. **The list effect** re-runs whenever `debouncedSearch`, `difficulty`, `tag`, or
   `page` changes. It builds the query params (omitting empty ones), calls
   `GET /problems`, and stores `problems` + `total`.
4. Changing a dropdown resets `page` to 1 (you don't want to land on page 3 of a
   freshly narrowed result set).
5. **Pager:** `totalPages = ceil(total / limit)`; Prev/Next are disabled at the
   ends. The row number is computed as `(page - 1) * limit + index + 1` so numbering
   continues across pages.

A small `active` flag in the effect ignores a stale response if the user changes a
filter before the previous request returns (avoids flicker / out-of-order results).

---

## How to extend / gotchas

- **Debounce vs. immediate:** only the text search is debounced; dropdown and page
  changes fire right away (a single deliberate click, not a stream of keystrokes).
- **Reset page on filter change** — handled in the dropdown handlers and the
  debounce effect. Forgetting this is the classic "empty results on page 5" bug.
- **Tag chips are hidden on very small screens** (`hidden sm:flex`) to keep rows
  readable; difficulty + solved stay visible.
- **Solved set is fetched once**, not per page — it's small and global to the user.
- **Phase 5/6:** the same filter bar is where a "language" or "status
  (solved/attempted/todo)" filter would slot in next.
