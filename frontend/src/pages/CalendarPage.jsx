import { useState, useEffect } from "react";
import { apiGet, apiPost, apiDelete, apiPut } from "../api";
import { ChevronLeft, ChevronRight, RefreshCw, Calendar as CalIcon } from "lucide-react";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function CalendarPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [events, setEvents] = useState([]);
  const [selected, setSelected] = useState(null);
  const [dayEvents, setDayEvents] = useState("");
  const [form, setForm] = useState({ id: "", title: "", date: "", time: "", endTime: "" });
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    loadMonth();
  }, [year, month]);

  const loadMonth = async () => {
    try {
      const data = await apiGet(`/api/calendar/month?year=${year}&month=${month}`);
      setEvents(data.events || []);
    } catch (err) {
      setEvents([]);
      setDayEvents(`Error loading calendar: ${err.message}`);
    }
  };

  const prev = () => {
    if (month === 1) { setMonth(12); setYear(year - 1); }
    else setMonth(month - 1);
  };

  const next = () => {
    if (month === 12) { setMonth(1); setYear(year + 1); }
    else setMonth(month + 1);
  };

  const goToday = () => {
    setYear(now.getFullYear());
    setMonth(now.getMonth() + 1);
  };

  const firstDay = (new Date(year, month - 1, 1).getDay() + 6) % 7;
  const daysInMonth = new Date(year, month, 0).getDate();
  const today = new Date();
  const isToday = (d) =>
    d === today.getDate() &&
    month === today.getMonth() + 1 &&
    year === today.getFullYear();

  const eventsOnDay = (d) => {
    const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    return events.filter((e) => {
      const start = e.start?.dateTime || e.start?.date || "";
      return start.startsWith(dateStr);
    });
  };

  const handleDayClick = (d) => {
    setSelected(d);
    const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    setForm({ id: "", title: "", date: dateStr, time: "10:00", endTime: "11:00" });
    setModalOpen(true);
  };

  const handleEventClick = (e, evt) => {
    e.stopPropagation();
    let startDT = evt.start?.dateTime || evt.start?.date || "";
    let endDT = evt.end?.dateTime || evt.end?.date || "";
    
    let date = startDT.split("T")[0] || startDT;
    let time = startDT.includes("T") ? startDT.split("T")[1].substring(0, 5) : "10:00";
    let endTime = endDT.includes("T") ? endDT.split("T")[1].substring(0, 5) : "11:00";

    setForm({ id: evt.id, title: evt.summary || "Untitled", date, time, endTime });
    setModalOpen(true);
  };

  const saveEvent = async () => {
    if (!form.title.trim()) return;
    const startIso = `${form.date}T${form.time}:00`;
    const endIso = `${form.date}T${form.endTime}:00`;

    try {
      if (form.id) {
        await apiPut(`/api/calendar/update/${form.id}`, { title: form.title, start_datetime: startIso, end_datetime: endIso });
      } else {
        await apiPost("/api/calendar/create", { title: form.title, datetime: startIso, end_datetime: endIso });
      }
      setModalOpen(false);
      loadMonth();
    } catch (err) {
      alert("Failed to save event");
    }
  };

  const deleteEvent = async () => {
    if (!form.id) return;
    try {
      await apiDelete(`/api/calendar/delete/${form.id}`);
      setModalOpen(false);
      loadMonth();
    } catch (err) {
      alert("Failed to delete event");
    }
  };

  const cells = [];
  for (let i = 0; i < firstDay; i++) {
    cells.push(<div key={`e-${i}`} className="calendar-day empty" />);
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const dayEvts = eventsOnDay(d);
    cells.push(
      <div
        key={d}
        className={`calendar-day${isToday(d) ? " today" : ""}${selected === d ? " selected" : ""}`}
        onClick={() => handleDayClick(d)}
      >
        <span className="calendar-day-number">{d}</span>
        {dayEvts.map((e, idx) => (
          <div key={idx} className="calendar-event-item" onClick={(ev) => handleEventClick(ev, e)}>
            {e.summary}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="page" style={{ display: "flex", flexDirection: "column" }}>
      <div>
        <h1 className="page-title">Calendar</h1>
        <p className="page-subtitle">Google Calendar integration</p>
      </div>

      <div className="calendar-header">
        <div className="calendar-nav">
          <button className="calendar-nav-btn" onClick={prev}>
            <ChevronLeft size={16} />
          </button>
          <span className="calendar-month-label">
            {MONTHS[month - 1]} {year}
          </span>
          <button className="calendar-nav-btn" onClick={next}>
            <ChevronRight size={16} />
          </button>
          <button className="btn btn-ghost" style={{ marginLeft: 10, padding: 6 }} onClick={goToday} title="Today">
            <CalIcon size={14} />
          </button>
          <button className="btn btn-ghost" style={{ padding: 6 }} onClick={loadMonth} title="Refresh Events">
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      <div className="calendar-header-row">
        {DAYS.map((d) => (
          <div key={d} className="calendar-day-header">{d}</div>
        ))}
      </div>
      <div className="calendar-grid">
        {cells}
      </div>

      {dayEvents && (
        <div
          className="card fade-in"
          style={{ marginTop: 20, whiteSpace: "pre-wrap", flexShrink: 0 }}
        >
          {dayEvents}
        </div>
      )}

      {modalOpen && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
          <div className="card fade-in" style={{ width: 400, maxWidth: "90%" }}>
            <h3 style={{ marginTop: 0, marginBottom: 15 }}>{form.id ? "Edit Event" : "New Event"}</h3>
            <input className="input" placeholder="Event Title" value={form.title} onChange={e => setForm({...form, title: e.target.value})} style={{ marginBottom: 10 }} />
            <input className="input" type="date" value={form.date} onChange={e => setForm({...form, date: e.target.value})} style={{ marginBottom: 10 }} />
            <div style={{ display: "flex", gap: 10, marginBottom: 15 }}>
              <input className="input" type="time" value={form.time} onChange={e => setForm({...form, time: e.target.value})} />
              <input className="input" type="time" value={form.endTime} onChange={e => setForm({...form, endTime: e.target.value})} />
            </div>
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              {form.id && <button className="btn btn-ghost" style={{ color: "var(--accent-red)", borderColor: "var(--accent-red)" }} onClick={deleteEvent}>Delete</button>}
              <div style={{ flex: 1 }} />
              <button className="btn btn-ghost" onClick={() => setModalOpen(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={saveEvent}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
