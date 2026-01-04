from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import IDS, AppType, Tcss

from .common.actionables import LogsTabButtons
from .common.loggers import AppLog, OperateLog, ReadCmdLog
from .common.views import GitLogGlobal

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResult

__all__ = ["LogsTab"]


class BorderTitle(StrEnum):
    app_log = " App Log "
    git_log_global = " Global Git Log "
    read_cmd_log = " Read Commands Output Log "
    operate_log = " Operate Commands Output Log "


class LogsTab(Vertical, AppType):

    git_log_result: reactive["CommandResult | None"] = reactive(
        None, init=False
    )

    def compose(self) -> ComposeResult:
        yield LogsTabButtons(ids=IDS.logs)
        with ContentSwitcher(
            id=IDS.logs.switcher.logs_tab,
            initial=IDS.logs.logger.app,
            classes=Tcss.border_title_top,
        ):
            yield AppLog(ids=IDS.logs)
            yield ReadCmdLog(ids=IDS.logs)
            yield OperateLog(ids=IDS.logs)
            yield GitLogGlobal(ids=IDS.logs)

    def on_mount(self) -> None:
        switcher = self.query_one(
            IDS.logs.switcher.logs_tab_q, ContentSwitcher
        )
        switcher.border_title = BorderTitle.app_log

    @on(Button.Pressed, Tcss.tab_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(
            IDS.logs.switcher.logs_tab_q, ContentSwitcher
        )
        if event.button.id == IDS.logs.tab_btn.app_log:
            switcher.current = IDS.logs.logger.app
            switcher.border_title = BorderTitle.app_log
        elif event.button.id == IDS.logs.tab_btn.read_log:
            switcher.current = IDS.logs.logger.read
            switcher.border_title = BorderTitle.read_cmd_log
        elif event.button.id == IDS.logs.tab_btn.operate_log:
            switcher.current = IDS.logs.logger.operate
            switcher.border_title = BorderTitle.operate_log
        elif event.button.id == IDS.logs.tab_btn.git_log_global:
            switcher.border_title = BorderTitle.git_log_global
            switcher.current = IDS.logs.container.git_log_global

    def watch_git_log_result(self) -> None:
        if self.git_log_result is None:
            return
        git_log_global = self.query_one(
            IDS.logs.container.git_log_global_q, GitLogGlobal
        )
        git_log_global.update_global_git_log(self.git_log_result)
