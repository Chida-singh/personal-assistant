"""Intent router that maps LLM JSON output to assistant module actions."""

import json
import re


def _extract_json(text: str) -> str:
	"""Strip markdown code fences and surrounding whitespace from LLM output.

	Models frequently wrap JSON in ```json ... ``` or ``` ... ``` blocks.
	This helper extracts just the raw JSON so json.loads can parse it cleanly.
	"""
	# Remove ```json ... ``` or ``` ... ``` wrappers (case-insensitive, multiline).
	stripped = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE).replace("```", "")
	return stripped.strip()


def route(llm_output: str, file_path: str = None) -> str:
	# Strip any markdown fences so json.loads receives clean JSON text.
	clean_output = _extract_json(llm_output)

	# Try to parse the model response as JSON; fall back to raw chat on invalid JSON.
	try:
		payload = json.loads(clean_output)
	except (TypeError, json.JSONDecodeError):
		# If the model returned a plain conversational reply, show it directly.
		return clean_output if clean_output else llm_output

	# Extract top-level fields used by all dispatch branches.
	intent = payload.get("intent")
	parameters = payload.get("parameters", {})

	# Handle general chat by returning the message directly.
	if intent == "general_chat":
		return str(parameters.get("message", ""))

	# Dispatch calendar intents.
	if intent == "check_calendar":
		from modules import calendar

		return calendar.check_events(str(parameters.get("date", "")))

	if intent == "create_event":
		from modules import calendar

		return calendar.create_event(
			str(parameters.get("title", "")),
			str(parameters.get("datetime", "")),
		)

	# Dispatch finance intent and prefer explicit route argument when provided.
	if intent == "analyze_statement":
		from modules import finance

		target_path = file_path or parameters.get("file_path", "")
		return finance.analyze(str(target_path))

	# Dispatch typing automation intent.
	if intent == "type_text":
		from modules import automation

		return automation.type_text(str(parameters.get("text", "")))

	# Dispatch todo intents.
	if intent == "add_todo":
		from modules import todo

		return todo.add_todo(str(parameters.get("task", "")))

	if intent == "complete_todo":
		from modules import todo

		return todo.complete_todo(str(parameters.get("task", "")))

	if intent == "delete_todo":
		from modules import todo

		return todo.delete_todo(str(parameters.get("task", "")))

	# Dispatch personal notes intents.
	if intent == "remember":
		from modules import girlfriend

		return girlfriend.remember(
			str(parameters.get("key", "")),
			str(parameters.get("value", "")),
		)

	if intent == "recall":
		from modules import girlfriend

		return girlfriend.recall(str(parameters.get("key", "")))

	# Return a friendly fallback for unknown intents.
	return "I'm not sure how to help with that."
