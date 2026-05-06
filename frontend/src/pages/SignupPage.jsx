import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { register } from "../api";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    setMsg("");
    try {
      await register(email, password);
      setMsg("Account created. Redirecting to login...");
      setTimeout(() => navigate("/login"), 800);
    } catch (error) {
      setErr(error.message);
    }
  }

  return (
    <form onSubmit={onSubmit}>
      <h1>Sign Up</h1>
      <input
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        type="email"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password (min 8 chars)"
      />
      <button type="submit">Create Account</button>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
      {msg && <p>{msg}</p>}
      {err && <p>{err}</p>}
    </form>
  );
}