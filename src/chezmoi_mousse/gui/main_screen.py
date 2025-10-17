from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import (
    ContentSwitcher,
    Footer,
    Header,
    TabbedContent,
    TabPane,
)

from chezmoi_mousse import (
    AppType,
    AreaName,
    Canvas,
    Chars,
    Id,
    OperateBtn,
    PaneBtn,
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
from .shared.operate.operate_info import OperateInfo

if TYPE_CHECKING:
    from .pre_run_screens.splash import SplashData

__all__ = ["MainScreen"]


class PostSplashHandler(AppType):
    # Groups the post-splash update methods, holds a reference to the main
    # App instance so it can call all app methods and set the chezmoi instance,
    # and access the return_data from the LoadingScreen.

    def __init__(self, screen: "MainScreen") -> None:
        self.screen = screen

    def handle_splash_data(self, splash_data: "SplashData") -> None:

        # TODO: add logic to push the Init screen if chezmoi is found but not
        # initialized, like on a newly installed system or deployment.

        self.update_chezmoi_instance(splash_data)
        self.update_diff_view_destDir(splash_data)
        self.update_managed_tree_destDir(splash_data)
        self.update_expanded_tree_destDir(splash_data)
        self.update_flat_tree_destDir(splash_data)
        self.update_contents_view_destDir(splash_data)
        self.update_git_log_view_destDir(splash_data)
        self.update_config_tab(splash_data)
        self.update_operate_info(splash_data)
        self.update_dir_tree_destDir(splash_data)

    def update_chezmoi_instance(self, data: "SplashData") -> None:
        self.app.chezmoi.managed_paths = data.managed_paths

    def update_managed_tree_destDir(self, data: "SplashData") -> None:
        apply_tab_managed_tree = self.screen.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.managed_tree), ManagedTree
        )
        apply_tab_managed_tree.destDir = data.parsed_config.dest_dir

        re_add_tab_managed_tree = self.screen.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.managed_tree), ManagedTree
        )
        re_add_tab_managed_tree.destDir = data.parsed_config.dest_dir

    def update_expanded_tree_destDir(self, data: "SplashData") -> None:
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

    def update_flat_tree_destDir(self, data: "SplashData") -> None:
        apply_tab_flat_tree = self.screen.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.flat_tree), FlatTree
        )
        apply_tab_flat_tree.destDir = data.parsed_config.dest_dir

        re_add_tab_flat_tree = self.screen.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.flat_tree), FlatTree
        )
        re_add_tab_flat_tree.destDir = data.parsed_config.dest_dir

    def update_diff_view_destDir(self, data: "SplashData") -> None:
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

    def update_contents_view_destDir(self, data: "SplashData") -> None:
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

    def update_git_log_view_destDir(self, data: "SplashData") -> None:
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

    def update_dir_tree_destDir(self, data: "SplashData") -> None:
        dir_tree = self.screen.query_one(
            Id.add_tab.tree_id("#", tree=TreeName.add_tree), FilteredDirTree
        )
        dir_tree.path = data.parsed_config.dest_dir

    def update_config_tab(self, data: "SplashData") -> None:
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

    def update_operate_info(self, data: "SplashData") -> None:
        OperateInfo.git_autocommit = data.parsed_config.git_autocommit
        OperateInfo.git_autopush = data.parsed_config.git_autopush


class MainScreen(Screen[None], AppType):

    BINDINGS = [
        Binding(
            key="H,h",
            action="hide_header_and_tabs",
            description="show/hide header",
        ),
        Binding(
            key="F,f",
            action="toggle_switch_slider",
            description="show/hide filters",
        ),
    ]
    CSS_PATH = "_gui.tcss"

    def __init__(self, splash_data: "SplashData") -> None:

        self.app_log: AppLog
        self.output_log: OutputLog
        self.debug_log: DebugLog

        super().__init__()

        self.post_splash_handler = PostSplashHandler(self)

    def on_mount(self) -> None:
        self._setup_ui_loggers()
        self.app_log.success(
            f"chezmoi command found: {self.app.chezmoi_found}"
        )
        self.app_log.ready_to_run("--- Loading screen completed ---")
        # Notify startup info
        if self.app.dev_mode is True:
            self.notify('Running in "dev mode"', severity="information")
        if self.app.changes_enabled is True:
            self.notify("Changes are enabled", severity="warning")
        else:
            self.notify("Changes are disabled", severity="information")

    def compose(self) -> ComposeResult:
        yield Header(icon=Chars.burger)
        with TabbedContent():
            with TabPane(PaneBtn.apply_tab.value, id=Canvas.apply):
                yield ApplyTab(ids=Id.apply_tab)
                yield OperateBtnHorizontal(
                    ids=Id.apply_tab,
                    buttons=(
                        OperateBtn.apply_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                )
            with TabPane(PaneBtn.re_add_tab.value, id=Canvas.re_add):
                yield ReAddTab(ids=Id.re_add_tab)
                yield OperateBtnHorizontal(
                    ids=Id.re_add_tab,
                    buttons=(
                        OperateBtn.re_add_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                )
            with TabPane(PaneBtn.add_tab.value, id=Canvas.add):
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

    def _setup_ui_loggers(self) -> None:
        app_logger: AppLog = self.query_one(
            Id.logs_tab.view_id("#", view=ViewName.app_log_view), AppLog
        )
        self.app_log = app_logger
        self.app.chezmoi.app_log = app_logger

        output_logger: OutputLog = self.query_one(
            Id.logs_tab.view_id("#", view=ViewName.output_log_view), OutputLog
        )
        self.output_log = output_logger
        self.app.chezmoi.output_log = output_logger

        if self.app.dev_mode:
            debug_logger: DebugLog = self.query_one(
                Id.logs_tab.view_id("#", view=ViewName.debug_log_view),
                DebugLog,
            )
            self.debug_log = debug_logger
            self.app.chezmoi.debug_log = debug_logger

    # def on_tabbed_content_tab_activated(
    #     self, event: TabbedContent.TabActivated
    # ) -> None:
    #     self.refresh_bindings()

    # def check_action(
    #     self, action: str, parameters: tuple[object, ...]
    # ) -> bool | None:
    #     if action == "toggle_switch_slider":
    #         if self.query_one(TabbedContent).active in (
    #             Id.apply_tab.canvas_name,
    #             Id.re_add_tab.canvas_name,
    #             Id.add_tab.canvas_name,
    #         ):
    #             return True
    #         return None
    #     elif action == "hide_header_and_tabs":
    #         return True
    #     return True

    # def action_toggle_switch_slider(self) -> None:
    #     # merely find the corresponding method in the active tab ant call it
    #     tab_widget = self.query_one(
    #         f"#{self.query_one(TabbedContent).active}", TabPane
    #     ).children[0]
    #     if hasattr(tab_widget, "action_toggle_switch_slider") is True:
    #         getattr(tab_widget, "action_toggle_switch_slider")()  # call it

    # def on_theme_change(self, _: str, new_theme: str) -> None:
    #     self.app_log.success(f"Theme set to {new_theme}")

    # def action_hide_header_and_tabs(self) -> None:
    #     header = self.query_exactly_one(Header)
    #     tabs = self.query_exactly_one(Tabs)
    #     if header.has_class("display_none"):
    #         header.remove_class("display_none")
    #         tabs.remove_class("display_none")
    #     else:
    #         header.add_class("display_none")
    #         tabs.add_class("display_none")
