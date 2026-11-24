from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

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
