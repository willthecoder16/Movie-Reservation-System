from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_admin
from app.models import Reservation, Screen, Seat, Showtime, User
from app.schemas.movie import ScreenCreate, ScreenPublic
from app.schemas.reservation import AdminReservationPublic, ReportSummary

router = APIRouter(prefix="/admin", tags=["admin"])


def _day_range_utc(d: date) -> tuple[datetime, datetime]:
    start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


@router.post("/screens", response_model=ScreenPublic)
def create_screen(
    body: ScreenCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ScreenPublic:
    screen = Screen(name=body.name.strip())
    db.add(screen)
    db.flush()
    labels = [chr(ord("A") + i) for i in range(body.num_rows)]
    for row_label in labels:
        for n in range(1, body.seats_per_row + 1):
            db.add(Seat(screen_id=screen.id, row_label=row_label, seat_number=n))
    db.commit()
    cnt = db.execute(select(func.count(Seat.id)).where(Seat.screen_id == screen.id)).scalar_one()
    return ScreenPublic(id=screen.id, name=screen.name, seat_count=int(cnt))


@router.get("/screens", response_model=list[ScreenPublic])
def list_screens(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[ScreenPublic]:
    screens = db.execute(select(Screen).order_by(Screen.name)).scalars().all()
    out: list[ScreenPublic] = []
    for s in screens:
        cnt = db.execute(select(func.count(Seat.id)).where(Seat.screen_id == s.id)).scalar_one()
        out.append(ScreenPublic(id=s.id, name=s.name, seat_count=int(cnt)))
    return out


@router.get("/reservations", response_model=list[AdminReservationPublic])
def list_reservations(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[AdminReservationPublic]:
    rows = db.execute(
        select(Reservation)
        .options(
            joinedload(Reservation.user),
            joinedload(Reservation.showtime).joinedload(Showtime.movie),
            joinedload(Reservation.seats),
        )
        .order_by(Reservation.created_at.desc())
    ).unique()
    out: list[AdminReservationPublic] = []
    for r in rows.scalars():
        seat_count = len(r.seats)
        revenue = 0 if r.cancelled_at is not None else r.showtime.price_cents * seat_count
        out.append(
            AdminReservationPublic(
                id=r.id,
                user_id=r.user_id,
                user_email=r.user.email,
                showtime_id=r.showtime_id,
                movie_title=r.showtime.movie.title,
                starts_at=r.showtime.starts_at,
                seat_count=seat_count,
                revenue_cents=revenue,
                created_at=r.created_at,
                cancelled_at=r.cancelled_at,
            )
        )
    return out


@router.get("/report/summary", response_model=ReportSummary)
def reservation_report(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
) -> ReportSummary:
    """Filters metrics by showtime start date (UTC calendar days), inclusive of from_date and to_date."""

    showtime_filter = []
    if from_date is not None:
        start, _ = _day_range_utc(from_date)
        showtime_filter.append(Showtime.starts_at >= start)
    if to_date is not None:
        _, end = _day_range_utc(to_date)
        showtime_filter.append(Showtime.starts_at < end)

    reservations_stmt = select(Reservation).join(Showtime)
    for cond in showtime_filter:
        reservations_stmt = reservations_stmt.where(cond)

    reservations = db.execute(
        reservations_stmt.options(joinedload(Reservation.showtime), joinedload(Reservation.seats))
    ).unique().scalars()

    total = 0
    active = 0
    cancelled = 0
    seats_active = 0
    revenue = 0

    for r in reservations:
        total += 1
        seat_count = len(r.seats)
        if r.cancelled_at is not None:
            cancelled += 1
            continue
        active += 1
        seats_active += seat_count
        revenue += r.showtime.price_cents * seat_count

    cap_stmt = select(Showtime)
    for cond in showtime_filter:
        cap_stmt = cap_stmt.where(cond)
    showtimes = db.execute(cap_stmt).scalars().all()

    screen_counts: dict[int, int] = {}
    total_capacity = 0
    for st in showtimes:
        if st.screen_id not in screen_counts:
            screen_counts[st.screen_id] = int(
                db.execute(select(func.count(Seat.id)).where(Seat.screen_id == st.screen_id)).scalar_one()
            )
        total_capacity += screen_counts[st.screen_id]

    return ReportSummary(
        total_reservations=total,
        active_reservations=active,
        cancelled_reservations=cancelled,
        total_seats_booked_active=seats_active,
        total_capacity_seats=total_capacity,
        revenue_cents_active=revenue,
    )
