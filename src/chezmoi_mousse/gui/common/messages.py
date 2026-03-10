from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds

    from .actionables import OpButton

__all__ = [
    "ChangedRootPaths",
    "CurrentApplyNodeMsg",
    "CurrentReAddNodeMsg",
    "OperateButtonMsg",
    "ProgressTextMsg",
]


class ChangedRootPaths(Message):
    def __init__(self, paths: list[Path]) -> None:
        self.paths = paths
        super().__init__()


class CurrentApplyNodeMsg(Message):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__()


class CurrentReAddNodeMsg(Message):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__()


class OperateButtonMsg(Message):
    def __init__(self, ids: AppIds, *, button: OpButton) -> None:
        self.button: OpButton = button
        self.ids = ids
        super().__init__()


class ProgressTextMsg(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()
