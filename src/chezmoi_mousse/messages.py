from dataclasses import dataclass
from pathlib import Path

from textual.message import Message

from chezmoi_mousse.id_typing import TabStr


@dataclass
class OperateDismissData:
    path: Path
    operation_executed: bool
    tab_name: TabStr


class OperateMessage(Message):
    def __init__(self, dismiss_data: OperateDismissData) -> None:
        self.dismiss_data: OperateDismissData = dismiss_data
        super().__init__()
