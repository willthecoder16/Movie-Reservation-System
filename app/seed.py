"""Seed genres, admin, screens, demo movies (TMDB posters), and a 14-day screening schedule."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

from sqlalchemy import select

from app.config import settings
from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Genre, Movie, Screen, Seat, Showtime, User, UserRole

_TMDB_IMG = "https://image.tmdb.org/t/p/w500"
_POSTER_MAP: dict[str, str] | None = None


def _load_tmdb_poster_map() -> dict[str, str]:
    global _POSTER_MAP
    if _POSTER_MAP is not None:
        return _POSTER_MAP
    path = Path(__file__).resolve().parent / "tmdb_poster_fallbacks.json"
    if path.exists():
        _POSTER_MAP = json.loads(path.read_text(encoding="utf-8"))
    else:
        _POSTER_MAP = {}
    return _POSTER_MAP


def _tmdb_api_poster_path(tmdb_id: int, api_key: str) -> str | None:
    q = urllib.parse.urlencode({"api_key": api_key})
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?{q}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    p = data.get("poster_path")
    if isinstance(p, str) and p.startswith("/"):
        return p
    return None


def _poster_url_for_tmdb_id(tmdb_id: int) -> str:
    """Poster from TMDB: optional live API (TMDB_API_KEY), else bundled paths from themoviedb.org."""
    api_key = (settings.tmdb_api_key or "").strip()
    if api_key:
        path = _tmdb_api_poster_path(tmdb_id, api_key)
        time.sleep(0.05)
        if path:
            return f"{_TMDB_IMG}{path}"
    path = _load_tmdb_poster_map().get(str(tmdb_id))
    if path:
        if not path.startswith("/"):
            path = "/" + path
        return f"{_TMDB_IMG}{path}"
    return ""


# (title, description, genre, tmdb_id) — IDs are themoviedb.org movie ids; posters resolved via TMDB.
_RAW_MOVIES: tuple[tuple[str, str, str, int], ...] = (
    ("The Dark Knight", "Batman faces the Joker in a battle for Gotham's soul.", "Action", 155),
    ("Dune", "Paul Atreides leads a rebellion on the desert planet Arrakis.", "Sci-Fi", 438631),
    ("Inception", "Thieves enter dreams to plant an idea in a CEO's mind.", "Sci-Fi", 27205),
    ("Spider-Man: No Way Home", "Peter Parker asks Doctor Strange to make the world forget he is Spider-Man.", "Action", 634649),
    ("Fight Club", "An insomniac office worker and a soap maker start an underground fight club.", "Drama", 550),
    ("The Matrix", "A hacker learns reality is a simulation and joins a rebellion against the machines.", "Sci-Fi", 603),
    ("Pulp Fiction", "Interlocking stories of Los Angeles mobsters, small-time criminals, and a mysterious briefcase.", "Drama", 680),
    ("The Lord of the Rings: The Fellowship of the Ring", "A hobbit and his allies set out to destroy a powerful ring.", "Action", 120),
    ("Gladiator", "A betrayed Roman general rises through the arena to avenge his family.", "Action", 98),
    ("Jurassic Park", "Scientists clone dinosaurs for a theme park—until systems fail.", "Sci-Fi", 329),
    ("Titanic", "A romance unfolds aboard the ill-fated luxury liner's maiden voyage.", "Drama", 597),
    ("Forrest Gump", "A kind-hearted man witnesses decades of American history firsthand.", "Drama", 13),
    ("The Shawshank Redemption", "Two imprisoned men bond over years, finding solace and hope.", "Drama", 278),
    ("Goodfellas", "The rise and fall of a mob associate in New York's criminal underworld.", "Drama", 769),
    ("The Godfather", "The aging patriarch of a crime dynasty transfers power to his reluctant son.", "Drama", 238),
    ("Back to the Future", "A teen accidentally travels to 1955 and must reunite his parents.", "Comedy", 105),
    ("Ghostbusters", "Parapsychologists start a ghost-catching business in New York City.", "Comedy", 620),
    ("Groundhog Day", "A cynical weatherman relives the same day until he changes his ways.", "Comedy", 1372),
    ("The Big Lebowski", "A mistaken-identity caper pulls an easygoing bowler into a kidnapping plot.", "Comedy", 115),
    ("Monty Python and the Holy Grail", "King Arthur and his knights embark on an absurd quest for the Grail.", "Comedy", 762),
    ("Blade Runner 2049", "A young blade runner uncovers a secret that could fracture society.", "Sci-Fi", 335984),
    ("Interstellar", "Explorers travel through a wormhole to find humanity a new home.", "Sci-Fi", 157336),
    ("Arrival", "A linguist races to communicate with visitors whose ships appear worldwide.", "Sci-Fi", 329865),
    ("Gravity", "Two astronauts struggle to survive after their shuttle is destroyed in orbit.", "Sci-Fi", 49047),
    ("Mad Max: Fury Road", "In a desert wasteland, fugitives flee a tyrant across a relentless chase.", "Action", 76341),
    ("John Wick", "An ex-hit-man returns to the underworld after a personal loss.", "Action", 245891),
    ("Mission: Impossible – Fallout", "Ethan Hunt races to recover plutonium before terrorists weaponize it.", "Action", 353081),
    ("Die Hard", "A New York cop battles terrorists in a Los Angeles skyscraper on Christmas Eve.", "Action", 562),
    ("Raiders of the Lost Ark", "Archaeologist Indiana Jones races Nazis to recover a biblical artifact.", "Action", 85),
    ("Jaws", "A police chief, scientist, and sailor hunt a great white shark menacing a beach town.", "Drama", 578),
    ("Alien", "The crew of a commercial tug encounters a deadly lifeform on a derelict ship.", "Sci-Fi", 348),
    ("Terminator 2: Judgment Day", "A reprogrammed cyborg protects a boy targeted by a liquid-metal assassin.", "Sci-Fi", 280),
    ("The Social Network", "The founding of Facebook sparks lawsuits and fractured friendships.", "Drama", 37799),
    ("Whiplash", "A drummer pushes himself under a ruthless conservatory instructor.", "Drama", 244786),
    ("Parasite", "A poor family schemes their way into the lives of a wealthy household.", "Drama", 496243),
    ("La La Land", "Two artists in Los Angeles chase dreams while navigating love and compromise.", "Comedy", 313369),
    ("Superbad", "Two high school friends try to score alcohol for a party before graduation.", "Comedy", 8363),
    ("Bridesmaids", "A maid of honor competes with a rival while planning her best friend's wedding.", "Comedy", 55721),
    ("Airplane!", "Passengers and crew face absurd chaos after pilots fall ill mid-flight.", "Comedy", 813),
    ("Knives Out", "A detective investigates the death of a wealthy crime novelist at a family gathering.", "Comedy", 546554),
    ("Logan", "An aging Wolverine protects a young mutant in a near-future road trip.", "Action", 263115),
    ("Edge of Tomorrow", "A soldier relives the same day fighting an alien invasion until he can win.", "Sci-Fi", 137113),
)


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
    """Upsert movies in catalog order; poster URLs from TMDB (API or bundled JSON)."""
    movies: list[Movie] = []
    for title, description, genre_name, tmdb_id in _RAW_MOVIES:
        poster_image_url = _poster_url_for_tmdb_id(tmdb_id)
        m = db.execute(select(Movie).where(Movie.title == title)).scalar_one_or_none()
        if m is None:
            g = genres[genre_name]
            m = Movie(
                title=title,
                description=description,
                poster_image_url=poster_image_url,
                genre_id=g.id,
            )
            db.add(m)
            db.flush()
        else:
            m.description = description
            m.poster_image_url = poster_image_url
            m.genre_id = genres[genre_name].id
        movies.append(m)
    return movies


def _slot_taken(db, screen_id: int, starts_at: datetime) -> bool:
    row = db.execute(
        select(Showtime.id).where(Showtime.screen_id == screen_id, Showtime.starts_at == starts_at)
    ).first()
    return row is not None


def _future_slot_starts(
    now: datetime, num_days: int, utc_hours: tuple[int, ...]
) -> list[datetime]:
    """Chronological UTC start times for the next num_days (inclusive from today UTC), future only."""
    base = _utc_day_start(now)
    slots: list[datetime] = []
    for day_offset in range(num_days):
        day = base + timedelta(days=day_offset)
        for hour in utc_hours:
            starts_at = datetime(day.year, day.month, day.day, hour, 0, tzinfo=timezone.utc)
            if starts_at > now:
                slots.append(starts_at)
    slots.sort()
    return slots


def _add_planned_showtimes(db, screens: Sequence[Screen], movies: Sequence[Movie]) -> int:
    """Insert showtimes for the next 14 UTC days.

    Each chronological slot is assigned ``movies[slot_index % n]``, so the lineup **repeats every
    n movies** while stepping through time. With six daily slots, every title appears at least once
    in the window whenever there are at least ``len(movies)`` future slots (84 max in 14 days).
    """
    now = datetime.now(timezone.utc)
    utc_hours = (11, 13, 15, 17, 19, 21)
    prices = (1299, 1499, 1599, 1799, 1899, 1999)
    added = 0

    slot_starts = _future_slot_starts(now, 14, utc_hours)
    if len(slot_starts) < len(movies):
        slot_starts = _future_slot_starts(now, 21, utc_hours)
    for idx, starts_at in enumerate(slot_starts):
        movie = movies[idx % len(movies)]
        screen = screens[idx % len(screens)]
        if _slot_taken(db, screen.id, starts_at):
            continue
        ends_at = starts_at + timedelta(hours=2, minutes=15)
        price = prices[(idx + movie.id) % len(prices)]
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
