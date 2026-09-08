from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.containers import Vertical
from textual.widgets import ContentSwitcher

from chezmoi_mousse.gui.common.actionables import OperateBtnGroup, TabBtn, TabButtons
from chezmoi_mousse.gui.common.contents import ContentsView
from chezmoi_mousse.gui.common.diffs import DiffView
from chezmoi_mousse.gui.common.git_log import GitLogView
from chezmoi_mousse.gui.common.messages import TabBtnMsg
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from chezmoi_mousse.app_ids import AppIds

__all__ = ["ViewSwitcher"]


class ViewSwitcher(Vertical):
    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=ids.container.right_side)
        self.ids = ids
        self.run_label = (
            BtnLabel.apply_review
            if self.ids.tab_label == BtnLabel.apply
            else BtnLabel.re_add_review
        )

    def compose(self) -> ComposeResult:
        yield TabButtons(
            app_ids=self.ids,
            labels=(BtnLabel.diff, BtnLabel.contents, BtnLabel.git_log),
        )
        with ContentSwitcher(initial=self.ids.container.diff):
            yield DiffView(self.ids)
            yield ContentsView(self.ids)
            yield GitLogView(self.ids)
        yield OperateBtnGroup(
            app_ids=self.ids,
            labels=(
                self.run_label,
                BtnLabel.forget_review,
                BtnLabel.destroy_review,
            ),
        )

    def on_mount(self) -> None:
        self.content_switcher = self.query_exactly_one(ContentSwitcher)

    @on(TabBtnMsg)
    def switch_view(self, msg: TabBtnMsg) -> None:
        if isinstance(msg.button, TabBtn):
            msg.stop()
            if msg.button.label == BtnLabel.contents:
                self.content_switcher.current = self.ids.container.contents
            elif msg.button.label == BtnLabel.diff:
                self.content_switcher.current = self.ids.container.diff
            elif msg.button.label == BtnLabel.git_log:
                self.content_switcher.current = self.ids.container.git_log
