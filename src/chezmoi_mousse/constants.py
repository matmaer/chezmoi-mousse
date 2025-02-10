import shutil
from collections import namedtuple


def build_command_namedtuple() -> namedtuple:

    all_commands = {
        "chezmoi": {
            "cmd": [
                shutil.which("chezmoi"),
                "--no-pager",
                "--color=false",
                "--no-tty",
                "--progress=false",
            ],
            # contains verb with proper hyphens and arguments
            "verbs":{
                "doctor": ["doctor"],
                "dump_config": ["dump-config", "--format=json"],
                "data": ["data", "--format=json"],
                "cat_config": ["cat-config"],
                "ignored": ["ignored"],
                "managed": ["managed", "--path-style=absolute"],
                "status": ["status", "--parent-dirs"],
                "unmanaged": ["unmanaged", "--path-style=absolute"],
            },
        },
        "git": {
            "cmd": [
                shutil.which("git"),
                "--no-advice",
                "--no-pager",
            ],
            "verbs": {"status": ["status"], "log": ["log"]},
        },
    }

    Commands = namedtuple("Commands", all_commands.keys())

    for command, section in all_commands.items():
        # Commands[command] = namedtuple(command, section["verbs"].keys())
        setattr(Commands, command, namedtuple(command, section["verbs"].keys()))

        for verb, args in section["verbs"].items():
            full_command = section["cmd"] + args
            setattr(getattr(Commands, command), verb, full_command)

    return Commands

