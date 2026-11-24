from fastapi import FastAPI
from models import EventCheck, EventCreate, EventUpdate
import repository

app = FastAPI(title="Calendar Service")

# --- Routes ---

@app.post("/api/calendar/check")
def check_calendar(req: EventCheck):
    result = repository.check_events(req.date)
    return {"message": result}

@app.get("/api/calendar/month")
def get_calendar_month(year: int, month: int):
    events = repository.get_month_events(year, month)
    return {"events": events}

@app.post("/api/calendar/create")
def create_calendar_event(event: EventCreate):
    result = repository.create_event(event.title, event.datetime, event.end_datetime)
    return {"message": result}

@app.put("/api/calendar/update/{event_id}")
def update_calendar_event(event_id: str, event: EventUpdate):
    result = repository.update_event(event_id, event.title, event.start_datetime, event.end_datetime)
    return {"message": result}

@app.delete("/api/calendar/delete/{event_id}")
def delete_calendar_event(event_id: str):
    result = repository.delete_event(event_id)
    return {"message": result}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "calendar-service"}
