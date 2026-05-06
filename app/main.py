from fastapi import FastAPI

from app.routers import admin, auth, catalog, genres, movies, reservations, showtimes, users

app = FastAPI(title="Movie Reservation API", version="1.0.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(genres.router)
app.include_router(movies.router)
app.include_router(showtimes.router)
app.include_router(catalog.router)
app.include_router(reservations.router)
app.include_router(admin.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
