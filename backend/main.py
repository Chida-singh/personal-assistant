"""FastAPI backend for AI Personal Assistant — uses Gemma 4 via Ollama."""

import json
import re
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import logging

# Basic logging for backend
logging.basicConfig(level=logging.INFO)

# ── app setup ──
app = FastAPI(title="AI Personal Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ── import modules ──
import sys
sys.path.insert(0, str(Path(__file__).parent))

from modules import finance as fin_module
from modules import todo as todo_module
from modules import girlfriend as notes_module
from modules import vault as vault_module
from modules import calendar as calendar_module
from core.storage import TODOS_FILE, GIRLFRIEND_FILE, load, save

# ── LLM config ──
OLLAMA_URL = "http://localhost:11434/api/chat"
LLM_MODEL = os.getenv("LLM_MODEL", "gemma4")

import requests as http_requests
import httpx

SYSTEM_PROMPT_TEMPLATE = (
    "You are Cookie, a smart, friendly, and reliable personal AI assistant. "
    "You help with scheduling, tasks, personal notes, finance, and everyday conversation.\n\n"

    "== RESPONSE FORMAT ==\n"
    "ALWAYS return a single valid JSON object. No markdown, no code fences, no extra text. Ever.\n"
    "Format: {{\"intent\": \"<intent_name>\", \"parameters\": {{...}}}}\n\n"

    "== SUPPORTED INTENTS ==\n"
    "- check_calendar    -> parameters: date (YYYY-MM-DD)\n"
    "- create_event      -> parameters: title (str), datetime (ISO 8601), end_datetime (ISO 8601, optional)\n"
    "- add_todo          -> parameters: task (str), priority (low/medium/high, optional)\n"
    "- complete_todo     -> parameters: task (str)\n"
    "- delete_todo       -> parameters: task (str)\n"
    "- remember          -> parameters: key (str), value (str)\n"
    "- recall            -> parameters: key (str)\n"
    "- general_chat      -> parameters: message (str)\n\n"

    "== DATE & TIME RULES ==\n"
    "Current date/time: {now}\n"
    "1. Resolve ALL dates/times yourself using current date above. NEVER ask user.\n"
    "2. Resolve relative terms: 'tomorrow', 'next Monday', 'tonight', etc.\n"
    "3. Default start time: 09:00:00. Default duration: 1 hour.\n"
    "4. Output datetime in ISO 8601: YYYY-MM-DDTHH:MM:SS\n\n"

    "== GENERAL CHAT ==\n"
    "1. For greetings, small talk, questions, jokes — use general_chat.\n"
    "2. Be concise, warm, occasionally witty. Under 3 sentences unless detail asked.\n"
    "3. Never say 'I am an AI'.\n\n"

    "== AMBIGUITY ==\n"
    "1. If could be task OR event, prefer create_event.\n"
    "2. If just a note with no time, use add_todo.\n"
    "3. If unsure, use general_chat.\n"
)


def _build_system_prompt() -> str:
    now_dt = datetime.now()
    now = now_dt.strftime("%A, %Y-%m-%d %H:%M")
    return SYSTEM_PROMPT_TEMPLATE.format(now=now)


def _extract_json(text: str) -> str:
    stripped = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE).replace("```", "")
    return stripped.strip()


def _llm_call(user_input: str, history: list[dict]) -> str:
    payload = {
        "model": LLM_MODEL,
        "format": "json",
        "messages": [
            {"role": "system", "content": _build_system_prompt()},
            *history,
            {"role": "user", "content": user_input},
        ],
        "stream": True,
    }
    resp = http_requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)
    resp.raise_for_status()
    full = ""
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        chunk = json.loads(line)
        full += chunk.get("message", {}).get("content", "")
    return full


