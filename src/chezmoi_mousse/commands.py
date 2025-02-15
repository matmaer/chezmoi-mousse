from dataclasses import dataclass, field
import shutil
import subprocess

CMD_OUTPUT = {}

def get_output(full_cmd: list, io_key: str, refresh: bool = False) -> str:
    if refresh or io_key not in CMD_OUTPUT:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        CMD_OUTPUT[io_key] = result.stdout
    return CMD_OUTPUT[io_key]

@dataclass(frozen=True)
class Command:

    command: str | None = None
    cmd_args: list = field(default_factory=list)
    verb_cmds: dict = field(default_factory=dict)
    verb: str | None = None

    @property
    def full_command(self) -> list:
        # if not found, does not raise an exception
        cmd_path = shutil.which(self.command)
        if cmd_path is None:
            raise FileNotFoundError(
                f"Command {self.command} not found in PATH"
            )
        try:
            verb_cmd = self.verb_cmds[self.verb]
        except KeyError as exc:
            raise KeyError(f"Invalid verb: {self.verb}") from exc
        return [cmd_path] + self.cmd_args + verb_cmd

    @property
    def io_key(self) -> str:
        return f"{self.command}_{self.verb}"

    # @property
    # def all_verbs(self) -> list:
    #     return list(self.verb_cmds.keys())

    def run(self, refresh: bool = False) -> str:
        return get_output(self.full_command, self.io_key, refresh)


@dataclass(frozen=True)
class Chezmoi(Command):

    command: str = "chezmoi"
    # verb: str
    cmd_args: tuple = (
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
    )

    verb_cmds: dict = field(default_factory={
        "doctor": ("doctor",),
        "dump_config": ("dump-config", "--format=json"),
        "data": ("data", "--format=json"),
        "cat_config": ("cat-config",),
        "ignored": ("ignored",),
        "managed": ("managed",),
        "status": ("status", "--parent-dirs"),
        "unmanaged": ("unmanaged", "--path-style=absolute"),
    })


@dataclass(frozen=True)
class Git(Command):
    command: str = "git"
    # verb: str
    cmd_args: tuple = (
        "--no-advice",
        "--no-pager",
    )
    verb_cmds: dict = field(default_factory={
        "status": ("status",),
        "log": ("log", "--oneline"),
    })
