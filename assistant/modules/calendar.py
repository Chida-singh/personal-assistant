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


def _get_credentials() -> Optional[Credentials]:
	# Load environment variables so client ID/secret can come from .env.
	load_dotenv()

	client_id = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("Google_calendar")
	client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
	redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost")

	# OAuth desktop flow requires both client ID and client secret.
	if not client_id or not client_secret:
		return None

	creds: Optional[Credentials] = None

	# Reuse an existing token when available to avoid logging in every run.
	if TOKEN_PATH.exists():
		try:
			creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
		except Exception:
			creds = None

	# Refresh an expired token if a refresh token exists.
	if creds and creds.expired and creds.refresh_token:
		try:
			creds.refresh(Request())
		except Exception:
			creds = None

	# If no valid token exists, run the browser-based OAuth flow.
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

	# Persist token credentials so future calls can run without re-auth.
	TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
	return creds


def _get_service():
	# Build a Calendar API service object from the active credentials.
	creds = _get_credentials()
	if not creds:
		return None
	return build("calendar", "v3", credentials=creds)


def check_events(date: str) -> str:
	# Read events for the requested date from the primary Google Calendar.
	service = _get_service()
	if not service:
		return "Google Calendar is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env."

	try:
		target_date = dt.fromisoformat(date).date()
	except ValueError:
		return "Invalid date format. Use YYYY-MM-DD."

	start_of_day = dt.combine(target_date, dt.min.time(), tzinfo=timezone.utc)
	end_of_day = start_of_day + timedelta(days=1)

	try:
		result = service.events().list(
			calendarId="primary",
			timeMin=start_of_day.isoformat(),
			timeMax=end_of_day.isoformat(),
			singleEvents=True,
			orderBy="startTime",
		).execute()
		items = result.get("items", [])
	except HttpError:
		return "Could not read calendar events right now."

	if not items:
		return f"You have no events on {date}."

	# Build a simple readable list of up to two event summaries with start times.
	descriptions = []
	for item in items[:2]:
		summary = item.get("summary", "Untitled event")
		start_info = item.get("start", {})
		start_value = start_info.get("dateTime", start_info.get("date", "all day"))
		time_label = "all day"
		if "T" in start_value:
			try:
				parsed = dt.fromisoformat(start_value.replace("Z", "+00:00"))
				time_label = parsed.strftime("%I:%M %p").lstrip("0").lower()
			except ValueError:
				time_label = start_value
		descriptions.append(f"{summary} at {time_label}")

	if len(items) == 1:
		return f"You have 1 event on {date}: {descriptions[0]}."

	return f"You have {len(items)} events on {date}: {descriptions[0]}, {descriptions[1]}."


def create_event(title: str, datetime: str) -> str:
	# Create a one-hour event in the primary Google Calendar.
	service = _get_service()
	if not service:
		return "Google Calendar is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env."

	try:
		start_time = dt.fromisoformat(datetime)
	except ValueError:
		return "Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS."

	# Assume UTC if timezone information is not provided by the caller.
	if start_time.tzinfo is None:
		start_time = start_time.replace(tzinfo=timezone.utc)

	end_time = start_time + timedelta(hours=1)
	event_body = {
		"summary": title,
		"start": {"dateTime": start_time.isoformat()},
		"end": {"dateTime": end_time.isoformat()},
	}

	try:
		service.events().insert(calendarId="primary", body=event_body).execute()
	except HttpError:
		return "Could not create the calendar event right now."

	return f"Event '{title}' added on {datetime}."
