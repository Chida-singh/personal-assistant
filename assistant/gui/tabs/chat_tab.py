"""Main chat interface tab with text and voice input."""

from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import (
	QHBoxLayout,
	QLineEdit,
	QLabel,
	QPushButton,
	QScrollArea,
	QSizePolicy,
	QVBoxLayout,
	QWidget,
)

from core import router
from core.llm import DEFAULT_MODEL, LLMWorker
from core.storage import CHAT_FILE, load, save
from core.voice import VoiceRecorder
from gui.chat_bubble import ChatBubble


class VoiceWorker(QThread):
	"""Worker thread to keep microphone transcription off the UI thread."""

	result_ready = Signal(str)

	def run(self) -> None:
		# Record audio and emit transcribed text when done.
		recorder = VoiceRecorder()
		self.result_ready.emit(recorder.record_and_transcribe())


class ChatTab(QWidget):
	"""Chat tab that renders bubbles and handles message exchange flow."""

	def __init__(self) -> None:
		super().__init__()
		self.setStyleSheet("background: #0F172A;")

		self.messages: list[dict[str, str]] = []
		self.llm_worker: LLMWorker | None = None
		self.voice_worker: VoiceWorker | None = None

		# Build top-level vertical layout for chat feed, status, and input controls.
		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(12, 12, 12, 12)
		main_layout.setSpacing(10)

		# Create scrollable area that hosts chat bubbles in a vertical stack.
		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

		self.chat_container = QWidget()
		self.chat_layout = QVBoxLayout(self.chat_container)
		self.chat_layout.setContentsMargins(0, 0, 0, 0)
		self.chat_layout.setSpacing(8)
		self.chat_layout.addStretch()

		self.scroll_area.setWidget(self.chat_container)
		main_layout.addWidget(self.scroll_area, 1)

		# Show this status while waiting for the LLM response.
		self.thinking_label = QLabel("Thinking...")
		self.thinking_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
		self.thinking_label.hide()
		main_layout.addWidget(self.thinking_label)

		# Create the bottom input row with text field, send button, and mic button.
		input_layout = QHBoxLayout()
		input_layout.setSpacing(8)

		self.input_edit = QLineEdit()
		self.input_edit.setPlaceholderText("Ask me anything...")
		self.input_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
		self.input_edit.returnPressed.connect(self._on_send_clicked)
		self.input_edit.setStyleSheet(
			"QLineEdit {"
			"background: #1E293B;"
			"border: 1px solid #334155;"
			"border-radius: 8px;"
			"color: #F1F5F9;"
			"padding: 8px 10px;"
			"}"
		)

		self.send_button = QPushButton("Send")
		self.send_button.setStyleSheet(
			"QPushButton {"
			"background: #2563EB;"
			"color: #FFFFFF;"
			"border-radius: 8px;"
			"padding: 8px 14px;"
			"}"
		)
		self.send_button.clicked.connect(self._on_send_clicked)

		self.mic_button = QPushButton("🎤")
		self.mic_button.setStyleSheet(
			"QPushButton {"
			"background: #1E293B;"
			"color: #F1F5F9;"
			"border: 1px solid #334155;"
			"border-radius: 8px;"
			"padding: 8px 12px;"
			"}"
		)
		self.mic_button.clicked.connect(self._on_mic_clicked)

		input_layout.addWidget(self.input_edit)
		input_layout.addWidget(self.send_button)
		input_layout.addWidget(self.mic_button)
		main_layout.addLayout(input_layout)

		# Load previously saved chat turns and render them as bubbles on startup.
		self._load_history()

	def _load_history(self) -> None:
		# Read saved chat messages and restore both internal state and visual bubbles.
		saved_messages = load(CHAT_FILE)
		self.messages = []

		for item in saved_messages:
			role = str(item.get("role", ""))
			content = str(item.get("content", ""))
			if role in {"user", "assistant"} and content:
				self.messages.append({"role": role, "content": content})
				self._add_bubble(content, role)

	def _on_send_clicked(self) -> None:
		# Send text input to the LLM worker and show immediate user feedback.
		user_text = self.input_edit.text().strip()
		if not user_text:
			return

		# Snapshot history BEFORE appending the new user message so the LLM
		# does not receive the same user turn twice (once in history, once as prompt).
		history_snapshot = list(self.messages)

		self._append_message("user", user_text)
		self.input_edit.clear()
		self.thinking_label.show()

		self.llm_worker = LLMWorker(user_text, DEFAULT_MODEL, history_snapshot)
		self.llm_worker.response_ready.connect(self._on_llm_response)
		self.llm_worker.error_occurred.connect(self._on_llm_error)
		self.llm_worker.start()

	def _on_llm_response(self, llm_output: str) -> None:
		# Route the LLM output through intent handling and display final assistant text.
		assistant_text = router.route(llm_output)
		self._append_message("assistant", assistant_text)
		self.thinking_label.hide()

	def _on_llm_error(self, message: str) -> None:
		# Surface worker errors as assistant bubbles to keep UX consistent.
		self._append_message("assistant", message)
		self.thinking_label.hide()

	def _on_mic_clicked(self) -> None:
		# Run voice capture in a background thread and fill the transcribed text on completion.
		self.mic_button.setEnabled(False)
		self.mic_button.setText("🔴 Listening...")

		self.voice_worker = VoiceWorker()
		self.voice_worker.result_ready.connect(self._on_voice_ready)
		self.voice_worker.finished.connect(self._reset_mic_button)
		self.voice_worker.start()

	def _on_voice_ready(self, text: str) -> None:
		# Populate input box with transcribed speech for review before sending.
		self.input_edit.setText(text)

	def _reset_mic_button(self) -> None:
		# Restore mic button state once recording/transcription is complete.
		self.mic_button.setEnabled(True)
		self.mic_button.setText("🎤")

	def _append_message(self, role: str, content: str) -> None:
		# Add message to local history, render bubble, and persist the latest chat state.
		self.messages.append({"role": role, "content": content})
		self._add_bubble(content, role)
		save(CHAT_FILE, self.messages)

	def _add_bubble(self, text: str, role: str) -> None:
		# Insert a bubble before the layout stretch and auto-scroll to the newest message.
		bubble = ChatBubble(text, role)
		stretch_index = self.chat_layout.count() - 1
		self.chat_layout.insertWidget(max(stretch_index, 0), bubble)
		QTimer.singleShot(0, self._scroll_to_bottom)

	def _scroll_to_bottom(self) -> None:
		# Keep the newest message visible after each bubble insertion.
		bar = self.scroll_area.verticalScrollBar()
		bar.setValue(bar.maximum())
