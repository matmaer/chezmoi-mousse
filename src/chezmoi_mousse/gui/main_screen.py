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
    ContentSwitcher,
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
from .config_tab import ConfigTab
from .destroy_tab import DestroyTab
from .forget_tab import ForgetTab
from .help_tab import HelpTab
from .logs_tab import LogsTab
from .re_add_tab import ReAddTab
from .shared.button_groups import OperateBtnHorizontal
from .shared.contents_view import ContentsView
from .shared.diff_view import DiffView
from .shared.expanded_tree import ExpandedTree
from .shared.flat_tree import FlatTree
from .shared.git_log_view import GitLogView
from .shared.loggers import AppLog, DebugLog, OutputLog
from .shared.managed_tree import ManagedTree
from .shared.operate_msg import CurrentOperatePathMsg
from .shared.operate_screen import OperateScreen

if TYPE_CHECKING:
    from chezmoi_mousse import OperateResultData

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

    def __init__(self, splash_data: "SplashData") -> None:

        self.splash_data = splash_data
        self.app_log: AppLog
        self.output_log: OutputLog
        self.debug_log: DebugLog

        self.current_operate_path: Path | None = None

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

        output_logger: OutputLog = self.query_one(
            Id.logs_tab.view_id("#", view=ViewName.output_log_view), OutputLog
        )
        self.output_log = output_logger
        self.app.chezmoi.output_log = output_logger
        self.app_log.success("Output log initialized")

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
                yield OperateBtnHorizontal(
                    ids=Id.apply_tab,
                    buttons=(
                        OperateBtn.apply_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                )
            with TabPane(PaneBtn.re_add_tab.value, id=Canvas.re_add.name):
                yield ReAddTab(ids=Id.re_add_tab)
                yield OperateBtnHorizontal(
                    ids=Id.re_add_tab,
                    buttons=(
                        OperateBtn.re_add_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                )
            with TabPane(PaneBtn.add_tab.value, id=Canvas.add.name):
                yield AddTab(ids=Id.add_tab)
                yield OperateBtnHorizontal(
                    ids=Id.add_tab,
                    buttons=(OperateBtn.add_file, OperateBtn.add_dir),
                )
            with TabPane(PaneBtn.forget_tab.value, id=Canvas.forget):
                yield ForgetTab(ids=Id.forget_tab)
            with TabPane(PaneBtn.destroy_tab.value, id=Canvas.destroy):
                yield DestroyTab(ids=Id.destroy_tab)
            with TabPane(PaneBtn.logs_tab.value, id=Canvas.logs):
                yield LogsTab(ids=Id.logs_tab)
            with TabPane(PaneBtn.config_tab.value, id=Canvas.config):
                yield ConfigTab(ids=Id.config_tab)
            with TabPane(PaneBtn.help_tab.value, id=Canvas.help):
                yield HelpTab(ids=Id.help_tab)
        yield Footer()

    def handle_splash_data(self, data: "SplashData") -> None:
        self.update_apply_trees_destDir(data.parsed_config.dest_dir)
        self.update_re_add_trees_destDir(data.parsed_config.dest_dir)
        self.update_add_dir_tree_destDir(data.parsed_config.dest_dir)
        self.update_diff_views_destDir(data.parsed_config.dest_dir)
        self.update_git_log_views_destDir(data.parsed_config.dest_dir)
        self.update_forget_trees_destDir(data.parsed_config.dest_dir)
        self.update_destroy_trees_destDir(data.parsed_config.dest_dir)
        self.update_contents_view_destDir(data.parsed_config.dest_dir)
        self.update_config_tab_outputs(data)

    def update_apply_trees_destDir(self, destDir: Path) -> None:
        apply_tab_managed_tree = self.screen.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.managed_tree), ManagedTree
        )
        apply_tab_expanded_tree = self.screen.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        apply_tab_flat_tree = self.screen.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.flat_tree), FlatTree
        )
        apply_tab_managed_tree.destDir = destDir
        apply_tab_expanded_tree.destDir = destDir
        apply_tab_flat_tree.destDir = destDir

    def update_re_add_trees_destDir(self, destDir: Path) -> None:
        re_add_tab_managed_tree = self.screen.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.managed_tree), ManagedTree
        )
        re_add_tab_expanded_tree = self.screen.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        re_add_tab_flat_tree = self.screen.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.flat_tree), FlatTree
        )
        re_add_tab_managed_tree.destDir = destDir
        re_add_tab_expanded_tree.destDir = destDir
        re_add_tab_flat_tree.destDir = destDir

    def update_add_dir_tree_destDir(self, destDir: Path) -> None:
        dir_tree = self.screen.query_one(
            Id.add_tab.tree_id("#", tree=TreeName.add_tree), FilteredDirTree
        )
        dir_tree.path = destDir

    def update_forget_trees_destDir(self, destDir: Path) -> None:
        forget_tab_managed_tree = self.screen.query_one(
            Id.forget_tab.tree_id("#", tree=TreeName.managed_tree), ManagedTree
        )
        forget_tab_expanded_tree = self.screen.query_one(
            Id.forget_tab.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        forget_tab_flat_tree = self.screen.query_one(
            Id.forget_tab.tree_id("#", tree=TreeName.flat_tree), FlatTree
        )
        forget_tab_managed_tree.destDir = destDir
        forget_tab_expanded_tree.destDir = destDir
        forget_tab_flat_tree.destDir = destDir

    def update_destroy_trees_destDir(self, destDir: Path) -> None:
        destroy_tab_managed_tree = self.screen.query_one(
            Id.destroy_tab.tree_id("#", tree=TreeName.managed_tree),
            ManagedTree,
        )
        destroy_tab_expanded_tree = self.screen.query_one(
            Id.destroy_tab.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        destroy_tab_flat_tree = self.screen.query_one(
            Id.destroy_tab.tree_id("#", tree=TreeName.flat_tree), FlatTree
        )
        destroy_tab_managed_tree.destDir = destDir
        destroy_tab_expanded_tree.destDir = destDir
        destroy_tab_flat_tree.destDir = destDir

    def update_diff_views_destDir(self, destDir: Path) -> None:
        apply_diff_view = self.screen.query_one(
            Id.apply_tab.view_id("#", view=ViewName.diff_view), DiffView
        )
        re_add_diff_view = self.screen.query_one(
            Id.re_add_tab.view_id("#", view=ViewName.diff_view), DiffView
        )
        forget_diff_view = self.screen.query_one(
            Id.forget_tab.view_id("#", view=ViewName.diff_view), DiffView
        )
        destroy_diff_view = self.screen.query_one(
            Id.destroy_tab.view_id("#", view=ViewName.diff_view), DiffView
        )
        apply_diff_view.destDir = destDir
        re_add_diff_view.destDir = destDir
        forget_diff_view.destDir = destDir
        destroy_diff_view.destDir = destDir

    def update_contents_view_destDir(self, destDir: Path) -> None:
        apply_contents_view = self.screen.query_one(
            Id.apply_tab.view_id("#", view=ViewName.contents_view),
            ContentsView,
        )
        apply_contents_view.destDir = destDir
        apply_contents_view.path = destDir

        # update ContentsView destDir
        add_tab_contents_view = self.screen.query_one(
            Id.add_tab.view_id("#", view=ViewName.contents_view), ContentsView
        )
        add_tab_contents_view.destDir = destDir
        add_tab_contents_view.path = destDir

        re_add_contents_view = self.screen.query_one(
            Id.re_add_tab.view_id("#", view=ViewName.contents_view),
            ContentsView,
        )
        re_add_contents_view.destDir = destDir
        re_add_contents_view.path = destDir

        forget_contents_view = self.screen.query_one(
            Id.forget_tab.view_id("#", view=ViewName.contents_view),
            ContentsView,
        )
        forget_contents_view.destDir = destDir
        forget_contents_view.path = destDir

        destroy_contents_view = self.screen.query_one(
            Id.destroy_tab.view_id("#", view=ViewName.contents_view),
            ContentsView,
        )
        destroy_contents_view.destDir = destDir
        destroy_contents_view.path = destDir

    def update_git_log_views_destDir(self, destDir: Path) -> None:

        apply_git_log_view = self.screen.query_one(
            Id.apply_tab.view_id("#", view=ViewName.git_log_view), GitLogView
        )
        apply_git_log_view.destDir = destDir
        apply_git_log_view.path = destDir

        re_add_git_log_view = self.screen.query_one(
            Id.re_add_tab.view_id("#", view=ViewName.git_log_view), GitLogView
        )
        re_add_git_log_view.destDir = destDir
        re_add_git_log_view.path = destDir

        forget_git_log_view = self.screen.query_one(
            Id.forget_tab.view_id("#", view=ViewName.git_log_view), GitLogView
        )
        forget_git_log_view.destDir = destDir
        forget_git_log_view.path = destDir

        destroy_git_log_view = self.screen.query_one(
            Id.destroy_tab.view_id("#", view=ViewName.git_log_view), GitLogView
        )
        destroy_git_log_view.destDir = destDir
        destroy_git_log_view.path = destDir

    def update_config_tab_outputs(self, data: "SplashData") -> None:
        config_tab_switcher = self.screen.query_one(
            Id.config_tab.content_switcher_id("#", area=AreaName.right),
            ContentSwitcher,
        )
        setattr(config_tab_switcher, "doctor_stdout", data.doctor)
        setattr(config_tab_switcher, "cat_config_stdout", data.cat_config)
        setattr(config_tab_switcher, "ignored_stdout", data.ignored)
        setattr(
            config_tab_switcher, "template_data_stdout", data.template_data
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
    def handle_operation_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id is None or self.current_operate_path is None:
            self.notify("Select a file to operate on", severity="warning")
            return
        launch_data = OperateLaunchData(
            btn_enum_member=OperateBtn(event.button.label),
            button_id=event.button.id,
            path=self.current_operate_path,
        )
        self.app.push_screen(
            OperateScreen(launch_data=launch_data),
            callback=self._handle_operate_result,
        )

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
        elif (
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
        else:
            self.notify("Unknown operation result.", severity="error")

    @on(CurrentOperatePathMsg)
    def update_operate_path(self, message: CurrentOperatePathMsg) -> None:
        self.current_operate_path = message.path
