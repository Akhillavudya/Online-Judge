# Project Documentation

Plain-language explanations of how this Online Judge works, written for people
reading the code for the first time.

## Layout

```
docs/
├── backend_explanation/     ← how the FastAPI backend works
│   └── 00_backend_overview.md   ← START HERE for the backend big picture
└── frontend_explanation/    ← how the React frontend works
    └── 00_frontend_overview.md  ← START HERE for the frontend big picture
```

## Documentation convention (important)

**Every time we add a new feature** — backend or frontend — we add a matching
`.md` file in the correct folder explaining it.

Rules for a feature doc:

1. **Location** — `docs/backend_explanation/` for backend features,
   `docs/frontend_explanation/` for frontend features.
2. **Name** — `NN_short_feature_name.md`, where `NN` is a two-digit order prefix
   (e.g. `01_authentication.md`, `02_code_execution.md`). The `00_*_overview.md`
   file is always the big-picture intro.
3. **Explain properly**, in this shape:
   - **What & why** — what the feature does and the problem it solves.
   - **Files involved** — which routers / services / repositories / schemas /
     components it touches, each with its purpose.
   - **Flow** — trace one request or interaction end-to-end.
   - **Analogy** — a simple real-world comparison so a beginner "gets it".
   - **How to extend / gotchas** — anything a future contributor should know.
4. **Keep it truthful** — when code changes, update its doc. The code is always
   the source of truth.
