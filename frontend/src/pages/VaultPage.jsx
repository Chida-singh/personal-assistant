import { useState, useEffect } from "react";
import { apiGet, apiPost, apiDelete } from "../api";
import { Plus, Trash2, Edit2, Eye, EyeOff, Copy } from "lucide-react";

export default function VaultPage() {
  const [entries, setEntries] = useState([]);
  const [editingEntry, setEditingEntry] = useState(null);
  const [form, setForm] = useState({ service: "", username: "", password: "", url: "", notes: "" });
  const [visiblePasswords, setVisiblePasswords] = useState({});
  const [search, setSearch] = useState("");

  const filteredEntries = entries.filter(e => 
    e.service.toLowerCase().includes(search.toLowerCase()) || 
    e.username.toLowerCase().includes(search.toLowerCase()) || 
    e.notes.toLowerCase().includes(search.toLowerCase())
  );

  const load = async () => {
    try {
      const data = await apiGet("/api/vault");
      setEntries(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    if (!form.service.trim() || !form.password.trim()) return;

    const newEntry = { ...form };
    const isUpdate = !!editingEntry;
    
    // Optimistic UI
    if (isUpdate) {
      newEntry.id = editingEntry.id;
      setEntries(prev => prev.map(e => e.id === newEntry.id ? newEntry : e));
    } else {
      newEntry.id = "temp-" + Date.now();
      setEntries(prev => [...prev, newEntry]);
    }
    
    setEditingEntry(null);
    setForm({ service: "", username: "", password: "", url: "", notes: "" });

    try {
      const resp = await apiPost("/api/vault", newEntry);
      if (!isUpdate) {
        // Update temp id with real id
        setEntries(prev => prev.map(e => e.id === newEntry.id ? resp.entry : e));
      }
    } catch (err) {
      console.error("Failed to save entry");
      load(); // Revert on failure
    }
  };

  const del = async (id) => {
    setEntries(prev => prev.filter(e => e.id !== id));
    try {
      await apiDelete(`/api/vault/${id}`);
    } catch (err) {
      console.error("Failed to delete entry");
      load(); // Revert on failure
    }
  };

  const edit = (entry) => {
    setEditingEntry(entry);
    setForm({ ...entry });
  };

  const toggleVisibility = (id) => {
    setVisiblePasswords(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="page">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <h1 className="page-title">Vault</h1>
          <p className="page-subtitle" style={{ marginBottom: 0 }}>Securely manage your passwords</p>
        </div>
        <input 
          className="input" 
          placeholder="Search vault..." 
          value={search} 
          onChange={e => setSearch(e.target.value)} 
          style={{ width: 250 }}
        />
      </div>

      <div className="card" style={{ padding: 20, marginBottom: 30 }}>
        <h3 style={{ marginTop: 0, marginBottom: 15 }}>{editingEntry ? "Edit Password" : "Add New Password"}</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
          <input className="input" placeholder="Service (e.g., Gmail, Netflix)" value={form.service} onChange={e => setForm({...form, service: e.target.value})} />
          <input className="input" placeholder="Username / Email" value={form.username} onChange={e => setForm({...form, username: e.target.value})} />
          <input className="input" placeholder="Password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} type="text" />
          <input className="input" placeholder="URL (Optional)" value={form.url} onChange={e => setForm({...form, url: e.target.value})} />
        </div>
        <input className="input" placeholder="Notes (Optional)" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} style={{ width: "100%", marginBottom: 10 }} />
        
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-primary" onClick={save}>
            {editingEntry ? "Update" : "Save"}
          </button>
          {editingEntry && (
            <button className="btn btn-ghost" onClick={() => { setEditingEntry(null); setForm({ service: "", username: "", password: "", url: "", notes: "" }); }}>
              Cancel
            </button>
          )}
        </div>
      </div>

      {filteredEntries.length > 0 ? (
        <div style={{ display: "grid", gap: 15, gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))" }}>
          {filteredEntries.map(entry => (
            <div key={entry.id} className="card fade-in" style={{ padding: 15, position: "relative" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                <div style={{ fontWeight: 600, fontSize: 16 }}>{entry.service}</div>
                <div style={{ display: "flex", gap: 5 }}>
                  <button className="btn btn-ghost" style={{ padding: 5 }} onClick={() => edit(entry)}><Edit2 size={14} /></button>
                  <button className="btn btn-ghost" style={{ padding: 5, color: "var(--text-muted)" }} onClick={() => del(entry.id)}><Trash2 size={14} /></button>
                </div>
              </div>
              
              {entry.username && <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 5 }}>{entry.username}</div>}
              
              <div style={{ display: "flex", alignItems: "center", gap: 10, background: "var(--bg-primary)", padding: "5px 10px", borderRadius: 4, marginBottom: 10 }}>
                <div style={{ flex: 1, fontFamily: "monospace", fontSize: 14 }}>
                  {visiblePasswords[entry.id] ? entry.password : "••••••••••••"}
                </div>
                <button className="btn btn-ghost" style={{ padding: 5 }} onClick={() => toggleVisibility(entry.id)}>
                  {visiblePasswords[entry.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
                <button className="btn btn-ghost" style={{ padding: 5 }} onClick={() => copyToClipboard(entry.password)}>
                  <Copy size={14} />
                </button>
              </div>

              {entry.url && (
                <div style={{ fontSize: 12, marginBottom: 5 }}>
                  <a href={entry.url.startsWith("http") ? entry.url : `https://${entry.url}`} target="_blank" rel="noreferrer" style={{ color: "var(--accent-amber)", textDecoration: "none" }}>{entry.url}</a>
                </div>
              )}
              {entry.notes && <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 5 }}>{entry.notes}</div>}
            </div>
          ))}
        </div>
      ) : (
        <div className="chat-empty" style={{ marginTop: 60 }}>
          <div className="empty-mark" aria-hidden="true" />
          <div className="chat-empty-text">No passwords saved yet.</div>
        </div>
      )}
    </div>
  );
}
