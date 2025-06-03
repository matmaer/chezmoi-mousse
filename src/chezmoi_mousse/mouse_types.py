from pathlib import Path
from typing import Literal, TypedDict

# Buttons available within a tab, so far used in Apply, Re-Add, Add tabs
type TreeButtonLabel = Literal["Tree"]
type ListButtonLabel = Literal["List"]
type ContentButtonLabel = Literal["Content"]
type DiffButtonLabel = Literal["Diff"]
type GitLogButtonLabel = Literal["Git-Log"]

# Current tab names depending on type checking aliases.
type ApplyTabLabel = Literal["Apply"]
type ReAddTabLabel = Literal["Re-Add"]
type AddTabLabel = Literal["Add"]

# Current button areas containing xxxButtonLabel aliases
type TopLeftArea = Literal["TopLeft"]
type TopRightArea = Literal["TopRight"]
type BottomRightArea = Literal["BottomRight"]

###############################################
# Aliases composed from literal type aliases. #
###############################################

type ApplyReAddLabel = Literal[ApplyTabLabel, ReAddTabLabel]
type ApplyReAddAddLabel = Literal[ApplyTabLabel, ReAddTabLabel, AddTabLabel]

type ButtonArea = Literal[TopLeftArea, TopRightArea, BottomRightArea]

type TreeViewButton = Literal[TreeButtonLabel, ListButtonLabel]
type PathViewButton = Literal[
    ContentButtonLabel, DiffButtonLabel, GitLogButtonLabel
]

########################################
# Type aliases used for reactive vars. #
########################################


class TreeSpecDict(TypedDict, total=True):
    """Dictionary to pass for tree_spec, with required tab_label and tree_kind
    keys.

    Logic in TreeView depends on these.
    """

    # key has to be "tab_label", value is an ApplyReAddLabel Literal type alias
    tab_label: ApplyReAddLabel
    # key has to be "tree_kind", value will be either "Tree" or "List"
    tree_kind: TreeViewButton


type TreeSpec = dict[Literal["tab_label"], ApplyReAddLabel] | None


class PathViewSpecDict(TypedDict, total=True):
    """Dictionary to pass for path_spec, with required path and tab_label keys.

    Logic in PathView depends on these.
    """

    # key has to be "path", value is a Path object
    path: Path
    # key has to be "tab_label", value is an ApplyReAddLabel Literal type alias
    tab_label: ApplyReAddLabel


type PathViewSpec = dict[Literal["path"], Path] | None


class DiffSpecDict(TypedDict, total=True):
    """Dictionary to pass for diff_spec, with required path and tab_label keys
    and value types.

    Logic in DiffView depends on these.
    """

    # key has to be "path", value is a Path object
    path: Path
    # key has to be "tab_label", value is an ApplyReAddLabel Literal type alias
    tab_label: ApplyReAddLabel


type DiffSpec = DiffSpecDict | None
