import { useState } from "react";
import { login } from "../api";

export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("password");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(username, password);
      if (data && data.token) {
        onLoginSuccess(data.token);
      } else {
        setError("Invalid response from server");
      }
    } catch (err) {
      setError(err.message || "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "var(--bg-0)",
      padding: 20,
    }}>
      <div style={{
        width: "100%",
        maxWidth: 380,
        background: "var(--bg-1)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: "32px 28px",
      }}>
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <img
            src="/logo.png"
            alt=""
            style={{ width: 44, height: 44, borderRadius: 10, marginBottom: 14 }}
          />
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 6px", color: "var(--text-0)" }}>
            Personal Assistant
          </h1>
          <p style={{ color: "var(--text-2)", fontSize: 13, margin: 0 }}>
            Sign in to continue
          </p>
        </div>

        {error && (
          <div style={{
            background: "rgba(239,68,68,.1)",
            border: "1px solid rgba(239,68,68,.3)",
            color: "var(--red)",
            borderRadius: 8,
            padding: "10px 12px",
            fontSize: 13,
            marginBottom: 16,
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 14 }}>
            <label style={{
              display: "block", fontSize: 12, fontWeight: 500,
              color: "var(--text-1)", marginBottom: 5,
            }}>
              Username
            </label>
            <input
              className="input"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{
              display: "block", fontSize: 12, fontWeight: 500,
              color: "var(--text-1)", marginBottom: 5,
            }}>
              Password
            </label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{
              width: "100%",
              padding: 11,
              fontSize: 14,
              justifyContent: "center",
            }}
          >
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <p style={{ textAlign: "center", color: "var(--text-2)", fontSize: 11, marginTop: 20 }}>
          Self-hosted · JWT + SQLite
        </p>
      </div>
    </div>
  );
}
