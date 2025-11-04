import dataclasses
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup, Vertical, VerticalGroup
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    TabbedContent,
    TabPane,
    Tabs,
)

from chezmoi_mousse import (
    AppType,
    CanvasName,
    Chars,
    ContainerName,
    OperateBtn,
    OperateScreenData,
    Tcss,
    TreeName,
    ViewName,
)

from .add_tab import AddTab, FilteredDirTree
from .apply_tab import ApplyTab
from .config_tab import ConfigTab, ConfigTabSwitcher
from .help_tab import HelpTab
from .logs_tab import LogsTab
from .re_add_tab import ReAddTab
from .screens.operate import OperateScreen
from .shared.canvas_ids import CanvasIds
from .shared.loggers import AppLog, DebugLog, OutputLog
from .shared.operate_msg import (
    CurrentAddNodeMsg,
    CurrentApplyNodeMsg,
    CurrentReAddNodeMsg,
)
from .shared.trees import ExpandedTree, ListTree, ManagedTree

if TYPE_CHECKING:
    from chezmoi_mousse import DirTreeNodeData, NodeData

    from .screens.splash import SplashData

__all__ = ["MainScreen"]


class Strings(StrEnum):
    add_tab_button = "Add"
    apply_tab_button = "Apply"
    config_tab_button = "Config"
    header_dry_run_mode = (
        " -  c h e z m o i  m o u s s e  --  d r y  r u n  m o d e  - "
    )
    header_live_mode = (
        " -  c h e z m o i  m o u s s e  --  l i v e  m o d e  - "
    )
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
    CSS_PATH = "_gui.tcss"

    destDir: Path | None = None

    def __init__(self, splash_data: "SplashData") -> None:
        super().__init__()

        self.splash_data = splash_data

        self.add_tab_ids = CanvasIds(CanvasName.add_tab)
        self.add_switch_slider_qid = self.add_tab_ids.switch_slider_id(
            "#", name=ContainerName.switch_slider
        )
        self.apply_tab_ids = CanvasIds(CanvasName.apply_tab)
        self.apply_switch_slider_qid = self.apply_tab_ids.switch_slider_id(
            "#", name=ContainerName.switch_slider
        )
        self.config_tab_ids = CanvasIds(CanvasName.config_tab)
        self.help_tab_ids = CanvasIds(CanvasName.help_tab)
        self.logs_tab_ids = CanvasIds(CanvasName.logs_tab)
        self.app_log_qid = self.logs_tab_ids.view_id(
            "#", view=ViewName.app_log_view
        )
        self.read_output_log_qid = self.logs_tab_ids.view_id(
            "#", view=ViewName.read_output_log_view
        )
        self.write_output_log_qid = self.logs_tab_ids.view_id(
            "#", view=ViewName.write_output_log_view
        )
        self.debug_log_qid = self.logs_tab_ids.view_id(
            "#", view=ViewName.debug_log_view
        )
        self.re_add_tab_ids = CanvasIds(CanvasName.re_add_tab)
        self.re_add_switch_slider_qid = self.re_add_tab_ids.switch_slider_id(
            "#", name=ContainerName.switch_slider
        )

        self.app_log: "AppLog"
        self.read_output_log: "OutputLog"
        self.write_output_log: "OutputLog"
        self.debug_log: "DebugLog"

        self.current_add_node: "DirTreeNodeData | None" = None
        self.current_apply_node: "NodeData | None" = None
        self.current_re_add_node: "NodeData | None" = None

    def on_mount(self) -> None:
        self.title = (
            Strings.header_live_mode.value
            if self.app.changes_enabled
            else Strings.header_dry_run_mode.value
        )
        app_logger = self.query_one(self.app_log_qid, AppLog)
        self.app_log = app_logger
        self.app.chezmoi.app_log = app_logger
        self.app_log.ready_to_run("--- Application log initialized ---")
        self.app_log.info(f"chezmoi command found: {self.app.chezmoi_found}.")
        self.app_log.info("Loading screen completed.")

        read_output_logger = self.query_one(
            self.read_output_log_qid, OutputLog
        )
        self.read_output_log = read_output_logger
        self.app.chezmoi.read_output_log = read_output_logger
        self.read_output_log.ready_to_run(
            "--- Read Output log initialized ---"
        )
        self.app_log.success("Read Output log initialized")

        self.app_log.info("Commands executed during startup:")
        for cmd in self.splash_data.executed_commands:
            self.app_log.log_cmd_results(cmd)
            self.read_output_log.log_cmd_results(cmd)
        self.app_log.info("End of startup commands.")
        self.write_output_log = self.query_one(
            self.write_output_log_qid, OutputLog
        )
        self.write_output_log.ready_to_run(
            "--- Write Output log initialized ---"
        )
        self.app.chezmoi.write_output_log = self.write_output_log
        self.app_log.info("Write Output log initialized")

        if self.app.dev_mode:
            debug_logger = self.query_one(self.debug_log_qid, DebugLog)
            self.debug_log = debug_logger
            self.app.chezmoi.debug_log = debug_logger
            self.debug_log.ready_to_run("--- Debug log initialized ---")
            self.app_log.info("Debug log initialized")
        # Notify startup info
        if self.app.dev_mode is True:
            self.notify('Running in "dev mode"', severity="information")
        if self.app.changes_enabled is True:
            self.notify("Changes are enabled", severity="warning")
        else:
            self.notify("Changes are disabled", severity="information")

        self.handle_splash_data(self.splash_data)

    def compose(self) -> ComposeResult:
        yield Header(icon=Chars.burger)
        with TabbedContent():
            with TabPane(
                Strings.apply_tab_button.value, id=CanvasName.apply_tab.name
            ):
                yield ApplyTab(ids=self.apply_tab_ids)
            with TabPane(
                Strings.re_add_tab_button.value, id=CanvasName.re_add_tab.name
            ):
                yield ReAddTab(ids=self.re_add_tab_ids)
            with TabPane(
                Strings.add_tab_button.value, id=CanvasName.add_tab.name
            ):
                yield AddTab(ids=self.add_tab_ids)
            with TabPane(
                Strings.logs_tab_button.value, id=CanvasName.logs_tab.name
            ):
                yield LogsTab(ids=self.logs_tab_ids)
            with TabPane(
                Strings.config_tab_button.value, id=CanvasName.config_tab.name
            ):
                yield ConfigTab(ids=self.config_tab_ids)
            with TabPane(
                Strings.help_tab_button.value, id=CanvasName.help_tab.name
            ):
                yield HelpTab(ids=self.help_tab_ids)
        yield Footer()

    def handle_splash_data(self, data: "SplashData") -> None:
        self.populate_trees()
        self.update_config_tab_outputs(data)

    def populate_trees(self) -> None:
        apply_tab_managed_tree = self.screen.query_one(
            self.apply_tab_ids.tree_id("#", tree=TreeName.managed_tree),
            ManagedTree,
        )
        apply_tab_expanded_tree = self.screen.query_one(
            self.apply_tab_ids.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        apply_tab_flat_tree = self.screen.query_one(
            self.apply_tab_ids.tree_id("#", tree=TreeName.list_tree), ListTree
        )
        apply_tab_managed_tree.populate_tree()
        apply_tab_expanded_tree.populate_tree()
        apply_tab_flat_tree.populate_tree()

        re_add_tab_managed_tree = self.screen.query_one(
            self.re_add_tab_ids.tree_id("#", tree=TreeName.managed_tree),
            ManagedTree,
        )
        re_add_tab_expanded_tree = self.screen.query_one(
            self.re_add_tab_ids.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        re_add_tab_flat_tree = self.screen.query_one(
            self.re_add_tab_ids.tree_id("#", tree=TreeName.list_tree), ListTree
        )
        re_add_tab_managed_tree.populate_tree()
        re_add_tab_expanded_tree.populate_tree()
        re_add_tab_flat_tree.populate_tree()

    def update_config_tab_outputs(self, data: "SplashData") -> None:
        config_tab_switcher = self.screen.query_one(
            self.config_tab_ids.content_switcher_id(
                "#", name=ContainerName.config_switcher
            ),
            ConfigTabSwitcher,
        )
        setattr(config_tab_switcher, "doctor_results", data.doctor)
        setattr(config_tab_switcher, "cat_config_results", data.cat_config)
        setattr(config_tab_switcher, "ignored_results", data.ignored)
        setattr(
            config_tab_switcher, "template_data_results", data.template_data
        )

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        if action == "toggle_switch_slider":
            active_tab = self.query_one(TabbedContent).active
            if active_tab == CanvasName.apply_tab:
                return True
            elif active_tab == CanvasName.re_add_tab:
                return True
            elif active_tab == CanvasName.add_tab:
                return True
            elif active_tab == CanvasName.logs_tab:
                return False
            elif active_tab == CanvasName.config_tab:
                return False
            elif active_tab == CanvasName.help_tab:
                return False
        return True

    def _get_slider_from_tab(self, tab_name: str) -> VerticalGroup | None:
        if tab_name == CanvasName.apply_tab:
            return self.query_one(self.apply_switch_slider_qid, VerticalGroup)
        elif tab_name == CanvasName.re_add_tab:
            return self.query_one(self.re_add_switch_slider_qid, VerticalGroup)
        elif tab_name == CanvasName.add_tab:
            return self.query_one(self.add_switch_slider_qid, VerticalGroup)
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
            CanvasName.apply_tab,
            CanvasName.re_add_tab,
            CanvasName.add_tab,
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

        header = self.query_exactly_one(Header)
        header.display = False if header.display is True else True
        main_tabs = self.query_exactly_one(Tabs)
        main_tabs.display = False if main_tabs.display is True else True

        if active_tab == CanvasName.apply_tab:
            left_side = self.query_one(
                self.apply_tab_ids.tab_vertical_id(
                    "#", name=ContainerName.left_container
                ),
                Vertical,
            )
            view_switcher_buttons = self.query_one(
                self.apply_tab_ids.buttons_group_id(
                    "#", name=ContainerName.switcher_btn_group
                ),
                HorizontalGroup,
            )
        elif active_tab == CanvasName.re_add_tab:
            left_side = self.query_one(
                self.re_add_tab_ids.tab_vertical_id(
                    "#", name=ContainerName.left_container
                ),
                Vertical,
            )
            operation_buttons = self.query_one(
                self.re_add_tab_ids.buttons_group_id(
                    "#", name=ContainerName.operate_btn_group
                )
            )
        elif active_tab == CanvasName.add_tab:
            left_side = self.query_one(
                self.add_tab_ids.tab_vertical_id(
                    "#", name=ContainerName.left_container
                ),
                Vertical,
            )
            operation_buttons = self.query_one(
                self.add_tab_ids.buttons_group_id(
                    "#", name=ContainerName.operate_btn_group
                )
            )
        elif active_tab == CanvasName.logs_tab:
            view_switcher_buttons = self.query_one(
                self.logs_tab_ids.buttons_group_id(
                    "#", name=ContainerName.switcher_btn_group
                ),
                HorizontalGroup,
            )
        elif active_tab == CanvasName.config_tab:
            left_side = self.query_one(
                self.config_tab_ids.tab_vertical_id(
                    "#", name=ContainerName.left_container
                ),
                Vertical,
            )
        elif active_tab == CanvasName.help_tab:
            left_side = self.query_one(
                self.help_tab_ids.tab_vertical_id(
                    "#", name=ContainerName.left_container
                ),
                Vertical,
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

    def on_theme_change(self, _: str, new_theme: str) -> None:
        self.app_log.success(f"Theme set to {new_theme}")

    @on(Button.Pressed, Tcss.operate_button.value)
    def push_operate_screen(self, event: Button.Pressed) -> None:
        button_enum = OperateBtn.from_label(str(event.button.label))
        current_tab = self.query_one(TabbedContent).active
        if (
            self.current_add_node is not None
            and button_enum in (OperateBtn.add_file, OperateBtn.add_dir)
            and current_tab == CanvasName.add_tab
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
            and current_tab == CanvasName.apply_tab
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
            and current_tab == CanvasName.re_add_tab
        ):
            operate_screen_data = OperateScreenData(
                operate_btn=button_enum, node_data=self.current_re_add_node
            )
        else:
            self.notify("No current node available.", severity="error")
            return
        self.app.push_screen(
            OperateScreen(operate_screen_data),
            callback=self._handle_operate_result,
        )

    def _handle_operate_result(
        self, screen_result: "OperateScreenData | None"
    ) -> None:
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
                    self.add_tab_ids.tree_id("#", tree=TreeName.add_tree),
                    FilteredDirTree,
                )
                add_dir_tree.reload()
            else:
                self.populate_trees()
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
