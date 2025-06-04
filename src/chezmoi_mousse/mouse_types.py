from pathlib import Path
from typing import Literal


type TabLabel = Literal["Apply", "Re-Add", "Add"]

type ButtonArea = Literal["TopLeft", "TopRight", "BottomRight"]

type ButtonLabel = Literal["Tree", "List", "Content", "Diff", "Git-Log"]

type DiffSpec = tuple[Path, str] | None
