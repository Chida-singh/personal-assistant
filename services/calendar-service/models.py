from pydantic import BaseModel

class EventCheck(BaseModel):
    date: str

class EventCreate(BaseModel):
    title: str
    datetime: str
    end_datetime: str = ""

class EventUpdate(BaseModel):
    title: str
    start_datetime: str
    end_datetime: str
