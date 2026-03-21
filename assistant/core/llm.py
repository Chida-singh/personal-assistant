"""Ollama LLM integration with streaming support and a Qt worker thread."""

import json
from typing import Optional

import requests
from PySide6.QtCore import QThread, Signal

BASE_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3"

SYSTEM_PROMPT = (
	"You are a smart personal assistant. When given a user command, "
	"return ONLY a valid JSON object with no extra text or markdown fences.\n\n"
	"Supported intents:\n"
	"- check_calendar    -> parameters: date (YYYY-MM-DD)\n"
	"- create_event      -> parameters: title, datetime (ISO 8601)\n"
	"- analyze_statement -> parameters: file_path\n"
	"- type_text         -> parameters: text\n"
	"- add_todo          -> parameters: task\n"
	"- complete_todo     -> parameters: task\n"
	"- delete_todo       -> parameters: task\n"
	"- remember          -> parameters: key, value\n"
	"- recall            -> parameters: key\n"
	"- general_chat      -> parameters: message\n\n"
	"For commands matching one of the specific intents above, return the matching JSON.\n"
	"For everything else (greetings, questions, advice, conversation), return:\n"
	'{ "intent": "general_chat", "parameters": { "message": "<your helpful reply here>" } }\n\n'
	"Important: the \"message\" value must be YOUR actual reply to the user, "
	"not a repetition of what they said. Be helpful and conversational."
)

# Shared conversation history stored as {"role": str, "content": str} entries.
conversation_history: list[dict[str, str]] = []


def configure(base_url: Optional[str] = None, model: Optional[str] = None) -> None:
	# Allow settings UI or callers to update default model and endpoint at runtime.
	global BASE_URL, DEFAULT_MODEL
	if base_url:
		BASE_URL = base_url
	if model:
		DEFAULT_MODEL = model


def send_message(user_input: str, model: Optional[str] = None) -> str:
	# Build the full message list with system prompt, history, and new user input.
	selected_model = model or DEFAULT_MODEL
	payload = {
		"model": selected_model,
		"messages": [
			{"role": "system", "content": SYSTEM_PROMPT},
			*conversation_history,
			{"role": "user", "content": user_input},
		],
		"stream": True,
	}

	# Stream line-delimited JSON chunks from Ollama and assemble full assistant text.
	response = requests.post(BASE_URL, json=payload, stream=True, timeout=120)
	response.raise_for_status()

	full_response = ""
	for raw_line in response.iter_lines(decode_unicode=True):
		if not raw_line:
			continue
		chunk = json.loads(raw_line)
		full_response += chunk.get("message", {}).get("content", "")

	# Store user and assistant turns so later calls include conversation context.
	conversation_history.append({"role": "user", "content": user_input})
	conversation_history.append({"role": "assistant", "content": full_response})
	return full_response


class LLMWorker(QThread):
	"""Background worker for non-blocking LLM calls from the UI."""

	response_ready = Signal(str)
	error_occurred = Signal(str)

	def __init__(self, user_input: str, model: str, history: list):
		super().__init__()
		self.user_input = user_input
		self.model = model
		self.history = history

	def run(self) -> None:
		# Copy provided history into shared state before making the streamed call.
		global conversation_history
		conversation_history = list(self.history)

		try:
			# Reuse send_message so worker and direct calls share one code path.
			full_response = send_message(self.user_input, self.model or DEFAULT_MODEL)
			self.response_ready.emit(full_response)
		except Exception:
			# Surface a user-friendly error when Ollama is not reachable.
			self.error_occurred.emit("LLM unavailable.")
