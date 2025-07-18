command_filters = [
    "--color=off"
    "--config"
    "--date-order"
    "--format=%ar by %cn;%s"
    "--force"
    "--format=json"
    "--mode=file"
    "--no-color"
    "--no-decorate"
    "--no-expand-tabs"
    "--no-pager"
    "--no-tty"
    "--path-style=absolute"
]

filter_tooltips = {
    "unmanaged_dirs": (
        "The default (disabled), only shows directories which already contain managed files."
        "This allows spotting new un-managed files in already managed directories."
        "Enable to show all directories which contain un-managed files."
    ),
    "unwanted": (
        'Include files and directories considered as "unwanted" for a dotfile manager. '
        "These include cache, temporary, trash (recycle bin) and other similar files or directories. "
        'For example enable this to add files to your chezmoi repository which are in a directory named ".cache".'
    ),
    "expand_all": "Expand all directories in the Tree view.",
    "unchanged": "Include files unchanged files which are not found in the 'chezmoi status' output.",
}

unwanted_names = {
    "dirs": {
        "__pycache__",
        ".build",
        ".bundle",
        ".cache",
        ".dart_tool",
        ".DS_Store",
        ".git",
        ".ipynb_checkpoints",
        ".mozilla",
        ".mypy_cache",
        ".parcel_cache",
        ".pytest_cache",
        ".ssh",
        ".Trash",
        ".venv",
        "bin",
        "cache",
        "Cache",
        "CMakeFiles",
        "Crash Reports",
        "DerivedData",
        "Desktop",
        "Documents",
        "Downloads",
        "extensions",
        "go-build",
        "node_modules",
        "Pictures",
        "Public",
        "Recent",
        "temp",
        "Temp",
        "tmp",
        "trash",
        "Trash",
        "Videos",
    },
    "files": {
        ".AppImage",
        ".bak",
        ".cache",
        ".coverage",
        ".doc",
        ".docx",
        ".egg-info",
        ".gz",
        ".kdbx",
        ".lock",
        ".pdf",
        ".pid",
        ".ppt",
        ".pptx",
        ".rar",
        ".swp",
        ".tar",
        ".temp",
        ".tgz",
        ".tmp",
        ".xls",
        ".xlsx",
        ".zip",
    },
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
