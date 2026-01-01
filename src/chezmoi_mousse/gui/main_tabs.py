from enum import StrEnum
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, TabbedContent, TabPane

from chezmoi_mousse import IDS, AppState, AppType, LogStrings, TabName
from chezmoi_mousse.shared import (
    AppLog,
    CustomHeader,
    DebugLog,
    OperateLog,
    ReadCmdLog,
)

from .tabs.add_tab import AddTab, FilteredDirTree
from .tabs.apply_tab import ApplyTab
from .tabs.common.trees import ExpandedTree, ListTree, ManagedTree
from .tabs.config_tab import ConfigTab, ConfigTabSwitcher
from .tabs.help_tab import HelpTab
from .tabs.logs_tab import LogsTab
from .tabs.re_add_tab import ReAddTab

__all__ = ["MainScreen"]


class TabPanes(StrEnum):
    add_tab_label = "Add"
    apply_tab_label = "Apply"
    config_tab_label = "Config"
    help_tab_label = "Help"
    logs_tab_label = "Logs"
    re_add_tab_label = "Re-Add"


class MainScreen(Screen[None], AppType):

    destDir: Path | None = None

    def __init__(self) -> None:
        super().__init__()

        self.app_log: "AppLog"
        self.read_log: "ReadCmdLog"
        self.operate_log: "OperateLog"
        self.debug_log: "DebugLog"

    def compose(self) -> ComposeResult:
        yield CustomHeader(IDS.main_tabs)
        with TabbedContent():
            yield TabPane(
                TabPanes.apply_tab_label, ApplyTab(), id=TabName.apply
            )
            yield TabPane(
                TabPanes.re_add_tab_label, ReAddTab(), id=TabName.re_add
            )
            yield TabPane(TabPanes.add_tab_label, AddTab(), id=TabName.add)
            yield TabPane(TabPanes.logs_tab_label, LogsTab(), id=TabName.logs)
            yield TabPane(
                TabPanes.config_tab_label, ConfigTab(), id=TabName.config
            )
            yield TabPane(TabPanes.help_tab_label, HelpTab(), id=TabName.help)
        yield Footer(id=IDS.main_tabs.footer)

    async def on_mount(self) -> None:
        initialize_loggers_worker = self.initialize_loggers()
        await initialize_loggers_worker.wait()
        self.log_splash_log_commands()
        self.populate_apply_trees()
        self.populate_re_add_trees()
        self.update_config_tab()
        self.update_global_git_log()

    @work
    async def initialize_loggers(self) -> None:
        # Initialize App logger
        self.app_log = self.query_one(IDS.logs.logger.app_q, AppLog)
        self.app.cmd.app_log = self.app_log
        # Initialize Operate logger
        self.operate_log = self.query_one(
            IDS.logs.logger.operate_q, OperateLog
        )
        self.app.cmd.operate_log = self.operate_log
        self.app_log.success(LogStrings.operate_log_initialized)
        # Initialize ReadCmd logger
        self.read_cmd_log = self.query_one(IDS.logs.logger.read_q, ReadCmdLog)
        self.app.cmd.read_cmd_log = self.read_cmd_log
        self.app_log.success(LogStrings.read_log_initialized)
        # Initialize Debug logger if in dev mode
        if AppState.is_dev_mode():
            self.debug_log = self.query_one(IDS.logs.logger.debug_q, DebugLog)
            self.notify(LogStrings.dev_mode_enabled)

    def log_splash_log_commands(self) -> None:
        # Log SplashScreen and OperateScreen commands, if any.
        self.app_log.info("--- Commands executed in loading screen ---")
        if self.app.splash_data is None:
            self.notify("No loading screen data available.")
            return
        commands_to_log = self.app.splash_data.executed_commands
        if self.app.init_cmd_result is not None:
            self.operate_log.log_cmd_results(self.app.init_cmd_result)
            commands_to_log += [self.app.init_cmd_result]
        for cmd in commands_to_log:
            self.app_log.log_cmd_results(cmd)
            self.read_cmd_log.log_cmd_results(cmd)
        self.app_log.info("--- End of loading screen commands ---")

    def populate_apply_trees(self) -> None:
        self.screen.query_one(
            IDS.apply.tree.managed_q, ManagedTree
        ).dest_dir = self.destDir
        self.app_log.success("Apply tab managed tree populated.")
        self.screen.query_one(
            IDS.apply.tree.expanded_q, ExpandedTree
        ).dest_dir = self.destDir
        self.app_log.success("Apply tab expanded tree populated.")
        self.screen.query_one(IDS.apply.tree.list_q, ListTree).dest_dir = (
            self.destDir
        )
        self.app_log.success("Apply list populated.")

    def populate_re_add_trees(self) -> None:
        self.screen.query_one(
            IDS.re_add.tree.managed_q, ManagedTree
        ).dest_dir = self.destDir
        self.app_log.success("Re-Add tab managed tree populated.")
        self.screen.query_one(
            IDS.re_add.tree.expanded_q, ExpandedTree
        ).dest_dir = self.destDir
        self.app_log.success("Re-Add tab expanded tree populated.")
        self.screen.query_one(IDS.re_add.tree.list_q, ListTree).dest_dir = (
            self.destDir
        )
        self.app_log.success("Re-Add list populated.")

    def update_global_git_log(self) -> None:
        if self.app.splash_data is None:
            self.notify("No loading screen data available.", severity="error")
            return
        logs_tab = self.screen.query_exactly_one(LogsTab)
        setattr(logs_tab, "git_log_result", self.app.splash_data.git_log)

    def update_config_tab(self) -> None:
        config_tab_switcher = self.screen.query_one(
            IDS.config.switcher.config_tab_q, ConfigTabSwitcher
        )
        setattr(config_tab_switcher, "splash_data", self.app.splash_data)

    def handle_operate_result(self, _: None) -> None:
        if self.app.operate_cmd_result is None:
            self.notify("Operation cancelled.")
            return
        self.refresh_bindings()
        if (
            self.app.operate_cmd_result.exit_code == 0
            and self.app.changes_enabled
        ):
            self.notify("Operation completed successfully.")
        elif (
            self.app.operate_cmd_result.exit_code == 0
            and not self.app.changes_enabled
        ):
            self.notify(
                "Operation completed in dry-run mode, no changes were made."
            )
        else:
            self.notify(
                "The command ran with errors, see the Logs tab for more info.",
                severity="error",
            )
        add_dir_tree = self.query_one(IDS.add.tree.dir_tree_q, FilteredDirTree)
        add_dir_tree.reload()
        self.populate_apply_trees()
        self.populate_re_add_trees()
