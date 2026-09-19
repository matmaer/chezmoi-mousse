from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from pathlib import Path

    from textual.widgets import Button

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.common.managed_trees import NodeMap
    from chezmoi_mousse.named_tuples import CommandResult, SwitchStates
    from chezmoi_mousse.str_enums import BtnLabel


__all__ = [
    "AppLogMsg",
    "CommandResultMsg",
    "CurrentNodeMsg",
    "DirContentBtnMsg",
    "FlatBtnMsg",
    "OperateBtnMsg",
    "RefreshBtnMsg",
    "TabBtnMsg",
]


class AppLogMsg(Message):
    def __init__(self, log_line: str) -> None:
        self.log_line = log_line
        super().__init__()


class CommandResultMsg(Message):
    def __init__(self, results: CommandResult) -> None:
        self.cmd_result: CommandResult = results
        super().__init__()


class CurrentNodeMsg(Message):
    def __init__(
        self,
        *,
        app_ids: AppIds,
        path: Path,
        has_status: bool,
        is_dest_dir: bool,
        is_unmanaged: bool,
    ) -> None:
        self.app_ids = app_ids
        self.path = path
        self.has_status = has_status
        self.is_dest_dir = is_dest_dir
        self.is_unmanaged = is_unmanaged
        super().__init__()


class DirContentBtnMsg(Message):
    def __init__(
        self, button: Button, app_ids: AppIds, btn_label: BtnLabel, *, path: Path
    ) -> None:
        self.button = button
        self.app_ids = app_ids
        self.btn_label = btn_label
        self.path = path
        super().__init__()


class FlatBtnMsg(Message):
    def __init__(self, button: Button, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.app_ids = app_ids
        self.btn_label = btn_label
        self.button = button
        super().__init__()


class RefreshBtnMsg(Message):
    def __init__(self, button: Button, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.button = button
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__()


class OperateBtnMsg(Message):
    def __init__(self, button: Button, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.button = button
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__()


class SwitchGroupMsg(Message):
    def __init__(self, switch_states: SwitchStates) -> None:
        self.switch_states = switch_states
        super().__init__()


class TabBtnMsg(Message):
    def __init__(self, button: Button, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.button = button
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__()


class TreeStateMsg(Message):
    """
    Posted each time the tree catches one of the following events:
    - Tree.NodeCollapsed
    - Tree.NodeExpanded
    - Tree.NodeSelected
    """

    def __init__(self, path: Path, tree_name: str, node_map: NodeMap) -> None:
        self.path = path
        self.tree_name = tree_name
        self.node_map = node_map
        super().__init__()
