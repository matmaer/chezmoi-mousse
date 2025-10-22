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
    OperateData,
    PaneBtn,
    Tcss,
    TreeName,
    ViewName,
)

from .add_tab import AddTab, FilteredDirTree
from .apply_tab import ApplyTab
from .config_tab import ConfigTab
from .help_tab import HelpTab
from .logs_tab import AppLog, DebugLog, LogsTab, OutputLog
from .re_add_tab import ReAddTab
from .shared.button_groups import OperateBtnHorizontal
from .shared.operate.contents_view import ContentsView
from .shared.operate.diff_view import DiffView
from .shared.operate.expanded_tree import ExpandedTree
from .shared.operate.flat_tree import FlatTree
from .shared.operate.git_log_view import GitLogView
from .shared.operate.managed_tree import ManagedTree
from .shared.operate.operate_screen import OperateInfo, OperateScreen

if TYPE_CHECKING:
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
            with TabPane(PaneBtn.logs_tab.value, id=Canvas.logs):
                yield LogsTab(ids=Id.logs_tab)
            with TabPane(PaneBtn.config_tab.value, id=Canvas.config):
                yield ConfigTab(ids=Id.config_tab)
            with TabPane(PaneBtn.help_tab.value, id=Canvas.help):
                yield HelpTab(ids=Id.help_tab)
        yield Footer()

    def handle_splash_data(self, data: "SplashData") -> None:

        # update ManagedTree destDir
        apply_tab_managed_tree = self.screen.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.managed_tree), ManagedTree
        )
        apply_tab_managed_tree.destDir = data.parsed_config.dest_dir
        re_add_tab_managed_tree = self.screen.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.managed_tree), ManagedTree
        )
        re_add_tab_managed_tree.destDir = data.parsed_config.dest_dir

        # update ExpandedTree destDir
        apply_tab_expanded_tree = self.screen.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        apply_tab_expanded_tree.destDir = data.parsed_config.dest_dir
        re_add_tab_expanded_tree = self.screen.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        re_add_tab_expanded_tree.destDir = data.parsed_config.dest_dir

        # update FlatTree destDir
        apply_tab_flat_tree = self.screen.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.flat_tree), FlatTree
        )
        apply_tab_flat_tree.destDir = data.parsed_config.dest_dir
        re_add_tab_flat_tree = self.screen.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.flat_tree), FlatTree
        )
        re_add_tab_flat_tree.destDir = data.parsed_config.dest_dir

        # update DiffView destDir
        apply_diff_view = self.screen.query_one(
            Id.apply_tab.view_id("#", view=ViewName.diff_view), DiffView
        )
        apply_diff_view.destDir = data.parsed_config.dest_dir
        apply_diff_view.path = data.parsed_config.dest_dir
        re_add_diff_view = self.screen.query_one(
            Id.re_add_tab.view_id("#", view=ViewName.diff_view), DiffView
        )
        re_add_diff_view.destDir = data.parsed_config.dest_dir
        re_add_diff_view.path = data.parsed_config.dest_dir

        # update ContentsView destDir
        add_tab_contents_view = self.screen.query_one(
            Id.add_tab.view_id("#", view=ViewName.contents_view), ContentsView
        )
        add_tab_contents_view.destDir = data.parsed_config.dest_dir
        add_tab_contents_view.path = data.parsed_config.dest_dir
        apply_contents_view = self.screen.query_one(
            Id.apply_tab.view_id("#", view=ViewName.contents_view),
            ContentsView,
        )
        apply_contents_view.destDir = data.parsed_config.dest_dir
        apply_contents_view.path = data.parsed_config.dest_dir

        re_add_contents_view = self.screen.query_one(
            Id.re_add_tab.view_id("#", view=ViewName.contents_view),
            ContentsView,
        )
        re_add_contents_view.destDir = data.parsed_config.dest_dir
        re_add_contents_view.path = data.parsed_config.dest_dir

        # update GitLogView destDir
        apply_git_log_view = self.screen.query_one(
            Id.apply_tab.view_id("#", view=ViewName.git_log_view), GitLogView
        )
        apply_git_log_view.destDir = data.parsed_config.dest_dir
        apply_git_log_view.path = data.parsed_config.dest_dir

        re_add_git_log_view = self.screen.query_one(
            Id.re_add_tab.view_id("#", view=ViewName.git_log_view), GitLogView
        )
        re_add_git_log_view.destDir = data.parsed_config.dest_dir
        re_add_git_log_view.path = data.parsed_config.dest_dir

        # update FilteredDirTree destDir
        dir_tree = self.screen.query_one(
            Id.add_tab.tree_id("#", tree=TreeName.add_tree), FilteredDirTree
        )
        dir_tree.path = data.parsed_config.dest_dir

        # update ConfigTab outputs
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

        # update OperateInfo git settings
        OperateInfo.git_autocommit = data.parsed_config.git_autocommit
        OperateInfo.git_autopush = data.parsed_config.git_autopush

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
            if left_side.has_class("display_none"):
                left_side.remove_class("display_none")
                operation_buttons.remove_class("display_none")
            else:
                left_side.add_class("display_none")
                operation_buttons.add_class("display_none")

            header = self.query_exactly_one(Header)
            tabs = self.query_exactly_one(Tabs)
            if header.has_class("display_none"):
                header.remove_class("display_none")
                tabs.remove_class("display_none")
            else:
                header.add_class("display_none")
                tabs.add_class("display_none")

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
        self.notify(f"Operation: {event.button}")
        assert event.button.id is not None
        operate_data = OperateData(button_id=event.button.id, path=Path.home())
        self.app.push_screen(OperateScreen(operate_data))
