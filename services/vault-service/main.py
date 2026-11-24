"""Vault Service — FastAPI routes.

Delegates all database operations to repository.py following SOLID principles.
"""

from fastapi import FastAPI
from pydantic import BaseModel

import repository

app = FastAPI(title="Vault Service")


class VaultEntryIn(BaseModel):
    service: str
    username: str = ""
    password: str = ""
    url: str = ""
    notes: str = ""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/vault")
def list_entries():
    return repository.get_all_entries()


@app.post("/api/vault", status_code=201)
def create_entry(entry: VaultEntryIn):
    new_entry = repository.create_entry(entry.dict())
    return {"message": "Entry added", "entry": new_entry}


@app.put("/api/vault/{entry_id}")
def update_entry(entry_id: str, entry: VaultEntryIn):
    db_entry = repository.update_entry(entry_id, entry.dict())
    return {"message": "Entry updated", "entry": db_entry}


@app.delete("/api/vault/{entry_id}")
def delete_entry(entry_id: str):
    repository.delete_entry(entry_id)
    return {"message": "Entry deleted"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "vault-service"}
