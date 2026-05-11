from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_admin
from app.models import Movie, Reservation, ReservationSeat, Screen, Seat, Showtime, User
from app.schemas.movie import (
    MoviePublic,
    SeatPublic,
    ShowtimeAdminRow,
    ShowtimeBookingPublic,
    ShowtimeCreate,
    ShowtimePublic,
    ShowtimeUpdate,
)

router = APIRouter(prefix="/showtimes", tags=["showtimes"])


@router.get("", response_model=list[ShowtimeAdminRow])
def list_showtimes_admin(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[ShowtimeAdminRow]:
    rows = db.execute(
        select(Showtime)
        .options(joinedload(Showtime.movie))
        .order_by(Showtime.starts_at.desc())
    ).unique()
    out: list[ShowtimeAdminRow] = []
    for st in rows.scalars():
        out.append(
            ShowtimeAdminRow(
                id=st.id,
                movie_id=st.movie_id,
                movie_title=st.movie.title,
                screen_id=st.screen_id,
                starts_at=st.starts_at,
                ends_at=st.ends_at,
                price_cents=st.price_cents,
            )
        )
    return out


@router.post("", response_model=ShowtimePublic)
def create_showtime(
    body: ShowtimeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Showtime:
    if body.ends_at <= body.starts_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ends_at must be after starts_at")
    movie = db.get(Movie, body.movie_id)
    if movie is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid movie_id")
    screen = db.get(Screen, body.screen_id)
    if screen is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid screen_id")

    st = Showtime(
        movie_id=body.movie_id,
        screen_id=body.screen_id,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        price_cents=body.price_cents,
    )
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


@router.patch("/{showtime_id}", response_model=ShowtimePublic)
def update_showtime(
    showtime_id: int,
    body: ShowtimeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Showtime:
    st = db.get(Showtime, showtime_id)
    if st is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Showtime not found")
    if body.starts_at is not None:
        st.starts_at = body.starts_at
    if body.ends_at is not None:
        st.ends_at = body.ends_at
    if body.price_cents is not None:
        st.price_cents = body.price_cents
    if st.ends_at <= st.starts_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ends_at must be after starts_at")
    db.commit()
    db.refresh(st)
    return st


@router.delete("/{showtime_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_showtime(
    showtime_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    st = db.get(Showtime, showtime_id)
    if st is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Showtime not found")
    db.delete(st)
    db.commit()


@router.get("/{showtime_id}/seats", response_model=list[SeatPublic])
def list_seats_for_showtime(showtime_id: int, db: Session = Depends(get_db)) -> list[SeatPublic]:
    st = db.execute(select(Showtime).where(Showtime.id == showtime_id)).scalar_one_or_none()
    if st is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Showtime not found")

    booked_rows = db.execute(
        select(ReservationSeat.seat_id).join(
            Reservation, ReservationSeat.reservation_id == Reservation.id
        ).where(
            ReservationSeat.showtime_id == showtime_id,
            ReservationSeat.is_active.is_(True),
            Reservation.cancelled_at.is_(None),
        )
    ).all()
    booked = {row[0] for row in booked_rows}

    seats = db.execute(
        select(Seat)
        .where(Seat.screen_id == st.screen_id)
        .order_by(Seat.row_label, Seat.seat_number)
    ).scalars()

    return [
        SeatPublic(id=s.id, row_label=s.row_label, seat_number=s.seat_number, available=s.id not in booked)
        for s in seats
    ]


@router.get("/{showtime_id}", response_model=ShowtimeBookingPublic)
def get_showtime_for_booking(showtime_id: int, db: Session = Depends(get_db)) -> ShowtimeBookingPublic:
    st = db.execute(
        select(Showtime)
        .where(Showtime.id == showtime_id)
        .options(joinedload(Showtime.movie).joinedload(Movie.genre))
    ).unique().scalar_one_or_none()
    if st is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Showtime not found")
    movie_public = MoviePublic.model_validate(st.movie)
    return ShowtimeBookingPublic(
        id=st.id,
        movie_id=st.movie_id,
        screen_id=st.screen_id,
        starts_at=st.starts_at,
        ends_at=st.ends_at,
        price_cents=st.price_cents,
        movie=movie_public,
    )
