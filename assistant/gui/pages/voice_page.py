"""Voice reply tab with local transcription and quick send actions."""

import pyperclip
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
	QHBoxLayout,
	QLabel,
	QPushButton,
	QTextEdit,
	QVBoxLayout,
	QWidget,
)

from core.voice import VoiceRecorder
from modules.automation import type_text


class VoiceWorker(QThread):
	result_ready = Signal(str)
	def run(self) -> None:
		recorder = VoiceRecorder()
		self.result_ready.emit(recorder.record_and_transcribe())


class VoiceReplyTab(QWidget):
	"""Voice-to-text tab for quickly drafting replies."""

	def __init__(self) -> None:
		super().__init__()
		self.setStyleSheet("background: #111;")
		self.voice_worker: VoiceWorker | None = None

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(16, 16, 16, 16)
		main_layout.setSpacing(14)

		title = QLabel("Voice Reply")
		title.setStyleSheet("font-size: 18px; font-weight: 700; color: #ccc;")
		main_layout.addWidget(title)

		instructions = QLabel("Press the mic, speak your message, then copy and paste anywhere.")
		instructions.setStyleSheet("color: #555; font-size: 13px; background: transparent;")
		main_layout.addWidget(instructions)

		# Mic button.
		mic_row = QHBoxLayout()
		mic_row.addStretch(1)

		self.mic_button = QPushButton("Tap to speak")
		self.mic_button.setFixedSize(120, 120)
		self.mic_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.mic_button.setStyleSheet(self._mic_idle_style())
		self.mic_button.clicked.connect(self.start_recording)
		mic_row.addWidget(self.mic_button)

		mic_row.addStretch(1)
		main_layout.addLayout(mic_row)

		# Transcription box.
		self.transcription_box = QTextEdit()
		self.transcription_box.setReadOnly(True)
		self.transcription_box.setPlaceholderText("Your words will appear here...")
		self.transcription_box.setStyleSheet(
			"QTextEdit {"
			"background: #1a1a1a; color: #ccc;"
			"border: 1px solid #222; border-radius: 10px;"
			"padding: 14px; font-size: 14px;"
			"}"
		)
		main_layout.addWidget(self.transcription_box, 1)

		# Action buttons.
		actions_row = QHBoxLayout()
		actions_row.setSpacing(8)

		self.copy_button = QPushButton("Copy")
		self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.copy_button.clicked.connect(self.copy_text)

		self.auto_type_button = QPushButton("Auto-Type")
		self.auto_type_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.auto_type_button.clicked.connect(self.auto_type_text)

		self.clear_button = QPushButton("Clear")
		self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.clear_button.clicked.connect(self.clear_text)

		for button in (self.copy_button, self.auto_type_button):
			button.setStyleSheet(
				"QPushButton {"
				"background: #333; color: #ccc; border: none;"
				"border-radius: 8px; padding: 10px 18px;"
				"font-size: 13px; font-weight: 600;"
				"}"
				"QPushButton:hover { background: #444; }"
			)

		self.clear_button.setStyleSheet(
			"QPushButton {"
			"background: transparent; color: #555;"
			"border: 1px solid #2a2a2a; border-radius: 8px;"
			"padding: 10px 18px; font-size: 13px; font-weight: 600;"
			"}"
			"QPushButton:hover { background: #1a0a0a; color: #c55; border-color: #c55; }"
		)

		actions_row.addWidget(self.copy_button)
		actions_row.addWidget(self.auto_type_button)
		actions_row.addWidget(self.clear_button)
		main_layout.addLayout(actions_row)

	def start_recording(self) -> None:
		self.mic_button.setEnabled(False)
		self.mic_button.setText("Listening...")
		self.mic_button.setStyleSheet(self._mic_recording_style())
		self.voice_worker = VoiceWorker()
		self.voice_worker.result_ready.connect(self.on_transcription_ready)
		self.voice_worker.finished.connect(self.reset_mic_button)
		self.voice_worker.start()

	def on_transcription_ready(self, text: str) -> None:
		self.transcription_box.setPlainText(text)

	def reset_mic_button(self) -> None:
		self.mic_button.setEnabled(True)
		self.mic_button.setText("Tap to speak")
		self.mic_button.setStyleSheet(self._mic_idle_style())

	def copy_text(self) -> None:
		pyperclip.copy(self.transcription_box.toPlainText())

	def auto_type_text(self) -> None:
		text = self.transcription_box.toPlainText().strip()
		if text:
			type_text(text)

	def clear_text(self) -> None:
		self.transcription_box.clear()

	@staticmethod
	def _mic_idle_style() -> str:
		return (
			"QPushButton {"
			"background: #222; color: #888;"
			"border: 2px solid #333; border-radius: 60px;"
			"font-size: 13px; font-weight: 600; padding: 8px;"
			"}"
			"QPushButton:hover { border-color: #555; color: #ccc; }"
		)

	@staticmethod
	def _mic_recording_style() -> str:
		return (
			"QPushButton {"
			"background: #2a1111; color: #c55;"
			"border: 2px solid #c55; border-radius: 60px;"
			"font-size: 13px; font-weight: 600; padding: 8px;"
			"}"
		)
