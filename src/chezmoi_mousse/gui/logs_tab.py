from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import IDS, AppType, SubTabLabel, Tcss

from .common.actionables import TabButtons
from .common.loggers import AppLog, OperateLog, ReadCmdLog
from .common.views import GitLogDataTable

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResult

__all__ = ["LogsTab"]


class BorderTitle(StrEnum):
    app_log = " App Log "
    git_log_global = " Global Git Log "
    read_cmd_log = " Read Commands Output Log "
    operate_log = " Operate Commands Output Log "


class LogsTab(Vertical, AppType):

    git_log_result: reactive["CommandResult | None"] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield TabButtons(
            ids=IDS.logs,
            buttons=(
                SubTabLabel.app_log,
                SubTabLabel.read_log,
                SubTabLabel.operate_log,
                SubTabLabel.git_log_global,
            ),
        )
        with ContentSwitcher(
            initial=IDS.logs.logger.app, classes=Tcss.border_title_top
        ):
            yield AppLog(ids=IDS.logs)
            yield ReadCmdLog(ids=IDS.logs)
            yield OperateLog(ids=IDS.logs)
            yield GitLogDataTable(ids=IDS.logs)

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self.switcher.border_title = BorderTitle.app_log
        self.git_log_table = self.query_one(
            IDS.logs.datatable.git_log_q, GitLogDataTable
        )

    @on(Button.Pressed, Tcss.tab_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == SubTabLabel.app_log:
            self.switcher.current = IDS.logs.logger.app
            self.switcher.border_title = BorderTitle.app_log
        elif event.button.label == SubTabLabel.read_log:
            self.switcher.current = IDS.logs.logger.read
            self.switcher.border_title = BorderTitle.read_cmd_log
        elif event.button.label == SubTabLabel.operate_log:
            self.switcher.current = IDS.logs.logger.operate
            self.switcher.border_title = BorderTitle.operate_log
        elif event.button.label == SubTabLabel.git_log_global:
            self.switcher.border_title = BorderTitle.git_log_global
            self.switcher.current = self.git_log_table.id

    def watch_git_log_result(self) -> None:
        if self.git_log_result is None:
            return
        self.git_log_table.populate_datatable(self.git_log_result)
