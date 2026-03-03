"""Punto de entrada para la GUI Qt.

Ejecutar:
    python -m src.infrastructure.gui_main
"""

import sys

from PySide6.QtWidgets import QApplication

from src.adapters.primary.gui import MainWindow
from src.infrastructure.reader_app import ReaderApp


def main() -> int:
    reader = ReaderApp()
    app = QApplication(sys.argv)
    window = MainWindow(reader)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
