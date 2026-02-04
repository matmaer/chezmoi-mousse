from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import IDS, AppType, SubTabLabel, Tcss

from .common.actionables import TabButtons
from .common.loggers import AppLog, CmdLog
from .common.views import GitLog

if TYPE_CHECKING:
    from textual.widgets import DataTable

__all__ = ["LogsTab"]


class LogsTab(Vertical, AppType):

    git_log_result: reactive["DataTable[str] | None"] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield TabButtons(
            ids=IDS.logs,
            buttons=(SubTabLabel.app_log, SubTabLabel.cmd_log, SubTabLabel.git_log),
        )
        with ContentSwitcher(initial=IDS.logs.logger.app):
            yield AppLog(ids=IDS.logs)
            yield CmdLog(ids=IDS.logs)
            yield GitLog(ids=IDS.logs)

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self.git_log = self.query_one(IDS.logs.container.git_log_q, GitLog)

    @on(Button.Pressed, Tcss.tab_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == SubTabLabel.app_log:
            self.switcher.current = IDS.logs.logger.app
        elif event.button.label == SubTabLabel.cmd_log:
            self.switcher.current = IDS.logs.logger.cmd
        elif event.button.label == SubTabLabel.git_log:
            self.switcher.current = IDS.logs.container.git_log

    def watch_git_log_result(self) -> None:
        if self.git_log_result is not None:
            self.git_log.remove_children()
            self.git_log.mount(self.git_log_result)
