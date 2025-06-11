from typing import Literal

# first define TreeName, as it is used in other type aliases
type TreeName = Literal["TreeTree", "TreeList", "FilteredDirTree"]
# sorted alphabetically:
type ButtonArea = Literal["TopLeft", "TopRight", "BottomRight"]
type ButtonLabel = Literal["Tree", "List", "Contents", "Diff", "Git-Log"]
type ComponentName = Literal[TreeName, "PathView", "DiffView", "GitLog"]
type FilterName = Literal["unchanged", "unwanted", "unmanaged_dirs"]
type StatusCode = Literal["A", "D", "M", "X"]
type TabLabel = Literal["Apply", "Re-Add", "Add"]
type TabSide = Literal["Left", "Right"]
