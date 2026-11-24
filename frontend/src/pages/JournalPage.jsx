import { useState, useEffect } from "react";
import { apiGet, apiPost, apiDelete } from "../api";
import { Trash2 } from "lucide-react";

const MOODS = [
  { val: 1, label: "Rough", color: "var(--red)" },
  { val: 2, label: "Low", color: "var(--amber)" },
  { val: 3, label: "Neutral", color: "var(--text-1)" },
  { val: 4, label: "Good", color: "var(--accent)" },
  { val: 5, label: "Great", color: "var(--green)" },
];

export default function JournalPage() {
  const todayStr = new Date().toISOString().slice(0, 10);
  const [selectedDate, setSelectedDate] = useState(todayStr);
  const [mood, setMood] = useState(3);
  const [content, setContent] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [savedStatus, setSavedStatus] = useState("");

  const loadEntries = async () => {
    try {
      const data = await apiGet("/api/journal?limit=30");
      setEntries(data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const loadStats = async () => {
    try {
      const data = await apiGet("/api/journal/stats");
      setStats(data);
    } catch {}
  };

  const loadDateEntry = async (date) => {
    try {
      const entry = await apiGet(`/api/journal/${date}`);
      setMood(entry.mood || 3);
      setContent(entry.content || "");
      setTagsInput(entry.tags ? entry.tags.join(", ") : "");
    } catch {
      setMood(3);
      setContent("");
      setTagsInput("");
    }
  };

  useEffect(() => {
    loadEntries();
    loadStats();
    loadDateEntry(todayStr);
  }, []);

  const handleDateChange = (newDate) => {
    setSelectedDate(newDate);
    loadDateEntry(newDate);
  };

  const saveCurrentEntry = async () => {
    if (!content.trim() && !tagsInput.trim()) return;
    try {
      await apiPost("/api/journal", {
        date: selectedDate,
        mood,
        content,
        tags: tagsInput,
      });
      setSavedStatus("Saved");
      setTimeout(() => setSavedStatus(""), 2000);
      loadEntries();
      loadStats();
    } catch {
      setSavedStatus("Error saving");
    }
  };

  const deleteEntry = async (id, e) => {
    e.stopPropagation();
    if (!confirm("Delete this journal entry?")) return;
    try {
      await apiDelete(`/api/journal/${id}`);
      loadEntries();
      loadStats();
      if (selectedDate === id) {
        setContent("");
        setTagsInput("");
      }
    } catch {}
  };

  const getMoodMeta = (m) => MOODS.find((x) => x.val === m) || MOODS[2];

  return (
    <div className="page">
      <div>
        <h1 className="page-title">Journal</h1>
        <p className="page-subtitle">Daily reflection and mood tracking</p>
      </div>

      {/* Editor Card */}
      <div className="card" style={{ padding: 24, marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <input
              type="date"
              className="input"
              value={selectedDate}
              onChange={(e) => handleDateChange(e.target.value)}
              style={{ width: "auto" }}
            />
            {selectedDate === todayStr && (
              <span style={{ fontSize: 11, background: "rgba(59,130,246,.15)", color: "var(--accent)", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
                Today
              </span>
            )}
          </div>

          {/* Mood Selector without emojis */}
          <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
            <span style={{ fontSize: 12, color: "var(--text-2)", marginRight: 4 }}>Mood:</span>
            {MOODS.map((m) => (
              <button
                key={m.val}
                type="button"
                onClick={() => setMood(m.val)}
                className={mood === m.val ? "btn btn-primary" : "btn btn-ghost"}
                style={{
                  padding: "4px 10px",
                  fontSize: 12,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <span className="mood-dot" style={{ background: m.color }} />
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <textarea
          className="input"
          placeholder="Write your reflection for this day…"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={6}
          style={{ width: "100%", marginBottom: 14, minHeight: 120, lineHeight: 1.6 }}
        />

        <div style={{ display: "flex", alignItems: "center", gap: 10, justifyContent: "space-between", flexWrap: "wrap" }}>
          <input
            className="input"
            placeholder="Tags (comma-separated, e.g. workout, reading, travel)"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            style={{ maxWidth: 360, flex: 1, minWidth: 200 }}
          />

          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {savedStatus && (
              <span style={{ fontSize: 12, color: "var(--green)" }}>{savedStatus}</span>
            )}
            <button className="btn btn-primary" onClick={saveCurrentEntry}>
              Save Entry
            </button>
          </div>
        </div>
      </div>

      {/* Stats summary banner */}
      {stats && stats.total_entries > 0 && (
        <div style={{ display: "flex", gap: 12, marginBottom: 24, alignItems: "center", flexWrap: "wrap" }}>
          <span style={{ fontSize: 12, color: "var(--text-2)", textTransform: "uppercase", letterSpacing: ".04em" }}>
            Last 30 Days:
          </span>
          <span style={{ fontSize: 12, color: "var(--text-1)" }}>
            {stats.total_entries} entries recorded
          </span>
          {stats.average_mood && (
            <span style={{ fontSize: 12, color: "var(--accent)" }}>
              · Average mood: {stats.average_mood}/5 ({getMoodMeta(Math.round(stats.average_mood)).label})
            </span>
          )}
        </div>
      )}

      {/* Past Entries Timeline */}
      <h3 style={{ fontSize: 13, fontWeight: 600, color: "var(--text-1)", textTransform: "uppercase", letterSpacing: ".03em", marginBottom: 14 }}>
        Past Entries
      </h3>

      {entries.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {entries.map((item) => {
            const mMeta = getMoodMeta(item.mood);
            return (
              <div
                key={item.id}
                onClick={() => handleDateChange(item.date)}
                className="card fade-in"
                style={{
                  padding: 16,
                  cursor: "pointer",
                  borderLeft: `3px solid ${mMeta.color}`,
                  transition: "border-color .15s",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontWeight: 600, fontSize: 14, color: "var(--text-0)" }}>
                      {item.date}
                    </span>
                    <span style={{ fontSize: 12, color: mMeta.color, display: "inline-flex", alignItems: "center", gap: 6 }}>
                      <span className="mood-dot" style={{ background: mMeta.color }} />
                      {mMeta.label}
                    </span>
                  </div>
                  <button
                    onClick={(e) => deleteEntry(item.id, e)}
                    className="btn btn-ghost"
                    style={{ padding: 4, border: "none", color: "var(--text-2)" }}
                    title="Delete entry"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>

                <p style={{ fontSize: 13, color: "var(--text-1)", whiteSpace: "pre-wrap", margin: "0 0 8px" }}>
                  {item.content || <i style={{ color: "var(--text-2)" }}>No written notes</i>}
                </p>

                {item.tags && item.tags.length > 0 && (
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {item.tags.map((t, idx) => (
                      <span key={idx} style={{ fontSize: 10, background: "var(--bg-3)", color: "var(--text-2)", padding: "1px 6px", borderRadius: 4 }}>
                        #{t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="chat-empty" style={{ marginTop: 40 }}>
          <div className="empty-mark" />
          <div className="chat-empty-text">No journal entries yet.</div>
          <div style={{ color: "var(--text-2)", fontSize: 12 }}>Write your first reflection above.</div>
        </div>
      )}
    </div>
  );
}
