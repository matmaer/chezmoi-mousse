import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalGroup
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
    AreaName,
    Canvas,
    Chars,
    Id,
    OperateBtn,
    OperateLaunchData,
    PaneBtn,
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
from .shared.loggers import AppLog, DebugLog, OutputLog
from .shared.operate_msg import (
    CurrentAddNodeMsg,
    CurrentApplyNodeMsg,
    CurrentReAddNodeMsg,
)
from .shared.operate_screen import OperateScreen
from .shared.trees import ExpandedTree, ListTree, ManagedTree

if TYPE_CHECKING:
    from chezmoi_mousse import DirTreeNodeData, NodeData, OperateResultData

    from .pre_run_screens.splash import SplashData

__all__ = ["MainScreen"]


class MainScreen(Screen[None], AppType):

    BINDINGS = [
        Binding(key="M,m", action="tcss_maximize", description="maximize"),
        Binding(
            key="F,f",
            action="toggle_switch_slider",
            description="hide filters",
        ),
    ]
    CSS_PATH = "_gui.tcss"

    destDir: Path | None = None

    def __init__(self, splash_data: "SplashData") -> None:

        self.splash_data = splash_data
        self.app_log: AppLog
        self.read_output_log: OutputLog
        self.write_output_log: OutputLog
        self.debug_log: DebugLog

        self.current_add_node: "DirTreeNodeData | None" = None
        self.current_apply_node: "NodeData | None" = None
        self.current_re_add_node: "NodeData | None" = None

        super().__init__()

    def on_mount(self) -> None:
        app_logger: AppLog = self.query_one(
            Id.logs_tab.view_id("#", view=ViewName.app_log_view), AppLog
        )
        self.app_log = app_logger
        self.app.chezmoi.app_log = app_logger
        self.app_log.ready_to_run("--- Application log initialized ---")
        self.app_log.info(f"chezmoi command found: {self.app.chezmoi_found}.")
        self.app_log.info("Loading screen completed.")
        self.app_log.success("Executed in loading screen:")
        for cmd in self.splash_data.exectuded_commands:
            self.app_log.dimmed(f"{cmd}")

        read_output_logger: OutputLog = self.query_one(
            Id.logs_tab.view_id("#", view=ViewName.read_output_log_view),
            OutputLog,
        )
        self.read_output_log = read_output_logger
        self.app.chezmoi.read_output_log = read_output_logger
        self.read_output_log.ready_to_run(
            "--- Read Output log initialized ---"
        )
        self.app_log.success("Read Output log initialized")
        self.write_output_log = self.query_one(
            Id.logs_tab.view_id("#", view=ViewName.write_output_log_view),
            OutputLog,
        )
        self.write_output_log.ready_to_run(
            "--- Write Output log initialized ---"
        )
        self.app.chezmoi.write_output_log = self.write_output_log
        self.app_log.success("Write Output log initialized")

        if self.app.dev_mode:
            debug_logger: DebugLog = self.query_one(
                Id.logs_tab.view_id("#", view=ViewName.debug_log_view),
                DebugLog,
            )
            self.debug_log = debug_logger
            self.app.chezmoi.debug_log = debug_logger
            self.debug_log.success("Debug log initialized")
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
            with TabPane(PaneBtn.apply_tab.value, id=Canvas.apply.name):
                yield ApplyTab(ids=Id.apply_tab)
            with TabPane(PaneBtn.re_add_tab.value, id=Canvas.re_add.name):
                yield ReAddTab(ids=Id.re_add_tab)
            with TabPane(PaneBtn.add_tab.value, id=Canvas.add.name):
                yield AddTab(ids=Id.add_tab)
            with TabPane(PaneBtn.logs_tab.value, id=Canvas.logs):
                yield LogsTab(ids=Id.logs_tab)
            with TabPane(PaneBtn.config_tab.value, id=Canvas.config):
                yield ConfigTab(ids=Id.config_tab)
            with TabPane(PaneBtn.help_tab.value, id=Canvas.help):
                yield HelpTab(ids=Id.help_tab)
        yield Footer()

    def handle_splash_data(self, data: "SplashData") -> None:
        self.populate_trees()
        self.update_config_tab_outputs(data)

    def populate_trees(self) -> None:
        apply_tab_managed_tree = self.screen.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.managed_tree), ManagedTree
        )
        apply_tab_expanded_tree = self.screen.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        apply_tab_flat_tree = self.screen.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.list_tree), ListTree
        )
        apply_tab_managed_tree.populate_tree()
        apply_tab_expanded_tree.populate_tree()
        apply_tab_flat_tree.populate_tree()

        re_add_tab_managed_tree = self.screen.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.managed_tree), ManagedTree
        )
        re_add_tab_expanded_tree = self.screen.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        re_add_tab_flat_tree = self.screen.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.list_tree), ListTree
        )
        re_add_tab_managed_tree.populate_tree()
        re_add_tab_expanded_tree.populate_tree()
        re_add_tab_flat_tree.populate_tree()

    def update_config_tab_outputs(self, data: "SplashData") -> None:
        config_tab_switcher = self.screen.query_one(
            Id.config_tab.content_switcher_id("#", area=AreaName.right),
            ConfigTabSwitcher,
        )
        setattr(config_tab_switcher, "doctor_results", data.doctor)
        setattr(config_tab_switcher, "cat_config_results", data.cat_config)
        setattr(config_tab_switcher, "ignored_results", data.ignored)
        setattr(
            config_tab_switcher, "template_data_results", data.template_data
        )

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        self._create_new_binding()
        self.refresh_bindings()

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        if action == "toggle_switch_slider":
            active_tab = self.query_one(TabbedContent).active
            if active_tab in (
                Id.apply_tab.canvas_name,
                Id.re_add_tab.canvas_name,
                Id.add_tab.canvas_name,
            ):
                return True
            return False
        elif action == "tcss_maximize":
            active_tab = self.query_one(TabbedContent).active
            if active_tab == Id.apply_tab.canvas_name:
                left_side = self.query_one(
                    Id.apply_tab.tab_vertical_id("#", area=AreaName.left)
                )
                operation_buttons = self.query_one(
                    Id.apply_tab.buttons_horizontal_id(
                        "#", area=AreaName.bottom
                    )
                )
            elif active_tab == Id.re_add_tab.canvas_name:
                left_side = self.query_one(
                    Id.re_add_tab.tab_vertical_id("#", area=AreaName.left)
                )
                operation_buttons = self.query_one(
                    Id.re_add_tab.buttons_horizontal_id(
                        "#", area=AreaName.bottom
                    )
                )
            else:
                left_side = self.query_one(
                    Id.add_tab.tab_vertical_id("#", area=AreaName.left)
                )
                operation_buttons = self.query_one(
                    Id.add_tab.buttons_horizontal_id("#", area=AreaName.bottom)
                )
            if left_side.has_class(Tcss.display_none.name):
                left_side.remove_class(Tcss.display_none.name)
                operation_buttons.remove_class(Tcss.display_none.name)
            else:
                left_side.add_class(Tcss.display_none.name)
                operation_buttons.add_class(Tcss.display_none.name)

            header = self.query_exactly_one(Header)
            tabs = self.query_exactly_one(Tabs)
            if header.has_class(Tcss.display_none.name):
                header.remove_class(Tcss.display_none.name)
                tabs.remove_class(Tcss.display_none.name)
            else:
                header.add_class(Tcss.display_none.name)
                tabs.add_class(Tcss.display_none.name)

            return True
        return True

    def _get_current_filter_slider(self) -> VerticalGroup:
        active_tab = self.query_one(TabbedContent).active

        if active_tab == Id.apply_tab.canvas_name:
            return self.query_one(
                Id.apply_tab.switches_slider_qid, VerticalGroup
            )
        elif active_tab == Id.re_add_tab.canvas_name:
            return self.query_one(
                Id.re_add_tab.switches_slider_qid, VerticalGroup
            )
        else:
            return self.query_one(
                Id.add_tab.switches_slider_qid, VerticalGroup
            )

    def _create_new_binding(self) -> None:
        # create a new binding with new description
        slider: VerticalGroup = self._get_current_filter_slider()

        new_description = (
            "show filters" if slider.has_class("-visible") else "hide filters"
        )
        for key, binding in self._bindings:
            if binding.action == "toggle_switch_slider":
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

    def action_toggle_switch_slider(self) -> None:
        slider = self._get_current_filter_slider()
        slider.toggle_class("-visible")

        self._create_new_binding()

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
            and current_tab == Canvas.add.name
        ):
            launch_data = OperateLaunchData(
                btn_enum_member=button_enum, node_data=self.current_add_node
            )
            self.app.push_screen(OperateScreen(launch_data))
        elif (
            self.current_apply_node is not None
            and button_enum
            in (
                OperateBtn.apply_path,
                OperateBtn.destroy_path,
                OperateBtn.forget_path,
            )
            and current_tab == Canvas.apply.name
        ):
            launch_data = OperateLaunchData(
                btn_enum_member=button_enum, node_data=self.current_apply_node
            )
            self.app.push_screen(OperateScreen(launch_data))
        elif (
            self.current_re_add_node is not None
            and button_enum
            in (
                OperateBtn.re_add_path,
                OperateBtn.destroy_path,
                OperateBtn.forget_path,
            )
            and current_tab == Canvas.re_add.name
        ):
            launch_data = OperateLaunchData(
                btn_enum_member=button_enum, node_data=self.current_re_add_node
            )
            self.app.push_screen(
                OperateScreen(launch_data),
                callback=self._handle_operate_result,
            )
        else:
            self.notify("No current node available.", severity="error")

    def _handle_operate_result(
        self, operate_result: "OperateResultData | None"
    ) -> None:
        if operate_result is None:
            self.notify("No operation result returned.", severity="error")
            return
        elif operate_result.operation_executed is False:
            self.notify(
                "Operation cancelled, no changes were made.",
                severity="information",
            )
            return
        if (
            operate_result.command_results is not None
            and operate_result.operation_executed is True
        ):
            if operate_result.command_results.returncode == 0:
                self.notify(
                    f"Operation completed successfully:\n{operate_result.command_results.pretty_cmd}"
                )
            else:
                self.notify(
                    f"Operation failed with return code {operate_result.command_results.returncode}:\n{operate_result.command_results.pretty_cmd}",
                    severity="error",
                )
            if operate_result.btn_enum_member in (
                OperateBtn.add_file,
                OperateBtn.add_dir,
            ):
                add_dir_tree = self.query_one(
                    Id.add_tab.tree_id("#", tree=TreeName.add_tree),
                    FilteredDirTree,
                )
                add_dir_tree.reload()
                add_tab = self.query_one(Id.add_tab.tab_container_id, AddTab)
                add_tab.refresh(recompose=True)
            else:
                self.populate_trees()
                apply_tab = self.query_one(
                    Id.apply_tab.tab_container_id, ApplyTab
                )
                apply_tab.refresh(recompose=True)
                re_add_tab = self.query_one(
                    Id.re_add_tab.tab_container_id, ReAddTab
                )
                re_add_tab.refresh(recompose=True)
        else:
            self.notify("Unknown operation result.", severity="error")

    @on(CurrentAddNodeMsg)
    def update_current_dir_tree_node(self, message: CurrentAddNodeMsg) -> None:
        self.current_add_node = message.dir_tree_node_data

    @on(CurrentApplyNodeMsg)
    def update_current_apply_node(self, message: CurrentApplyNodeMsg) -> None:
        self.current_apply_node = message.node_data

    @on(CurrentReAddNodeMsg)
    def update_current_re_add_node(self, message: CurrentReAddNodeMsg) -> None:
        self.current_re_add_node = message.node_data
