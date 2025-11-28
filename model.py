from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List


BASE_DIR: Path = Path(__file__).resolve().parent
CONFIG_FILE: Path = BASE_DIR / "identities.json"


class SSHKeyNotFoundError(Exception):
    """
    Raised when the configured SSH key file does not exist.
    """


def run(command: str) -> None:
    """
    Run a shell command and ignore the exit code.

    This is intentionally simple because different platforms
    may have different SSH / Git setups.
    """
    subprocess.call(command, shell=True)


def load_identities() -> List[Dict]:
    """
    Load identities from JSON. Create an empty file if missing.

    The JSON structure is:
        { "identities": [ { ... }, ... ] }
    """
    if not CONFIG_FILE.exists():
        data: Dict[str, List[Dict]] = {"identities": []}
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return []

    raw: str = CONFIG_FILE.read_text(encoding="utf-8")
    try:
        data: Dict = json.loads(raw)
    except json.JSONDecodeError:
        data = {"identities": []}

    identities: List[Dict] = data.get("identities", [])
    if not isinstance(identities, list):
        identities = []

    return identities


def save_identities(identities: List[Dict]) -> None:
    """
    Persist identities list to JSON.
    """
    data: Dict[str, List[Dict]] = {"identities": list(identities)}
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def apply_identity(identity: Dict) -> str:
    """
    Apply a single identity:

    - On Unix: reset ssh-agent keys and add the selected SSH key.
    - Configure Git global user.name and user.email.
    - Force Git to use the selected SSH key via core.sshCommand.

    Returns a human-readable summary string that the UI can display.

    Raises:
        SSHKeyNotFoundError: if the SSH key path is missing.
    """
    ssh_key_raw: str = identity.get("ssh_key", "")
    git_name: str = identity.get("git_name", "")
    git_email: str = identity.get("git_email", "")
    profile_name: str = identity.get("name", "")

    ssh_key: str = os.path.expanduser(ssh_key_raw)

    if ssh_key == "" or not os.path.exists(ssh_key):
        raise SSHKeyNotFoundError(f"SSH key file does not exist: {ssh_key}")

    # Unix-style ssh-agent handling – safe to no-op on Windows
    if os.name != "nt":
        run("ssh-add -D")
        run(f'ssh-add "{ssh_key}"')

    # Git identity
    if git_name != "":
        run(f'git config --global user.name "{git_name}"')

    if git_email != "":
        run(f'git config --global user.email "{git_email}"')

    # Force Git to use the selected key (works with Git for Windows too)
    run(f'git config --global core.sshCommand "ssh -i \\"{ssh_key}\\""')

    summary: str = (
        "Now using:\n\n"
        f"Profile: {profile_name}\n"
        f"Git name: {git_name}\n"
        f"Email: {git_email}"
    )
    return summary
