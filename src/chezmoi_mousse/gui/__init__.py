from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

__all__ = ["AppType", "NodeData", "SplashReturnData"]

if TYPE_CHECKING:
    from chezmoi_mousse.gui.app import ChezmoiGUI


class AppType:
    """Type hint for self.app attributes in widgets and screens."""

    if TYPE_CHECKING:
        app: "ChezmoiGUI"


@dataclass
class NodeData:
    found: bool
    path: Path
    # chezmoi status codes processed: A, D, M, or a space
    # "node status" codes:
    #   X (no status but managed)
    #   F (fake for the root node)
    status: Literal["A", "D", "M", "F", "X"]
    is_dir: bool


@dataclass
class SplashReturnData:
    dir_status_lines: str
    doctor: str
    dump_config: str
    file_status_lines: str
    managed_dirs: str
    managed_files: str
