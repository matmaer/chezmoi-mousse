from math import ceil
from pathlib import PurePath
from typing import TYPE_CHECKING

from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.scrollbar import ScrollBar, ScrollBarRender
from textual.theme import Theme
from textual.widgets import (
    ContentSwitcher,
    Footer,
    Header,
    TabbedContent,
    TabPane,
)

from chezmoi_mousse import (
    AreaName,
    Canvas,
    Chars,
    Id,
    OperateBtn,
    PaneBtn,
    TreeName,
    ViewName,
)

from .button_groups import OperateBtnHorizontal
from .config_tab import ConfigTab
from .directory_tree import FilteredDirTree
from .help_tab import HelpTab
from .logs_tab import LogsTab
from .operate_tabs import (
    AddTab,
    ApplyTab,
    ExpandedTree,
    FlatTree,
    ManagedTree,
    ReAddTab,
)
from .pre_run_screens import InstallHelp, LoadingScreen
from .rich_logs import AppLog, ContentsView, DebugLog, DiffView, OutputLog
from .widgets import GitLogView, OperateInfo

if TYPE_CHECKING:
    from chezmoi_mousse import PreRunData

    from .pre_run_screens import ParsedConfig, SplashData

__all__ = ["ChezmoiGUI"]

# TODO: implement 'chezmoi verify', if exit 0, display message in Tree
# widgets inform the user why the Tree widget is empty
# TODO: implement spinner for commands taking a bit longer like operations


chezmoi_mousse_dark = Theme(
    name="chezmoi-mousse-dark",
    dark=True,
    accent="#F187FB",
    background="#000000",
    error="#ba3c5b",  # textual dark
    foreground="#DCDCDC",
    primary="#0178D4",  # textual dark
    secondary="#004578",  # textual dark
    surface="#101010",  # see also textual/theme.py
    success="#4EBF71",  # textual dark
    warning="#ffa62b",  # textual dark
)

chezmoi_mousse_light = Theme(
    name="chezmoi-mousse-light",
    dark=False,
    background="#DEDEDE",
    foreground="#000000",
    primary="#0060AA",
    accent="#790084",
    surface="#B8B8B8",
)


