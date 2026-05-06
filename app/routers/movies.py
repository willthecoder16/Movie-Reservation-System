from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_admin
from app.models import Genre, Movie, User
from app.schemas.movie import MovieCreate, MoviePublic, MovieUpdate

router = APIRouter(prefix="/movies", tags=["movies"])


def _load_movie_public(db: Session, movie_id: int) -> Movie:
    movie = db.execute(
        select(Movie).where(Movie.id == movie_id).options(joinedload(Movie.genre))
    ).unique().scalar_one()
    return movie


@router.get("", response_model=list[MoviePublic])
def list_movies(db: Session = Depends(get_db)) -> list[Movie]:
    rows = db.execute(
        select(Movie).options(joinedload(Movie.genre)).order_by(Movie.title)
    ).unique()
    return list(rows.scalars())


@router.get("/{movie_id}", response_model=MoviePublic)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> Movie:
    movie = db.execute(
        select(Movie).where(Movie.id == movie_id).options(joinedload(Movie.genre))
    ).unique().scalar_one_or_none()
    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    return movie


@router.post("", response_model=MoviePublic)
def create_movie(
    body: MovieCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Movie:
    genre = db.get(Genre, body.genre_id)
    if genre is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid genre_id")
    movie = Movie(
        title=body.title,
        description=body.description,
        poster_image_url=body.poster_image_url,
        genre_id=body.genre_id,
    )
    db.add(movie)
    db.commit()
    return _load_movie_public(db, movie.id)


@router.patch("/{movie_id}", response_model=MoviePublic)
def update_movie(
    movie_id: int,
    body: MovieUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Movie:
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    if body.genre_id is not None:
        genre = db.get(Genre, body.genre_id)
        if genre is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid genre_id")
        movie.genre_id = body.genre_id
    if body.title is not None:
        movie.title = body.title
    if body.description is not None:
        movie.description = body.description
    if body.poster_image_url is not None:
        movie.poster_image_url = body.poster_image_url
    db.commit()
    return _load_movie_public(db, movie_id)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    db.delete(movie)
    db.commit()
