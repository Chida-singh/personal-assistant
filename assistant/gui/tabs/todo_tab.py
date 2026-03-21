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

	def __init__(self, task_item: dict, on_complete, on_delete) -> None:
		super().__init__()
		task_text = str(task_item.get("task", ""))
		is_done = bool(task_item.get("done", False))

		# Build horizontal row controls for checkbox, label, and delete action.
		row_layout = QHBoxLayout(self)
		row_layout.setContentsMargins(10, 8, 10, 8)
		row_layout.setSpacing(8)

		self.checkbox = QCheckBox()
		self.checkbox.setChecked(is_done)
		self.checkbox.setStyleSheet("QCheckBox::indicator { width: 16px; height: 16px; }")
		self.checkbox.stateChanged.connect(
			lambda state: on_complete(task_text) if state == Qt.CheckState.Checked.value else None
		)

		self.label = QLabel(task_text)
		self.label.setWordWrap(True)

		self.delete_button = QPushButton("🗑")
		self.delete_button.setFixedWidth(36)
		self.delete_button.clicked.connect(lambda: on_delete(task_text))

		row_layout.addWidget(self.checkbox)
		row_layout.addWidget(self.label, 1)
		row_layout.addWidget(self.delete_button)

		# Style the row and apply done/undone text appearance.
		self.setStyleSheet(
			"QWidget {"
			"background: #1E293B;"
			"border-radius: 8px;"
			"}"
			"QPushButton {"
			"background: transparent;"
			"color: #CBD5E1;"
			"border: none;"
			"font-size: 14px;"
			"}"
			"QPushButton:hover { color: #F87171; }"
		)
		self._apply_done_style(is_done)

	def _apply_done_style(self, is_done: bool) -> None:
		# Strike through completed tasks and mute text color.
		font = self.label.font()
		font.setStrikeOut(is_done)
		self.label.setFont(font)
		self.label.setStyleSheet("color: #475569;" if is_done else "color: #F1F5F9;")


class TodoTab(QWidget):
	"""Todo list tab that renders tasks from storage and updates interactively."""

	def __init__(self) -> None:
		super().__init__()
		self.setStyleSheet("background: #0F172A;")

		# Arrange title, input row, and scrollable task list top-to-bottom.
		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(12, 12, 12, 12)
		main_layout.setSpacing(10)

		self.title_label = QLabel("✅ My Tasks")
		self.title_label.setStyleSheet(
			"font-family: 'Segoe UI'; font-size: 18px; font-weight: bold; color: #F1F5F9;"
		)
		main_layout.addWidget(self.title_label)

		# Create task input controls for adding new items.
		input_layout = QHBoxLayout()
		input_layout.setSpacing(8)

		self.input_edit = QLineEdit()
		self.input_edit.setPlaceholderText("Add a new task...")
		self.input_edit.returnPressed.connect(self.add_task)
		self.input_edit.setStyleSheet(
			"QLineEdit {"
			"background: #1E293B;"
			"border: 1px solid #334155;"
			"border-radius: 8px;"
			"color: #F1F5F9;"
			"padding: 8px 10px;"
			"}"
		)

		self.add_button = QPushButton("Add")
		self.add_button.clicked.connect(self.add_task)
		self.add_button.setStyleSheet(
			"QPushButton {"
			"background: #2563EB;"
			"color: #FFFFFF;"
			"border-radius: 8px;"
			"padding: 8px 14px;"
			"}"
		)

		input_layout.addWidget(self.input_edit, 1)
		input_layout.addWidget(self.add_button)
		main_layout.addLayout(input_layout)

		# Build a scrollable region that contains one TaskRow per todo item.
		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

		self.list_container = QWidget()
		self.list_layout = QVBoxLayout(self.list_container)
		self.list_layout.setContentsMargins(0, 0, 0, 0)
		self.list_layout.setSpacing(8)
		self.list_layout.addStretch()

		self.scroll_area.setWidget(self.list_container)
		main_layout.addWidget(self.scroll_area, 1)

		# Load and render saved tasks when the tab is created.
		self.load_tasks()

	def load_tasks(self) -> None:
		# Read all saved tasks from storage and display each as a TaskRow.
		self.refresh()

	def add_task(self) -> None:
		# Add a new task through the todo module, then reload the visible list.
		task_text = self.input_edit.text().strip()
		if not task_text:
			return

		todo.add_todo(task_text)
		self.input_edit.clear()
		self.refresh()

	def _complete_task(self, task_text: str) -> None:
		# Mark selected task as complete and re-render to show updated state.
		todo.complete_todo(task_text)
		self.refresh()

	def _delete_task(self, task_text: str) -> None:
		# Delete selected task and re-render the list.
		todo.delete_todo(task_text)
		self.refresh()

	def refresh(self) -> None:
		# Clear existing rows and rebuild the list from the latest storage snapshot.
		while self.list_layout.count() > 1:
			item = self.list_layout.takeAt(0)
			widget = item.widget()
			if widget:
				widget.deleteLater()

		for task_item in todo.get_all():
			row = TaskRow(task_item, self._complete_task, self._delete_task)
			self.list_layout.insertWidget(self.list_layout.count() - 1, row)
