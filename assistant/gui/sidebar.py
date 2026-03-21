"""Left sidebar with chat history, tool navigation, and collapsible layout."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
	QFrame,
	QHBoxLayout,
	QLabel,
	QPushButton,
	QScrollArea,
	QSizePolicy,
	QVBoxLayout,
	QWidget,
)

from gui.chat_store import ChatStore


class ChatHistoryItem(QWidget):
	"""A single chat session entry in the sidebar list."""

	clicked = Signal(str)
	delete_requested = Signal(str)

	def __init__(self, session_id: str, title: str, is_active: bool = False) -> None:
		super().__init__()
		self.session_id = session_id
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		self.setFixedHeight(38)

		layout = QHBoxLayout(self)
		layout.setContentsMargins(14, 0, 8, 0)
		layout.setSpacing(6)

		# Title label (truncated).
		display = title if len(title) <= 30 else title[:30] + "..."
		self.title_label = QLabel(display)
		self.title_label.setStyleSheet(
			f"color: {'#e0e0e0' if is_active else '#888'};"
			"font-size: 13px; background: transparent;"
		)
		layout.addWidget(self.title_label, 1)

		# Delete button — visible on hover of the row.
		del_btn = QPushButton("x")
		del_btn.setFixedSize(22, 22)
		del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		del_btn.setStyleSheet(
			"QPushButton {"
			"background: transparent; color: #555; border: none;"
			"border-radius: 11px; font-size: 11px; font-weight: 700;"
			"}"
			"QPushButton:hover { background: #3a1111; color: #e55; }"
		)
		del_btn.clicked.connect(lambda: self.delete_requested.emit(self.session_id))
		layout.addWidget(del_btn)

		# Active/inactive styling.
		bg = "#1a1a1a" if is_active else "transparent"
		border = "border-left: 3px solid #555;" if is_active else "border-left: 3px solid transparent;"
		self.setStyleSheet(
			f"ChatHistoryItem {{"
			f"background: {bg}; {border} border-radius: 0;"
			f"}}"
			f"ChatHistoryItem:hover {{"
			f"background: #1a1a1a;"
			f"}}"
		)

	def mousePressEvent(self, event) -> None:
		self.clicked.emit(self.session_id)


class Sidebar(QWidget):
	"""Sidebar with chat history, tool navigation, and collapse support."""

	chat_selected = Signal(str)
	new_chat_requested = Signal()
	chat_deleted = Signal(str)
	clear_all_requested = Signal()
	page_requested = Signal(str)

	EXPANDED_WIDTH = 250
	COLLAPSED_WIDTH = 0

	def __init__(self, store: ChatStore) -> None:
		super().__init__()
		self.store = store
		self._expanded = True

		self.setFixedWidth(self.EXPANDED_WIDTH)
		self.setStyleSheet("background: #0a0a0a;")

		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

		# Top: branding + new chat.
		top_section = QWidget()
		top_section.setFixedHeight(100)
		top_section.setStyleSheet("background: transparent;")
		top_layout = QVBoxLayout(top_section)
		top_layout.setContentsMargins(16, 16, 16, 8)
		top_layout.setSpacing(10)

		brand = QLabel("AI Assistant")
		brand.setStyleSheet(
			"color: #ccc; font-size: 16px; font-weight: 700;"
			"background: transparent; letter-spacing: 0.5px;"
		)
		top_layout.addWidget(brand)

		new_chat_btn = QPushButton("+ New Chat")
		new_chat_btn.setFixedHeight(36)
		new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		new_chat_btn.setStyleSheet(
			"QPushButton {"
			"background: #1a1a1a; color: #888;"
			"border: 1px dashed #333; border-radius: 8px;"
			"font-size: 13px; font-weight: 600; text-align: left;"
			"padding: 0 14px;"
			"}"
			"QPushButton:hover { border-color: #666; color: #ccc; }"
		)
		new_chat_btn.clicked.connect(self.new_chat_requested.emit)
		top_layout.addWidget(new_chat_btn)

		layout.addWidget(top_section)

		# Chat history label.
		history_label = QLabel("  CHATS")
		history_label.setStyleSheet(
			"color: #444; font-size: 10px; font-weight: 700;"
			"letter-spacing: 1.5px; padding: 4px 16px; background: transparent;"
		)
		layout.addWidget(history_label)

		# Scrollable history list.
		self.history_scroll = QScrollArea()
		self.history_scroll.setWidgetResizable(True)
		self.history_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

		self.history_container = QWidget()
		self.history_container.setStyleSheet("background: transparent;")
		self.history_layout = QVBoxLayout(self.history_container)
		self.history_layout.setContentsMargins(0, 0, 0, 0)
		self.history_layout.setSpacing(1)
		self.history_layout.addStretch()

		self.history_scroll.setWidget(self.history_container)
		layout.addWidget(self.history_scroll, 1)

		# Clear all chats.
		clear_all_btn = QPushButton("Clear All Chats")
		clear_all_btn.setFixedHeight(30)
		clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		clear_all_btn.setStyleSheet(
			"QPushButton {"
			"text-align: left; padding: 0 16px;"
			"color: #444; font-size: 11px; background: transparent;"
			"border: none; border-radius: 0;"
			"}"
			"QPushButton:hover { background: #1a0a0a; color: #c55; }"
		)
		clear_all_btn.clicked.connect(self.clear_all_requested.emit)
		layout.addWidget(clear_all_btn)

		# Separator.
		sep = QFrame()
		sep.setFrameShape(QFrame.Shape.HLine)
		sep.setFixedHeight(1)
		sep.setStyleSheet("background: #1a1a1a; border: none;")
		layout.addWidget(sep)

		# Tools section.
		tools_label = QLabel("  TOOLS")
		tools_label.setStyleSheet(
			"color: #444; font-size: 10px; font-weight: 700;"
			"letter-spacing: 1.5px; padding: 8px 16px 4px; background: transparent;"
		)
		layout.addWidget(tools_label)

		for name, page_key in [
			("Tasks", "todo"),
			("About Her", "girlfriend"),
			("Voice", "voice"),
			("Finance", "finance"),
		]:
			btn = QPushButton(f"  {name}")
			btn.setFixedHeight(34)
			btn.setCursor(Qt.CursorShape.PointingHandCursor)
			btn.setStyleSheet(
				"QPushButton {"
				"text-align: left; padding: 0 16px;"
				"color: #666; font-size: 12px; background: transparent;"
				"border: none; border-radius: 0;"
				"}"
				"QPushButton:hover { background: #1a1a1a; color: #aaa; }"
			)
			btn.clicked.connect(lambda _, p=page_key: self.page_requested.emit(p))
			layout.addWidget(btn)

		layout.addSpacing(4)

		# Settings.
		sep2 = QFrame()
		sep2.setFrameShape(QFrame.Shape.HLine)
		sep2.setFixedHeight(1)
		sep2.setStyleSheet("background: #1a1a1a; border: none;")
		layout.addWidget(sep2)

		settings_btn = QPushButton("  Settings")
		settings_btn.setFixedHeight(38)
		settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		settings_btn.setStyleSheet(
			"QPushButton {"
			"text-align: left; padding: 0 16px;"
			"color: #666; font-size: 12px; background: transparent;"
			"border: none; border-radius: 0;"
			"}"
			"QPushButton:hover { background: #1a1a1a; color: #aaa; }"
		)
		settings_btn.clicked.connect(lambda: self.page_requested.emit("settings"))
		layout.addWidget(settings_btn)

		self.refresh_history()

	def refresh_history(self) -> None:
		while self.history_layout.count() > 1:
			item = self.history_layout.takeAt(0)
			if item.widget():
				item.widget().deleteLater()

		active_id = self.store.active_session_id
		for session in self.store.sessions:
			item = ChatHistoryItem(session.id, session.title, session.id == active_id)
			item.clicked.connect(self._on_chat_clicked)
			item.delete_requested.connect(self._on_delete_clicked)
			self.history_layout.insertWidget(self.history_layout.count() - 1, item)

	def _on_chat_clicked(self, session_id: str) -> None:
		self.chat_selected.emit(session_id)

	def _on_delete_clicked(self, session_id: str) -> None:
		self.chat_deleted.emit(session_id)

	def toggle(self) -> None:
		self._expanded = not self._expanded
		self.setFixedWidth(self.EXPANDED_WIDTH if self._expanded else self.COLLAPSED_WIDTH)
		self.setVisible(self._expanded)

	@property
	def is_expanded(self) -> bool:
		return self._expanded
