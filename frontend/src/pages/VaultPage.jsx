import { useState, useEffect } from "react";
import { apiGet, apiPost, apiPut, apiDelete } from "../api";
import { Plus, Trash2, Edit2, Eye, EyeOff, Copy, SortAsc, SortDesc, Clock } from "lucide-react";

const SORT_OPTIONS = [
  { value: "recent", label: "Recent", icon: Clock },
  { value: "az", label: "A → Z", icon: SortAsc },
  { value: "za", label: "Z → A", icon: SortDesc },
];

export default function VaultPage() {
  const [entries, setEntries] = useState([]);
  const [editingEntry, setEditingEntry] = useState(null);
  const [form, setForm] = useState({ service: "", username: "", password: "", url: "", notes: "" });
  const [visiblePasswords, setVisiblePasswords] = useState({});
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("recent");
  const [copied, setCopied] = useState(null);

  const load = async () => {
    try { setEntries(await apiGet("/api/vault")); } catch (err) { console.error(err); }
  };

  useEffect(() => { load(); }, []);

  const filteredEntries = entries
    .filter(e =>
      e.service.toLowerCase().includes(search.toLowerCase()) ||
      (e.username || "").toLowerCase().includes(search.toLowerCase()) ||
      (e.notes || "").toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => {
      if (sort === "az") return a.service.localeCompare(b.service);
      if (sort === "za") return b.service.localeCompare(a.service);
      const ta = a.created_at ? new Date(a.created_at).getTime() : 0;
      const tb = b.created_at ? new Date(b.created_at).getTime() : 0;
      return tb - ta;
    });

  const save = async () => {
    if (!form.service.trim() || !form.password.trim()) return;
    const isUpdate = !!editingEntry;
    if (isUpdate) {
      const updated = { ...form, id: editingEntry.id, created_at: editingEntry.created_at };
      setEntries(prev => prev.map(e => e.id === updated.id ? updated : e));
      setEditingEntry(null);
      setForm({ service: "", username: "", password: "", url: "", notes: "" });
      try { const resp = await apiPut(`/api/vault/${editingEntry.id}`, form); setEntries(prev => prev.map(e => e.id === editingEntry.id ? resp.entry : e)); }
      catch { load(); }
    } else {
      const tempId = "temp-" + Date.now();
      const tempEntry = { ...form, id: tempId, created_at: new Date().toISOString() };
      setEntries(prev => [tempEntry, ...prev]);
      setEditingEntry(null);
      setForm({ service: "", username: "", password: "", url: "", notes: "" });
      try { const resp = await apiPost("/api/vault", form); setEntries(prev => prev.map(e => e.id === tempId ? resp.entry : e)); }
      catch { load(); }
    }
  };

  const del = async (id) => {
    setEntries(prev => prev.filter(e => e.id !== id));
    try { await apiDelete(`/api/vault/${id}`); } catch { load(); }
  };

  const edit = (entry) => {
    setEditingEntry(entry);
    setForm({ service: entry.service, username: entry.username, password: entry.password, url: entry.url, notes: entry.notes });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const toggleVisibility = (id) => setVisiblePasswords(prev => ({ ...prev, [id]: !prev[id] }));

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 1500);
  };

  return (
    <div className="page">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 className="page-title">Vault</h1>
          <p className="page-subtitle" style={{ marginBottom: 0 }}>Securely store and manage passwords</p>
        </div>
        <input className="input" placeholder="Search…" value={search} onChange={e => setSearch(e.target.value)} style={{ width: 200 }} />
      </div>

      {/* Add/Edit Form with responsive-grid-2 */}
      <div className="card" style={{ padding: 20, marginBottom: 24 }}>
        <h3 style={{ margin: "0 0 14px", fontSize: 14, fontWeight: 600 }}>{editingEntry ? "Edit Password" : "Add Password"}</h3>
        <div className="responsive-grid-2" style={{ marginBottom: 10 }}>
          <input className="input" placeholder="Service (e.g. Gmail)" value={form.service} onChange={e => setForm({ ...form, service: e.target.value })} />
          <input className="input" placeholder="Username / Email" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} />
          <input className="input" placeholder="Password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} type="text" />
          <input className="input" placeholder="URL (optional)" value={form.url} onChange={e => setForm({ ...form, url: e.target.value })} />
        </div>
        <input className="input" placeholder="Notes (optional)" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} style={{ marginBottom: 12 }} />
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-primary" onClick={save}>{editingEntry ? "Update" : "Save"}</button>
          {editingEntry && <button className="btn btn-ghost" onClick={() => { setEditingEntry(null); setForm({ service: "", username: "", password: "", url: "", notes: "" }); }}>Cancel</button>}
        </div>
      </div>

      {/* Sort */}
      <div style={{ display: "flex", gap: 6, marginBottom: 20, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontSize: 12, color: "var(--text-2)", marginRight: 2 }}>Sort:</span>
        {SORT_OPTIONS.map(opt => {
          const Icon = opt.icon;
          const active = sort === opt.value;
          return (
            <button key={opt.value} onClick={() => setSort(opt.value)}
              className={active ? "btn btn-primary" : "btn btn-ghost"}
              style={{ padding: "4px 10px", fontSize: 12 }}>
              <Icon size={12} /> {opt.label}
            </button>
          );
        })}
        <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--text-2)" }}>
          {filteredEntries.length} {filteredEntries.length === 1 ? "entry" : "entries"}
        </span>
      </div>

      {/* Entries */}
      {filteredEntries.length > 0 ? (
        <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 280px), 1fr))" }}>
          {filteredEntries.map(entry => (
            <div key={entry.id} className="card fade-in" style={{ padding: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{entry.service}</div>
                  {entry.created_at && (
                    <div style={{ fontSize: 11, color: "var(--text-2)", marginTop: 2 }}>
                      {new Date(entry.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    </div>
                  )}
                </div>
                <div style={{ display: "flex", gap: 4 }}>
                  <button className="btn btn-ghost" style={{ padding: 5, border: "none" }} onClick={() => edit(entry)}><Edit2 size={14} /></button>
                  <button className="btn btn-ghost" style={{ padding: 5, border: "none" }} onClick={() => del(entry.id)}><Trash2 size={14} /></button>
                </div>
              </div>

              {entry.username && <div style={{ fontSize: 13, color: "var(--text-1)", marginBottom: 6 }}>{entry.username}</div>}

              <div style={{ display: "flex", alignItems: "center", gap: 8, background: "var(--bg-0)", padding: "6px 10px", borderRadius: 6, marginBottom: 8, border: "1px solid var(--border)" }}>
                <div style={{ flex: 1, fontFamily: "monospace", fontSize: 13, color: "var(--text-0)", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {visiblePasswords[entry.id] ? entry.password : "••••••••"}
                </div>
                <button className="btn btn-ghost" style={{ padding: 3, border: "none" }} onClick={() => toggleVisibility(entry.id)}>
                  {visiblePasswords[entry.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
                <button className="btn btn-ghost"
                  style={{ padding: 3, border: "none", color: copied === entry.id ? "var(--green)" : undefined }}
                  onClick={() => copyToClipboard(entry.password, entry.id)} title="Copy">
                  <Copy size={14} />
                </button>
              </div>

              {entry.url && (
                <div style={{ fontSize: 12, marginBottom: 4 }}>
                  <a href={entry.url.startsWith("http") ? entry.url : `https://${entry.url}`} target="_blank" rel="noreferrer"
                    style={{ color: "var(--accent)", textDecoration: "none" }}>{entry.url}</a>
                </div>
              )}
              {entry.notes && <div style={{ fontSize: 12, color: "var(--text-2)", marginTop: 4 }}>{entry.notes}</div>}
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
