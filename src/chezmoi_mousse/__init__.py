"""Singleton to store output for each command in the ChezmoiCommands class"""

# current chezmoi commands used by the TUI, including default verb flags

COMMANDS = (
    "data --format=json",
    "dump-config --format=json",
    "cat-config", # no flags available, except --help
    "doctor", # only available flag is --no-network, not used in the TUI
    "ignored", # only available flag is --tree, not used in the TUI
    "managed --path-style=absolute", # absolute to filter for DirectoryTree
    "unmanaged --path-style=absolute", # absolute for DirectoryTree
    "status --parent-dirs", # flag probably not needed
)

# singleton to "cache" the output for each command
CHEZMOI = dict()

for command in COMMANDS:
    verb = command.split()[0] # remove flags to create short dict key

    CHEZMOI[verb] = {
        "command": command, # verb+arguments that will be added to chezmoi
        "full_command": str(), # will hold the full command run by subprocess
        "output": str(), # will store stdout or stderr from subprocess.run
    }
