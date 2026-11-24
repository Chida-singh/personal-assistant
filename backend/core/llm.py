"""
LLM Fallback Client — supports Ollama locally and Google Gemini Flash in cloud.
"""

import json
import os
import re
from datetime import datetime
from typing import AsyncGenerator, Optional

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma4")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

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
    "- track_habit       -> parameters: name (str), completed (bool, default true)\n"
    "- habit_summary     -> parameters: period (week/month, optional)\n"
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
    "Never say 'I am an AI'."
)


def build_system_prompt() -> str:
    return _SYSTEM_TEMPLATE.format(now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def check_ollama_alive() -> bool:
    try:
        with httpx.Client(timeout=1.0) as client:
            tags_url = OLLAMA_URL.replace("/api/chat", "/api/tags")
            res = client.get(tags_url)
            return res.status_code == 200
    except Exception:
        return False


def get_llm_source() -> str:
    """Returns 'ollama', 'gemini', or 'offline'."""
    if check_ollama_alive():
        return "ollama"
    api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
    if api_key:
        return "gemini"
    return "offline"


def _call_gemini(message: str, history: list[dict], system_prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
    if not api_key:
        return json.dumps({
            "intent": "general_chat",
            "parameters": {"message": "Ollama is not running and GEMINI_API_KEY is not set. Please set GEMINI_API_KEY in .env."}
        })

    # Prepare Gemini generateContent payload
    contents = []
    for h in history[-8:]:
        role = "user" if h.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.3
        }
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            return json.dumps({"intent": "general_chat", "parameters": {"message": "No response generated."}})
    except Exception as e:
        return json.dumps({
            "intent": "general_chat",
            "parameters": {"message": f"Gemini error: {str(e)}"}
        })


def call_llm(message: str, history: list[dict] = None) -> str:
    history = history or []
    source = get_llm_source()
    system_prompt = build_system_prompt()

    if source == "ollama":
        try:
            with httpx.Client(timeout=60.0) as client:
                payload = {
                    "model": LLM_MODEL,
                    "format": "json",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        *history[-8:],
                        {"role": "user", "content": message},
                    ],
                    "stream": False,
                }
                resp = client.post(OLLAMA_URL, json=payload)
                resp.raise_for_status()
                return resp.json().get("message", {}).get("content", "").strip()
        except Exception:
            # Fall back to Gemini if Ollama fails mid-request
            if os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY:
                return _call_gemini(message, history, system_prompt)

    if source == "gemini":
        return _call_gemini(message, history, system_prompt)

    return json.dumps({
        "intent": "general_chat",
        "parameters": {"message": "AI is offline. Please start Ollama locally or configure GEMINI_API_KEY in .env."}
    })
