"""FastAPI backend for AI Personal Assistant — Streamlined Monolith with SQLite."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session

from .core.auth import ensure_default_user, verify_token
from .core.database import create_db_and_tables, engine
from .core.llm import get_llm_source
from .finance import core as fin_core
from .routers import auth, calendar, chat, dashboard, finance, habits, journal, notes, todos, vault



@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize SQLite tables
    create_db_and_tables()

    # 2. Ensure initial admin user exists
    with Session(engine) as session:
        ensure_default_user(session)

    # 3. Auto-recategorize finance ledger if present
    try:
        changed = fin_core.recategorize_ledger()
        if changed:
            print(f"[Finance] Auto-recategorized {changed} transactions.")
    except Exception as exc:
        print(f"[Finance] Recategorization note: {exc}")

    yield


app = FastAPI(title="AI Personal Assistant", lifespan=lifespan)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "*",  # For mobile access / Vercel deployment
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Auth Middleware for /api/* ─────────────────────────────────────────
UNPROTECTED_PREFIXES = (
    "/api/auth/login",
    "/api/health",
    "/health",
    "/docs",
    "/openapi.json",
    "/api/calendar/auth",
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS" or any(path.startswith(prefix) for prefix in UNPROTECTED_PREFIXES):
        return await call_next(request)

    # For chart image requests, token can be in query params (?token=...)
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "token" in request.query_params:
        token = request.query_params.get("token")

    if not token or not verify_token(token):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentication required or token expired"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await call_next(request)


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(habits.router)
app.include_router(notes.router)
app.include_router(vault.router)
app.include_router(calendar.router)
app.include_router(finance.router)
app.include_router(chat.router)
app.include_router(journal.router)
app.include_router(dashboard.router)



# ── Health Endpoint ───────────────────────────────────────────────────────────
@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "llm_source": get_llm_source(),
        "storage": "sqlite",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
