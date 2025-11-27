from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import AppType, Tcss
from chezmoi_mousse.shared import (
    AppLog,
    DebugLog,
    GitLogGlobal,
    LogsTabButtons,
    OperateLog,
    ReadCmdLog,
)

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, CommandResult

__all__ = ["LogsTab"]


class BorderTitle(StrEnum):
    app_log = " App Log "
    debug_log = " Debug Log "
    git_log_global = " Global Git Log "
    read_cmd_log = " Read Commands Output Log "
    operate_log = " Operate Commands Output Log "


class LogsTab(Vertical, AppType):

    git_log_result: reactive["CommandResult | None"] = reactive(
        None, init=False
    )

    def __init__(self, ids: "AppIds") -> None:
        super().__init__()

        self.ids = ids

    def compose(self) -> ComposeResult:
        yield LogsTabButtons(ids=self.ids)
        with ContentSwitcher(
            id=self.ids.switcher.logs_tab,
            initial=self.ids.logger.app,
            classes=Tcss.border_title_top.name,
        ):
            yield AppLog(ids=self.ids)
            yield ReadCmdLog(ids=self.ids)
            yield OperateLog(ids=self.ids)
            yield GitLogGlobal(ids=self.ids)
            if self.app.dev_mode is True:
                yield DebugLog(ids=self.ids)

    def on_mount(self) -> None:
        switcher = self.query_one(
            self.ids.switcher.logs_tab_q, ContentSwitcher
        )
        switcher.border_title = BorderTitle.app_log

    @on(Button.Pressed, Tcss.tab_button)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(
            self.ids.switcher.logs_tab_q, ContentSwitcher
        )
        if event.button.id == self.ids.tab_btn.app_log:
            switcher.current = self.ids.logger.app
            switcher.border_title = BorderTitle.app_log
        elif event.button.id == self.ids.tab_btn.read_log:
            switcher.current = self.ids.logger.read
            switcher.border_title = BorderTitle.read_cmd_log
        elif event.button.id == self.ids.tab_btn.operate_log:
            switcher.current = self.ids.logger.operate
            switcher.border_title = BorderTitle.operate_log
        elif event.button.id == self.ids.tab_btn.git_log_global:
            switcher.border_title = BorderTitle.git_log_global
            switcher.current = self.ids.container.git_log_global
        elif (
            self.app.dev_mode is True
            and event.button.id == self.ids.tab_btn.debug_log
        ):
            switcher.current = self.ids.logger.debug
            switcher.border_title = BorderTitle.debug_log

    def watch_git_log_result(self) -> None:
        if self.git_log_result is None:
            return
        git_log_global = self.query_one(
            self.ids.container.git_log_global_q, GitLogGlobal
        )
        git_log_global.update_global_git_log(self.git_log_result)
