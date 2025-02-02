from dataclasses import dataclass, field


@dataclass
class ChezmoiIO:
    input: str = field(default_factory=str)
    stdout: str = field(default_factory=str)
    stderr: str = field(default_factory=str)


@dataclass
class ChezmoiOutput(ChezmoiIO):
    data: ChezmoiIO = field(default_factory=ChezmoiIO)
    dump_config: ChezmoiIO = field(default_factory=ChezmoiIO)
    cat_config: ChezmoiIO = field(default_factory=ChezmoiIO)
    doctor: ChezmoiIO = field(default_factory=ChezmoiIO)
    ignored: ChezmoiIO = field(default_factory=ChezmoiIO)
    managed: ChezmoiIO = field(default_factory=ChezmoiIO)
    status: ChezmoiIO = field(default_factory=ChezmoiIO)

chezmoi_io = ChezmoiOutput()
