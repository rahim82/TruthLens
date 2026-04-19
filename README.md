# TruthLens Deployment Notes

This repository is set up for a single Vercel project using Services:

- `frontend/` serves the Vite web app at `/`
- `backend/app.py` serves the Flask API at `/api`

## Local development

Backend:

```powershell
cd backend
.\venv\Scripts\python.exe app.py
```

Frontend:

```powershell
cd frontend
npm run dev
```

Optional local env for frontend:

```env
VITE_API_URL=http://localhost:5000
```

## Vercel deployment

1. Import the repo into Vercel.
2. In Project Settings, set **Framework Preset** to `Services`.
3. Deploy from the repo root.

The frontend uses:

- `VITE_API_URL` if you provide it
- otherwise `/api` in production
- otherwise `http://localhost:5000` during local frontend development

That means deployed browser requests stay same-origin and do not need a public API URL override.
