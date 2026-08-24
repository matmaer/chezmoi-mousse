from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message
from textual.widgets import Button

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.str_enums import TabLabel

    from .actionables import ReviewBtn


__all__ = [
    "CurrentNodeMsg",
    "DirContentBtnMsg",
    "DryRunBtnMsg",
    "ExitModalBtnMsg",
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
        is_unmanaged: bool,
    ) -> None:
        self.app_ids = app_ids
        self.path = path
        self.has_status = has_status
        self.is_unmanaged = is_unmanaged
        super().__init__()


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


class RefreshBtnMsg(Message):
    def __init__(self, button: Button) -> None:
        self.button = button
        super().__init__()


class ReviewBtnMsg(Message):
    def __init__(self, tab_label: TabLabel, review_btn: ReviewBtn) -> None:
        self.tab_label = tab_label
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
