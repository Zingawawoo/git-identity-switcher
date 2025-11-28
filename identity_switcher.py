from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import List, Dict

from model import load_identities, save_identities
from views import HomeView, ConfigView


class IdentitySwitcherApp:
    def __init__(self) -> None:
        self.root: tk.Tk = tk.Tk()
        self.root.title("Git Identity Switcher")

        # Basic window sizing
        self.root.geometry("720x440")
        self.root.minsize(640, 360)

        self._setup_style()
        self._set_app_icon()

        self._identities: List[Dict] = load_identities()

        # Container frame
        self.container: ttk.Frame = ttk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        self.home_view: HomeView = HomeView(
            self.container,
            get_identities=self.get_identities,
            open_config_cb=self.show_config,
            quit_cb=self.root.quit,
        )
        self.config_view: ConfigView = ConfigView(
            self.container,
            get_identities=self.get_identities,
            set_identities=self.set_identities,
            back_cb=self.show_home,
        )

        self.home_view.pack(fill="both", expand=True)

    def _setup_style(self) -> None:
        style: ttk.Style = ttk.Style()
        # Use a platform-appropriate base theme
        if sys.platform == "win32":
            base_theme: str = "vista"
        elif sys.platform == "darwin":
            base_theme = "aqua"
        else:
            base_theme = "clam"

        try:
            style.theme_use(base_theme)
        except tk.TclError:
            # Fallback if theme not available
            style.theme_use("default")

        # Accent / background colours
        bg: str = "#0d1117"
        surface: str = "#161b22"
        accent: str = "#238636"
        fg: str = "#f0f6fc"
        subtle: str = "#8b949e"

        self.root.configure(bg=bg)

        style.configure(
            "TFrame",
            background=bg,
        )
        style.configure(
            "TLabelframe",
            background=bg,
            foreground=fg,
        )
        style.configure(
            "TLabelframe.Label",
            background=bg,
            foreground=subtle,
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "TLabel",
            background=bg,
            foreground=fg,
        )
        style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#ffffff",
            focusthickness=3,
            focuscolor=accent,
        )
        style.map(
            "Accent.TButton",
            foreground=[("disabled", "#cccccc")],
        )

    def _set_app_icon(self) -> None:
        """
        Try to set a window icon if an icon file exists.
        This works on most platforms but is optional.
        """
        try:
            base_dir: Path = Path(__file__).resolve().parent
            icon_dir: Path = base_dir / "icons"
            icon_path_png: Path = icon_dir / "app.png"

            if icon_path_png.exists():
                icon_image: tk.PhotoImage = tk.PhotoImage(file=str(icon_path_png))
                self.root.iconphoto(True, icon_image)
        except Exception:
            # Icon is not critical; silently ignore
            return

    def get_identities(self) -> List[Dict]:
        return list(self._identities)

    def set_identities(self, identities: List[Dict]) -> None:
        self._identities = list(identities)
        save_identities(self._identities)
        self.home_view.refresh_identities()

    def show_home(self) -> None:
        self.config_view.pack_forget()
        self.home_view.refresh_identities()
        self.home_view.pack(fill="both", expand=True)

    def show_config(self) -> None:
        self.home_view.pack_forget()
        self.config_view.refresh_list()
        self.config_view.clear_form()
        self.config_view.pack(fill="both", expand=True)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    app = IdentitySwitcherApp()
    app.run()
