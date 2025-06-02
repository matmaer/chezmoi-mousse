from pathlib import Path
from textual.reactive import reactive
from typing import Literal

TabModifyLabel = Literal["Apply", "ReAdd"]
TabOperateLabel = Literal[TabModifyLabel, "Add"]
TabLabel = Literal[TabOperateLabel, "Doctor", "Diagram", "Log"]
TreeViewButton = Literal["Tree", "List"]
PathViewButton = Literal["Content", "Diff"]
TabButton = Literal[TreeViewButton, PathViewButton, "Git-Log"]
ButtonArea = Literal["TopLeft", "TopRight", "BottomRight", "BottomLeft"]

DiffSpec = reactive[tuple[Path, TabModifyLabel]] | reactive[None]
