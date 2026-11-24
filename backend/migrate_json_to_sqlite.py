"""
One-time migration script: Imports legacy JSON data files into SQLite database.
Usage:
    python backend/migrate_json_to_sqlite.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.core.database import engine, create_db_and_tables
from backend.core.models import VaultItem, Todo, Note, Habit, HabitLog, Transaction
from sqlmodel import Session, select


def migrate():
    create_db_and_tables()
    with Session(engine) as session:
        # 1. Migrate vault.json
        vault_paths = [ROOT_DIR / "vault.json", ROOT_DIR / "backend" / "data" / "vault.json"]
        for vp in vault_paths:
            if vp.exists():
                try:
                    with open(vp, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    count = 0
                    for item in data:
                        vid = item.get("id")
                        if not vid or session.exec(select(VaultItem).where(VaultItem.id == vid)).first():
                            continue
                        v = VaultItem(
                            id=vid,
                            service=item.get("service", ""),
                            username=item.get("username", ""),
                            password=item.get("password", ""),
                            url=item.get("url", ""),
                            notes=item.get("notes", ""),
                            created_at=datetime.utcnow()
                        )
                        session.add(v)
                        count += 1
                    session.commit()
                    print(f"[Migrate] Imported {count} vault entries from {vp.name}")
                except Exception as e:
                    print(f"[Migrate] Error reading {vp}: {e}")

        # 2. Migrate todos.json
        todo_paths = [
            ROOT_DIR / "backend" / "data" / "todos.json",
            ROOT_DIR / "assistant" / "data" / "todos.json",
            ROOT_DIR / "todos.json",
        ]
        for tp in todo_paths:
            if tp.exists():
                try:
                    with open(tp, "r", encoding="utf-8") as f:
                        todos = json.load(f)
                    count = 0
                    for t in todos:
                        task = t.get("task")
                        if not task or session.exec(select(Todo).where(Todo.task == task)).first():
                            continue
                        session.add(Todo(
                            task=task,
                            done=t.get("done", False),
                            priority=t.get("priority", "medium"),
                            created_at=datetime.utcnow()
                        ))
                        count += 1
                    session.commit()
                    print(f"[Migrate] Imported {count} todos from {tp.name}")
                except Exception as e:
                    print(f"[Migrate] Error reading {tp}: {e}")

        # 3. Migrate habits.json
        habit_paths = [
            ROOT_DIR / "backend" / "data" / "habits.json",
            ROOT_DIR / "habits.json"
        ]
        for hp in habit_paths:
            if hp.exists():
                try:
                    with open(hp, "r", encoding="utf-8") as f:
                        habits = json.load(f)
                    count = 0
                    for h in habits:
                        hid = h.get("id")
                        if not hid or session.exec(select(Habit).where(Habit.id == hid)).first():
                            continue
                        session.add(Habit(
                            id=hid,
                            name=h.get("name", ""),
                            type=h.get("type", "checkbox"),
                            order=h.get("order", 0),
                            created_at=datetime.utcnow()
                        ))
                        count += 1
                    session.commit()
                    print(f"[Migrate] Imported {count} habits from {hp.name}")
                except Exception as e:
                    print(f"[Migrate] Error reading {hp}: {e}")

        # 4. Migrate notes (girlfriend.json / notes.json)
        note_paths = [
            ROOT_DIR / "backend" / "data" / "notes.json",
            ROOT_DIR / "backend" / "data" / "girlfriend.json",
            ROOT_DIR / "assistant" / "data" / "girlfriend.json",
        ]
        for np in note_paths:
            if np.exists():
                try:
                    with open(np, "r", encoding="utf-8") as f:
                        notes = json.load(f)
                    count = 0
                    if isinstance(notes, dict):
                        for k, v in notes.items():
                            if session.exec(select(Note).where(Note.key == k)).first():
                                continue
                            session.add(Note(key=k, value=str(v), created_at=datetime.utcnow()))
                            count += 1
                    elif isinstance(notes, list):
                        for item in notes:
                            k = item.get("key")
                            v = item.get("value")
                            if not k or session.exec(select(Note).where(Note.key == k)).first():
                                continue
                            session.add(Note(key=k, value=str(v), created_at=datetime.utcnow()))
                            count += 1
                    session.commit()
                    print(f"[Migrate] Imported {count} notes from {np.name}")
                except Exception as e:
                    print(f"[Migrate] Error reading {np}: {e}")

    print("[Migrate] Migration complete! All data stored in SQLite.")


if __name__ == "__main__":
    migrate()
