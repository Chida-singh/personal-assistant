from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class VaultEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    service: str
    username: str = ""
    password: str = ""
    url: str = ""
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
