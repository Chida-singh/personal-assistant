"""Chat header bar with title, model selector, and action buttons."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
	QComboBox,
	QHBoxLayout,
	QLabel,
	QPushButton,
	QWidget,
)

from core import llm


class ChatHeader(QWidget):
	"""Top header bar with model selection and controls."""

	toggle_sidebar = Signal()
	clear_chat = Signal()
	model_changed = Signal(str)

	def __init__(self) -> None:
		super().__init__()
		self.setFixedHeight(48)
		self.setStyleSheet("background: #111; border-bottom: 1px solid #1a1a1a;")

		layout = QHBoxLayout(self)
		layout.setContentsMargins(12, 0, 12, 0)
		layout.setSpacing(10)

		# Sidebar toggle.
		self.toggle_btn = QPushButton("=")
		self.toggle_btn.setFixedSize(32, 32)
		self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		self.toggle_btn.setStyleSheet(
			"QPushButton {"
			"background: transparent; color: #666; border: none;"
			"border-radius: 6px; font-size: 16px; font-weight: 700;"
			"}"
			"QPushButton:hover { background: #1a1a1a; color: #aaa; }"
		)
		self.toggle_btn.clicked.connect(self.toggle_sidebar.emit)
		layout.addWidget(self.toggle_btn)

		# Title.
		self.title_label = QLabel("New Chat")
		self.title_label.setStyleSheet(
			"color: #ccc; font-size: 14px; font-weight: 600; background: transparent;"
		)
		layout.addWidget(self.title_label)

		layout.addStretch()

		# Model selector.
		self.model_combo = QComboBox()
		self.model_combo.addItems(["llama3", "qwen2.5", "mistral", "deepseek-r1", "gemma", "phi3", "codellama"])
		self.model_combo.setCurrentText(llm.DEFAULT_MODEL)
		self.model_combo.setStyleSheet(
			"QComboBox {"
			"background: #1a1a1a; color: #888;"
			"border: 1px solid #222; border-radius: 6px;"
			"padding: 4px 10px; font-size: 12px; min-width: 80px;"
			"}"
			"QComboBox::drop-down { border: none; }"
			"QComboBox QAbstractItemView {"
			"background: #1a1a1a; color: #ccc;"
			"border: 1px solid #333;"
			"selection-background-color: #333;"
			"}"
		)
		self.model_combo.currentTextChanged.connect(self._on_model_changed)
		layout.addWidget(self.model_combo)

		# Clear chat.
		clear_btn = QPushButton("Clear")
		clear_btn.setFixedHeight(28)
		clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		clear_btn.setToolTip("Clear chat")
		clear_btn.setStyleSheet(
			"QPushButton {"
			"background: transparent; color: #555; border: none;"
			"border-radius: 6px; font-size: 11px; padding: 0 8px;"
			"}"
			"QPushButton:hover { background: #1a0a0a; color: #c55; }"
		)
		clear_btn.clicked.connect(self.clear_chat.emit)
		layout.addWidget(clear_btn)

	def set_title(self, title: str) -> None:
		display = title if len(title) <= 50 else title[:50] + "..."
		self.title_label.setText(display)

	def _on_model_changed(self, model: str) -> None:
		llm.configure(model=model)
		self.model_changed.emit(model)
