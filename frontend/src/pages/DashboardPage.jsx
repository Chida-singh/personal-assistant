import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiPost, apiPut } from "../api";
import {
  CheckSquare,
  Flame,
  Calendar as CalIcon,
  BarChart3,
  BookOpen,
  ArrowRight,
  Clock,
  AlertCircle,
} from "lucide-react";

const MOODS = [
  { val: 1, label: "Rough", color: "var(--red)" },
  { val: 2, label: "Low", color: "var(--amber)" },
  { val: 3, label: "Neutral", color: "var(--text-1)" },
  { val: 4, label: "Good", color: "var(--accent)" },
  { val: 5, label: "Great", color: "var(--green)" },
];

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [journalMood, setJournalMood] = useState(3);
  const [journalText, setJournalText] = useState("");
  const [journalSaved, setJournalSaved] = useState(false);

  const loadDashboard = async () => {
    try {
      const res = await apiGet("/api/dashboard");
      setData(res);
      if (res.journal) {
        setJournalMood(res.journal.mood || 3);
        setJournalText(res.journal.content || "");
      }
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const toggleHabit = async (habitId, currentVal) => {
    if (!data) return;
    const nextVal = !currentVal;
    setData((prev) => {
      const updated = prev.habits.items.map((h) =>
        h.id === habitId ? { ...h, completed: nextVal, value: nextVal } : h
      );
      const completedCount = updated.filter((h) => h.completed).length;
      const totalCount = prev.habits.total;
      return {
        ...prev,
        habits: {
          ...prev.habits,
          items: updated,
          completed: completedCount,
          rate: totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0,
        },
      };
    });

    try {
      await apiPost("/api/habits/logs", {
        date: data.date,
        habit_id: habitId,
        value: nextVal,
      });
    } catch {
      loadDashboard();
    }
  };

  const completeTodo = async (taskName) => {
    setData((prev) => ({
      ...prev,
      todos: {
        ...prev.todos,
        items: prev.todos.items.filter((t) => t.task !== taskName),
        total_pending: Math.max(0, prev.todos.total_pending - 1),
      },
    }));

    try {
      await apiPut("/api/todos/complete", { task: taskName });
    } catch {
      loadDashboard();
    }
  };

  const saveJournal = async () => {
    if (!data) return;
    try {
      await apiPost("/api/journal", {
        date: data.date,
        mood: journalMood,
        content: journalText,
      });
      setJournalSaved(true);
      setTimeout(() => setJournalSaved(false), 2000);
    } catch (err) {
      alert("Failed to save journal entry");
    }
  };

  if (loading) {
    return (
      <div className="page" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: "var(--text-2)", fontSize: 13 }}>Loading overview…</div>
      </div>
    );
  }

  const { greeting, formatted_date, habits, todos, events, finance, date } = data || {
    greeting: "Welcome",
    formatted_date: "",
    habits: { items: [], completed: 0, total: 0, rate: 0 },
    todos: { items: [], total_pending: 0, due_today_count: 0, overdue_count: 0 },
    events: [],
    finance: { spent: 0, income: 0, net: 0 },
  };

  return (
    <div className="page">
      {/* Top Greeting Bar */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <div>
            <h1 className="page-title" style={{ fontSize: 24, marginBottom: 4 }}>
              {greeting}, Chida
            </h1>
            <p className="page-subtitle" style={{ marginBottom: 0 }}>
              {formatted_date}
            </p>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <Link to="/chat" className="btn btn-outline" style={{ textDecoration: "none" }}>
              Ask Assistant
            </Link>
          </div>
        </div>
      </div>

      {/* Grid of Core Widgets */}
      <div className="dashboard-grid">
        {/* 1. Habits Widget */}
        <div className="card" style={{ padding: 18, display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 600, fontSize: 12, textTransform: "uppercase", letterSpacing: ".03em", color: "var(--text-1)" }}>
              <Flame size={14} color="var(--amber)" /> Habits Today
            </div>
            <Link to="/habits" style={{ color: "var(--text-2)", display: "flex", alignItems: "center", gap: 4, fontSize: 12, textDecoration: "none" }}>
              {habits.completed}/{habits.total} <ArrowRight size={12} />
            </Link>
          </div>

          <div style={{ height: 4, background: "var(--bg-3)", borderRadius: 2, marginBottom: 16, overflow: "hidden" }}>
            <div
              style={{
                height: 4,
                width: `${habits.rate}%`,
                background: "var(--amber)",
                borderRadius: 2,
                transition: "width .3s ease",
              }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
            {habits.items.length > 0 ? (
              habits.items.slice(0, 5).map((h) => (
                <div
                  key={h.id}
                  onClick={() => toggleHabit(h.id, h.completed)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "8px 10px",
                    borderRadius: 6,
                    background: "var(--bg-0)",
                    border: "1px solid var(--border)",
                    cursor: "pointer",
                    transition: "all .15s",
                  }}
                >
                  <div
                    style={{
                      width: 16,
                      height: 16,
                      borderRadius: 4,
                      border: h.completed ? "1px solid var(--amber)" : "1px solid var(--border-active)",
                      background: h.completed ? "var(--amber)" : "transparent",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 10,
                      color: "#111",
                      fontWeight: 700,
                    }}
                  >
                    {h.completed ? "✓" : ""}
                  </div>
                  <span
                    style={{
                      fontSize: 13,
                      color: h.completed ? "var(--text-2)" : "var(--text-0)",
                      textDecoration: h.completed ? "line-through" : "none",
                    }}
                  >
                    {h.name}
                  </span>
                </div>
              ))
            ) : (
              <div style={{ color: "var(--text-2)", fontSize: 12, padding: "16px 0", textAlign: "center" }}>
                No habits configured. <Link to="/habits" style={{ color: "var(--accent)" }}>Add one</Link>
              </div>
            )}
          </div>
        </div>

        {/* 2. Tasks / Todos Widget */}
        <div className="card" style={{ padding: 18, display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 600, fontSize: 12, textTransform: "uppercase", letterSpacing: ".03em", color: "var(--text-1)" }}>
              <CheckSquare size={14} color="var(--accent)" /> Priority Tasks
            </div>
            <Link to="/todos" style={{ color: "var(--text-2)", display: "flex", alignItems: "center", gap: 4, fontSize: 12, textDecoration: "none" }}>
              {todos.total_pending} pending <ArrowRight size={12} />
            </Link>
          </div>

          {todos.overdue_count > 0 && (
            <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 10px", borderRadius: 6, background: "rgba(239,68,68,.08)", color: "var(--red)", fontSize: 12, marginBottom: 12 }}>
              <AlertCircle size={13} /> {todos.overdue_count} overdue task{todos.overdue_count !== 1 ? "s" : ""}
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
            {todos.items.length > 0 ? (
              todos.items.slice(0, 5).map((t, idx) => {
                const isOverdue = t.due_date && t.due_date < date;
                const isToday = t.due_date === date;
                return (
                  <div
                    key={idx}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 8,
                      padding: "8px 10px",
                      borderRadius: 6,
                      background: "var(--bg-0)",
                      border: "1px solid var(--border)",
                      borderLeft: `3px solid ${
                        t.priority === "high" ? "var(--red)" : t.priority === "medium" ? "var(--amber)" : "var(--accent)"
                      }`,
                    }}
                  >
                    <div style={{ display: "flex", flexDirection: "column", overflow: "hidden", gap: 2 }}>
                      <span style={{ fontSize: 13, color: "var(--text-0)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {t.task}
                      </span>
                      {t.due_date && (
                        <span style={{ fontSize: 10, color: isOverdue ? "var(--red)" : isToday ? "var(--amber)" : "var(--text-2)" }}>
                          {isOverdue ? "Overdue" : isToday ? "Due Today" : t.due_date}
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => completeTodo(t.task)}
                      className="btn btn-ghost"
                      style={{ padding: "3px 8px", fontSize: 11, border: "none" }}
                      title="Mark as done"
                    >
                      Done
                    </button>
                  </div>
                );
              })
            ) : (
              <div style={{ color: "var(--text-2)", fontSize: 12, padding: "16px 0", textAlign: "center" }}>
                All clear! No pending tasks.
              </div>
            )}
          </div>
        </div>

        {/* 3. Upcoming Schedule Widget */}
        <div className="card" style={{ padding: 18, display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 600, fontSize: 12, textTransform: "uppercase", letterSpacing: ".03em", color: "var(--text-1)" }}>
              <CalIcon size={14} color="var(--purple)" /> Upcoming Schedule
            </div>
            <Link to="/calendar" style={{ color: "var(--text-2)", display: "flex", alignItems: "center", gap: 4, fontSize: 12, textDecoration: "none" }}>
              Calendar <ArrowRight size={12} />
            </Link>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1 }}>
            {events.length > 0 ? (
              events.map((evt) => (
                <div
                  key={evt.id}
                  style={{
                    padding: "10px 12px",
                    borderRadius: 6,
                    background: "var(--bg-0)",
                    border: "1px solid var(--border)",
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-0)" }}>{evt.title}</div>
                  <div style={{ fontSize: 11, color: "var(--text-2)", display: "flex", alignItems: "center", gap: 4, marginTop: 3 }}>
                    <Clock size={11} />
                    {evt.start.includes("T")
                      ? `${evt.start.split("T")[0]} at ${evt.start.split("T")[1].slice(0, 5)}`
                      : evt.start}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ color: "var(--text-2)", fontSize: 12, padding: "20px 0", textAlign: "center" }}>
                No events scheduled for upcoming days.
              </div>
            )}
          </div>
        </div>

        {/* 4. Financial Pulse Widget */}
        <div className="card" style={{ padding: 18, display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 600, fontSize: 12, textTransform: "uppercase", letterSpacing: ".03em", color: "var(--text-1)" }}>
              <BarChart3 size={14} color="var(--green)" /> Monthly Finances
            </div>
            <Link to="/finance" style={{ color: "var(--text-2)", display: "flex", alignItems: "center", gap: 4, fontSize: 12, textDecoration: "none" }}>
              Analytics <ArrowRight size={12} />
            </Link>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
            <div style={{ padding: "10px 12px", background: "var(--bg-0)", borderRadius: 6, border: "1px solid var(--border)" }}>
              <div style={{ fontSize: 11, color: "var(--text-2)", textTransform: "uppercase" }}>Spent</div>
              <div style={{ fontSize: 17, fontWeight: 700, color: "var(--red)", marginTop: 2 }}>
                ₹{(finance.spent || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
              </div>
            </div>
            <div style={{ padding: "10px 12px", background: "var(--bg-0)", borderRadius: 6, border: "1px solid var(--border)" }}>
              <div style={{ fontSize: 11, color: "var(--text-2)", textTransform: "uppercase" }}>Received</div>
              <div style={{ fontSize: 17, fontWeight: 700, color: "var(--green)", marginTop: 2 }}>
                ₹{(finance.income || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
              </div>
            </div>
          </div>

          <div style={{ padding: "9px 12px", borderRadius: 6, background: "var(--bg-0)", border: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "var(--text-1)" }}>Net Cash Flow</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: finance.net >= 0 ? "var(--green)" : "var(--red)" }}>
              {finance.net >= 0 ? "+" : ""}₹{(finance.net || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
            </span>
          </div>
        </div>

        {/* 5. Daily Check-in & Mood Widget (No emojis) */}
        <div className="card" style={{ padding: 18, gridColumn: "1 / -1" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 600, fontSize: 12, textTransform: "uppercase", letterSpacing: ".03em", color: "var(--text-1)" }}>
              <BookOpen size={14} color="var(--accent)" /> Daily Reflection & Mood
            </div>
            <Link to="/journal" style={{ color: "var(--text-2)", display: "flex", alignItems: "center", gap: 4, fontSize: 12, textDecoration: "none" }}>
              Journal <ArrowRight size={12} />
            </Link>
          </div>

          <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "var(--text-2)", marginRight: 4 }}>How was today?</span>
            {MOODS.map((m) => (
              <button
                key={m.val}
                onClick={() => setJournalMood(m.val)}
                className={journalMood === m.val ? "btn btn-primary" : "btn btn-ghost"}
                style={{ padding: "4px 10px", fontSize: 12, display: "inline-flex", alignItems: "center", gap: 6 }}
              >
                <span className="mood-dot" style={{ background: m.color }} />
                {m.label}
              </button>
            ))}
            {journalSaved && (
              <span style={{ fontSize: 12, color: "var(--green)", marginLeft: "auto" }}>
                Saved to Journal
              </span>
            )}
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <textarea
              className="input"
              rows={2}
              placeholder="Jot down a quick thought, highlight, or observation from today…"
              value={journalText}
              onChange={(e) => setJournalText(e.target.value)}
              style={{ flex: 1, minHeight: 56, minWidth: 200 }}
            />
            <button className="btn btn-primary" onClick={saveJournal} style={{ alignSelf: "flex-end" }}>
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
