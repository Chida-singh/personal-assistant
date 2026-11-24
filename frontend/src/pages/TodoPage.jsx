import { useState, useEffect } from "react";
import { apiGet, apiPost, apiPut, apiDelete } from "../api";
import { Plus, Trash2, Calendar, Tag } from "lucide-react";

const COLUMNS = [
  { id: "high", title: "High", colorClass: "high" },
  { id: "medium", title: "Medium", colorClass: "medium" },
  { id: "low", title: "Low", colorClass: "low" },
  { id: "done", title: "Done", colorClass: "done" },
];

export default function TodoPage() {
  const todayStr = new Date().toISOString().slice(0, 10);
  const [todos, setTodos] = useState([]);
  const [task, setTask] = useState("");
  const [priority, setPriority] = useState("medium");
  const [dueDate, setDueDate] = useState("");
  const [tags, setTags] = useState("");
  const [draggedTask, setDraggedTask] = useState(null);
  const [selectedTag, setSelectedTag] = useState("all");

  const load = async () => {
    try {
      const data = await apiGet("/api/todos");
      setTodos(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const add = async () => {
    if (!task.trim()) return;
    const newTask = task.trim();
    const newPriority = priority;
    const newDueDate = dueDate || null;
    const newTags = tags.trim();

    setTask("");
    setDueDate("");
    setTags("");

    setTodos((prev) => [
      ...prev,
      { task: newTask, done: false, priority: newPriority, due_date: newDueDate, tags: newTags },
    ]);
    await apiPost("/api/todos", { task: newTask, priority: newPriority, due_date: newDueDate, tags: newTags });
  };

  const del = async (t) => {
    setTodos((prev) => prev.filter((x) => x.task !== t));
    await apiDelete(`/api/todos/${encodeURIComponent(t)}`);
  };

  const handleKey = (e) => {
    if (e.key === "Enter") add();
  };

  const handleDragStart = (e, taskObj) => {
    setDraggedTask(taskObj);
    e.dataTransfer.effectAllowed = "move";
  };
  const handleDragOver = (e) => e.preventDefault();
  const handleDrop = async (e, colId) => {
    e.preventDefault();
    if (!draggedTask) return;
    const oldTask = draggedTask;
    setDraggedTask(null);
    if ((oldTask.done && colId === "done") || (!oldTask.done && oldTask.priority === colId)) return;
    setTodos((prev) =>
      prev.map((t) => {
        if (t.task === oldTask.task) {
          if (colId === "done") return { ...t, done: true };
          return { ...t, done: false, priority: colId };
        }
        return t;
      })
    );
    await apiPut("/api/todos/move", { task: oldTask.task, target_key: colId });
  };

  const clearDone = async () => {
    setTodos((prev) => prev.filter((t) => !t.done));
    await apiDelete("/api/todos/done");
  };
  const clearAll = async () => {
    setTodos([]);
    await apiDelete("/api/todos/all");
  };

  // Extract all unique tags
  const allTags = Array.from(
    new Set(
      todos
        .flatMap((t) => (t.tags ? t.tags.split(",").map((x) => x.trim()) : []))
        .filter(Boolean)
    )
  );

  const filteredTodos = todos.filter((t) => {
    if (selectedTag === "all") return true;
    return t.tags && t.tags.split(",").map((x) => x.trim()).includes(selectedTag);
  });

  return (
    <div className="page" style={{ display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 10 }}>
        <div>
          <h1 className="page-title">Tasks</h1>
          <p className="page-subtitle" style={{ marginBottom: 0 }}>Organize and prioritize your deliverables</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-ghost" onClick={clearDone} style={{ fontSize: 12 }}>Clear done</button>
          <button className="btn btn-ghost" onClick={clearAll} style={{ fontSize: 12 }}>Delete all</button>
        </div>
      </div>

      {/* Creation row with due date and tags */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 20, flexShrink: 0 }}>
        <div className="todo-add-row" style={{ marginBottom: 0 }}>
          <input
            className="input"
            placeholder="What needs to be done?"
            value={task}
            onChange={(e) => setTask(e.target.value)}
            onKeyDown={handleKey}
          />
          <select className="input" value={priority} onChange={(e) => setPriority(e.target.value)} style={{ width: 110 }}>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <input
            type="date"
            className="input"
            title="Due date (optional)"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            style={{ width: 140 }}
          />
          <input
            className="input"
            placeholder="Tags (e.g. work, dev)"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            onKeyDown={handleKey}
            style={{ width: 160 }}
          />
          <button className="btn btn-primary" onClick={add}>
            <Plus size={14} /> Add
          </button>
        </div>

        {/* Tag filter pills */}
        {allTags.length > 0 && (
          <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
            <span style={{ fontSize: 11, color: "var(--text-2)" }}>Filter:</span>
            <button
              onClick={() => setSelectedTag("all")}
              className={selectedTag === "all" ? "btn btn-primary" : "btn btn-ghost"}
              style={{ padding: "2px 8px", fontSize: 11 }}
            >
              All
            </button>
            {allTags.map((tag) => (
              <button
                key={tag}
                onClick={() => setSelectedTag(tag)}
                className={selectedTag === tag ? "btn btn-primary" : "btn btn-ghost"}
                style={{ padding: "2px 8px", fontSize: 11 }}
              >
                #{tag}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="kanban-board">
        {COLUMNS.map((col) => {
          const colTasks = filteredTodos.filter((t) => {
            if (col.id === "done") return t.done;
            return !t.done && t.priority === col.id;
          });
          return (
            <div
              key={col.id}
              className={`kanban-col ${col.colorClass}`}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, col.id)}
            >
              <div className="kanban-col-header">
                <div className="kanban-col-title">{col.title}</div>
                <div className="kanban-badge">{colTasks.length}</div>
              </div>
              <div className="kanban-cards">
                {colTasks.map((t, i) => {
                  const isOverdue = t.due_date && t.due_date < todayStr && !t.done;
                  const isToday = t.due_date === todayStr && !t.done;
                  const tagList = t.tags ? t.tags.split(",").map((x) => x.trim()).filter(Boolean) : [];

                  return (
                    <div
                      key={`${col.id}-${t.task}-${i}`}
                      className={`kanban-card ${col.id === "done" ? "done-card done" : col.colorClass} fade-in`}
                      draggable
                      onDragStart={(e) => handleDragStart(e, t)}
                    >
                      <div style={{ flex: 1, marginRight: 6 }}>
                        <div className="kanban-card-text">{t.task}</div>
                        <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap", marginTop: 4 }}>
                          {t.due_date && (
                            <span
                              style={{
                                fontSize: 10,
                                fontWeight: 500,
                                padding: "1px 5px",
                                borderRadius: 3,
                                background: isOverdue ? "rgba(239,68,68,.15)" : isToday ? "rgba(245,158,11,.15)" : "var(--bg-3)",
                                color: isOverdue ? "var(--red)" : isToday ? "var(--amber)" : "var(--text-2)",
                              }}
                            >
                              {isOverdue ? "Overdue" : isToday ? "Due Today" : t.due_date}
                            </span>
                          )}
                          {tagList.map((tg, idx) => (
                            <span key={idx} style={{ fontSize: 10, color: "var(--text-2)" }}>
                              #{tg}
                            </span>
                          ))}
                        </div>
                      </div>
                      <button className="kanban-card-del" onClick={() => del(t.task)}>
                        <Trash2 size={13} />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
