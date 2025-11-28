from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Dict, Callable, Optional

from model import apply_identity


class HomeView(ttk.Frame):
    """
    Home screen: quick switch between identities.
    """

    def __init__(
        self,
        master: tk.Misc,
        get_identities: Callable[[], List[Dict]],
        open_config_cb: Callable[[], None],
        quit_cb: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self.get_identities: Callable[[], List[Dict]] = get_identities
        self.open_config_cb: Callable[[], None] = open_config_cb
        self.quit_cb: Callable[[], None] = quit_cb

        self._build_ui()
        self.refresh_identities()

    def _build_ui(self) -> None:
        self.configure(padding=16)

        # Top section
        header_frame: ttk.Frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 12))

        title_label: ttk.Label = ttk.Label(
            header_frame,
            text="Git Identity Switcher",
            font=("Segoe UI", 16, "bold"),
        )
        title_label.pack(side="left")

        subtitle_label: ttk.Label = ttk.Label(
            header_frame,
            text="Quickly switch between your Git + SSH profiles",
            font=("Segoe UI", 9),
        )
        subtitle_label.pack(side="left", padx=(12, 0))

        # Middle section: list of identities
        middle_frame: ttk.Frame = ttk.Frame(self)
        middle_frame.pack(fill="both", expand=True)

        list_frame: ttk.LabelFrame = ttk.LabelFrame(
            middle_frame,
            text="Available identities",
            padding=8,
        )
        list_frame.pack(fill="both", expand=True)

        self.listbox: tk.Listbox = tk.Listbox(
            list_frame,
            activestyle="dotbox",
            height=8,
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar: ttk.Scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.listbox.yview,
        )
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        # Bottom buttons
        button_frame: ttk.Frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=(12, 0))

        self.switch_button: ttk.Button = ttk.Button(
            button_frame,
            text="Switch to selected",
            command=self._on_switch_clicked,
        )
        self.switch_button.pack(side="left")

        self.config_button: ttk.Button = ttk.Button(
            button_frame,
            text="Manage identities…",
            command=self.open_config_cb,
        )
        self.config_button.pack(side="left", padx=(8, 0))

        self.quit_button: ttk.Button = ttk.Button(
            button_frame,
            text="Quit",
            command=self.quit_cb,
        )
        self.quit_button.pack(side="right")

    def refresh_identities(self) -> None:
        self.listbox.delete(0, tk.END)
        identities: List[Dict] = self.get_identities()
        if len(identities) == 0:
            self.listbox.insert(tk.END, "No identities configured yet.")
            self.listbox.configure(state="disabled")
        else:
            self.listbox.configure(state="normal")
            for ident in identities:
                label: str = "{0}  —  {1}".format(
                    ident.get("name", "Unnamed"),
                    ident.get("git_email", ""),
                )
                self.listbox.insert(tk.END, label)

    def _on_switch_clicked(self) -> None:
        identities: List[Dict] = self.get_identities()
        if len(identities) == 0:
            messagebox.showinfo(
                "No identities",
                "You have not configured any identities yet.\n\n"
                "Click 'Manage identities…' to add one.",
            )
            return

        selection: Optional[int]
        try:
            selection = self.listbox.curselection()[0]
        except IndexError:
            selection = None

        if selection is None:
            messagebox.showwarning(
                "No selection",
                "Please select an identity from the list.",
            )
            return

        identity: Dict = identities[selection]
        apply_identity(identity)


