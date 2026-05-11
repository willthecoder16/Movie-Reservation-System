export const API_BASE =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE) ||
  "http://127.0.0.1:8000";

export async function register(email, password) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Signup failed");
  return res.json();
}

export async function login(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Login failed");
  return res.json();
}

export async function me(token) {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Unauthorized");
  return res.json();
}

/** @returns {Promise<Array<{ movie: object, showtimes: object[] }>>} */
export async function getMoviesByDate(isoDate) {
  const res = await fetch(
    `${API_BASE}/catalog/movies-by-date?date=${encodeURIComponent(isoDate)}`
  );
  if (!res.ok) {
    let detail = "Could not load schedule";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

/** @returns {Promise<object[]>} */
export async function listMovies() {
  const res = await fetch(`${API_BASE}/movies`);
  if (!res.ok) throw new Error("Could not load movies");
  return res.json();
}

/** @returns {Promise<object>} showtime + nested movie */
export async function getShowtimeDetail(showtimeId) {
  const res = await fetch(`${API_BASE}/showtimes/${showtimeId}`);
  if (!res.ok) {
    const detail = await parseErrorDetail(res);
    throw new Error(detail);
  }
  return res.json();
}

/** @returns {Promise<Array<{ id: number, row_label: string, seat_number: number, available: boolean }>>} */
export async function getShowtimeSeats(showtimeId) {
  const res = await fetch(`${API_BASE}/showtimes/${showtimeId}/seats`);
  if (!res.ok) {
    const detail = await parseErrorDetail(res);
    throw new Error(detail);
  }
  return res.json();
}

/** @returns {Promise<object>} reservation payload */
export async function createReservation(token, { showtime_id, seat_ids }) {
  const res = await fetch(`${API_BASE}/reservations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ showtime_id, seat_ids }),
  });
  if (!res.ok) {
    const detail = await parseErrorDetail(res);
    throw new Error(detail);
  }
  return res.json();
}

export async function parseErrorDetail(res) {
  try {
    const body = await res.json();
    const d = body.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d))
      return d.map((e) => (e.msg ? `${e.loc?.join(".")}: ${e.msg}` : JSON.stringify(e))).join("; ");
    return "Request failed";
  } catch {
    return "Request failed";
  }
}

export async function authFetch(token, path, { method = "GET", body } = {}) {
  const headers = { Authorization: `Bearer ${token}` };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  if (res.status === 204) return null;
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export async function myReservations(token) {
  return authFetch(token, "/reservations/me");
}

export async function cancelReservation(token, reservationId) {
  return authFetch(token, `/reservations/${reservationId}`, { method: "DELETE" });
}

export async function listUsersAdmin(token) {
  return authFetch(token, "/users");
}

export async function setUserRole(token, userId, role) {
  return authFetch(token, `/users/${userId}/role`, { method: "PATCH", body: { role } });
}

export async function listGenresPublic() {
  const res = await fetch(`${API_BASE}/genres`);
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res.json();
}

export async function createGenreAdmin(token, name) {
  return authFetch(token, "/genres", { method: "POST", body: { name } });
}

export async function createMovieAdmin(token, payload) {
  return authFetch(token, "/movies", { method: "POST", body: payload });
}

export async function updateMovieAdmin(token, movieId, payload) {
  return authFetch(token, `/movies/${movieId}`, { method: "PATCH", body: payload });
}

export async function deleteMovieAdmin(token, movieId) {
  return authFetch(token, `/movies/${movieId}`, { method: "DELETE" });
}

export async function listShowtimesAdmin(token) {
  return authFetch(token, "/showtimes");
}

export async function createShowtimeAdmin(token, payload) {
  return authFetch(token, "/showtimes", { method: "POST", body: payload });
}

export async function deleteShowtimeAdmin(token, showtimeId) {
  return authFetch(token, `/showtimes/${showtimeId}`, { method: "DELETE" });
}

export async function listScreensAdmin(token) {
  return authFetch(token, "/admin/screens");
}

export async function createScreenAdmin(token, payload) {
  return authFetch(token, "/admin/screens", { method: "POST", body: payload });
}

export async function adminReservations(token) {
  return authFetch(token, "/admin/reservations");
}

export async function adminReport(token, { fromDate, toDate } = {}) {
  const q = new URLSearchParams();
  if (fromDate) q.set("from_date", fromDate);
  if (toDate) q.set("to_date", toDate);
  const qs = q.toString();
  return authFetch(token, `/admin/report/summary${qs ? `?${qs}` : ""}`);
}