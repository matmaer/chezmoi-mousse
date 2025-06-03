from pathlib import Path
from typing import Literal

ModifyTabLabel = Literal["Apply", "ReAdd"]
OperateTabLabel = Literal[ModifyTabLabel, "Add"]
AnyTabLabel = Literal[OperateTabLabel, "Doctor", "Diagram", "Log"]
TreeViewButton = Literal["Tree", "List"]
PathViewButton = Literal["Content", "Diff"]
AnyTabButton = Literal[TreeViewButton, PathViewButton, "Git-Log"]
ButtonArea = Literal["TopLeft", "TopRight", "BottomRight", "BottomLeft"]

DiffSpec = tuple[Path, ModifyTabLabel] | None
