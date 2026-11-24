from datetime import datetime
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, desc
import json

from ..core.database import get_session
from ..core.models import Todo, Habit, HabitLog, Event, JournalEntry
from ..finance import analytics as fin_analytics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard_summary(session: Session = Depends(get_session)):
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    hour = now.hour

    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # 1. Habits for today
    habits = session.exec(select(Habit).order_by(Habit.order)).all()
    today_logs = session.exec(select(HabitLog).where(HabitLog.date == today_str)).all()
    log_map = {l.habit_id: json.loads(l.value) if l.value is not None else None for l in today_logs}

    habits_data = []
    completed_habits = 0
    total_checkbox_habits = 0
    for h in habits:
        val = log_map.get(h.id, False if h.type == "checkbox" else None)
        is_done = val is True if h.type == "checkbox" else (val is not None and val > 0)
        if h.type == "checkbox":
            total_checkbox_habits += 1
            if is_done:
                completed_habits += 1
        habits_data.append({
            "id": h.id,
            "name": h.name,
            "type": h.type,
            "value": val,
            "completed": is_done
        })

    # 2. Todos summary
    all_todos = session.exec(select(Todo)).all()
    pending_todos = [t for t in all_todos if not t.done]
    due_today_todos = [t for t in pending_todos if t.due_date == today_str]
    overdue_todos = [t for t in pending_todos if t.due_date and t.due_date < today_str]

    # Top high-priority or pending todos (up to 5)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    sorted_todos = sorted(
        pending_todos,
        key=lambda x: (
            0 if x.due_date and x.due_date <= today_str else 1,
            priority_order.get(x.priority, 1),
            x.created_at
        )
    )[:6]

    # 3. Calendar events (next 3 events from today onwards)
    upcoming_events = session.exec(
        select(Event)
        .where(Event.start_datetime >= today_str)
        .order_by(Event.start_datetime)
        .limit(3)
    ).all()

    # 4. Finance summary (current month)
    fin_summary = {"spent": 0, "income": 0, "net": 0}
    try:
        current_month = now.strftime("%Y-%m")
        overview = fin_analytics.get_kpis(period="month")
        if overview:
            fin_summary["spent"] = overview.get("total_debit", 0)
            fin_summary["income"] = overview.get("total_credit", 0)
            fin_summary["net"] = overview.get("net_flow", 0)
    except Exception:
        pass

    # 5. Journal for today
    today_journal = session.exec(
        select(JournalEntry).where(JournalEntry.date == today_str)
    ).first()

    return {
        "greeting": greeting,
        "date": today_str,
        "time": now.strftime("%I:%M %p"),
        "formatted_date": now.strftime("%A, %B %d, %Y"),
        "habits": {
            "items": habits_data,
            "completed": completed_habits,
            "total": total_checkbox_habits,
            "rate": round((completed_habits / total_checkbox_habits) * 100) if total_checkbox_habits > 0 else 0
        },
        "todos": {
            "total_pending": len(pending_todos),
            "due_today_count": len(due_today_todos),
            "overdue_count": len(overdue_todos),
            "items": [
                {"task": t.task, "priority": t.priority, "done": t.done, "due_date": t.due_date, "tags": t.tags}
                for t in sorted_todos
            ]
        },
        "events": [
            {
                "id": e.id,
                "title": e.title,
                "start": e.start_datetime,
                "end": e.end_datetime
            }
            for e in upcoming_events
        ],
        "finance": fin_summary,
        "journal": {
            "has_entry": today_journal is not None,
            "mood": today_journal.mood if today_journal else 3,
            "content": today_journal.content if today_journal else "",
        }
    }
