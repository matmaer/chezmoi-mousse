import ast
import subprocess
import tomllib
from dataclasses import dataclass  # , field

# from textual import log
# log.debug("debug message")


class Utils:

    @staticmethod
    def parse_stdout(new_stdout: str) -> str | list | dict:
        new_stdout = new_stdout.strip()
        if new_stdout in (None, ""):
            raise ValueError("Empty new_stdout, this needs to be handled.")
        try:
            return ast.literal_eval(new_stdout)
        except SyntaxError:
            return tomllib.loads(new_stdout)
        except ValueError:
            return new_stdout.splitlines()

    @staticmethod
    def run(long_command) -> str:
        result = subprocess.run(
            long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        return result.stdout

    @staticmethod
    def long_cmd_label_id(long_command: list) -> tuple:
        label = " ".join([w for w in long_command if not w.startswith("-")])
        cmd_id = label.replace("-", "_")
        return label, cmd_id

@dataclass
class Data:

    long_command: list
    py_out: str | list | dict | None = None
    std_out: str | None = None

    @property
    def label(self) -> str:
        return " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )

    @property
    def cmd_id(self) -> str:
        return self.label.replace(" ", "_").replace("-", "_")


class Chezmoi(Utils):

    base = [
        "chezmoi",
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
    ]
    subs = [
        ["doctor"],
        ["dump-config", "--format=json"],
        ["data", "--format=json"],
        ["cat-config"],
        ["ignored"],
        ["managed", "--path-style=absolute"],
        ["status", "--parent-dirs"],
        ["unmanaged", "--path-style=absolute"],
        ["git", "status"],
        ["git", "log", "--", "--oneline"],
    ]

    def __init__(self):
        self.name = self.base[0]
        self._data_instances = {}

        for sub in self.subs:
            cmd_id, _ = self.long_cmd_id_label(sub)
            setattr(self, cmd_id, self.cmd_data(sub))

    def cmd_data(self, subcommand: list) -> Data:
        long_command = self.base + subcommand
        cmd_data = Data(long_command)
        self._data_instances[cmd_data.cmd_id] = cmd_data
        return cmd_data

    # used to loop over on the loading screen
    @property
    def all_long_commands(self) -> dict:
        all_long_commands = []
        for sub in self.subs:
            all_long_commands.append(self.base + sub)
        return all_long_commands
