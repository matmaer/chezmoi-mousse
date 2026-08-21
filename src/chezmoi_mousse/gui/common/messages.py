from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message
from textual.widgets import Button

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.named_tuples import CommandResult

    from .actionables import ReviewBtn


__all__ = [
    "CurrentNodeMsg",
    "DirContentBtnMsg",
    "DryRunBtnMsg",
    "ExitModalBtnMsg",
    "LogCmdResultMsg",
    "RefreshBtnMsg",
    "ReviewBtnMsg",
    "RunBtnMsg",
    "TabBtnMsg",
]


class CurrentNodeMsg(Message):
    def __init__(
        self,
        *,
        app_ids: AppIds,
        path: Path,
        has_status: bool,
        dest_dir: Path,
        is_unmanaged: bool,
    ) -> None:
        self.app_ids = app_ids
        self.path = path
        self.has_status = has_status
        self._dest_dir = dest_dir
        self.is_unmanaged = is_unmanaged
        super().__init__()

    @property
    def border_path(self) -> str:
        rel_path_border = f" {self.path.relative_to(self._dest_dir)} "
        return rel_path_border if self.path != self._dest_dir else f" {self._dest_dir} "


class DirContentBtnMsg(Message):
    def __init__(self, button: Button) -> None:
        self.button = button
        super().__init__()


class DryRunBtnMsg(Message):
    def __init__(self, button: Button) -> None:
        self.button = button
        super().__init__()


class ExitModalBtnMsg(Message):
    def __init__(self, button: Button) -> None:
        self.button = button
        super().__init__()


class LogCmdResultMsg(Message):
    def __init__(self, cmd_result: list[CommandResult]) -> None:
        self.cmd_result = cmd_result
        super().__init__()


class RefreshBtnMsg(Message):
    def __init__(self, button: Button) -> None:
        self.button = button
        super().__init__()


class ReviewBtnMsg(Message):
    def __init__(self, review_btn: ReviewBtn) -> None:
        self.review_button: ReviewBtn = review_btn
        super().__init__()


class RunBtnMsg(Message):
    def __init__(self, button: Button) -> None:
        self.button = button
        super().__init__()


class TabBtnMsg(Message):
    def __init__(self, button: Button) -> None:
        self.button = button
        super().__init__()
