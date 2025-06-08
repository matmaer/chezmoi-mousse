from pathlib import Path
from typing import Literal

type ApplyLabel = Literal["Apply"]
type ReAddLabel = Literal["Re-Add"]
type AddLabel = Literal["Add"]

# chezmoi status: added, deleted, modified, and no status
type StatusCode = Literal["A", "D", "M", "X"]

type TabLabel = Literal[ApplyLabel, ReAddLabel, AddLabel]

type ButtonLabel = Literal["Tree", "List", "Contents", "Diff", "Git-Log"]

type ButtonArea = Literal["TopLeft", "TopRight"]

type FilterName = Literal[
    "expand_all", "unchanged", "unwanted", "unmanaged_dirs"
]

type TreeName = Literal["ManagedTree", "ManTreeList", "DirTree"]

type StatusGroup = Literal[
    "apply_files", "apply_dirs", "re_add_files", "re_add_dirs"
]

type PathStatusDict = dict[StatusGroup, dict[Path, StatusCode]]
