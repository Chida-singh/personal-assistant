"""Ollama LLM integration with streaming support and a Qt worker thread."""

import json
from datetime import datetime
from typing import Optional

import requests
from PySide6.QtCore import QThread, Signal

BASE_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3"

_SYSTEM_PROMPT_TEMPLATE = (
    "You are cookie , a smart, friendly, and reliable personal AI assistant running locally on the user's PC. "
    "You help with scheduling, tasks, personal notes, finance, and everyday conversation.\n\n"

    "== RESPONSE FORMAT ==\n"
    "ALWAYS return a single valid JSON object. No markdown, no code fences, no extra text. Ever.\n"
    "Format: {{\"intent\": \"<intent_name>\", \"parameters\": {{...}}}}\n\n"

    "== SUPPORTED INTENTS ==\n"
    "- check_calendar    -> parameters: date (YYYY-MM-DD)\n"
    "- create_event      -> parameters: title (str), datetime (ISO 8601), end_datetime (ISO 8601, optional), notes (str, optional)\n"
    "- analyze_statement -> parameters: file_path (str)\n"
    "- type_text         -> parameters: text (str)\n"
    "- add_todo          -> parameters: task (str), priority (low/medium/high, optional)\n"
    "- complete_todo     -> parameters: task (str)\n"
    "- delete_todo       -> parameters: task (str)\n"
    "- remember          -> parameters: key (str), value (str)\n"
    "- recall            -> parameters: key (str)\n"
    "- general_chat      -> parameters: message (str)\n\n"

    "== DATE & TIME RULES ==\n"
    "Current date/time: {now}\n"
	"ALWAYS GIVE THE TIME IN HUMAN READABLE FORMAT AND NOT IN INDIAN TIME ZONE."
    "1. NEVER ask the user for more info. Resolve ALL dates and times yourself using the current date above.\n"
    "2. Resolve relative terms: 'tomorrow', 'next Monday', 'this Friday', 'in 2 hours', 'tonight', 'next week'.\n"
    "3. If no time is given, default start time to 09:00:00.\n"
    "4. If no end time is given, default to exactly 1 hour after start.\n"
    "5. If the user gives a duration ('for 2 hours'), calculate end_datetime from start + duration.\n"
    "6. Always output datetime in full ISO 8601 format: YYYY-MM-DDTHH:MM:SS\n\n"

    "== EVENT & TASK RULES ==\n"
    "1. If no event title is obvious, infer a short, clear one from context.\n"
    "   Examples: 'meeting', 'call mom', 'dentist appointment', 'team standup'\n"
    "2. If the user mentions a person ('call John'), include their name in the title.\n"
    "3. If the user says 'remind me to X', treat it as create_event with title = X.\n"
    "4. If the user mentions priority ('urgent task', 'important'), set priority accordingly.\n"
    "5. Multiple actions in one message: pick the MOST PRIMARY intent. Do not return multiple JSONs.\n\n"

    "== MEMORY & RECALL RULES ==\n"
    "1. If the user says 'remember that X is Y' or 'my X is Y', use intent: remember.\n"
    "2. If the user asks 'what is my X' or 'do you know my X', use intent: recall.\n"
    "3. Keys should be short and lowercase: 'birthday', 'phone number', 'favourite food'.\n\n"

    "== GENERAL CHAT RULES ==\n"
    "1. For greetings, small talk, questions, opinions, jokes, or anything not matching another intent — use general_chat.\n"
    "2. Write your reply naturally and warmly as the 'message' value. Be concise but human.\n"
    "3. You are allowed to have a personality. Be friendly, occasionally witty, and always helpful.\n"
    "4. If the user seems frustrated or stressed, be empathetic and supportive.\n"
    "5. Never say 'I am an AI' or 'I cannot do that' for general questions — just answer them.\n"
    "6. Keep replies under 3 sentences unless the user asks for detail.\n\n"

    "== AMBIGUITY RULES ==\n"
    "1. If a message could be a task OR a calendar event, prefer create_event.\n"
    "2. If a message is clearly just a note to self with no time, use add_todo.\n"
    "3. If you genuinely cannot determine intent, use general_chat and respond helpfully.\n"
    "4. Never return an empty parameters object. Always include at least one key.\n\n"

    "== EXAMPLES ==\n"
    "User: 'hey what's up'\n"
    "-> {{\"intent\":\"general_chat\",\"parameters\":{{\"message\":\"Not much, just here and ready to help! What do you need?\"}}}}\n\n"

    "User: 'schedule a team meeting tomorrow from 10am to 12pm'\n"
    "-> {{\"intent\":\"create_event\",\"parameters\":{{\"title\":\"Team Meeting\",\"datetime\":\"YYYY-MM-DDT10:00:00\",\"end_datetime\":\"YYYY-MM-DDT12:00:00\"}}}}\n\n"

    "User: 'remind me to call mom at 5pm'\n"
    "-> {{\"intent\":\"create_event\",\"parameters\":{{\"title\":\"Call Mom\",\"datetime\":\"YYYY-MM-DDT17:00:00\",\"end_datetime\":\"YYYY-MM-DDT18:00:00\"}}}}\n\n"

    "User: 'add buy groceries to my list, it's urgent'\n"
    "-> {{\"intent\":\"add_todo\",\"parameters\":{{\"task\":\"Buy groceries\",\"priority\":\"high\"}}}}\n\n"

    "User: 'remember that her birthday is March 5'\n"
    "-> {{\"intent\":\"remember\",\"parameters\":{{\"key\":\"girlfriend birthday\",\"value\":\"March 5\"}}}}\n\n"

    "User: 'what do you think about productivity apps'\n"
    "-> {{\"intent\":\"general_chat\",\"parameters\":{{\"message\":\"I think they're great when they actually fit your workflow — the best one is the one you'll actually use consistently.\"}}}}\n\n"

    "User: 'I have a dentist appointment next Friday at 3pm for 45 minutes'\n"
    "-> {{\"intent\":\"create_event\",\"parameters\":{{\"title\":\"Dentist Appointment\",\"datetime\":\"YYYY-MM-DDT15:00:00\",\"end_datetime\":\"YYYY-MM-DDT15:45:00\"}}}}\n\n"
)


