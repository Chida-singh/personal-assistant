"""Todo & Notes Repository — Database operations."""

import json
from fastapi import HTTPException
from sqlmodel import Session, select

from models import Habit, HabitLog, Note, Todo



# ── Internal Helpers ──────────────────────────────────────────────────────────

def _get_todo_or_404(task: str, session: Session) -> Todo:
    db_todo = session.exec(select(Todo).where(Todo.task == task)).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo


def _get_note_or_404(key: str, session: Session) -> Note:
    note = session.exec(select(Note).where(Note.key == key)).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


# ── Todo Operations ───────────────────────────────────────────────────────────

def get_all_todos(session: Session) -> list[dict]:
    todos = session.exec(select(Todo)).all()
    return [{"task": t.task, "done": t.done, "priority": t.priority} for t in todos]


def create_todo(task: str, priority: str, session: Session) -> None:
    session.add(Todo(task=task, priority=priority, done=False))
    session.commit()


def complete_todo(task: str, session: Session) -> None:
    db_todo = _get_todo_or_404(task, session)
    db_todo.done = True
    session.add(db_todo)
    session.commit()


def move_todo(task: str, target_key: str, session: Session) -> None:
    db_todo = _get_todo_or_404(task, session)
    if target_key == "done":
        db_todo.done = True
    else:
        db_todo.done = False
        db_todo.priority = target_key
    session.add(db_todo)
    session.commit()


def delete_all_todos(session: Session) -> None:
    for t in session.exec(select(Todo)).all():
        session.delete(t)
    session.commit()


def delete_done_todos(session: Session) -> None:
    for t in session.exec(select(Todo).where(Todo.done == True)).all():
        session.delete(t)
    session.commit()


def delete_todo(task: str, session: Session) -> None:
    session.delete(_get_todo_or_404(task, session))
    session.commit()


# ── Note Operations ───────────────────────────────────────────────────────────

def get_all_notes(session: Session) -> list[dict]:
    notes = session.exec(select(Note)).all()
    return [{"key": n.key, "value": n.value} for n in notes]


def upsert_note(key: str, value: str, session: Session) -> str:
    existing = session.exec(select(Note).where(Note.key == key)).first()
    if existing:
        existing.value = value
        session.add(existing)
        session.commit()
        return "Updated"
    session.add(Note(key=key, value=value))
    session.commit()
    return "Added"


def recall_note(key: str, session: Session) -> dict:
    note = _get_note_or_404(key, session)
    return {"key": note.key, "value": note.value}


def delete_note(key: str, session: Session) -> None:
    session.delete(_get_note_or_404(key, session))
    session.commit()


# ── Habits Operations ─────────────────────────────────────────────────────────

def get_all_habits(session: Session) -> list[dict]:
    habits = session.exec(select(Habit).order_by(Habit.order)).all()
    return [{"id": h.id, "name": h.name, "type": h.type, "order": h.order} for h in habits]


def create_habit(name: str, habit_type: str, session: Session) -> dict:
    count = len(session.exec(select(Habit)).all())
    habit = Habit(name=name, type=habit_type, order=count)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return {"id": habit.id, "name": habit.name, "type": habit.type, "order": habit.order}


def delete_habit(habit_id: str, session: Session) -> bool:
    habit = session.exec(select(Habit).where(Habit.id == habit_id)).first()
    if not habit:
        return False
    logs = session.exec(select(HabitLog).where(HabitLog.habit_id == habit_id)).all()
    for l in logs:
        session.delete(l)
    session.delete(habit)
    session.commit()
    return True


def reorder_habits(ordered_ids: list[str], session: Session) -> list[dict]:
    habits = session.exec(select(Habit)).all()
    habits_by_id = {h.id: h for h in habits}
    reordered = []
    for i, hid in enumerate(ordered_ids):
        if hid in habits_by_id:
            h = habits_by_id[hid]
            h.order = i
            session.add(h)
            reordered.append(h)
    session.commit()
    return [{"id": h.id, "name": h.name, "type": h.type, "order": h.order} for h in reordered]


def get_month_logs(year: int, month: int, session: Session) -> list[dict]:
    prefix = f"{year}-{month:02d}"
    statement = select(HabitLog).where(HabitLog.date.startswith(prefix))
    logs = session.exec(statement).all()
    return [
        {
            "date": l.date,
            "habit_id": l.habit_id,
            "value": json.loads(l.value) if l.value is not None else None,
        }
        for l in logs
    ]


def set_habit_log(date_str: str, habit_id: str, value: object, session: Session) -> dict:
    val_json = json.dumps(value)
    existing = session.exec(
        select(HabitLog).where(HabitLog.date == date_str, HabitLog.habit_id == habit_id)
    ).first()
    if existing:
        existing.value = val_json
        session.add(existing)
        session.commit()
    else:
        new_log = HabitLog(date=date_str, habit_id=habit_id, value=val_json)
        session.add(new_log)
        session.commit()
    return {"date": date_str, "habit_id": habit_id, "value": value}


def clear_habit_log(date_str: str, habit_id: str, session: Session) -> bool:
    existing = session.exec(
        select(HabitLog).where(HabitLog.date == date_str, HabitLog.habit_id == habit_id)
    ).first()
    if existing:
        session.delete(existing)
        session.commit()
        return True
    return False

