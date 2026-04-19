# TruthLens Deployment Notes

This repo is configured for a split deployment:

- `frontend/` -> deploy to **Vercel**
- `backend/` -> deploy to **Render**

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

Optional local frontend env:

```env
VITE_API_URL=http://localhost:5000
```

## Backend on Render

Create a **Web Service** from the `backend` directory with:

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`

After deploy, confirm:

- `https://your-backend.onrender.com/health`

## Frontend on Vercel

Create a Vercel project using the `frontend` directory as the root.

Set this environment variable in Vercel:

```env
VITE_API_URL=https://your-backend.onrender.com
```

Then redeploy the frontend.

## Notes

- The frontend now expects `VITE_API_URL` in production.
- Backend CORS is already enabled in Flask.
- Model files stay in `backend/model/` and are loaded at startup.
