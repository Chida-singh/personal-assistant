"""Main application window that hosts sidebar navigation and all tabs."""

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from gui.sidebar import Sidebar
from gui.tabs.chat_tab import ChatTab
from gui.tabs.girlfriend_tab import GirlfriendTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.todo_tab import TodoTab
from gui.tabs.whatsapp_tab import VoiceReplyTab


class MainWindow(QMainWindow):
	"""Primary shell window with left navigation and stacked content tabs."""

	def __init__(self) -> None:
		super().__init__()

		# Apply core window metadata and baseline geometry.
		self.setWindowTitle("🧠 Local AI Assistant")
		self.setMinimumSize(1000, 650)

		# Create a central widget that holds a horizontal two-panel layout.
		central_widget = QWidget()
		self.setCentralWidget(central_widget)

		main_layout = QHBoxLayout(central_widget)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(0)

		# Left panel: fixed sidebar used to choose which tab is active.
		self.sidebar = Sidebar()
		main_layout.addWidget(self.sidebar)

		# Right panel: stacked tabs shown one at a time in sidebar order.
		self.stacked_widget = QStackedWidget()
		self.stacked_widget.addWidget(ChatTab())        # index 0 -> chat
		self.stacked_widget.addWidget(TodoTab())        # index 1 -> todo
		self.stacked_widget.addWidget(GirlfriendTab())  # index 2 -> girlfriend
		self.stacked_widget.addWidget(VoiceReplyTab())  # index 3 -> voice
		self.stacked_widget.addWidget(SettingsTab())    # index 4 -> settings
		main_layout.addWidget(self.stacked_widget, 1)

		# Connect sidebar selection changes to stacked widget index switching.
		self.sidebar.tab_changed.connect(self.switch_tab)

		# Start on the chat tab by default.
		self.switch_tab("chat")

		# Apply global dark styles across key widget types.
		self.setStyleSheet(
			"QMainWindow { background: #0F172A; color: #F1F5F9; }"
			"QLineEdit {"
			"background: #1E293B;"
			"border: 1px solid #334155;"
			"border-radius: 8px;"
			"color: #F1F5F9;"
			"padding: 6px 10px;"
			"}"
			"QPushButton {"
			"background: #2563EB;"
			"color: #FFFFFF;"
			"border-radius: 8px;"
			"padding: 8px 16px;"
			"font-size: 13px;"
			"}"
			"QPushButton:hover { background: #1D4ED8; }"
			"QScrollArea { border: none; background: transparent; }"
		)

	def switch_tab(self, name: str) -> None:
		# Map sidebar tab names to stacked indexes and update both panels.
		index_map = {
			"chat": 0,
			"todo": 1,
			"girlfriend": 2,
			"voice": 3,
			"settings": 4,
		}

		index = index_map.get(name, 0)
		self.stacked_widget.setCurrentIndex(index)
		self.sidebar.set_active_tab(name if name in index_map else "chat")
