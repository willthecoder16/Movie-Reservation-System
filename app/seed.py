"""Load seed data: genres, admin user, sample screen/seats, movie, future showtime."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Genre, Movie, Screen, Seat, Showtime, User, UserRole


def seed() -> None:
    db = SessionLocal()
    try:
        if db.execute(select(User).where(User.email == "admin@example.com")).scalar_one_or_none():
            print("Seed already applied (admin@example.com exists). Skipping.")
            return

        for name in ("Action", "Drama", "Sci-Fi", "Comedy"):
            db.add(Genre(name=name))
        db.flush()

        sci_fi = db.execute(select(Genre).where(Genre.name == "Sci-Fi")).scalar_one()

        admin = User(
            email="admin@example.com",
            hashed_password=hash_password("adminpassword"),
            role=UserRole.ADMIN,
        )
        db.add(admin)

        screen = Screen(name="Hall 1")
        db.add(screen)
        db.flush()
        for row in range(5):
            label = chr(ord("A") + row)
            for num in range(1, 11):
                db.add(Seat(screen_id=screen.id, row_label=label, seat_number=num))

        movie = Movie(
            title="The Sample Odyssey",
            description="A demo film for the reservation API.",
            poster_image_url="https://example.com/posters/sample.jpg",
            genre_id=sci_fi.id,
        )
        db.add(movie)
        db.flush()

        now = datetime.now(timezone.utc)
        starts = now + timedelta(days=1)
        ends = starts + timedelta(hours=2)
        db.add(
            Showtime(
                movie_id=movie.id,
                screen_id=screen.id,
                starts_at=starts,
                ends_at=ends,
                price_cents=1200,
            )
        )

        db.commit()
        print("Seed complete.")
        print("  Admin login: admin@example.com / adminpassword")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
