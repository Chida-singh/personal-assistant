import { useState, useEffect, useCallback } from "react";
import { apiGet, apiPost, apiDelete } from "../api";

const MONTHS = ["January","February","March","April","May","June",
                "July","August","September","October","November","December"];
const DAYS   = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

function getDaysInMonth(year, month) {
  return new Date(year, month, 0).getDate();
}

function pad2(n) { return String(n).padStart(2, "0"); }

export default function HabitsPage() {
  const today = new Date();
  const [year,  setYear]  = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);

  const [habits, setHabits] = useState([]);
  const [logs,   setLogs]   = useState({});   // key: "YYYY-MM-DD|habit_id" → value

  const [adding,    setAdding]    = useState(false);
  const [newName,   setNewName]   = useState("");
  const [newType,   setNewType]   = useState("checkbox");
  const [editingCell, setEditingCell] = useState(null);  // "date|habit_id"
  const [numInput,    setNumInput]    = useState("");

  // ── Load ────────────────────────────────────────────────────────────────
  const loadHabits = useCallback(async () => {
    try { setHabits(await apiGet("/api/habits")); } catch {}
  }, []);

  const loadLogs = useCallback(async () => {
    try {
      const data = await apiGet(`/api/habits/logs?year=${year}&month=${month}`);
      const map = {};
      data.forEach(l => { map[`${l.date}|${l.habit_id}`] = l.value; });
      setLogs(map);
    } catch {}
  }, [year, month]);

  useEffect(() => { loadHabits(); }, []);
  useEffect(() => { loadLogs(); },   [year, month]);

  // ── Helpers ─────────────────────────────────────────────────────────────
  const daysInMonth = getDaysInMonth(year, month);
  const rows = Array.from({ length: daysInMonth }, (_, i) => {
    const d   = i + 1;
    const dt  = new Date(year, month - 1, d);
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
      const avg = vals.reduce((a, b) => a + Number(b), 0) / vals.length;
      return avg.toFixed(1);
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

  // ── Interactions ─────────────────────────────────────────────────────────
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
    try { await apiPost("/api/habits/logs", { date, habit_id: hid, value: val }); }
    catch {}
  }

  async function addHabit() {
    if (!newName.trim()) return;
    try {
      const h = await apiPost("/api/habits", { name: newName.trim(), type: newType });
      setHabits(prev => [...prev, h]);
    } catch {}
    setNewName(""); setNewType("checkbox"); setAdding(false);
  }

  async function deleteHabit(hid) {
    if (!confirm("Delete this habit and all its logs?")) return;
    try {
      await apiDelete(`/api/habits/${hid}`);
      setHabits(prev => prev.filter(h => h.id !== hid));
    } catch {}
  }

  function prevMonth() { month === 1 ? (setYear(y => y-1), setMonth(12)) : setMonth(m => m-1); }
  function nextMonth() { month === 12? (setYear(y => y+1), setMonth(1))  : setMonth(m => m+1); }

  // ── Score colour ─────────────────────────────────────────────────────────
  function scoreColor(pct) {
    if (pct === null) return "#555";
    if (pct === 0)   return "#ef4444";
    if (pct < 50)    return "#f97316";
    if (pct < 80)    return "#eab308";
    return "#22c55e";
  }

  // ── Cell colour for checkbox ──────────────────────────────────────────────
  const DONE_BG  = "#1a3d2b";
  const MISS_BG  = "#3d1a1a";
  const NONE_BG  = "transparent";

  function cellBg(date, hid) {
    const key = logKey(date, hid);
    if (!(key in logs)) return NONE_BG;
    return logs[key] === true ? DONE_BG : MISS_BG;
  }

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="page" style={{ padding: "24px 16px" }}>
      {/* Header */}
      <div style={{ display:"flex", alignItems:"center", gap:16, marginBottom:20, flexWrap:"wrap" }}>
        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
          <button onClick={prevMonth} style={navBtn}>‹</button>
          <h1 style={{ margin:0, fontSize:20, fontWeight:700, color:"var(--text-primary)", minWidth:200, textAlign:"center" }}>
            {MONTHS[month-1]} {year} Habit Tracker
          </h1>
          <button onClick={nextMonth} style={navBtn}>›</button>
        </div>
        <button onClick={() => setAdding(true)} style={addBtn}>+ Add Habit</button>
      </div>

      {/* Add habit form */}
      {adding && (
        <div style={{ display:"flex", gap:8, marginBottom:16, alignItems:"center" }}>
          <input
            autoFocus
            value={newName}
            onChange={e => setNewName(e.target.value)}
            onKeyDown={e => { if (e.key==="Enter") addHabit(); if (e.key==="Escape") setAdding(false); }}
            placeholder="Habit name…"
            style={inputStyle}
          />
          <select value={newType} onChange={e => setNewType(e.target.value)} style={inputStyle}>
            <option value="checkbox">Checkbox</option>
            <option value="number">Number (e.g. weight)</option>
          </select>
          <button onClick={addHabit} style={addBtn}>Add</button>
          <button onClick={() => setAdding(false)} style={cancelBtn}>Cancel</button>
        </div>
      )}

      {/* Table */}
      <div style={{ overflowX:"auto" }}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={{ ...thStyle, minWidth:70 }}>Date</th>
              <th style={{ ...thStyle, minWidth:50 }}>Day</th>
              {habits.map(h => (
                <th key={h.id} style={{ ...thStyle, minWidth:100 }}>
                  <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:4 }}>
                    <span>{h.name}</span>
                    <button
                      onClick={() => deleteHabit(h.id)}
                      title="Delete habit"
                      style={{ background:"none", border:"none", color:"#555", cursor:"pointer", fontSize:11, padding:0, lineHeight:1 }}
                    >✕</button>
                  </div>
                </th>
              ))}
              <th style={{ ...thStyle, minWidth:90, color:"#fbbf24" }}>Daily Score</th>
            </tr>
          </thead>

          <tbody>
            {rows.map(({ d, date, dayName }) => {
              const score = dailyScore(date);
              const isToday = date === `${today.getFullYear()}-${pad2(today.getMonth()+1)}-${pad2(today.getDate())}`;
              return (
                <tr key={date} style={{ background: isToday ? "rgba(251,191,36,0.06)" : undefined }}>
                  <td style={{ ...tdStyle, fontWeight: isToday ? 700 : 400, color: isToday ? "#fbbf24" : "var(--text-primary)" }}>
                    {MONTHS[month-1].slice(0,3)} {pad2(d)}
                  </td>
                  <td style={{ ...tdStyle, color:"#888" }}>{dayName}</td>

                  {habits.map(h => {
                    const key = logKey(date, h.id);
                    if (h.type === "number") {
                      const isEditing = editingCell === key;
                      return (
                        <td key={h.id} style={{ ...tdStyle, background:"#1e1e1e" }}>
                          {isEditing ? (
                            <input
                              autoFocus
                              value={numInput}
                              onChange={e => setNumInput(e.target.value)}
                              onBlur={() => saveNumber(date, h.id)}
                              onKeyDown={e => { if(e.key==="Enter") saveNumber(date, h.id); if(e.key==="Escape") setEditingCell(null); }}
                              style={{ width:60, background:"#2a2a2a", border:"1px solid #444", color:"var(--text-primary)", borderRadius:4, padding:"2px 6px", textAlign:"center" }}
                            />
                          ) : (
                            <span
                              onClick={() => { setEditingCell(key); setNumInput(logs[key] != null ? String(logs[key]) : ""); }}
                              style={{ cursor:"pointer", color: logs[key] != null ? "#93c5fd" : "#555", display:"block", textAlign:"center" }}
                            >
                              {logs[key] != null ? logs[key] : "—"}
                            </span>
                          )}
                        </td>
                      );
                    }

                    // checkbox
                    const checked = logs[key] === true;
                    const hasLog  = key in logs;
                    return (
                      <td
                        key={h.id}
                        onClick={() => toggleCheckbox(date, h.id)}
                        style={{ ...tdStyle, background: cellBg(date, h.id), cursor:"pointer", textAlign:"center", userSelect:"none" }}
                      >
                        <span style={{ fontSize:16, color: checked ? "#4ade80" : hasLog ? "#f87171" : "#444" }}>
                          {checked ? "☑" : "☐"}
                        </span>
                      </td>
                    );
                  })}

                  <td style={{ ...tdStyle, textAlign:"center", fontWeight:600, color: scoreColor(score) }}>
                    {score !== null ? `${score}%` : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>

          {/* Monthly rate footer */}
          <tfoot>
            <tr style={{ borderTop:"2px solid #333" }}>
              <td style={{ ...tfStyle, color:"#fbbf24" }} colSpan={2}>Monthly Rate</td>
              {habits.map(h => (
                <td key={h.id} style={{ ...tfStyle, color:"#4ade80" }}>
                  {monthlyRate(h.id) ?? "—"}
                </td>
              ))}
              <td style={{ ...tfStyle, color:"#fbbf24" }}>{overallMonthlyRate() ?? "—"}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      {habits.length === 0 && (
        <div style={{ textAlign:"center", color:"#555", marginTop:48, fontSize:15 }}>
          No habits yet — click <strong style={{ color:"#fbbf24" }}>+ Add Habit</strong> to start tracking.
        </div>
      )}
    </div>
  );
}

// ── Styles ──────────────────────────────────────────────────────────────────
const tableStyle = {
  borderCollapse: "collapse",
  width: "100%",
  fontSize: 13,
  fontFamily: "monospace",
};
const thStyle = {
  padding: "10px 12px",
  background: "#1a2a3a",
  color: "#93c5fd",
  fontWeight: 700,
  textAlign: "center",
  border: "1px solid #2a3a4a",
  whiteSpace: "nowrap",
  position: "sticky",
  top: 0,
  zIndex: 1,
};
const tdStyle = {
  padding: "6px 12px",
  border: "1px solid #222",
  color: "var(--text-primary)",
  whiteSpace: "nowrap",
  transition: "background 0.1s",
};
const tfStyle = {
  padding: "10px 12px",
  border: "1px solid #333",
  textAlign: "center",
  fontWeight: 700,
  fontSize: 13,
  background: "#111",
};
const navBtn = {
  background: "#1e2a38", border: "1px solid #2a3a4a", color: "#93c5fd",
  borderRadius: 6, padding: "4px 14px", cursor: "pointer", fontSize: 18, lineHeight: 1,
};
const addBtn = {
  background: "#1a3d2b", border: "1px solid #2d6a4f", color: "#4ade80",
  borderRadius: 6, padding: "6px 14px", cursor: "pointer", fontSize: 13, fontWeight: 600,
};
const cancelBtn = {
  background: "transparent", border: "1px solid #444", color: "#888",
  borderRadius: 6, padding: "6px 14px", cursor: "pointer", fontSize: 13,
};
const inputStyle = {
  background: "#1e1e1e", border: "1px solid #444", color: "var(--text-primary)",
  borderRadius: 6, padding: "6px 10px", fontSize: 13,
};
