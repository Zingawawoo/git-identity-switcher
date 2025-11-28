from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from widgets import NeonButton

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ConfigDialog(QDialog):
    """
    Neon glass dialog for adding/editing identities.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        identities: Optional[List[Dict]] = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Manage identities")
        self.setModal(True)
        self.resize(520, 360)
        self.setAttribute(Qt.WA_StyledBackground, True)

        if identities is None:
            self._identities: List[Dict] = []
        else:
            self._identities = list(identities)

        self.current_index: Optional[int] = None

        self._build_ui()
        self._populate_list()
        self._slide_in_animation()

    # ---------- UI ---------- #

    def _build_ui(self) -> None:
        root_layout: QHBoxLayout = QHBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(16)

        # Left panel: profiles list
        left_panel: QWidget = QWidget(self)
        left_layout: QVBoxLayout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)

        label_profiles: QLabel = QLabel("Profiles", left_panel)
        label_profiles.setProperty("class", "sectionTitle")
        left_layout.addWidget(label_profiles)

        self.table: QTableWidget = QTableWidget(0, 1, left_panel)
        self.table.setHorizontalHeaderLabels(["Profile"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        left_layout.addWidget(self.table)

        root_layout.addWidget(left_panel, 1)

        # Right panel: form
        right_panel: QWidget = QWidget(self)
        form: QGridLayout = QGridLayout(right_panel)
        form.setVerticalSpacing(10)

        label_name: QLabel = QLabel("Profile name", right_panel)
        label_name.setProperty("class", "fieldLabel")
        self.edit_name: QLineEdit = QLineEdit(right_panel)

        label_git_name: QLabel = QLabel("Git user.name", right_panel)
        label_git_name.setProperty("class", "fieldLabel")
        self.edit_git_name: QLineEdit = QLineEdit(right_panel)

        label_git_email: QLabel = QLabel("Git user.email", right_panel)
        label_git_email.setProperty("class", "fieldLabel")
        self.edit_git_email: QLineEdit = QLineEdit(right_panel)

        label_ssh: QLabel = QLabel("SSH key path", right_panel)
        label_ssh.setProperty("class", "fieldLabel")
        ssh_row: QHBoxLayout = QHBoxLayout()
        self.edit_ssh_key: QLineEdit = QLineEdit(right_panel)
        browse_btn: QPushButton = QPushButton("Browse…", right_panel)
        browse_btn.clicked.connect(self._browse_ssh_key)
        ssh_row.addWidget(self.edit_ssh_key)
        ssh_row.addWidget(browse_btn)

        row: int = 0
        form.addWidget(label_name, row, 0, 1, 2)
        row += 1
        form.addWidget(self.edit_name, row, 0, 1, 2)
        row += 1
        form.addWidget(label_git_name, row, 0, 1, 2)
        row += 1
        form.addWidget(self.edit_git_name, row, 0, 1, 2)
        row += 1
        form.addWidget(label_git_email, row, 0, 1, 2)
        row += 1
        form.addWidget(self.edit_git_email, row, 0, 1, 2)
        row += 1
        form.addWidget(label_ssh, row, 0, 1, 2)
        row += 1
        form.addLayout(ssh_row, row, 0, 1, 2)

        # Buttons row
        buttons_row: QHBoxLayout = QHBoxLayout()

        new_btn: NeonButton = NeonButton(
            "New",
            right_panel,
            variant="secondary",
        )
        save_btn: NeonButton = NeonButton(
            "Save",
            right_panel,
            variant="accent",
        )
        delete_btn: NeonButton = NeonButton(
            "Delete",
            right_panel,
            variant="danger",
        )

        new_btn.clicked.connect(self._on_new)
        save_btn.clicked.connect(self._on_save)
        delete_btn.clicked.connect(self._on_delete)

        buttons_row.addWidget(new_btn)
        buttons_row.addWidget(save_btn)
        buttons_row.addWidget(delete_btn)

        form.addLayout(buttons_row, row, 0, 1, 2)

    # ---------- data helpers ---------- #

    def _populate_list(self) -> None:
        self.table.setRowCount(0)
        for index, ident in enumerate(self._identities):
            self.table.insertRow(index)
            item: QTableWidgetItem = QTableWidgetItem(ident.get("name", "Unnamed"))
            self.table.setItem(index, 0, item)

        if self._identities:
            self.table.selectRow(0)
            self._load_row(0)

        self.table.cellClicked.connect(self._on_row_clicked)

    def _on_row_clicked(self, row: int, _column: int) -> None:
        self._load_row(row)

    def _load_row(self, index: int) -> None:
        if index < 0 or index >= len(self._identities):
            return
        self.current_index = index
        ident: Dict = self._identities[index]

        self.edit_name.setText(ident.get("name", ""))
        self.edit_git_name.setText(ident.get("git_name", ""))
        self.edit_git_email.setText(ident.get("git_email", ""))
        self.edit_ssh_key.setText(ident.get("ssh_key", ""))

    # ---------- actions ---------- #

    def _browse_ssh_key(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SSH private key",
            str(Path.home()),
        )
        if path:
            self.edit_ssh_key.setText(path)

    def _on_new(self) -> None:
        self.current_index = None
        self.edit_name.clear()
        self.edit_git_name.clear()
        self.edit_git_email.clear()
        self.edit_ssh_key.clear()
        self.edit_name.setFocus()

    def _on_save(self) -> None:
        name: str = self.edit_name.text().strip()
        git_name: str = self.edit_git_name.text().strip()
        git_email: str = self.edit_git_email.text().strip()
        ssh_key: str = self.edit_ssh_key.text().strip()

        if (
            name == ""
            or git_name == ""
            or git_email == ""
            or ssh_key == ""
        ):
            QMessageBox.warning(
                self,
                "Missing fields",
                "Please fill in profile name, Git name, Git email and SSH key path.",
            )
            return

        new_identity: Dict = {
            "name": name,
            "git_name": git_name,
            "git_email": git_email,
            "ssh_key": ssh_key,
        }

        if self.current_index is None:
            self._identities.append(new_identity)
        else:
            if 0 <= self.current_index < len(self._identities):
                self._identities[self.current_index] = new_identity
            else:
                self._identities.append(new_identity)

        self._populate_list()

    def _on_delete(self) -> None:
        if self.current_index is None:
            QMessageBox.warning(
                self,
                "No selection",
                "Select a profile from the list to delete.",
            )
            return

        if not (0 <= self.current_index < len(self._identities)):
            return

        ident: Dict = self._identities[self.current_index]
        name: str = ident.get("name", "")

        confirm = QMessageBox.question(
            self,
            "Delete profile",
            f"Remove profile:\n\n{name}?",
        )
        if confirm != QMessageBox.Yes:
            return

        del self._identities[self.current_index]
        self.current_index = None
        self._populate_list()

    # ---------- public API ---------- #

    def get_identities(self) -> List[Dict]:
        return list(self._identities)

    # ---------- animation ---------- #

    def _slide_in_animation(self) -> None:
        """
        Small slide-in animation from the top to make the dialog feel alive.
        """
        start_pos: QPoint = self.pos() - QPoint(0, 40)
        end_pos: QPoint = self.pos()

        animation: QPropertyAnimation = QPropertyAnimation(self, b"pos")
        animation.setDuration(260)
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start(QPropertyAnimation.DeleteWhenStopped)
