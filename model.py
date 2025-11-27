import json
import os
import subprocess
from typing import List, Dict

CONFIG_FILE: str = "identities.json"


def run(cmd: str) -> None:
    """Run a shell command."""
    subprocess.call(cmd, shell=True)


def load_identities() -> List[Dict]:
    """Load identities from JSON. Create an empty file if missing."""
    if not os.path.exists(CONFIG_FILE):
        data = {"identities": []}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return []

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("identities", [])


def save_identities(identities: List[Dict]) -> None:
    """Persist identities to JSON."""
    data = {"identities": identities}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def apply_identity(identity: Dict) -> None:
    """
    Apply a single identity:
    - Reset ssh-agent keys
    - Add the selected SSH key
    - Set global git user.name / user.email
    - Force git to use this SSH key via core.sshCommand
    """
    from tkinter import messagebox  # imported here to avoid hard Tk dependency

    ssh_key: str = os.path.expanduser(identity["ssh_key"])
    git_name: str = identity["git_name"]
    git_email: str = identity["git_email"]

    if not os.path.exists(ssh_key):
        messagebox.showerror(
            "SSH key not found",
            f"SSH key file does not exist:\n{ssh_key}",
        )
        return

    # Reset ssh-agent identities
    run("ssh-add -D")

    # Load the selected key
    run(f"ssh-add {ssh_key}")

    # Configure Git identity
    run(f'git config --global user.name "{git_name}"')
    run(f'git config --global user.email "{git_email}"')

    # Force Git to use the selected key for all remotes
    run(f'git config --global core.sshCommand "ssh -i {ssh_key}"')

    messagebox.showinfo(
        "Identity switched",
        f"Now using:\n\n"
        f"Profile: {identity['name']}\n"
        f"Git name: {git_name}\n"
        f"Email: {git_email}",
    )
