import { useState, useEffect, useCallback } from "react";
import { apiGet, apiPost, apiDelete } from "../api";
import { Plus, Trash2, ChevronLeft, ChevronRight } from "lucide-react";

const MONTHS = ["January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"];
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function getDaysInMonth(year, month) { return new Date(year, month, 0).getDate(); }
function pad2(n) { return String(n).padStart(2, "0"); }

export default function HabitsPage() {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [habits, setHabits] = useState([]);
  const [logs, setLogs] = useState({});
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("checkbox");
  const [editingCell, setEditingCell] = useState(null);
  const [numInput, setNumInput] = useState("");

  const loadHabits = useCallback(async () => {
    try { setHabits(await apiGet("/api/habits")); } catch { }
  }, []);

  const loadLogs = useCallback(async () => {
    try {
      const data = await apiGet(`/api/habits/logs?year=${year}&month=${month}`);
      const map = {};
      data.forEach(l => { map[`${l.date}|${l.habit_id}`] = l.value; });
      setLogs(map);
    } catch { }
  }, [year, month]);

  useEffect(() => { loadHabits(); }, []);
  useEffect(() => { loadLogs(); }, [year, month]);

  const daysInMonth = getDaysInMonth(year, month);
  const rows = Array.from({ length: daysInMonth }, (_, i) => {
    const d = i + 1;
    const dt = new Date(year, month - 1, d);
    return { d, date: `${year}-${pad2(month)}-${pad2(d)}`, dayName: DAYS[dt.getDay()] };
  });

  const logKey = (date, hid) => `${date}|${hid}`;
  const checkboxHabits = habits.filter(h => h.type === "checkbox");

  function dailyScore(date) {
    if (!checkboxHabits.length) return null;
    const done = checkboxHabits.filter(h => logs[logKey(date, h.id)] === true).length;
    return Math.round((done / checkboxHabits.length) * 100);
  }

  function monthlyRate(hid) {
    const h = habits.find(x => x.id === hid);
    if (!h) return null;
    if (h.type === "number") {
      const vals = rows.map(r => logs[logKey(r.date, hid)]).filter(v => v != null && v !== false);
      if (!vals.length) return null;
      return (vals.reduce((a, b) => a + Number(b), 0) / vals.length).toFixed(1);
    }
    const done = rows.filter(r => logs[logKey(r.date, hid)] === true).length;
    return Math.round((done / daysInMonth) * 100) + "%";
  }

  function overallMonthlyRate() {
    if (!checkboxHabits.length || !rows.length) return null;
    const total = rows.reduce((sum, r) => {
      const done = checkboxHabits.filter(h => logs[logKey(r.date, h.id)] === true).length;
      return sum + (done / checkboxHabits.length);
    }, 0);
    return Math.round((total / rows.length) * 100) + "%";
  }

  async function toggleCheckbox(date, hid) {
    const key = logKey(date, hid);
    const cur = logs[key] === true;
    const next = !cur;
    setLogs(prev => ({ ...prev, [key]: next }));
    try { await apiPost("/api/habits/logs", { date, habit_id: hid, value: next }); }
    catch { setLogs(prev => ({ ...prev, [key]: cur })); }
  }

  async function saveNumber(date, hid) {
    const val = parseFloat(numInput);
    setEditingCell(null);
    setNumInput("");
    if (isNaN(val)) return;
    const key = logKey(date, hid);
    setLogs(prev => ({ ...prev, [key]: val }));
    try { await apiPost("/api/habits/logs", { date, habit_id: hid, value: val }); } catch { }
  }

  async function addHabit() {
    if (!newName.trim()) return;
    try { const h = await apiPost("/api/habits", { name: newName.trim(), type: newType }); setHabits(prev => [...prev, h]); } catch { }
    setNewName(""); setNewType("checkbox"); setAdding(false);
  }

  async function deleteHabit(hid) {
    if (!confirm("Delete this habit and all its logs?")) return;
    try { await apiDelete(`/api/habits/${hid}`); setHabits(prev => prev.filter(h => h.id !== hid)); } catch { }
  }

  function prevMonth() { month === 1 ? (setYear(y => y - 1), setMonth(12)) : setMonth(m => m - 1); }
  function nextMonth() { month === 12 ? (setYear(y => y + 1), setMonth(1)) : setMonth(m => m + 1); }

  function scoreColor(pct) {
    if (pct === null) return "var(--text-2)";
    if (pct === 0) return "var(--red)";
    if (pct < 50) return "var(--amber)";
    if (pct < 80) return "var(--amber)";
    return "var(--green)";
  }

  function cellBg(date, hid) {
    const key = logKey(date, hid);
    if (!(key in logs)) return "transparent";
    return logs[key] === true ? "rgba(34,197,94,.12)" : "rgba(239,68,68,.08)";
  }

  return (
    <div className="page" style={{ padding: "24px 20px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button onClick={prevMonth} className="calendar-nav-btn"><ChevronLeft size={16} /></button>
          <h1 className="page-title" style={{ margin: 0, minWidth: 240, textAlign: "center" }}>
            {MONTHS[month - 1]} {year}
          </h1>
          <button onClick={nextMonth} className="calendar-nav-btn"><ChevronRight size={16} /></button>
        </div>
        <button onClick={() => setAdding(true)} className="btn btn-primary" style={{ marginLeft: "auto" }}>
          <Plus size={14} /> Add Habit
        </button>
      </div>

      {adding && (
        <div style={{ display: "flex", gap: 8, marginBottom: 16, alignItems: "center" }}>
          <input autoFocus className="input" value={newName} onChange={e => setNewName(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter") addHabit(); if (e.key === "Escape") setAdding(false); }}
            placeholder="Habit name…" style={{ maxWidth: 220 }} />
          <select className="input" value={newType} onChange={e => setNewType(e.target.value)} style={{ width: 150 }}>
            <option value="checkbox">Checkbox</option>
            <option value="number">Number</option>
          </select>
          <button onClick={addHabit} className="btn btn-primary">Add</button>
          <button onClick={() => setAdding(false)} className="btn btn-ghost">Cancel</button>
        </div>
      )}

      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 13 }}>
          <thead>
            <tr>
              <th style={thS}>Date</th>
              <th style={thS}>Day</th>
              {habits.map(h => (
                <th key={h.id} style={{ ...thS, minWidth: 90 }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
                    <span>{h.name}</span>
                    <button onClick={() => deleteHabit(h.id)} title="Delete"
                      style={{ background: "none", border: "none", color: "var(--text-2)", cursor: "pointer", fontSize: 10, padding: 0 }}>✕</button>
                  </div>
                </th>
              ))}
              <th style={{ ...thS, color: "var(--accent)" }}>Score</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ d, date, dayName }) => {
              const score = dailyScore(date);
              const isToday = date === `${today.getFullYear()}-${pad2(today.getMonth() + 1)}-${pad2(today.getDate())}`;
              return (
                <tr key={date} style={{ background: isToday ? "rgba(59,130,246,.06)" : undefined }}>
                  <td style={{ ...tdS, fontWeight: isToday ? 600 : 400, color: isToday ? "var(--accent)" : "var(--text-0)" }}>
                    {MONTHS[month - 1].slice(0, 3)} {pad2(d)}
                  </td>
                  <td style={{ ...tdS, color: "var(--text-2)" }}>{dayName}</td>
                  {habits.map(h => {
                    const key = logKey(date, h.id);
                    if (h.type === "number") {
                      const isEditing = editingCell === key;
                      return (
                        <td key={h.id} style={{ ...tdS, background: "var(--bg-2)" }}>
                          {isEditing ? (
                            <input autoFocus value={numInput} onChange={e => setNumInput(e.target.value)}
                              onBlur={() => saveNumber(date, h.id)}
                              onKeyDown={e => { if (e.key === "Enter") saveNumber(date, h.id); if (e.key === "Escape") setEditingCell(null); }}
                              style={{ width: 56, background: "var(--bg-3)", border: "1px solid var(--border-active)", color: "var(--text-0)", borderRadius: 4, padding: "2px 6px", textAlign: "center", fontSize: 12 }} />
                          ) : (
                            <span onClick={() => { setEditingCell(key); setNumInput(logs[key] != null ? String(logs[key]) : ""); }}
                              style={{ cursor: "pointer", color: logs[key] != null ? "var(--accent)" : "var(--text-2)", display: "block", textAlign: "center" }}>
                              {logs[key] != null ? logs[key] : "—"}
                            </span>
                          )}
                        </td>
                      );
                    }
                    const checked = logs[key] === true;
                    const hasLog = key in logs;
                    return (
                      <td key={h.id} onClick={() => toggleCheckbox(date, h.id)}
                        style={{ ...tdS, background: cellBg(date, h.id), cursor: "pointer", textAlign: "center", userSelect: "none" }}>
                        <span style={{ fontSize: 15, color: checked ? "var(--green)" : hasLog ? "var(--red)" : "var(--text-2)" }}>
                          {checked ? "✓" : "·"}
                        </span>
                      </td>
                    );
                  })}
                  <td style={{ ...tdS, textAlign: "center", fontWeight: 600, color: scoreColor(score) }}>
                    {score !== null ? `${score}%` : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr style={{ borderTop: "2px solid var(--border)" }}>
              <td style={{ ...tfS, color: "var(--accent)" }} colSpan={2}>Monthly</td>
              {habits.map(h => <td key={h.id} style={{ ...tfS, color: "var(--green)" }}>{monthlyRate(h.id) ?? "—"}</td>)}
              <td style={{ ...tfS, color: "var(--accent)" }}>{overallMonthlyRate() ?? "—"}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      {habits.length === 0 && (
        <div style={{ textAlign: "center", color: "var(--text-2)", marginTop: 48, fontSize: 14 }}>
          No habits yet — click <strong style={{ color: "var(--accent)" }}>+ Add Habit</strong> to start tracking.
        </div>
      )}
    </div>
  );
}

const thS = {
  padding: "10px 12px", background: "var(--bg-2)", color: "var(--text-1)",
  fontWeight: 600, textAlign: "center", border: "1px solid var(--border)",
  whiteSpace: "nowrap", position: "sticky", top: 0, zIndex: 1, fontSize: 12,
};
const tdS = {
  padding: "5px 10px", border: "1px solid var(--border)", color: "var(--text-0)",
  whiteSpace: "nowrap", transition: "background .1s",
};
const tfS = {
  padding: "10px 12px", border: "1px solid var(--border)", textAlign: "center",
  fontWeight: 700, fontSize: 13, background: "var(--bg-1)",
};
