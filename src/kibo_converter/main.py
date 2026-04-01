# Responsibility: Application entry point; start Qt event loop and main window.

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from kibo_converter.ui.main_window import MainWindow


def main() -> None:
    """Start the desktop application."""
    application = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()
