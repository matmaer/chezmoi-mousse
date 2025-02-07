"""Singleton to store output for each command in the ChezmoiCommands class"""

# current chezmoi commands used by the TUI, including default verb flags

# singleton to "cache" the output for each command
CHEZMOI = {
    "data": {
        "command": "data --format=json",
        "full_command": str(),
        "output": str(),
    },
    "dump-config": {
        "command": "dump-config --format=json",
        "full_command": str(),
        "output": str(),
    },
    "cat-config": {
        "command": "cat-config",
        "full_command": str(),
        "output": str(),
    },
    "doctor": {
        "command": "doctor",
        "full_command": str(),
        "output": str(),
    },
    "ignored": {
        "command": "ignored",
        "full_command": str(),
        "output": str(),
    },
    "managed": {
        "command": "managed --path-style=absolute",
        "full_command": str(),
        "output": str(),
    },
    "unmanaged": {
        "command": "unmanaged --path-style=absolute",
        "full_command": str(),
        "output": str(),
    },
    "status": {
        "command": "status --parent-dirs",
        "full_command": str(),
        "output": str(),
    },
}