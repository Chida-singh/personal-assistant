from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select, desc

from ..core.database import get_session
from ..core.models import JournalEntry

router = APIRouter(prefix="/api/journal", tags=["journal"])


class JournalCreateOrUpdate(BaseModel):
    date: str  # YYYY-MM-DD
    mood: int = 3
    content: str = ""
    tags: Optional[str] = ""


@router.get("")
def list_entries(
    limit: int = Query(default=30, ge=1, le=100),
    session: Session = Depends(get_session)
):
    entries = session.exec(
        select(JournalEntry).order_by(desc(JournalEntry.date)).limit(limit)
    ).all()
    return [
        {
            "id": e.id,
            "date": e.date,
            "mood": e.mood,
            "content": e.content,
            "tags": [t.strip() for t in e.tags.split(",") if t.strip()] if e.tags else [],
            "created_at": e.created_at.isoformat(),
            "updated_at": e.updated_at.isoformat(),
        }
        for e in entries
    ]


@router.get("/stats")
def get_journal_stats(session: Session = Depends(get_session)):
    entries = session.exec(
        select(JournalEntry).order_by(desc(JournalEntry.date)).limit(30)
    ).all()
    # Return chronologically for chart display
    chronological = list(reversed(entries))
    return {
        "trend": [{"date": e.date, "mood": e.mood} for e in chronological],
        "total_entries": len(entries),
        "average_mood": round(sum(e.mood for e in entries) / len(entries), 1) if entries else None,
    }


@router.get("/{date}")
def get_entry_by_date(date: str, session: Session = Depends(get_session)):
    entry = session.exec(select(JournalEntry).where(JournalEntry.date == date)).first()
    if not entry:
        return {"date": date, "mood": 3, "content": "", "tags": [], "exists": False}
    return {
        "id": entry.id,
        "date": entry.date,
        "mood": entry.mood,
        "content": entry.content,
        "tags": [t.strip() for t in entry.tags.split(",") if t.strip()] if entry.tags else [],
        "exists": True,
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat(),
    }


@router.post("")
def save_entry(body: JournalCreateOrUpdate, session: Session = Depends(get_session)):
    entry = session.exec(select(JournalEntry).where(JournalEntry.date == body.date)).first()
    if entry:
        entry.mood = max(1, min(5, body.mood))
        entry.content = body.content
        entry.tags = body.tags or ""
        entry.updated_at = datetime.utcnow()
        session.add(entry)
    else:
        entry = JournalEntry(
            date=body.date,
            mood=max(1, min(5, body.mood)),
            content=body.content,
            tags=body.tags or "",
        )
        session.add(entry)
    session.commit()
    session.refresh(entry)
    return {
        "id": entry.id,
        "date": entry.date,
        "mood": entry.mood,
        "content": entry.content,
        "tags": [t.strip() for t in entry.tags.split(",") if t.strip()] if entry.tags else [],
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat(),
    }


@router.delete("/{entry_id}")
def delete_entry(entry_id: str, session: Session = Depends(get_session)):
    entry = session.exec(select(JournalEntry).where(JournalEntry.id == entry_id)).first()
    if not entry:
        raise HTTPException(404, "Entry not found")
    session.delete(entry)
    session.commit()
    return {"message": "Deleted"}
