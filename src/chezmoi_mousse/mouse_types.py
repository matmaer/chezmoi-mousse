from typing import Literal

# chezmoi status: added, deleted, modified, and no status
type StatusCode = Literal["A", "D", "M", "X"]

type TabLabel = Literal["Apply", "Re-Add", "Add"]

type ButtonLabel = Literal["Tree", "List", "Contents", "Diff", "Git-Log"]

type ButtonArea = Literal["TopLeft", "TopRight", "BottomRight"]

type FilterName = Literal["unchanged", "unwanted", "unmanaged_dirs"]

type TreeName = Literal["ManagedTree", "ManTreeList", "DirTree"]

type TabSide = Literal["Left", "Right"]
