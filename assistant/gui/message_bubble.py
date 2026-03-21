"""Single chat message widget with hover actions and markdown rendering."""

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
	QHBoxLayout,
	QLabel,
	QPushButton,
	QSizePolicy,
	QTextBrowser,
	QVBoxLayout,
	QWidget,
)

from gui.markdown_render import markdown_to_html


class MessageBubble(QWidget):
	"""A message bubble with rendered content, timestamp, and hover actions."""

	copy_clicked = Signal(str)
	regenerate_clicked = Signal()

	def __init__(self, content: str, role: str, timestamp: float = 0) -> None:
		super().__init__()
		self.content = content
		self.role = role

		self.setStyleSheet("background: transparent;")

		# Outer centering layout.
		outer = QHBoxLayout(self)
		outer.setContentsMargins(0, 0, 0, 0)

		center = QWidget()
		center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
		outer.addWidget(center, 1)

		main_layout = QVBoxLayout(center)
		main_layout.setContentsMargins(20, 12, 20, 12)
		main_layout.setSpacing(6)

		# Role label.
		role_label = QLabel("You" if role == "user" else "Assistant")
		role_label.setStyleSheet(
			"color: #888; font-size: 11px; font-weight: 700;"
			"background: transparent; letter-spacing: 0.5px;"
		)
		main_layout.addWidget(role_label)

		# Content area.
		self.content_browser = QTextBrowser()
		self.content_browser.setOpenExternalLinks(True)
		self.content_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.content_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.content_browser.setSizePolicy(
			QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
		)

		bg = "#1a1a1a" if role == "assistant" else "transparent"
		border = "1px solid #222" if role == "assistant" else "none"
		radius = "8px" if role == "assistant" else "0"

		self.content_browser.setStyleSheet(
			f"QTextBrowser {{"
			f"background: {bg}; border: {border}; border-radius: {radius};"
			f"padding: {'12px' if role == 'assistant' else '4px 0'};"
			f"color: #ccc; font-size: 13px;"
			f"}}"
		)

		if content:
			self._render_content(content)

		main_layout.addWidget(self.content_browser)

		# Bottom row: timestamp + actions.
		bottom_row = QHBoxLayout()
		bottom_row.setContentsMargins(0, 0, 0, 0)
		bottom_row.setSpacing(8)

		ts = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
		ts_label = QLabel(ts.strftime("%I:%M %p").lstrip("0").lower())
		ts_label.setStyleSheet("color: #444; font-size: 10px; background: transparent;")
		bottom_row.addWidget(ts_label)

		bottom_row.addStretch()

		copy_btn = QPushButton("Copy")
		copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		copy_btn.setFixedHeight(22)
		copy_btn.setStyleSheet(
			"QPushButton {"
			"background: transparent; color: #444; border: none;"
			"font-size: 11px; padding: 2px 6px; border-radius: 4px;"
			"}"
			"QPushButton:hover { background: #222; color: #aaa; }"
		)
		copy_btn.clicked.connect(lambda: self.copy_clicked.emit(self.content))
		bottom_row.addWidget(copy_btn)

		if role == "assistant":
			regen_btn = QPushButton("Regenerate")
			regen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
			regen_btn.setFixedHeight(22)
			regen_btn.setStyleSheet(
				"QPushButton {"
				"background: transparent; color: #444; border: none;"
				"font-size: 11px; padding: 2px 6px; border-radius: 4px;"
				"}"
				"QPushButton:hover { background: #222; color: #aaa; }"
			)
			regen_btn.clicked.connect(self.regenerate_clicked.emit)
			bottom_row.addWidget(regen_btn)

		main_layout.addLayout(bottom_row)

	def _render_content(self, text: str) -> None:
		html_content = markdown_to_html(text)
		self.content_browser.setHtml(html_content)
		self._adjust_height()

	def _adjust_height(self) -> None:
		doc = self.content_browser.document()
		doc.setTextWidth(self.content_browser.viewport().width() or 700)
		height = int(doc.size().height()) + 10
		self.content_browser.setFixedHeight(max(height, 30))

	def append_token(self, token: str) -> None:
		self.content = (self.content or "") + token
		self._render_content(self.content)

	def finish_streaming(self) -> None:
		self._render_content(self.content)

	def resizeEvent(self, event) -> None:
		super().resizeEvent(event)
		self._adjust_height()
