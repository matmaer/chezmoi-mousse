"""Singleton to store output for each command in the ChezmoiCommands class"""

# current chezmoi verbs that can be handled by the TUI
VERBS = (
    "data",
    "dump-config",
    "cat-config",
    "doctor",
    "ignored",
    "managed",
    "unmanaged",
    "status",
)

# singleton to cache the output for each command
CHEZMOI = dict()

for verb in VERBS:
    CHEZMOI[verb] = {
        "command": str(),
        "output": str(),
    }
