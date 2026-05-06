from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)

    movies: Mapped[list["Movie"]] = relationship("Movie", back_populates="genre")


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    poster_image_url: Mapped[str] = mapped_column(String(2048), default="")
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    genre: Mapped["Genre"] = relationship("Genre", back_populates="movies")
    showtimes: Mapped[list["Showtime"]] = relationship(
        "Showtime", back_populates="movie", cascade="all, delete-orphan"
    )
