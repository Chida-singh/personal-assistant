"""Shared JSON storage helpers for assistant data files."""

import json
from pathlib import Path

TODOS_FILE = "todos.json"
GIRLFRIEND_FILE = "girlfriend.json"
CHAT_FILE = "chat_history.json"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load(filename: str) -> list:
	# Read a JSON list from the data folder and return an empty list on errors.
	file_path = DATA_DIR / filename
	try:
		with file_path.open("r", encoding="utf-8") as file:
			data = json.load(file)
		return data if isinstance(data, list) else []
	except (FileNotFoundError, json.JSONDecodeError, OSError):
		return []


def save(filename: str, data: list) -> None:
	# Persist a Python list to the data folder using pretty JSON formatting.
	file_path = DATA_DIR / filename
	DATA_DIR.mkdir(parents=True, exist_ok=True)
	with file_path.open("w", encoding="utf-8") as file:
		json.dump(data, file, indent=2)
