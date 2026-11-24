import { useState, useEffect } from "react";
import { apiGet, apiPost, apiDelete } from "../api";
import { Plus, Trash2, Search } from "lucide-react";

export default function NotesPage() {
  const [notes, setNotes] = useState([]);
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [search, setSearch] = useState("");
  const [editingKey, setEditingKey] = useState(null);
  const [editingValue, setEditingValue] = useState("");

  const load = async () => {
    try {
      setNotes(await apiGet("/api/notes"));
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const add = async () => {
    if (!key.trim() || !value.trim()) return;
    const k = key.trim(),
      v = value.trim();
    setKey("");
    setValue("");
    setNotes((prev) => {
      const existing = prev.find((n) => n.key.toLowerCase() === k.toLowerCase());
      if (existing) return prev.map((n) => (n.key.toLowerCase() === k.toLowerCase() ? { ...n, value: v } : n));
      return [...prev, { key: k, value: v }];
    });
    await apiPost("/api/notes", { key: k, value: v });
  };

  const handleKey = (e) => {
    if (e.key === "Enter") add();
  };

  const del = async (noteKey) => {
    setNotes((prev) => prev.filter((n) => n.key !== noteKey));
    await apiDelete(`/api/notes/${encodeURIComponent(noteKey)}`);
  };

  const handleDoubleClick = (n) => {
    setEditingKey(n.key);
    setEditingValue(n.value);
  };

  const saveEdit = async (n) => {
    if (!editingValue.trim()) {
      setEditingKey(null);
      return;
    }
    const v = editingValue.trim();
    setEditingKey(null);
    setNotes((prev) => prev.map((note) => (note.key === n.key ? { ...note, value: v } : note)));
    await apiPost("/api/notes", { key: n.key, value: v });
  };

  const handleEditKey = (e, n) => {
    if (e.key === "Enter") saveEdit(n);
    else if (e.key === "Escape") setEditingKey(null);
  };

  const filteredNotes = notes.filter(
    (n) =>
      n.key.toLowerCase().includes(search.toLowerCase()) ||
      n.value.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 10 }}>
        <div>
          <h1 className="page-title">Notes</h1>
          <p className="page-subtitle" style={{ marginBottom: 0 }}>Quick reference — double-click any note to edit</p>
        </div>
        <div style={{ position: "relative" }}>
          <Search size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--text-2)", pointerEvents: "none" }} />
          <input
            className="input"
            placeholder="Search notes…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: 30, width: 200 }}
          />
        </div>
      </div>

      <div className="notes-add-row">
        <input
          className="input"
          placeholder="Label (e.g. birthday)"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          onKeyDown={handleKey}
          style={{ maxWidth: 220 }}
        />
        <input
          className="input"
          placeholder="Value (e.g. March 5)"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKey}
        />
        <button className="btn btn-primary" onClick={add}>
          <Plus size={14} /> Save
        </button>
      </div>

      {filteredNotes.length > 0 ? (
        <div className="notes-grid">
          {filteredNotes.map((n, i) => (
            <div
              key={n.key}
              className={`note-card note-accent-${i % 6} fade-in`}
              onDoubleClick={() => handleDoubleClick(n)}
            >
              <button className="note-card-del" onClick={() => del(n.key)}>
                <Trash2 size={13} />
              </button>
              <div className="note-key">{n.key}</div>
              {editingKey === n.key ? (
                <input
                  autoFocus
                  className="input"
                  value={editingValue}
                  onChange={(e) => setEditingValue(e.target.value)}
                  onBlur={() => saveEdit(n)}
                  onKeyDown={(e) => handleEditKey(e, n)}
                  style={{
                    width: "100%",
                    marginTop: 6,
                    fontSize: 13,
                  }}
                />
              ) : (
                <div className="note-value" style={{ cursor: "pointer" }} title="Double click to edit">
                  {n.value}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="chat-empty" style={{ marginTop: 60 }}>
          <div className="empty-mark" aria-hidden="true" />
          <div className="chat-empty-text">No notes found.</div>
        </div>
      )}
    </div>
  );
}
