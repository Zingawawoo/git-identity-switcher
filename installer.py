#!/usr/bin/env python3
"""
Installer for Git Identity Switcher (Linux-focused).

What it does on Linux:
- Copies the app into ~/.local/share/git-identity-switcher
- Creates a wrapper script: ~/.local/bin/git-identity-switcher
- Creates a .desktop launcher wired to that wrapper

Windows / others:
- For now, just prints a message (we will flesh this out later).
"""

from __future__ import annotations

import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Optional

APP_DIR_NAME: str = "git-identity-switcher"


def copy_app_files(source_dir: Path, target_dir: Path) -> None:
    """
    Copy the core application files into the target directory.
    """
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)

    # Core application files. We now rely entirely on the inline card editor,
    # so config_dialog.py is no longer shipped.
    python_files = [
        "identity_switcher.py",
        "model.py",
        "views.py",
        "widgets.py",
    ]

    for name in python_files:
        src: Path = source_dir / name
        dst: Path = target_dir / name
        if not src.exists():
            print("[WARN] Expected file not found, skipping:", src)
            continue
        shutil.copy2(src, dst)

    # Copy icons directory if present
    icons_src: Path = source_dir / "icons"
    icons_dst: Path = target_dir / "icons"

    if icons_src.exists() and icons_src.is_dir():
        if icons_dst.exists():
            shutil.rmtree(icons_dst)
        shutil.copytree(icons_src, icons_dst)
        print("[INFO] Copied icons to", icons_dst)

    # Copy styles directory (for neon.qss)
    styles_src: Path = source_dir / "styles"
    styles_dst: Path = target_dir / "styles"

    if styles_src.exists() and styles_src.is_dir():
        if styles_dst.exists():
            shutil.rmtree(styles_dst)
        shutil.copytree(styles_src, styles_dst)
        print("[INFO] Copied styles to", styles_dst)


def find_icon(target_dir: Path) -> Optional[Path]:
    """
    Try to locate an icon file inside the app directory.
    Prefer .png, then .svg.
    """
    icons_dir: Path = target_dir / "icons"
    if not icons_dir.exists() or not icons_dir.is_dir():
        return None

    preferred_suffixes = [".png", ".svg"]
    for suffix in preferred_suffixes:
        for candidate in icons_dir.iterdir():
            if candidate.suffix.lower() == suffix:
                return candidate

    return None


def make_executable(path: Path) -> None:
    """
    Mark a file as executable (no-op on Windows).
    """
    if sys.platform == "win32":
        return

    if not path.exists():
        return

    mode: int = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def create_wrapper_script(app_dir: Path) -> Path:
    """
    Create ~/.local/bin/git-identity-switcher which simply runs the app.

    We call this from the .desktop file instead of calling python directly.
    """
    bin_dir: Path = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    wrapper_path: Path = bin_dir / "git-identity-switcher"
    main_script: Path = app_dir / "identity_switcher.py"

    # exec forwards arguments and preserves exit code
    content: str = "#!/usr/bin/env bash\n" \
                   "exec python3 \"{0}\" \"$@\"\n".format(main_script)

    wrapper_path.write_text(content, encoding="utf-8")
    make_executable(wrapper_path)

    print("[INFO] Created wrapper script:", wrapper_path)
    return wrapper_path


def create_desktop_file(wrapper_path: Path, icon_path: Optional[Path]) -> Path:
    """
    Create ~/.local/share/applications/git-identity-switcher.desktop
    pointing to the wrapper script.
    """
    applications_dir: Path = Path.home() / ".local" / "share" / "applications"
    applications_dir.mkdir(parents=True, exist_ok=True)

    desktop_file: Path = applications_dir / "git-identity-switcher.desktop"

    exec_command: str = str(wrapper_path)

    if icon_path is not None:
        icon_entry: str = str(icon_path)
    else:
        icon_entry = "utilities-terminal"

    content: str = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Git Identity Switcher\n"
        "Comment=Switch between multiple Git + SSH identities\n"
        "Exec={0}\n"
        "Icon={1}\n"
        "Terminal=false\n"
        "Categories=Development;Utility;\n"
        "StartupNotify=true\n".format(exec_command, icon_entry)
    )

    desktop_file.write_text(content, encoding="utf-8")
    make_executable(desktop_file)

    print("[INFO] Created desktop file:", desktop_file)
    return desktop_file


def install_unix() -> None:
    """
    Install on Linux / BSD / WSL environments.
    """
    source_dir: Path = Path(__file__).resolve().parent
    target_dir: Path = Path.home() / ".local" / "share" / APP_DIR_NAME

    print("[INFO] Installing Git Identity Switcher to:", target_dir)
    copy_app_files(source_dir, target_dir)

    wrapper: Path = create_wrapper_script(target_dir)
    icon: Optional[Path] = find_icon(target_dir)
    if icon is not None:
        print("[INFO] Using icon:", icon)
    else:
        print("[WARN] No icon found in icons/, using system default.")

    create_desktop_file(wrapper, icon)

    print("\n[DONE] Installation complete.")
    print("You should now see 'Git Identity Switcher' in your application launcher.")
    print("If it does not appear immediately, log out and back in, or restart the desktop shell.")


def install_windows_stub() -> None:
    """
    Minimal Windows message for now.
    """
    print("Windows install is not wired up in this installer yet.")
    print("You can still run the app with:")
    print("  python identity_switcher.py")


def main() -> None:
    if sys.platform == "win32":
        install_windows_stub()
    else:
        install_unix()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[ABORTED] Installer interrupted by user.", file=sys.stderr)
        sys.exit(1)
