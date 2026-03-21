"""Personal notes tab for storing and querying relationship details."""

import json

from PySide6.QtWidgets import (
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QPushButton,
	QScrollArea,
	QVBoxLayout,
	QWidget,
)

from core import router
from core import llm
from core.storage import GIRLFRIEND_FILE, load, save
from modules import girlfriend


class GirlfriendTab(QWidget):
	"""UI tab for saving notes and asking contextual questions."""

	def __init__(self) -> None:
		super().__init__()
		self.setStyleSheet("background: #0F172A;")

		# Arrange title, input form, ask section, and notes list vertically.
		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(12, 12, 12, 12)
		main_layout.setSpacing(10)

		self.title_label = QLabel("💕 About Her")
		self.title_label.setStyleSheet(
			"font-family: 'Segoe UI'; font-size: 18px; font-weight: bold; color: #F472B6;"
		)
		main_layout.addWidget(self.title_label)

		# Build note input row: key, value, and save action.
		form_layout = QHBoxLayout()
		form_layout.setSpacing(8)

		self.key_input = QLineEdit()
		self.key_input.setPlaceholderText("e.g. birthday, favourite food")
		self.key_input.setStyleSheet(self._input_style())

		self.value_input = QLineEdit()
		self.value_input.setPlaceholderText("e.g. March 5, Pasta")
		self.value_input.setStyleSheet(self._input_style())

		self.save_button = QPushButton("Save")
		self.save_button.setStyleSheet(self._accent_button_style())
		self.save_button.clicked.connect(self.save_note)

		form_layout.addWidget(self.key_input, 1)
		form_layout.addWidget(self.value_input, 1)
		form_layout.addWidget(self.save_button)
		main_layout.addLayout(form_layout)

		# Build ask row and response label for note-aware conversational help.
		ask_layout = QHBoxLayout()
		ask_layout.setSpacing(8)

		self.ask_input = QLineEdit()
		self.ask_input.setPlaceholderText("Ask something... e.g. What does she like?")
		self.ask_input.setStyleSheet(self._input_style())
		self.ask_input.returnPressed.connect(self.ask_question)

		self.ask_button = QPushButton("Ask")
		self.ask_button.setStyleSheet(self._accent_button_style())
		self.ask_button.clicked.connect(self.ask_question)

		ask_layout.addWidget(self.ask_input, 1)
		ask_layout.addWidget(self.ask_button)
		main_layout.addLayout(ask_layout)

		self.response_label = QLabel("")
		self.response_label.setWordWrap(True)
		self.response_label.setStyleSheet(
			"color: #CBD5E1; background: #1E293B; border-radius: 8px; padding: 10px;"
		)
		main_layout.addWidget(self.response_label)

		# Create a scroll area where each saved note appears as a card row.
		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

		self.notes_container = QWidget()
		self.notes_layout = QVBoxLayout(self.notes_container)
		self.notes_layout.setContentsMargins(0, 0, 0, 0)
		self.notes_layout.setSpacing(8)
		self.notes_layout.addStretch()

		self.scroll_area.setWidget(self.notes_container)
		main_layout.addWidget(self.scroll_area, 1)

		# Load saved notes as soon as the tab opens.
		self.load_notes()

	def load_notes(self) -> None:
		# Read all stored notes and rebuild the visible list.
		self.refresh()

	def save_note(self) -> None:
		# Save or update a note through the module helper, then reload the list.
		key = self.key_input.text().strip()
		value = self.value_input.text().strip()
		if not key or not value:
			return

		girlfriend.remember(key, value)
		self.key_input.clear()
		self.value_input.clear()
		self.refresh()

	def delete_note(self, key: str) -> None:
		# Remove a note by key (case-insensitive) and persist updated storage.
		notes = load(GIRLFRIEND_FILE)
		target = key.strip().lower()
		filtered = [item for item in notes if str(item.get("key", "")).strip().lower() != target]
		save(GIRLFRIEND_FILE, filtered)
		self.refresh()

	def ask_question(self) -> None:
		# Ask LLM using note context and display the routed textual response.
		question = self.ask_input.text().strip()
		if not question:
			return

		notes = girlfriend.get_all()
		prompt = f"Based on these notes: {json.dumps(notes)}, answer: {question}"

		try:
			llm_output = llm.send_message(prompt)
			answer = router.route(llm_output)
			self.response_label.setText(answer)
		except Exception:
			self.response_label.setText("I couldn't get an answer right now.")

	def refresh(self) -> None:
		# Clear current note rows and re-render from latest storage data.
		while self.notes_layout.count() > 1:
			item = self.notes_layout.takeAt(0)
			widget = item.widget()
			if widget:
				widget.deleteLater()

		for item in girlfriend.get_all():
			key = str(item.get("key", ""))
			value = str(item.get("value", ""))

			row_widget = QWidget()
			row_widget.setStyleSheet("background: #1E293B; border-radius: 8px;")
			row_layout = QHBoxLayout(row_widget)
			row_layout.setContentsMargins(10, 8, 10, 8)
			row_layout.setSpacing(8)

			key_label = QLabel(key)
			key_label.setStyleSheet("color: #F472B6; font-weight: bold;")

			value_label = QLabel(value)
			value_label.setWordWrap(True)
			value_label.setStyleSheet("color: #CBD5E1;")

			delete_button = QPushButton("Delete")
			delete_button.setStyleSheet(self._danger_button_style())
			delete_button.clicked.connect(lambda _=False, note_key=key: self.delete_note(note_key))

			row_layout.addWidget(key_label)
			row_layout.addWidget(value_label, 1)
			row_layout.addWidget(delete_button)

			self.notes_layout.insertWidget(self.notes_layout.count() - 1, row_widget)

	@staticmethod
	def _input_style() -> str:
		return (
			"QLineEdit {"
			"background: #1E293B;"
			"border: 1px solid #334155;"
			"border-radius: 8px;"
			"color: #F1F5F9;"
			"padding: 8px 10px;"
			"}"
		)

	@staticmethod
	def _accent_button_style() -> str:
		return (
			"QPushButton {"
			"background: #F472B6;"
			"color: #0F172A;"
			"border-radius: 8px;"
			"padding: 8px 14px;"
			"font-weight: bold;"
			"}"
		)

	@staticmethod
	def _danger_button_style() -> str:
		return (
			"QPushButton {"
			"background: transparent;"
			"color: #FCA5A5;"
			"border: 1px solid #FCA5A5;"
			"border-radius: 6px;"
			"padding: 4px 8px;"
			"}"
			"QPushButton:hover {"
			"background: #7F1D1D;"
			"color: #FEE2E2;"
			"}"
		)