class ConfigView(ttk.Frame):
    """
    Configuration screen: add / edit / delete identities.
    """

    def __init__(
        self,
        master: tk.Misc,
        get_identities: Callable[[], List[Dict]],
        set_identities: Callable[[List[Dict]], None],
        back_cb: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self.get_identities: Callable[[], List[Dict]] = get_identities
        self.set_identities: Callable[[List[Dict]], None] = set_identities
        self.back_cb: Callable[[], None] = back_cb

        self.current_index: Optional[int] = None

        self._build_ui()
        self.refresh_list()

    def _build_ui(self) -> None:
        self.configure(padding=16)

        top_frame: ttk.Frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=(0, 12))

        title_label: ttk.Label = ttk.Label(
            top_frame,
            text="Manage identities",
            font=("Segoe UI", 14, "bold"),
        )
        title_label.pack(side="left")

        back_button: ttk.Button = ttk.Button(
            top_frame,
            text="← Back",
            command=self.back_cb,
        )
        back_button.pack(side="right")

        main_frame: ttk.Frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        # Left: list of identities
        list_frame: ttk.LabelFrame = ttk.LabelFrame(
            main_frame,
            text="Profiles",
            padding=8,
        )
        list_frame.pack(side="left", fill="y")

        self.listbox: tk.Listbox = tk.Listbox(
            list_frame,
            height=12,
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar: ttk.Scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.listbox.yview,
        )
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # Right: form
        form_frame: ttk.LabelFrame = ttk.LabelFrame(
            main_frame,
            text="Details",
            padding=12,
        )
        form_frame.pack(side="left", fill="both", expand=True, padx=(12, 0))

        # Name
        name_label: ttk.Label = ttk.Label(form_frame, text="Profile name")
        name_label.grid(row=0, column=0, sticky="w")
        self.name_entry: ttk.Entry = ttk.Entry(form_frame, width=32)
        self.name_entry.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        # Git name
        git_name_label: ttk.Label = ttk.Label(form_frame, text="Git user.name")
        git_name_label.grid(row=2, column=0, sticky="w")
        self.git_name_entry: ttk.Entry = ttk.Entry(form_frame, width=32)
        self.git_name_entry.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        # Git email
        git_email_label: ttk.Label = ttk.Label(form_frame, text="Git user.email")
        git_email_label.grid(row=4, column=0, sticky="w")
        self.git_email_entry: ttk.Entry = ttk.Entry(form_frame, width=32)
        self.git_email_entry.grid(row=5, column=0, sticky="ew", pady=(0, 8))

        # SSH key
        ssh_key_label: ttk.Label = ttk.Label(form_frame, text="SSH key path")
        ssh_key_label.grid(row=6, column=0, sticky="w")
        ssh_frame: ttk.Frame = ttk.Frame(form_frame)
        ssh_frame.grid(row=7, column=0, sticky="ew", pady=(0, 8))
        self.ssh_key_entry: ttk.Entry = ttk.Entry(ssh_frame, width=32)
        self.ssh_key_entry.pack(side="left", fill="x", expand=True)
        browse_button: ttk.Button = ttk.Button(
            ssh_frame,
            text="Browse…",
            command=self._browse_ssh_key,
        )
        browse_button.pack(side="left", padx=(4, 0))

        form_frame.columnconfigure(0, weight=1)

        # Bottom buttons
        button_frame: ttk.Frame = ttk.Frame(form_frame)
        button_frame.grid(row=8, column=0, sticky="ew", pady=(12, 0))

        new_button: ttk.Button = ttk.Button(
            button_frame,
            text="New",
            command=self._on_new,
        )
        new_button.pack(side="left")

        save_button: ttk.Button = ttk.Button(
            button_frame,
            text="Save",
            command=self._on_save,
        )
        save_button.pack(side="left", padx=(8, 0))

        delete_button: ttk.Button = ttk.Button(
            button_frame,
            text="Delete",
            command=self._on_delete,
        )
        delete_button.pack(side="right")

    def refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        identities: List[Dict] = self.get_identities()
        for index, ident in enumerate(identities):
            label: str = "{0}: {1}".format(
                index + 1,
                ident.get("name", "Unnamed"),
            )
            self.listbox.insert(tk.END, label)

    def clear_form(self) -> None:
        self.current_index = None
        self.name_entry.delete(0, tk.END)
        self.git_name_entry.delete(0, tk.END)
        self.git_email_entry.delete(0, tk.END)
        self.ssh_key_entry.delete(0, tk.END)

    def _on_listbox_select(self, event: tk.Event) -> None:  # type: ignore[override]
        try:
            selection_index: int = self.listbox.curselection()[0]
        except IndexError:
            return

        identities: List[Dict] = self.get_identities()
        if selection_index < 0 or selection_index >= len(identities):
            return

        self.current_index = selection_index
        ident: Dict = identities[selection_index]

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, ident.get("name", ""))

        self.git_name_entry.delete(0, tk.END)
        self.git_name_entry.insert(0, ident.get("git_name", ""))

        self.git_email_entry.delete(0, tk.END)
        self.git_email_entry.insert(0, ident.get("git_email", ""))

        self.ssh_key_entry.delete(0, tk.END)
        self.ssh_key_entry.insert(0, ident.get("ssh_key", ""))

    def _browse_ssh_key(self) -> None:
        initial_dir: str = os.path.expanduser("~")
        path: str = filedialog.askopenfilename(
            title="Select SSH private key",
            initialdir=initial_dir,
        )
        if path is None or path == "":
            return
        self.ssh_key_entry.delete(0, tk.END)
        self.ssh_key_entry.insert(0, path)

    def _on_new(self) -> None:
        self.clear_form()
        self.name_entry.focus_set()

    def _on_save(self) -> None:
        name: str = self.name_entry.get().strip()
        git_name: str = self.git_name_entry.get().strip()
        git_email: str = self.git_email_entry.get().strip()
        ssh_key: str = self.ssh_key_entry.get().strip()

        if name == "" or git_name == "" or git_email == "" or ssh_key == "":
            messagebox.showwarning(
                "Missing fields",
                "Please fill in all fields (profile name, Git name, email, SSH key).",
            )
            return

        identities: List[Dict] = self.get_identities()

        new_identity: Dict = {
            "name": name,
            "git_name": git_name,
            "git_email": git_email,
            "ssh_key": ssh_key,
        }

        if self.current_index is None:
            identities.append(new_identity)
        else:
            identities[self.current_index] = new_identity

        self.set_identities(identities)
        self.refresh_list()
        self._select_last_or_current()

    def _select_last_or_current(self) -> None:
        identities: List[Dict] = self.get_identities()
        if len(identities) == 0:
            self.current_index = None
            return

        if self.current_index is None:
            self.current_index = len(identities) - 1

        index: int = self.current_index
        if index < 0:
            index = 0
        if index >= len(identities):
            index = len(identities) - 1

        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.see(index)

    def _on_delete(self) -> None:
        if self.current_index is None:
            messagebox.showwarning(
                "No selection",
                "Select a profile to delete from the list on the left.",
            )
            return

        identities: List[Dict] = self.get_identities()
        if self.current_index < 0 or self.current_index >= len(identities):
            return

        ident: Dict = identities[self.current_index]

        confirm: bool = messagebox.askyesno(
            "Delete identity",
            "Remove profile:\n\n{0}?".format(ident.get("name", "")),
        )
        if not confirm:
            return

        del identities[self.current_index]
        self.set_identities(identities)
        self.refresh_list()
        self.clear_form()
