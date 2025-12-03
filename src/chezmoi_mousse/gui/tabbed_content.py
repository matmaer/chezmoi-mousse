from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, TabbedContent, TabPane

from chezmoi_mousse import (
    AppType,
    LogText,
    OperateBtn,
    OperateData,
    TabName,
    Tcss,
)
from chezmoi_mousse.shared import (
    AppLog,
    CurrentAddNodeMsg,
    CurrentApplyNodeMsg,
    CurrentReAddNodeMsg,
    CustomHeader,
    DebugLog,
    OperateLog,
    ReadCmdLog,
)

from .operate import OperateScreen
from .tabs.add_tab import AddTab, FilteredDirTree
from .tabs.apply_tab import ApplyTab
from .tabs.common.trees import ExpandedTree, ListTree, ManagedTree
from .tabs.config_tab import ConfigTab, ConfigTabSwitcher
from .tabs.help_tab import HelpTab
from .tabs.logs_tab import LogsTab
from .tabs.re_add_tab import ReAddTab

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, DirTreeNodeData, NodeData, SplashData

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

    def __init__(
        self,
        *,
        ids: "AppIds",
        splash_data: "SplashData",
        operate_data: "OperateData | None" = None,
    ) -> None:
        self.app_log: "AppLog"
        self.read_log: "ReadCmdLog"
        self.operate_log: "OperateLog"
        self.debug_log: "DebugLog"
        super().__init__()

        self.ids = ids
        self.splash_data = splash_data
        self.operate_data = operate_data

        self.current_add_node: "DirTreeNodeData | None" = None
        self.current_apply_node: "NodeData | None" = None
        self.current_re_add_node: "NodeData | None" = None

    def compose(self) -> ComposeResult:
        yield CustomHeader(ids=self.ids)
        with TabbedContent():
            yield TabPane(
                TabPanes.apply_tab_label,
                ApplyTab(ids=self.app.tab_ids.apply),
                id=TabName.apply.name,
            )
            yield TabPane(
                TabPanes.re_add_tab_label,
                ReAddTab(ids=self.app.tab_ids.re_add),
                id=TabName.re_add,
            )
            yield TabPane(
                TabPanes.add_tab_label,
                AddTab(ids=self.app.tab_ids.add),
                id=TabName.add,
            )
            yield TabPane(
                TabPanes.logs_tab_label,
                LogsTab(ids=self.app.tab_ids.logs),
                id=TabName.logs,
            )
            yield TabPane(
                TabPanes.config_tab_label,
                ConfigTab(ids=self.app.tab_ids.config),
                id=TabName.config,
            )
            yield TabPane(
                TabPanes.help_tab_label,
                HelpTab(ids=self.app.tab_ids.help),
                id=TabName.help,
            )
        yield Footer(id=self.ids.footer)

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
        self.app_log = self.query_one(
            self.app.tab_ids.logs.logger.app_q, AppLog
        )
        self.app.chezmoi.app_log = self.app_log
        self.app_log.ready_to_run(LogText.app_log_initialized)
        if self.app.chezmoi_found:
            self.app_log.success(LogText.chezmoi_found)
        else:
            self.notify(LogText.chezmoi_not_found, severity="error")
        # Initialize Operate logger
        self.operate_log = self.query_one(
            self.app.tab_ids.logs.logger.operate_q, OperateLog
        )
        self.app.chezmoi.operate_log = self.operate_log
        self.app_log.success(LogText.operate_log_initialized)
        self.operate_log.ready_to_run(LogText.operate_log_initialized)
        # Initialize ReadCmd logger
        self.read_cmd_log = self.query_one(
            self.app.tab_ids.logs.logger.read_q, ReadCmdLog
        )
        self.app.chezmoi.read_cmd_log = self.read_cmd_log
        self.app_log.success(LogText.read_log_initialized)
        # Initialize Debug logger if in dev mode
        if self.app.dev_mode:
            self.debug_log = self.query_one(
                self.app.tab_ids.logs.logger.debug_q, DebugLog
            )
            self.app.chezmoi.debug_log = self.debug_log
            self.app_log.success(LogText.debug_log_initialized)
            self.debug_log.ready_to_run(LogText.debug_log_initialized)
            self.notify(LogText.dev_mode_enabled, severity="information")

    def log_splash_log_commands(self) -> None:
        # Log SplashScreen and OperateScreen commands, if any.
        self.app_log.info("--- Commands executed in loading screen ---")
        commands_to_log = self.splash_data.executed_commands
        if (
            self.operate_data is not None
            and self.operate_data.command_result is not None
        ):
            commands_to_log += [self.operate_data.command_result]
        for cmd in commands_to_log:
            self.app_log.log_cmd_results(cmd)
            self.read_cmd_log.log_cmd_results(cmd)
        self.app_log.info("--- End of loading screen commands ---")

    def populate_apply_trees(self) -> None:
        self.app_log.info("Updating managed paths")
        self.app.chezmoi.update_managed_paths()
        managed_tree = self.screen.query_one(
            self.app.tab_ids.apply.tree.managed_q, ManagedTree
        )
        expanded_tree = self.screen.query_one(
            self.app.tab_ids.apply.tree.expanded_q, ExpandedTree
        )
        list_tree = self.screen.query_one(
            self.app.tab_ids.apply.tree.list_q, ListTree
        )
        managed_tree.populate_tree()
        self.app_log.success("Apply tab managed tree populated.")
        expanded_tree.populate_tree()
        self.app_log.success("Apply tab expanded tree populated.")
        list_tree.populate_tree()
        self.app_log.success("Apply list populated.")

    def populate_re_add_trees(self) -> None:
        managed_tree = self.screen.query_one(
            self.app.tab_ids.re_add.tree.managed_q, ManagedTree
        )
        expanded_tree = self.screen.query_one(
            self.app.tab_ids.re_add.tree.expanded_q, ExpandedTree
        )
        list_tree = self.screen.query_one(
            self.app.tab_ids.re_add.tree.list_q, ListTree
        )
        managed_tree.populate_tree()
        self.app_log.success("Re-Add tab managed tree populated.")
        expanded_tree.populate_tree()
        self.app_log.success("Re-Add tab expanded tree populated.")
        list_tree.populate_tree()
        self.app_log.success("Re-Add list populated.")

    def update_global_git_log(self) -> None:
        logs_tab = self.screen.query_exactly_one(LogsTab)
        logs_tab.git_log_result = self.splash_data.git_log

    def update_config_tab(self) -> None:
        config_tab_switcher = self.screen.query_one(
            self.app.tab_ids.config.switcher.config_tab_q, ConfigTabSwitcher
        )
        setattr(config_tab_switcher, "splash_data", self.splash_data)

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def push_operate_screen(self, event: Button.Pressed) -> None:
        button_enum = OperateBtn.from_label(str(event.button.label))
        current_tab = self.query_exactly_one(TabbedContent).active
        if (
            self.current_add_node is not None
            and button_enum in (OperateBtn.add_file, OperateBtn.add_dir)
            and current_tab == TabName.add
        ):
            operate_screen_data = OperateData(
                operate_btn=button_enum, node_data=self.current_add_node
            )
            self.app.push_screen(
                OperateScreen(
                    ids=self.app.screen_ids.operate,
                    operate_data=operate_screen_data,
                ),
                callback=self.handle_operate_result,
            )
        elif (
            self.current_apply_node is not None
            and button_enum
            in (
                OperateBtn.apply_path,
                OperateBtn.destroy_path,
                OperateBtn.forget_path,
            )
            and current_tab == TabName.apply.name
        ):
            operate_screen_data = OperateData(
                operate_btn=button_enum, node_data=self.current_apply_node
            )
            self.app.push_screen(
                OperateScreen(
                    ids=self.app.screen_ids.operate,
                    operate_data=operate_screen_data,
                ),
                callback=self.handle_operate_result,
            )

        elif (
            self.current_re_add_node is not None
            and button_enum
            in (
                OperateBtn.re_add_path,
                OperateBtn.destroy_path,
                OperateBtn.forget_path,
            )
            and current_tab == TabName.re_add
        ):
            operate_screen_data = OperateData(
                operate_btn=button_enum, node_data=self.current_re_add_node
            )
            self.app.push_screen(
                OperateScreen(
                    ids=self.app.screen_ids.operate,
                    operate_data=operate_screen_data,
                ),
                callback=self.handle_operate_result,
            )
        else:
            self.notify("No current node available.", severity="error")
            return

    def handle_operate_result(
        self, operate_result: OperateData | None
    ) -> None:
        if operate_result is None:
            self.notify("Operation cancelled.")
            return
        # The dry/live mode could have changed while in the operate screen
        reactive_header = self.query_exactly_one(CustomHeader)
        reactive_header.changes_enabled = self.app.changes_enabled
        self.refresh_bindings()
        if operate_result.command_result is None:
            self.notify("Operation was cancelled.")
            return
        if (
            operate_result.command_result.returncode == 0
            and self.app.changes_enabled
        ):
            self.notify("Operation completed successfully.")
        elif (
            operate_result.command_result.returncode == 0
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
        if operate_result.operate_btn in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
        ):
            add_dir_tree = self.query_one(
                self.app.tab_ids.add.tree.dir_tree_q, FilteredDirTree
            )
            add_dir_tree.reload()
            return
        if operate_result.operate_btn in (
            OperateBtn.apply_path,
            OperateBtn.re_add_path,
            OperateBtn.destroy_path,
            OperateBtn.forget_path,
        ):
            self.populate_apply_trees()
            self.populate_re_add_trees()
            return
        self.notify("Operation result not handled.", severity="error")

    @on(CurrentAddNodeMsg)
    def update_current_dir_tree_node(self, message: CurrentAddNodeMsg) -> None:
        self.current_add_node = message.dir_tree_node_data

    @on(CurrentApplyNodeMsg)
    def update_current_apply_node(self, message: CurrentApplyNodeMsg) -> None:
        self.current_apply_node = message.node_data

    @on(CurrentReAddNodeMsg)
    def update_current_re_add_node(self, message: CurrentReAddNodeMsg) -> None:
        self.current_re_add_node = message.node_data
