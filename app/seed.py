"""Seed genres, admin, screens, demo movies (with poster URLs), and a 14-day screening schedule."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import func, select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Genre, Movie, Screen, Seat, Showtime, User, UserRole

# Poster images from TMDB CDN (https://www.themoviedb.org/) — verified HTTP 200 as of seed authoring.
DEMO_MOVIES: list[dict[str, str]] = [
    {
        "title": "The Dark Knight",
        "description": "Batman faces the Joker in a battle for Gotham's soul.",
        "poster_image_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "genre": "Action",
    },
    {
        "title": "Dune",
        "description": "Paul Atreides leads a rebellion on the desert planet Arrakis.",
        "poster_image_url": "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
        "genre": "Sci-Fi",
    },
    {
        "title": "Inception",
        "description": "Thieves enter dreams to plant an idea in a CEO's mind.",
        "poster_image_url": "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
        "genre": "Sci-Fi",
    },
    {
        "title": "Spider-Man: No Way Home",
        "description": "Peter Parker asks Doctor Strange to make the world forget he is Spider-Man.",
        "poster_image_url": "https://image.tmdb.org/t/p/w500/iQFcwSGbZXMkeyKrxbPnwnRo5fl.jpg",
        "genre": "Action",
    },
    {
        "title": "Fight Club",
        "description": "An insomniac office worker and a soap maker start an underground fight club.",
        "poster_image_url": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        "genre": "Drama",
    },
    {
        "title": "The Matrix",
        "description": "A hacker discovers reality is a simulation and joins a rebellion against its machine overlords.",
        "poster_image_url": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
        "genre": "Sci-Fi",
    },
]


def _utc_day_start(d: datetime) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def _ensure_genres(db) -> dict[str, Genre]:
    names = ("Action", "Drama", "Sci-Fi", "Comedy")
    out: dict[str, Genre] = {}
    for name in names:
        g = db.execute(select(Genre).where(Genre.name == name)).scalar_one_or_none()
        if g is None:
            g = Genre(name=name)
            db.add(g)
            db.flush()
        out[name] = g
    return out


def _ensure_admin(db) -> None:
    exists = db.execute(select(User).where(User.email == "admin@example.com")).scalar_one_or_none()
    if exists:
        return
    db.add(
        User(
            email="admin@example.com",
            hashed_password=hash_password("adminpassword"),
            role=UserRole.ADMIN,
        )
    )


def _add_seat_grid(db, screen_id: int, rows: int, seats_per_row: int) -> None:
    for r in range(rows):
        label = chr(ord("A") + r)
        for n in range(1, seats_per_row + 1):
            db.add(Seat(screen_id=screen_id, row_label=label, seat_number=n))


def _ensure_screens(db) -> list[Screen]:
    screens = list(db.execute(select(Screen).order_by(Screen.id)).scalars())
    if len(screens) >= 2:
        return screens[:2]

    names = ["Hall 1 — IMAX", "Hall 2 — Standard"]
    for i in range(len(screens), 2):
        s = Screen(name=names[i])
        db.add(s)
        db.flush()
        _add_seat_grid(db, s.id, rows=8, seats_per_row=14)
    db.flush()
    return list(db.execute(select(Screen).order_by(Screen.id)).scalars())[:2]


def _ensure_demo_movies(db, genres: dict[str, Genre]) -> list[Movie]:
    movies: list[Movie] = []
    for spec in DEMO_MOVIES:
        m = db.execute(select(Movie).where(Movie.title == spec["title"])).scalar_one_or_none()
        if m is None:
            g = genres[spec["genre"]]
            m = Movie(
                title=spec["title"],
                description=spec["description"],
                poster_image_url=spec["poster_image_url"],
                genre_id=g.id,
            )
            db.add(m)
            db.flush()
        else:
            m.description = spec["description"]
            m.poster_image_url = spec["poster_image_url"]
            m.genre_id = genres[spec["genre"]].id
        movies.append(m)
    return movies


def _slot_taken(db, screen_id: int, starts_at: datetime) -> bool:
    row = db.execute(
        select(Showtime.id).where(Showtime.screen_id == screen_id, Showtime.starts_at == starts_at)
    ).first()
    return row is not None


def _add_planned_showtimes(db, screens: Sequence[Screen], movies: Sequence[Movie]) -> int:
    """Insert showtimes for the next 14 UTC days. Skips slots that already exist."""
    now = datetime.now(timezone.utc)
    today = _utc_day_start(now)
    utc_hours = (13, 16, 19, 22)
    prices = (1299, 1499, 1599, 1799, 1899)
    added = 0

    for day_offset in range(14):
        day = today + timedelta(days=day_offset)
        for slot_i, hour in enumerate(utc_hours):
            movie = movies[(day_offset * len(utc_hours) + slot_i) % len(movies)]
            screen = screens[(day_offset + slot_i) % len(screens)]
            starts_at = datetime(day.year, day.month, day.day, hour, 0, tzinfo=timezone.utc)
            if starts_at <= now:
                continue
            if _slot_taken(db, screen.id, starts_at):
                continue
            ends_at = starts_at + timedelta(hours=2, minutes=15)
            price = prices[(day_offset + slot_i + movie.id) % len(prices)]
            db.add(
                Showtime(
                    movie_id=movie.id,
                    screen_id=screen.id,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    price_cents=price,
                )
            )
            added += 1
    return added


def seed() -> None:
    db = SessionLocal()
    try:
        genres = _ensure_genres(db)
        _ensure_admin(db)
        screens = _ensure_screens(db)
        movies = _ensure_demo_movies(db, genres)
        db.flush()

        future_count = db.execute(
            select(func.count(Showtime.id)).where(Showtime.starts_at > datetime.now(timezone.utc))
        ).scalar_one()
        if future_count > 80:
            print("Many future showtimes already exist; skipping schedule insert.")
            db.commit()
            print("Seed baseline OK (genres / admin / movies updated).")
            print("  Admin login: admin@example.com / adminpassword")
            return

        added = _add_planned_showtimes(db, screens, movies)
        db.commit()
        print(f"Seed complete. Added {added} new showtime(s).")
        print("  Admin login: admin@example.com / adminpassword")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
