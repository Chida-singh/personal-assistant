"""Google Calendar helpers using OAuth 2.0 Desktop flow."""

import os
from datetime import datetime as dt
from datetime import timedelta, timezone
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


def _get_credentials() -> Optional[Credentials]:
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
		client_config = {
			"installed": {
				"client_id": client_id,
				"client_secret": client_secret,
				"auth_uri": "https://accounts.google.com/o/oauth2/auth",
				"token_uri": "https://oauth2.googleapis.com/token",
				"redirect_uris": [redirect_uri],
			}
		}
		flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
		creds = flow.run_local_server(port=0)

	TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
	return creds


def _get_service():
	creds = _get_credentials()
	if not creds:
		return None
	return build("calendar", "v3", credentials=creds)


def check_events(date: str) -> str:
	service = _get_service()
	if not service:
		return "Google Calendar is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env."

	try:
		target_date = dt.fromisoformat(date).date()
	except ValueError:
		return "Invalid date format. Use YYYY-MM-DD."

	start_of_day = dt.combine(target_date, dt.min.time(), tzinfo=IST)
	end_of_day = start_of_day + timedelta(days=1)

	try:
		result = service.events().list(
			calendarId="primary",
			timeMin=start_of_day.isoformat(),
			timeMax=end_of_day.isoformat(),
			singleEvents=True,
			orderBy="startTime",
			timeZone=IST_TZ_NAME,
		).execute()
		items = result.get("items", [])
	except HttpError:
		return "Could not read calendar events right now."

	if not items:
		readable_date = target_date.strftime("%A, %B %d").replace(" 0", " ")
		return f"You have no events on {readable_date}."

	descriptions = []
	for item in items[:5]:
		summary = item.get("summary", "Untitled event")
		start_info = item.get("start", {})
		start_value = start_info.get("dateTime", start_info.get("date", "all day"))
		time_label = "all day"
		if "T" in start_value:
			try:
				parsed = dt.fromisoformat(start_value.replace("Z", "+00:00"))
				if parsed.tzinfo is not None:
					parsed = parsed.astimezone(IST)
				time_label = parsed.strftime("%I:%M %p").lstrip("0").lower()
			except ValueError:
				time_label = start_value
		descriptions.append(f"  - {summary} at {time_label}")

	count = len(items)
	readable_date = target_date.strftime("%A, %B %d").replace(" 0", " ")
	lines = [f"You have {count} event{'s' if count > 1 else ''} on {readable_date}:"]
	lines.extend(descriptions)
	return "\n".join(lines)


def create_event(title: str, datetime: str, end_datetime: str = "") -> str:
	service = _get_service()
	if not service:
		return "Google Calendar is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env."

	try:
		start_time = dt.fromisoformat(datetime)
	except ValueError:
		return "Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS."

	if start_time.tzinfo is None:
		# Treat user-provided naive datetime as IST.
		start_time = start_time.replace(tzinfo=IST)
	else:
		start_time = start_time.astimezone(IST)

	if end_datetime:
		try:
			end_time = dt.fromisoformat(end_datetime)
			if end_time.tzinfo is None:
				end_time = end_time.replace(tzinfo=IST)
			else:
				end_time = end_time.astimezone(IST)
		except ValueError:
			end_time = start_time + timedelta(hours=1)
	else:
		end_time = start_time + timedelta(hours=1)

	event_body = {
		"summary": title,
		"start": {"dateTime": start_time.isoformat(), "timeZone": IST_TZ_NAME},
		"end": {"dateTime": end_time.isoformat(), "timeZone": IST_TZ_NAME},
	}

	try:
		service.events().insert(calendarId="primary", body=event_body).execute()
	except HttpError:
		return "Could not create the calendar event right now."

	time_str = start_time.strftime("%I:%M %p").lstrip("0").lower()
	end_str = end_time.strftime("%I:%M %p").lstrip("0").lower()
	date_str = start_time.strftime("%A, %B %d").replace(" 0", " ")
	return f"Event '{title}' scheduled for {date_str} — {time_str} to {end_str}."

