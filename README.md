# Movie Reservation System

Full-stack demo for cinema reservations: **FastAPI** + **PostgreSQL** backend and a **React (Vite)** frontend. Users sign up, browse showtimes by date, pick seats, and manage reservations. **Admins** manage movies, showtimes, screens, genres, users, and reporting.

---

## What you can do

| Role | Capabilities |
|------|----------------|
| **Guest** | Sign up, log in |
| **User** | Browse the schedule by date, open a showtime, pick seats on a theater-style map, create reservations, view **My reservations**, cancel **upcoming** bookings only |
| **Admin** | Everything a user can do, plus **Admin** panel: summary stats, reservation list, CRUD movies, create/delete showtimes, manage genres & screens, promote users to admin |

API documentation (when the backend is running): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Prerequisites

- **Docker** (recommended) or PostgreSQL 16+ you can reach with a connection string  
- **Python 3.10+**  
- **Node.js 20+** and npm (for the frontend)

---

## 1. Start the database

From the repository root:

```bash
docker compose up -d
```

This starts PostgreSQL on **port 5432** with user `movie`, password `movie`, database `movie_reservation` (see `docker-compose.yml`).

---

## 2. Configure the backend

Copy the example env file and adjust if needed:

```bash
cp .env.example .env
```

Important variables (see `app/config.py`):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL URL (default matches Docker Compose) |
| `SECRET_KEY` | JWT signing secret — **set a long random value in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (default in `.env.example` is one week) |

---

## 3. Install Python dependencies and migrate

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
```

---

## 4. Seed demo data

Populates genres, an **admin** account, demo screens/seats, **40+ movies**, and a rolling **14-day** showtime schedule (skips inserting new showtimes if many future slots already exist — safe to re-run).

```bash
python -m app.seed
```

**Admin login (after seed):**

- Email: `admin@example.com`  
- Password: `adminpassword`

Create normal accounts via **Sign up** in the UI or `POST /auth/register` in `/docs`.

---

## 5. Run the API

From the repository root (with the virtual environment active):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 6. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually [http://localhost:5173](http://localhost:5173)).

The app calls the API at **`http://127.0.0.1:8000`** by default (`frontend/src/api.js`). To point at another host, set:

```bash
# frontend/.env.local (create if needed)
VITE_API_BASE=http://your-api-host:8000
```

**CORS:** the backend allows `http://localhost:5173` and `http://127.0.0.1:5173` (`app/main.py`). If you change the Vite port or origin, add it there and restart the API.

Production build:

```bash
cd frontend
npm run build
npm run preview   # optional local preview of the build
```

---

## Typical usage flow

1. **Start** Docker, run migrations, **seed**, then **uvicorn** and **`npm run dev`**.  
2. **Sign up** a new user or log in as **admin** with the credentials above.  
3. **Dashboard** — pick a date, choose a movie/showtime, **select seats**, confirm reservation.  
4. **My reservations** — see bookings; **Cancel** only applies to showtimes that have not started yet (enforced on the server).  
5. As **admin**, open **Admin** — manage movies/showtimes, view reports, promote a user to admin if you need another admin account.

---

## Project layout (high level)

| Path | Role |
|------|------|
| `app/main.py` | FastAPI app, CORS, routers |
| `app/routers/` | Auth, users, catalog, movies, showtimes, reservations, admin |
| `app/models/` | SQLAlchemy models |
| `app/seed.py` | Idempotent seed data |
| `alembic/` | Database migrations |
| `frontend/src/` | React UI (dashboard, booking, reservations, admin) |

---

## Troubleshooting

- **`Failed to fetch` in the browser** — confirm the API is running, `VITE_API_BASE` matches the API URL, and the browser origin is allowed by CORS.  
- **Database connection errors** — check `DATABASE_URL`, that PostgreSQL is up, and port **5432** is not used by another service.  
- **Re-seeding** — Running `python -m app.seed` again updates demo movies and admin password hash logic as implemented; showtime inserts may be skipped when there are already many future showtimes (see messages in the seed output).

---

## License

Use and modify for learning or your own projects; add a license file if you distribute the project.
