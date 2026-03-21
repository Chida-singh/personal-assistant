"""Chat bubble widget used to render a single user or assistant message."""

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


class ChatBubble(QWidget):
	"""A message bubble styled by sender role with timestamp."""

	def __init__(self, message: str, sender: str) -> None:
		super().__init__()

		# Create the message label with clean typography.
		self.label = QLabel(message)
		self.label.setWordWrap(True)
		self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
		self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
		self.label.setMaximumWidth(700)

		# Compact timestamp underneath the bubble.
		timestamp = QLabel(datetime.now().strftime("%I:%M %p").lstrip("0").lower())
		timestamp.setStyleSheet(
			"font-size: 10px; color: #475569; background: transparent; padding: 0; margin: 0;"
		)

		# Vertical stack: bubble text + timestamp.
		bubble_stack = QVBoxLayout()
		bubble_stack.setContentsMargins(0, 0, 0, 0)
		bubble_stack.setSpacing(2)
		bubble_stack.addWidget(self.label)

		# Build a single-row layout that pushes bubbles left or right by sender.
		layout = QHBoxLayout(self)
		layout.setContentsMargins(4, 2, 4, 2)

		if sender == "user":
			# Timestamp aligned right under the user bubble.
			timestamp.setAlignment(Qt.AlignmentFlag.AlignRight)
			bubble_stack.addWidget(timestamp)

			layout.addStretch()
			layout.addLayout(bubble_stack)
			self.label.setStyleSheet(
				"QLabel {"
				"background: qlineargradient("
				"  x1:0, y1:0, x2:1, y2:1,"
				"  stop:0 #2563EB, stop:1 #1D4ED8);"
				"color: #FFFFFF;"
				"border-radius: 16px 16px 4px 16px;"
				"padding: 10px 16px;"
				"font-family: 'Segoe UI', sans-serif;"
				"font-size: 13px;"
				"line-height: 1.5;"
				"}"
			)
		else:
			# Timestamp aligned left under the assistant bubble.
			timestamp.setAlignment(Qt.AlignmentFlag.AlignLeft)
			bubble_stack.addWidget(timestamp)

			layout.addLayout(bubble_stack)
			layout.addStretch()
			self.label.setStyleSheet(
				"QLabel {"
				"background: #1E293B;"
				"color: #E2E8F0;"
				"border-radius: 16px 16px 16px 4px;"
				"border: 1px solid #334155;"
				"padding: 10px 16px;"
				"font-family: 'Segoe UI', sans-serif;"
				"font-size: 13px;"
				"line-height: 1.5;"
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
