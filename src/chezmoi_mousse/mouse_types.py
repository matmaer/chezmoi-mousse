from pathlib import Path
from typing import Literal

type ApplyLabel = Literal["Apply"]
type ReAddLabel = Literal["Re-Add"]
type AddLabel = Literal["Add"]

type TabLabel = Literal[ApplyLabel, ReAddLabel, AddLabel]

type ButtonLabel = Literal["Tree", "List", "Content", "Diff", "Git-Log"]

type DiffSpec = tuple[Path, str] | None
