import os
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import List, Dict, Callable

from model import apply_identity


class HomeView(tk.Frame):
    """
    Home screen: shows buttons for each identity + 'Configure' button.
    """

    def __init__(
        self,
        master: tk.Misc,
        get_identities: Callable[[], List[Dict]],
        open_config_cb: Callable[[], None],
    ) -> None:
        super().__init__(master, bg="#0d1117")
        self.get_identities = get_identities
        self.open_config_cb = open_config_cb

        title: tk.Label = tk.Label(
            self,
            text="Git Identity Switcher",
            bg="#0d1117",
            fg="white",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(pady=(16, 4))

        subtitle: tk.Label = tk.Label(
            self,
            text="Click a profile to switch your Git + SSH identity.",
            bg="#0d1117",
            fg="#8b949e",
            font=("Segoe UI", 10),
        )
        subtitle.pack(pady=(0, 12))

        self.buttons_frame: tk.Frame = tk.Frame(self, bg="#0d1117")
        self.buttons_frame.pack(fill="both", expand=True, padx=24)

        bottom: tk.Frame = tk.Frame(self, bg="#0d1117")
        bottom.pack(fill="x", pady=12)

        config_btn: tk.Button = tk.Button(
            bottom,
            text="Configure identities…",
            command=self.open_config_cb,
            bg="#21262d",
            fg="white",
            activebackground="#30363d",
            relief="flat",
            width=20,
        )
        config_btn.pack(side="left", padx=20)

        hint: tk.Label = tk.Label(
            bottom,
            text="Configured via identities.json",
            bg="#0d1117",
            fg="#6e7681",
            font=("Segoe UI", 9),
        )
        hint.pack(side="right", padx=20)

        self.render_buttons()

    def render_buttons(self) -> None:
        """Render one button per identity."""
        for child in self.buttons_frame.winfo_children():
            child.destroy()

        identities: List[Dict] = self.get_identities()

        if not identities:
            tk.Label(
                self.buttons_frame,
                text="No identities yet. Click 'Configure identities…' to add one.",
                bg="#0d1117",
                fg="#8b949e",
            ).pack(pady=20)
            return

        for ident in identities:
            label_text: str = f"{ident.get('name', '')}  ({ident.get('git_email', '')})"
            btn: tk.Button = tk.Button(
                self.buttons_frame,
                text=label_text,
                font=("Segoe UI", 12),
                width=40,
                height=2,
                bg="#21262d",
                fg="white",
                activebackground="#30363d",
                relief="flat",
                command=lambda ident=ident: apply_identity(ident),
            )
            btn.pack(pady=6)


class ConfigView(tk.Frame):
    """
    Configuration screen:
    - List of identities
    - Form to edit / add
    """

    def __init__(
        self,
        master: tk.Misc,
        get_identities: Callable[[], List[Dict]],
        set_identities: Callable[[List[Dict]], None],
        back_cb: Callable[[], None],
    ) -> None:
        super().__init__(master, bg="#0d1117")
        self.get_identities = get_identities
        self.set_identities = set_identities
        self.back_cb = back_cb

        self.current_index: int | None = None

        header: tk.Frame = tk.Frame(self, bg="#0d1117")
        header.pack(fill="x", pady=(8, 4), padx=10)

        title: tk.Label = tk.Label(
            header,
            text="Configure Identities",
            bg="#0d1117",
            fg="white",
            font=("Segoe UI", 14, "bold"),
        )
        title.pack(side="left")

        back_btn: tk.Button = tk.Button(
            header,
            text="← Back",
            command=self.back_cb,
            bg="#21262d",
            fg="white",
            activebackground="#30363d",
            relief="flat",
            width=10,
        )
        back_btn.pack(side="right")

        body: tk.Frame = tk.Frame(self, bg="#0d1117")
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # Left: listbox
        left: tk.Frame = tk.Frame(body, bg="#0d1117")
        left.pack(side="left", fill="y")

        tk.Label(
            left,
            text="Profiles",
            bg="#0d1117",
            fg="#8b949e",
        ).pack(anchor="w", pady=(0, 4))

        self.listbox: tk.Listbox = tk.Listbox(
            left,
            height=12,
            width=26,
            bg="#161b22",
            fg="white",
            selectbackground="#238636",
            selectforeground="white",
            borderwidth=0,
            highlightthickness=0,
        )
        self.listbox.pack(fill="y", expand=False)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        btn_row: tk.Frame = tk.Frame(left, bg="#0d1117")
        btn_row.pack(pady=8)

        add_btn: tk.Button = tk.Button(
            btn_row,
            text="+ New",
            command=self.new_identity,
            bg="#238636",
            fg="white",
            activebackground="#2ea043",
            relief="flat",
            width=8,
        )
        add_btn.pack(side="left", padx=3)

        del_btn: tk.Button = tk.Button(
            btn_row,
            text="Delete",
            command=self.delete_identity,
            bg="#8b0000",
            fg="white",
            activebackground="#a11",
            relief="flat",
            width=8,
        )
        del_btn.pack(side="left", padx=3)

        # Right: form
        form: tk.Frame = tk.Frame(body, bg="#0d1117")
        form.pack(side="left", fill="both", expand=True, padx=(16, 4))

        pad = {"padx": 4, "pady": 4}

        tk.Label(form, text="Profile name:", bg="#0d1117", fg="white").grid(
            row=0, column=0, sticky="w", **pad
        )
        self.entry_name: tk.Entry = tk.Entry(form, width=40)
        self.entry_name.grid(row=0, column=1, **pad)

        tk.Label(form, text="Git user.name:", bg="#0d1117", fg="white").grid(
            row=1, column=0, sticky="w", **pad
        )
        self.entry_git_name: tk.Entry = tk.Entry(form, width=40)
        self.entry_git_name.grid(row=1, column=1, **pad)

        tk.Label(form, text="Git user.email:", bg="#0d1117", fg="white").grid(
            row=2, column=0, sticky="w", **pad
        )
        self.entry_git_email: tk.Entry = tk.Entry(form, width=40)
        self.entry_git_email.grid(row=2, column=1, **pad)

        tk.Label(form, text="SSH key path:", bg="#0d1117", fg="white").grid(
            row=3, column=0, sticky="w", **pad
        )

        ssh_row: tk.Frame = tk.Frame(form, bg="#0d1117")
        ssh_row.grid(row=3, column=1, sticky="w", **pad)

        self.entry_ssh_key: tk.Entry = tk.Entry(ssh_row, width=30)
        self.entry_ssh_key.pack(side="left")

        browse_btn: tk.Button = tk.Button(
            ssh_row,
            text="Browse…",
            command=self.browse_ssh_key,
            bg="#21262d",
            fg="white",
            activebackground="#30363d",
            relief="flat",
            width=10,
        )
        browse_btn.pack(side="left", padx=4)

        save_btn: tk.Button = tk.Button(
            form,
            text="Save",
            command=self.save_identity,
            bg="#238636",
            fg="white",
            activebackground="#2ea043",
            relief="flat",
            width=14,
        )
        save_btn.grid(row=4, column=1, sticky="e", pady=(16, 4))

        self.refresh_list()
        self.clear_form()

    # ---- UI actions ---- #

    def refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for ident in self.get_identities():
            label: str = f"{ident.get('name', '')} ({ident.get('git_email', '')})"
            self.listbox.insert(tk.END, label)

    def clear_form(self) -> None:
        self.current_index = None
        self.entry_name.delete(0, tk.END)
        self.entry_git_name.delete(0, tk.END)
        self.entry_git_email.delete(0, tk.END)
        self.entry_ssh_key.delete(0, tk.END)
        # default suggestion
        self.entry_ssh_key.insert(0, "~/.ssh/id_ed25519")

    def new_identity(self) -> None:
        self.listbox.selection_clear(0, tk.END)
        self.clear_form()

    def on_select(self, _event=None) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        index: int = selection[0]
        self.current_index = index
        identities: List[Dict] = self.get_identities()
        ident: Dict = identities[index]

        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, ident.get("name", ""))

        self.entry_git_name.delete(0, tk.END)
        self.entry_git_name.insert(0, ident.get("git_name", ""))

        self.entry_git_email.delete(0, tk.END)
        self.entry_git_email.insert(0, ident.get("git_email", ""))

        self.entry_ssh_key.delete(0, tk.END)
        self.entry_ssh_key.insert(0, ident.get("ssh_key", ""))

    def browse_ssh_key(self) -> None:
        initial_dir: str = os.path.expanduser("~/.ssh")
        path: str = filedialog.askopenfilename(
            title="Select SSH key",
            initialdir=initial_dir,
        )
        if path:
            self.entry_ssh_key.delete(0, tk.END)
            self.entry_ssh_key.insert(0, path)

    def save_identity(self) -> None:
        name: str = self.entry_name.get().strip()
        git_name: str = self.entry_git_name.get().strip()
        git_email: str = self.entry_git_email.get().strip()
        ssh_key: str = self.entry_ssh_key.get().strip()

        if not name or not git_name or not git_email or not ssh_key:
            messagebox.showerror("Missing fields", "All fields are required.")
            return

        identities: List[Dict] = self.get_identities()
        new_ident: Dict = {
            "name": name,
            "git_name": git_name,
            "git_email": git_email,
            "ssh_key": ssh_key,
        }

        if self.current_index is None:
            identities.append(new_ident)
        else:
            identities[self.current_index] = new_ident

        self.set_identities(identities)
        self.refresh_list()

        if self.current_index is None:
            self.current_index = len(identities) - 1
            self.listbox.selection_set(self.current_index)

    def delete_identity(self) -> None:
        if self.current_index is None:
            return
        identities: List[Dict] = self.get_identities()
        ident: Dict = identities[self.current_index]

        if not messagebox.askyesno(
            "Delete identity",
            f"Remove profile:\n\n{ident.get('name', '')}?",
        ):
            return

        del identities[self.current_index]
        self.set_identities(identities)
        self.refresh_list()
        self.clear_form()
