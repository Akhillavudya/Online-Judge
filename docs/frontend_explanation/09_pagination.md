# 09 — Paginated submission lists (Phase 9)

## What & why

Backend list endpoints now return one **page** at a time (`page`, `limit`,
`total`) instead of every row. The frontend has to ask for a page and offer the
user a way to move between pages. We wire this up on the **My Submissions** page —
the one list that genuinely grows without bound — and leave the other lists on a
sensible default.

## Files involved

| File | Change |
| ---- | ------ |
| `pages/MySubmissionsPage.jsx` | Requests `/me/submissions?page&limit`, tracks `page`/`total`, and renders a Prev/Next pager. |
| `pages/CompilerPage.jsx` | The saved-snippet sidebar shows everything, so it explicitly asks for `?limit=100`. |
| `pages/ProblemDetailPage.jsx` | Unchanged — it reads `data.submissions`, and the default first page (20 latest attempts) is plenty for a single problem. |

## End-to-end flow (My Submissions)

```
page state starts at 1
useEffect([page]) → GET /me/submissions?page={page}&limit=20
  data = { submissions, total, page, limit }
  totalPages = ceil(total / 20)
Prev/Next buttons call setPage(...) → effect re-runs → new page loads
The pager only renders when total > one page.
```

The response still has the same `submissions` array it always did, so the table
rendering didn't change — only the data-fetching and the footer pager are new.

## Beginner-friendly analogy

It's a search-results page. You don't get all 10,000 results at once — you get
"page 1 of 50" with Next/Prev at the bottom. The server tells you the **total**
so the page count is honest, and you only download the rows you're actually
looking at.

## How to extend / gotchas

- **Add a pager to another list:** copy the `page`/`total` state + the footer
  block from `MySubmissionsPage`. Compute `totalPages = Math.ceil(total / limit)`
  and guard the buttons with `disabled`.
- **Want "show everything" instead of paging?** Pass an explicit high `limit`
  (max `100`, as the backend caps it) like the Compiler sidebar does. Asking for
  more than `100` returns `422`, so don't.
- **Gotcha — reset to page 1** whenever a filter changes, or you can land on an
  empty page. (Not an issue on My Submissions today since it has no filters.)
- **Gotcha — the response shape is additive.** Old code that just read
  `data.submissions` keeps working; `total`/`page`/`limit` are extra fields you
  opt into when you add a pager.
```
