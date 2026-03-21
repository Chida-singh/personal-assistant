"""Automation helpers for typing text into the currently focused field."""

import time

import pyautogui


def type_text(text: str) -> str:
	# Gives the user time to focus WhatsApp or any other target text field.
	time.sleep(2)

	try:
		# Safety note: This types at wherever the cursor is currently focused.
		pyautogui.typewrite(text, interval=0.03)
		return f"Typed successfully. ({len(text)} characters)"
	except Exception:
		return "Typing failed. Make sure a text field is focused."
