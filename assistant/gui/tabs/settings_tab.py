"""Settings tab for runtime model/voice preferences and data utilities."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QComboBox,
	QFrame,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMessageBox,
	QPushButton,
	QSpinBox,
	QVBoxLayout,
	QWidget,
)

from core import llm
from core.storage import CHAT_FILE, GIRLFRIEND_FILE, TODOS_FILE, load, save
from core.voice import VoiceRecorder


class SettingsTab(QWidget):
	"""Runtime settings page for model config, voice config, and data actions."""

	def __init__(self) -> None:
		super().__init__()
		self.setStyleSheet("background: #0F172A;")

		# Build vertical page layout for title and all settings sections.
		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(16, 16, 16, 16)
		main_layout.setSpacing(12)

		title = QLabel("⚙ Settings")
		title.setStyleSheet(
			"font-family: 'Segoe UI'; font-size: 18px; font-weight: 700; color: #F1F5F9;"
		)
		main_layout.addWidget(title)

		main_layout.addWidget(self._build_llm_section())
		main_layout.addWidget(self._build_voice_section())
		main_layout.addWidget(self._build_data_section())
		main_layout.addWidget(self._build_export_section())
		main_layout.addStretch(1)

	def _build_llm_section(self) -> QWidget:
		# LLM controls for model choice and Ollama base URL.
		section = self._create_section_container("LLM Settings")
		layout = section.layout()

		model_label = QLabel("Ollama Model")
		model_label.setStyleSheet("color: #CBD5E1; font-size: 12px;")
		layout.addWidget(model_label)

		self.model_combo = QComboBox()
		self.model_combo.addItems(["llama3", "mistral", "gemma", "phi3"])
		self.model_combo.setCurrentText(llm.DEFAULT_MODEL)
		self.model_combo.setStyleSheet(
			"QComboBox {"
			"background: #1E293B;"
			"color: #F1F5F9;"
			"border: 1px solid #334155;"
			"border-radius: 8px;"
			"padding: 6px 8px;"
			"}"
		)
		layout.addWidget(self.model_combo)

		url_label = QLabel("Ollama Base URL")
		url_label.setStyleSheet("color: #CBD5E1; font-size: 12px;")
		layout.addWidget(url_label)

		self.url_input = QLineEdit(self._extract_base_url(llm.BASE_URL))
		self.url_input.setPlaceholderText("http://localhost:11434")
		self.url_input.setStyleSheet(
			"QLineEdit {"
			"background: #1E293B;"
			"border: 1px solid #334155;"
			"border-radius: 8px;"
			"color: #F1F5F9;"
			"padding: 6px 10px;"
			"}"
		)
		layout.addWidget(self.url_input)

		save_button = QPushButton("Save Settings")
		save_button.clicked.connect(self.save_llm_settings)
		save_button.setStyleSheet(self._button_style())
		layout.addWidget(save_button)

		return section

	def _build_voice_section(self) -> QWidget:
		# Voice controls for speech recording duration.
		section = self._create_section_container("Voice Settings")
		layout = section.layout()

		duration_label = QLabel("Recording Duration (seconds)")
		duration_label.setStyleSheet("color: #CBD5E1; font-size: 12px;")
		layout.addWidget(duration_label)

		self.duration_spin = QSpinBox()
		self.duration_spin.setRange(3, 15)
		self.duration_spin.setValue(int(VoiceRecorder.default_duration))
		self.duration_spin.setStyleSheet(
			"QSpinBox {"
			"background: #1E293B;"
			"color: #F1F5F9;"
			"border: 1px solid #334155;"
			"border-radius: 8px;"
			"padding: 6px 8px;"
			"}"
		)
		self.duration_spin.valueChanged.connect(self.update_voice_duration)
		layout.addWidget(self.duration_spin)

		return section

	def _build_data_section(self) -> QWidget:
		# Data management controls for clearing individual JSON stores.
		section = self._create_section_container("Data Management")
		layout = section.layout()

		chat_button = QPushButton("🗑 Clear Chat History")
		chat_button.clicked.connect(lambda: self.clear_data_file(CHAT_FILE, "Chat history cleared."))

		todo_button = QPushButton("🗑 Clear Todo List")
		todo_button.clicked.connect(lambda: self.clear_data_file(TODOS_FILE, "Todo list cleared."))

		notes_button = QPushButton("🗑 Clear Girlfriend Notes")
		notes_button.clicked.connect(
			lambda: self.clear_data_file(GIRLFRIEND_FILE, "Girlfriend notes cleared.")
		)

		for button in (chat_button, todo_button, notes_button):
			button.setStyleSheet(self._button_style())
			layout.addWidget(button)

		return section

	def _build_export_section(self) -> QWidget:
		# Export controls for writing chat history to a plain text file.
		section = self._create_section_container("Export")
		layout = section.layout()

		export_button = QPushButton("💾 Export Chat")
		export_button.setStyleSheet(self._button_style())
		export_button.clicked.connect(self.export_chat)
		layout.addWidget(export_button)

		return section

	def save_llm_settings(self) -> None:
		# Persist selected LLM model and endpoint in runtime module config.
		model = self.model_combo.currentText().strip() or "llama3"
		base_url = self.url_input.text().strip() or "http://localhost:11434"
		chat_url = self._build_chat_url(base_url)
		llm.configure(base_url=chat_url, model=model)

		QMessageBox.information(self, "Settings", "LLM settings saved.")

	def update_voice_duration(self, seconds: int) -> None:
		# Update shared recorder duration so future recordings use this value.
		VoiceRecorder.default_duration = int(seconds)
		QMessageBox.information(self, "Settings", f"Voice recording duration set to {seconds} seconds.")

	def clear_data_file(self, filename: str, message: str) -> None:
		# Replace selected JSON data file with an empty list and confirm to user.
		save(filename, [])
		QMessageBox.information(self, "Data Management", message)

	def export_chat(self) -> None:
		# Write chat history entries to chat_export.txt in the assistant project root.
		messages = load(CHAT_FILE)
		export_path = Path(__file__).resolve().parents[2] / "chat_export.txt"

		lines: list[str] = []
		for item in messages:
			role = str(item.get("role", "assistant")).title()
			content = str(item.get("content", "")).strip()
			if content:
				lines.append(f"{role}: {content}")

		export_path.write_text("\n".join(lines), encoding="utf-8")
		QMessageBox.information(self, "Export", "Chat exported to chat_export.txt")

	def _create_section_container(self, title: str) -> QFrame:
		# Helper to keep section cards visually consistent in the dark theme.
		frame = QFrame()
		frame.setStyleSheet(
			"QFrame {"
			"background: #1E293B;"
			"border: 1px solid #334155;"
			"border-radius: 10px;"
			"}"
		)

		layout = QVBoxLayout(frame)
		layout.setContentsMargins(12, 12, 12, 12)
		layout.setSpacing(8)

		header = QLabel(title)
		header.setStyleSheet("color: #F1F5F9; font-size: 13px; font-weight: 700;")
		header.setAlignment(Qt.AlignmentFlag.AlignLeft)
		layout.addWidget(header)

		return frame

	def _button_style(self) -> str:
		# Shared button style for a consistent action look across sections.
		return (
			"QPushButton {"
			"background: #2563EB;"
			"color: #FFFFFF;"
			"border: none;"
			"border-radius: 8px;"
			"padding: 8px 12px;"
			"font-family: 'Segoe UI';"
			"font-size: 12px;"
			"font-weight: 600;"
			"}"
			"QPushButton:hover {"
			"background: #1D4ED8;"
			"}"
		)

	def _extract_base_url(self, chat_url: str) -> str:
		# Convert full chat endpoint into the editable base URL shown in UI.
		trimmed = chat_url.strip()
		suffix = "/api/chat"
		if trimmed.endswith(suffix):
			return trimmed[: -len(suffix)]
		return trimmed

	def _build_chat_url(self, base_url: str) -> str:
		# Normalize user input so runtime config always targets Ollama chat endpoint.
		clean = base_url.strip().rstrip("/")
		if clean.endswith("/api/chat"):
			return clean
		return f"{clean}/api/chat"
