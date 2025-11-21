import dataclasses
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalGroup
from textual.screen import Screen
from textual.widgets import Button, Footer, TabbedContent, TabPane, Tabs

from chezmoi_mousse import (
    AppIds,
    AppType,
    Chars,
    ContainerName,
    OperateBtn,
    OperateScreenData,
    TabName,
    Tcss,
    TreeName,
)
from chezmoi_mousse.shared import (
    CurrentAddNodeMsg,
    CurrentApplyNodeMsg,
    CurrentReAddNodeMsg,
    ReactiveHeader,
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
    from chezmoi_mousse import DirTreeNodeData, NodeData, SplashData

__all__ = ["MainScreen"]


class TabIds:
    def __init__(self) -> None:
        # Construct the ids for the tabs
        self.add = AppIds(TabName.add)
        self.apply = AppIds(TabName.apply)
        self.config = AppIds(TabName.config)
        self.help = AppIds(TabName.help)
        self.logs = AppIds(TabName.logs)
        self.re_add = AppIds(TabName.re_add)


class TabPanes(StrEnum):
    add_tab_button = "Add"
    apply_tab_button = "Apply"
    config_tab_button = "Config"
    help_tab_button = "Help"
    logs_tab_button = "Logs"
    re_add_tab_button = "Re-Add"


class MainScreen(Screen[None], AppType):

    BINDINGS = [
        Binding(
            key="M,m",
            action="toggle_maximized_display",
            description="maximize",
        ),
        Binding(
            key="F,f",
            action="toggle_switch_slider",
            description="hide filters",
        ),
    ]

    destDir: Path | None = None

    def __init__(self, *, ids: "AppIds", splash_data: "SplashData") -> None:
        self.ids = ids
        super().__init__()

        self.splash_data = splash_data
        self.tab_ids = TabIds()

        self.app_log: "AppLog"
        self.read_log: "ReadCmdLog"
        self.operate_log: "OperateLog"
        self.debug_log: "DebugLog"

        self.current_add_node: "DirTreeNodeData | None" = None
        self.current_apply_node: "NodeData | None" = None
        self.current_re_add_node: "NodeData | None" = None

    def compose(self) -> ComposeResult:
        yield ReactiveHeader(ids=self.ids)
        with TabbedContent():
            yield TabPane(
                TabPanes.apply_tab_button.value,
                ApplyTab(ids=self.tab_ids.apply),
                id=TabName.apply.name,
            )
            yield TabPane(
                TabPanes.re_add_tab_button.value,
                ReAddTab(ids=self.tab_ids.re_add),
                id=TabName.re_add,
            )
            yield TabPane(
                TabPanes.add_tab_button.value,
                AddTab(ids=self.tab_ids.add),
                id=TabName.add,
            )
            yield TabPane(
                TabPanes.logs_tab_button.value,
                LogsTab(ids=self.tab_ids.logs),
                id=TabName.logs,
            )
            yield TabPane(
                TabPanes.config_tab_button.value,
                ConfigTab(ids=self.tab_ids.config),
                id=TabName.config,
            )
            yield TabPane(
                TabPanes.help_tab_button.value,
                HelpTab(ids=self.tab_ids.help),
                id=TabName.help,
            )
        yield Footer(id=self.ids.footer_id)

    async def on_mount(self) -> None:
        init_loggers_worker = self.initialize_loggers()
        await init_loggers_worker.wait()
        log_splash_commands_worker = self.log_splash_log_commands()
        await log_splash_commands_worker.wait()
        self.populate_apply_trees()
        self.populate_re_add_trees()
        self.update_config_tab()
        self.update_global_git_log()
        # Notify startup info
        if self.app.dev_mode is True:
            self.notify('Running in "dev mode"', severity="information")

    @work
    async def initialize_loggers(self) -> None:
        # Initialize App logger
        app_logger = self.query_one(self.tab_ids.logs.logger.app_q, AppLog)
        self.app_log = app_logger
        self.app.chezmoi.app_log = app_logger
        self.app_log.ready_to_run("--- Application log initialized ---")
        if self.app.chezmoi_found:
            self.app_log.success(
                f"{Chars.check_mark} Found chezmoi executable."
            )
        else:
            self.notify("chezmoi executable not found.", severity="error")
            self.app_log.error("chezmoi executable not found.")
        # Initialize Operate logger
        self.operate_log = self.query_one(
            self.tab_ids.logs.logger.operate_q, OperateLog
        )
        self.app_log.success(f"{Chars.check_mark} Operate log initialized")
        self.operate_log.ready_to_run("--- Operate log initialized ---")
        # Initialize ReadCmd logger
        read_cmd_logger = self.query_one(
            self.tab_ids.logs.logger.read_q, ReadCmdLog
        )
        self.read_cmd_log = read_cmd_logger
        self.app.chezmoi.read_cmd_log = self.read_cmd_log
        self.app_log.success(f"{Chars.check_mark} Read Output log initialized")
        # Initialize and focus Debug logger if in dev mode
        if self.app.dev_mode:
            debug_logger = self.query_one(
                self.tab_ids.logs.logger.debug_q, DebugLog
            )
            self.debug_log = debug_logger
            self.app.chezmoi.debug_log = debug_logger
            self.debug_log.ready_to_run("--- Debug log initialized ---")
            self.app_log.success(f"{Chars.check_mark} Debug log initialized")
            debug_logger.focus()

    @work
    async def log_splash_log_commands(self) -> None:
        # Log loading screen commands
        self.app_log.info("--- Commands executed in loading screen ---")
        if self.splash_data.init is not None:
            self.app_log.log_cmd_results(self.splash_data.init)
            self.operate_log.log_cmd_results(self.splash_data.init)
        self.app.chezmoi.operate_log = self.operate_log

        for cmd in self.splash_data.executed_commands:
            self.app_log.log_cmd_results(cmd)
            self.read_cmd_log.log_cmd_results(cmd)
        self.app_log.info("--- End of loading screen commands ---")

    def populate_apply_trees(self) -> None:
        self.app_log.info("Updating managed paths")
        self.app.chezmoi.update_managed_paths()
        apply_tab_managed_tree = self.screen.query_one(
            self.tab_ids.apply.tree_id("#", tree=TreeName.managed_tree),
            ManagedTree,
        )
        apply_tab_expanded_tree = self.screen.query_one(
            self.tab_ids.apply.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        apply_tab_flat_tree = self.screen.query_one(
            self.tab_ids.apply.tree_id("#", tree=TreeName.list_tree), ListTree
        )
        self.app_log.info("Populating Apply tab trees")
        apply_tab_managed_tree.populate_tree()
        self.app_log.success(f"{Chars.check_mark} Apply tab tree populated.")
        apply_tab_expanded_tree.populate_tree()
        self.app_log.success(
            f"{Chars.check_mark} Apply tab expanded tree populated."
        )
        apply_tab_flat_tree.populate_tree()
        self.app_log.success(
            f"{Chars.check_mark} Apply tab flat tree populated."
        )

    def populate_re_add_trees(self) -> None:
        self.app_log.info("Populating Re-Add tab trees")
        re_add_tab_managed_tree = self.screen.query_one(
            self.tab_ids.re_add.tree_id("#", tree=TreeName.managed_tree),
            ManagedTree,
        )
        re_add_tab_expanded_tree = self.screen.query_one(
            self.tab_ids.re_add.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        re_add_tab_flat_tree = self.screen.query_one(
            self.tab_ids.re_add.tree_id("#", tree=TreeName.list_tree), ListTree
        )
        re_add_tab_managed_tree.populate_tree()
        self.app_log.success(f"{Chars.check_mark} Re-Add tab tree populated.")
        re_add_tab_expanded_tree.populate_tree()
        self.app_log.success(
            f"{Chars.check_mark} Re-Add tab expanded tree populated."
        )
        re_add_tab_flat_tree.populate_tree()
        self.app_log.success(
            f"{Chars.check_mark} Re-Add tab flat tree populated."
        )

    def update_global_git_log(self) -> None:
        logs_tab = self.screen.query_exactly_one(LogsTab)
        logs_tab.git_log_result = self.splash_data.git_log

    def update_config_tab(self) -> None:
        config_tab_switcher = self.screen.query_one(
            self.tab_ids.config.container_id(
                "#", name=ContainerName.config_switcher
            ),
            ConfigTabSwitcher,
        )
        setattr(config_tab_switcher, "splash_data", self.splash_data)

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        if action == "toggle_switch_slider":
            active_tab = self.query_one(TabbedContent).active
            if active_tab == TabName.apply.name:
                return True
            elif active_tab == TabName.re_add:
                return True
            elif active_tab == TabName.add:
                return True
            elif active_tab == TabName.logs:
                return None
            elif active_tab == TabName.config:
                return None
            elif active_tab == TabName.help:
                return None
        return True

    def _get_slider_from_tab(self, tab_name: str) -> VerticalGroup | None:
        if tab_name == TabName.apply.name:
            return self.query_one(
                self.tab_ids.apply.container.switch_slider_q, VerticalGroup
            )
        elif tab_name == TabName.re_add:
            return self.query_one(
                self.tab_ids.re_add.container.switch_slider_q, VerticalGroup
            )
        elif tab_name == TabName.add:
            return self.query_one(
                self.tab_ids.add.container.switch_slider_q, VerticalGroup
            )
        else:
            return None

    def _update_toggle_switch_slider_binding(self, tab_name: str) -> None:
        slider = self._get_slider_from_tab(tab_name)
        if slider is None:
            return
        slider_visible = slider.has_class("-visible")
        new_description = (
            "hide filters" if slider_visible is False else "show filters"
        )
        for key, binding in self._bindings:
            if binding.action == "toggle_switch_slider":
                if (
                    binding.description == "show filters"
                    and slider_visible is True
                ):
                    return
                if (
                    binding.description == "hide filters"
                    and slider_visible is False
                ):
                    return
                # Create a new binding with the updated description
                updated_binding = dataclasses.replace(
                    binding, description=new_description
                )
                # Update the bindings map
                if key in self._bindings.key_to_bindings:
                    bindings_list = self._bindings.key_to_bindings[key]
                    for i, b in enumerate(bindings_list):
                        if b.action == "toggle_switch_slider":
                            bindings_list[i] = updated_binding
                            break
                break
        self.refresh_bindings()

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        if event.tabbed_content.active in (
            TabName.apply.name,
            TabName.re_add,
            TabName.add,
        ):
            self._update_toggle_switch_slider_binding(
                event.tabbed_content.active
            )
        self.refresh_bindings()

    def action_toggle_switch_slider(self) -> None:
        active_tab = self.query_one(TabbedContent).active
        slider = self._get_slider_from_tab(active_tab)
        if slider is None:
            return

        slider.toggle_class("-visible")
        self._update_toggle_switch_slider_binding(active_tab)

    def action_toggle_maximized_display(self) -> None:

        active_tab = self.query_one(TabbedContent).active
        left_side = None
        operation_buttons = None
        view_switcher_buttons = None
        switch_slider = None

        header = self.query_exactly_one(ReactiveHeader)
        header.display = False if header.display is True else True
        main_tabs = self.query_exactly_one(Tabs)
        main_tabs.display = False if main_tabs.display is True else True

        if active_tab == TabName.apply.name:
            left_side = self.query_one(
                self.tab_ids.apply.container.left_side_q, Vertical
            )
            operation_buttons = self.query_one(
                self.tab_ids.apply.container_id(
                    "#", name=ContainerName.operate_btn_group
                )
            )
            switch_slider = self.query_one(
                self.tab_ids.apply.container.switch_slider_q, VerticalGroup
            )
            view_switcher_buttons = self.query_one(
                self.tab_ids.apply.container_id(
                    "#", name=ContainerName.switcher_btn_group
                ),
                Horizontal,
            )
        elif active_tab == TabName.re_add:
            left_side = self.query_one(
                self.tab_ids.re_add.container.left_side_q, Vertical
            )
            operation_buttons = self.query_one(
                self.tab_ids.re_add.container_id(
                    "#", name=ContainerName.operate_btn_group
                )
            )
            switch_slider = self.query_one(
                self.tab_ids.re_add.container.switch_slider_q, VerticalGroup
            )
            view_switcher_buttons = self.query_one(
                self.tab_ids.re_add.container_id(
                    "#", name=ContainerName.switcher_btn_group
                ),
                Horizontal,
            )
        elif active_tab == TabName.add:
            left_side = self.query_one(
                self.tab_ids.add.container.left_side_q, Vertical
            )
            operation_buttons = self.query_one(
                self.tab_ids.add.container_id(
                    "#", name=ContainerName.operate_btn_group
                )
            )
            switch_slider = self.query_one(
                self.tab_ids.add.container.switch_slider_q, VerticalGroup
            )
            view_switcher_buttons = None
        elif active_tab == TabName.logs:
            view_switcher_buttons = self.query_one(
                self.tab_ids.logs.container_id(
                    "#", name=ContainerName.switcher_btn_group
                ),
                Horizontal,
            )
        elif active_tab == TabName.config:
            left_side = self.query_one(
                self.tab_ids.config.container.left_side_q, Vertical
            )
            view_switcher_buttons = self.query_one(
                self.tab_ids.logs.container_id(
                    "#", name=ContainerName.switcher_btn_group
                ),
                Horizontal,
            )
        elif active_tab == TabName.help:
            left_side = self.query_one(
                self.tab_ids.help.container.left_side_q, Vertical
            )
            view_switcher_buttons = self.query_one(
                self.tab_ids.help.container_id(
                    "#", name=ContainerName.switcher_btn_group
                ),
                Horizontal,
            )

        if left_side is not None:
            left_side.display = False if left_side.display is True else True

        if operation_buttons is not None:
            operation_buttons.display = (
                False if operation_buttons.display is True else True
            )

        if view_switcher_buttons is not None:
            view_switcher_buttons.display = (
                False if view_switcher_buttons.display is True else True
            )

        if switch_slider is not None:
            switch_slider.display = (
                False if switch_slider.display is True else True
            )

        new_description = "maximize" if header.display is True else "minimize"

        for key, binding in self._bindings:
            if binding.action == "toggle_maximized_display":
                # Create a new binding with the updated description
                updated_binding = dataclasses.replace(
                    binding, description=new_description
                )
                # Update the bindings map
                if key in self._bindings.key_to_bindings:
                    bindings_list = self._bindings.key_to_bindings[key]
                    for i, b in enumerate(bindings_list):
                        if b.action == "toggle_maximized_display":
                            bindings_list[i] = updated_binding
                            break
                break

        self.refresh_bindings()

    @on(Button.Pressed, Tcss.operate_button.value)
    def push_operate_screen(self, event: Button.Pressed) -> None:
        button_enum = OperateBtn.from_label(str(event.button.label))
        current_tab = self.query_one(TabbedContent).active
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
                ids=self.app.screen_id.operate,
                operate_data=operate_screen_data,
            ),
            callback=self._handle_operate_result,
        )

    def _handle_operate_result(
        self, screen_result: "OperateScreenData | None"
    ) -> None:
        # the mode could have changed while in the operate screen
        reactive_header = self.query_exactly_one(ReactiveHeader)
        reactive_header.changes_enabled = self.app.changes_enabled
        self.refresh_bindings()
        # Actual handling of the result
        if screen_result is None:
            self.notify("No operation result returned.", severity="error")
            return
        elif screen_result.operation_executed is False:
            self.notify(
                "Operation cancelled, no changes were made.",
                severity="warning",
            )
            return
        elif (
            screen_result.operation_executed is True
            and screen_result.command_result is not None
        ):
            if screen_result.command_result.returncode == 0:
                self.notify(
                    "Operation completed successfully, Logs tab updated."
                )
            else:
                self.notify(
                    "Operation failed, check the Logs tab for more info.",
                    severity="error",
                )
            if screen_result.operate_btn in (
                OperateBtn.add_file,
                OperateBtn.add_dir,
            ):
                add_dir_tree = self.query_one(
                    self.tab_ids.add.tree_id("#", tree=TreeName.add_tree),
                    FilteredDirTree,
                )
                add_dir_tree.reload()
            else:
                self.populate_apply_trees()
                self.populate_re_add_trees()
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
