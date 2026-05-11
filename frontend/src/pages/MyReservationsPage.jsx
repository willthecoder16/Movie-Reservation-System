import { useCallback, useEffect, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";

import { cancelReservation, myReservations } from "../api";
import "../AdminPage.css";

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

function seatSummary(seats) {
  if (!seats?.length) return "—";
  return seats.map((s) => `${s.row_label}${s.seat_number}`).join(", ");
}

function canCancel(r) {
  if (r.cancelled_at) return false;
  const start = new Date(r.starts_at);
  return start > new Date();
}

export default function MyReservationsPage() {
  const { token } = useOutletContext();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    setErr("");
    setLoading(true);
    try {
      const data = await myReservations(token);
      setRows(data);
    } catch (e) {
      setErr(e.message || "Failed to load reservations");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function onCancel(id) {
    if (!window.confirm("Cancel this reservation? Seats will be released.")) return;
    setBusyId(id);
    setErr("");
    try {
      await cancelReservation(token, id);
      await load();
    } catch (e) {
      setErr(e.message || "Cancel failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="admin-page">
      <h1 className="admin-page-title">My reservations</h1>
      <p className="admin-page-lead">
        Upcoming showtimes can be cancelled here. Past showtimes cannot be cancelled.
      </p>
      <p>
        <Link to="/dashboard">← Back to dashboard</Link>
      </p>

      {err && <div className="admin-banner admin-banner-error">{err}</div>}
      {loading && <p>Loading…</p>}

      {!loading && rows.length === 0 && !err && (
        <p className="admin-muted">You have no reservations yet. Pick a showtime from the dashboard.</p>
      )}

      {!loading && rows.length > 0 && (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Movie</th>
                <th>Showtime</th>
                <th>Seats</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>{r.movie_title}</td>
                  <td>{formatWhen(r.starts_at)}</td>
                  <td>{seatSummary(r.seats)}</td>
                  <td>
                    {r.cancelled_at ? (
                      <span className="admin-muted">Cancelled</span>
                    ) : (
                      "Confirmed"
                    )}
                  </td>
                  <td>
                    {canCancel(r) ? (
                      <button
                        type="button"
                        className="admin-btn admin-btn-danger"
                        disabled={busyId === r.id}
                        onClick={() => onCancel(r.id)}
                      >
                        {busyId === r.id ? "…" : "Cancel"}
                      </button>
                    ) : (
                      <span className="admin-muted">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
