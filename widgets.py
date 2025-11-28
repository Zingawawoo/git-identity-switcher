from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class GlassFrame(QFrame):
    """
    Soft rounded container whose look is entirely driven by QSS.
    """

    def __init__(self, parent: Optional[QWidget] = None, variant: str = "glass") -> None:
        super().__init__(parent)

        if variant == "header":
            self.setObjectName("headerCard")
        else:
            self.setObjectName("glassCard")


class NeonButton(QPushButton):
    """
    Button with a 'class' dynamic property so QSS can theme
    accent / secondary / danger variants.
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
    PS5-style identity orb.

    - Circular avatar + name underneath.
    - Emits `on_clicked(index)` when pressed.
    - Has a 'selected' state so QSS can react.
    """

    def __init__(
        self,
        index: int,
        identity: Dict,
        on_clicked: Callable[[int], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent, variant="glass")
        self.setObjectName("identityBubble")

        self._index: int = index
        self._identity: Dict = identity
        self._on_clicked: Callable[[int], None] = on_clicked
        self._selected: bool = False

        self.avatar_label: QLabel
        self.name_label: QLabel

        self._build_ui()
        self._sync_labels()

    def _build_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        self.avatar_label = QLabel(self)
        self.avatar_label.setObjectName("identityAvatar")
        self.avatar_label.setFixedSize(96, 96)
        self.avatar_label.setAlignment(Qt.AlignCenter)

        self.name_label = QLabel(self)
        self.name_label.setObjectName("identityName")
        self.name_label.setAlignment(Qt.AlignHCenter)

        layout.addWidget(self.avatar_label)
        layout.addWidget(self.name_label)

    def _sync_labels(self) -> None:
        name: str = self._identity.get("name", "").strip()
        git_name: str = self._identity.get("git_name", "").strip()

        if name != "":
            display_name: str = name
        elif git_name != "":
            display_name = git_name
        else:
            display_name = "Unnamed"

        self.name_label.setText(display_name)

        if display_name != "":
            self.avatar_label.setText(display_name[0].upper())
        else:
            self.avatar_label.setText("?")

    # ---------- public API ---------- #

    def update_identity(self, identity: Dict) -> None:
        self._identity = identity
        self._sync_labels()

    def set_selected(self, selected: bool) -> None:
        if selected == self._selected:
            return

        self._selected = selected

        # Expose to QSS
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    # ---------- events ---------- #

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self._on_clicked(self._index)
        super().mousePressEvent(event)


class AddIdentityCard(GlassFrame):
    """
    '+' orb bubble for creating a new identity.
    """

    def __init__(
        self,
        on_add: Callable[[], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent, variant="glass")
        self.setObjectName("addIdentityBubble")

        self._on_add: Callable[[], None] = on_add

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        plus_label: QLabel = QLabel("+", self)
        plus_label.setObjectName("addIdentityPlus")
        plus_label.setAlignment(Qt.AlignCenter)
        plus_label.setFixedSize(96, 96)

        badge_container: QWidget = QWidget(self)
        badge_container.setObjectName("addIdentityTitleBadge")
        badge_layout: QVBoxLayout = QVBoxLayout(badge_container)
        badge_layout.setContentsMargins(12, 4, 12, 4)
        badge_layout.setSpacing(0)

        title_label: QLabel = QLabel("New identity", badge_container)
        title_label.setObjectName("addIdentityTitle")
        title_label.setAlignment(Qt.AlignHCenter)
        badge_layout.addWidget(title_label)

        subtitle_label: QLabel = QLabel(
            "Create a new Git + SSH profile.",
            self,
        )
        subtitle_label.setObjectName("addIdentitySubtitle")
        subtitle_label.setAlignment(Qt.AlignHCenter)
        subtitle_label.setWordWrap(True)

        layout.addWidget(plus_label)
        layout.addWidget(badge_container)
        layout.addWidget(subtitle_label)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self._on_add()
        super().mousePressEvent(event)


class EditPanel(GlassFrame):
    """
    Full-page editor form.

    - Shows name / git_name / email / ssh_key fields.
    - Exposes set_identity() + collect_data().
    - Has Save / Cancel callbacks provided by MainWindow.
    """

    def __init__(
        self,
        on_save: Callable[[], None],
        on_cancel: Callable[[], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent, variant="glass")
        self.setObjectName("editPanel")

        self._on_save: Callable[[], None] = on_save
        self._on_cancel: Callable[[], None] = on_cancel

        self._title_label: QLabel
        self.name_edit: QLineEdit
        self.git_name_edit: QLineEdit
        self.email_edit: QLineEdit
        self.ssh_key_edit: QLineEdit

        self._build_ui()

    def _build_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        self._title_label = QLabel("Edit profile", self)
        self._title_label.setObjectName("editPanelTitle")
        layout.addWidget(self._title_label)

        self.name_edit = self._add_field(layout, "Profile name")
        self.git_name_edit = self._add_field(layout, "Git user.name")
        self.email_edit = self._add_field(layout, "Git user.email")

        # SSH key row with Browse button
        ssh_container: QWidget = QWidget(self)
        ssh_layout: QVBoxLayout = QVBoxLayout(ssh_container)
        ssh_layout.setContentsMargins(0, 0, 0, 0)
        ssh_layout.setSpacing(4)

        ssh_label: QLabel = QLabel("SSH key path", ssh_container)
        ssh_label.setObjectName("fieldLabel")

        ssh_row: QHBoxLayout = QHBoxLayout()
        ssh_row.setContentsMargins(0, 0, 0, 0)
        ssh_row.setSpacing(8)

        self.ssh_key_edit = QLineEdit(ssh_container)
        browse_btn: NeonButton = NeonButton(
            "Browse…",
            ssh_container,
            variant="secondary",
        )
        browse_btn.clicked.connect(self._browse_ssh_key)

        ssh_row.addWidget(self.ssh_key_edit, 1)
        ssh_row.addWidget(browse_btn)

        ssh_layout.addWidget(ssh_label)
        ssh_layout.addLayout(ssh_row)

        layout.addWidget(ssh_container)

        # Button row
        buttons_row: QHBoxLayout = QHBoxLayout()
        buttons_row.setSpacing(10)
        buttons_row.setAlignment(Qt.AlignRight)

        cancel_btn: NeonButton = NeonButton("Cancel", self, variant="secondary")
        save_btn: NeonButton = NeonButton("Save", self, variant="accent")

        cancel_btn.clicked.connect(self._on_cancel)
        save_btn.clicked.connect(self._on_save)

        buttons_row.addWidget(cancel_btn)
        buttons_row.addWidget(save_btn)

        layout.addLayout(buttons_row)

    def _add_field(self, root: QVBoxLayout, label_text: str) -> QLineEdit:
        container: QWidget = QWidget(self)
        vbox: QVBoxLayout = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)

        label: QLabel = QLabel(label_text, container)
        label.setObjectName("fieldLabel")
        edit: QLineEdit = QLineEdit(container)

        vbox.addWidget(label)
        vbox.addWidget(edit)
        root.addWidget(container)

        return edit

    # ---------- SSH key browsing ---------- #

    def _browse_ssh_key(self) -> None:
        start_dir: Path = Path.home() / ".ssh"
        if start_dir.exists():
            initial: str = str(start_dir)
        else:
            initial = str(Path.home())

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SSH key",
            initial,
            "SSH keys (*)",
        )
        if file_path:
            self.ssh_key_edit.setText(file_path)

    # ---------- public helpers ---------- #

    def set_title(self, text: str) -> None:
        self._title_label.setText(text)

    def set_identity(self, identity: Dict) -> None:
        self.name_edit.setText(identity.get("name", ""))
        self.git_name_edit.setText(identity.get("git_name", ""))
        self.email_edit.setText(identity.get("git_email", ""))
        self.ssh_key_edit.setText(identity.get("ssh_key", ""))

    def collect_data(self) -> Dict[str, str]:
        data: Dict[str, str] = {}
        data["name"] = self.name_edit.text().strip()
        data["git_name"] = self.git_name_edit.text().strip()
        data["git_email"] = self.email_edit.text().strip()
        data["ssh_key"] = self.ssh_key_edit.text().strip()
        return data
