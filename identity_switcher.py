from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from views import MainWindow


QSS_RELATIVE_PATH: Final[str] = "styles/neon.qss"


def _set_dark_palette(app: QApplication) -> None:
    palette: QPalette = QPalette()
    palette.setColor(QPalette.Window, QColor("#050816"))
    palette.setColor(QPalette.WindowText, QColor("#F9FAFB"))
    palette.setColor(QPalette.Base, QColor("#020617"))
    palette.setColor(QPalette.AlternateBase, QColor("#020617"))
    palette.setColor(QPalette.Text, QColor("#F9FAFB"))
    palette.setColor(QPalette.Button, QColor("#0f172a"))
    palette.setColor(QPalette.ButtonText, QColor("#F9FAFB"))
    palette.setColor(QPalette.ToolTipBase, QColor("#111827"))
    palette.setColor(QPalette.ToolTipText, QColor("#F9FAFB"))
    palette.setColor(QPalette.Highlight, QColor("#38bdf8"))
    palette.setColor(QPalette.HighlightedText, QColor("#0b1120"))
    app.setPalette(palette)


def _load_stylesheet(app: QApplication) -> None:
    base_dir: Path = Path(__file__).resolve().parent
    qss_path: Path = base_dir / QSS_RELATIVE_PATH

    if not qss_path.exists():
        print(f"[WARN] Stylesheet not found at {qss_path}, running without it.")
        return

    try:
        qss: str = qss_path.read_text(encoding="utf-8")
        app.setStyleSheet(qss)
        print(f"[INFO] Loaded stylesheet from {qss_path}")
    except Exception as exc:
        print(f"[WARN] Failed to load stylesheet: {exc}")


def main() -> None:
    app: QApplication = QApplication(sys.argv)

    _set_dark_palette(app)
    _load_stylesheet(app)

    window: MainWindow = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