def _route_intent(llm_output: str) -> str:
    clean = _extract_json(llm_output)
    try:
        payload = json.loads(clean)
    except (TypeError, json.JSONDecodeError):
        return clean if clean else llm_output

    intent = payload.get("intent")
    params = payload.get("parameters", {})

    if intent == "general_chat":
        return str(params.get("message", ""))

    if intent == "check_calendar":
        from modules import calendar as cal_mod
        return cal_mod.check_events(str(params.get("date", "")))

    if intent == "create_event":
        from modules import calendar as cal_mod
        return cal_mod.create_event(
            str(params.get("title", "")),
            str(params.get("datetime", "")),
            str(params.get("end_datetime", "")),
        )

    if intent == "add_todo":
        task_text = str(params.get("task", ""))
        priority = str(params.get("priority", "medium")).lower()
        if priority not in ("high", "medium", "low"):
            priority = "medium"
        tasks = load(TODOS_FILE)
        tasks.append({"task": task_text, "done": False, "priority": priority})
        save(TODOS_FILE, tasks)
        return f"Added '{task_text}' to your {priority} priority tasks."

    if intent == "complete_todo":
        return todo_module.complete_todo(str(params.get("task", "")))

    if intent == "delete_todo":
        return todo_module.delete_todo(str(params.get("task", "")))

    if intent == "remember":
        return notes_module.remember(str(params.get("key", "")), str(params.get("value", "")))

    if intent == "recall":
        return notes_module.recall(str(params.get("key", "")))

    return "I'm not sure how to help with that."


# ──────────────────────────────────────────
# API Models
# ──────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

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

class EventCreate(BaseModel):
    title: str
    datetime: str
    end_datetime: str = ""

class EventCheck(BaseModel):
    date: str

class EventCreate(BaseModel):
    title: str
    datetime: str
    end_datetime: str = ""

class EventUpdate(BaseModel):
    title: str
    start_datetime: str
    end_datetime: str

class VaultEntry(BaseModel):
    id: Optional[str] = None
    service: str
    username: str = ""
    password: str = ""
    url: str = ""
    notes: str = ""


# ──────────────────────────────────────────
# Chat endpoints
# ──────────────────────────────────────────

