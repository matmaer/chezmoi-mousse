from enum import StrEnum

from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, TabbedContent, TabPane

from chezmoi_mousse import CMD, IDS, PARSED, AppType, LogString, ReadCmd, TabName

from .add_tab import AddTab
from .apply_tab import ApplyTab
from .common.git_log import GitLogTable
from .common.loggers import AppLog, DebugLog
from .common.screen_header import CustomHeader
from .common.trees import ListTree, ManagedTree
from .config_tab import ConfigTab
from .help_tab import HelpTab
from .logs_tab import LogsTab
from .re_add_tab import ReAddTab

__all__ = ["MainScreen"]


class TabPanes(StrEnum):
    add_tab_label = "Add"
    apply_tab_label = "Apply"
    config_tab_label = "Config"
    debug_tab_label = "Debug"
    help_tab_label = "Help"
    logs_tab_label = "Logs"
    re_add_tab_label = "Re-Add"


class MainScreen(Screen[None], AppType):

    def compose(self) -> ComposeResult:
        yield CustomHeader()
        with TabbedContent():
            yield TabPane(TabPanes.apply_tab_label, ApplyTab(), id=TabName.apply)
            yield TabPane(TabPanes.re_add_tab_label, ReAddTab(), id=TabName.re_add)
            yield TabPane(TabPanes.add_tab_label, AddTab(), id=TabName.add)
            yield TabPane(TabPanes.logs_tab_label, LogsTab(), id=TabName.logs)
            yield TabPane(TabPanes.config_tab_label, ConfigTab(), id=TabName.config)
            yield TabPane(TabPanes.help_tab_label, HelpTab(), id=TabName.help)
            if self.app.dev_mode is True:
                from .debug_tab import DebugTab

                yield TabPane(TabPanes.debug_tab_label, DebugTab(), id=TabName.debug)

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
        self._populate_global_git_log()
        self._set_config_screen_reactives()
        self.app.call_later(self._log_splash_log_commands)

    def _set_config_screen_reactives(self) -> None:
        config_tab = self.screen.query_exactly_one(ConfigTab)
        config_tab.command_results = PARSED.cmd_results

    def _log_splash_log_commands(self) -> None:
        self.app_log.info("--- Commands executed in loading screen ---")
        commands_to_log = PARSED.cmd_results.executed_commands
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

    def _populate_global_git_log(self) -> None:
        logs_tab = self.screen.query_exactly_one(LogsTab)
        logs_tab.git_log_result = GitLogTable(CMD.read(ReadCmd.git_log, path_arg=None))
