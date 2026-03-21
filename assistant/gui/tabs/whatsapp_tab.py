"""Voice reply tab with local transcription and quick send actions."""

import pyperclip
from PySide6.QtCore import QThread, Signal
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
	"""Runs microphone recording and transcription off the UI thread."""

	result_ready = Signal(str)

	def run(self) -> None:
		# Record from microphone and emit text when transcription completes.
		recorder = VoiceRecorder()
		self.result_ready.emit(recorder.record_and_transcribe())


class VoiceReplyTab(QWidget):
	"""Voice-to-text tab for quickly drafting replies anywhere."""

	def __init__(self) -> None:
		super().__init__()
		self.setStyleSheet("background: #0F172A;")

		self.voice_worker: VoiceWorker | None = None

		# Build the vertical page layout from title to action buttons.
		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(16, 16, 16, 16)
		main_layout.setSpacing(12)

		# Title for the voice reply feature.
		title = QLabel("🎙️ Voice Reply")
		title.setStyleSheet(
			"font-family: 'Segoe UI'; font-size: 18px; font-weight: 700; color: #F1F5F9;"
		)
		main_layout.addWidget(title)

		# Short helper text that explains the voice reply workflow.
		instructions = QLabel(
			"Press the mic, speak your message, then copy and paste anywhere."
		)
		instructions.setStyleSheet("color: #94A3B8; font-size: 12px;")
		main_layout.addWidget(instructions)

		# Place a large circular microphone button at the center.
		mic_row = QHBoxLayout()
		mic_row.addStretch(1)

		self.mic_button = QPushButton("🎤 Hold to Speak")
		self.mic_button.setFixedSize(120, 120)
		self.mic_button.setStyleSheet(
			"QPushButton {"
			"background: #2563EB;"
			"color: #FFFFFF;"
			"border: none;"
			"border-radius: 60px;"
			"font-family: 'Segoe UI';"
			"font-size: 13px;"
			"font-weight: 600;"
			"padding: 8px;"
			"}"
			"QPushButton:hover {"
			"background: #1D4ED8;"
			"}"
		)
		self.mic_button.clicked.connect(self.start_recording)
		mic_row.addWidget(self.mic_button)

		mic_row.addStretch(1)
		main_layout.addLayout(mic_row)

		# Read-only text box that displays the latest transcription.
		self.transcription_box = QTextEdit()
		self.transcription_box.setReadOnly(True)
		self.transcription_box.setPlaceholderText("Your words will appear here...")
		self.transcription_box.setStyleSheet(
			"QTextEdit {"
			"background: #1E293B;"
			"color: #F1F5F9;"
			"border: 1px solid #334155;"
			"border-radius: 10px;"
			"padding: 10px;"
			"font-size: 13px;"
			"}"
		)
		main_layout.addWidget(self.transcription_box, 1)

		# Action buttons for copy, auto-typing, and clearing the transcript.
		actions_row = QHBoxLayout()
		actions_row.setSpacing(8)

		self.copy_button = QPushButton("📋 Copy to Clipboard")
		self.copy_button.clicked.connect(self.copy_text)

		self.auto_type_button = QPushButton("⌨️ Auto-Type")
		self.auto_type_button.clicked.connect(self.auto_type_text)

		self.clear_button = QPushButton("🗑 Clear")
		self.clear_button.clicked.connect(self.clear_text)

		for button in (self.copy_button, self.auto_type_button, self.clear_button):
			button.setStyleSheet(
				"QPushButton {"
				"background: #2563EB;"
				"color: #FFFFFF;"
				"border: none;"
				"border-radius: 8px;"
				"padding: 8px 12px;"
				"font-family: 'Segoe UI';"
				"font-size: 12px;"
				"font-weight: 600;"
				"}"
				"QPushButton:hover {"
				"background: #1D4ED8;"
				"}"
			)

		actions_row.addWidget(self.copy_button)
		actions_row.addWidget(self.auto_type_button)
		actions_row.addWidget(self.clear_button)
		main_layout.addLayout(actions_row)

	def start_recording(self) -> None:
		# Disable the mic button and show listening state while the worker runs.
		self.mic_button.setEnabled(False)
		self.mic_button.setText("🔴 Listening...")
		self.mic_button.setStyleSheet(
			"QPushButton {"
			"background: #DC2626;"
			"color: #FFFFFF;"
			"border: none;"
			"border-radius: 60px;"
			"font-family: 'Segoe UI';"
			"font-size: 13px;"
			"font-weight: 600;"
			"padding: 8px;"
			"}"
		)

		self.voice_worker = VoiceWorker()
		self.voice_worker.result_ready.connect(self.on_transcription_ready)
		self.voice_worker.finished.connect(self.reset_mic_button)
		self.voice_worker.start()

	def on_transcription_ready(self, text: str) -> None:
		# Update the transcription area with whatever text was captured.
		self.transcription_box.setPlainText(text)

	def reset_mic_button(self) -> None:
		# Restore mic button visuals and enable it for the next recording.
		self.mic_button.setEnabled(True)
		self.mic_button.setText("🎤 Hold to Speak")
		self.mic_button.setStyleSheet(
			"QPushButton {"
			"background: #2563EB;"
			"color: #FFFFFF;"
			"border: none;"
			"border-radius: 60px;"
			"font-family: 'Segoe UI';"
			"font-size: 13px;"
			"font-weight: 600;"
			"padding: 8px;"
			"}"
			"QPushButton:hover {"
			"background: #1D4ED8;"
			"}"
		)

	def copy_text(self) -> None:
		# Copy the full transcription text to system clipboard.
		pyperclip.copy(self.transcription_box.toPlainText())

	def auto_type_text(self) -> None:
		# Use automation helper to type the transcribed message into focused input.
		text = self.transcription_box.toPlainText().strip()
		if text:
			type_text(text)

	def clear_text(self) -> None:
		# Clear transcript so the user can start over with a clean box.
		self.transcription_box.clear()
