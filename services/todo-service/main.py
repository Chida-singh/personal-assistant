"""Todo & Notes Service — FastAPI routes.

Delegates all database operations to repository.py following SOLID principles.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlmodel import Session

import repository
from database import create_db_and_tables, get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Todo & Notes Service", lifespan=lifespan)


# ── Request schemas ───────────────────────────────────────────────────────────

class TodoCreate(BaseModel):
    task: str
    priority: str = "medium"

class TodoUpdate(BaseModel):
    task: str

class TodoMove(BaseModel):
    task: str
    target_key: str

class NoteCreate(BaseModel):
    key: str
    value: str

class NoteRecall(BaseModel):
    key: str

class HabitCreate(BaseModel):
    name: str
    type: str = "checkbox"

class HabitReorder(BaseModel):
    ordered_ids: list[str]

class HabitLog(BaseModel):
    date: str
    habit_id: str
    value: object



# ── Todo routes ───────────────────────────────────────────────────────────────

@app.get("/api/todos")
def read_todos(session: Session = Depends(get_session)):
    return repository.get_all_todos(session)


@app.post("/api/todos")
def add_todo(todo: TodoCreate, session: Session = Depends(get_session)):
    repository.create_todo(todo.task, todo.priority, session)
    return {"message": "Added"}


@app.put("/api/todos/complete")
def complete_todo(body: TodoUpdate, session: Session = Depends(get_session)):
    repository.complete_todo(body.task, session)
    return {"message": "Completed"}


@app.put("/api/todos/move")
def move_todo(move: TodoMove, session: Session = Depends(get_session)):
    repository.move_todo(move.task, move.target_key, session)
    return {"message": "Moved"}


@app.delete("/api/todos/all")
def delete_all_todos(session: Session = Depends(get_session)):
    repository.delete_all_todos(session)
    return {"message": "All deleted"}


@app.delete("/api/todos/done")
def delete_done_todos(session: Session = Depends(get_session)):
    repository.delete_done_todos(session)
    return {"message": "Done deleted"}


@app.delete("/api/todos/{task}")
def delete_todo(task: str, session: Session = Depends(get_session)):
    repository.delete_todo(task, session)
    return {"message": "Deleted"}


# ── Notes routes ──────────────────────────────────────────────────────────────

@app.get("/api/notes")
def read_notes(session: Session = Depends(get_session)):
    return repository.get_all_notes(session)


@app.post("/api/notes")
def upsert_note(note: NoteCreate, session: Session = Depends(get_session)):
    msg = repository.upsert_note(note.key, note.value, session)
    return {"message": msg}


@app.post("/api/notes/recall")
def recall_note(recall: NoteRecall, session: Session = Depends(get_session)):
    return repository.recall_note(recall.key, session)


@app.delete("/api/notes/{key}")
def delete_note(key: str, session: Session = Depends(get_session)):
    repository.delete_note(key, session)
    return {"message": "Deleted"}


# ── Habits routes ─────────────────────────────────────────────────────────────

@app.get("/api/habits")
def get_habits(session: Session = Depends(get_session)):
    return repository.get_all_habits(session)


@app.post("/api/habits")
def add_habit(body: HabitCreate, session: Session = Depends(get_session)):
    return repository.create_habit(body.name, body.type, session)


@app.delete("/api/habits/{habit_id}")
def delete_habit(habit_id: str, session: Session = Depends(get_session)):
    if not repository.delete_habit(habit_id, session):
        raise HTTPException(404, "Habit not found")
    return {"message": "Deleted"}


@app.put("/api/habits/reorder")
def reorder_habits(body: HabitReorder, session: Session = Depends(get_session)):
    return repository.reorder_habits(body.ordered_ids, session)


@app.get("/api/habits/logs")
def get_month_logs(year: int, month: int, session: Session = Depends(get_session)):
    return repository.get_month_logs(year, month, session)


@app.post("/api/habits/logs")
def set_log(body: HabitLog, session: Session = Depends(get_session)):
    return repository.set_habit_log(body.date, body.habit_id, body.value, session)


@app.delete("/api/habits/logs/{date}/{habit_id}")
def clear_log(date: str, habit_id: str, session: Session = Depends(get_session)):
    repository.clear_habit_log(date, habit_id, session)
    return {"message": "Cleared"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "todo-service"}
