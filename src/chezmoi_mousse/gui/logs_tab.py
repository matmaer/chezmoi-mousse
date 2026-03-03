from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import IDS, AppType, SubTabLabel, Tcss

from .common.actionables import TabButtons
from .common.git_log import GitLog
from .common.loggers import AppLog, CmdLog

__all__ = ["LogsTab"]


class LogsTab(Vertical, AppType):

    def compose(self) -> ComposeResult:
        yield TabButtons(
            IDS.logs,
            buttons=(SubTabLabel.app_log, SubTabLabel.cmd_log, SubTabLabel.git_log),
        )
        with ContentSwitcher(initial=IDS.logs.logger.app):
            yield AppLog(IDS.logs)
            yield CmdLog(id=IDS.logs.logger.cmd, classes=Tcss.border_title_top)
            yield GitLog(IDS.logs)

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
