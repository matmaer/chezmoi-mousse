import json
import shutil
import subprocess
from dataclasses import dataclass, field

__all__ = ["run", "chezmoi_config"]


@dataclass
class Components:

    cmd_name = "chezmoi"

    global_cmd = [
        shutil.which(cmd_name),
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
    ]

    subs = {
        "doctor": ["doctor"],
        "dump_config": ["dump-config", "--format=json"],
        "data": ["data", "--format=json"],
        "cat_config": ["cat-config"],
        "ignored": ["ignored"],
        "managed": ["managed", "--path-style=absolute"],
        "status": ["status", "--parent-dirs"],
        "unmanaged": ["unmanaged", "--path-style=absolute"],
        "git_status": ["git", "status"],
        "git_log": ["git", "log", "--", "--oneline"],
    }

    def full_cmd(self, sub_cmd_name: str) -> list[str]:
        return self.global_cmd + self.subs[sub_cmd_name]

    # pretty string for logging: full command without flags
    def pretty_cmd(self, sub_cmd_name: str) -> str:
        sub_cmd = self.subs[sub_cmd_name]
        pretty_subs = " ".join([_ for _ in sub_cmd if not _.startswith("-")])
        return f"{self.cmd_name} {pretty_subs}"


    # property for the loader screen loop
    @property
    def all_full_commands(self):
        return [self.full_cmd(_) for _ in self.subs]


@dataclass
class CommandIO(Components):
    output: dict = field(init=False)

    def __post_init__(self):
        self.output = {key: None for key in self.subs}

    def get_command_output(self, sub_cmd: str) -> str:
        return self.output[sub_cmd]

    def set_command_output(self, sub_cmd: str, output: str):
        self.output[sub_cmd] = output

    def _subprocess_run(self, sub_cmd: str) -> str:
        command_to_run = self.full_cmd(sub_cmd)
        result = subprocess.run(
            command_to_run,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        return result.stdout

    def get_output(self, sub_cmd: str, refresh: bool = False) -> str:
        if refresh or not self.get_command_output(sub_cmd):
            subprocess_stdout = self._subprocess_run(sub_cmd)
            self.set_command_output(sub_cmd, subprocess_stdout)
        return self.get_command_output(sub_cmd)

    @property
    def chezmoi_config(self) -> dict:
        return json.loads(self.get_output("dump_config"))


run = CommandIO().get_output

chezmoi_config = CommandIO().chezmoi_config
