from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GenrePublic(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class MovieCreate(BaseModel):
    title: str = Field(max_length=300)
    description: str = ""
    poster_image_url: str = ""
    genre_id: int


class MovieUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    description: str | None = None
    poster_image_url: str | None = None
    genre_id: int | None = None


class MoviePublic(BaseModel):
    id: int
    title: str
    description: str
    poster_image_url: str
    genre_id: int
    genre: GenrePublic | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ShowtimeCreate(BaseModel):
    movie_id: int
    screen_id: int
    starts_at: datetime
    ends_at: datetime
    price_cents: int = Field(ge=0, default=1500)


class ShowtimeUpdate(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    price_cents: int | None = Field(default=None, ge=0)


class ShowtimePublic(BaseModel):
    id: int
    movie_id: int
    screen_id: int
    starts_at: datetime
    ends_at: datetime
    price_cents: int

    model_config = {"from_attributes": True}


class MovieWithShowtimesForDate(BaseModel):
    movie: MoviePublic
    showtimes: list[ShowtimePublic]


class ShowtimeBookingPublic(BaseModel):
    """Showtime + movie for the public booking UI."""

    id: int
    movie_id: int
    screen_id: int
    starts_at: datetime
    ends_at: datetime
    price_cents: int
    movie: MoviePublic


class ShowtimeAdminRow(BaseModel):
    """Showtime row for admin scheduling table."""

    id: int
    movie_id: int
    movie_title: str
    screen_id: int
    starts_at: datetime
    ends_at: datetime
    price_cents: int


class SeatPublic(BaseModel):
    id: int
    row_label: str
    seat_number: int
    available: bool

    model_config = {"from_attributes": True}


class ScreenCreate(BaseModel):
    name: str = Field(max_length=200)
    num_rows: int = Field(ge=1, le=26)
    seats_per_row: int = Field(ge=1, le=50)


class ScreenPublic(BaseModel):
    id: int
    name: str
    seat_count: int

    model_config = {"from_attributes": True}
