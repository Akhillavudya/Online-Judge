# Frontend — The Big Picture

> This folder holds plain-language explanations of the React frontend. This
> overview is a stub to be filled in; feature docs are added here as features land.

## What the frontend is

A **React + Vite** single-page app (in `frontend/`) that gives the user a code
editor, a "Run" button, login/signup screens, and a list of saved submissions.
It talks to the FastAPI backend over HTTP using `axios`.

## Key files (quick map — expand as documented)

- `frontend/src/lib/api.js` — the configured `axios` client; automatically
  attaches the saved bearer token to every request.
- `frontend/src/context/AuthContext.jsx` — holds the logged-in user/token and
  shares it across the app.
- `frontend/src/pages/` — the screens (editor, login, etc.).
- `frontend/src/components/` — reusable UI pieces.

## Documentation convention

When a new **frontend** feature is added, create a
`NN_feature_name.md` file in this folder following the structure in
[`../README.md`](../README.md): *what & why, files involved, flow, analogy,
how to extend.*

> This is a starter overview. Flesh out the sections above (and add per-feature
> docs) as the frontend is documented.
