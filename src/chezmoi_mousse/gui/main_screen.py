from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, TabbedContent, TabPane

from chezmoi_mousse import CMD, IDS, AppType, LogString, TabLabel, TabName

from .add_tab import AddTab
from .apply_tab import ApplyTab
from .common.loggers import AppLog, DebugLog
from .common.screen_header import CustomHeader
from .common.trees import ListTree, ManagedTree
from .config_tab import ConfigTab
from .help_tab import HelpTab
from .logs_tab import LogsTab
from .re_add_tab import ReAddTab

__all__ = ["MainScreen"]


class MainScreen(Screen[None], AppType):

    def compose(self) -> ComposeResult:
        yield CustomHeader()
        with TabbedContent():
            yield TabPane(TabLabel.apply_tab, ApplyTab(), id=TabName.apply)
            yield TabPane(TabLabel.re_add_tab, ReAddTab(), id=TabName.re_add)
            yield TabPane(TabLabel.add_tab, AddTab(), id=TabName.add)
            yield TabPane(TabLabel.logs_tab, LogsTab(), id=TabName.logs)
            yield TabPane(TabLabel.config_tab, ConfigTab(), id=TabName.config)
            yield TabPane(TabLabel.help_tab, HelpTab(), id=TabName.help)
            if self.app.dev_mode is True:
                from .debug_tab import DebugTab

                yield TabPane(TabLabel.debug_tab, DebugTab(), id=TabName.debug)

        yield Footer()

    def on_mount(self) -> None:
        # Initialize App logger
        self.app_log = self.query_one(IDS.logs.logger.app_q, AppLog)
        self.app_log.success(LogString.cmd_log_initialized)
        # Initialize Debug logger if in dev mode
        if self.app.dev_mode is True:
            self.debug_log = self.query_one(IDS.debug.logger.debug_q, DebugLog)
            self.app_log.success(LogString.dev_mode_enabled)
            self.notify(LogString.dev_mode_enabled)

        self._populate_apply_trees()
        self._populate_re_add_trees()
        self._set_config_screen_reactives()
        self.app.call_later(self._log_splash_log_commands)

    def _set_config_screen_reactives(self) -> None:
        config_tab = self.screen.query_exactly_one(ConfigTab)
        config_tab.command_results = CMD.cmd_results

    def _log_splash_log_commands(self) -> None:
        self.app_log.info("--- Commands executed in loading screen ---")
        commands_to_log = CMD.cmd_results.executed_commands
        for cmd in commands_to_log:
            self.app.log_cmd_result(cmd)
        self.app_log.info("--- End of loading screen commands ---")

    def _populate_apply_trees(self) -> None:
        self.screen.query_one(IDS.apply.tree.managed_q, ManagedTree).populate_tree()
        self.app_log.success("Apply tab managed tree populated.")
        self.screen.query_one(IDS.apply.tree.list_q, ListTree).populate_tree()
        self.app_log.success("Apply tab list tree populated.")

    @work
    async def _populate_re_add_trees(self) -> None:
        self.screen.query_one(IDS.re_add.tree.managed_q, ManagedTree).populate_tree()
        self.app_log.success("Re-Add tab managed tree populated.")
        self.screen.query_one(IDS.re_add.tree.list_q, ListTree).populate_tree()
        self.app_log.success("Re-Add tab list tree populated.")
