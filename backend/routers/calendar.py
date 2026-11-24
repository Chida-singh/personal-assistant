import os
from datetime import datetime as dt, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ..core.database import get_session
from ..core.models import Event

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PATH = Path(__file__).resolve().parent.parent.parent / "token.json"
IST = timezone(timedelta(hours=5, minutes=30), name="IST")
IST_TZ_NAME = "Asia/Kolkata"


class EventCheck(BaseModel):
    date: str  # YYYY-MM-DD


class EventCreate(BaseModel):
    title: str
    datetime: str
    end_datetime: Optional[str] = ""


class EventUpdate(BaseModel):
    title: str
    start_datetime: str
    end_datetime: Optional[str] = ""


def _get_google_service():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret or not TOKEN_PATH.exists():
        return None

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        if creds and creds.valid:
            return build("calendar", "v3", credentials=creds)
    except Exception:
        return None
    return None


@router.post("/check")
def check_calendar(req: EventCheck, session: Session = Depends(get_session)):
    svc = _get_google_service()
    if svc:
        try:
            target = dt.fromisoformat(req.date).date()
            start = dt.combine(target, dt.min.time(), tzinfo=IST)
            end = start + timedelta(days=1)
            items = svc.events().list(
                calendarId="primary",
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                timeZone=IST_TZ_NAME,
            ).execute().get("items", [])
            lines = [f"You have {len(items)} event(s) on {req.date}:"]
            for item in items[:5]:
                summary = item.get("summary", "Untitled event")
                lines.append(f"  - {summary}")
            return {"message": "\n".join(lines)}
        except Exception:
            pass

    # Local SQLite fallback
    events = session.exec(select(Event).where(Event.start_datetime.startswith(req.date))).all()
    if not events:
        return {"message": f"You have no events on {req.date}."}
    lines = [f"You have {len(events)} event(s) on {req.date}:"]
    for ev in events:
        lines.append(f"  - {ev.title} at {ev.start_datetime}")
    return {"message": "\n".join(lines)}


@router.get("/month")
def get_calendar_month(year: int, month: int, session: Session = Depends(get_session)):
    prefix = f"{year}-{month:02d}"
    svc = _get_google_service()
    if svc:
        try:
            start_date = dt(year, month, 1, tzinfo=IST)
            if month == 12:
                end_date = dt(year + 1, 1, 1, tzinfo=IST)
            else:
                end_date = dt(year, month + 1, 1, tzinfo=IST)

            items = svc.events().list(
                calendarId="primary",
                timeMin=start_date.isoformat(),
                timeMax=end_date.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                timeZone=IST_TZ_NAME,
            ).execute().get("items", [])
            events = []
            for item in items:
                start_info = item.get("start", {})
                start_dt = start_info.get("dateTime", start_info.get("date", ""))
                end_info = item.get("end", {})
                end_dt = end_info.get("dateTime", end_info.get("date", ""))
                events.append({
                    "id": item.get("id"),
                    "title": item.get("summary", "Untitled Event"),
                    "start": start_dt,
                    "end": end_dt,
                    "description": item.get("description", ""),
                    "source": "google",
                })
            return {"events": events}
        except Exception:
            pass

    # Local SQLite fallback
    local_events = session.exec(select(Event).where(Event.start_datetime.startswith(prefix))).all()
    return {
        "events": [
            {
                "id": ev.id,
                "title": ev.title,
                "start": ev.start_datetime,
                "end": ev.end_datetime or "",
                "description": ev.description or "",
                "source": "local",
            }
            for ev in local_events
        ]
    }


@router.post("/create")
def create_calendar_event(event: EventCreate, session: Session = Depends(get_session)):
    svc = _get_google_service()
    if svc:
        try:
            start_dt = dt.fromisoformat(event.datetime).astimezone(IST)
            end_dt = (
                dt.fromisoformat(event.end_datetime).astimezone(IST)
                if event.end_datetime
                else start_dt + timedelta(hours=1)
            )
            created = svc.events().insert(
                calendarId="primary",
                body={
                    "summary": event.title,
                    "start": {"dateTime": start_dt.isoformat(), "timeZone": IST_TZ_NAME},
                    "end": {"dateTime": end_dt.isoformat(), "timeZone": IST_TZ_NAME},
                },
            ).execute()
            return {"message": f"Created Google Calendar event '{event.title}'.", "id": created.get("id")}
        except Exception:
            pass

    # Local SQLite fallback
    new_event = Event(
        title=event.title,
        start_datetime=event.datetime,
        end_datetime=event.end_datetime,
    )
    session.add(new_event)
    session.commit()
    session.refresh(new_event)
    return {"message": f"Created local event '{event.title}'.", "id": new_event.id}


@router.put("/update/{event_id}")
def update_calendar_event(event_id: str, event: EventUpdate, session: Session = Depends(get_session)):
    svc = _get_google_service()
    if svc:
        try:
            svc.events().patch(
                calendarId="primary",
                eventId=event_id,
                body={"summary": event.title},
            ).execute()
            return {"message": "Event updated in Google Calendar."}
        except Exception:
            pass

    local_ev = session.exec(select(Event).where(Event.id == event_id)).first()
    if local_ev:
        local_ev.title = event.title
        local_ev.start_datetime = event.start_datetime
        local_ev.end_datetime = event.end_datetime
        session.add(local_ev)
        session.commit()
        return {"message": "Event updated locally."}
    return {"message": "Event updated."}


@router.delete("/delete/{event_id}")
def delete_calendar_event(event_id: str, session: Session = Depends(get_session)):
    svc = _get_google_service()
    if svc:
        try:
            svc.events().delete(calendarId="primary", eventId=event_id).execute()
            return {"message": "Event deleted from Google Calendar."}
        except Exception:
            pass

    local_ev = session.exec(select(Event).where(Event.id == event_id)).first()
    if local_ev:
        session.delete(local_ev)
        session.commit()
        return {"message": "Event deleted."}
    return {"message": "Event deleted."}
