from typing import Literal

# first define TreeName, as it is used in other type aliases
type TreeName = Literal[
    "ExpandedTree", "ManagedTree", "FlatTree", "FilteredDirTree"
]
# sorted alphabetically:
type ButtonArea = Literal["TopLeft", "TopRight", "BottomRight"]
type ButtonLabel = Literal["Tree", "List", "Contents", "Diff", "Git-Log"]
type ComponentName = Literal[TreeName, "PathView", "DiffView", "GitLog"]
type FilterName = Literal[
    "expand_all", "unchanged", "unwanted", "unmanaged_dirs"
]
type FilterGroups = Literal["dir-tree-filters", "tree-filters", "list-filters"]
type StatusCode = Literal["A", "D", "M", "X"]
type TabLabel = Literal["Apply", "Re-Add", "Add", "Doctor", "Diagram", "Log"]
type TabSide = Literal["Left", "Right"]
