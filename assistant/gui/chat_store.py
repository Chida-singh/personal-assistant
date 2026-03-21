"""Multi-conversation state manager with persistent storage."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONVERSATIONS_FILE = DATA_DIR / "conversations.json"


class ChatMessage:
	"""A single message in a conversation."""

	def __init__(self, role: str, content: str, msg_id: str = "", timestamp: float = 0):
		self.id = msg_id or str(uuid.uuid4())[:8]
		self.role = role
		self.content = content
		self.timestamp = timestamp or datetime.now().timestamp()

	def to_dict(self) -> dict:
		return {
			"id": self.id,
			"role": self.role,
			"content": self.content,
			"timestamp": self.timestamp,
		}

	@classmethod
	def from_dict(cls, data: dict) -> "ChatMessage":
		return cls(
			role=data.get("role", "user"),
			content=data.get("content", ""),
			msg_id=data.get("id", ""),
			timestamp=data.get("timestamp", 0),
		)


class ChatSession:
	"""A single conversation with its own message history."""

	def __init__(self, session_id: str = "", title: str = "New Chat", messages: list = None,
				 created_at: float = 0):
		self.id = session_id or str(uuid.uuid4())[:12]
		self.title = title
		self.messages: list[ChatMessage] = messages or []
		self.created_at = created_at or datetime.now().timestamp()

	def add_message(self, role: str, content: str) -> ChatMessage:
		msg = ChatMessage(role, content)
		self.messages.append(msg)
		# Auto-title from first user message.
		if role == "user" and self.title == "New Chat":
			self.title = content[:40] + ("..." if len(content) > 40 else "")
		return msg

	def get_history_dicts(self) -> list[dict[str, str]]:
		"""Return messages as simple {role, content} dicts for the LLM."""
		return [{"role": m.role, "content": m.content} for m in self.messages]

	def clear(self) -> None:
		self.messages.clear()

	def to_dict(self) -> dict:
		return {
			"id": self.id,
			"title": self.title,
			"messages": [m.to_dict() for m in self.messages],
			"created_at": self.created_at,
		}

	@classmethod
	def from_dict(cls, data: dict) -> "ChatSession":
		messages = [ChatMessage.from_dict(m) for m in data.get("messages", [])]
		return cls(
			session_id=data.get("id", ""),
			title=data.get("title", "New Chat"),
			messages=messages,
			created_at=data.get("created_at", 0),
		)


class ChatStore:
	"""Manages multiple chat sessions with persistence."""

	def __init__(self):
		self.sessions: list[ChatSession] = []
		self.active_session_id: str = ""
		self._load()

		# Ensure at least one session exists.
		if not self.sessions:
			self.new_session()

	@property
	def active_session(self) -> Optional[ChatSession]:
		for s in self.sessions:
			if s.id == self.active_session_id:
				return s
		return self.sessions[0] if self.sessions else None

	def new_session(self) -> ChatSession:
		session = ChatSession()
		self.sessions.insert(0, session)
		self.active_session_id = session.id
		self.save()
		return session

	def switch_to(self, session_id: str) -> Optional[ChatSession]:
		for s in self.sessions:
			if s.id == session_id:
				self.active_session_id = session_id
				return s
		return None

	def delete_session(self, session_id: str) -> None:
		self.sessions = [s for s in self.sessions if s.id != session_id]
		if self.active_session_id == session_id:
			if self.sessions:
				self.active_session_id = self.sessions[0].id
			else:
				self.new_session()
		self.save()

	def rename_session(self, session_id: str, new_title: str) -> None:
		for s in self.sessions:
			if s.id == session_id:
				s.title = new_title
				break
		self.save()

	def save(self) -> None:
		DATA_DIR.mkdir(parents=True, exist_ok=True)
		data = {
			"active_session_id": self.active_session_id,
			"sessions": [s.to_dict() for s in self.sessions],
		}
		with CONVERSATIONS_FILE.open("w", encoding="utf-8") as f:
			json.dump(data, f, indent=2)

	def _load(self) -> None:
		if not CONVERSATIONS_FILE.exists():
			return
		try:
			with CONVERSATIONS_FILE.open("r", encoding="utf-8") as f:
				data = json.load(f)
			self.sessions = [ChatSession.from_dict(s) for s in data.get("sessions", [])]
			self.active_session_id = data.get("active_session_id", "")
		except (json.JSONDecodeError, OSError):
			self.sessions = []
