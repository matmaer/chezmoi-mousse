"""Module to run shell commands with subprocess."""

from collections.abc import Sequence
from dataclasses import dataclass, field
import shutil
import subprocess


@dataclass
class FullCommand:
    command: str = field(default="exit")
    cmd_args: list = field(default_factory=list)
    verb_args: list = field(default_factory=list)

    def get_full_cmd_list(self) -> tuple:
        cmd_list = [self.command] + self.cmd_args + self.verb_args
        return tuple(cmd_list)

    def get_short_cmd(self) -> list:
        return [self.command]


@dataclass
class Chezmoi(FullCommand):

    command = shutil.which("chezmoi")
    cmd_args = [
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
    ]
    verb_dict = {
        "doctor": ["doctor"],
        "dump_config": ["dump-config", "--format=json"],
        "data": ["data", "--format=json"],
        "cat_config": ["cat-config"],
        "ignored": ["ignored"],
        "managed": ["managed"],
        "status": ["status", "--parent-dirs"],
        "unmanaged": ["unmanaged", "--path-style=absolute"],
    }


# same logic as the Chezmoi class but with different command and verbs
@dataclass
class Git(FullCommand):
    command = shutil.which("git")
    cmd_args = [
        "--no-advice",
        "--no-pager",
    ]
    verb_dict = {
        "status": [],
        "log": ["--oneline"],
    }


###########################################################
# run returns from the stored data or runs subprocess.run #
###########################################################


class ChezmoiIO(FullCommand):

    def __init__(self, refresh: bool = False) -> None:
        super().__init__()
        self.short_cmd = self.get_short_cmd()
        self.full_cmd = self.get_full_cmd_list()
        self.refresh = refresh

    def get_cmd_output(self):
        if self.refresh:
            pass

    def _sub_run(self, cmd_sequence: Sequence) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd_sequence,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )

