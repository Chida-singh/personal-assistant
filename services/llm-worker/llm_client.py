"""LLM Worker — chat endpoint backed by a local Ollama model.

Responsibilities:
  intent_router.py  — parse LLM JSON output and call downstream services
  prompt.py         — build the system prompt
  llm_client.py     — talk to Ollama (sync and streaming)
  main.py           — FastAPI routes only
"""

import json
import os
from datetime import datetime

import requests as http_requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/chat")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma4")


_SYSTEM_TEMPLATE = (
    "You are Cookie, a smart, friendly, and reliable personal AI assistant. "
    "You help with scheduling, tasks, personal notes, finance, and everyday conversation.\n\n"

    "== RESPONSE FORMAT ==\n"
    "ALWAYS return a single valid JSON object. No markdown, no code fences, no extra text. Ever.\n"
    'Format: {"intent": "<intent_name>", "parameters": {...}}\n\n'

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
    "1. Resolve ALL dates/times yourself. NEVER ask the user.\n"
    "2. Resolve relative terms: 'tomorrow', 'next Monday', 'tonight', etc.\n"
    "3. Default start time: 09:00:00. Default duration: 1 hour.\n"
    "4. Output datetime in ISO 8601: YYYY-MM-DDTHH:MM:SS\n\n"

    "== GENERAL CHAT ==\n"
    "For greetings, small talk, questions — use general_chat.\n"
    "Be concise, warm, occasionally witty. Under 3 sentences unless detail asked.\n"
    "Never say 'I am an AI'.\n\n"

    "== AMBIGUITY ==\n"
    "If could be task OR event, prefer create_event.\n"
    "If just a note with no time, use add_todo.\n"
    "If unsure, use general_chat.\n"
)


def build_system_prompt() -> str:
    now = datetime.now().strftime("%A, %Y-%m-%d %H:%M")
    return _SYSTEM_TEMPLATE.format(now=now)


def call_ollama(user_input: str, history: list[dict]) -> str:
    """Send a message to Ollama and return the full response string."""
    payload = {
        "model": LLM_MODEL,
        "format": "json",
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            *history,
            {"role": "user", "content": user_input},
        ],
        "stream": True,
    }
    try:
        resp = http_requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)
        resp.raise_for_status()
        return "".join(
            json.loads(line).get("message", {}).get("content", "")
            for line in resp.iter_lines(decode_unicode=True)
            if line
        )
    except http_requests.exceptions.ConnectionError:
        return json.dumps({"intent": "general_chat", "parameters": {"message": "Could not connect to Ollama."}})
    except Exception as exc:
        return json.dumps({"intent": "general_chat", "parameters": {"message": f"LLM Error: {exc}"}})
