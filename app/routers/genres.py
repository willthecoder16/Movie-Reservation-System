from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import Genre, User
from app.schemas.movie import GenrePublic
from pydantic import BaseModel, Field

router = APIRouter(prefix="/genres", tags=["genres"])


class GenreCreate(BaseModel):
    name: str = Field(max_length=120)


@router.get("", response_model=list[GenrePublic])
def list_genres(db: Session = Depends(get_db)) -> list[Genre]:
    return list(db.execute(select(Genre).order_by(Genre.name)).scalars())


@router.post("", response_model=GenrePublic)
def create_genre(
    body: GenreCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Genre:
    g = Genre(name=body.name.strip())
    db.add(g)
    try:
        db.commit()
        db.refresh(g)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Genre already exists") from None
    return g
