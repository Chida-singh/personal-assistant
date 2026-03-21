"""Full chat page: header + scrollable message list + input bar."""

import pyperclip
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
	QHBoxLayout,
	QLabel,
	QPushButton,
	QScrollArea,
	QSizePolicy,
	QVBoxLayout,
	QWidget,
)

from core import router
from core.llm import DEFAULT_MODEL, StreamingLLMWorker
from core.voice import VoiceRecorder
from gui.chat_header import ChatHeader
from gui.chat_input import ChatInput
from gui.chat_store import ChatStore
from gui.message_bubble import MessageBubble


class VoiceWorker(QThread):
	result_ready = Signal(str)
	def run(self) -> None:
		recorder = VoiceRecorder()
		self.result_ready.emit(recorder.record_and_transcribe())


class ChatArea(QWidget):
	"""Main chat page with header, scrollable messages, and input."""

	toggle_sidebar_requested = Signal()

	def __init__(self, store: ChatStore) -> None:
		super().__init__()
		self.store = store
		self.setStyleSheet("background: #111;")

		self._llm_worker: StreamingLLMWorker | None = None
		self._voice_worker: VoiceWorker | None = None
		self._thinking_dots = 0

		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

		# Header.
		self.header = ChatHeader()
		self.header.toggle_sidebar.connect(self.toggle_sidebar_requested.emit)
		self.header.clear_chat.connect(self._clear_chat)
		layout.addWidget(self.header)

		# Scrollable message area.
		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setStyleSheet("QScrollArea { border: none; background: #111; }")

		self.messages_container = QWidget()
		self.messages_container.setStyleSheet("background: #111;")
		self.messages_layout = QVBoxLayout(self.messages_container)
		self.messages_layout.setContentsMargins(0, 24, 0, 24)
		self.messages_layout.setSpacing(4)
		self.messages_layout.addStretch()

		self.scroll_area.setWidget(self.messages_container)
		layout.addWidget(self.scroll_area, 1)

		# Typing indicator.
		self.typing_widget = self._build_typing_indicator()
		self.typing_widget.hide()
		layout.addWidget(self.typing_widget)

		self._typing_timer = QTimer(self)
		self._typing_timer.setInterval(350)
		self._typing_timer.timeout.connect(self._animate_typing)

		# Scroll-to-bottom button.
		self._scroll_btn = QPushButton("v")
		self._scroll_btn.setParent(self.scroll_area)
		self._scroll_btn.setFixedSize(32, 32)
		self._scroll_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		self._scroll_btn.setStyleSheet(
			"QPushButton {"
			"background: #222; color: #888; border: 1px solid #333;"
			"border-radius: 16px; font-size: 13px; font-weight: 700;"
			"}"
			"QPushButton:hover { background: #333; color: #ccc; }"
		)
		self._scroll_btn.clicked.connect(self._scroll_to_bottom)
		self._scroll_btn.hide()
		self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)

		# Input bar.
		self.input_bar = ChatInput()
		self.input_bar.message_submitted.connect(self._on_send)
		self.input_bar.mic_clicked.connect(self._on_mic)
		layout.addWidget(self.input_bar)

		self.load_session()

	def load_session(self) -> None:
		while self.messages_layout.count() > 1:
			item = self.messages_layout.takeAt(0)
			if item.widget():
				item.widget().deleteLater()

		session = self.store.active_session
		if not session:
			return

		self.header.set_title(session.title)

		if not session.messages:
			self._show_welcome()
		else:
			for msg in session.messages:
				self._add_bubble(msg.content, msg.role, msg.timestamp)

		QTimer.singleShot(50, self._scroll_to_bottom)

	def _show_welcome(self) -> None:
		welcome = QWidget()
		welcome.setStyleSheet("background: transparent;")
		wl = QVBoxLayout(welcome)
		wl.setAlignment(Qt.AlignmentFlag.AlignCenter)
		wl.setSpacing(16)

		title = QLabel("How can I help you today?")
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		title.setStyleSheet(
			"color: #888; font-size: 20px; font-weight: 600; background: transparent;"
		)
		wl.addWidget(title)

		subtitle = QLabel("Ask anything, manage tasks, schedule events, or chat.")
		subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
		subtitle.setWordWrap(True)
		subtitle.setStyleSheet(
			"color: #555; font-size: 12px; background: transparent;"
		)
		wl.addWidget(subtitle)

		chips_row = QHBoxLayout()
		chips_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
		chips_row.setSpacing(8)
		for suggestion in ["Add a task", "Schedule event", "Just chat"]:
			chip = QPushButton(suggestion)
			chip.setCursor(Qt.CursorShape.PointingHandCursor)
			chip.setStyleSheet(
				"QPushButton {"
				"background: #1a1a1a; color: #777;"
				"border: 1px solid #2a2a2a; border-radius: 8px;"
				"padding: 6px 16px; font-size: 12px;"
				"}"
				"QPushButton:hover { border-color: #555; color: #ccc; }"
			)
			chip.clicked.connect(lambda _, t=suggestion: self.input_bar.set_text(t))
			chips_row.addWidget(chip)
		wl.addLayout(chips_row)

		stretch_idx = self.messages_layout.count() - 1
		self.messages_layout.insertWidget(max(stretch_idx, 0), welcome)

	def _on_send(self, user_text: str) -> None:
		session = self.store.active_session
		if not session:
			return

		if not session.messages:
			while self.messages_layout.count() > 1:
				item = self.messages_layout.takeAt(0)
				if item.widget():
					item.widget().deleteLater()

		history = session.get_history_dicts()
		session.add_message("user", user_text)
		self._add_bubble(user_text, "user")
		self.header.set_title(session.title)
		self.store.save()

		self.typing_widget.show()
		self._typing_timer.start()
		self.input_bar.set_enabled(False)

		model = self.header.model_combo.currentText() or DEFAULT_MODEL
		self._llm_worker = StreamingLLMWorker(user_text, model, history)
		self._llm_worker.stream_finished.connect(self._on_stream_finished)
		self._llm_worker.error_occurred.connect(self._on_error)
		self._llm_worker.start()

	def _on_stream_finished(self, full_response: str) -> None:
		# Debug: log raw LLM output so we can trace issues.
		from pathlib import Path
		log_path = Path(__file__).resolve().parent.parent / "data" / "debug_llm.log"
		try:
			with open(log_path, "a", encoding="utf-8") as f:
				f.write(f"\n--- {__import__('datetime').datetime.now()} ---\n")
				f.write(f"RAW LLM:\n{full_response}\n")
		except Exception:
			pass

		routed_text = router.route(full_response)

		try:
			with open(log_path, "a", encoding="utf-8") as f:
				f.write(f"ROUTED:\n{routed_text}\n")
		except Exception:
			pass

		self.typing_widget.hide()
		self._typing_timer.stop()
		self._add_bubble(routed_text, "assistant")

		session = self.store.active_session
		if session:
			session.add_message("assistant", routed_text)
			self.store.save()

		self.input_bar.set_enabled(True)
		self._scroll_to_bottom()

	def _on_error(self, error_msg: str) -> None:
		self.typing_widget.hide()
		self._typing_timer.stop()
		self.input_bar.set_enabled(True)
		self._add_bubble(error_msg, "assistant")
		session = self.store.active_session
		if session:
			session.add_message("assistant", error_msg)
			self.store.save()

	def _clear_chat(self) -> None:
		session = self.store.active_session
		if session:
			session.clear()
			session.title = "New Chat"
			self.store.save()
		self.load_session()

	def _on_mic(self) -> None:
		self.input_bar.mic_btn.setEnabled(False)
		self._voice_worker = VoiceWorker()
		self._voice_worker.result_ready.connect(lambda t: self.input_bar.set_text(t))
		self._voice_worker.finished.connect(lambda: self.input_bar.mic_btn.setEnabled(True))
		self._voice_worker.start()

	def _add_bubble(self, content: str, role: str, timestamp: float = 0) -> None:
		bubble = MessageBubble(content, role, timestamp)
		bubble.copy_clicked.connect(lambda t: pyperclip.copy(t))
		stretch_idx = self.messages_layout.count() - 1
		self.messages_layout.insertWidget(max(stretch_idx, 0), bubble)
		QTimer.singleShot(10, self._scroll_to_bottom)

	def _scroll_to_bottom(self) -> None:
		bar = self.scroll_area.verticalScrollBar()
		bar.setValue(bar.maximum())

	def _on_scroll(self, value: int) -> None:
		bar = self.scroll_area.verticalScrollBar()
		at_bottom = value >= bar.maximum() - 50
		self._scroll_btn.setVisible(not at_bottom and bar.maximum() > 100)
		if not at_bottom:
			w = self.scroll_area.width()
			h = self.scroll_area.height()
			self._scroll_btn.move(w // 2 - 16, h - 50)

	def _build_typing_indicator(self) -> QWidget:
		widget = QWidget()
		widget.setStyleSheet("background: transparent;")
		widget.setFixedHeight(36)
		outer = QHBoxLayout(widget)
		outer.setContentsMargins(0, 0, 0, 0)
		center = QWidget()
		center.setMaximumWidth(800)
		outer.addStretch()
		outer.addWidget(center)
		outer.addStretch()
		inner = QHBoxLayout(center)
		inner.setContentsMargins(20, 4, 20, 4)
		inner.setAlignment(Qt.AlignmentFlag.AlignLeft)
		self._typing_label = QLabel("...")
		self._typing_label.setStyleSheet(
			"color: #555; font-size: 18px; background: transparent; letter-spacing: 3px;"
		)
		inner.addWidget(self._typing_label)
		return widget

	def _animate_typing(self) -> None:
		self._thinking_dots = (self._thinking_dots + 1) % 4
		patterns = [".  ", ".. ", "...", "   "]
		self._typing_label.setText(patterns[self._thinking_dots])
