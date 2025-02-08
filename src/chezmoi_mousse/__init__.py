"""Singleton to store output for each command"""

import shutil
from dataclasses import dataclass, field

if shutil.which("chezmoi") is None:
    raise FileNotFoundError("The chezmoi command was not found in PATH.")


@dataclass
class CommandData:
    verb_cmd: list = field(default_factory=list)
    stdout: str = field(default_factory=str)
    pyout: str | list | dict = field(default_factory=str)
    base_cmd: list = field(
        default_factory=lambda: [
            shutil.which("chezmoi"),
            "--no-pager",
            "--color=false",
            "--no-tty",
            "--progress=false",
        ],
        init=False,
    )


@dataclass
class KnownCommands:

    cat_config: CommandData = field(
        default_factory=lambda: CommandData(verb_cmd=["cat-config"])
    )
    doctor: CommandData = field(
        default_factory=lambda: CommandData(verb_cmd=["doctor"])
    )
    ignored: CommandData = field(
        default_factory=lambda: CommandData(verb_cmd=["ignored"])
    )
    data: CommandData = field(
        default_factory=lambda: CommandData(verb_cmd=["data", "--format=json"])
    )
    dump_config: CommandData = field(
        default_factory=lambda: CommandData(
            verb_cmd=["dump-config", "--format=json"]
        )
    )
    managed: CommandData = field(
        default_factory=lambda: CommandData(
            verb_cmd=["managed", "--path-style=absolute"]
        )
    )
    unmanaged: CommandData = field(
        default_factory=lambda: CommandData(
            verb_cmd=["unmanaged", "--path-style=absolute"]
        )
    )
    status: CommandData = field(
        default_factory=lambda: CommandData(
            verb_cmd=["status", "--parent-dirs"]
        )
    )


CHEZMOI = KnownCommands()

SPLASH = """\
 _______ _______ _______ _______ ____ ____ _______ _o_
|       |   |   |    ___|___    |    ˇ    |       |   |
|    ===|       |     __'     __|         |   |   |   |
|       |   |   |       |       |   |ˇ|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
   ____ ____ _______ ___ ___ _______ _______ _______
  |    ˇ    |       |   |   |    ___|    ___|    ___|
  |         |   |   |   |   |__     |__     |     __|
  |   |ˇ|   |       |       |       |       |       |
  '---' '---^-------^-------^-------^-------^-------'
"""
