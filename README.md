# TruthLens

TruthLens is a simple but powerful proof-of-concept for verifying news claims. It lets a user paste a headline or paragraph, then checks live news coverage and a local classifier to show whether the claim is likely supported, disputed, or mixed.

## What This Project Does

TruthLens combines a modern frontend with a backend that:

- accepts user claims through a clean React interface
- generates search queries from the claim text
- fetches live news results from Google News RSS
- weighs evidence from trusted sources
- shows a verdict, confidence score, and evidence breakdown
- falls back to a local ML classifier when live data is limited

## Why This Project Matters

This project is a good showcase of full-stack work because it:

- connects frontend and backend cleanly
- uses live external data alongside a local model
- visualizes results in a user-friendly way
- is structured for deployment with separate frontend and backend services

## Structure

- `frontend/`
  - React + Vite app
  - sends claim text to the backend API
  - displays verdict details, source summaries, and confidence metrics

- `backend/`
  - Flask API service
  - loads a saved ML model and vectorizer from `backend/model/`
  - builds claim-focused search queries
  - fetches news data from Google News RSS
  - computes source stance and verdict confidence

## Folder structure

- `frontend/`
  - `src/` — React source files, including `App.jsx`
  - `package.json` — frontend dependencies and scripts
  - `vite.config.js` — Vite configuration
  - `public/` — static assets served by Vite

- `backend/`
  - `app.py` — Flask API implementation
  - `requirements.txt` — Python dependencies
  - `model/` — saved ML model and vectorizer files

## Tech Stack

- Frontend: React, Vite, Axios, Lucide React icons
- Backend: Python, Flask, Flask-CORS, scikit-learn model persistence
- Deployment: Render for backend, Vercel for frontend

## Run Locally

### Backend

```powershell
cd backend
python -m venv venv
.
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Local environment variable

```env
VITE_API_URL=http://localhost:5000
```

## Deployment Notes

- Deploy the `frontend/` folder to Vercel.
- Deploy the `backend/` folder to Render.
- Set `VITE_API_URL` in the frontend environment to the deployed backend URL.

## Resume-Friendly Highlights

- End-to-end full-stack implementation with frontend, backend, and ML.
- Real-time news verification use case.
- Clear separation of frontend and backend responsibilities.
- Deployment-ready configuration for Vercel and Render.
