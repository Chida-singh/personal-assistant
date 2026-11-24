import { useState, useRef, useEffect } from "react";
import { apiPost } from "../api";
import { Send, Trash2 } from "lucide-react";

const STORAGE_KEY = "chat_history";
const MAX_STORED = 200;

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveHistory(messages) {
  try {
    const trimmed = messages.slice(-MAX_STORED);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch (e) {
    console.warn("Failed to save chat history:", e);
  }
}

export default function ChatPage() {
  const [messages, setMessages] = useState(() => loadHistory());
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    saveHistory(messages);
  }, [messages]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const buildHistory = () =>
    messages.map((m) => ({ role: m.role, content: m.content }));

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", content: text, ts: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const data = await apiPost("/api/chat", {
        message: text,
        history: buildHistory(),
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response, ts: Date.now() },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err.message}`, ts: Date.now() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = () => {
    if (window.confirm("Clear all chat history?")) {
      setMessages([]);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="chat-container">
      {messages.length === 0 ? (
        <div className="chat-empty">
          <img src="/logo.png" alt="" style={{ width: 56, height: 56, borderRadius: 14, objectFit: "cover" }} />
          <div className="chat-empty-text">What can I help you with?</div>
          <div style={{ color: "var(--text-2)", fontSize: 13 }}>Powered by Gemma 4</div>
        </div>
      ) : (
        <div className="chat-messages">
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 4 }}>
            <button
              onClick={clearHistory}
              style={{
                display: "flex", alignItems: "center", gap: 5,
                padding: "4px 10px", borderRadius: 6,
                border: "1px solid var(--border)", background: "transparent",
                color: "var(--text-2)", cursor: "pointer", fontSize: 12,
              }}
              title="Clear chat history"
            >
              <Trash2 size={12} />
              Clear
            </button>
          </div>

          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble ${m.role} fade-in`}>
              {m.content}
            </div>
          ))}
          {loading && (
            <div className="chat-bubble assistant fade-in">
              <div className="loading-dots">
                <span />
                <span />
                <span />
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>
      )}

      <div className="chat-input-bar">
        <input
          className="input"
          placeholder="Type a message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={loading}
        />
        <button
          className="chat-send-btn"
          onClick={send}
          disabled={loading || !input.trim()}
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
