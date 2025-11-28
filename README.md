# Git Identity Switcher

Git Identity Switcher is a simple, cross-platform tool that allows you to quickly switch between multiple Git identities (username, email, and SSH keys). Designed for developers who work across personal, work, university, or open‑source contexts.

This README explains **how to install, run, and use the app** on Linux (including Fedora/Bazzite via Distrobox) and Windows.

---

# 📦 Features

* Store multiple Git profiles
* Switch Git `user.name`, `user.email`, and preferred SSH key with one click
* Works on Linux, macOS, and Windows
* Clean UI for creating, editing, and deleting profiles
* Installer & uninstaller scripts

---

# 🚀 Installation

## Linux (Fedora, Bazzite, Ubuntu, Arch, Debian, Distrobox)

### 🔧 Inside a Distrobox (recommended)

If you are using Bazzite, Silverblue, or an rpm‑ostree based distro, **run the app from inside a Distrobox container**.

1. Enter your Distrobox:

   ```bash
   distrobox enter <container-name>
   ```

   Example:

   ```bash
   distrobox enter fedora-dev
   ```

2. Inside the container, install the app:

   ```bash
   python3 installer.py
   ```

3. Export it to your host system:

   ```bash
   distrobox-export --app git-identity-switcher
   ```

4. You will now see **Git Identity Switcher** in your desktop environment's application list.
   Clicking it will automatically launch the app *inside the container*, where all dependencies exist.

---

### 🐧 Standard Linux install (no Distrobox)

If you are not using Distrobox and want the app on your native system:

1. Install dependencies:

   ```bash
   sudo dnf install python3 python3-tkinter   # Fedora/Bazzite
   sudo apt install python3 python3-tk         # Debian/Ubuntu
   sudo pacman -S python tk                    # Arch
   ```

2. Install the app:

   ```bash
   python3 installer.py
   ```

3. Search for **Git Identity Switcher** in your system application launcher.

No further setup required.

---

# 🪟 Windows Installation

1. Install Python 3.10+ from [https://python.org](https://python.org)
2. Clone or download this repository
3. Open PowerShell in the project folder and run:

   ```powershell
   python installer.py
   ```

This installs the app into:

```
%APPDATA%\GitIdentitySwitcher
```

You may create a Start Menu shortcut pointing to:

```
%APPDATA%\GitIdentitySwitcher\git-identity-switcher.bat
```

---

# ▶️ Running the App

After installation:

### Linux (native)

Search your system launcher for:

```
Git Identity Switcher
```

### Linux (Distrobox export)

Your desktop launcher automatically uses:

```
distrobox enter <container-name> -- git-identity-switcher
```

### Windows

Run:

```
%APPDATA%\GitIdentitySwitcher\git-identity-switcher.bat
```

Or use your shortcut.

---

# 🧭 Usage

1. Start the application
2. Add new identities using the **Manage identities** menu
3. Each identity consists of:

   * Profile name
   * Git user.name
   * Git user.email
   * SSH key path

When you select an identity and click **Switch**, the app will:

* Load your SSH key into `ssh-agent`
* Set your global Git username/email
* Set Git to use the selected SSH key for all remotes

---

# 🔧 Uninstalling

Run:

```bash
python3 uninstall.py
```

This removes:

* `~/.local/share/git-identity-switcher` (Linux)
* `~/.local/bin/git-identity-switcher`
* App launcher (`.desktop` file)
* Windows: `%APPDATA%/GitIdentitySwitcher`

---

# 💡 Troubleshooting

### App doesn't launch from GNOME/KDE but works in terminal

If you're using **Distrobox**, the host cannot see container-installed Python/Tk.

Solution: **export the app properly**:

```bash
distrobox-export --app git-identity-switcher
```

This ensures the desktop launcher runs inside the correct environment.

### App silently does nothing when clicked

Check logs (only if logging wrapper is enabled):

```
~/.local/share/git-identity-switcher/run.log
```

---

# 📜 License

Licensed under MIT. See `LICENSE` for details.

---

# 🙌 Contributions

Contributions and issues are welcome!
Feel free to submit PRs to improve functionality, UI design, or platform support.
