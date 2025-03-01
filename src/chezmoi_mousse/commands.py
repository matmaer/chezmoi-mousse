import json
import subprocess
import tomllib
from dataclasses import dataclass


class Utils:

    @staticmethod
    def get_arg_id(long_command: list[str]) -> str:
        all_args = long_command[1:]
        verbs = [w for w in all_args if not w.startswith("-")]
        return "_".join([w.replace("-", "_") for w in verbs])

    @staticmethod
    def parse_std_out(std_out) -> str | list | dict:
        failures = {}
        std_out = std_out.strip()
        if std_out == "":
            return "std_out is an empty string nothing to decode"
        try:
            return json.loads(std_out)
        except json.JSONDecodeError:
            failures["json"] = "std_out json.JSONDecodeError"
            try:
                return tomllib.loads(std_out)
            except tomllib.TOMLDecodeError:
                failures["toml"] = "std_out tomllib.TOMLDecodeError"
                # check how many "\n" newlines are found in the output
                if std_out.count("\n") > 0:
                    return std_out.splitlines()
        # should not be returned, just gives feedback in the tui
        return failures

    @staticmethod
    def subprocess_run(long_command):
        result = subprocess.run(
            long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        return result.stdout


@dataclass
class InputOutput:
    long_cmd: list[str]
    arg_id: str
    std_out: str = ""
    py_out: str | list | dict | None = None
    label: str = "Will contain the label after initialization."

    def update(self) -> str | list | dict:
        self.std_out = Utils.subprocess_run(self.long_cmd)
        self.py_out = Utils.parse_std_out(self.std_out)
        return self.py_out

    def __post_init__(self):
        self.label = " ".join(
            [w for w in self.long_cmd if not w.startswith("-")]
        )


class Chezmoi(Utils):

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
        self.all_arg_ids = []
        for long_cmd in self.long_commands:
            arg_id = Utils.get_arg_id(long_cmd)
            setattr(self, arg_id, InputOutput(long_cmd, arg_id))
            self.all_arg_ids.append(arg_id)


chezmoi = Chezmoi()
