import ast
import subprocess
import tomllib
from dataclasses import dataclass  # , field

# from textual import log

# log.warning("useless update, no change in stdout")
# log.debug(f"getting output for {self.name} {sub_label}")


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


@dataclass  # (kw_only=True, frozen=True)
class Data:

    cmd_id: str
    long_cmd: list
    std_out: str | None = None
    py_out: str | list | dict | None = None


class IO(Utils):

    def __init__(self, long_commands: list) -> None:
        self.long_commands = long_commands
        self.data = self._empty_data_dict()

    def _empty_data_dict(self) -> None:
        # construct a dict with std_out and py_out for each command id
        io = {}
        for long_command in self.long_commands:
            no_flags = [w for w in long_command if not w.startswith("-")]
            cmd_id = "_".join(no_flags).replace("-", "_")
            io[cmd_id] = Data(cmd_id, long_command)
        return io

    def get_output(self, cmd_id: str) -> str | list | dict:
        return self.data[cmd_id]["py_out"]

    def set_output(self, cmd_id: str, long_command) -> str | list | dict:
        self.data[cmd_id].std_out = self.run(long_command)
        self.data[cmd_id]["py_out"] = self.parse_stdout(
            self.data[cmd_id]["std_out"]
        )
        return self.data[cmd_id]["py_out"]


class Chezmoi(IO):

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
        super().__init__([self.base + words for words in self.subs])
        self._generate_attributes()

    def _generate_attributes(self):
        for cmd_id in self.data:
            setattr(self, cmd_id, self.data[cmd_id])

    @property
    def get(self) -> str:
        # return self.data.
        pass


chezmoi = Chezmoi()
