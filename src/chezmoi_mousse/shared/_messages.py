from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:

    from chezmoi_mousse import (
        NodeData,
        OperateBtn,
        ScreenName,
        TabName,
        WriteCmd,
    )

__all__ = [
    "CurrentAddNodeMsg",
    "CurrentApplyNodeMsg",
    "CurrentReAddNodeMsg",
    "CurrentInitCmdMsg",
    "OperateButtonMsg",
]

# messages used to keep track in main screen to push the operate screen with
# the correct data


class CurrentApplyNodeMsg(Message):
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()


class CurrentReAddNodeMsg(Message):
    # used to keep track in main screen to push the operate screen
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()


class CurrentAddNodeMsg(Message):
    # used to keep track in main screen to push the operate screen
    def __init__(self, node_data: "NodeData") -> None:
        self.node_data = node_data
        super().__init__()


class CurrentInitCmdMsg(Message):
    def __init__(
        self,
        https_arg: str | None = None,
        ssh_arg: str | None = None,
        guess_url_arg: str | None = None,
        guess_ssh_arg: str | None = None,
        https_cmd: "WriteCmd | None" = None,
        ssh_cmd: "WriteCmd | None" = None,
        guess_url_cmd: "WriteCmd | None" = None,
        guess_ssh_cmd: "WriteCmd | None" = None,
    ) -> None:
        self.https_arg: str | None = https_arg
        self.ssh_arg: str | None = ssh_arg
        self.guess_url_arg: str | None = guess_url_arg
        self.guess_ssh_arg: str | None = guess_ssh_arg
        self.https_cmd: "WriteCmd | None" = https_cmd
        self.ssh_cmd: "WriteCmd | None" = ssh_cmd
        self.guess_url_cmd: "WriteCmd | None" = guess_url_cmd
        self.guess_ssh_cmd: "WriteCmd | None" = guess_ssh_cmd
        super().__init__()


class OperateButtonMsg(Message):
    def __init__(
        self,
        *,
        btn_enum: "OperateBtn",
        label: "str",
        tooltip: "str",
        canvas_name: "TabName|ScreenName",
    ) -> None:
        self.btn_enum = btn_enum
        self.label = label
        self.tooltip = tooltip
        self.canvas_name = canvas_name
        super().__init__()
