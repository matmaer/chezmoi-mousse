"""Expose dataclasses and classes from _id_classes.py and types from
_types.py."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from chezmoi_mousse.id_typing._id_classes import (
    Id,
    NodeData,
    ScreenIds,
    SplashReturnData,
    TabIds,
)

# from chezmoi_mousse.id_typing._types import Any, AppType, ParsedJson, PathDict

__all__ = [
    # imports from id_classes.py
    "Id",
    "NodeData",
    "ScreenIds",
    "SplashReturnData",
    "TabIds",
    # module types
    "Any",
    "AppType",
    "ParsedJson",
    "PathDict",
]

type ParsedJson = dict[str, Any]
type PathDict = dict[Path, str]

if TYPE_CHECKING:
    from chezmoi_mousse.gui import ChezmoiGUI


class AppType:
    """Type hint for self.app attributes in widgets and screens."""

    if TYPE_CHECKING:
        app: "ChezmoiGUI"
