from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from sqlalchemy.exc import IntegrityError

from app.models import Reservation, ReservationSeat, Seat, Showtime, User, UserRole


class BookingError(Exception):
    pass


def create_reservation(db: Session, user_id: int, showtime_id: int, seat_ids: list[int]) -> Reservation:
    unique_seats = list(dict.fromkeys(seat_ids))
    if len(unique_seats) != len(seat_ids):
        raise BookingError("Duplicate seat ids in request")

    showtime = db.get(Showtime, showtime_id)
    if showtime is None:
        raise BookingError("Showtime not found")

    now = datetime.now(timezone.utc)
    if showtime.starts_at <= now:
        raise BookingError("Cannot reserve seats for a showtime that already started")

    seats = db.execute(select(Seat).where(Seat.id.in_(unique_seats)).with_for_update()).scalars().all()
    if len(seats) != len(unique_seats):
        raise BookingError("One or more seats not found")

    for seat in seats:
        if seat.screen_id != showtime.screen_id:
            raise BookingError("Seat does not belong to this showtime's screen")

    taken = db.execute(
        select(ReservationSeat.id)
        .join(Reservation, ReservationSeat.reservation_id == Reservation.id)
        .where(
            ReservationSeat.showtime_id == showtime_id,
            ReservationSeat.seat_id.in_(unique_seats),
            ReservationSeat.is_active.is_(True),
            Reservation.cancelled_at.is_(None),
        )
        .with_for_update()
    ).first()
    if taken:
        raise BookingError("One or more seats are no longer available")

    reservation = Reservation(user_id=user_id, showtime_id=showtime_id)
    db.add(reservation)
    db.flush()
    for sid in unique_seats:
        db.add(
            ReservationSeat(
                reservation_id=reservation.id,
                showtime_id=showtime_id,
                seat_id=sid,
                is_active=True,
            )
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BookingError("One or more seats are no longer available") from None
    db.refresh(reservation)
    return reservation


def cancel_reservation(db: Session, reservation_id: int, user: User) -> Reservation:
    reservation = db.execute(
        select(Reservation)
        .where(Reservation.id == reservation_id)
        .options(joinedload(Reservation.showtime))
    ).scalar_one_or_none()
    if reservation is None:
        raise BookingError("Reservation not found")

    if user.role != UserRole.ADMIN and reservation.user_id != user.id:
        raise BookingError("Forbidden")

    if reservation.cancelled_at is not None:
        raise BookingError("Reservation already cancelled")

    now = datetime.now(timezone.utc)
    if reservation.showtime.starts_at <= now:
        raise BookingError("Cannot cancel a reservation for a showtime that already started")

    reservation.cancelled_at = now
    for rs in db.execute(
        select(ReservationSeat).where(ReservationSeat.reservation_id == reservation.id)
    ).scalars():
        rs.is_active = False
    db.commit()
    db.refresh(reservation)
    return reservation