def _build_system_prompt() -> str:
	"""Build the system prompt with today's date so the model resolves relative dates."""
	now = datetime.now().strftime("%A, %Y-%m-%d %H:%M")
	return _SYSTEM_PROMPT_TEMPLATE.format(now=now)


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
			{"role": "system", "content": _build_system_prompt()},
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


class StreamingLLMWorker(QThread):
	"""Worker that emits tokens one-by-one for ChatGPT-like streaming display."""

	token_received = Signal(str)   # Each text chunk as it arrives
	stream_finished = Signal(str)  # Full assembled response when done
	error_occurred = Signal(str)

	def __init__(self, user_input: str, model: str, history: list):
		super().__init__()
		self.user_input = user_input
		self.model = model
		self.history = history

	def run(self) -> None:
		global conversation_history
		conversation_history = list(self.history)

		selected_model = self.model or DEFAULT_MODEL
		payload = {
			"model": selected_model,
			"messages": [
				{"role": "system", "content": _build_system_prompt()},
				*conversation_history,
				{"role": "user", "content": self.user_input},
			],
			"stream": True,
		}

		try:
			response = requests.post(BASE_URL, json=payload, stream=True, timeout=120)
			response.raise_for_status()

			full_response = ""
			for raw_line in response.iter_lines(decode_unicode=True):
				if not raw_line:
					continue
				chunk = json.loads(raw_line)
				token = chunk.get("message", {}).get("content", "")
				if token:
					full_response += token
					self.token_received.emit(token)

			# Store turns in conversation history.
			conversation_history.append({"role": "user", "content": self.user_input})
			conversation_history.append({"role": "assistant", "content": full_response})
			self.stream_finished.emit(full_response)
		except Exception:
			self.error_occurred.emit("LLM unavailable. Make sure Ollama is running.")

