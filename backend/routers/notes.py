from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ..core.database import get_session
from ..core.models import Note

router = APIRouter(prefix="/api/notes", tags=["notes"])


class NoteCreate(BaseModel):
    key: str
    value: str


class NoteRecall(BaseModel):
    key: str


@router.get("")
def read_notes(session: Session = Depends(get_session)):
    notes = session.exec(select(Note)).all()
    return [{"key": n.key, "value": n.value} for n in notes]


@router.post("")
def upsert_note(note: NoteCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(Note).where(Note.key == note.key)).first()
    if existing:
        existing.value = note.value
        session.add(existing)
        session.commit()
        return {"message": "Updated"}
    session.add(Note(key=note.key, value=note.value))
    session.commit()
    return {"message": "Added"}


@router.post("/recall")
def recall_note(recall: NoteRecall, session: Session = Depends(get_session)):
    note = session.exec(select(Note).where(Note.key == recall.key)).first()
    if not note:
        raise HTTPException(404, "Note not found")
    return {"key": note.key, "value": note.value}


@router.delete("/{key}")
def delete_note(key: str, session: Session = Depends(get_session)):
    note = session.exec(select(Note).where(Note.key == key)).first()
    if not note:
        raise HTTPException(404, "Note not found")
    session.delete(note)
    session.commit()
    return {"message": "Deleted"}
