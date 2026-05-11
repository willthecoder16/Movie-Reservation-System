import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";

import { me } from "../api";
import AppNav from "./AppNav";

export default function ProtectedLayout() {
  const token = localStorage.getItem("token");
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    me(token)
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .catch(() => {
        if (!cancelled) {
          localStorage.removeItem("token");
          navigate("/login", { replace: true });
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token, navigate]);

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (loading || !user) {
    return <p style={{ padding: "1.5rem", textAlign: "center" }}>Loading…</p>;
  }

  return (
    <>
      <AppNav user={user} />
      <Outlet context={{ user, token }} />
    </>
  );
}
