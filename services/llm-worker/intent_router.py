"""Intent router — maps LLM JSON output to downstream service calls."""

import json
import os
import re

import requests as http_requests

TODO_URL = os.getenv("TODO_SERVICE_URL", "http://todo-service:8001")
CALENDAR_URL = os.getenv("CALENDAR_SERVICE_URL", "http://calendar-service:8003")


def route(llm_output: str) -> str:
    """Parse LLM intent JSON and dispatch to the correct downstream service."""
    clean = re.sub(r"```(?:json)?\s*", "", llm_output, flags=re.IGNORECASE).replace("```", "").strip()

    try:
        payload = json.loads(clean)
    except (TypeError, json.JSONDecodeError):
        return clean or llm_output

    intent = payload.get("intent")
    params = payload.get("parameters", {})

    handler = _HANDLERS.get(intent)
    if handler:
        return handler(params)
    return "I'm not sure how to help with that."


# ── Individual intent handlers (each does exactly one thing) ──────────────────

def _general_chat(params: dict) -> str:
    return str(params.get("message", ""))


def _check_calendar(params: dict) -> str:
    return _post(f"{CALENDAR_URL}/api/calendar/check", {"date": str(params.get("date", ""))}, "message")


def _create_event(params: dict) -> str:
    return _post(f"{CALENDAR_URL}/api/calendar/create", {
        "title": str(params.get("title", "")),
        "datetime": str(params.get("datetime", "")),
        "end_datetime": str(params.get("end_datetime", "")),
    }, "message")


def _add_todo(params: dict) -> str:
    task = str(params.get("task", ""))
    _post(f"{TODO_URL}/api/todos", {"task": task, "priority": str(params.get("priority", "medium")).lower()})
    return f"Added '{task}' to your tasks."


def _complete_todo(params: dict) -> str:
    task = str(params.get("task", ""))
    r = _raw_delete(f"{TODO_URL}/api/todos/{task}")
    return f"Marked '{task}' as complete." if r and r.status_code == 200 else "Task not found."


def _delete_todo(params: dict) -> str:
    task = str(params.get("task", ""))
    r = _raw_delete(f"{TODO_URL}/api/todos/{task}")
    return f"Deleted '{task}'." if r and r.status_code == 200 else "Task not found."


def _remember(params: dict) -> str:
    key, value = str(params.get("key", "")), str(params.get("value", ""))
    _post(f"{TODO_URL}/api/notes", {"key": key, "value": value})
    return f"I'll remember that {key} is {value}."


def _recall(params: dict) -> str:
    return _post(f"{TODO_URL}/api/notes/recall", {"key": str(params.get("key", ""))}, "value",
                 fallback="Could not recall that.")


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _post(url: str, body: dict, field: str = "", fallback: str = "Service unavailable.") -> str:
    try:
        r = http_requests.post(url, json=body, timeout=10)
        return r.json().get(field, fallback) if field else fallback
    except Exception:
        return fallback


def _raw_delete(url: str):
    try:
        return http_requests.delete(url, timeout=10)
    except Exception:
        return None


_HANDLERS = {
    "general_chat": _general_chat,
    "check_calendar": _check_calendar,
    "create_event": _create_event,
    "add_todo": _add_todo,
    "complete_todo": _complete_todo,
    "delete_todo": _delete_todo,
    "remember": _remember,
    "recall": _recall,
}
