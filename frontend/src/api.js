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