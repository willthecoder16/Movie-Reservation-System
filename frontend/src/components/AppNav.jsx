import { Link, useNavigate } from "react-router-dom";

import "../AppNav.css";

export default function AppNav({ user }) {
  const navigate = useNavigate();
  const isAdmin = user?.role === "admin";

  function logout() {
    localStorage.removeItem("token");
    navigate("/login", { replace: true });
  }

  return (
    <header className="app-nav">
      <div className="app-nav-inner">
        <Link to="/dashboard" className="app-nav-brand">
          MovieReserve
        </Link>
        <nav className="app-nav-links" aria-label="Main">
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/reservations">My reservations</Link>
          {isAdmin && <Link to="/admin">Admin</Link>}
        </nav>
        <div className="app-nav-user">
          <span className="app-nav-email" title={user?.email}>
            {user?.email}
            {user?.role ? ` · ${user.role}` : ""}
          </span>
          <button type="button" className="app-nav-logout" onClick={logout}>
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}
