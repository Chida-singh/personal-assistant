"""Multiline input bar with send button, mic button, and keyboard shortcuts."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
	QHBoxLayout,
	QLabel,
	QPushButton,
	QSizePolicy,
	QTextEdit,
	QVBoxLayout,
	QWidget,
)


class GrowingTextEdit(QTextEdit):
	"""A QTextEdit that grows vertically to fit content, up to a max line count."""

	submit_pressed = Signal()

	def __init__(self, max_lines: int = 6) -> None:
		super().__init__()
		self.max_lines = max_lines
		self.setAcceptRichText(False)
		self.textChanged.connect(self._adjust_height)
		self._adjust_height()

	def keyPressEvent(self, event: QKeyEvent) -> None:
		if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
			if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
				super().keyPressEvent(event)
			else:
				self.submit_pressed.emit()
			return
		super().keyPressEvent(event)

	def _adjust_height(self) -> None:
		doc = self.document()
		doc.setTextWidth(self.viewport().width() or 500)
		line_height = self.fontMetrics().lineSpacing()
		content_height = int(doc.size().height()) + 12
		min_h = line_height + 20
		max_h = line_height * self.max_lines + 20
		self.setFixedHeight(max(min_h, min(content_height, max_h)))


class ChatInput(QWidget):
	"""Bottom input bar with auto-growing text field, send, and mic buttons."""

	message_submitted = Signal(str)
	mic_clicked = Signal()

	def __init__(self) -> None:
		super().__init__()
		self.setStyleSheet("background: transparent;")

		outer = QHBoxLayout(self)
		outer.setContentsMargins(0, 0, 0, 0)

		center = QWidget()
		center.setMaximumWidth(800)
		center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
		outer.addStretch()
		outer.addWidget(center)
		outer.addStretch()

		# Input container.
		container = QWidget()
		container.setStyleSheet(
			"QWidget#inputBox {"
			"background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px;"
			"}"
		)
		container.setObjectName("inputBox")

		container_layout = QVBoxLayout(container)
		container_layout.setContentsMargins(8, 6, 8, 6)
		container_layout.setSpacing(0)

		row = QHBoxLayout()
		row.setContentsMargins(4, 0, 4, 0)
		row.setSpacing(6)

		# Mic button.
		self.mic_btn = QPushButton("mic")
		self.mic_btn.setFixedSize(32, 32)
		self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		self.mic_btn.setStyleSheet(
			"QPushButton {"
			"background: transparent; color: #555; border: none;"
			"border-radius: 16px; font-size: 11px;"
			"}"
			"QPushButton:hover { background: #222; color: #aaa; }"
		)
		self.mic_btn.clicked.connect(self.mic_clicked.emit)
		row.addWidget(self.mic_btn)

		# Text input.
		self.text_edit = GrowingTextEdit(max_lines=6)
		self.text_edit.setPlaceholderText("Message your assistant...")
		self.text_edit.submit_pressed.connect(self._on_submit)
		self.text_edit.setStyleSheet(
			"QTextEdit {"
			"background: transparent; border: none;"
			"color: #ccc; font-size: 14px;"
			"font-family: 'Segoe UI', sans-serif;"
			"padding: 6px 4px;"
			"}"
		)
		row.addWidget(self.text_edit, 1)

		# Send button.
		self.send_btn = QPushButton("Send")
		self.send_btn.setFixedHeight(32)
		self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		self.send_btn.setStyleSheet(
			"QPushButton {"
			"background: #333; color: #ccc; border: none;"
			"border-radius: 8px; font-size: 12px; font-weight: 600;"
			"padding: 0 14px;"
			"}"
			"QPushButton:hover { background: #444; color: #eee; }"
			"QPushButton:disabled { background: #1a1a1a; color: #444; }"
		)
		self.send_btn.clicked.connect(self._on_submit)
		row.addWidget(self.send_btn)

		container_layout.addLayout(row)

		main_layout = QVBoxLayout(center)
		main_layout.setContentsMargins(20, 8, 20, 14)
		main_layout.setSpacing(4)
		main_layout.addWidget(container)

	def _on_submit(self) -> None:
		text = self.text_edit.toPlainText().strip()
		if text:
			self.message_submitted.emit(text)
			self.text_edit.clear()

	def set_enabled(self, enabled: bool) -> None:
		self.text_edit.setEnabled(enabled)
		self.send_btn.setEnabled(enabled)
		self.mic_btn.setEnabled(enabled)
		if enabled:
			self.text_edit.setFocus()

	def get_text(self) -> str:
		return self.text_edit.toPlainText().strip()

	def set_text(self, text: str) -> None:
		self.text_edit.setPlainText(text)
