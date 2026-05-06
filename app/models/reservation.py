from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.showtime import Seat


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.id"), index=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="reservations")
    showtime: Mapped["Showtime"] = relationship("Showtime", back_populates="reservations")
    seats: Mapped[list["ReservationSeat"]] = relationship(
        "ReservationSeat",
        back_populates="reservation",
        cascade="all, delete-orphan",
    )


class ReservationSeat(Base):
    """Seat assignment. `is_active=False` after cancel; partial unique index prevents double-booking."""

    __tablename__ = "reservation_seats"
    __table_args__ = (
        Index(
            "uq_reservation_seats_active_showtime_seat",
            "showtime_id",
            "seat_id",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"), index=True)
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.id"), index=True)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    reservation: Mapped["Reservation"] = relationship("Reservation", back_populates="seats")
    seat: Mapped["Seat"] = relationship("Seat", foreign_keys=[seat_id])
