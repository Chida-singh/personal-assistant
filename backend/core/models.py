import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task: str
    done: bool = Field(default=False)
    priority: str = Field(default="medium")  # high, medium, low
    due_date: Optional[str] = Field(default=None)  # YYYY-MM-DD
    tags: Optional[str] = Field(default="")  # comma-separated
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Habit(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], primary_key=True)
    name: str
    type: str = Field(default="checkbox")  # checkbox, number
    order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HabitLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True)  # YYYY-MM-DD
    habit_id: str = Field(index=True)
    value: str  # JSON-encoded string (true, false, number)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Note(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Transaction(SQLModel, table=True):
    id: str = Field(primary_key=True)
    date: str
    description: str
    debit: float = Field(default=0.0)
    credit: float = Field(default=0.0)
    balance: float = Field(default=0.0)
    category: str = Field(default="Other")
    payment_type: str = Field(default="")
    account: str = Field(default="Main")
    user_confirmed: bool = Field(default=False)
    note: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VaultItem(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], primary_key=True)
    service: str
    username: str = ""
    password: str = ""
    url: str = ""
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Event(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12], primary_key=True)
    title: str
    start_datetime: str
    end_datetime: Optional[str] = None
    description: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JournalEntry(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], primary_key=True)
    date: str = Field(index=True, unique=True)  # YYYY-MM-DD
    mood: int = Field(default=3)  # 1 to 5 scale
    content: str = Field(default="")
    tags: Optional[str] = Field(default="")  # comma-separated
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

