# ============================================
# Local AI Assistant
# Run:     python main.py
# Requires: Ollama running -> ollama serve
#           Model pulled  -> ollama pull llama3
# Install:  pip install -r requirements.txt
# ============================================

import sys
import ctypes
from pathlib import Path

from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


if __name__ == "__main__":
	# On Windows, set an explicit AppUserModelID so taskbar icon mapping is stable.
	try:
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
			"chida.personalassistant.desktop"
		)
	except Exception:
		pass

	# Create the Qt application instance for the desktop UI.
	app = QApplication(sys.argv)
	app.setApplicationName("Local AI Assistant")
	app.setFont(QFont("Segoe UI", 10))

	# Load and apply the app icon so the logo appears on window chrome and taskbar.
	icon_path = Path(__file__).resolve().parent.parent / "logo.png"
	if icon_path.exists():
		app.setWindowIcon(QIcon(str(icon_path)))

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
	if icon_path.exists():
		window.setWindowIcon(QIcon(str(icon_path)))
	window.show()
	sys.exit(app.exec())
