# Deploying SYQ App on Render.com

## Overview
This guide walks you through publishing **SYQ** on **Render.com**. The backend is FastAPI with async SQLAlchemy; the frontend is a Create React App static build.

---

## Prerequisites (already configured in this repo)

1. **Database** reads `DATABASE_URL` from the environment.
   - Local dev: SQLite via `sqlite+aiosqlite:///./syq.db`
   - Render production: PostgreSQL (Render converts `postgres://` → `postgresql+asyncpg://` automatically)
2. **Frontend API URL** uses `REACT_APP_API_URL` (Create React App), not Vite.
3. **Static build output** is `frontend/build` (CRA default), not `frontend/dist`.
4. **`homepage: "."`** is set in `frontend/package.json` for relative asset paths on Render.

---

## Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: SYQ ready for Render deploy"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

---

## Step 2: Backend Web Service

1. Go to [render.com](https://render.com) and sign in with GitHub.
2. **New + → Web Service** → connect your repo, branch `main`.
3. Configure:
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
4. Environment variables:
   - `SECRET_KEY`: generate a long random string (PowerShell: `[guid]::NewGuid().ToString()`)
   - `ALLOWED_HOSTS`: `*`
   - `BACKEND_CORS_ORIGINS`: your frontend URL once deployed (e.g. `https://syq-frontend.onrender.com`)
5. Create the service and wait for the first build.

---

## Step 3: PostgreSQL Database

1. **New + → PostgreSQL** (or Integrations → Add PostgreSQL on the web service).
2. Name: `syqdb`, plan: Free.
3. Copy the **Internal Database URL** (`postgres://...`).
4. Add to the backend service environment:
   - `DATABASE_URL` = Internal Database URL
5. **Manual Deploy → Deploy latest commit**.

---

## Step 4: Frontend Static Site

1. **New + → Static Site** → same repo, branch `main`.
2. Configure:
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/build`
3. Environment variables:
   - `REACT_APP_API_URL`: `https://<your-backend>.onrender.com/api/v1`
   - `NODE_ENV`: `production`
4. Create the site.

---

## Step 5: Final CORS update

After the frontend URL is known, update the backend:

- `BACKEND_CORS_ORIGINS` = `https://<your-frontend>.onrender.com`

Then redeploy the backend.

---

## Optional: Blueprint deploy

This repo includes `render.yaml`. You can use **New + → Blueprint** to provision backend, database, and frontend in one step. Set `REACT_APP_API_URL` and `BACKEND_CORS_ORIGINS` in the Render dashboard after the first deploy.

---

## Verify

- Backend health: `https://<backend>.onrender.com/health`
- API docs: `https://<backend>.onrender.com/api/v1/docs`
- Frontend: open the static site URL and check network requests return 200.

---

## Local development

```bash
# Backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm start
```

Use `frontend/.env` with `REACT_APP_API_URL=http://localhost:8000/api/v1`.
