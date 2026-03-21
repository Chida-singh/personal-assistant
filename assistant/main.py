# ============================================
# Local AI Assistant
# Run:     python main.py
# Requires: Ollama running -> ollama serve
#           Model pulled  -> ollama pull llama3
# Install:  pip install -r requirements.txt
# ============================================

import sys

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


if __name__ == "__main__":
	# Create the Qt application instance for the desktop UI.
	app = QApplication(sys.argv)
	app.setApplicationName("Local AI Assistant")

	# Apply a dark palette so base widget colors are consistent app-wide.
	palette = QPalette()
	palette.setColor(QPalette.ColorRole.Window, QColor("#0F172A"))
	palette.setColor(QPalette.ColorRole.WindowText, QColor("#F1F5F9"))
	palette.setColor(QPalette.ColorRole.Base, QColor("#1E293B"))
	palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#0F172A"))
	palette.setColor(QPalette.ColorRole.Text, QColor("#F1F5F9"))
	palette.setColor(QPalette.ColorRole.Button, QColor("#1E293B"))
	palette.setColor(QPalette.ColorRole.ButtonText, QColor("#F1F5F9"))
	palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563EB"))
	palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
	app.setPalette(palette)

	# Build and show the main window, then start the event loop.
	window = MainWindow()
	window.show()
	sys.exit(app.exec())
