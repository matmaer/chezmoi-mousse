from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds, InitCloneData, NodeData

    from .actionables import CloseButton, OpButton

__all__ = [
    "CloseButtonMsg",
    "CompletedOpMsg",
    "CurrentApplyNodeMsg",
    "CurrentReAddNodeMsg",
    "InitCloneCmdMsg",
    "OperateButtonMsg",
    "ProgressTextMsg",
]


class CloseButtonMsg(Message):
    def __init__(self, *, button: "CloseButton", ids: "AppIds") -> None:
        self.button = button
        self.ids = ids
        super().__init__()


class CompletedOpMsg(Message):
    def __init__(self, *, path_arg: "Path | None") -> None:
        self.path_arg = path_arg
        super().__init__()


class CurrentApplyNodeMsg(Message):
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()


class CurrentReAddNodeMsg(Message):
    # used to keep track in main screen to push the operate screen
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()


class InitCloneCmdMsg(Message):
    def __init__(self, init_clone_data: "InitCloneData") -> None:
        self.init_clone_data = init_clone_data
        super().__init__()


class OperateButtonMsg(Message):
    def __init__(self, *, button: "OpButton", ids: "AppIds") -> None:
        self.button = button
        self.ids = ids
        super().__init__()


class ProgressTextMsg(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()
