from typing import Literal

type ApplyLabel = Literal["Apply"]
type ReAddLabel = Literal["Re-Add"]
type AddLabel = Literal["Add"]

# chezmoi status: added, deleted, modified, and no status
type StatusCode = Literal["A", "D", "M", "X"]

type TabLabel = Literal[ApplyLabel, ReAddLabel, AddLabel]

type ButtonLabel = Literal["Tree", "List", "Contents", "Diff", "Git-Log"]

type ButtonArea = Literal["TopLeft", "TopRight"]

type FilterName = Literal["unchanged", "unwanted", "unmanaged_dirs"]

type TreeName = Literal["ManagedTree", "ManTreeList", "DirTree"]
