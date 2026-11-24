import json
import os
from fastapi import HTTPException
from models import VaultEntry

FILE_PATH = "vault.json"

def _load_data() -> list[dict]:
    if not os.path.exists(FILE_PATH):
        return []
    try:
        with open(FILE_PATH, "r") as f:
            data = json.load(f)
            return data
    except Exception:
        return []

def _save_data(data: list[dict]):
    # Pydantic models need datetime serialization, so use string dump instead of dict if needed,
    # or just trust that everything in the list is JSON serializable via dict conversion.
    # Since we store as dict containing ISO format datetimes, we should be good.
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)

def get_all_entries() -> list[VaultEntry]:
    data = _load_data()
    return [VaultEntry(**entry) for entry in data]

def create_entry(data: dict) -> VaultEntry:
    new_entry = VaultEntry(**data)
    # Convert to dict with json-serializable datetime
    entry_dict = json.loads(new_entry.json())
    entries = _load_data()
    entries.append(entry_dict)
    _save_data(entries)
    return new_entry

def update_entry(entry_id: str, data: dict) -> VaultEntry:
    entries = _load_data()
    for i, entry in enumerate(entries):
        if entry.get("id") == entry_id:
            for field, value in data.items():
                if field != "id" and field != "created_at":
                    entry[field] = value
            entries[i] = entry
            _save_data(entries)
            return VaultEntry(**entry)
    
    raise HTTPException(status_code=404, detail="Entry not found")

def delete_entry(entry_id: str) -> None:
    entries = _load_data()
    new_entries = [e for e in entries if e.get("id") != entry_id]
    if len(entries) == len(new_entries):
        raise HTTPException(status_code=404, detail="Entry not found")
    _save_data(new_entries)
