"""Personal notes tab for storing and querying relationship details."""

import json

from PySide6.QtCore import Qt
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
		self.setStyleSheet("background: #111;")

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(16, 16, 16, 16)
		main_layout.setSpacing(12)

		self.title_label = QLabel("About Her")
		self.title_label.setStyleSheet(
			"font-size: 18px; font-weight: 700; color: #ccc;"
		)
		main_layout.addWidget(self.title_label)

		# Save note form.
		form_container = QWidget()
		form_container.setStyleSheet(
			"QWidget { background: #1a1a1a; border: 1px solid #222; border-radius: 10px; }"
		)
		form_inner = QVBoxLayout(form_container)
		form_inner.setContentsMargins(14, 12, 14, 12)
		form_inner.setSpacing(8)

		form_title = QLabel("SAVE A NOTE")
		form_title.setStyleSheet(
			"color: #555; font-size: 10px; font-weight: 700;"
			"letter-spacing: 1px; background: transparent; border: none;"
		)
		form_inner.addWidget(form_title)

		form_row = QHBoxLayout()
		form_row.setSpacing(8)

		self.key_input = QLineEdit()
		self.key_input.setPlaceholderText("e.g. birthday, favourite food")
		self.key_input.setStyleSheet(self._input_style())

		self.value_input = QLineEdit()
		self.value_input.setPlaceholderText("e.g. March 5, Pasta")
		self.value_input.setStyleSheet(self._input_style())

		self.save_button = QPushButton("Save")
		self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.save_button.setStyleSheet(self._btn_style())
		self.save_button.clicked.connect(self.save_note)

		form_row.addWidget(self.key_input, 1)
		form_row.addWidget(self.value_input, 1)
		form_row.addWidget(self.save_button)
		form_inner.addLayout(form_row)
		main_layout.addWidget(form_container)

		# Ask section.
		ask_container = QWidget()
		ask_container.setStyleSheet(
			"QWidget { background: #1a1a1a; border: 1px solid #222; border-radius: 10px; }"
		)
		ask_inner = QVBoxLayout(ask_container)
		ask_inner.setContentsMargins(14, 12, 14, 12)
		ask_inner.setSpacing(8)

		ask_title = QLabel("ASK ABOUT HER")
		ask_title.setStyleSheet(
			"color: #555; font-size: 10px; font-weight: 700;"
			"letter-spacing: 1px; background: transparent; border: none;"
		)
		ask_inner.addWidget(ask_title)

		ask_row = QHBoxLayout()
		ask_row.setSpacing(8)

		self.ask_input = QLineEdit()
		self.ask_input.setPlaceholderText("Ask something... e.g. What does she like?")
		self.ask_input.setStyleSheet(self._input_style())
		self.ask_input.returnPressed.connect(self.ask_question)

		self.ask_button = QPushButton("Ask")
		self.ask_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.ask_button.setStyleSheet(self._btn_style())
		self.ask_button.clicked.connect(self.ask_question)

		ask_row.addWidget(self.ask_input, 1)
		ask_row.addWidget(self.ask_button)
		ask_inner.addLayout(ask_row)

		self.response_label = QLabel("")
		self.response_label.setWordWrap(True)
		self.response_label.setStyleSheet(
			"color: #ccc; background: #1a1a1a;"
			"border: 1px solid #2a2a2a; border-radius: 8px;"
			"padding: 12px; font-size: 13px;"
		)
		self.response_label.hide()
		ask_inner.addWidget(self.response_label)

		main_layout.addWidget(ask_container)

		# Empty state.
		self.empty_label = QLabel("No notes yet — save something above")
		self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.empty_label.setStyleSheet(
			"color: #444; font-size: 13px; padding: 30px 0; background: transparent;"
		)
		self.empty_label.hide()
		main_layout.addWidget(self.empty_label)

		# Notes list.
		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

		self.notes_container = QWidget()
		self.notes_layout = QVBoxLayout(self.notes_container)
		self.notes_layout.setContentsMargins(0, 0, 0, 0)
		self.notes_layout.setSpacing(6)
		self.notes_layout.addStretch()

		self.scroll_area.setWidget(self.notes_container)
		main_layout.addWidget(self.scroll_area, 1)

		self.load_notes()

	def load_notes(self) -> None:
		self.refresh()

	def save_note(self) -> None:
		key = self.key_input.text().strip()
		value = self.value_input.text().strip()
		if not key or not value:
			return
		girlfriend.remember(key, value)
		self.key_input.clear()
		self.value_input.clear()
		self.refresh()

	def delete_note(self, key: str) -> None:
		notes = load(GIRLFRIEND_FILE)
		target = key.strip().lower()
		filtered = [item for item in notes if str(item.get("key", "")).strip().lower() != target]
		save(GIRLFRIEND_FILE, filtered)
		self.refresh()

	def ask_question(self) -> None:
		question = self.ask_input.text().strip()
		if not question:
			return
		notes = girlfriend.get_all()
		prompt = f"Based on these notes: {json.dumps(notes)}, answer: {question}"
		try:
			llm_output = llm.send_message(prompt)
			answer = router.route(llm_output)
			self.response_label.setText(answer)
			self.response_label.show()
		except Exception:
			self.response_label.setText("Couldn't get an answer right now.")
			self.response_label.show()

	def refresh(self) -> None:
		while self.notes_layout.count() > 1:
			item = self.notes_layout.takeAt(0)
			widget = item.widget()
			if widget:
				widget.deleteLater()

		all_notes = girlfriend.get_all()
		self.empty_label.setVisible(len(all_notes) == 0)
		self.scroll_area.setVisible(len(all_notes) > 0)

		for item in all_notes:
			key = str(item.get("key", ""))
			value = str(item.get("value", ""))

			row_widget = QWidget()
			row_widget.setStyleSheet(
				"QWidget {"
				"background: #1a1a1a; border: 1px solid #222;"
				"border-left: 3px solid #555; border-radius: 8px;"
				"}"
			)
			row_layout = QHBoxLayout(row_widget)
			row_layout.setContentsMargins(14, 10, 14, 10)
			row_layout.setSpacing(10)

			key_label = QLabel(key)
			key_label.setStyleSheet(
				"color: #aaa; font-weight: 700; font-size: 13px;"
				"background: transparent; border: none;"
			)

			value_label = QLabel(value)
			value_label.setWordWrap(True)
			value_label.setStyleSheet(
				"color: #888; font-size: 13px; background: transparent; border: none;"
			)

			delete_button = QPushButton("x")
			delete_button.setFixedSize(24, 24)
			delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
			delete_button.setStyleSheet(
				"QPushButton {"
				"background: transparent; color: #444; border: none;"
				"border-radius: 12px; font-size: 11px; font-weight: 700;"
				"}"
				"QPushButton:hover { background: #2a1111; color: #c55; }"
			)
			delete_button.clicked.connect(lambda _=False, k=key: self.delete_note(k))

			row_layout.addWidget(key_label)
			row_layout.addWidget(value_label, 1)
			row_layout.addWidget(delete_button)

			self.notes_layout.insertWidget(self.notes_layout.count() - 1, row_widget)

	@staticmethod
	def _input_style() -> str:
		return (
			"QLineEdit {"
			"background: #111; border: 1px solid #2a2a2a; border-radius: 8px;"
			"color: #ccc; padding: 8px 12px; font-size: 13px;"
			"}"
			"QLineEdit:focus { border-color: #444; }"
		)

	@staticmethod
	def _btn_style() -> str:
		return (
			"QPushButton {"
			"background: #333; color: #ccc; border-radius: 8px;"
			"padding: 8px 18px; font-weight: 600; font-size: 13px; border: none;"
			"}"
			"QPushButton:hover { background: #444; }"
		)
