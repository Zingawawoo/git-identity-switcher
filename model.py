from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict


APP_DIR_NAME: str = "git-identity-switcher"
APP_NAME_WIN: str = "GitIdentitySwitcher"


def run(cmd: str) -> None:
    """
    Run a shell command.
    Uses shell=True for simplicity since commands differ per platform.
    """
    subprocess.call(cmd, shell=True)


def get_config_dir() -> Path:
    """
    Return the directory where identities.json should live,
    in a cross-platform way.
    """
    if sys.platform == "win32":
        appdata: str | None = os.environ.get("APPDATA")
        if appdata is not None:
            base: Path = Path(appdata)
        else:
            base = Path.home() / "AppData" / "Roaming"
        return base / APP_NAME_WIN
    else:
        xdg_config_home: str | None = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home is not None:
            base = Path(xdg_config_home)
        else:
            base = Path.home() / ".config"
        return base / APP_DIR_NAME


CONFIG_DIR: Path = get_config_dir()
CONFIG_FILE: Path = CONFIG_DIR / "identities.json"


def ensure_config_dir() -> None:
    """
    Make sure the configuration directory exists.
    """
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_identities() -> List[Dict]:
    """
    Load identities from JSON. Create an empty file if missing.
    """
    ensure_config_dir()

    if not CONFIG_FILE.exists():
        data: Dict[str, List[Dict]] = {"identities": []}
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return []

    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        data: Dict = json.load(f)

    identities: List[Dict] = data.get("identities", [])
    return identities


def save_identities(identities: List[Dict]) -> None:
    """
    Persist identities to JSON.
    """
    ensure_config_dir()
    data: Dict[str, List[Dict]] = {"identities": identities}
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def apply_identity(identity: Dict) -> None:
    """
    Apply a single identity:
    - On Unix: reset ssh-agent keys and add the selected SSH key.
    - On all platforms: set global git user.name / user.email.
    - Force git to use this SSH key via core.sshCommand.
    """
    from tkinter import messagebox  # imported here to avoid hard Tk dependency

    ssh_key_raw: str = identity["ssh_key"]
    ssh_key: str = os.path.expanduser(ssh_key_raw)
    git_name: str = identity["git_name"]
    git_email: str = identity["git_email"]

    if not os.path.exists(ssh_key):
        messagebox.showerror(
            "SSH key not found",
            "SSH key file does not exist:\n{0}".format(ssh_key),
        )
        return

    # Platform-specific ssh-agent handling
    if sys.platform != "win32":
        # Reset ssh-agent identities
        run("ssh-add -D")
        # Load the selected key
        run('ssh-add "{0}"'.format(ssh_key))

    # Configure Git identity (cross-platform)
    run('git config --global user.name "{0}"'.format(git_name))
    run('git config --global user.email "{0}"'.format(git_email))

    # Force Git to use the selected key for all remotes
    run('git config --global core.sshCommand "ssh -i \\"{0}\\""'.format(ssh_key))

    messagebox.showinfo(
        "Identity switched",
        "Now using:\n\n"
        "Profile: {0}\n"
        "Git name: {1}\n"
        "Email: {2}".format(identity["name"], git_name, git_email),
    )