class ChezmoiGUI(App[None]):
    def __init__(self, pre_run_data: "PreRunData") -> None:

        self.chezmoi = pre_run_data.chezmoi_instance
        self.changes_enabled = pre_run_data.changes_enabled
        self.chezmoi_found = pre_run_data.chezmoi_found
        self.dev_mode = pre_run_data.dev_mode
        self.parsed_config: "ParsedConfig | None" = None

        self.app_log: AppLog
        self.output_log: OutputLog
        self.debug_log: DebugLog

        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        super().__init__()

    CSS_PATH = PurePath("data", "gui.tcss")

    BINDINGS = [
        Binding(
            key="F,f",
            action="toggle_switch_slider",
            description="show/hide filters",
        )
    ]

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

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        if self.chezmoi_found is False:
            self.push_screen(
                LoadingScreen(chezmoi_found=self.chezmoi_found),
                callback=self.run_post_splash_actions,
            )
            return

        self.setup_ui_loggers()
        self.app_log.success("App initialized successfully")
        self.app_log.ready_to_run("--- Start loading screen ---")

        self.push_screen(
            LoadingScreen(chezmoi_found=self.chezmoi_found),
            callback=self.run_post_splash_actions,
        )

    def setup_ui_loggers(self) -> None:
        app_logger: AppLog = self.query_one(
            Id.logs_tab.view_id("#", view=ViewName.app_log_view), AppLog
        )
        self.app_log = app_logger
        self.chezmoi.app_log = app_logger

        output_logger: OutputLog = self.query_one(
            Id.logs_tab.view_id("#", view=ViewName.output_log_view), OutputLog
        )
        self.output_log = output_logger
        self.chezmoi.output_log = output_logger

        if self.dev_mode:
            debug_logger: DebugLog = self.query_one(
                Id.logs_tab.view_id("#", view=ViewName.debug_log_view),
                DebugLog,
            )
            self.debug_log = debug_logger
            self.chezmoi.debug_log = debug_logger

    def run_post_splash_actions(
        self, return_data: "SplashData | None"
    ) -> None:
        if return_data is None:
            self.push_screen(InstallHelp(chezmoi_found=self.chezmoi_found))
            return
        self.app_log.success(f"chezmoi command found: {self.chezmoi_found}")
        self.app_log.ready_to_run("--- Loading screen completed ---")
        # Notify startup info
        if self.dev_mode is True:
            self.notify('Running in "dev mode"', severity="information")
        if self.changes_enabled is True:
            self.notify("Changes are enabled", severity="warning")
        else:
            self.notify("Changes are disabled", severity="information")

        self.update_chezmoi_instance(return_data)
        self.update_diff_view_destDir(return_data)
        self.update_managed_tree_destDir(return_data)
        self.update_expanded_tree_destDir(return_data)
        self.update_flat_tree_destDir(return_data)
        self.update_contents_view_destDir(return_data)
        self.update_git_log_view_destDir(return_data)
        self.update_config_tab(return_data)
        self.update_operate_info(return_data)
        self.update_dir_tree_destDir(return_data)

    def update_chezmoi_instance(self, data: "SplashData") -> None:
        self.chezmoi.managed_files_stdout = data.managed_files
        self.chezmoi.managed_dirs_stdout = data.managed_dirs
        self.chezmoi.status_dirs_stdout = data.status_dirs
        self.chezmoi.status_files_stdout = data.status_files
        self.chezmoi.status_paths_stdout = data.status_paths

    def update_managed_tree_destDir(self, data: "SplashData") -> None:
        apply_tab_managed_tree = self.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.managed_tree), ManagedTree
        )
        apply_tab_managed_tree.destDir = data.dump_config.dest_dir

        re_add_tab_managed_tree = self.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.managed_tree), ManagedTree
        )
        re_add_tab_managed_tree.destDir = data.dump_config.dest_dir

    def update_expanded_tree_destDir(self, data: "SplashData") -> None:
        apply_tab_expanded_tree = self.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        apply_tab_expanded_tree.destDir = data.dump_config.dest_dir

        re_add_tab_expanded_tree = self.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.expanded_tree),
            ExpandedTree,
        )
        re_add_tab_expanded_tree.destDir = data.dump_config.dest_dir

    def update_flat_tree_destDir(self, data: "SplashData") -> None:
        apply_tab_flat_tree = self.query_one(
            Id.apply_tab.tree_id("#", tree=TreeName.flat_tree), FlatTree
        )
        apply_tab_flat_tree.destDir = data.dump_config.dest_dir

        re_add_tab_flat_tree = self.query_one(
            Id.re_add_tab.tree_id("#", tree=TreeName.flat_tree), FlatTree
        )
        re_add_tab_flat_tree.destDir = data.dump_config.dest_dir

    def update_diff_view_destDir(self, data: "SplashData") -> None:
        apply_diff_view = self.query_one(
            Id.apply_tab.view_id("#", view=ViewName.diff_view), DiffView
        )
        apply_diff_view.destDir = data.dump_config.dest_dir
        apply_diff_view.path = data.dump_config.dest_dir

        re_add_diff_view = self.query_one(
            Id.re_add_tab.view_id("#", view=ViewName.diff_view), DiffView
        )
        re_add_diff_view.destDir = data.dump_config.dest_dir
        re_add_diff_view.path = data.dump_config.dest_dir

    def update_contents_view_destDir(self, data: "SplashData") -> None:
        apply_contents_view = self.query_one(
            Id.apply_tab.view_id("#", view=ViewName.contents_view),
            ContentsView,
        )
        apply_contents_view.destDir = data.dump_config.dest_dir
        apply_contents_view.path = data.dump_config.dest_dir

        re_add_contents_view = self.query_one(
            Id.re_add_tab.view_id("#", view=ViewName.contents_view),
            ContentsView,
        )
        re_add_contents_view.destDir = data.dump_config.dest_dir
        re_add_contents_view.path = data.dump_config.dest_dir

    def update_git_log_view_destDir(self, data: "SplashData") -> None:
        apply_git_log_view = self.query_one(
            Id.apply_tab.view_id("#", view=ViewName.git_log_view), GitLogView
        )
        apply_git_log_view.destDir = data.dump_config.dest_dir
        apply_git_log_view.path = data.dump_config.dest_dir

        re_add_git_log_view = self.query_one(
            Id.re_add_tab.view_id("#", view=ViewName.git_log_view), GitLogView
        )
        re_add_git_log_view.destDir = data.dump_config.dest_dir
        re_add_git_log_view.path = data.dump_config.dest_dir

    def update_dir_tree_destDir(self, data: "SplashData") -> None:
        dir_tree = self.query_one(
            Id.add_tab.tree_id("#", tree=TreeName.add_tree), FilteredDirTree
        )
        dir_tree.path = data.dump_config.dest_dir

    def update_config_tab(self, data: "SplashData") -> None:
        config_tab_switcher = self.query_one(
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
        OperateInfo.git_autocommit = data.dump_config.git_autocommit
        OperateInfo.git_autopush = data.dump_config.git_autopush

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        self.refresh_bindings()

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        if action == "toggle_switch_slider":
            if self.query_one(TabbedContent).active in (
                Id.apply_tab.canvas_name,
                Id.re_add_tab.canvas_name,
                Id.add_tab.canvas_name,
            ):
                return True
            return None
        return True

    def action_toggle_switch_slider(self) -> None:
        # merely find the corresponding method in the active tab ant call it
        tab_widget = self.query_one(
            f"#{self.query_one(TabbedContent).active}", TabPane
        ).children[0]
        if hasattr(tab_widget, "action_toggle_switch_slider") is True:
            getattr(tab_widget, "action_toggle_switch_slider")()  # call it

    def on_theme_change(self, _: str, new_theme: str) -> None:
        self.app_log.success(f"Theme set to {new_theme}")


class CustomScrollBarRender(ScrollBarRender):
    # Used to monkey patch the textual ScrollBar.renderer method in gui.py.

    @classmethod
    def render_bar(
        cls,
        size: int = 25,
        virtual_size: float = 50,
        window_size: float = 20,
        position: float = 0,
        thickness: int = 1,
        vertical: bool = True,
        back_color: Color = Color.parse("#555555"),
        bar_color: Color = Color.parse("bright_magenta"),
    ) -> Segments:
        if vertical:
            bars = cls.VERTICAL_BARS
        else:
            bars = cls.HORIZONTAL_BARS

        back = back_color
        bar = bar_color

        len_bars = len(bars)
        width_thickness = thickness if vertical else 1

        _Segment = Segment
        _Style = Style
        blank = cls.BLANK_GLYPH * width_thickness

        foreground_meta = {"@mouse.down": "grab"}
        if window_size and size and virtual_size and size != virtual_size:
            bar_ratio = virtual_size / size
            thumb_size = max(1, window_size / bar_ratio)

            position_ratio = position / (virtual_size - window_size)
            position = (size - thumb_size) * position_ratio

            start = int(position * len_bars)
            end = start + ceil(thumb_size * len_bars)

            start_index, start_bar = divmod(max(0, start), len_bars)
            end_index, end_bar = divmod(max(0, end), len_bars)

            upper = {"@mouse.up": "scroll_up"}
            lower = {"@mouse.up": "scroll_down"}

            upper_back_segment = Segment(
                blank, _Style(bgcolor=back, meta=upper)
            )
            lower_back_segment = Segment(
                blank, _Style(bgcolor=back, meta=lower)
            )

            segments = [upper_back_segment] * int(size)
            segments[end_index:] = [lower_back_segment] * (size - end_index)
            if vertical:
                segments[start_index:end_index] = [
                    _Segment(
                        blank,
                        _Style(color=bar, reverse=True, meta=foreground_meta),
                    )
                ] * (end_index - start_index)
                if start_index < len(segments):
                    bar_character = bars[len_bars - 1 - start_bar]
                    if bar_character != " ":
                        segments[start_index] = _Segment(
                            bar_character * width_thickness,
                            (
                                _Style(
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
                                )
                                if vertical
                                else _Style(
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
                                    reverse=True,
                                )
                            ),
                        )
                if end_index < len(segments):
                    bar_character = bars[len_bars - 1 - end_bar]
                    if bar_character != " ":
                        segments[end_index] = _Segment(
                            bar_character * width_thickness,
                            (
                                _Style(
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
                                    reverse=True,
                                )
                                if vertical
                                else _Style(
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
                                )
                            ),
                        )
            else:
                segments = [
                    _Segment(blank * width_thickness, _Style(bgcolor=back))
                ] * int(size)
                for i in range(start_index, end_index):
                    segments[i] = _Segment(
                        Chars.lower_3_8ths_block * width_thickness,
                        _Style(bgcolor=back, color=bar, meta=foreground_meta),
                    )
        else:
            style = _Style(bgcolor=back)
            segments = [_Segment(blank, style=style)] * int(size)
        if vertical:
            return Segments(segments, new_lines=True)
        else:
            return Segments(
                (segments + [_Segment.line()]) * thickness, new_lines=False
            )
