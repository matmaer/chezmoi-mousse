from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.containers import (
    Vertical,
)
from textual.widgets import (
    ContentSwitcher,
    TabPane,
)

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.loggers import AppLog, CmdLog
from chezmoi_mousse.gui.common.messages import TabBtnMsg
from chezmoi_mousse.str_enums import (
    BtnLabel,
)

from .common.actionables import (
    TabButtons,
)

if TYPE_CHECKING:
    from textual.app import ComposeResult


__all__ = ["LogsTab"]


class LogsTab(TabPane):
    def __init__(self) -> None:
        super().__init__(id=BtnLabel.logs.pane_id, title=BtnLabel.logs)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield TabButtons(
                app_ids=store.logs_ids, labels=(BtnLabel.cmd_log, BtnLabel.app_log)
            )
            with ContentSwitcher(initial=store.logs_ids.container.cmd_log):
                yield CmdLog()
                yield AppLog()

    @on(TabBtnMsg)
    def switch_content(self, msg: TabBtnMsg) -> None:
        msg.stop()
        switcher = self.query_exactly_one(ContentSwitcher)
        if msg.button.label == BtnLabel.app_log:
            switcher.current = store.logs_ids.richlog.app
        elif msg.button.label == BtnLabel.cmd_log:
            switcher.current = store.logs_ids.container.cmd_log
