"""Expose dataclasses and classes from _id_classes.py and types from
_types.py."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from chezmoi_mousse.id_typing._id_classes import (
    Id,
    ScreenIds,
    Switches,
    TabIds,
)

__all__ = [
    "Any",
    "AppType",
    "NodeData",
    "ParsedJson",
    "PathDict",
    "SplashReturnData",
    # imports from id_classes.py
    "Id",
    "ScreenIds",
    "Switches",
    "TabIds",
]

type ParsedJson = dict[str, Any]
type PathDict = dict[Path, str]

if TYPE_CHECKING:
    from chezmoi_mousse.gui import ChezmoiGUI


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
    doctor: str
    dir_status_lines: str
    file_status_lines: str
    managed_dirs: str
    managed_files: str
