from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ..core.database import get_session
from ..core.models import VaultItem

router = APIRouter(prefix="/api/vault", tags=["vault"])


class VaultEntryIn(BaseModel):
    service: str
    username: str = ""
    password: str = ""
    url: str = ""
    notes: str = ""


@router.get("")
def list_entries(session: Session = Depends(get_session)):
    entries = session.exec(select(VaultItem)).all()
    return [
        {
            "id": e.id,
            "service": e.service,
            "username": e.username,
            "password": e.password,
            "url": e.url,
            "notes": e.notes,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]


@router.post("", status_code=201)
def create_entry(entry: VaultEntryIn, session: Session = Depends(get_session)):
    item = VaultItem(
        service=entry.service,
        username=entry.username,
        password=entry.password,
        url=entry.url,
        notes=entry.notes,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return {"message": "Entry added", "entry": item}


@router.put("/{entry_id}")
def update_entry(entry_id: str, entry: VaultEntryIn, session: Session = Depends(get_session)):
    item = session.exec(select(VaultItem).where(VaultItem.id == entry_id)).first()
    if not item:
        raise HTTPException(404, "Entry not found")
    item.service = entry.service
    item.username = entry.username
    item.password = entry.password
    item.url = entry.url
    item.notes = entry.notes
    session.add(item)
    session.commit()
    session.refresh(item)
    return {"message": "Entry updated", "entry": item}


@router.delete("/{entry_id}")
def delete_entry(entry_id: str, session: Session = Depends(get_session)):
    item = session.exec(select(VaultItem).where(VaultItem.id == entry_id)).first()
    if not item:
        raise HTTPException(404, "Entry not found")
    session.delete(item)
    session.commit()
    return {"message": "Entry deleted"}
