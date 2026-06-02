import { useState, useEffect } from "react";
import { apiGet, apiPost, apiPut, apiDelete } from "../api";
import { Plus, Trash2 } from "lucide-react";

const COLUMNS = [
  { id: "high", title: "High", colorClass: "high" },
  { id: "medium", title: "Medium", colorClass: "medium" },
  { id: "low", title: "Low", colorClass: "low" },
  { id: "done", title: "Done", colorClass: "done" },
];

export default function TodoPage() {
  const [todos, setTodos] = useState([]);
  const [task, setTask] = useState("");
  const [priority, setPriority] = useState("medium");
  const [draggedTask, setDraggedTask] = useState(null);

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
    setTask("");
    setTodos(prev => [...prev, { task: newTask, done: false, priority: newPriority }]);
    await apiPost("/api/todos", { task: newTask, priority: newPriority });
  };

  const del = async (t) => {
    setTodos(prev => prev.filter(x => x.task !== t));
    await apiDelete(`/api/todos/${encodeURIComponent(t)}`);
  };

  const handleKey = (e) => {
    if (e.key === "Enter") add();
  };

  const handleDragStart = (e, taskObj) => {
    setDraggedTask(taskObj);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = async (e, colId) => {
    e.preventDefault();
    if (!draggedTask) return;

    const oldTask = draggedTask;
    setDraggedTask(null);

    if ((oldTask.done && colId === "done") || (!oldTask.done && oldTask.priority === colId)) {
      return; // no change
    }

    setTodos(prev => prev.map(t => {
      if (t.task === oldTask.task) {
        if (colId === "done") return { ...t, done: true };
        return { ...t, done: false, priority: colId };
      }
      return t;
    }));

    await apiPut("/api/todos/move", { task: oldTask.task, target_key: colId });
  };

  const clearDone = async () => {
    setTodos(prev => prev.filter(t => !t.done));
    await apiDelete("/api/todos/done");
  };

  const clearAll = async () => {
    setTodos([]);
    await apiDelete("/api/todos/all");
  };

  return (
    <div className="page" style={{ display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <h1 className="page-title">Tasks</h1>
          <p className="page-subtitle" style={{ marginBottom: 0 }}>Manage your to-do list</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-ghost" onClick={clearDone} style={{ fontSize: 11, padding: "4px 10px" }}>Clear done</button>
          <button className="btn btn-ghost" onClick={clearAll} style={{ fontSize: 11, padding: "4px 10px" }}>Delete all</button>
        </div>
      </div>

      <div className="todo-add-row" style={{ flexShrink: 0 }}>
        <input
          className="input"
          placeholder="What needs to be done?"
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={handleKey}
        />
        <select
          className="input"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          style={{ width: 120 }}
        >
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <button className="btn btn-primary" onClick={add}>
          <Plus size={14} />
          Add
        </button>
      </div>

      <div className="kanban-board">
        {COLUMNS.map((col) => {
          const colTasks = todos.filter((t) => {
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
                <div className="kanban-col-title">
                  <span style={{ fontSize: 9 }}>●</span>
                  {col.title}
                </div>
                <div className="kanban-badge">{colTasks.length}</div>
              </div>
              <div className="kanban-cards">
                {colTasks.map((t, i) => (
                  <div
                    key={`${col.id}-${t.task}-${i}`}
                    className={`kanban-card ${col.id === "done" ? "done-card" : col.colorClass} fade-in`}
                    draggable
                    onDragStart={(e) => handleDragStart(e, t)}
                  >
                    <div className="kanban-card-text">{t.task}</div>
                    <button className="kanban-card-del" onClick={() => del(t.task)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
