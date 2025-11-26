from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, TabbedContent, TabPane

from chezmoi_mousse import (
    AppType,
    CommandResult,
    OperateBtn,
    OperateScreenData,
    TabName,
    Tcss,
)
from chezmoi_mousse.shared import (
    CurrentAddNodeMsg,
    CurrentApplyNodeMsg,
    CurrentReAddNodeMsg,
    CustomHeader,
)

from .operate import OperateScreen
from .tabs.add_tab import AddTab, FilteredDirTree
from .tabs.apply_tab import ApplyTab
from .tabs.common.trees import ExpandedTree, ListTree, ManagedTree
from .tabs.config_tab import ConfigTab, ConfigTabSwitcher
from .tabs.help_tab import HelpTab
from .tabs.logs_tab import AppLog, DebugLog, LogsTab, OperateLog, ReadCmdLog
from .tabs.re_add_tab import ReAddTab

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, DirTreeNodeData, NodeData, SplashData

__all__ = ["TabbedContentScreen"]


class TabPanes(StrEnum):
    add_tab_button = "Add"
    apply_tab_button = "Apply"
    config_tab_button = "Config"
    help_tab_button = "Help"
    logs_tab_button = "Logs"
    re_add_tab_button = "Re-Add"


class TabbedContentScreen(Screen[None], AppType):

    destDir: Path | None = None
    init_cmd_result: "CommandResult | None" = None

    def __init__(self, *, ids: "AppIds", splash_data: "SplashData") -> None:
        self.ids = ids
        super().__init__()

        self.splash_data = splash_data
        self.app_log: "AppLog"
        self.read_log: "ReadCmdLog"
        self.operate_log: "OperateLog"
        self.debug_log: "DebugLog"

        self.current_add_node: "DirTreeNodeData | None" = None
        self.current_apply_node: "NodeData | None" = None
        self.current_re_add_node: "NodeData | None" = None

    def compose(self) -> ComposeResult:
        yield CustomHeader(ids=self.ids)
        with TabbedContent():
            yield TabPane(
                TabPanes.apply_tab_button,
                ApplyTab(ids=self.app.tab_ids.apply),
                id=TabName.apply.name,
            )
            yield TabPane(
                TabPanes.re_add_tab_button,
                ReAddTab(ids=self.app.tab_ids.re_add),
                id=TabName.re_add,
            )
            yield TabPane(
                TabPanes.add_tab_button,
                AddTab(ids=self.app.tab_ids.add),
                id=TabName.add,
            )
            yield TabPane(
                TabPanes.logs_tab_button,
                LogsTab(ids=self.app.tab_ids.logs),
                id=TabName.logs,
            )
            yield TabPane(
                TabPanes.config_tab_button,
                ConfigTab(ids=self.app.tab_ids.config),
                id=TabName.config,
            )
            yield TabPane(
                TabPanes.help_tab_button,
                HelpTab(ids=self.app.tab_ids.help),
                id=TabName.help,
            )
        yield Footer(id=self.ids.footer)

    async def on_mount(self) -> None:
        init_loggers_worker = self.initialize_loggers()
        await init_loggers_worker.wait()
        log_init_cmd_worker = self.log_init_screen_command()
        await log_init_cmd_worker.wait()
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
        self.app_log.ready_to_run("--- Application log initialized ---")
        if self.app.chezmoi_found:
            self.app_log.success("Found chezmoi executable.")
        else:
            self.notify("chezmoi executable not found.", severity="error")
        # Initialize Operate logger
        self.operate_log = self.query_one(
            self.app.tab_ids.logs.logger.operate_q, OperateLog
        )
        self.app.chezmoi.operate_log = self.operate_log
        self.app_log.success("Operate log initialized")
        self.operate_log.ready_to_run("--- Operate log initialized ---")
        # Initialize ReadCmd logger
        self.read_cmd_log = self.query_one(
            self.app.tab_ids.logs.logger.read_q, ReadCmdLog
        )
        self.app.chezmoi.read_cmd_log = self.read_cmd_log
        self.app_log.success("Read Output log initialized")
        # Initialize and focus Debug logger if in dev mode
        if self.app.dev_mode:
            self.debug_log = self.query_one(
                self.app.tab_ids.logs.logger.debug_q, DebugLog
            )
            self.app.chezmoi.debug_log = self.debug_log
            self.app_log.success("Debug log initialized")
            self.debug_log.ready_to_run("--- Debug log initialized ---")
            self.notify('Running in "dev mode"', severity="information")

    @work
    async def log_init_screen_command(self) -> None:
        if self.init_cmd_result is None:
            return
        self.app_log.log_cmd_results(self.init_cmd_result)
        self.operate_log.log_cmd_results(self.init_cmd_result)

    def log_splash_log_commands(self) -> None:
        # Log SplashScreen and InitScreen commands
        self.app_log.info("--- Commands executed in loading screen ---")
        if self.splash_data.init is not None:
            self.app_log.log_cmd_results(self.splash_data.init)
            self.operate_log.log_cmd_results(self.splash_data.init)
        for cmd in self.splash_data.executed_commands:
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
        self.app_log.info("Populating Apply tab trees")
        managed_tree.populate_tree()
        self.app_log.success("Apply tab managed tree populated.")
        expanded_tree.populate_tree()
        self.app_log.success("Apply tab expanded tree populated.")
        list_tree.populate_tree()
        self.app_log.success("Apply list populated.")

    def populate_re_add_trees(self) -> None:
        self.app_log.info("Populating Re-Add tab trees")
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

    @on(Button.Pressed, Tcss.operate_button)
    def push_operate_screen(self, event: Button.Pressed) -> None:
        button_enum = OperateBtn.from_label(str(event.button.label))
        current_tab = self.query_exactly_one(TabbedContent).active
        if (
            self.current_add_node is not None
            and button_enum in (OperateBtn.add_file, OperateBtn.add_dir)
            and current_tab == TabName.add
        ):
            operate_screen_data = OperateScreenData(
                operate_btn=button_enum, node_data=self.current_add_node
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
            operate_screen_data = OperateScreenData(
                operate_btn=button_enum, node_data=self.current_apply_node
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
            operate_screen_data = OperateScreenData(
                operate_btn=button_enum, node_data=self.current_re_add_node
            )
        else:
            self.notify("No current node available.", severity="error")
            return
        self.app.push_screen(
            OperateScreen(
                ids=self.app.screen_ids.operate,
                operate_data=operate_screen_data,
            ),
            callback=self.handle_operate_result,
        )

    def handle_operate_result(
        self, screen_result: OperateScreenData | None
    ) -> None:
        # the mode could have changed while in the operate screen
        reactive_header = self.query_exactly_one(CustomHeader)
        reactive_header.changes_enabled = self.app.changes_enabled
        self.refresh_bindings()
        if (
            screen_result is not None
            and screen_result.command_result is not None
        ):
            if (
                screen_result.command_result.returncode == 0
                and self.app.changes_enabled
            ):
                self.notify(
                    "Operation completed successfully, Logs tab updated."
                )
            elif (
                screen_result.command_result.returncode == 0
                and not self.app.changes_enabled
            ):
                self.notify(
                    "Operation completed in dry-run mode, Logs tab updated."
                )

            else:
                self.notify(
                    "Operation failed, check the Logs tab for more info.",
                    severity="error",
                )
            add_dir_tree = self.query_one(
                self.app.tab_ids.add.tree.dir_tree_q, FilteredDirTree
            )
            add_dir_tree.reload()
            self.populate_apply_trees()
            self.populate_re_add_trees()
        elif (
            screen_result is not None
            and screen_result.command_result is None
            and not self.app.changes_enabled
        ):
            self.notify("Operation cancelled, no changes were made.")
        else:
            self.notify(
                "Unknown operation result condition.", severity="error"
            )

    @on(CurrentAddNodeMsg)
    def update_current_dir_tree_node(self, message: CurrentAddNodeMsg) -> None:
        self.current_add_node = message.dir_tree_node_data

    @on(CurrentApplyNodeMsg)
    def update_current_apply_node(self, message: CurrentApplyNodeMsg) -> None:
        self.current_apply_node = message.node_data

    @on(CurrentReAddNodeMsg)
    def update_current_re_add_node(self, message: CurrentReAddNodeMsg) -> None:
        self.current_re_add_node = message.node_data
