import { useState, useRef, useEffect } from "react";
import { apiPost } from "../api";
import { Send } from "lucide-react";

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const buildHistory = () =>
    messages.map((m) => ({ role: m.role, content: m.content }));

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", content: text };
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
        { role: "assistant", content: data.response },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
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
          <img src="/logo.png" alt="Cookie Logo" style={{ width: 64, height: 64, borderRadius: '16px', objectFit: 'cover' }} />
          <div className="chat-empty-text">
            Welcome to Cookie.
          </div>
          <div style={{ color: "#555", fontSize: 12 }}>
            Powered by Gemma 4. Ask me anything.
          </div>
        </div>
      ) : (
        <div className="chat-messages">
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
          placeholder="Type a message..."
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
