# Feature: Multi-language support (Frontend) — Phase 5

> The editor already sent a `language` field and offered a language dropdown.
> Phase 5 makes **Python actually runnable** (not just C++) and fixes the
> messaging so it tells the truth about what the backend can run.

---

## What & why

The backend now runs **C++ and Python** (see
`docs/backend_explanation/05_multi_language.md`). The frontend barely changes —
it already passed `{ language, code }` to `/run` and `/problems/{slug}/submit`.
The only stale bit was the hard-coded "Only C++ is supported" placeholder shown
when the user switched languages. We replace that with a small **runnable set**.

---

## Files involved

| File | Change |
| ---- | ------ |
| `src/pages/ProblemDetailPage.jsx` | Added `runnableLanguages = new Set(['cpp', 'python'])`. The language-change handler now shows "Run your code…" for runnable languages and "Only C++ and Python can be run right now." for the rest. |
| `src/pages/CompilerPage.jsx` | Same `runnableLanguages` set + message, applied in its language-change handler. |
| `src/components/CompilerNavbar.jsx` | Unchanged — the dropdown still lists C++ / Java / Python / JavaScript. Java & JavaScript remain selectable for editing, but Run/Submit will return a backend 400 until they're added server-side. |

No new components, routes, or API calls — `handleRun` / `handleSubmit` already
forward whatever `language` is selected.

---

## Flow

```
User picks "Python" in the dropdown
        │
        ▼
handleLanguageChange('python')
        ├─ setCode(starterCode.python)          # Python starter snippet
        ├─ monaco switches to python highlighting
        └─ runnableLanguages.has('python') → "Run your code to see the output."
        │
User clicks Run / Submit
        ▼
api.post('/run' | '/problems/{slug}/submit', { language: 'python', code })
        ▼
backend runs `python file.py` and returns output / verdict (AC/WA/TLE/RE)
```

Pick Java instead and the backend responds `400 Unsupported language. Supported:
cpp, python.`, which the existing `catch` blocks already surface in the output /
status area.

---

## Analogy

The editor is a **vending machine** with buttons for four drinks. Phase 5 stocks
a second drink (Python) behind the C++ button's neighbour. The other two buttons
still light up, but pressing them returns your coin with a note: "not stocked
yet." No rewiring of the machine — just what's on the shelf.

---

## How to extend / gotchas

- When the backend adds a language (e.g. Java in a later phase), add it to
  `runnableLanguages` in **both** pages so the messaging matches reality.
- `starterCode` and `monacoLanguage` already have entries for all four languages,
  so a newly-enabled language gets a starter template and syntax highlighting for
  free.
- The dropdown intentionally shows languages that aren't runnable yet — users can
  still write/highlight code in them. The honest error comes from the backend.
