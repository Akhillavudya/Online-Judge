# Verdex FastAPI Backend

This backend uses FastAPI while keeping the same routes the frontend already expects:

- `GET /` returns `{ "online": "compiler" }`
- `POST /run` accepts `{ "language": "cpp", "code": "..." }`

## Run Locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The React frontend should point `VITE_BACKEND_URL` to:

```env
VITE_BACKEND_URL=http://localhost:8000/run
```
