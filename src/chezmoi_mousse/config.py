filter_switch_data = {
    "unmanaged": {
        "tooltip": (
            "Enable to include all un-managed files, even if they live in an un-managed directory. "
            "Disable to only show un-managed files in directories which already contain managed files (the default). "
            "The purpose is to easily spot new un-managed files in already managed directories. "
            "(in both cases, only the un-managed files are shown)"
        ),
        "label": "Include unmanaged directories",
        "filter_keys": ["add_tab"],
    },
    "unwanted": {
        "tooltip": (
            'Show files and directories considered as "unwanted" for a dotfile manager. '
            "These include cache, temporary, trash (recycle bin) and other similar files or directories. "
            'For example enable this to add files to your chezmoi repository which are in a directory named ".cache".'
        ),
        "label": "Show unwanted paths",
        "filter_keys": ["add_tab"],
    },
    "include_unchanged_files": {
        "label": "Include files without changed status",
        "tooltip": "Show only files which are found in the chezmoi status output.",
        "filter_keys": ["apply_tab", "re_add_tab"],
    },
}

unwanted = {
    "dirs": {
        "__pycache__",
        ".build",
        ".bundle",
        ".cache",
        ".dart_tool",
        ".DS_Store",
        ".git",
        ".ipynb_checkpoints",
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
        "go-build",
        "node_modules",
        "Recent",
        "temp",
        "Temp",
        "tmp",
        "trash",
        "Trash",
    },
    "files": {
        ".bak",
        ".cache",
        ".coverage",
        ".doc",
        ".docx",
        ".egg-info",
        ".gz",
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
