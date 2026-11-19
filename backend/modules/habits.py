"""Habit tracker module — monthly grid with checkbox and numeric habits."""

import json
import uuid
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HABITS_FILE = DATA_DIR / "habits.json"
LOGS_FILE   = DATA_DIR / "habit_logs.json"


def _load(path: Path) -> list:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(path: Path, data: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── Habit definitions ──────────────────────────────────────────────────────

def get_habits() -> list:
    return sorted(_load(HABITS_FILE), key=lambda h: h.get("order", 0))


def add_habit(name: str, habit_type: str = "checkbox") -> dict:
    habits = _load(HABITS_FILE)
    habit = {
        "id":    str(uuid.uuid4())[:8],
        "name":  name,
        "type":  habit_type,   # "checkbox" | "number"
        "order": len(habits),
    }
    habits.append(habit)
    _save(HABITS_FILE, habits)
    return habit


def delete_habit(habit_id: str) -> bool:
    habits = _load(HABITS_FILE)
    new_habits = [h for h in habits if h["id"] != habit_id]
    if len(new_habits) == len(habits):
        return False
    _save(HABITS_FILE, new_habits)
    # Clean up logs for this habit
    logs = _load(LOGS_FILE)
    _save(LOGS_FILE, [l for l in logs if l["habit_id"] != habit_id])
    return True


def reorder_habits(ordered_ids: list) -> list:
    habits = _load(HABITS_FILE)
    index = {h["id"]: h for h in habits}
    reordered = []
    for i, hid in enumerate(ordered_ids):
        if hid in index:
            index[hid]["order"] = i
            reordered.append(index[hid])
    _save(HABITS_FILE, reordered)
    return reordered


# ── Logs ───────────────────────────────────────────────────────────────────

def get_month_logs(year: int, month: int) -> list:
    prefix = f"{year}-{month:02d}"
    return [l for l in _load(LOGS_FILE) if l["date"].startswith(prefix)]


def set_log(date_str: str, habit_id: str, value) -> dict:
    """Create or update a log entry. value = True/False for checkbox, float for number."""
    logs = _load(LOGS_FILE)
    for log in logs:
        if log["date"] == date_str and log["habit_id"] == habit_id:
            log["value"] = value
            _save(LOGS_FILE, logs)
            return log
    new_log = {"date": date_str, "habit_id": habit_id, "value": value}
    logs.append(new_log)
    _save(LOGS_FILE, logs)
    return new_log


def clear_log(date_str: str, habit_id: str) -> bool:
    logs = _load(LOGS_FILE)
    new_logs = [l for l in logs if not (l["date"] == date_str and l["habit_id"] == habit_id)]
    _save(LOGS_FILE, new_logs)
    return len(new_logs) != len(logs)
