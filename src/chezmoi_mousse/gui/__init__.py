from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

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
    # Should be Literal["A", "D", "M", "F", "X"] type
    status: str
    is_leaf: bool


@dataclass
class SplashReturnData:
    cat_config: str
    doctor: str
    dump_config: str
    ignored: str
    managed_dirs: str
    managed_files: str
    status_dirs: str
    status_files: str
    status_paths: str
    template_data: str
