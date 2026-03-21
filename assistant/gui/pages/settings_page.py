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
	QScrollArea,
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
		self.setStyleSheet("background: #111;")

		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

		content = QWidget()
		main_layout = QVBoxLayout(content)
		main_layout.setContentsMargins(16, 16, 16, 16)
		main_layout.setSpacing(14)

		title = QLabel("Settings")
		title.setStyleSheet("font-size: 18px; font-weight: 700; color: #ccc;")
		main_layout.addWidget(title)

		main_layout.addWidget(self._build_llm_section())
		main_layout.addWidget(self._build_voice_section())
		main_layout.addWidget(self._build_data_section())
		main_layout.addWidget(self._build_export_section())
		main_layout.addStretch(1)

		scroll.setWidget(content)

		outer = QVBoxLayout(self)
		outer.setContentsMargins(0, 0, 0, 0)
		outer.addWidget(scroll)

	def _build_llm_section(self) -> QWidget:
		section = self._section("LLM Settings")
		layout = section.layout()

		model_label = QLabel("Ollama Model")
		model_label.setStyleSheet("color: #888; font-size: 12px; font-weight: 600; background: transparent; border: none;")
		layout.addWidget(model_label)

		self.model_combo = QComboBox()
		self.model_combo.addItems(["llama3", "qwen2.5", "mistral", "deepseek-r1", "gemma", "phi3", "codellama"])
		self.model_combo.setCurrentText(llm.DEFAULT_MODEL)
		self.model_combo.setStyleSheet(
			"QComboBox {"
			"background: #111; color: #ccc;"
			"border: 1px solid #2a2a2a; border-radius: 8px;"
			"padding: 8px 10px; font-size: 13px;"
			"}"
			"QComboBox::drop-down { border: none; }"
			"QComboBox QAbstractItemView {"
			"background: #1a1a1a; color: #ccc;"
			"border: 1px solid #333;"
			"selection-background-color: #333;"
			"}"
		)
		layout.addWidget(self.model_combo)

		url_label = QLabel("Ollama Base URL")
		url_label.setStyleSheet("color: #888; font-size: 12px; font-weight: 600; background: transparent; border: none;")
		layout.addWidget(url_label)

		self.url_input = QLineEdit(self._extract_base_url(llm.BASE_URL))
		self.url_input.setPlaceholderText("http://localhost:11434")
		self.url_input.setStyleSheet(
			"QLineEdit {"
			"background: #111; border: 1px solid #2a2a2a; border-radius: 8px;"
			"color: #ccc; padding: 8px 12px; font-size: 13px;"
			"}"
			"QLineEdit:focus { border-color: #444; }"
		)
		layout.addWidget(self.url_input)

		save_button = QPushButton("Save Settings")
		save_button.setCursor(Qt.CursorShape.PointingHandCursor)
		save_button.clicked.connect(self.save_llm_settings)
		save_button.setStyleSheet(self._btn_style())
		layout.addWidget(save_button)

		return section

	def _build_voice_section(self) -> QWidget:
		section = self._section("Voice Settings")
		layout = section.layout()

		duration_label = QLabel("Recording Duration (seconds)")
		duration_label.setStyleSheet("color: #888; font-size: 12px; font-weight: 600; background: transparent; border: none;")
		layout.addWidget(duration_label)

		self.duration_spin = QSpinBox()
		self.duration_spin.setRange(3, 15)
		self.duration_spin.setValue(int(VoiceRecorder.default_duration))
		self.duration_spin.setStyleSheet(
			"QSpinBox {"
			"background: #111; color: #ccc;"
			"border: 1px solid #2a2a2a; border-radius: 8px;"
			"padding: 8px 10px; font-size: 13px;"
			"}"
			"QSpinBox::up-button, QSpinBox::down-button {"
			"background: #2a2a2a; border: none; width: 20px;"
			"}"
		)
		self.duration_spin.valueChanged.connect(self.update_voice_duration)
		layout.addWidget(self.duration_spin)

		return section

	def _build_data_section(self) -> QWidget:
		section = self._section("Data Management")
		layout = section.layout()

		for label, file, msg in [
			("Clear Chat History", CHAT_FILE, "Chat history cleared."),
			("Clear Todo List", TODOS_FILE, "Todo list cleared."),
			("Clear Notes", GIRLFRIEND_FILE, "Notes cleared."),
		]:
			btn = QPushButton(label)
			btn.setCursor(Qt.CursorShape.PointingHandCursor)
			btn.clicked.connect(lambda _, f=file, m=msg: self.clear_data_file(f, m))
			btn.setStyleSheet(self._danger_btn_style())
			layout.addWidget(btn)

		return section

	def _build_export_section(self) -> QWidget:
		section = self._section("Export")
		layout = section.layout()

		export_button = QPushButton("Export Chat")
		export_button.setCursor(Qt.CursorShape.PointingHandCursor)
		export_button.setStyleSheet(self._btn_style())
		export_button.clicked.connect(self.export_chat)
		layout.addWidget(export_button)

		return section

	def save_llm_settings(self) -> None:
		model = self.model_combo.currentText().strip() or "llama3"
		base_url = self.url_input.text().strip() or "http://localhost:11434"
		chat_url = self._build_chat_url(base_url)
		llm.configure(base_url=chat_url, model=model)
		QMessageBox.information(self, "Settings", "LLM settings saved.")

	def update_voice_duration(self, seconds: int) -> None:
		VoiceRecorder.default_duration = int(seconds)

	def clear_data_file(self, filename: str, message: str) -> None:
		save(filename, [])
		QMessageBox.information(self, "Data Management", message)

	def export_chat(self) -> None:
		messages = load(CHAT_FILE)
		export_path = Path(__file__).resolve().parents[2] / "chat_export.txt"
		lines = []
		for item in messages:
			role = str(item.get("role", "assistant")).title()
			content = str(item.get("content", "")).strip()
			if content:
				lines.append(f"{role}: {content}")
		export_path.write_text("\n".join(lines), encoding="utf-8")
		QMessageBox.information(self, "Export", "Chat exported to chat_export.txt")

	def _section(self, title: str) -> QFrame:
		frame = QFrame()
		frame.setStyleSheet(
			"QFrame { background: #1a1a1a; border: 1px solid #222; border-radius: 10px; }"
		)
		layout = QVBoxLayout(frame)
		layout.setContentsMargins(14, 14, 14, 14)
		layout.setSpacing(10)
		header = QLabel(title)
		header.setStyleSheet(
			"color: #ccc; font-size: 14px; font-weight: 700;"
			"background: transparent; border: none;"
		)
		layout.addWidget(header)
		return frame

	@staticmethod
	def _btn_style() -> str:
		return (
			"QPushButton {"
			"background: #333; color: #ccc; border: none; border-radius: 8px;"
			"padding: 10px 18px; font-size: 13px; font-weight: 600;"
			"}"
			"QPushButton:hover { background: #444; }"
		)

	@staticmethod
	def _danger_btn_style() -> str:
		return (
			"QPushButton {"
			"background: transparent; color: #666;"
			"border: 1px solid #2a2a2a; border-radius: 8px;"
			"padding: 10px 14px; font-size: 13px; font-weight: 600; text-align: left;"
			"}"
			"QPushButton:hover { background: #1a0a0a; color: #c55; border-color: #c55; }"
		)

	def _extract_base_url(self, chat_url: str) -> str:
		trimmed = chat_url.strip()
		suffix = "/api/chat"
		if trimmed.endswith(suffix):
			return trimmed[: -len(suffix)]
		return trimmed

	def _build_chat_url(self, base_url: str) -> str:
		clean = base_url.strip().rstrip("/")
		if clean.endswith("/api/chat"):
			return clean
		return f"{clean}/api/chat"
