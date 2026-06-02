import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional

VAULT_FILE = Path(__file__).resolve().parent.parent / "data" / "vault.json"

def _load() -> List[Dict]:
    if not VAULT_FILE.exists():
        return []
    try:
        with open(VAULT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def _save(data: List[Dict]):
    VAULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_all() -> List[Dict]:
    return _load()

def add_entry(service: str, username: str, password: str, url: str = "", notes: str = "") -> Dict:
    vault = _load()
    entry = {
        "id": str(uuid.uuid4())[:8],
        "service": service,
        "username": username,
        "password": password,
        "url": url,
        "notes": notes
    }
    vault.append(entry)
    _save(vault)
    return entry

def update_entry(entry_id: str, service: str, username: str, password: str, url: str = "", notes: str = "") -> Optional[Dict]:
    vault = _load()
    for item in vault:
        if item.get("id") == entry_id:
            item["service"] = service
            item["username"] = username
            item["password"] = password
            item["url"] = url
            item["notes"] = notes
            _save(vault)
            return item
    return None

def delete_entry(entry_id: str) -> bool:
    vault = _load()
    new_vault = [item for item in vault if item.get("id") != entry_id]
    if len(vault) != len(new_vault):
        _save(new_vault)
        return True
    return False
