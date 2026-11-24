"""LLM Worker — FastAPI routes only.

All business logic lives in:
  llm_client.py    — Ollama communication
  intent_router.py — intent dispatch to downstream services
"""

import json
import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import intent_router
import llm_client

app = FastAPI(title="LLM Worker Service")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/chat")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma4")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        raw = llm_client.call_ollama(req.message, req.history)
        response = intent_router.route(raw)
        return {"response": response, "raw_intent": raw}
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    async def generate():
        payload = {
            "model": LLM_MODEL,
            "format": "json",
            "messages": [
                {"role": "system", "content": llm_client.build_system_prompt()},
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
                        token = json.loads(line).get("message", {}).get("content", "")
                        if token:
                            full += token
                            yield f"data: {json.dumps({'token': token})}\n\n"

            routed = intent_router.route(full)
            yield f"data: {json.dumps({'done': True, 'response': routed, 'raw': full})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "llm-worker"}
