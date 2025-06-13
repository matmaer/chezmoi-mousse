from typing import Literal

# Type aliases not to be imported or used directly
type OperationButtonLabel = Literal[
    "Add Directory",
    "Add File",
    "Apply Directory",
    "Apply File",
    "Re-Add Directory",
    "Re-Add File",
]
type TreeName = Literal["AddTree", "ExpandedTree", "FlatTree", "ManagedTree"]
type TabButtonLabel = Literal["Tree", "List", "Contents", "Diff", "Git-Log"]
type VerticalAreaName = Literal["Left", "Right"]
type SquareAreaName = Literal["TopLeft", "TopRight", "BottomRight"]

# Type aliases to be used instead of the above
type Area = Literal[VerticalAreaName, SquareAreaName]
type ButtonLabel = Literal[TabButtonLabel, OperationButtonLabel]
type ComponentName = Literal[TreeName, "PathView", "DiffView", "GitLog"]
type FilterName = Literal[
    "expand_all", "unchanged", "unwanted", "unmanaged_dirs"
]
type TabLabel = Literal["Apply", "Re-Add", "Add", "Doctor", "Diagram", "Log"]


# from chezmoi_mousse.mouse_types import (
#     Area,
#     ButtonLabel,
#     ComponentName,
#     FilterName,
#     TabLabel,
# )
