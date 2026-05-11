import { useEffect, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";

import { API_BASE, getMoviesByDate, listMovies } from "../api";
import "../DashboardPage.css";

function localDateInputValue(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function formatShowtime(iso) {
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

function formatPrice(cents) {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

export default function DashboardPage() {
  const { user } = useOutletContext();

  const [selectedDate, setSelectedDate] = useState(() => localDateInputValue());
  const [catalog, setCatalog] = useState([]);
  const [allMovies, setAllMovies] = useState([]);
  const [catalogError, setCatalogError] = useState("");
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [moviesError, setMoviesError] = useState("");
  const [brokenPosters, setBrokenPosters] = useState({});

  useEffect(() => {
    if (!user) return;

    let cancelled = false;

    async function loadCatalog() {
      setCatalogLoading(true);
      setCatalogError("");
      try {
        const rows = await getMoviesByDate(selectedDate);
        if (!cancelled) setCatalog(rows);
      } catch (e) {
        if (!cancelled) setCatalogError(e.message || "Failed to load showtimes");
      } finally {
        if (!cancelled) setCatalogLoading(false);
      }
    }

    loadCatalog();
    return () => {
      cancelled = true;
    };
  }, [user, selectedDate]);

  useEffect(() => {
    if (!user) return;

    let cancelled = false;

    async function loadAllMovies() {
      setMoviesError("");
      try {
        const movies = await listMovies();
        if (!cancelled) setAllMovies(movies);
      } catch {
        if (!cancelled) setMoviesError("Could not load full movie list.");
      }
    }

    loadAllMovies();
    return () => {
      cancelled = true;
    };
  }, [user]);

  const isAdmin = user?.role === "admin";

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>Dashboard</h1>
          <p className="dashboard-meta">
            Signed in as <strong>{user?.email}</strong>
            {user?.role ? ` · ${user.role}` : ""}
          </p>
          {isAdmin && (
            <p className="admin-note">
              Admin tools: <Link to="/admin">open admin console</Link> (movies, showtimes, reporting, users) or{" "}
              <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">
                API docs
              </a>
              .
            </p>
          )}
        </div>
      </header>

      <section aria-labelledby="schedule-heading">
        <h2 id="schedule-heading" className="section-title">
          What&apos;s playing
        </h2>
        <div className="catalog-toolbar">
          <label htmlFor="show-date">Pick a date (UTC calendar day)</label>
          <input
            id="show-date"
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
          {catalogLoading && <span className="showtime-meta">Loading…</span>}
        </div>
        {catalogError && <div className="error-banner">{catalogError}</div>}
        {!catalogLoading && catalog.length === 0 && !catalogError && (
          <p className="empty-state">
            No showtimes on this date. Try another day, or{" "}
            {isAdmin ? (
              <Link to="/admin">add showtimes in the admin console</Link>
            ) : (
              "ask an admin to add showtimes."
            )}
          </p>
        )}
        <div className="movie-grid">
          {catalog.map(({ movie, showtimes }) => (
            <article key={movie.id} className="movie-card">
              {movie.poster_image_url && !brokenPosters[`c-${movie.id}`] ? (
                <img
                  className="movie-card-poster"
                  src={movie.poster_image_url}
                  alt=""
                  loading="lazy"
                  onError={() =>
                    setBrokenPosters((s) => ({ ...s, [`c-${movie.id}`]: true }))
                  }
                />
              ) : (
                <div className="movie-card-poster">No poster</div>
              )}
              <div className="movie-card-body">
                <h3 className="movie-card-title">{movie.title}</h3>
                {movie.genre?.name && (
                  <p className="movie-card-genre">{movie.genre.name}</p>
                )}
                {movie.description ? (
                  <p className="movie-card-desc">{movie.description}</p>
                ) : null}
                <ul className="showtimes-list">
                  {showtimes.map((st) => (
                    <li key={st.id}>
                      <Link
                        to={`/showtimes/${st.id}`}
                        style={{
                          display: "flex",
                          flexWrap: "wrap",
                          alignItems: "baseline",
                          justifyContent: "space-between",
                          gap: "0.5rem",
                          textDecoration: "none",
                          color: "inherit",
                        }}
                      >
                        <span className="showtime-time">{formatShowtime(st.starts_at)}</span>
                        <span className="showtime-meta">
                          Screen #{st.screen_id} · {formatPrice(st.price_cents)} · Reserve seats →
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section style={{ marginTop: "2.5rem" }} aria-labelledby="catalog-heading">
        <h2 id="catalog-heading" className="section-title">
          All movies in catalog
        </h2>
        <p className="showtime-meta" style={{ marginBottom: "1rem" }}>
          Showtimes appear under &quot;What&apos;s playing&quot; when you pick a date.{" "}
          <Link to="/reservations">View your reservations</Link>.
        </p>
        {moviesError && <div className="error-banner">{moviesError}</div>}
        <div className="movie-grid">
          {allMovies.map((m) => (
            <article key={m.id} className="movie-card">
              {m.poster_image_url && !brokenPosters[`a-${m.id}`] ? (
                <img
                  className="movie-card-poster"
                  src={m.poster_image_url}
                  alt=""
                  loading="lazy"
                  onError={() =>
                    setBrokenPosters((s) => ({ ...s, [`a-${m.id}`]: true }))
                  }
                />
              ) : (
                <div className="movie-card-poster">No poster</div>
              )}
              <div className="movie-card-body">
                <h3 className="movie-card-title">{m.title}</h3>
                {m.genre?.name && (
                  <p className="movie-card-genre">{m.genre.name}</p>
                )}
                {m.description ? (
                  <p className="movie-card-desc">{m.description}</p>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
