from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReservationCreate(BaseModel):
    showtime_id: int
    seat_ids: list[int] = Field(min_length=1)


class ReservationSeatPublic(BaseModel):
    seat_id: int
    row_label: str
    seat_number: int


class ReservationPublic(BaseModel):
    id: int
    showtime_id: int
    starts_at: datetime
    movie_title: str
    seats: list[ReservationSeatPublic]
    created_at: datetime
    cancelled_at: datetime | None


class AdminReservationPublic(BaseModel):
    id: int
    user_id: int
    user_email: str
    showtime_id: int
    movie_title: str
    starts_at: datetime
    seat_count: int
    revenue_cents: int
    created_at: datetime
    cancelled_at: datetime | None


class ReportSummary(BaseModel):
    total_reservations: int
    active_reservations: int
    cancelled_reservations: int
    total_seats_booked_active: int
    total_capacity_seats: int
    revenue_cents_active: int
