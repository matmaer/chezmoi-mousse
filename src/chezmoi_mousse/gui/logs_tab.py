from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher, TabPane

from chezmoi_mousse import IDS, TabLabel

from .common.actionables import TabButtons
from .common.loggers import AppLog, CmdLog

__all__ = ["LogsTab"]


class LogsTab(TabPane):

    def compose(self) -> ComposeResult:
        with Vertical():
            yield TabButtons(IDS.logs, (TabLabel.cmd_log, TabLabel.app_log))
            with ContentSwitcher(initial=IDS.logs.logger.cmd):
                yield CmdLog()
                yield AppLog()

    def on_mount(self) -> None:
        self.tab_buttons = self.query_exactly_one(TabButtons)
        self.switcher = self.query_exactly_one(ContentSwitcher)

    @on(Button.Pressed)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == TabLabel.app_log:
            self.switcher.current = IDS.logs.logger.app
        elif event.button.label == TabLabel.cmd_log:
            self.switcher.current = IDS.logs.logger.cmd
