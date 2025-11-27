# Git Identity Switcher

A simple desktop application for managing and switching between multiple Git identities.  
Useful for users who work with separate personal, university, and work GitHub accounts.

The application provides a graphical interface where each identity stores:
- Git `user.name`
- Git `user.email`
- Associated SSH private key (selected via file dialog)

Identities can be added, edited, or removed without manually editing Git or SSH configuration files.

---

## Features

- Switch Git identity with a single click.
- Add multiple identities with separate Git and SSH settings.
- Edit or remove identities at any time.
- SSH keys selected through a file chooser (no manual typing).
- Clean, single-window application flow.
- Modular code structure split across multiple Python files.
- Identities stored in a simple JSON file.

---

## Requirements

- Python 3.9 or later  
- Tkinter (ships with most Linux distributions)  
- Git installed  
- SSH keys already generated (e.g., using `ssh-keygen`)

---


## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/git-identity-switcher.git
cd git-identity-switcher
```

Run the application: 

```bash
python3 identity_switcher.py
```

I could explain in depth what to do but if you need this tool I assume you already know how ssh keys and git configs work.
