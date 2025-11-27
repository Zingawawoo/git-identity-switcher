import tkinter as tk
from typing import List, Dict

from model import load_identities, save_identities
from views import HomeView, ConfigView


class IdentitySwitcherApp:
    def __init__(self) -> None:
        self.root: tk.Tk = tk.Tk()
        self.root.title("Git Identity Switcher")
        self.root.configure(bg="#0d1117")
        self.root.geometry("640x400")

        self._identities: List[Dict] = load_identities()

        self.home_view: HomeView = HomeView(
            self.root,
            get_identities=self.get_identities,
            open_config_cb=self.show_config,
        )
        self.config_view: ConfigView | None = None

        self.home_view.pack(fill="both", expand=True)

    # ---- identity storage ---- #

    def get_identities(self) -> List[Dict]:
        return self._identities

    def set_identities(self, identities: List[Dict]) -> None:
        self._identities = identities
        save_identities(self._identities)
        # refresh home view buttons if visible
        self.home_view.render_buttons()

    # ---- view switching ---- #

    def show_home(self) -> None:
        if self.config_view is not None:
            self.config_view.pack_forget()
        self.home_view.render_buttons()
        self.home_view.pack(fill="both", expand=True)

    def show_config(self) -> None:
        self.home_view.pack_forget()
        if self.config_view is None:
            self.config_view = ConfigView(
                self.root,
                get_identities=self.get_identities,
                set_identities=self.set_identities,
                back_cb=self.show_home,
            )
        self.config_view.refresh_list()
        self.config_view.clear_form()
        self.config_view.pack(fill="both", expand=True)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    app = IdentitySwitcherApp()
    app.run()
