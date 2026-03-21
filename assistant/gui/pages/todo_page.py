"""Todo tab UI for creating, completing, and deleting tasks."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QCheckBox,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QPushButton,
	QScrollArea,
	QVBoxLayout,
	QWidget,
)

from modules import todo


class TaskRow(QWidget):
	"""Single task row with complete and delete actions."""

	def __init__(self, task_item: dict, on_complete, on_uncomplete, on_delete) -> None:
		super().__init__()
		task_text = str(task_item.get("task", ""))
		is_done = bool(task_item.get("done", False))

		row_layout = QHBoxLayout(self)
		row_layout.setContentsMargins(14, 10, 14, 10)
		row_layout.setSpacing(10)

		self.checkbox = QCheckBox()
		self.checkbox.setChecked(is_done)
		self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
		self.checkbox.setStyleSheet(
			"QCheckBox::indicator {"
			"width: 16px; height: 16px;"
			"border: 2px solid #444; border-radius: 3px;"
			"background: transparent;"
			"}"
			"QCheckBox::indicator:checked {"
			"background: #555; border-color: #555;"
			"}"
			"QCheckBox::indicator:hover { border-color: #777; }"
		)
		self.checkbox.stateChanged.connect(
			lambda state: on_complete(task_text) if state == Qt.CheckState.Checked.value
			else on_uncomplete(task_text)
		)

		self.label = QLabel(task_text)
		self.label.setWordWrap(True)

		self.delete_button = QPushButton("x")
		self.delete_button.setFixedSize(24, 24)
		self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.delete_button.clicked.connect(lambda: on_delete(task_text))
		self.delete_button.setStyleSheet(
			"QPushButton {"
			"background: transparent; color: #444; border: none;"
			"border-radius: 12px; font-size: 11px; font-weight: 700;"
			"}"
			"QPushButton:hover { background: #2a1111; color: #c55; }"
		)

		row_layout.addWidget(self.checkbox)
		row_layout.addWidget(self.label, 1)
		row_layout.addWidget(self.delete_button)

		self.setStyleSheet(
			"TaskRow {"
			"background: #1a1a1a; border: 1px solid #222; border-radius: 8px;"
			"}"
			"TaskRow:hover { border-color: #333; }"
		)
		self._apply_done_style(is_done)

	def _apply_done_style(self, is_done: bool) -> None:
		font = self.label.font()
		font.setStrikeOut(is_done)
		self.label.setFont(font)
		self.label.setStyleSheet(
			"color: #444; font-size: 13px;" if is_done
			else "color: #ccc; font-size: 13px;"
		)


class TodoTab(QWidget):
	"""Todo list tab with task management."""

	def __init__(self) -> None:
		super().__init__()
		self.setStyleSheet("background: #111;")

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(16, 16, 16, 16)
		main_layout.setSpacing(12)

		# Title row with count and clear button.
		title_row = QHBoxLayout()
		self.title_label = QLabel("My Tasks")
		self.title_label.setStyleSheet(
			"font-size: 18px; font-weight: 700; color: #ccc;"
		)

		self.count_badge = QLabel("0")
		self.count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.count_badge.setFixedSize(26, 20)
		self.count_badge.setStyleSheet(
			"background: #2a2a2a; color: #888; border-radius: 10px;"
			"font-size: 11px; font-weight: 700;"
		)

		self.clear_done_btn = QPushButton("Clear completed")
		self.clear_done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		self.clear_done_btn.setStyleSheet(
			"QPushButton {"
			"background: transparent; color: #555; border: none;"
			"font-size: 11px; padding: 2px 8px; border-radius: 4px;"
			"}"
			"QPushButton:hover { color: #c55; }"
		)
		self.clear_done_btn.clicked.connect(self._clear_completed)

		self.clear_all_btn = QPushButton("Delete all")
		self.clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		self.clear_all_btn.setStyleSheet(
			"QPushButton {"
			"background: transparent; color: #555; border: none;"
			"font-size: 11px; padding: 2px 8px; border-radius: 4px;"
			"}"
			"QPushButton:hover { color: #c55; }"
		)
		self.clear_all_btn.clicked.connect(self._clear_all)

		title_row.addWidget(self.title_label)
		title_row.addWidget(self.count_badge)
		title_row.addStretch()
		title_row.addWidget(self.clear_done_btn)
		title_row.addWidget(self.clear_all_btn)
		main_layout.addLayout(title_row)

		# Input row.
		input_layout = QHBoxLayout()
		input_layout.setSpacing(8)

		self.input_edit = QLineEdit()
		self.input_edit.setPlaceholderText("What needs to be done?")
		self.input_edit.returnPressed.connect(self.add_task)
		self.input_edit.setStyleSheet(
			"QLineEdit {"
			"background: #1a1a1a; border: 1px solid #2a2a2a;"
			"border-radius: 8px; color: #ccc; padding: 10px 14px; font-size: 13px;"
			"}"
			"QLineEdit:focus { border-color: #444; }"
		)

		self.add_button = QPushButton("Add")
		self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.add_button.clicked.connect(self.add_task)
		self.add_button.setStyleSheet(
			"QPushButton {"
			"background: #333; color: #ccc; border-radius: 8px;"
			"padding: 10px 18px; font-weight: 600; font-size: 13px; border: none;"
			"}"
			"QPushButton:hover { background: #444; }"
		)

		input_layout.addWidget(self.input_edit, 1)
		input_layout.addWidget(self.add_button)
		main_layout.addLayout(input_layout)

		# Empty state.
		self.empty_label = QLabel("No tasks yet — add one above")
		self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.empty_label.setStyleSheet(
			"color: #444; font-size: 13px; padding: 40px 0; background: transparent;"
		)
		self.empty_label.hide()

		# Task list.
		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

		self.list_container = QWidget()
		self.list_layout = QVBoxLayout(self.list_container)
		self.list_layout.setContentsMargins(0, 0, 0, 0)
		self.list_layout.setSpacing(6)
		self.list_layout.addStretch()

		self.scroll_area.setWidget(self.list_container)

		main_layout.addWidget(self.empty_label)
		main_layout.addWidget(self.scroll_area, 1)

		self.load_tasks()

	def load_tasks(self) -> None:
		self.refresh()

	def add_task(self) -> None:
		task_text = self.input_edit.text().strip()
		if not task_text:
			return
		todo.add_todo(task_text)
		self.input_edit.clear()
		self.refresh()

	def _complete_task(self, task_text: str) -> None:
		todo.complete_todo(task_text)
		self.refresh()

	def _uncomplete_task(self, task_text: str) -> None:
		"""Unmark a task as done."""
		from core.storage import TODOS_FILE, load, save
		todos = load(TODOS_FILE)
		for item in todos:
			if str(item.get("task", "")).strip().lower() == task_text.strip().lower():
				item["done"] = False
				break
		save(TODOS_FILE, todos)
		self.refresh()

	def _delete_task(self, task_text: str) -> None:
		todo.delete_todo(task_text)
		self.refresh()

	def _clear_completed(self) -> None:
		"""Remove all completed tasks."""
		from core.storage import TODOS_FILE, load, save
		all_tasks = load(TODOS_FILE)
		remaining = [t for t in all_tasks if not t.get("done", False)]
		save(TODOS_FILE, remaining)
		self.refresh()

	def _clear_all(self) -> None:
		"""Delete all tasks."""
		from core.storage import TODOS_FILE, save
		save(TODOS_FILE, [])
		self.refresh()

	def refresh(self) -> None:
		while self.list_layout.count() > 1:
			item = self.list_layout.takeAt(0)
			widget = item.widget()
			if widget:
				widget.deleteLater()

		all_tasks = todo.get_all()
		pending = sum(1 for t in all_tasks if not t.get("done", False))
		self.count_badge.setText(str(pending))

		self.empty_label.setVisible(len(all_tasks) == 0)
		self.scroll_area.setVisible(len(all_tasks) > 0)

		for task_item in all_tasks:
			row = TaskRow(task_item, self._complete_task, self._uncomplete_task, self._delete_task)
			self.list_layout.insertWidget(self.list_layout.count() - 1, row)
