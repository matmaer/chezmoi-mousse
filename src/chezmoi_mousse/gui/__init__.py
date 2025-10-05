from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.gui._id_classes import Id, ScreenIds, Switches, TabIds

__all__ = [
    "AppType",
    "Id",
    "NodeData",
    "ScreenIds",
    "SplashReturnData",
    "Switches",
    "TabIds",
]

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
    status: str
    is_dir: bool


@dataclass
class SplashReturnData:
    dir_status_lines: str
    doctor: str
    dump_config: str
    file_status_lines: str
    managed_dirs: str
    managed_files: str
