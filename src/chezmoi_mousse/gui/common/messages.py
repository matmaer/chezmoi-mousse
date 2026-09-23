from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from pathlib import Path

    from textual.widgets import Button

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.named_tuples import CommandResult
    from chezmoi_mousse.str_enums import BtnLabel


__all__ = [
    "CommandResultMsg",
    "DirContentBtnMsg",
    "FlatBtnMsg",
    "OperateBtnMsg",
    "ShowTreeQidMsg",
    "TabBtnMsg",
]


class CommandResultMsg(Message):
    def __init__(self, results: CommandResult) -> None:
        self.cmd_result: CommandResult = results
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


class OperateBtnMsg(Message):
    def __init__(self, button: Button, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.button = button
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__()


class ShowTreeQidMsg(Message):
    def __init__(self, tree_qid: str) -> None:
        self.tree_qid = tree_qid
        super().__init__()


class TabBtnMsg(Message):
    def __init__(self, button: Button, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.button = button
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__()
