import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";

import {
  createReservation,
  getShowtimeDetail,
  getShowtimeSeats,
} from "../api";
import "../ShowtimeBookingPage.css";

function formatWhen(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatMoney(cents) {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

function groupSeatsByRow(seats) {
  const byRow = new Map();
  for (const s of seats) {
    if (!byRow.has(s.row_label)) byRow.set(s.row_label, []);
    byRow.get(s.row_label).push(s);
  }
  for (const arr of byRow.values()) {
    arr.sort((a, b) => a.seat_number - b.seat_number);
  }
  return Array.from(byRow.entries()).sort(([a], [b]) => a.localeCompare(b));
}

export default function ShowtimeBookingPage() {
  const { showtimeId } = useParams();
  const { token } = useOutletContext();
  const id = Number(showtimeId);

  const [detail, setDetail] = useState(null);
  const [seats, setSeats] = useState([]);
  const [selected, setSelected] = useState(() => new Set());
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  const loadAll = useCallback(async () => {
    if (!Number.isFinite(id) || id < 1) {
      setLoadError("Invalid showtime.");
      setLoading(false);
      return;
    }
    setLoadError("");
    setLoading(true);
    try {
      const [d, seatList] = await Promise.all([
        getShowtimeDetail(id),
        getShowtimeSeats(id),
      ]);
      setDetail(d);
      setSeats(seatList);
    } catch (e) {
      setLoadError(e.message || "Failed to load showtime");
      setDetail(null);
      setSeats([]);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const rows = useMemo(() => groupSeatsByRow(seats), [seats]);

  const startsAt = detail?.starts_at ? new Date(detail.starts_at) : null;
  const isPast = startsAt && startsAt <= new Date();

  function toggleSeat(seat) {
    if (!seat.available || isPast) return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(seat.id)) next.delete(seat.id);
      else next.add(seat.id);
      return next;
    });
  }

  async function handleReserve() {
    if (!token || selected.size === 0 || isPast) return;
    setActionError("");
    setSuccessMsg("");
    setSubmitting(true);
    try {
      await createReservation(token, {
        showtime_id: id,
        seat_ids: Array.from(selected),
      });
      setSuccessMsg(`Reserved ${selected.size} seat(s).`);
      setSelected(new Set());
      const seatList = await getShowtimeSeats(id);
      setSeats(seatList);
    } catch (e) {
      setActionError(e.message || "Reservation failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="booking-page">
        <p>Loading seats…</p>
      </div>
    );
  }

  if (loadError || !detail) {
    return (
      <div className="booking-page">
        <Link className="booking-back" to="/dashboard">
          ← Back to dashboard
        </Link>
        <p className="booking-error">{loadError || "Showtime not found."}</p>
      </div>
    );
  }

  const totalCents = selected.size * (detail.price_cents || 0);

  return (
    <div className="booking-page">
      <Link className="booking-back" to="/dashboard">
        ← Back to dashboard
      </Link>

      <div className="booking-hero">
        {detail.movie?.poster_image_url ? (
          <img
            className="booking-poster"
            src={detail.movie.poster_image_url}
            alt=""
          />
        ) : (
          <div className="booking-poster" style={{ display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.75rem", color: "var(--text)" }}>
            No poster
          </div>
        )}
        <div>
          <h1 className="booking-title">{detail.movie?.title}</h1>
          <p className="booking-meta">
            {formatWhen(detail.starts_at)} · Screen #{detail.screen_id} ·{" "}
            {formatMoney(detail.price_cents)} per seat
          </p>
          {detail.movie?.genre?.name && (
            <p className="booking-meta">Genre: {detail.movie.genre.name}</p>
          )}
        </div>
      </div>

      {isPast ? (
        <p className="booking-past">This showtime has already started — reservations are closed.</p>
      ) : (
        <>
          <div className="theater" aria-label="Seat map">
            <div className="theater-screen">SCREEN</div>
            <div className="theater-legend">
              <span>
                <span className="legend-dot available" aria-hidden /> Available
              </span>
              <span>
                <span className="legend-dot selected" aria-hidden /> Your selection
              </span>
              <span>
                <span className="legend-dot taken" aria-hidden /> Taken
              </span>
            </div>
            <div className="theater-rows">
              {rows.map(([rowLabel, rowSeats]) => (
                <div key={rowLabel} className="theater-row">
                  <span className="row-label">{rowLabel}</span>
                  {rowSeats.map((seat) => {
                    const isSelected = selected.has(seat.id);
                    let cls = "seat-btn ";
                    if (!seat.available) cls += "taken";
                    else if (isSelected) cls += "selected";
                    else cls += "available";
                    return (
                      <button
                        key={seat.id}
                        type="button"
                        className={cls}
                        disabled={!seat.available}
                        onClick={() => toggleSeat(seat)}
                        aria-pressed={isSelected}
                        aria-label={`Seat ${rowLabel}${seat.seat_number}${!seat.available ? " taken" : isSelected ? " selected" : ""}`}
                        title={`${rowLabel}${seat.seat_number}`}
                      >
                        {seat.seat_number}
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          <div className="booking-actions">
            <button
              type="button"
              disabled={selected.size === 0 || submitting}
              onClick={handleReserve}
            >
              {submitting ? "Reserving…" : `Reserve ${selected.size || ""} seat${selected.size === 1 ? "" : "s"}`.trim()}
            </button>
            <button
              type="button"
              className="ghost"
              disabled={selected.size === 0}
              onClick={() => setSelected(new Set())}
            >
              Clear selection
            </button>
            <span className="booking-summary">
              {selected.size > 0
                ? `Estimated total: ${formatMoney(totalCents)}`
                : "Tap seats to select them."}
            </span>
          </div>
        </>
      )}

      {actionError && <div className="booking-error">{actionError}</div>}
      {successMsg && (
        <div className="booking-success">
          {successMsg} Other accounts will see these seats as taken.{" "}
          <Link to="/reservations">View your reservations</Link>.
        </div>
      )}
    </div>
  );
}
