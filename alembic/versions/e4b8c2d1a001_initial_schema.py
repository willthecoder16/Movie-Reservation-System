"""initial schema

Revision ID: e4b8c2d1a001
Revises:
Create Date: 2026-05-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "e4b8c2d1a001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_genres_name", "genres", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", postgresql.ENUM("USER", "ADMIN", name="userrole"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("poster_image_url", sa.String(length=2048), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_movies_genre_id", "movies", ["genre_id"])
    op.create_index("ix_movies_title", "movies", ["title"])

    op.create_table(
        "screens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "seats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("screen_id", sa.Integer(), nullable=False),
        sa.Column("row_label", sa.String(length=8), nullable=False),
        sa.Column("seat_number", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["screen_id"], ["screens.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("screen_id", "row_label", "seat_number"),
    )
    op.create_index("ix_seats_screen_id", "seats", ["screen_id"])

    op.create_table(
        "showtimes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("screen_id", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"]),
        sa.ForeignKeyConstraint(["screen_id"], ["screens.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_showtimes_movie_id", "showtimes", ["movie_id"])
    op.create_index("ix_showtimes_screen_id", "showtimes", ["screen_id"])
    op.create_index("ix_showtimes_starts_at", "showtimes", ["starts_at"])

    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("showtime_id", sa.Integer(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["showtime_id"], ["showtimes.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reservations_showtime_id", "reservations", ["showtime_id"])
    op.create_index("ix_reservations_user_id", "reservations", ["user_id"])

    op.create_table(
        "reservation_seats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("reservation_id", sa.Integer(), nullable=False),
        sa.Column("showtime_id", sa.Integer(), nullable=False),
        sa.Column("seat_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
        sa.ForeignKeyConstraint(["seat_id"], ["seats.id"]),
        sa.ForeignKeyConstraint(["showtime_id"], ["showtimes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reservation_seats_reservation_id", "reservation_seats", ["reservation_id"])
    op.create_index("ix_reservation_seats_seat_id", "reservation_seats", ["seat_id"])
    op.create_index("ix_reservation_seats_showtime_id", "reservation_seats", ["showtime_id"])
    op.create_index(
        "uq_reservation_seats_active_showtime_seat",
        "reservation_seats",
        ["showtime_id", "seat_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_reservation_seats_active_showtime_seat", table_name="reservation_seats")
    op.drop_index("ix_reservation_seats_showtime_id", table_name="reservation_seats")
    op.drop_index("ix_reservation_seats_seat_id", table_name="reservation_seats")
    op.drop_index("ix_reservation_seats_reservation_id", table_name="reservation_seats")
    op.drop_table("reservation_seats")

    op.drop_index("ix_reservations_user_id", table_name="reservations")
    op.drop_index("ix_reservations_showtime_id", table_name="reservations")
    op.drop_table("reservations")

    op.drop_index("ix_showtimes_starts_at", table_name="showtimes")
    op.drop_index("ix_showtimes_screen_id", table_name="showtimes")
    op.drop_index("ix_showtimes_movie_id", table_name="showtimes")
    op.drop_table("showtimes")

    op.drop_index("ix_seats_screen_id", table_name="seats")
    op.drop_table("seats")

    op.drop_table("screens")

    op.drop_index("ix_movies_title", table_name="movies")
    op.drop_index("ix_movies_genre_id", table_name="movies")
    op.drop_table("movies")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_genres_name", table_name="genres")
    op.drop_table("genres")

    postgresql.ENUM(name="userrole").drop(op.get_bind(), checkfirst=True)
