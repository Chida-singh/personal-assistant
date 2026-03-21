"""Left sidebar navigation widget for switching assistant tabs."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget


class Sidebar(QWidget):
	"""Sidebar with styled navigation buttons and active-state tracking."""

	tab_changed = Signal(str)

	def __init__(self) -> None:
		super().__init__()

		# Keep the sidebar narrow and visually separated from the main content panel.
		self.setFixedWidth(200)
		self.setStyleSheet("background: #0A0F1E;")

		self._buttons: dict[str, QPushButton] = {}

		# Stack navigation buttons from top to bottom in the requested order.
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 12, 0, 12)
		layout.setSpacing(4)

		self._add_nav_button(layout, "chat", "💬  Chat")
		self._add_nav_button(layout, "todo", "✅  Todo")
		self._add_nav_button(layout, "girlfriend", "💕  Girlfriend")
		self._add_nav_button(layout, "voice", "🎙️  Voice Reply")
		self._add_nav_button(layout, "settings", "⚙   Settings")
		layout.addStretch()

		# Select the default tab style so the initial UI has a clear active state.
		self.set_active_tab("chat")

	def _add_nav_button(self, layout: QVBoxLayout, tab_name: str, label: str) -> None:
		# Create and style each full-width button according to the dark theme spec.
		button = QPushButton(label)
		button.setFixedHeight(48)
		button.setStyleSheet(self._default_button_style())
		button.clicked.connect(lambda _checked=False, name=tab_name: self._on_button_clicked(name))

		layout.addWidget(button)
		self._buttons[tab_name] = button

	def _on_button_clicked(self, tab_name: str) -> None:
		# Update active visuals and notify parent widgets about the selected tab.
		self.set_active_tab(tab_name)
		self.tab_changed.emit(tab_name)

	def set_active_tab(self, tab_name: str) -> None:
		# Apply active style to one button and reset all other buttons to default style.
		for name, button in self._buttons.items():
			button.setStyleSheet(
				self._active_button_style() if name == tab_name else self._default_button_style()
			)

	@staticmethod
	def _default_button_style() -> str:
		return (
			"QPushButton {"
			"text-align: left;"
			"padding: 0 14px;"
			"font-family: 'Segoe UI';"
			"font-size: 13px;"
			"color: #94A3B8;"
			"background: transparent;"
			"border: none;"
			"border-left: 3px solid transparent;"
			"}"
			"QPushButton:hover {"
			"background: #1E293B;"
			"}"
		)

	@staticmethod
	def _active_button_style() -> str:
		return (
			"QPushButton {"
			"text-align: left;"
			"padding: 0 14px;"
			"font-family: 'Segoe UI';"
			"font-size: 13px;"
			"color: #F1F5F9;"
			"background: #1E293B;"
			"border: none;"
			"border-left: 3px solid #2563EB;"
			"}"
			"QPushButton:hover {"
			"background: #1E293B;"
			"}"
		)
