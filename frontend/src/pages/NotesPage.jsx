import { useState, useEffect } from "react";
import { apiGet, apiPost, apiDelete } from "../api";
import { Plus, Trash2 } from "lucide-react";

export default function NotesPage() {
  const [notes, setNotes] = useState([]);
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [editingKey, setEditingKey] = useState(null);
  const [editingValue, setEditingValue] = useState("");

  const load = async () => {
    try {
      const data = await apiGet("/api/notes");
      setNotes(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const add = async () => {
    if (!key.trim() || !value.trim()) return;
    const newKey = key.trim();
    const newValue = value.trim();
    setKey("");
    setValue("");

    setNotes(prev => {
      const existing = prev.find(n => n.key.toLowerCase() === newKey.toLowerCase());
      if (existing) {
        return prev.map(n => n.key.toLowerCase() === newKey.toLowerCase() ? { ...n, value: newValue } : n);
      }
      return [...prev, { key: newKey, value: newValue }];
    });

    await apiPost("/api/notes", { key: newKey, value: newValue });
  };

  const handleKey = (e) => {
    if (e.key === "Enter") add();
  };

  const del = async (noteKey) => {
    setNotes(prev => prev.filter(n => n.key !== noteKey));
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
    const newValue = editingValue.trim();
    setEditingKey(null);
    
    setNotes(prev => prev.map(note => note.key === n.key ? { ...note, value: newValue } : note));
    await apiPost("/api/notes", { key: n.key, value: newValue });
  };

  const handleEditKey = (e, n) => {
    if (e.key === "Enter") {
      saveEdit(n);
    } else if (e.key === "Escape") {
      setEditingKey(null);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Sticky Notes</h1>
      <p className="page-subtitle">
        Remember important things — birthdays, favorites, personal details
      </p>

      <div className="notes-add-row">
        <input
          className="input"
          placeholder="Key (e.g. birthday, fav food)"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          onKeyDown={handleKey}
          style={{ maxWidth: 200 }}
        />
        <input
          className="input"
          placeholder="Value (e.g. March 5, Pizza)"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKey}
        />
        <button className="btn btn-primary" onClick={add}>
          <Plus size={14} />
          Save
        </button>
      </div>

      {notes.length > 0 ? (
        <div className="notes-grid">
          {notes.map((n, i) => (
            <div key={n.key} className={`note-card note-color-${i % 6} fade-in`} onDoubleClick={() => handleDoubleClick(n)}>
              <button className="note-card-del" onClick={() => del(n.key)}>
                <Trash2 size={14} />
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
                  style={{ width: "100%", marginTop: 8, fontSize: 13 }}
                />
              ) : (
                <div className="note-value" style={{ cursor: "pointer" }} title="Double click to edit">{n.value}</div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="chat-empty" style={{ marginTop: 60 }}>
          <div className="empty-mark" aria-hidden="true" />
          <div className="chat-empty-text">No notes saved yet.</div>
        </div>
      )}
    </div>
  );
}
