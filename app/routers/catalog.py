from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Movie, Showtime
from app.schemas.movie import MoviePublic, MovieWithShowtimesForDate, ShowtimePublic

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _utc_day_bounds(d: date) -> tuple[datetime, datetime]:
    start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


@router.get("/movies-by-date", response_model=list[MovieWithShowtimesForDate])
def movies_for_date(
    day: date = Query(..., alias="date"),
    db: Session = Depends(get_db),
) -> list[MovieWithShowtimesForDate]:
    start, end = _utc_day_bounds(day)
    showtimes = db.execute(
        select(Showtime)
        .where(Showtime.starts_at >= start, Showtime.starts_at < end)
        .options(joinedload(Showtime.movie).joinedload(Movie.genre))
        .order_by(Showtime.starts_at)
    ).unique()

    by_movie: dict[int, tuple[Movie, list[Showtime]]] = {}
    for st in showtimes.scalars():
        movie = st.movie
        if movie.id not in by_movie:
            by_movie[movie.id] = (movie, [])
        by_movie[movie.id][1].append(st)

    out: list[MovieWithShowtimesForDate] = []
    for movie, sts in by_movie.values():
        mp = MoviePublic.model_validate(movie)
        out.append(
            MovieWithShowtimesForDate(
                movie=mp,
                showtimes=[ShowtimePublic.model_validate(x) for x in sts],
            )
        )
    out.sort(key=lambda x: x.movie.title)
    return out
