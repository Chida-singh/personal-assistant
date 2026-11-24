import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ..core.database import get_session
from ..core.models import Habit, HabitLog

router = APIRouter(prefix="/api/habits", tags=["habits"])


class HabitCreate(BaseModel):
    name: str
    type: str = "checkbox"


class HabitReorder(BaseModel):
    ordered_ids: list[str]


class HabitLogCreate(BaseModel):
    date: str
    habit_id: str
    value: object


@router.get("")
def get_habits(session: Session = Depends(get_session)):
    habits = session.exec(select(Habit).order_by(Habit.order)).all()
    return [{"id": h.id, "name": h.name, "type": h.type, "order": h.order} for h in habits]


@router.post("")
def add_habit(body: HabitCreate, session: Session = Depends(get_session)):
    count = len(session.exec(select(Habit)).all())
    habit = Habit(name=body.name, type=body.type, order=count)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return {"id": habit.id, "name": habit.name, "type": habit.type, "order": habit.order}


@router.delete("/{habit_id}")
def delete_habit(habit_id: str, session: Session = Depends(get_session)):
    habit = session.exec(select(Habit).where(Habit.id == habit_id)).first()
    if not habit:
        raise HTTPException(404, "Habit not found")
    logs = session.exec(select(HabitLog).where(HabitLog.habit_id == habit_id)).all()
    for l in logs:
        session.delete(l)
    session.delete(habit)
    session.commit()
    return {"message": "Deleted"}


@router.put("/reorder")
def reorder_habits(body: HabitReorder, session: Session = Depends(get_session)):
    habits = session.exec(select(Habit)).all()
    habits_by_id = {h.id: h for h in habits}
    reordered = []
    for i, hid in enumerate(body.ordered_ids):
        if hid in habits_by_id:
            h = habits_by_id[hid]
            h.order = i
            session.add(h)
            reordered.append(h)
    session.commit()
    return [{"id": h.id, "name": h.name, "type": h.type, "order": h.order} for h in reordered]


@router.get("/today")
def get_today_habits(session: Session = Depends(get_session)):
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    habits = session.exec(select(Habit).order_by(Habit.order)).all()
    logs = session.exec(select(HabitLog).where(HabitLog.date == today)).all()
    log_map = {l.habit_id: json.loads(l.value) if l.value is not None else None for l in logs}

    result = []
    completed_count = 0
    total_checkbox = 0
    for h in habits:
        val = log_map.get(h.id, False if h.type == "checkbox" else None)
        if h.type == "checkbox":
            total_checkbox += 1
            if val is True:
                completed_count += 1
        result.append({
            "id": h.id,
            "name": h.name,
            "type": h.type,
            "order": h.order,
            "value": val,
            "completed": val is True if h.type == "checkbox" else (val is not None and val > 0),
        })

    completion_rate = round((completed_count / total_checkbox) * 100) if total_checkbox > 0 else 0
    return {
        "date": today,
        "habits": result,
        "completed_count": completed_count,
        "total_count": total_checkbox,
        "completion_rate": completion_rate,
    }


@router.get("/logs")
def get_month_logs(year: int, month: int, session: Session = Depends(get_session)):
    prefix = f"{year}-{month:02d}"
    logs = session.exec(select(HabitLog).where(HabitLog.date.startswith(prefix))).all()
    return [
        {
            "date": l.date,
            "habit_id": l.habit_id,
            "value": json.loads(l.value) if l.value is not None else None,
        }
        for l in logs
    ]


@router.post("/logs")
def set_log(body: HabitLogCreate, session: Session = Depends(get_session)):
    val_json = json.dumps(body.value)
    existing = session.exec(
        select(HabitLog).where(HabitLog.date == body.date, HabitLog.habit_id == body.habit_id)
    ).first()
    if existing:
        existing.value = val_json
        session.add(existing)
    else:
        new_log = HabitLog(date=body.date, habit_id=body.habit_id, value=val_json)
        session.add(new_log)
    session.commit()
    return {"date": body.date, "habit_id": body.habit_id, "value": body.value}


@router.delete("/logs/{date}/{habit_id}")
def clear_log(date: str, habit_id: str, session: Session = Depends(get_session)):
    existing = session.exec(
        select(HabitLog).where(HabitLog.date == date, HabitLog.habit_id == habit_id)
    ).first()
    if existing:
        session.delete(existing)
        session.commit()
    return {"message": "Cleared"}
