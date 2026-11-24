import json
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from ..core.database import get_session
from ..core.llm import call_llm
from ..core.models import Event, Habit, HabitLog, Note, Todo

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


def _route_intent(raw_output: str, session: Session) -> str:
    clean = re.sub(r"```(?:json)?\s*", "", raw_output, flags=re.IGNORECASE).replace("```", "").strip()
    try:
        payload = json.loads(clean)
    except Exception:
        return clean or raw_output

    intent = payload.get("intent")
    params = payload.get("parameters", {})

    if intent == "general_chat":
        return str(params.get("message", "How can I help you today?"))

    elif intent == "add_todo":
        task = str(params.get("task", ""))
        priority = str(params.get("priority", "medium")).lower()
        session.add(Todo(task=task, priority=priority, done=False))
        session.commit()
        return f"Added '{task}' to your tasks."

    elif intent == "complete_todo":
        task = str(params.get("task", ""))
        todo = session.exec(select(Todo).where(Todo.task == task)).first()
        if todo:
            todo.done = True
            session.add(todo)
            session.commit()
            return f"Marked '{task}' as completed."
        return f"Could not find task '{task}'."

    elif intent == "delete_todo":
        task = str(params.get("task", ""))
        todo = session.exec(select(Todo).where(Todo.task == task)).first()
        if todo:
            session.delete(todo)
            session.commit()
            return f"Deleted task '{task}'."
        return f"Could not find task '{task}'."

    elif intent == "remember":
        key = str(params.get("key", ""))
        value = str(params.get("value", ""))
        existing = session.exec(select(Note).where(Note.key == key)).first()
        if existing:
            existing.value = value
            session.add(existing)
        else:
            session.add(Note(key=key, value=value))
        session.commit()
        return f"Remembered: {key} = {value}"

    elif intent == "recall":
        key = str(params.get("key", ""))
        note = session.exec(select(Note).where(Note.key == key)).first()
        if note:
            return f"{key}: {note.value}"
        return f"I don't have any note saved for '{key}'."

    elif intent == "track_habit":
        name = str(params.get("name", ""))
        habit = session.exec(select(Habit).where(Habit.name == name)).first()
        if not habit:
            habit = Habit(name=name, type="checkbox")
            session.add(habit)
            session.commit()
            session.refresh(habit)
        from datetime import date
        today_str = date.today().isoformat()
        session.add(HabitLog(date=today_str, habit_id=habit.id, value=json.dumps(True)))
        session.commit()
        return f"Logged habit '{name}' as completed for today!"

    elif intent == "check_calendar":
        target_date = str(params.get("date", ""))
        events = session.exec(select(Event).where(Event.start_datetime.startswith(target_date))).all()
        if not events:
            return f"No events scheduled on {target_date}."
        lines = [f"Events on {target_date}:"]
        for ev in events:
            lines.append(f"  - {ev.title} at {ev.start_datetime}")
        return "\n".join(lines)

    elif intent == "create_event":
        title = str(params.get("title", ""))
        dt_str = str(params.get("datetime", ""))
        end_dt = params.get("end_datetime")
        ev = Event(title=title, start_datetime=dt_str, end_datetime=end_dt)
        session.add(ev)
        session.commit()
        return f"Created event '{title}' on {dt_str}."

    return clean or "I processed your request."


@router.post("")
def chat(req: ChatRequest, session: Session = Depends(get_session)):
    try:
        raw = call_llm(req.message, req.history)
        response = _route_intent(raw, session)
        return {"response": response, "raw_intent": raw}
    except Exception as exc:
        raise HTTPException(500, str(exc))


@router.post("/stream")
def chat_stream(req: ChatRequest, session: Session = Depends(get_session)):
    def generate():
        try:
            raw = call_llm(req.message, req.history)
            response = _route_intent(raw, session)
            yield f"data: {json.dumps({'done': True, 'response': response, 'raw': raw})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
