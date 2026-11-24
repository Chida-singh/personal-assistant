import uuid
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task: str
    done: bool = Field(default=False)
    priority: str = Field(default="medium") # high, medium, low
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Note(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True)
    value: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Habit(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], primary_key=True)
    name: str
    type: str = Field(default="checkbox") # checkbox, number
    order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HabitLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True) # YYYY-MM-DD
    habit_id: str = Field(index=True)
    value: str # stored as json string (e.g. "true", "false", "12.5")
    created_at: datetime = Field(default_factory=datetime.utcnow)

