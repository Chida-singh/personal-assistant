"""Google Calendar helpers using OAuth 2.0 Desktop flow."""

import os
from datetime import datetime as dt, timedelta, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PATH = Path(__file__).resolve().parent.parent / "token.json"
IST = timezone(timedelta(hours=5, minutes=30), name="IST")
IST_TZ_NAME = "Asia/Kolkata"

_NOT_CONFIGURED = "Google Calendar is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env."
_GENERIC_ERROR = "Could not reach Google Calendar right now."


# ── Auth ───────────────────────────────────────────────────────────────────────

def _get_service():
    """Return an authenticated Calendar API client, or None if unconfigured."""
    load_dotenv()
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost")

    if not client_id or not client_secret:
        return None

    creds: Optional[Credentials] = None
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_config(
            {"installed": {
                "client_id": client_id, "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }},
            SCOPES,
        )
        creds = flow.run_local_server(port=0)

    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return build("calendar", "v3", credentials=creds)


def _require_service():
    """Return service or raise RuntimeError with a friendly message."""
    svc = _get_service()
    if not svc:
        raise RuntimeError(_NOT_CONFIGURED)
    return svc


# ── Datetime helpers ───────────────────────────────────────────────────────────

def _to_ist(iso_str: str) -> dt:
    """Parse an ISO datetime string and attach IST timezone."""
    t = dt.fromisoformat(iso_str)
    return t.replace(tzinfo=IST) if t.tzinfo is None else t.astimezone(IST)


def _fmt_time(t: dt) -> str:
    return t.strftime("%I:%M %p").lstrip("0").lower()


def _fmt_date(t: dt) -> str:
    return t.strftime("%A, %B %d").replace(" 0", " ")


# ── Calendar operations ────────────────────────────────────────────────────────

def check_events(date: str) -> str:
    try:
        service = _require_service()
        target = dt.fromisoformat(date).date()
    except RuntimeError as e:
        return str(e)
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD."

    start = dt.combine(target, dt.min.time(), tzinfo=IST)
    end = start + timedelta(days=1)

    try:
        items = service.events().list(
            calendarId="primary",
            timeMin=start.isoformat(), timeMax=end.isoformat(),
            singleEvents=True, orderBy="startTime", timeZone=IST_TZ_NAME,
        ).execute().get("items", [])
    except HttpError:
        return _GENERIC_ERROR

    readable_date = _fmt_date(start)
    if not items:
        return f"You have no events on {readable_date}."

    lines = [f"You have {len(items)} event{'s' if len(items) > 1 else ''} on {readable_date}:"]
    for item in items[:5]:
        summary = item.get("summary", "Untitled event")
        start_info = item.get("start", {})
        raw = start_info.get("dateTime", start_info.get("date", ""))
        time_label = "all day"
        if "T" in raw:
            try:
                time_label = _fmt_time(dt.fromisoformat(raw.replace("Z", "+00:00")).astimezone(IST))
            except ValueError:
                time_label = raw
        lines.append(f"  - {summary} at {time_label}")

    if len(items) > 5:
        extra = len(items) - 5
        lines.append(f"  ...and {extra} more event{'s' if extra > 1 else ''}.")
    return "\n".join(lines)


def create_event(title: str, datetime: str, end_datetime: str = "") -> str:
    try:
        service = _require_service()
        start = _to_ist(datetime)
    except RuntimeError as e:
        return str(e)
    except ValueError:
        return "Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS."

    end = _to_ist(end_datetime) if end_datetime else start + timedelta(hours=1)

    try:
        service.events().insert(
            calendarId="primary",
            body={
                "summary": title,
                "start": {"dateTime": start.isoformat(), "timeZone": IST_TZ_NAME},
                "end": {"dateTime": end.isoformat(), "timeZone": IST_TZ_NAME},
            },
        ).execute()
    except HttpError:
        return _GENERIC_ERROR

    return f"Event '{title}' scheduled for {_fmt_date(start)} — {_fmt_time(start)} to {_fmt_time(end)}."


def delete_event(event_id: str) -> str:
    try:
        service = _require_service()
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return "Event deleted."
    except RuntimeError as e:
        return str(e)
    except HttpError:
        return _GENERIC_ERROR


def update_event(event_id: str, title: str, start_datetime: str, end_datetime: str) -> str:
    try:
        service = _require_service()
        start = _to_ist(start_datetime)
        end = _to_ist(end_datetime)
    except RuntimeError as e:
        return str(e)
    except ValueError:
        return "Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS."

    try:
        service.events().update(
            calendarId="primary", eventId=event_id,
            body={
                "summary": title,
                "start": {"dateTime": start.isoformat(), "timeZone": IST_TZ_NAME},
                "end": {"dateTime": end.isoformat(), "timeZone": IST_TZ_NAME},
            },
        ).execute()
        return "Event updated successfully."
    except HttpError:
        return _GENERIC_ERROR


def get_month_events(year: int, month: int) -> list:
    try:
        service = _require_service()
    except RuntimeError:
        return []

    start = dt(year, month, 1, tzinfo=IST)
    end = dt(year + 1, 1, 1, tzinfo=IST) if month == 12 else dt(year, month + 1, 1, tzinfo=IST)

    try:
        return service.events().list(
            calendarId="primary",
            timeMin=start.isoformat(), timeMax=end.isoformat(),
            singleEvents=True, orderBy="startTime", timeZone=IST_TZ_NAME,
        ).execute().get("items", [])
    except Exception:
        return []
