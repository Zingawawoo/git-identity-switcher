from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from views import MainWindow


def main() -> None:
    # Absolutely minimal: no palette, no stylesheet.
    app: QApplication = QApplication(sys.argv)

    window: MainWindow = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
