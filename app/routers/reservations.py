from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Reservation, ReservationSeat, Showtime, User
from app.schemas.reservation import ReservationCreate, ReservationPublic, ReservationSeatPublic
from app.services.booking import BookingError, cancel_reservation, create_reservation

router = APIRouter(prefix="/reservations", tags=["reservations"])


def _load_with_lines(db: Session, reservation_id: int) -> Reservation:
    return db.execute(
        select(Reservation)
        .where(Reservation.id == reservation_id)
        .options(
            joinedload(Reservation.showtime).joinedload(Showtime.movie),
            joinedload(Reservation.seats).joinedload(ReservationSeat.seat),
        )
    ).unique().scalar_one()


def _to_public(r: Reservation) -> ReservationPublic:
    seats_sorted = sorted(r.seats, key=lambda rs: (rs.seat.row_label, rs.seat.seat_number))
    return ReservationPublic(
        id=r.id,
        showtime_id=r.showtime_id,
        starts_at=r.showtime.starts_at,
        movie_title=r.showtime.movie.title,
        seats=[
            ReservationSeatPublic(
                seat_id=rs.seat_id,
                row_label=rs.seat.row_label,
                seat_number=rs.seat.seat_number,
            )
            for rs in seats_sorted
        ],
        created_at=r.created_at,
        cancelled_at=r.cancelled_at,
    )


@router.post("", response_model=ReservationPublic)
def create_reservation_route(
    body: ReservationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReservationPublic:
    try:
        resv = create_reservation(db, user.id, body.showtime_id, body.seat_ids)
    except BookingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    loaded = _load_with_lines(db, resv.id)
    return _to_public(loaded)


@router.get("/me", response_model=list[ReservationPublic])
def my_reservations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ReservationPublic]:
    rows = db.execute(
        select(Reservation)
        .where(Reservation.user_id == user.id)
        .options(
            joinedload(Reservation.showtime).joinedload(Showtime.movie),
            joinedload(Reservation.seats).joinedload(ReservationSeat.seat),
        )
        .order_by(Reservation.created_at.desc())
    ).unique()
    return [_to_public(r) for r in rows.scalars()]


@router.delete("/{reservation_id}", response_model=ReservationPublic)
def cancel_reservation_route(
    reservation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReservationPublic:
    try:
        cancel_reservation(db, reservation_id, user)
    except BookingError as e:
        if str(e) == "Forbidden":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    loaded = _load_with_lines(db, reservation_id)
    return _to_public(loaded)
