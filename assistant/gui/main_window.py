"""Main application window — ChatGPT-like shell with sidebar and stacked content."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from gui.chat_area import ChatArea
from gui.chat_store import ChatStore
from gui.sidebar import Sidebar
from gui.pages.todo_page import TodoTab
from gui.pages.girlfriend_page import GirlfriendTab
from gui.pages.voice_page import VoiceReplyTab
from gui.pages.settings_page import SettingsTab
from gui.pages.finance_page import FinancePage


class MainWindow(QMainWindow):
	"""Primary shell window with ChatGPT-style sidebar and stacked content."""

	# Page index mapping.
	PAGE_CHAT = 0
	PAGE_TODO = 1
	PAGE_GIRLFRIEND = 2
	PAGE_VOICE = 3
	PAGE_SETTINGS = 4
	PAGE_FINANCE = 5

	def __init__(self) -> None:
		super().__init__()

		self.setWindowTitle("AI Assistant")
		self.setMinimumSize(1050, 680)

		# Shared chat store for all components.
		self.store = ChatStore()
		# Reopen the current session (including an unused new chat) on app launch.

		# Central widget.
		central = QWidget()
		self.setCentralWidget(central)

		main_layout = QHBoxLayout(central)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(0)

		# Sidebar.
		self.sidebar = Sidebar(self.store)
		self.sidebar.chat_selected.connect(self._on_chat_selected)
		self.sidebar.new_chat_requested.connect(self._on_new_chat)
		self.sidebar.chat_deleted.connect(self._on_chat_deleted)
		self.sidebar.clear_all_requested.connect(self._on_clear_all)
		self.sidebar.page_requested.connect(self._on_page_requested)
		main_layout.addWidget(self.sidebar)

		# Stacked widget for content pages.
		self.stack = QStackedWidget()

		# Chat page.
		self.chat_area = ChatArea(self.store)
		self.chat_area.toggle_sidebar_requested.connect(self._toggle_sidebar)
		self.stack.addWidget(self.chat_area)  # index 0

		# Tool pages.
		self.stack.addWidget(TodoTab())          # index 1
		self.stack.addWidget(GirlfriendTab())    # index 2
		self.stack.addWidget(VoiceReplyTab())    # index 3
		self.stack.addWidget(SettingsTab())       # index 4
		self.stack.addWidget(FinancePage())       # index 5

		main_layout.addWidget(self.stack, 1)

		# Start on chat page.
		self.stack.setCurrentIndex(self.PAGE_CHAT)

		# Keyboard shortcuts.
		QShortcut(QKeySequence("Ctrl+K"), self, self._on_new_chat)
		QShortcut(QKeySequence("Ctrl+B"), self, self._toggle_sidebar)

		# Apply global dark stylesheet.
		self.setStyleSheet(self._global_stylesheet())

	def _on_chat_selected(self, session_id: str) -> None:
		"""Switch to a different chat session."""
		self.store.switch_to(session_id)
		self.chat_area.load_session()
		self.sidebar.refresh_history()
		self.stack.setCurrentIndex(self.PAGE_CHAT)

	def _on_new_chat(self) -> None:
		"""Create and switch to a new chat session."""
		self.store.new_session()
		self.chat_area.load_session()
		self.sidebar.refresh_history()
		self.stack.setCurrentIndex(self.PAGE_CHAT)

	def _on_chat_deleted(self, session_id: str) -> None:
		"""Delete a chat session."""
		self.store.delete_session(session_id)
		self.chat_area.load_session()
		self.sidebar.refresh_history()

	def _on_clear_all(self) -> None:
		"""Clear all chat sessions."""
		self.store.sessions.clear()
		self.store.new_session()
		self.chat_area.load_session()
		self.sidebar.refresh_history()
		self.stack.setCurrentIndex(self.PAGE_CHAT)

	def _on_page_requested(self, page: str) -> None:
		"""Navigate to a tool page."""
		page_map = {
			"todo": self.PAGE_TODO,
			"girlfriend": self.PAGE_GIRLFRIEND,
			"voice": self.PAGE_VOICE,
			"settings": self.PAGE_SETTINGS,
			"finance": self.PAGE_FINANCE,
		}
		idx = page_map.get(page, self.PAGE_CHAT)
		self.stack.setCurrentIndex(idx)

	def _toggle_sidebar(self) -> None:
		"""Toggle sidebar visibility."""
		self.sidebar.toggle()

	@staticmethod
	def _global_stylesheet() -> str:
		"""Dark theme stylesheet using shades of black and grey."""
		return """
			QMainWindow {
				background: #111;
				color: #ccc;
				font-family: 'Segoe UI', 'Inter', sans-serif;
				font-size: 13px;
			}
			QLineEdit {
				background: #1a1a1a;
				border: 1px solid #2a2a2a;
				border-radius: 8px;
				color: #ccc;
				padding: 8px 12px;
				font-size: 13px;
				selection-background-color: #444;
			}
			QLineEdit:focus { border-color: #444; }
			QPushButton {
				background: #333;
				color: #ccc;
				border: none;
				border-radius: 8px;
				padding: 8px 18px;
				font-size: 13px;
				font-weight: 600;
			}
			QPushButton:hover { background: #444; }
			QPushButton:pressed { background: #555; }
			QPushButton:disabled { background: #1a1a1a; color: #444; }
			QScrollArea { border: none; background: transparent; }
			QScrollBar:vertical {
				background: transparent;
				width: 5px;
				margin: 4px 0;
			}
			QScrollBar::handle:vertical {
				background: #2a2a2a;
				min-height: 30px;
				border-radius: 2px;
			}
			QScrollBar::handle:vertical:hover { background: #444; }
			QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
			QScrollBar:horizontal { height: 0; }
			QLabel { font-family: 'Segoe UI', sans-serif; }
			QTextEdit { font-family: 'Segoe UI', sans-serif; }
			QTextBrowser {
				font-family: 'Segoe UI', sans-serif;
				selection-background-color: #444;
			}
			QComboBox { font-family: 'Segoe UI', sans-serif; }
			QSpinBox { font-family: 'Segoe UI', sans-serif; }
		"""
