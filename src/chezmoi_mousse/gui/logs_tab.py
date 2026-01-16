from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import IDS, AppType, SubTabLabel, Tcss

from .common.actionables import TabButtons
from .common.loggers import AppLog, OperateLog, ReadCmdLog
from .common.views import GitLog

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResult

__all__ = ["LogsTab"]


class LogsTab(Vertical, AppType):

    git_log_result: reactive["CommandResult | None"] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield TabButtons(
            ids=IDS.logs,
            buttons=(
                SubTabLabel.app_log,
                SubTabLabel.read_log,
                SubTabLabel.operate_log,
                SubTabLabel.git_log,
            ),
        )
        with ContentSwitcher(initial=IDS.logs.logger.app):
            yield AppLog(ids=IDS.logs)
            yield ReadCmdLog(ids=IDS.logs)
            yield OperateLog(ids=IDS.logs)
            yield GitLog(ids=IDS.logs)

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self.git_log_table = self.query_one(IDS.logs.container.git_log_q, GitLog)

    @on(Button.Pressed, Tcss.tab_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == SubTabLabel.app_log:
            self.switcher.current = IDS.logs.logger.app
        elif event.button.label == SubTabLabel.read_log:
            self.switcher.current = IDS.logs.logger.read
        elif event.button.label == SubTabLabel.operate_log:
            self.switcher.current = IDS.logs.logger.operate
        elif event.button.label == SubTabLabel.git_log:
            self.switcher.current = self.git_log_table.id

    def watch_git_log_result(self) -> None:
        if self.git_log_result is None:
            return
        self.git_log_table.populate_datatable(self.git_log_result)
