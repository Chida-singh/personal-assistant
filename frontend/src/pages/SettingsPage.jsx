import { useState, useEffect } from "react";
import { apiGet, clearToken } from "../api";

export default function SettingsPage() {
  const [health, setHealth] = useState({ status: "checking…", llm_source: "checking…", storage: "checking…" });

  useEffect(() => {
    async function checkHealth() {
      try {
        const data = await apiGet("/api/health");
        setHealth(data);
      } catch {
        setHealth({ status: "offline", llm_source: "offline", storage: "unknown" });
      }
    }
    checkHealth();
  }, []);

  const statusColor = health.status === "ok" ? "var(--green)" : "var(--red)";
  const llmColor = health.llm_source === "ollama" ? "var(--green)" : health.llm_source === "gemini" ? "var(--accent)" : "var(--red)";

  return (
    <div className="page">
      <h1 className="page-title">Settings</h1>
      <p className="page-subtitle">System status and configuration</p>

      <div className="card" style={{ maxWidth: 500, padding: 24 }}>
        {/* AI Source */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ color: "var(--text-2)", fontSize: 11, fontWeight: 600, marginBottom: 6, letterSpacing: ".03em", textTransform: "uppercase" }}>
            AI Engine
          </div>
          <div style={{ color: llmColor, fontSize: 15, fontWeight: 600, textTransform: "uppercase" }}>
            {health.llm_source}
          </div>
          <div style={{ color: "var(--text-2)", fontSize: 12, marginTop: 3 }}>
            {health.llm_source === "ollama"
              ? "Running locally via Ollama"
              : health.llm_source === "gemini"
              ? "Google Gemini Flash API"
              : "Offline — start Ollama or set GEMINI_API_KEY"}
          </div>
        </div>

        <div style={{ height: 1, background: "var(--border)", margin: "0 0 20px" }} />

        {/* Backend */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ color: "var(--text-2)", fontSize: 11, fontWeight: 600, marginBottom: 6, letterSpacing: ".03em", textTransform: "uppercase" }}>
            Backend
          </div>
          <div style={{ color: statusColor, fontSize: 15, fontWeight: 600 }}>
            FastAPI ({health.status}) · SQLite ({health.storage})
          </div>
          <div style={{ color: "var(--text-2)", fontSize: 12, marginTop: 3 }}>
            Single process · optimized for 1 GB RAM
          </div>
        </div>

        <div style={{ height: 1, background: "var(--border)", margin: "0 0 20px" }} />

        {/* Session */}
        <div>
          <div style={{ color: "var(--text-2)", fontSize: 11, fontWeight: 600, marginBottom: 8, letterSpacing: ".03em", textTransform: "uppercase" }}>
            Session
          </div>
          <button onClick={() => clearToken()} className="btn" style={{
            background: "rgba(239,68,68,.1)",
            color: "var(--red)",
            border: "1px solid rgba(239,68,68,.2)",
          }}>
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
