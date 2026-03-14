from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import CMD, IDS, AppType, BorderTitle, TabLabel

from .common.actionables import TabButtons
from .common.git_log import GitLogView
from .common.loggers import AppLog, CmdLog

__all__ = ["LogsTab"]


class LogsTab(Vertical, AppType):

    def compose(self) -> ComposeResult:
        yield TabButtons((TabLabel.app_log, TabLabel.cmd_log, TabLabel.git_log))
        with ContentSwitcher(initial=IDS.logs.logger.app):
            yield AppLog()
            yield CmdLog()
            yield GitLogView(IDS.logs)

    def on_mount(self) -> None:
        self.tab_buttons = self.query_exactly_one(TabButtons)
        self.tab_buttons.border_subtitle = BorderTitle.app_log
        self.switcher = self.query_exactly_one(ContentSwitcher)
        self.git_log = self.query_one(IDS.logs.container.git_log_q, GitLogView)
        self.git_log.show_path = CMD.cache.dest_dir

    @on(Button.Pressed)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == TabLabel.app_log:
            self.switcher.current = IDS.logs.logger.app
            self.tab_buttons.border_subtitle = BorderTitle.app_log
        elif event.button.label == TabLabel.cmd_log:
            self.switcher.current = IDS.logs.logger.cmd
            self.tab_buttons.border_subtitle = BorderTitle.cmd_log
        elif event.button.label == TabLabel.git_log:
            self.switcher.current = IDS.logs.container.git_log
            self.tab_buttons.border_subtitle = BorderTitle.global_git_log
