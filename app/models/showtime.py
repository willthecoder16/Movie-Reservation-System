from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Screen(Base):
    __tablename__ = "screens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200))

    seats: Mapped[list["Seat"]] = relationship(
        "Seat", back_populates="screen", cascade="all, delete-orphan"
    )
    showtimes: Mapped[list["Showtime"]] = relationship("Showtime", back_populates="screen")


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("screen_id", "row_label", "seat_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    screen_id: Mapped[int] = mapped_column(ForeignKey("screens.id"), index=True)
    row_label: Mapped[str] = mapped_column(String(8))
    seat_number: Mapped[int] = mapped_column(Integer)

    screen: Mapped["Screen"] = relationship("Screen", back_populates="seats")


class Showtime(Base):
    __tablename__ = "showtimes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), index=True)
    screen_id: Mapped[int] = mapped_column(ForeignKey("screens.id"), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    price_cents: Mapped[int] = mapped_column(Integer, default=1500)

    movie: Mapped["Movie"] = relationship("Movie", back_populates="showtimes")
    screen: Mapped["Screen"] = relationship("Screen", back_populates="showtimes")
    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation", back_populates="showtime"
    )
