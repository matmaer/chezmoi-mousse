"""
Module to run shell commands with subprocess.

CMD_OUTPUT is primitive "cache" to store the last output from subprocess.run().
The output gets overwritten each time a new call is made when specified.
For the wrapper, "refresh=False" by default to return this CMD_OUTPUT value.
"""

# from dataclasses import dataclass
import shutil
import subprocess

CMD_OUTPUT = {}


def _get_output(
    cmd_and_args: list, verb_and_args: str, refresh: bool = False
) -> str:
    io_key = f"{cmd_and_args[0]}_{verb_and_args[0]}"
    full_command = cmd_and_args + verb_and_args
    refresh = refresh or io_key not in CMD_OUTPUT
    if refresh:
        result = subprocess.run(
            full_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        CMD_OUTPUT[io_key] = result.stdout
    return CMD_OUTPUT[io_key]


class Command:

    command: str | None = None
    #     global_flags: list | None = None
    #     verbs_with_flags: dict | None = None

    @property
    def cmd_path(self) -> str:
        cmd_path = shutil.which(self.command)
        if not cmd_path:
            raise FileNotFoundError(
                f"Command {self.command} not found in PATH"
            )
        return cmd_path


#     @property
#     def cmd_and_args(self) -> list:
#         return [self.command] + self.global_flags

#     @property
#     def available_verbs(self) -> list:
#         return self.verbs_with_flags.keys()


class Chezmoi(Command):

    command = "chezmoi"

    def __init__(self) -> None:
        # self.verb = verb
        self.cmd_with_args = [
            self.cmd_path,
            "--no-pager",
            "--color=false",
            "--no-tty",
            "--progress=false",
        ]
        self.verbs_with_flags = {
            "doctor": ["doctor"],
            "dump_config": ["dump-config", "--format=json"],
            "data": ["data", "--format=json"],
            "cat_config": ["cat-config"],
            "ignored": ["ignored"],
            "managed": ["managed"],
            "status": ["status", "--parent-dirs"],
            "unmanaged": ["unmanaged", "--path-style=absolute"],
        }

    def run(self, verb) -> str:
        return _get_output(self.cmd_with_args, self.verbs_with_flags[verb])


# @dataclass
# class Git(Command):

#     command: str = "git"
#     global_flags: list = [
#         "--no-advice",
#         "--no-pager",
#     ]
#     verbs_with_flags: dict = {
#         "status": ["status"],
#         "log": ["log", "--oneline"],
#     }

#     @classmethod
#     def run(cls, verb) -> str:
#         return _get_output(cls.cmd_and_args, cls.verbs_with_flags[verb])
