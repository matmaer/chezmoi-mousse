import json
import subprocess
from dataclasses import dataclass


class Utils:

    @staticmethod
    def get_args_id(long_cmd: list[str]) -> str:
        all_args = long_cmd[1:]
        verbs = [w for w in all_args if not w.startswith("-")]
        return "_".join([w.replace("-", "_") for w in verbs])


@dataclass
class InputOutput:
    long_cmd: list[str]
    std_out: str = ""

    @property
    def label(self) -> str:
        return " ".join([w for w in self.long_cmd if not w.startswith("-")])

    @property
    def args_id(self) -> str:
        return Utils.get_args_id(self.long_cmd)

    @property
    def list_out(self) -> list[str]:
        try:
            return self.std_out.splitlines()
        except AttributeError:
            return []

    @property
    def dict_out(self) -> dict[str, str]:
        try:
            return json.loads(self.std_out.strip())
        except json.JSONDecodeError:
            return {}

    def update(self) -> str:
        result = subprocess.run(
            self.long_cmd,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        self.std_out = result.stdout
        return result.stdout


class Chezmoi:

    name = "chezmoi"
    base = [name] + [
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
    ]
    subs = [
        ["cat-config"],
        ["data", "--format=json"],
        ["doctor"],
        ["dump-config", "--format=json"],
        ["git", "log", "--", "--oneline"],
        ["git", "status"],
        ["ignored"],
        ["managed", "--path-style=absolute"],
        ["status", "--parent-dirs"],
        ["unmanaged", "--path-style=absolute"],
    ]

    @property
    def long_commands(self):
        return [self.base + sub for sub in self.subs]

    def __init__(self):
        for long_cmd in self.long_commands:
            input_output = InputOutput(long_cmd)
            setattr(self, input_output.args_id, input_output)


chezmoi = Chezmoi()