@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        raw = _llm_call(req.message, req.history)
        response = _route_intent(raw)
        return {"response": response, "raw_intent": raw}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE streaming endpoint for real-time token display."""
    import asyncio

    async def generate():
        payload = {
            "model": LLM_MODEL,
            "format": "json",
            "messages": [
                {"role": "system", "content": _build_system_prompt()},
                *req.history,
                {"role": "user", "content": req.message},
            ],
            "stream": True,
        }
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", OLLAMA_URL, json=payload, timeout=120.0) as resp:
                    resp.raise_for_status()
                    full = ""
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            full += token
                            yield f"data: {json.dumps({'token': token})}\n\n"

            # After streaming, route the full response
            routed = _route_intent(full)
            yield f"data: {json.dumps({'done': True, 'response': routed, 'raw': full})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ──────────────────────────────────────────
# Finance endpoints
# ──────────────────────────────────────────

# Auto-fix miscategorized rows on startup
@app.on_event("startup")
def startup_recategorize():
    try:
        changed = fin_module.recategorize_ledger()
        if changed:
            logging.info("[Finance] Auto-recategorized %s transactions.", changed)
    except Exception as e:
        logging.exception("[Finance] Recategorization error")


from fastapi import Form

@app.post("/api/finance/upload")
async def finance_upload(file: UploadFile = File(...), account: str = Form("Main")):
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)
    count, err = fin_module.ingest_file(str(dest), account)
    if err:
        raise HTTPException(400, err)
    return {"count": count, "message": f"{count} transactions imported", "filename": file.filename}


@app.get("/api/finance/accounts")
def finance_accounts():
    return {"accounts": fin_module.get_accounts()}


@app.get("/api/finance/dashboard")
def finance_dashboard(period: str = "month", account: str = "All"):
    df = fin_module.get_ledger_df()
    if account != "All" and not df.empty:
        df = df[df["Account"] == account]
    if df.empty:
        return {"empty": True, "stats": {}, "chart_data": {}}

    stats = fin_module.summary_stats(df)
    chart_data = {}

    # Period grouped data
    gp = fin_module.group_by_period(df, period)
    if not gp.empty:
        chart_data["period"] = [
            {
                "label": (
                    f"{pd.Timestamp(row.Period):%b %y}" if period == "month"
                    else f"{pd.Timestamp(row.Period):%d %b}" if period == "week"
                    else f"Q{pd.Timestamp(row.Period).quarter} {pd.Timestamp(row.Period):%y}"
                ),
                "debit": round(float(row.Debit), 2),
                "credit": round(float(row.Credit), 2),
                "net": round(float(row.Net), 2),
            }
            for row in gp.itertuples()
        ]

    # Category breakdown
    cat = fin_module.category_breakdown(df)
    if not cat.empty:
        chart_data["category"] = [
            {"category": row.Category, "amount": round(float(row.Amount), 2)}
            for row in cat.itertuples()
        ]

    # Weekday avg
    wd = fin_module.weekday_avg_spending(df)
    if not wd.empty:
        chart_data["weekday"] = [
            {"day": row.Weekday[:3], "avg": round(float(row.AvgSpend), 2)}
            for row in wd.itertuples()
        ]

    # Balance trend (sampled to last 60 points)
    bal_df = df[df["Balance"] > 0].sort_values("Date")
    if not bal_df.empty:
        sample = bal_df.tail(60)
        chart_data["balance"] = [
            {"date": str(row.Date)[:10], "balance": round(float(row.Balance), 2)}
            for row in sample.itertuples()
        ]

    return {"empty": False, "stats": stats, "chart_data": chart_data}


@app.get("/api/finance/report")
def finance_report(account: str = "All"):
    df = fin_module.get_ledger_df()
    if account != "All" and not df.empty:
        df = df[df["Account"] == account]
    if df.empty:
        return {"empty": True}
    report = fin_module.generate_report(df)
    return {"empty": False, **report}


@app.get("/api/finance/transactions")
def finance_transactions(
    category: str = "",
    search: str = "",
    sort_by: str = "date_desc",
    page: int = 1,
    limit: int = 50,
    account: str = "All"
):
    return fin_module.get_transactions(category, search, sort_by, page, limit, account)


class ManualTransaction(BaseModel):
    date: str
    description: str
    debit: float = 0.0
    credit: float = 0.0
    category: str = ""
    account: str = "Main"


@app.post("/api/finance/transactions/manual")
def finance_add_manual(txn: ManualTransaction):
    row = fin_module.add_manual_transaction(
        txn.date, txn.description, txn.debit, txn.credit, txn.category, txn.account
    )
    return {"message": "Transaction added", "transaction": row}


class CategoryUpdate(BaseModel):
    category: str = ""
    note: str = None


@app.patch("/api/finance/transactions/{txn_id}")
def finance_update_category(txn_id: str, body: CategoryUpdate):
    ok = fin_module.update_transaction_category(txn_id, body.category, body.note)
    if not ok:
        raise HTTPException(404, "Transaction not found")
    return {"message": "Transaction updated"}


@app.get("/api/finance/ambiguous")
def finance_ambiguous():
    return {"transactions": fin_module.get_ambiguous_transactions()}


class ConfirmUpdate(BaseModel):
    category: str
    note: str = ""


@app.post("/api/finance/transactions/{txn_id}/confirm")
def finance_confirm_txn(txn_id: str, body: ConfirmUpdate):
    ok = fin_module.confirm_transaction(txn_id, body.category, body.note)
    if not ok:
        raise HTTPException(404, "Transaction not found")
    return {"message": "Transaction confirmed"}


@app.get("/api/finance/insights")
def finance_insights():
    return fin_module.generate_ai_insights()


@app.get("/api/finance/charts/{name}")
def finance_chart(name: str, period: str = "month"):
    data_dir = Path(__file__).parent / "data"
    # period chart uses period-specific filename
    if name == "period":
        fp = data_dir / f"chart_period_{period}.png"
    else:
        chart_map = {
            "category": "chart_category.png",
            "weekday": "chart_weekday.png",
            "paytype": "chart_paytype.png",
            "balance": "chart_balance.png",
        }
        filename = chart_map.get(name)
        if not filename:
            raise HTTPException(404, "Chart not found")
        fp = data_dir / filename
    if not fp.exists():
        raise HTTPException(404, "Chart not generated yet")
    return FileResponse(str(fp), media_type="image/png", headers={"Cache-Control": "no-cache"})


@app.delete("/api/finance/clear")
def finance_clear():
    fin_module.clear_ledger()
    return {"message": "All finance data cleared"}


# ──────────────────────────────────────────
# Todo endpoints
# ──────────────────────────────────────────

@app.get("/api/todos")
def get_todos():
    return load(TODOS_FILE)


@app.post("/api/todos")
def add_todo(todo: TodoCreate):
    tasks = load(TODOS_FILE)
    tasks.append({"task": todo.task, "done": False, "priority": todo.priority})
    save(TODOS_FILE, tasks)
    return {"message": f"Added: {todo.task}"}


@app.put("/api/todos/complete")
def complete_todo(todo: TodoUpdate):
    result = todo_module.complete_todo(todo.task)
    return {"message": result}


@app.delete("/api/todos/{task}")
def delete_todo(task: str):
    result = todo_module.delete_todo(task)
    return {"message": result}

@app.delete("/api/todos/all")
def delete_all_todos():
    save(TODOS_FILE, [])
    return {"message": "All tasks deleted"}

@app.delete("/api/todos/done")
def delete_done_todos():
    tasks = load(TODOS_FILE)
    remaining = [t for t in tasks if not t.get("done")]
    save(TODOS_FILE, remaining)
    return {"message": "Done tasks deleted"}


@app.put("/api/todos/move")
def move_todo(todo: TodoMove):
    tasks = load(TODOS_FILE)
    for t in tasks:
        if t.get("task") == todo.task:
            if todo.target_key == "done":
                t["done"] = True
            else:
                t["done"] = False
                t["priority"] = todo.target_key
            break
    save(TODOS_FILE, tasks)
    return {"message": f"Moved {todo.task} to {todo.target_key}"}


# ──────────────────────────────────────────
# Notes (Sticky Notes) endpoints
# ──────────────────────────────────────────

@app.get("/api/notes")
def get_notes():
    return load(GIRLFRIEND_FILE)


@app.post("/api/notes")
def add_note(note: NoteCreate):
    result = notes_module.remember(note.key, note.value)
    return {"message": result}


@app.post("/api/notes/recall")
def recall_note(note: NoteRecall):
    result = notes_module.recall(note.key)
    return {"message": result}

@app.delete("/api/notes/{key}")
def delete_note(key: str):
    notes = load(GIRLFRIEND_FILE)
    key_to_match = key.strip().lower()
    new_notes = [n for n in notes if str(n.get("key", "")).strip().lower() != key_to_match]
    save(GIRLFRIEND_FILE, new_notes)
    return {"message": "Note deleted"}



# ──────────────────────────────────────────
# Vault endpoints
# ──────────────────────────────────────────

@app.get("/api/vault")
def get_vault():
    return vault_module.get_all()

@app.post("/api/vault")
def add_vault_entry(entry: VaultEntry):
    if entry.id:
        res = vault_module.update_entry(entry.id, entry.service, entry.username, entry.password, entry.url, entry.notes)
        if not res:
            raise HTTPException(404, "Entry not found")
        return {"message": "Entry updated", "entry": res}
    else:
        res = vault_module.add_entry(entry.service, entry.username, entry.password, entry.url, entry.notes)
        return {"message": "Entry added", "entry": res}

@app.delete("/api/vault/{entry_id}")
def delete_vault_entry(entry_id: str):
    if vault_module.delete_entry(entry_id):
        return {"message": "Entry deleted"}
    raise HTTPException(404, "Entry not found")

# ──────────────────────────────────────────
# Calendar endpoints
# ──────────────────────────────────────────

@app.post("/api/calendar/check")
def check_calendar(req: EventCheck):
    from modules import calendar as cal_mod
    result = cal_mod.check_events(req.date)
    return {"message": result}


@app.get("/api/calendar/month")
def get_calendar_month(year: int, month: int):
    events = calendar_module.get_month_events(year, month)
    return {"events": events}

@app.post("/api/calendar/create")
def create_calendar_event(event: EventCreate):
    result = calendar_module.create_event(event.title, event.datetime, event.end_datetime)
    return {"message": result}

@app.put("/api/calendar/update/{event_id}")
def update_calendar_event(event_id: str, event: EventUpdate):
    result = calendar_module.update_event(event_id, event.title, event.start_datetime, event.end_datetime)
    return {"message": result}

@app.delete("/api/calendar/delete/{event_id}")
def delete_calendar_event(event_id: str):
    result = calendar_module.delete_event(event_id)
    return {"message": result}


# ──────────────────────────────────────────
# Health check
# ──────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "model": LLM_MODEL}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
