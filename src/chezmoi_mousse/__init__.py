"""Singleton to store output for each command"""

from dataclasses import dataclass, field


@dataclass
class ChezmoiOutput:
    command: str
    full_command: str = ""
    output: str = ""


@dataclass
class VerbOutput:
    data: ChezmoiOutput = field(
        default_factory=lambda: ChezmoiOutput("data --format=json")
    )
    dump_config: ChezmoiOutput = field(
        default_factory=lambda: ChezmoiOutput("dump-config --format=json")
    )
    cat_config: ChezmoiOutput = field(
        default_factory=lambda: ChezmoiOutput("cat-config")
    )
    doctor: ChezmoiOutput = field(
        default_factory=lambda: ChezmoiOutput("doctor")
    )
    ignored: ChezmoiOutput = field(
        default_factory=lambda: ChezmoiOutput("ignored")
    )
    managed: ChezmoiOutput = field(
        default_factory=lambda: ChezmoiOutput("managed --path-style=absolute")
    )
    unmanaged: ChezmoiOutput = field(
        default_factory=lambda: ChezmoiOutput(
            "unmanaged --path-style=absolute"
        )
    )
    status: ChezmoiOutput = field(
        default_factory=lambda: ChezmoiOutput("status --parent-dirs")
    )


CHEZMOI = VerbOutput()
