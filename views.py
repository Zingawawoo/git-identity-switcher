from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from model import SSHKeyNotFoundError, apply_identity, load_identities, save_identities
from widgets import AddIdentityCard, EditPanel, GlassFrame, IdentityCard, NeonButton


class MainWindow(QMainWindow):
    """
    Warm PS5-style orb selector.

    - Page 0: orbs + Select/Edit/Delete bar.
    - Page 1: full-page editor.
    - Status bar at the bottom.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Git Identity Switcher")
        self.setFixedSize(1100, 620)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)

        self._identities: List[Dict] = load_identities()
        if len(self._identities) > 0:
            self._selected_index: int = 0
        else:
            self._selected_index = -1

        self._cards: List[IdentityCard] = []

        self._logo_pixmap: Optional[QPixmap] = None

        self._status_label: Optional[QLabel] = None
        self._status_effect: Optional[QGraphicsOpacityEffect] = None
        self._status_anim: Optional[QPropertyAnimation] = None

        self._pages: Optional[QStackedWidget] = None
        self._main_page: Optional[QWidget] = None
        self._edit_page: Optional[QWidget] = None
        self._main_page_effect: Optional[QGraphicsOpacityEffect] = None
        self._edit_page_effect: Optional[QGraphicsOpacityEffect] = None

        self._cards_container: Optional[QWidget] = None
        self._cards_layout: Optional[QHBoxLayout] = None

        self._btn_select: Optional[NeonButton] = None
        self._btn_edit: Optional[NeonButton] = None
        self._btn_delete: Optional[NeonButton] = None

        self._edit_panel: Optional[EditPanel] = None

        self._splash: Optional[QWidget] = None
        self._splash_anim: Optional[QPropertyAnimation] = None

        self._build_ui()
        self._init_status_animation()
        self._load_logo()
        self._rebuild_cards()
        self._sync_selection_state()
        self._show_splash()

    # ---------- UI construction ---------- #

    def _build_ui(self) -> None:
        central: QWidget = QWidget(self)
        root_layout: QVBoxLayout = QVBoxLayout(central)
        root_layout.setContentsMargins(24, 18, 24, 18)
        root_layout.setSpacing(12)

        # Stacked pages
        self._pages = QStackedWidget(central)
        root_layout.addWidget(self._pages, 1)

        self._build_main_page()
        self._build_edit_page()
        if self._main_page is not None:
            self._pages.setCurrentWidget(self._main_page)

        # Status card at bottom
        status_card: GlassFrame = GlassFrame(central, variant="glass")
        status_layout: QHBoxLayout = QHBoxLayout(status_card)
        status_layout.setContentsMargins(12, 8, 12, 8)
        status_layout.setSpacing(6)

        self._status_label = QLabel("", status_card)
        self._status_label.setObjectName("statusLabel")

        status_layout.addWidget(self._status_label)
        status_layout.addStretch(1)

        root_layout.addWidget(status_card)

        self.setCentralWidget(central)

    def _build_main_page(self) -> None:
        if self._pages is None:
            return

        page: QWidget = QWidget(self._pages)
        page_layout: QVBoxLayout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(10)

        profiles_card: GlassFrame = GlassFrame(page, variant="glass")
        profiles_layout: QVBoxLayout = QVBoxLayout(profiles_card)
        profiles_layout.setContentsMargins(16, 14, 16, 14)
        profiles_layout.setSpacing(10)

        title_label: QLabel = QLabel("Who is using this Git config?", profiles_card)
        title_label.setProperty("class", "sectionTitle")
        profiles_layout.addWidget(title_label)

        scroll: QScrollArea = QScrollArea(profiles_card)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._cards_container = QWidget(scroll)
        self._cards_layout = QHBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(4, 24, 4, 24)
        self._cards_layout.setSpacing(36)
        self._cards_layout.setAlignment(Qt.AlignHCenter)

        scroll.setWidget(self._cards_container)
        profiles_layout.addWidget(scroll)

        # Action bar
        action_row: QHBoxLayout = QHBoxLayout()
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(12)
        action_row.setAlignment(Qt.AlignHCenter)

        self._btn_select = NeonButton("Select", profiles_card, variant="accent")
        self._btn_edit = NeonButton("Edit", profiles_card, variant="secondary")
        self._btn_delete = NeonButton("Delete", profiles_card, variant="danger")

        self._btn_select.clicked.connect(self._select_current)
        self._btn_edit.clicked.connect(self._open_edit_page)
        self._btn_delete.clicked.connect(self._delete_current)

        action_row.addWidget(self._btn_select)
        action_row.addWidget(self._btn_edit)
        action_row.addWidget(self._btn_delete)

        profiles_layout.addLayout(action_row)

        page_layout.addWidget(profiles_card, 1)

        # Opacity effect
        main_effect: QGraphicsOpacityEffect = QGraphicsOpacityEffect(page)
        main_effect.setOpacity(1.0)
        page.setGraphicsEffect(main_effect)
        self._main_page_effect = main_effect

        self._pages.addWidget(page)
        self._main_page = page

    def _build_edit_page(self) -> None:
        if self._pages is None:
            return

        page: QWidget = QWidget(self._pages)
        page_layout: QVBoxLayout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(10)

        editor_card: GlassFrame = GlassFrame(page, variant="glass")
        editor_layout: QVBoxLayout = QVBoxLayout(editor_card)
        editor_layout.setContentsMargins(16, 14, 16, 14)
        editor_layout.setSpacing(10)

        self._edit_panel = EditPanel(
            on_save=self._save_edit,
            on_cancel=self._cancel_edit,
            parent=editor_card,
        )
        editor_layout.addWidget(self._edit_panel)

        page_layout.addWidget(editor_card, 1)

        edit_effect: QGraphicsOpacityEffect = QGraphicsOpacityEffect(page)
        edit_effect.setOpacity(0.0)
        page.setGraphicsEffect(edit_effect)
        self._edit_page_effect = edit_effect

        self._pages.addWidget(page)
        self._edit_page = page

    def _init_status_animation(self) -> None:
        if self._status_label is None:
            return

        effect: QGraphicsOpacityEffect = QGraphicsOpacityEffect(self._status_label)
        self._status_label.setGraphicsEffect(effect)
        self._status_effect = effect

        anim: QPropertyAnimation = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(200)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        self._status_anim = anim

    # ---------- logo / splash ---------- #

    def _load_logo(self) -> None:
        base_dir: Path = Path(__file__).resolve().parent
        icon_path: Path = base_dir / "icons" / "GIS.png"
        if not icon_path.exists():
            return

        self._logo_pixmap = QPixmap(str(icon_path))
        self.setWindowIcon(QIcon(self._logo_pixmap))

    # ---------- cards & selection ---------- #

    def _rebuild_cards(self) -> None:
        if self._cards_container is None or self._cards_layout is None:
            return

        while self._cards_layout.count() > 0:
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._cards = []

        for index, identity in enumerate(self._identities):
            card: IdentityCard = IdentityCard(
                index=index,
                identity=identity,
                on_clicked=self._on_card_clicked,
                parent=self._cards_container,
            )
            card.setFixedSize(200, 210)
            self._cards_layout.addWidget(card)
            self._cards.append(card)

        add_card: AddIdentityCard = AddIdentityCard(
            on_add=self._create_identity,
            parent=self._cards_container,
        )
        add_card.setFixedSize(200, 210)
        self._cards_layout.addWidget(add_card)

        count: int = len(self._identities)
        if count == 0:
            self._set_status("No profiles yet. Click the + orb to create one.")
        else:
            self._set_status(f"Configured identities: {count}")

    def _sync_selection_state(self) -> None:
        if len(self._identities) == 0:
            self._selected_index = -1
        else:
            if self._selected_index < 0:
                self._selected_index = 0
            if self._selected_index >= len(self._identities):
                self._selected_index = len(self._identities) - 1

        for i, card in enumerate(self._cards):
            card.set_selected(i == self._selected_index)

        has_sel: bool = self._selected_index != -1
        if self._btn_select is not None:
            self._btn_select.setEnabled(has_sel)
        if self._btn_edit is not None:
            self._btn_edit.setEnabled(has_sel)
        if self._btn_delete is not None:
            self._btn_delete.setEnabled(has_sel)

    def _on_card_clicked(self, index: int) -> None:
        if index < 0:
            return
        if index >= len(self._identities):
            return

        self._selected_index = index
        self._sync_selection_state()

    # ---------- helpers ---------- #

    def _current_identity(self) -> Optional[Dict]:
        if self._selected_index < 0:
            return None
        if self._selected_index >= len(self._identities):
            return None
        return self._identities[self._selected_index]

    def _set_status(self, text: str) -> None:
        if self._status_label is None:
            return

        self._status_label.setText(text)

        if self._status_effect is None or self._status_anim is None:
            return

        self._status_anim.stop()
        self._status_anim.setStartValue(0.0)
        self._status_anim.setEndValue(1.0)
        self._status_anim.start()

    # ---------- actions ---------- #

    def _select_current(self) -> None:
        identity: Optional[Dict] = self._current_identity()
        if identity is None:
            return

        try:
            summary: str = apply_identity(identity)
        except SSHKeyNotFoundError as exc:
            self._set_status(f"SSH key not found: {exc}")
            return

        self._set_status(summary)

    def _open_edit_page(self) -> None:
        identity: Optional[Dict] = self._current_identity()
        if identity is None:
            return
        if self._pages is None or self._edit_panel is None:
            return

        name: str = identity.get("name", "") or "Unnamed"

        self._edit_panel.set_title(f"Edit profile – {name}")
        self._edit_panel.set_identity(identity)
        self._fade_to_page(self._edit_page)

    def _save_edit(self) -> None:
        if self._edit_panel is None:
            return
        if self._selected_index < 0:
            return
        if self._selected_index >= len(self._identities):
            return

        data: Dict[str, str] = self._edit_panel.collect_data()

        updated: Dict = dict(self._identities[self._selected_index])
        updated.update(data)

        self._identities[self._selected_index] = updated
        save_identities(self._identities)

        self._rebuild_cards()
        self._sync_selection_state()
        self._fade_to_page(self._main_page)

        name: str = updated.get("name", "") or "Unnamed"
        self._set_status(f"Updated identity “{name}”")

    def _cancel_edit(self) -> None:
        self._fade_to_page(self._main_page)

    def _delete_current(self) -> None:
        if self._selected_index < 0:
            return
        if self._selected_index >= len(self._identities):
            return

        ident: Dict = self._identities.pop(self._selected_index)
        save_identities(self._identities)

        name: str = ident.get("name", "") or "Unnamed"
        self._set_status(f"Deleted identity “{name}”")

        self._rebuild_cards()
        self._sync_selection_state()

    def _create_identity(self) -> None:
        new: Dict = {
            "name": "New profile",
            "git_name": "",
            "git_email": "",
            "ssh_key": "",
        }

        self._identities.append(new)
        save_identities(self._identities)

        self._selected_index = len(self._identities) - 1
        self._rebuild_cards()
        self._sync_selection_state()
        self._set_status("New identity created. Select it to edit details.")

    # ---------- page fade helper ---------- #

    def _fade_to_page(self, target: Optional[QWidget]) -> None:
        if self._pages is None or target is None:
            return

        current: QWidget = self._pages.currentWidget()

        current_effect: Optional[QGraphicsOpacityEffect] = None
        target_effect: Optional[QGraphicsOpacityEffect] = None

        if current is self._main_page:
            current_effect = self._main_page_effect
        elif current is self._edit_page:
            current_effect = self._edit_page_effect

        if target is self._main_page:
            target_effect = self._main_page_effect
        elif target is self._edit_page:
            target_effect = self._edit_page_effect

        if current_effect is None or target_effect is None:
            self._pages.setCurrentWidget(target)
            return

        target_effect.setOpacity(0.0)
        self._pages.setCurrentWidget(target)

        fade_out: QPropertyAnimation = QPropertyAnimation(
            current_effect,
            b"opacity",
            self,
        )
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.OutCubic)
        fade_out.start()

        fade_in: QPropertyAnimation = QPropertyAnimation(
            target_effect,
            b"opacity",
            self,
        )
        fade_in.setDuration(200)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.OutCubic)
        fade_in.start()

    # ---------- splash ---------- #

    def _show_splash(self) -> None:
        if self._logo_pixmap is None:
            return

        self._splash = QWidget(self)
        self._splash.setObjectName("splashOverlay")
        self._splash.setAttribute(Qt.WA_StyledBackground, True)
        self._splash.setGeometry(self.rect())

        layout: QVBoxLayout = QVBoxLayout(self._splash)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        logo_label: QLabel = QLabel(self._splash)
        logo_label.setPixmap(
            self._logo_pixmap.scaled(
                260,
                260,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        layout.addWidget(logo_label)

        effect: QGraphicsOpacityEffect = QGraphicsOpacityEffect(self._splash)
        self._splash.setGraphicsEffect(effect)

        self._splash_anim = QPropertyAnimation(effect, b"opacity", self)
        self._splash_anim.setDuration(200)
        self._splash_anim.setStartValue(1.0)
        self._splash_anim.setEndValue(0.0)
        self._splash_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._splash_anim.finished.connect(self._hide_splash)

        self._splash.show()
        self._splash.raise_()

        QTimer.singleShot(260, self._splash_anim.start)

    def _hide_splash(self) -> None:
        if self._splash is None:
            return

        self._splash.hide()
        self._splash.deleteLater()
        self._splash = None
