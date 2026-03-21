"""Finance page for analyzing bank statement CSVs."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QFileDialog,
	QHBoxLayout,
	QLabel,
	QPushButton,
	QTextEdit,
	QVBoxLayout,
	QWidget,
)

from modules import finance


class FinancePage(QWidget):
	"""Finance page for uploading and analyzing CSV bank statements."""

	def __init__(self) -> None:
		super().__init__()
		self.setStyleSheet("background: #111;")

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(16, 16, 16, 16)
		main_layout.setSpacing(14)

		title = QLabel("Finance Analyzer")
		title.setStyleSheet("font-size: 18px; font-weight: 700; color: #ccc;")
		main_layout.addWidget(title)

		subtitle = QLabel("Upload a CSV bank statement with Date, Description, Amount columns.")
		subtitle.setWordWrap(True)
		subtitle.setStyleSheet("color: #555; font-size: 13px; background: transparent;")
		main_layout.addWidget(subtitle)

		# Upload card.
		upload_container = QWidget()
		upload_container.setStyleSheet(
			"QWidget#uploadCard {"
			"background: #1a1a1a; border: 1px dashed #2a2a2a; border-radius: 10px;"
			"}"
		)
		upload_container.setObjectName("uploadCard")
		upload_layout = QVBoxLayout(upload_container)
		upload_layout.setContentsMargins(20, 20, 20, 20)
		upload_layout.setSpacing(10)
		upload_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.file_label = QLabel("No file selected")
		self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.file_label.setStyleSheet("color: #666; font-size: 13px; background: transparent;")
		upload_layout.addWidget(self.file_label)

		btn_row = QHBoxLayout()
		btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
		btn_row.setSpacing(10)

		browse_btn = QPushButton("Browse CSV")
		browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		browse_btn.setStyleSheet(
			"QPushButton {"
			"background: #333; color: #ccc; border: none;"
			"border-radius: 8px; padding: 10px 20px;"
			"font-size: 13px; font-weight: 600;"
			"}"
			"QPushButton:hover { background: #444; }"
		)
		browse_btn.clicked.connect(self._browse_file)
		btn_row.addWidget(browse_btn)

		self.analyze_btn = QPushButton("Analyze")
		self.analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		self.analyze_btn.setEnabled(False)
		self.analyze_btn.setStyleSheet(
			"QPushButton {"
			"background: #333; color: #ccc; border: none;"
			"border-radius: 8px; padding: 10px 20px;"
			"font-size: 13px; font-weight: 600;"
			"}"
			"QPushButton:hover { background: #444; }"
			"QPushButton:disabled { background: #1a1a1a; color: #444; }"
		)
		self.analyze_btn.clicked.connect(self._run_analysis)
		btn_row.addWidget(self.analyze_btn)

		upload_layout.addLayout(btn_row)
		main_layout.addWidget(upload_container)

		# Results.
		self.results_box = QTextEdit()
		self.results_box.setReadOnly(True)
		self.results_box.setPlaceholderText("Analysis results will appear here...")
		self.results_box.setStyleSheet(
			"QTextEdit {"
			"background: #1a1a1a; color: #ccc;"
			"border: 1px solid #222; border-radius: 10px;"
			"padding: 14px; font-size: 13px;"
			"}"
		)
		main_layout.addWidget(self.results_box, 1)

		self._selected_file = ""

	def _browse_file(self) -> None:
		file_path, _ = QFileDialog.getOpenFileName(
			self, "Select CSV file", "", "CSV files (*.csv);;All files (*)"
		)
		if file_path:
			self._selected_file = file_path
			name = file_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
			self.file_label.setText(name)
			self.file_label.setStyleSheet("color: #ccc; font-size: 13px; background: transparent;")
			self.analyze_btn.setEnabled(True)

	def _run_analysis(self) -> None:
		if not self._selected_file:
			return
		result = finance.analyze(self._selected_file)
		self.results_box.setPlainText(result)
