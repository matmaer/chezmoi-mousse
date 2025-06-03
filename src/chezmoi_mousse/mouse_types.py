from pathlib import Path
from typing import Literal, TypedDict


type TabLabel = Literal["Apply", "Re-Add", "Add"]

type ButtonArea = Literal["TopLeft", "TopRight", "BottomRight"]

type TopLeftButton = Literal["Tree", "List"]
type TopRightButton = Literal["Content", "Diff", "Git-Log"]


class TreeSpecDict(TypedDict, total=True):
    """Dictionary to pass for tree_spec, with required tab_label and tree_kind
    keys.

    Logic in TreeView depends on these.
    """

    # key has to be "tab_label", value is an ApplyReAddLabel Literal type alias
    tab_label: TabLabel
    # key has to be "tree_kind", value will be either "Tree" or "List"
    tree_kind: TopLeftButton


type TreeSpec = TreeSpecDict


class PathViewSpecDict(TypedDict, total=True):
    """Dictionary to pass for path_spec, with required path and tab_label keys.

    Logic in PathView depends on these.
    """

    # key has to be "path", value is a Path object
    path: Path
    # key has to be "tab_label", value is an ApplyReAddLabel Literal type alias
    tab_label: TabLabel


type PathViewSpec = dict[Literal["path"], Path] | None


class DiffSpecDict(TypedDict, total=True):
    """Dictionary to pass for diff_spec, with required path and tab_label keys
    and value types.

    Logic in DiffView depends on these.
    """

    # key has to be "path", value is a Path object
    path: Path
    # key has to be "tab_label", value is an ApplyReAddLabel Literal type alias
    tab_label: TabLabel


type DiffSpec = DiffSpecDict | None
