"""Singleton to store output for each command in the ChezmoiCommands class"""

# current chezmoi commands used by the TUI, including default verb flags

COMMANDS = {
    "data": "data --format=json",
    "dump-config": "dump-config --format=json",
    "cat-config": "cat-config", # no flags available, except --help
    "doctor": "doctor", # only available flag is --no-network, not used in the TUI
    "ignored": "ignored", # only available flag is --tree, not used in the TUI
    "managed": "managed --path-style=absolute", # absolute to filter for DirectoryTree
    "unmanaged": "unmanaged --path-style=absolute", # absolute for DirectoryTree
    "status": "status --parent-dirs", # flag probably not needed
}

# singleton to "cache" the output for each command
CHEZMOI = dict()

for command in COMMANDS.values():
    verb = command.split()[0] # remove flags to create short dict key

    CHEZMOI[verb] = {
        "command": command, # verb+arguments to run chezmoi
        "full_command": str(), # will hold the full command run by subprocess.run
        "output": str(), # will store stdout or stderr from subprocess.run
    }
