import ast
import subprocess
import tomllib
from dataclasses import dataclass

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
    def run(long_cmd) -> str:
        result = subprocess.run(
            long_cmd,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        return result.stdout


@dataclass
class InputOutput:
    """
    Contains the command list for, and return from a subprocess.run call.
    """

    # Dataclass that also serves as a kind of API, @property decorated methods,
    # for any command class which is instantiated for each sub command.

    long_cmd: list
    py_out: str | list | dict | None = None
    std_out: str | None = None

    @property
    def label(self) -> str:
        return " ".join([w for w in self.long_cmd if not w.startswith("-")])

    # Should be sub id so it can be accessed from an instantiated command class
    # without repeating the main command name
    @property
    def sub_id(self) -> str:
        sub_label = "_".join(self.label.split(" ")[1:])
        return sub_label.replace("-", "_")


class Chezmoi:
    # TODO: general command logic can be moved to command class when more
    # commands are added like ls, tree, etc.
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
    all_long_cmds = [    ]

    def __init__(self):
        # just the name, not sure why yet
        self.name = self.base[0]

        # will hold all InputOutput instances mapped to sub command id
        # the same sub command id will also be set as an attribute
        # see set attr
        self.io = {}

        for sub in self.subs:
            long_command = self.base + sub
            # dictionary key is the sub command id
            io = InputOutput(long_command)
            self.io[io.sub_id] = io
            # attribute which points to the corresponding InputOutput instance
            setattr(self, io.sub_id, io)

        # used to loop over all commands, eg the loading screen
        for sub in self.subs:
            self.all_long_cmds.append(self.base + sub)
