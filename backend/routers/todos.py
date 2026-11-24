from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ..core.database import get_session
from ..core.models import Todo

router = APIRouter(prefix="/api/todos", tags=["todos"])


class TodoCreate(BaseModel):
    task: str
    priority: str = "medium"
    due_date: Optional[str] = None
    tags: Optional[str] = ""


class TodoUpdate(BaseModel):
    task: str


class TodoMove(BaseModel):
    task: str
    target_key: str


@router.get("")
def read_todos(session: Session = Depends(get_session)):
    todos = session.exec(select(Todo)).all()
    return [{"task": t.task, "done": t.done, "priority": t.priority, "due_date": t.due_date, "tags": t.tags} for t in todos]


@router.get("/due-today")
def read_due_today(session: Session = Depends(get_session)):
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    todos = session.exec(select(Todo).where(Todo.due_date == today, Todo.done == False)).all()
    return [{"task": t.task, "done": t.done, "priority": t.priority, "due_date": t.due_date, "tags": t.tags} for t in todos]


@router.get("/overdue")
def read_overdue(session: Session = Depends(get_session)):
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    todos = session.exec(
        select(Todo).where(Todo.due_date != None, Todo.due_date < today, Todo.done == False)
    ).all()
    return [{"task": t.task, "done": t.done, "priority": t.priority, "due_date": t.due_date, "tags": t.tags} for t in todos]


@router.post("")
def add_todo(todo: TodoCreate, session: Session = Depends(get_session)):
    new_todo = Todo(task=todo.task, priority=todo.priority, done=False, due_date=todo.due_date, tags=todo.tags)
    session.add(new_todo)
    session.commit()
    return {"message": "Added"}


@router.put("/complete")
def complete_todo(body: TodoUpdate, session: Session = Depends(get_session)):
    item = session.exec(select(Todo).where(Todo.task == body.task)).first()
    if not item:
        raise HTTPException(404, "Todo not found")
    item.done = True
    session.add(item)
    session.commit()
    return {"message": "Completed"}


@router.put("/move")
def move_todo(move: TodoMove, session: Session = Depends(get_session)):
    item = session.exec(select(Todo).where(Todo.task == move.task)).first()
    if not item:
        raise HTTPException(404, "Todo not found")
    if move.target_key == "done":
        item.done = True
    else:
        item.done = False
        item.priority = move.target_key
    session.add(item)
    session.commit()
    return {"message": "Moved"}


@router.delete("/all")
def delete_all_todos(session: Session = Depends(get_session)):
    for t in session.exec(select(Todo)).all():
        session.delete(t)
    session.commit()
    return {"message": "All deleted"}


@router.delete("/done")
def delete_done_todos(session: Session = Depends(get_session)):
    for t in session.exec(select(Todo).where(Todo.done == True)).all():
        session.delete(t)
    session.commit()
    return {"message": "Done deleted"}


@router.delete("/{task}")
def delete_todo(task: str, session: Session = Depends(get_session)):
    item = session.exec(select(Todo).where(Todo.task == task)).first()
    if not item:
        raise HTTPException(404, "Todo not found")
    session.delete(item)
    session.commit()
    return {"message": "Deleted"}
