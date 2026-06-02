import { useState, useEffect } from "react";
import { apiGet } from "../api";

export default function SettingsPage() {
  const [health, setHealth] = useState({ status: "checking...", model: "checking..." });

  useEffect(() => {
    async function checkHealth() {
      try {
        const data = await apiGet("/api/health");
        setHealth(data);
      } catch (err) {
        setHealth({ status: "offline", model: "unknown" });
      }
    }
    checkHealth();
  }, []);

  return (
    <div className="page">
      <h1 className="page-title">Settings</h1>
      <p className="page-subtitle">Configure your assistant</p>

      <div className="card" style={{ maxWidth: 500, padding: 24 }}>
        <div style={{ marginBottom: 16 }}>
          <div
            style={{
              color: "#888",
              fontSize: 11,
              fontWeight: 600,
              marginBottom: 6,
              letterSpacing: 0.5,
            }}
          >
            LLM MODEL
          </div>
          <div style={{ color: "#fbbf24", fontSize: 15, fontWeight: 600 }}>
            {health.model}
          </div>
          <div style={{ color: "#555", fontSize: 12, marginTop: 2 }}>
            Running via Ollama at localhost:11434
          </div>
        </div>

        <div className="sidebar-separator" style={{ margin: "16px 0" }} />

        <div>
          <div
            style={{
              color: "#888",
              fontSize: 11,
              fontWeight: 600,
              marginBottom: 6,
              letterSpacing: 0.5,
            }}
          >
            BACKEND
          </div>
          <div style={{ color: health.status === "ok" ? "#34d399" : "#f87171", fontSize: 15, fontWeight: 600 }}>
            FastAPI ({health.status})
          </div>
          <div style={{ color: "#555", fontSize: 12, marginTop: 2 }}>
            Running at localhost:8000
          </div>
        </div>
      </div>
    </div>
  );
}
