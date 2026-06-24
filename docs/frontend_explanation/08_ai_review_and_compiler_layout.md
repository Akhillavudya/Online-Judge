# 08 — Compiler page: real AI review + one-screen layout

## What & why

Two fixes to the **Compiler page** (`/compiler`):

1. **AI review now shows the real thing.** Previously "Ask AI" always displayed
   hard-coded fallback text and three invented lines ("Time/Space: See Gemini
   review above") — it *looked* like it worked even when the backend call failed.
   Now it renders the actual Gemini markdown, with honest **loading / error**
   states (e.g. it shows "GEMINI_API_KEY is not configured…" when the key is
   missing) instead of pretending.
2. **The page fits one screen.** The editor used a fixed `58vh` height and the
   Input/Output/AI panels were each `208px`, so the page overflowed and scrolled.
   The layout is now a flex column that fills the viewport: the editor stretches
   to take the leftover space, and the three panels sit in a fixed-height row at
   the bottom that scrolls *internally*.

## Files involved

| File | Purpose |
| ---- | ------- |
| `src/pages/CompilerPage.jsx` | The page. Holds the review **state machine** and the new flex layout. |
| `src/components/Markdown.jsx` | **New.** A tiny, dependency-free markdown renderer for the review text. |
| `src/components/Panel.jsx` | Reused. Now passed `className="flex flex-col"` so its body can flex to fill a panel. |
| `src/components/Sidebar.jsx`, `CompilerNavbar.jsx` | Reused unchanged. |
| Backend `POST /ai/review` | The data source — see `docs/backend_explanation/08_ai_review.md`. |

## How the AI review state works

Instead of a fake `{quality, time, space, tips}` object, the page keeps:

- `review` — the markdown **string** returned by Gemini,
- `reviewState` — `idle | loading | ready | error`,
- `reviewError` — the message to show when a call fails.

`handleReview()` sets `loading`, calls `/ai/review`, then either stores the
`review` and flips to `ready`, or captures the backend's `detail` and flips to
`error`. Switching language or opening a saved file calls `resetReview()` →
`idle` (no stale review hangs around). The AI panel renders one of four things
based on `reviewState`; only `ready` renders `<Markdown text={review} />`.

## The Markdown component

`Markdown.jsx` is deliberately small — it only handles what the review prompt
asks Gemini to emit, so we avoid pulling in a heavy markdown dependency:

- paragraphs and line breaks,
- `**bold**` and `` `inline code` ``,
- `-` / `*` bullet lists,
- fenced ```` ``` ```` code blocks,
- `#`–`####` headings.

It's a line-based parser: it walks the text, groups consecutive lines into
blocks (code fence / list / heading / paragraph), and runs a small inline pass
for bold + code. Not a full CommonMark parser — just enough, on purpose.

## The one-screen layout

```
main  (lg:h-screen lg:overflow-hidden, flex col)
├─ CompilerNavbar                         (shrink-0)
└─ row  (flex-1 min-h-0)
   ├─ Sidebar                             (xl only)
   └─ section  (flex col, min-h-0)
      ├─ file/status bar                  (shrink-0)
      ├─ editor wrapper  (flex-1 min-h-0) ← Monaco height="100%" fills this
      └─ panels row  (shrink-0, lg:h-52)  ← Input | Output | AI, scroll inside
```

The keys: `min-h-0` on flex children lets them shrink so the editor can give the
bottom row its fixed height; `flex-1` on the editor wrapper makes it absorb the
leftover space; Monaco's `automaticLayout: true` re-fits it on resize. On
narrow/short screens the page falls back to normal scrolling (the `lg:`
prefixes), so mobile isn't clipped.

## Analogy

Like a desk that always fits the room: the **editor** is the big work surface in
the middle that grows or shrinks to fill whatever space is left, while the
**Input / Output / AI** trays are a fixed shelf along the bottom edge. Add more
to a tray and that tray scrolls — the desk never spills onto the floor (the page
never scrolls).

## How to extend / gotchas

- **Restart the backend after adding the key.** The UI can't review until
  `backend/.env` has a valid `GEMINI_API_KEY` and the server has been restarted
  (see the backend doc). A missing key surfaces as a red error in the AI panel —
  that's expected, not a frontend bug.
- **Don't fake AI output again.** If you add structure (e.g. separate complexity
  cards), drive it from real model output (have the backend return JSON), not
  placeholder strings.
- **The Markdown renderer is minimal.** If Gemini starts emitting tables or
  nested lists and you need them, extend `Markdown.jsx` or switch to
  `react-markdown` — but weigh the bundle cost first.
- **`min-h-0` is load-bearing.** Removing it from the flex children brings back
  the overflow/scroll. The editor also keeps a `min-h-[320px]` floor so it never
  collapses to nothing on short viewports.
