from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QGraphicsOpacityEffect,
)

from model import SSHKeyNotFoundError, apply_identity, load_identities, save_identities
from widgets import AddIdentityCard, GlassFrame, IdentityCard


class MainWindow(QMainWindow):
    """
    Main neon window:
    - Splash animation on startup
    - Identity cards in the middle (PS login vibes)
    - Inline select / edit / delete flows
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Git Identity Switcher")
        # Fixed size, no resize / maximize.
        self.setFixedSize(1100, 620)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)

        self._identities: List[Dict] = load_identities()
        self._logo_pixmap: Optional[QPixmap] = None

        self._cards_container: Optional[QWidget] = None
        self._cards_layout: Optional[QHBoxLayout] = None
        self._status_label: Optional[QLabel] = None

        self._splash: Optional[QWidget] = None
        self._splash_anim: Optional[QPropertyAnimation] = None

        self._build_ui()
        self._load_logo()
        self._rebuild_cards()
        self._show_splash()

    # ---------- UI construction ---------- #

    def _build_ui(self) -> None:
        central: QWidget = QWidget(self)
        root_layout: QVBoxLayout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(12)

        # Header card with logo + text
        header_card: GlassFrame = GlassFrame(central, variant="header")
        header_layout: QHBoxLayout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.setSpacing(16)

        self.logo_label: QLabel = QLabel(header_card)
        self.logo_label.setFixedSize(160, 160)
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

        # Middle: scrollable row of identity cards
        cards_frame: GlassFrame = GlassFrame(central, variant="glass")
        cards_layout_outer: QVBoxLayout = QVBoxLayout(cards_frame)
        cards_layout_outer.setContentsMargins(12, 12, 12, 12)
        cards_layout_outer.setSpacing(8)

        list_label: QLabel = QLabel("Identities", cards_frame)
        list_label.setProperty("class", "sectionTitle")
        cards_layout_outer.addWidget(list_label)

        scroll: QScrollArea = QScrollArea(cards_frame)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._cards_container = QWidget(scroll)
        self._cards_layout = QHBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(4, 4, 4, 4)
        self._cards_layout.setSpacing(16)
        self._cards_layout.addStretch(1)

        scroll.setWidget(self._cards_container)
        cards_layout_outer.addWidget(scroll)

        root_layout.addWidget(cards_frame, 1)

        # Bottom status line
        status_frame: GlassFrame = GlassFrame(central, variant="glass")
        status_layout: QHBoxLayout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 6, 12, 6)
        status_layout.setSpacing(8)

        self._status_label = QLabel("", status_frame)
        self._status_label.setObjectName("statusLabel")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch(1)

        root_layout.addWidget(status_frame)

        self.setCentralWidget(central)

    # ---------- logo / identities ---------- #

    def _load_logo(self) -> None:
        base_dir: Path = Path(__file__).resolve().parent
        icon_path: Path = base_dir / "icons" / "GIS.png"
        if icon_path.exists():
            self._logo_pixmap = QPixmap(str(icon_path))
            self.logo_label.setPixmap(self._logo_pixmap)
            self.setWindowIcon(QIcon(self._logo_pixmap))

    def _rebuild_cards(self) -> None:
        if self._cards_container is None or self._cards_layout is None:
            return

        # Clear layout except trailing stretch
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index, ident in enumerate(self._identities):
            card: IdentityCard = IdentityCard(
                index=index,
                identity=ident,
                on_select=self._select_identity,
                on_update=self._update_identity,
                on_delete=self._delete_identity,
                parent=self._cards_container,
            )
            card.setFixedSize(280, 220)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

        # Add "new identity" card at end
        add_card: AddIdentityCard = AddIdentityCard(
            on_add=self._create_identity,
            parent=self._cards_container,
        )
        add_card.setFixedSize(230, 180)
        self._cards_layout.insertWidget(self._cards_layout.count() - 1, add_card)

        count: int = len(self._identities)
        if count == 0:
            self._set_status("No identities yet. Click “+ New identity” to create one.")
        else:
            self._set_status(f"Configured identities: {count}")

    # ---------- status helper ---------- #

    def _set_status(self, text: str) -> None:
        if self._status_label is not None:
            self._status_label.setText(text)

    # ---------- callbacks from cards ---------- #

    def _select_identity(self, index: int) -> None:
        if index < 0 or index >= len(self._identities):
            return

        identity: Dict = self._identities[index]
        try:
            summary: str = apply_identity(identity)
        except SSHKeyNotFoundError as exc:
            self._set_status(f"SSH key not found: {exc}")
            return

        self._set_status(summary)

    def _update_identity(self, index: int, updated: Dict) -> None:
        if index < 0 or index >= len(self._identities):
            return

        self._identities[index] = updated
        save_identities(self._identities)
        self._rebuild_cards()
        name: str = updated.get("name", "Unnamed")
        self._set_status(f"Updated identity “{name or 'Unnamed'}”")

    def _delete_identity(self, index: int) -> None:
        if index < 0 or index >= len(self._identities):
            return

        ident: Dict = self._identities.pop(index)
        save_identities(self._identities)
        self._rebuild_cards()
        name: str = ident.get("name", "Unnamed")
        self._set_status(f"Deleted identity “{name or 'Unnamed'}”")

    def _create_identity(self) -> None:
        # Simple default; user edits inline afterwards
        new: Dict = {
            "name": "New profile",
            "git_name": "",
            "git_email": "",
            "ssh_key_path": "",
        }
        self._identities.append(new)
        save_identities(self._identities)
        self._rebuild_cards()
        self._set_status("New identity created. Click it to edit.")

    # ---------- splash animation ---------- #

    def _show_splash(self) -> None:
        """
        Simple overlay: large GIS logo fades out, then reveals cards.
        """
        if self._logo_pixmap is None:
            return  # nothing fancy if we have no logo

        self._splash = QWidget(self)
        self._splash.setObjectName("splashOverlay")
        self._splash.setAttribute(Qt.WA_StyledBackground, True)
        self._splash.setGeometry(self.rect())

        layout: QVBoxLayout = QVBoxLayout(self._splash)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        logo_label: QLabel = QLabel(self._splash)
        logo_label.setPixmap(self._logo_pixmap.scaled(
            260,
            260,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        ))
        layout.addWidget(logo_label)

        effect: QGraphicsOpacityEffect = QGraphicsOpacityEffect(self._splash)
        self._splash.setGraphicsEffect(effect)

        self._splash_anim = QPropertyAnimation(effect, b"opacity", self)
        self._splash_anim.setDuration(520)
        self._splash_anim.setStartValue(1.0)
        self._splash_anim.setEndValue(0.0)
        self._splash_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._splash_anim.finished.connect(self._hide_splash)

        self._splash.show()
        self._splash.raise_()

        # Let the user see the logo briefly, then fade out.
        QTimer.singleShot(500, self._splash_anim.start)

    def _hide_splash(self) -> None:
        if self._splash is not None:
            self._splash.hide()
            self._splash.deleteLater()
            self._splash = None
