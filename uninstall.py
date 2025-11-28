#!/usr/bin/env python3
"""
Uninstaller for Git Identity Switcher.

Linux / *BSD / WSL:
- Removes ~/.local/share/git-identity-switcher
- Removes ~/.local/bin/git-identity-switcher
- Removes ~/.local/share/applications/git-identity-switcher.desktop

Windows:
- Removes %APPDATA%\\GitIdentitySwitcher
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


APP_DIR_NAME: str = "git-identity-switcher"
APP_NAME_WIN: str = "GitIdentitySwitcher"


def uninstall_unix() -> None:
    app_dir: Path = Path.home() / ".local" / "share" / APP_DIR_NAME
    wrapper: Path = Path.home() / ".local" / "bin" / "git-identity-switcher"
    desktop: Path = Path.home() / ".local" / "share" / "applications" / "git-identity-switcher.desktop"

    if app_dir.exists():
        print("[INFO] Removing application directory: {0}".format(app_dir))
        shutil.rmtree(app_dir)
    else:
        print("[INFO] Application directory not found: {0}".format(app_dir))

    if wrapper.exists():
        print("[INFO] Removing wrapper script: {0}".format(wrapper))
        wrapper.unlink()
    else:
        print("[INFO] Wrapper script not found: {0}".format(wrapper))

    if desktop.exists():
        print("[INFO] Removing desktop file: {0}".format(desktop))
        desktop.unlink()
    else:
        print("[INFO] Desktop file not found: {0}".format(desktop))

    print("\n[DONE] Uninstall complete.")


def uninstall_windows() -> None:
    appdata_env: str | None = os.environ.get("APPDATA")
    if appdata_env is not None:
        base: Path = Path(appdata_env)
    else:
        base = Path.home() / "AppData" / "Roaming"

    app_dir: Path = base / APP_NAME_WIN

    if app_dir.exists():
        print("[INFO] Removing application directory: {0}".format(app_dir))
        shutil.rmtree(app_dir)
    else:
        print("[INFO] Application directory not found: {0}".format(app_dir))

    print("\n[DONE] Uninstall complete.")
    print("You may remove any shortcuts you created manually.")


def main() -> None:
    if sys.platform == "win32":
        uninstall_windows()
    else:
        uninstall_unix()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[ABORTED] Uninstall interrupted by user.", file=sys.stderr)
        sys.exit(1)
