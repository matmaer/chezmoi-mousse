from enum import StrEnum


class UnwantedDir(StrEnum):
    __pycache__ = "__pycache__"
    dot_build = ".build"
    dot_bundle = ".bundle"
    dot_cache = ".cache"
    dot_dart_tool = ".dart_tool"
    dot_DS_Store = ".DS_Store"
    dot_git = ".git"
    dot_ipynb_checkpoints = ".ipynb_checkpoints"
    dot_mozilla = ".mozilla"
    dot_mypy_cache = ".mypy_cache"
    dot_parcel_cache = ".parcel_cache"
    dot_pytest_cache = ".pytest_cache"
    dot_ssh = ".ssh"
    dot_Trash = ".Trash"
    dot_venv = ".venv"
    bin = "bin"
    cache = "cache"
    Cache = "Cache"
    CMakeFiles = "CMakeFiles"
    Crash_Reports = "Crash Reports"
    DerivedData = "DerivedData"
    Desktop = "Desktop"
    Documents = "Documents"
    Downloads = "Downloads"
    extensions = "extensions"
    go_build = "go-build"
    node_modules = "node_modules"
    Pictures = "Pictures"
    Public = "Public"
    Recent = "Recent"
    temp = "temp"
    Temp = "Temp"
    tmp = "tmp"
    trash = "trash"
    Trash = "Trash"
    Videos = "Videos"


class UnwantedFile(StrEnum):
    AppImage = ".AppImage"
    bak = ".bak"
    cache = ".cache"
    coverage = ".coverage"
    doc = ".doc"
    docx = ".docx"
    egg_info = ".egg-info"
    gz = ".gz"
    kdbx = ".kdbx"
    lock = ".lock"
    pdf = ".pdf"
    pid = ".pid"
    ppt = ".ppt"
    pptx = ".pptx"
    rar = ".rar"
    swp = ".swp"
    tar = ".tar"
    temp = ".temp"
    tgz = ".tgz"
    tmp = ".tmp"
    xls = ".xls"
    xlsx = ".xlsx"
    zip = ".zip"


unwanted_names = {
    "dirs": set(item.value for item in UnwantedDir),
    "files": set(item.value for item in UnwantedFile),
}


# Chezmoi status command output reference:
# https://www.chezmoi.io/reference/commands/status/
status_info = {
    "code name": {
        "space": "No change",
        "A": "Added",
        "D": "Deleted",
        "M": "Modified",
        "R": "Modified Script",
    },
    "re add change": {
        "space": "no changes for repository",
        "A": "add to repository",
        "D": "mark as deleted in repository",
        "M": "modify in repository",
        "R": "not applicable for repository",
    },
    "apply change": {
        "space": "no changes for filesystem",
        "A": "create on filesystem",
        "D": "delete from filesystem",
        "M": "modify on filesystem",
        "R": "modify script on filesystem",
    },
}


pw_mgr_info = {
    "age-command": {
        "description": "A simple, modern and secure file encryption tool",
        "link": "https://github.com/FiloSottile/age",
    },
    "bitwarden-command": {
        "description": "Bitwarden Password Manager",
        "link": "https://github.com/bitwarden/cli",
    },
    "bitwarden-secrets-command": {
        "description": "Bitwarden Secrets Manager CLI for managing secrets securely.",
        "link": "https://github.com/bitwarden/bitwarden-secrets",
    },
    "doppler-command": {
        "description": "The Doppler CLI for managing secrets, configs, and environment variables.",
        "link": "https://github.com/DopplerHQ/cli",
    },
    "gopass-command": {
        "description": "The slightly more awesome standard unix password manager for teams.",
        "link": "https://github.com/gopasspw/gopass",
    },
    "keeper-command": {
        "description": "An interface to Keeper® Password Manager",
        "link": "https://github.com/Keeper-Security/Commander",
    },
    "keepassxc-command": {
        "description": "Cross-platform community-driven port of Keepass password manager",
        "link": "https://keepassxc.org/",
    },
    "lpass-command": {
        "description": "Old LastPass CLI for accessing your LastPass vault.",
        "link": "https://github.com/lastpass/lastpass-cli",
    },
    "pass-command": {
        "description": "Stores, retrieves, generates, and synchronizes passwords securely",
        "link": "https://www.passwordstore.org/",
    },
    "pinentry-command": {
        "description": "Collection of simple PIN or passphrase entry dialogs which utilize the Assuan protocol",
        "link": "https://gnupg.org/related_software/pinentry/",
    },
    "rbw-command": {
        "description": "Unofficial Bitwarden CLI",
        "link": "https://git.tozt.net/rbw",
    },
    "vault-command": {
        "description": "A tool for managing secrets",
        "link": "https://vaultproject.io/",
    },
}


# provisional diagrams until dynamically created
FLOW = """\
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │                   │                   │                   │
       │     Add Tab       │    autoCommit     │     git push      │
       │   Re-Add Tab      │──────────────────>│──────────────────>│
       │──────────────────>│                   │                   │
       │                   │                autopush               │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │                   │
       │     Apply Tab     │     chezmoi init & chezmoi git pull   │
       │<──────────────────│<──────────────────────────────────────│
       │                   │                   │                   │
       │     Diff View     │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─>│                   │                   │
       │                   │                   │                   │
       │                   │    chezmoi init & chezmoi git pull    │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │        chezmoi init --one-shot & chezmoi init --apply     │
       │<──────────────────────────────────────────────────────────│
       │                   │                   │                   │
┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐
│ destination  │    │ target state │    │ source state │    │  git remote  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
"""
