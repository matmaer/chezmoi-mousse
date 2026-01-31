from enum import StrEnum

from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, TabbedContent, TabPane

from chezmoi_mousse import IDS, AppType, LogString, TabName

from .add_tab import AddTab
from .apply_tab import ApplyTab
from .common.loggers import AppLog, CmdLog
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

    def __init__(self) -> None:
        super().__init__()
        self.app_log: "AppLog"
        self.cmd_log: "CmdLog"

    def compose(self) -> ComposeResult:
        yield CustomHeader(IDS.main_tabs)
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

        yield Footer(id=IDS.main_tabs.footer)

    def on_mount(self) -> None:
        # Initialize App logger
        self.app_log = self.query_one(IDS.logs.logger.app_q, AppLog)
        self.app.cmd.app_log = self.app_log
        # Initialize chezmoi commands logger
        self.cmd_log = self.query_one(IDS.logs.logger.cmd_q, CmdLog)
        self.app.cmd.cmd_log = self.cmd_log
        self.app_log.success(LogString.cmd_log_initialized)
        # Initialize Debug logger if in dev mode
        if self.app.dev_mode is True:
            from .common.loggers import DebugLog

            self.debug_log = self.query_one(IDS.debug.logger.debug_q, DebugLog)
            self.notify(LogString.dev_mode_enabled)
        # Workers
        self.populate_apply_trees()
        self.populate_re_add_trees()
        self.log_splash_log_commands()
        self.populate_global_git_log()

    @work
    async def log_splash_log_commands(self) -> None:
        # Log SplashScreen and OperateScreen commands, if any.
        self.app_log.info("--- Commands executed in loading screen ---")
        commands_to_log = self.app.cmd_results.executed_commands
        if self.app.init_cmd_result is not None:
            self.cmd_log.log_cmd_results(self.app.init_cmd_result)
            commands_to_log += [self.app.init_cmd_result]
        for cmd in commands_to_log:
            self.app_log.log_cmd_results(cmd)
            self.cmd_log.log_cmd_results(cmd)
        self.app_log.info("--- End of loading screen commands ---")

    @work
    async def populate_apply_trees(self) -> None:
        self.screen.query_one(IDS.apply.tree.managed_q, ManagedTree).populate_dest_dir()
        self.app_log.success("Apply tab managed tree populated.")
        self.screen.query_one(IDS.apply.tree.list_q, ListTree).populate_dest_dir()
        self.app_log.success("Apply tab list tree populated.")

    @work
    async def populate_re_add_trees(self) -> None:
        self.screen.query_one(
            IDS.re_add.tree.managed_q, ManagedTree
        ).populate_dest_dir()
        self.app_log.success("Re-Add tab managed tree populated.")
        self.screen.query_one(IDS.re_add.tree.list_q, ListTree).populate_dest_dir()
        self.app_log.success("Re-Add tab list tree populated.")

    @work
    async def populate_global_git_log(self) -> None:
        if self.app.paths is None:
            return
        logs_tab = self.screen.query_exactly_one(LogsTab)
        logs_tab.git_log_result = self.app.paths.global_git_log_table
