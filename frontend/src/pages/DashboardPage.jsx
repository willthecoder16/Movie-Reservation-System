import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { me } from "../api";

export default function DashboardPage() {
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;

    async function loadUser() {
      const token = localStorage.getItem("token");
      if (!token) {
        navigate("/login", { replace: true });
        return;
      }

      try {
        const profile = await me(token);
        if (isMounted) {
          setUser(profile);
          setError("");
        }
      } catch (err) {
        if (!isMounted) return;
        localStorage.removeItem("token");
        setError("Session expired. Please log in again.");
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadUser();
    return () => {
      isMounted = false;
    };
  }, [navigate]);

  function handleLogout() {
    localStorage.removeItem("token");
    navigate("/login", { replace: true });
  }

  if (loading) return <p>Loading dashboard...</p>;

  if (error) {
    return (
      <div>
        <p>{error}</p>
        <Link to="/login">Go to Log In</Link>
      </div>
    );
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Welcome {user?.email}</p>
      <p>Your role: {user?.role}</p>
      <button onClick={handleLogout}>Log Out</button>
    </div>
  );
}
