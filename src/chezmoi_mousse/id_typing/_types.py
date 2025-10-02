from pathlib import Path
from typing import TYPE_CHECKING, Any

__all__ = ["AppType", "Any", "ParsedJson", "PathDict"]

type ParsedJson = dict[str, Any]
type PathDict = dict[Path, str]

if TYPE_CHECKING:
    from chezmoi_mousse.gui import ChezmoiGUI


class AppType:
    """Type hint for self.app attributes in widgets and screens."""

    if TYPE_CHECKING:
        app: "ChezmoiGUI"
