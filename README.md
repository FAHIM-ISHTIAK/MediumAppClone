# MediumAppClone

A Medium-style full-stack app with:

- FastAPI backend
- SQLAlchemy async ORM
- Alembic migrations
- Vite + React frontend
- Supabase-based authentication

## Project structure

```text
.
├── app/                # FastAPI app
├── alembic/            # Database migrations
├── tests/              # Backend test suite
├── Frontend/           # Vite + React frontend
├── seed.py             # Seed script for sample data
├── requirements.txt    # Backend dependencies
├── Dockerfile          # Backend container image
└── render.yaml         # Render deployment config
```

## Tech stack

- Python 3.11 recommended
- Node.js 20+ recommended
- FastAPI
- SQLAlchemy async
- Alembic
- React
- Vite
- Supabase Auth

## Quick start

If you just want the app running locally with the fewest moving parts:

1. Start the backend with the default SQLite database.
2. Start the frontend.
3. Add Supabase frontend env vars if you want login to work.

Backend data can run entirely on local SQLite. Authentication still depends on Supabase tokens and credentials.

## Backend setup

### 1. Create and activate a virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

If `python3.11` is not available, use your local Python 3.11 binary.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

Important notes:

- If you do nothing else, the backend defaults to `sqlite+aiosqlite:///./medium_clone.db`.
- The sample `.env.example` is configured for Supabase/Postgres.
- For fully local backend development, you can leave out `DATABASE_URL` and let SQLite be used.

### Backend environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | No | Main database URL. Defaults to local SQLite if unset. |
| `DATABASE_CONNECTION_MODE` | No | `auto`, `direct`, `session`, or `transaction`. Default is `auto`. |
| `SUPABASE_URL` | Needed for auth | Supabase project URL. |
| `SUPABASE_JWT_SECRET` | Needed for HS256 auth | Secret used to validate Supabase JWTs. |
| `FRONTEND_URL` | Recommended | Comma-separated allowed CORS origins. |

### 4. Run database migrations

Run this for Postgres or SQLite before starting the app:

```bash
alembic upgrade head
```

### 5. Start the backend server

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://localhost:8000
```

## Frontend setup

### 1. Install dependencies

```bash
cd Frontend
npm install
```

### 2. Configure frontend environment variables

```bash
cp .env.example .env
```

Frontend env vars:

| Variable | Required | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | Recommended | Backend API base URL. Default is `http://localhost:8000`. |
| `VITE_SUPABASE_URL` | Needed for login | Supabase project URL. |
| `VITE_SUPABASE_ANON_KEY` | Needed for login | Supabase anon/public key. |

### 3. Start the frontend

```bash
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

## Local development workflows

### Simplest local backend flow

Use SQLite and skip Supabase database setup:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

This is enough for local API work and backend development.

### Full app flow with auth

If you want Google login and authenticated frontend flows:

1. Set backend `SUPABASE_URL` and `SUPABASE_JWT_SECRET`.
2. Set frontend `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
3. Keep `FRONTEND_URL=http://localhost:5173`.
4. Start backend and frontend.

### Supabase/Postgres backend flow

If you want the backend to use Supabase Postgres instead of SQLite:

1. Put your Supabase connection string in `DATABASE_URL`.
2. Optionally set `DATABASE_DIRECT_URL`.
3. Run `alembic upgrade head`.
4. Start the backend.

The config automatically handles Supabase pooler modes:

- `auto`: prefers direct URL when present; otherwise promotes transaction pooler URLs to session mode
- `direct`: forces `DATABASE_DIRECT_URL`
- `session`: forces session pooler port
- `transaction`: keeps transaction pooler safeguards enabled

## Seeding sample data

After migrations, populate the database with sample users, articles, publications, responses, highlights, and library activity:

```bash
python seed.py
```

The seed script skips execution if users already exist in the database.

## Running tests

The test suite uses an in-memory SQLite database and does not require your real database.

Run all tests:

```bash
pytest
```

Run a specific file:

```bash
pytest tests/test_config.py
```

Run with verbose output:

```bash
pytest -v
```

## Authentication notes

- The frontend uses Supabase for login.
- The backend verifies Supabase access tokens.
- If `SUPABASE_URL` or frontend Supabase env vars are missing, login-related flows will not work correctly.
- Unauthenticated or public endpoints can still be tested locally without full auth setup.

## Useful commands

### Backend

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
alembic upgrade head
pytest
python seed.py
```

### Frontend

```bash
cd Frontend
npm install
npm run dev
npm run build
npm run preview
```

## Docker

Build the backend image:

```bash
docker build -t medium-clone-api .
```

Run it:

```bash
docker run --rm -p 8000:8000 --env-file .env medium-clone-api
```

## Deployment

`render.yaml` contains a Render service definition for the backend. You still need to provide these environment variables in Render:

- `DATABASE_URL`
- `SUPABASE_JWT_SECRET`
- `SUPABASE_URL`
- `FRONTEND_URL`

## Common issues

### Frontend loads but login fails

Usually caused by missing:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- backend `SUPABASE_URL`
- backend `SUPABASE_JWT_SECRET`

### CORS errors

Set `FRONTEND_URL` in the backend `.env` to include your frontend origin, for example:

```env
FRONTEND_URL=http://localhost:5173,http://localhost:3000
```

### Database connection problems with Supabase

Check:

- `DATABASE_URL`
- `DATABASE_DIRECT_URL`
- `DATABASE_CONNECTION_MODE`

If you are not intentionally using Supabase Postgres locally, remove `DATABASE_URL` and use SQLite instead.
