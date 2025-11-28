from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class GlassFrame(QFrame):
    """
    Simple 'glass' container.
    QSS drives the styling via #headerCard / #glassCard.
    """

    def __init__(self, parent: Optional[QWidget] = None, variant: str = "glass") -> None:
        super().__init__(parent)

        if variant == "header":
            self.setObjectName("headerCard")
        else:
            self.setObjectName("glassCard")


class NeonButton(QPushButton):
    """
    Button that uses the 'class' dynamic property so QSS can style it
    as accent / secondary / danger.
    """

    def __init__(
        self,
        text: str,
        parent: Optional[QWidget] = None,
        variant: Optional[str] = None,
    ) -> None:
        super().__init__(text, parent)

        if variant is not None:
            self.setProperty("class", variant)


class IdentityCard(GlassFrame):
    """
    A single identity "card" like a console login tile.

    - Click anywhere on the card header to expand / collapse actions.
    - Expanded area contains:
        * Select
        * Edit (switches to inline editor)
        * Delete
    - Edit mode lets you change fields and save/cancel inline.
    """

    def __init__(
        self,
        index: int,
        identity: Dict,
        on_select: Callable[[int], None],
        on_update: Callable[[int, Dict], None],
        on_delete: Callable[[int], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent, variant="glass")

        self._index: int = index
        self._identity: Dict = identity
        self._on_select: Callable[[int], None] = on_select
        self._on_update: Callable[[int, Dict], None] = on_update
        self._on_delete: Callable[[int], None] = on_delete

        self._expanded: bool = False

        self._build_ui()
        self._sync_labels()

    # ---------- construction ---------- #

    def _build_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header (always visible)
        header_row: QHBoxLayout = QHBoxLayout()
        header_row.setSpacing(6)

        self.name_label: QLabel = QLabel(self)
        self.name_label.setObjectName("identityName")

        self.email_label: QLabel = QLabel(self)
        self.email_label.setObjectName("identityEmail")

        header_block: QVBoxLayout = QVBoxLayout()
        header_block.setSpacing(2)
        header_block.addWidget(self.name_label)
        header_block.addWidget(self.email_label)

        header_row.addLayout(header_block)
        header_row.addStretch(1)

        hint_label: QLabel = QLabel("▼", self)
        hint_label.setObjectName("identityChevron")
        header_row.addWidget(hint_label)

        header_container: QWidget = QWidget(self)
        header_container.setLayout(header_row)
        header_container.setObjectName("identityHeader")
        header_container.mousePressEvent = self._toggle_expanded  # type: ignore[assignment]

        layout.addWidget(header_container)

        # Expandable panel
        self.panel: QWidget = QWidget(self)
        self.panel.setMaximumHeight(0)
        self.panel.setVisible(False)

        panel_layout: QVBoxLayout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(0, 4, 0, 0)
        panel_layout.setSpacing(6)

        self.stack: QStackedWidget = QStackedWidget(self.panel)
        panel_layout.addWidget(self.stack)

        # Page 0: action buttons
        actions_page: QWidget = QWidget(self.stack)
        actions_layout: QHBoxLayout = QHBoxLayout(actions_page)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        select_btn: NeonButton = NeonButton(
            "Use this identity",
            actions_page,
            variant="accent",
        )
        edit_btn: NeonButton = NeonButton(
            "Edit",
            actions_page,
            variant="secondary",
        )
        delete_btn: NeonButton = NeonButton(
            "Delete",
            actions_page,
            variant="danger",
        )

        select_btn.clicked.connect(self._on_select_clicked)
        edit_btn.clicked.connect(self._enter_edit_mode)
        delete_btn.clicked.connect(self._on_delete_clicked)

        actions_layout.addWidget(select_btn)
        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(delete_btn)

        self.stack.addWidget(actions_page)

        # Page 1: inline editor
        edit_page: QWidget = QWidget(self.stack)
        edit_layout: QVBoxLayout = QVBoxLayout(edit_page)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        edit_layout.setSpacing(6)

        self.edit_name: QLineEdit = QLineEdit(edit_page)
        self.edit_email: QLineEdit = QLineEdit(edit_page)
        self.edit_git_name: QLineEdit = QLineEdit(edit_page)
        self.edit_ssh_key: QLineEdit = QLineEdit(edit_page)

        # Simple stacked vertical form
        edit_layout.addWidget(self._make_field("Profile name", self.edit_name))
        edit_layout.addWidget(self._make_field("Git user.name", self.edit_git_name))
        edit_layout.addWidget(self._make_field("Git user.email", self.edit_email))
        edit_layout.addWidget(self._make_field("SSH key path", self.edit_ssh_key))

        buttons_row: QHBoxLayout = QHBoxLayout()
        buttons_row.setSpacing(8)

        save_btn: NeonButton = NeonButton("Save", edit_page, variant="accent")
        cancel_btn: NeonButton = NeonButton("Cancel", edit_page, variant="secondary")

        save_btn.clicked.connect(self._save_edits)
        cancel_btn.clicked.connect(self._exit_edit_mode)

        buttons_row.addWidget(save_btn)
        buttons_row.addWidget(cancel_btn)
        edit_layout.addLayout(buttons_row)

        self.stack.addWidget(edit_page)

        layout.addWidget(self.panel)

        # Animation for expanding / collapsing
        self._panel_anim: QPropertyAnimation = QPropertyAnimation(
            self.panel,
            b"maximumHeight",
            self,
        )
        self._panel_anim.setDuration(200)
        self._panel_anim.setEasingCurve(QEasingCurve.OutCubic)

    def _make_field(self, label_text: str, line_edit: QLineEdit) -> QWidget:
        container: QWidget = QWidget(self)
        row: QVBoxLayout = QVBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)

        label: QLabel = QLabel(label_text, container)
        label.setObjectName("fieldLabel")

        row.addWidget(label)
        row.addWidget(line_edit)
        return container

    # ---------- state sync ---------- #

    def _sync_labels(self) -> None:
        name: str = self._identity.get("name", "Unnamed")
        git_email: str = self._identity.get("git_email", "")
        git_name: str = self._identity.get("git_name", "")

        display_name: str = name or git_name or "Unnamed"
        self.name_label.setText(display_name)

        if git_email:
            self.email_label.setText(git_email)
        else:
            self.email_label.setText("No email set")

    def _sync_edit_fields(self) -> None:
        self.edit_name.setText(self._identity.get("name", ""))
        self.edit_git_name.setText(self._identity.get("git_name", ""))
        self.edit_email.setText(self._identity.get("git_email", ""))
        self.edit_ssh_key.setText(self._identity.get("ssh_key_path", ""))

    # ---------- actions ---------- #

    def _toggle_expanded(self, event) -> None:  # type: ignore[override]
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded: bool) -> None:
        if expanded == self._expanded:
            return

        self._expanded = expanded
        self.panel.setVisible(True)

        start: int = self.panel.maximumHeight()
        end: int = 160 if expanded else 0

        self._panel_anim.stop()
        self._panel_anim.setStartValue(start)
        self._panel_anim.setEndValue(end)
        self._panel_anim.start()

    def _on_select_clicked(self) -> None:
        self._on_select(self._index)

    def _on_delete_clicked(self) -> None:
        self._on_delete(self._index)

    def _enter_edit_mode(self) -> None:
        self._sync_edit_fields()
        self.stack.setCurrentIndex(1)
        if not self._expanded:
            self.set_expanded(True)

    def _exit_edit_mode(self) -> None:
        self.stack.setCurrentIndex(0)

    def _save_edits(self) -> None:
        updated: Dict = dict(self._identity)
        updated["name"] = self.edit_name.text().strip()
        updated["git_name"] = self.edit_git_name.text().strip()
        updated["git_email"] = self.edit_email.text().strip()
        updated["ssh_key_path"] = self.edit_ssh_key.text().strip()

        self._identity = updated
        self._sync_labels()
        self._on_update(self._index, updated)
        self._exit_edit_mode()


class AddIdentityCard(GlassFrame):
    """
    Special card that creates a new identity when clicked.
    """

    def __init__(
        self,
        on_add: Callable[[], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent, variant="glass")
        self._on_add: Callable[[], None] = on_add

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)

        title: QLabel = QLabel("+ New identity", self)
        title.setObjectName("addIdentityTitle")

        subtitle: QLabel = QLabel(
            "Create a new Git + SSH profile.",
            self,
        )
        subtitle.setObjectName("addIdentitySubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch(1)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self._on_add()
        super().mousePressEvent(event)
