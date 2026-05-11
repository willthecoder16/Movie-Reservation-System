import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, Navigate, useOutletContext } from "react-router-dom";

import {
  adminReport,
  adminReservations,
  createGenreAdmin,
  createMovieAdmin,
  createScreenAdmin,
  createShowtimeAdmin,
  deleteMovieAdmin,
  deleteShowtimeAdmin,
  listGenresPublic,
  listMovies,
  listScreensAdmin,
  listShowtimesAdmin,
  listUsersAdmin,
  setUserRole,
  updateMovieAdmin,
} from "../api";
import "../AdminPage.css";

function formatMoney(cents) {
  return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(
    cents / 100
  );
}

function formatWhen(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function toIsoFromLocal(dtLocal) {
  if (!dtLocal) return null;
  const d = new Date(dtLocal);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

function UserRoleCell({ user, onSave }) {
  const [role, setRole] = useState(user.role);
  useEffect(() => {
    setRole(user.role);
  }, [user.id, user.role]);
  return (
    <div className="admin-row" style={{ margin: 0 }}>
      <select value={role} onChange={(e) => setRole(e.target.value)} aria-label={`Role for ${user.email}`}>
        <option value="user">user</option>
        <option value="admin">admin</option>
      </select>
      <button type="button" className="admin-btn admin-btn-secondary" onClick={() => onSave(user.id, role)}>
        Save role
      </button>
    </div>
  );
}

export default function AdminPage() {
  const { user, token } = useOutletContext();

  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const [report, setReport] = useState(null);
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [reportLoading, setReportLoading] = useState(false);

  const [adminRes, setAdminRes] = useState([]);
  const [resLoading, setResLoading] = useState(false);

  const [movies, setMovies] = useState([]);
  const [genres, setGenres] = useState([]);
  const [movieTitle, setMovieTitle] = useState("");
  const [movieDesc, setMovieDesc] = useState("");
  const [moviePoster, setMoviePoster] = useState("");
  const [movieGenreId, setMovieGenreId] = useState("");
  const [editMovieId, setEditMovieId] = useState(null);

  const [screens, setScreens] = useState([]);
  const [screenName, setScreenName] = useState("Hall 3");
  const [screenRows, setScreenRows] = useState(6);
  const [screenSeats, setScreenSeats] = useState(12);

  const [showtimes, setShowtimes] = useState([]);
  const [stMovieId, setStMovieId] = useState("");
  const [stScreenId, setStScreenId] = useState("");
  const [stStart, setStStart] = useState("");
  const [stEnd, setStEnd] = useState("");
  const [stPrice, setStPrice] = useState(1500);

  const [genreName, setGenreName] = useState("");

  const [users, setUsers] = useState([]);

  const clearBanners = () => {
    setMsg("");
    setErr("");
  };

  const reloadCatalog = useCallback(async () => {
    const [m, g, s, st, u] = await Promise.all([
      listMovies(),
      listGenresPublic(),
      listScreensAdmin(token),
      listShowtimesAdmin(token),
      listUsersAdmin(token),
    ]);
    setMovies(m);
    setGenres(g);
    setScreens(s);
    setShowtimes(st);
    setUsers(u);
    setStMovieId((prev) => (prev && m.some((x) => String(x.id) === prev) ? prev : m[0] ? String(m[0].id) : ""));
    setStScreenId((prev) => (prev && s.some((x) => String(x.id) === prev) ? prev : s[0] ? String(s[0].id) : ""));
    setMovieGenreId((prev) => (prev && g.some((x) => String(x.id) === prev) ? prev : g[0] ? String(g[0].id) : ""));
  }, [token]);

  useEffect(() => {
    if (user?.role !== "admin") return;
    clearBanners();
    reloadCatalog().catch((e) => setErr(e.message || "Load failed"));
  }, [user, reloadCatalog]);

  const isAdmin = user?.role === "admin";

  const genreOptions = useMemo(
    () =>
      genres.map((g) => (
        <option key={g.id} value={g.id}>
          {g.name}
        </option>
      )),
    [genres]
  );

  async function loadReport() {
    setReportLoading(true);
    setErr("");
    try {
      const r = await adminReport(token, { fromDate: fromDate || undefined, toDate: toDate || undefined });
      setReport(r);
    } catch (e) {
      setErr(e.message || "Report failed");
    } finally {
      setReportLoading(false);
    }
  }

  async function loadAdminReservations() {
    setResLoading(true);
    setErr("");
    try {
      setAdminRes(await adminReservations(token));
    } catch (e) {
      setErr(e.message || "Failed to load reservations");
    } finally {
      setResLoading(false);
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    loadReport();
    loadAdminReservations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin, token]);

  if (!isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  async function onCreateMovie(e) {
    e.preventDefault();
    clearBanners();
    try {
      await createMovieAdmin(token, {
        title: movieTitle.trim(),
        description: movieDesc,
        poster_image_url: moviePoster.trim(),
        genre_id: Number(movieGenreId),
      });
      setMsg("Movie created.");
      setMovieTitle("");
      setMovieDesc("");
      setMoviePoster("");
      await reloadCatalog();
    } catch (e) {
      setErr(e.message || "Create failed");
    }
  }

  function startEditMovie(m) {
    setEditMovieId(m.id);
    setMovieTitle(m.title);
    setMovieDesc(m.description || "");
    setMoviePoster(m.poster_image_url || "");
    setMovieGenreId(String(m.genre_id));
    clearBanners();
  }

  async function onSaveMovie(e) {
    e.preventDefault();
    if (!editMovieId) return;
    clearBanners();
    try {
      await updateMovieAdmin(token, editMovieId, {
        title: movieTitle.trim(),
        description: movieDesc,
        poster_image_url: moviePoster.trim(),
        genre_id: Number(movieGenreId),
      });
      setMsg("Movie updated.");
      setEditMovieId(null);
      setMovieTitle("");
      setMovieDesc("");
      setMoviePoster("");
      await reloadCatalog();
    } catch (e) {
      setErr(e.message || "Update failed");
    }
  }

  async function onDeleteMovie(id) {
    if (!window.confirm("Delete this movie and its showtimes?")) return;
    clearBanners();
    try {
      await deleteMovieAdmin(token, id);
      setMsg("Movie deleted.");
      if (editMovieId === id) setEditMovieId(null);
      await reloadCatalog();
    } catch (e) {
      setErr(e.message || "Delete failed");
    }
  }

  async function onCreateShowtime(e) {
    e.preventDefault();
    clearBanners();
    const starts_at = toIsoFromLocal(stStart);
    const ends_at = toIsoFromLocal(stEnd);
    if (!starts_at || !ends_at) {
      setErr("Start and end times are required.");
      return;
    }
    try {
      await createShowtimeAdmin(token, {
        movie_id: Number(stMovieId),
        screen_id: Number(stScreenId),
        starts_at,
        ends_at,
        price_cents: Number(stPrice) || 0,
      });
      setMsg("Showtime created.");
      setStStart("");
      setStEnd("");
      await reloadCatalog();
    } catch (e) {
      setErr(e.message || "Create showtime failed");
    }
  }

  async function onDeleteShowtime(id) {
    if (!window.confirm("Delete this showtime?")) return;
    clearBanners();
    try {
      await deleteShowtimeAdmin(token, id);
      setMsg("Showtime deleted.");
      await reloadCatalog();
    } catch (e) {
      setErr(e.message || "Delete failed");
    }
  }

  async function onCreateGenre(e) {
    e.preventDefault();
    clearBanners();
    try {
      await createGenreAdmin(token, genreName.trim());
      setMsg("Genre created.");
      setGenreName("");
      await reloadCatalog();
    } catch (e) {
      setErr(e.message || "Genre create failed");
    }
  }

  async function onCreateScreen(e) {
    e.preventDefault();
    clearBanners();
    try {
      await createScreenAdmin(token, {
        name: screenName.trim(),
        num_rows: Number(screenRows),
        seats_per_row: Number(screenSeats),
      });
      setMsg("Screen created.");
      await reloadCatalog();
    } catch (e) {
      setErr(e.message || "Screen create failed");
    }
  }

  async function onSaveUserRole(userId, role) {
    clearBanners();
    try {
      await setUserRole(token, userId, role);
      setMsg(`User ${userId} is now ${role}.`);
      await reloadCatalog();
    } catch (e) {
      setErr(e.message || "Role update failed");
    }
  }

  return (
    <div className="admin-page">
      <h1 className="admin-page-title">Admin console</h1>
      <p className="admin-page-lead">
        Manage movies, showtimes, genres, screens, reporting, and user roles. Only admins see this page.
      </p>
      <p>
        <Link to="/dashboard">← Dashboard</Link>
      </p>

      {msg && <div className="admin-banner admin-banner-ok">{msg}</div>}
      {err && <div className="admin-banner admin-banner-error">{err}</div>}

      <section className="admin-section" aria-labelledby="rep-h">
        <h2 id="rep-h">Reporting (capacity & revenue)</h2>
        <p className="admin-muted">
          Optional filters use UTC calendar days (same as catalog). Leave blank for all showtimes in range of data.
        </p>
        <div className="admin-row">
          <div className="admin-field">
            <label htmlFor="from-d">From date</label>
            <input
              id="from-d"
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
            />
          </div>
          <div className="admin-field">
            <label htmlFor="to-d">To date</label>
            <input id="to-d" type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
          </div>
          <button type="button" className="admin-btn" disabled={reportLoading} onClick={loadReport}>
            {reportLoading ? "Loading…" : "Refresh report"}
          </button>
        </div>
        {report && (
          <div className="admin-grid">
            <div>
              <strong>Total reservations</strong>
              <div>{report.total_reservations}</div>
            </div>
            <div>
              <strong>Active</strong>
              <div>{report.active_reservations}</div>
            </div>
            <div>
              <strong>Cancelled</strong>
              <div>{report.cancelled_reservations}</div>
            </div>
            <div>
              <strong>Seats booked (active)</strong>
              <div>{report.total_seats_booked_active}</div>
            </div>
            <div>
              <strong>Capacity (seat-slots in filtered showtimes)</strong>
              <div>{report.total_capacity_seats}</div>
            </div>
            <div>
              <strong>Revenue (active)</strong>
              <div>{formatMoney(report.revenue_cents_active)}</div>
            </div>
          </div>
        )}
      </section>

      <section className="admin-section" aria-labelledby="ar-h">
        <h2 id="ar-h">All reservations</h2>
        <button type="button" className="admin-btn admin-btn-secondary" onClick={loadAdminReservations}>
          Refresh list
        </button>
        {resLoading && <p>Loading…</p>}
        {!resLoading && adminRes.length > 0 && (
          <div className="admin-table-wrap" style={{ marginTop: "0.75rem" }}>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>User</th>
                  <th>Movie</th>
                  <th>Starts</th>
                  <th>Seats</th>
                  <th>Revenue</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {adminRes.map((r) => (
                  <tr key={r.id}>
                    <td>{r.id}</td>
                    <td>{r.user_email}</td>
                    <td>{r.movie_title}</td>
                    <td>{formatWhen(r.starts_at)}</td>
                    <td>{r.seat_count}</td>
                    <td>{formatMoney(r.revenue_cents)}</td>
                    <td>{r.cancelled_at ? "Cancelled" : "Active"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="admin-section" aria-labelledby="mv-h">
        <h2 id="mv-h">Movies</h2>
        <form onSubmit={editMovieId ? onSaveMovie : onCreateMovie}>
          <div className="admin-grid">
            <div className="admin-field">
              <label>Title</label>
              <input value={movieTitle} onChange={(e) => setMovieTitle(e.target.value)} required />
            </div>
            <div className="admin-field">
              <label>Genre</label>
              <select value={movieGenreId} onChange={(e) => setMovieGenreId(e.target.value)} required>
                {genreOptions}
              </select>
            </div>
            <div className="admin-field" style={{ gridColumn: "1 / -1" }}>
              <label>Poster URL</label>
              <input value={moviePoster} onChange={(e) => setMoviePoster(e.target.value)} />
            </div>
            <div className="admin-field" style={{ gridColumn: "1 / -1" }}>
              <label>Description</label>
              <textarea value={movieDesc} onChange={(e) => setMovieDesc(e.target.value)} />
            </div>
          </div>
          <div className="admin-row">
            <button type="submit" className="admin-btn">
              {editMovieId ? "Save changes" : "Add movie"}
            </button>
            {editMovieId && (
              <button
                type="button"
                className="admin-btn admin-btn-secondary"
                onClick={() => {
                  setEditMovieId(null);
                  setMovieTitle("");
                  setMovieDesc("");
                  setMoviePoster("");
                  if (genres[0]) setMovieGenreId(String(genres[0].id));
                }}
              >
                Cancel edit
              </button>
            )}
          </div>
        </form>

        <div className="admin-table-wrap" style={{ marginTop: "1rem" }}>
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Genre</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {movies.map((m) => (
                <tr key={m.id}>
                  <td>{m.id}</td>
                  <td>{m.title}</td>
                  <td>{m.genre?.name ?? m.genre_id}</td>
                  <td>
                    <button type="button" className="admin-btn admin-btn-secondary" onClick={() => startEditMovie(m)}>
                      Edit
                    </button>{" "}
                    <button type="button" className="admin-btn admin-btn-danger" onClick={() => onDeleteMovie(m.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="admin-section" aria-labelledby="st-h">
        <h2 id="st-h">Showtimes</h2>
        <form onSubmit={onCreateShowtime}>
          <div className="admin-grid">
            <div className="admin-field">
              <label>Movie</label>
              <select value={stMovieId} onChange={(e) => setStMovieId(e.target.value)} required>
                {movies.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.title}
                  </option>
                ))}
              </select>
            </div>
            <div className="admin-field">
              <label>Screen</label>
              <select value={stScreenId} onChange={(e) => setStScreenId(e.target.value)} required>
                {screens.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.seat_count} seats)
                  </option>
                ))}
              </select>
            </div>
            <div className="admin-field">
              <label>Starts (local)</label>
              <input
                type="datetime-local"
                value={stStart}
                onChange={(e) => setStStart(e.target.value)}
                required
              />
            </div>
            <div className="admin-field">
              <label>Ends (local)</label>
              <input type="datetime-local" value={stEnd} onChange={(e) => setStEnd(e.target.value)} required />
            </div>
            <div className="admin-field">
              <label>Price (cents)</label>
              <input
                type="number"
                min={0}
                value={stPrice}
                onChange={(e) => setStPrice(e.target.value)}
                required
              />
            </div>
          </div>
          <button type="submit" className="admin-btn">
            Add showtime
          </button>
        </form>

        <div className="admin-table-wrap" style={{ marginTop: "1rem" }}>
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Movie</th>
                <th>Screen</th>
                <th>Starts</th>
                <th>Price</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {showtimes.map((st) => (
                <tr key={st.id}>
                  <td>{st.id}</td>
                  <td>{st.movie_title}</td>
                  <td>{st.screen_id}</td>
                  <td>{formatWhen(st.starts_at)}</td>
                  <td>{formatMoney(st.price_cents)}</td>
                  <td>
                    <button
                      type="button"
                      className="admin-btn admin-btn-danger"
                      onClick={() => onDeleteShowtime(st.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="admin-section" aria-labelledby="g-h">
        <h2 id="g-h">Genres</h2>
        <ul className="admin-muted">
          {genres.map((g) => (
            <li key={g.id}>
              {g.name} (id {g.id})
            </li>
          ))}
        </ul>
        <form onSubmit={onCreateGenre} className="admin-row">
          <div className="admin-field" style={{ minWidth: "200px" }}>
            <label>New genre name</label>
            <input value={genreName} onChange={(e) => setGenreName(e.target.value)} required />
          </div>
          <button type="submit" className="admin-btn">
            Add genre
          </button>
        </form>
      </section>

      <section className="admin-section" aria-labelledby="sc-h">
        <h2 id="sc-h">Screens</h2>
        <ul className="admin-muted">
          {screens.map((s) => (
            <li key={s.id}>
              {s.name} — {s.seat_count} seats (id {s.id})
            </li>
          ))}
        </ul>
        <form onSubmit={onCreateScreen}>
          <div className="admin-grid">
            <div className="admin-field">
              <label>Name</label>
              <input value={screenName} onChange={(e) => setScreenName(e.target.value)} required />
            </div>
            <div className="admin-field">
              <label>Rows</label>
              <input
                type="number"
                min={1}
                max={26}
                value={screenRows}
                onChange={(e) => setScreenRows(e.target.value)}
                required
              />
            </div>
            <div className="admin-field">
              <label>Seats per row</label>
              <input
                type="number"
                min={1}
                max={50}
                value={screenSeats}
                onChange={(e) => setScreenSeats(e.target.value)}
                required
              />
            </div>
          </div>
          <button type="submit" className="admin-btn">
            Create screen & seats
          </button>
        </form>
      </section>

      <section className="admin-section" aria-labelledby="u-h">
        <h2 id="u-h">Users & roles</h2>
        <p className="admin-muted">Only admins can promote users to admin.</p>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.id}</td>
                  <td>{u.email}</td>
                  <td>
                    <UserRoleCell user={u} onSave={onSaveUserRole} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
