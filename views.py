from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config_dialog import ConfigDialog
from model import SSHKeyNotFoundError, apply_identity, load_identities, save_identities


class MainWindow(QMainWindow):
    """
    Main neon window: logo + identity list + quick actions.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Git Identity Switcher")
        self.resize(920, 520)
        self.setMinimumSize(820, 440)
        self.setAttribute(Qt.WA_StyledBackground, True)

        # data
        self._identities: List[Dict] = load_identities()
        self._logo_pixmap: Optional[QPixmap] = None

        # animation members must be kept on self so they are not GC'd
        self._fade_effect: Optional[QGraphicsOpacityEffect] = None
        self._fade_anim: Optional[QPropertyAnimation] = None

        self._build_ui()
        self._load_logo()
        self._populate_table()
        self._fade_in()

    # ---------- UI ---------- #

    def _build_ui(self) -> None:
        central: QWidget = QWidget(self)
        root_layout: QVBoxLayout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(12)

        # Top: header card
        header_card: QFrame = QFrame(central)
        header_card.setObjectName("headerCard")
        header_layout: QHBoxLayout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.setSpacing(16)

        self.logo_label: QLabel = QLabel(header_card)
        self.logo_label.setFixedSize(200, 200)
        self.logo_label.setScaledContents(True)
        header_layout.addWidget(self.logo_label)

        text_block: QVBoxLayout = QVBoxLayout()
        title_label: QLabel = QLabel("Git Identity Switcher", header_card)
        title_label.setObjectName("headerTitle")
        subtitle_label: QLabel = QLabel(
            "Neon-glossy switching between multiple Git + SSH profiles.",
            header_card,
        )
        subtitle_label.setObjectName("headerSubtitle")
        subtitle_label.setWordWrap(True)

        text_block.addWidget(title_label)
        text_block.addWidget(subtitle_label)
        text_block.addStretch(1)
        header_layout.addLayout(text_block)

        root_layout.addWidget(header_card)

        # Middle: main glass area
        main_row: QHBoxLayout = QHBoxLayout()
        main_row.setSpacing(16)

        # Identities glass card
        table_card: QFrame = QFrame(central)
        table_card.setObjectName("glassCard")
        table_layout: QVBoxLayout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(6)

        list_label: QLabel = QLabel("Identities", table_card)
        list_label.setProperty("class", "sectionTitle")
        table_layout.addWidget(list_label)

        self.table: QTableWidget = QTableWidget(0, 2, table_card)
        self.table.setHorizontalHeaderLabels(["Profile", "Email"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table_layout.addWidget(self.table)

        main_row.addWidget(table_card, 3)

        # Quick actions glass card
        actions_card: QFrame = QFrame(central)
        actions_card.setObjectName("glassCard")
        actions_layout: QVBoxLayout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(12, 12, 12, 12)
        actions_layout.setSpacing(10)

        actions_title: QLabel = QLabel("Quick actions", actions_card)
        actions_title.setProperty("class", "sectionTitle")
        actions_layout.addWidget(actions_title)

        self.switch_btn: QPushButton = QPushButton(
            "Switch to selected identity",
            actions_card,
        )
        self.switch_btn.setProperty("class", "accent")
        self.switch_btn.clicked.connect(self._on_switch_identity)

        manage_btn: QPushButton = QPushButton("Manage identities…", actions_card)
        manage_btn.setProperty("class", "secondary")
        manage_btn.clicked.connect(self._on_manage_identities)

        actions_layout.addWidget(self.switch_btn)
        actions_layout.addWidget(manage_btn)
        actions_layout.addStretch(1)

        main_row.addWidget(actions_card, 1)

        root_layout.addLayout(main_row)

        # Bottom status line
        self.status_label: QLabel = QLabel("", central)
        self.status_label.setObjectName("statusLabel")
        root_layout.addWidget(self.status_label)

        self.setCentralWidget(central)

    # ---------- data ---------- #

    def _load_logo(self) -> None:
        base_dir: Path = Path(__file__).resolve().parent
        icon_path: Path = base_dir / "icons" / "GIS.png"
        if icon_path.exists():
            self._logo_pixmap = QPixmap(str(icon_path))
            self.logo_label.setPixmap(self._logo_pixmap)
            self.setWindowIcon(QIcon(self._logo_pixmap))

    def _populate_table(self) -> None:
        self.table.setRowCount(0)
        for row, ident in enumerate(self._identities):
            self.table.insertRow(row)
            profile_item: QTableWidgetItem = QTableWidgetItem(
                ident.get("name", "Unnamed"),
            )
            email_item: QTableWidgetItem = QTableWidgetItem(
                ident.get("git_email", ""),
            )
            self.table.setItem(row, 0, profile_item)
            self.table.setItem(row, 1, email_item)

        count: int = len(self._identities)
        if count == 0:
            self.status_label.setText(
                "No identities yet. Click “Manage identities…” to create one.",
            )
            self.switch_btn.setEnabled(False)
        else:
            self.status_label.setText(f"Configured identities: {count}")
            self.switch_btn.setEnabled(True)

    # ---------- actions ---------- #

    def _current_index(self) -> Optional[int]:
        row: int = self.table.currentRow()
        if row < 0 or row >= len(self._identities):
            return None
        return row

    def _on_switch_identity(self) -> None:
        index: Optional[int] = self._current_index()
        if index is None:
            QMessageBox.warning(
                self,
                "No selection",
                "Select an identity from the list first.",
            )
            return

        identity: Dict = self._identities[index]
        try:
            summary: str = apply_identity(identity)
        except SSHKeyNotFoundError as exc:
            QMessageBox.critical(
                self,
                "SSH key not found",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Identity switched",
            summary,
        )

    def _on_manage_identities(self) -> None:
        dialog: ConfigDialog = ConfigDialog(self, identities=self._identities)
        dialog.exec()
        self._identities = dialog.get_identities()
        save_identities(self._identities)
        self._populate_table()

    # ---------- animation ---------- #

    def _fade_in(self) -> None:
        """
        Fade-in animation for the whole window.

        IMPORTANT: keep references on self so the animation is not
        garbage-collected while running; otherwise opacity could stay at 0.
        """
        self._fade_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._fade_effect)

        self._fade_anim = QPropertyAnimation(self._fade_effect, b"opacity", self)
        self._fade_anim.setDuration(260)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._fade_anim.start()
