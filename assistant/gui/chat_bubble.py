"""Chat bubble widget used to render a single user or assistant message."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget


class ChatBubble(QWidget):
	"""A message bubble styled by sender role."""

	def __init__(self, message: str, sender: str) -> None:
		super().__init__()

		# Create the message label and apply common typography and spacing.
		self.label = QLabel(message)
		self.label.setWordWrap(True)
		self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
		self.label.setMaximumWidth(700)

		# Build a single-row layout that pushes bubbles left or right by sender.
		layout = QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)

		if sender == "user":
			layout.addStretch()
			layout.addWidget(self.label)
			self.label.setStyleSheet(
				"QLabel {"
				"background: #2563EB;"
				"color: #FFFFFF;"
				"border-radius: 18px 18px 4px 18px;"
				"padding: 10px 16px;"
				"font-family: Consolas;"
				"font-size: 13px;"
				"}"
			)
		else:
			layout.addWidget(self.label)
			layout.addStretch()
			self.label.setStyleSheet(
				"QLabel {"
				"background: #1E293B;"
				"color: #CBD5E1;"
				"border-radius: 18px 18px 18px 4px;"
				"padding: 10px 16px;"
				"font-family: Consolas;"
				"font-size: 13px;"
				"}"
			)

		self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
		self._update_max_width()

	def resizeEvent(self, event) -> None:
		# Keep bubble width near 70% of available row width as the UI resizes.
		self._update_max_width()
		super().resizeEvent(event)

	def _update_max_width(self) -> None:
		# Use parent row width when available, otherwise retain a safe fallback.
		parent_width = self.parentWidget().width() if self.parentWidget() else 1000
		self.label.setMaximumWidth(int(parent_width * 0.7))
