import dataclasses
from math import ceil
from typing import TYPE_CHECKING

from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style
from textual.app import App
from textual.binding import Binding
from textual.scrollbar import ScrollBar, ScrollBarRender
from textual.theme import Theme

from chezmoi_mousse import AppIds, CanvasName, Chars
from chezmoi_mousse.shared import (
    ContentsView,
    DiffView,
    GitLogPath,
    ReactiveHeader,
)

from .init_screen import InitScreen
from .install_help import InstallHelp
from .main_screen import MainScreen
from .splash import LoadingScreen
from .tabs.add_tab import AddTab
from .tabs.common.operate_info import OperateInfo
from .tabs.common.switchers import ViewSwitcher
from .tabs.common.trees import TreeBase

if TYPE_CHECKING:
    from chezmoi_mousse import Chezmoi, PreRunData, SplashData

__all__ = ["ChezmoiGUI"]

# TODO: implement 'chezmoi verify', if exit 0, display message in Tree
# widgets inform the user why the Tree widget is empty.
# TODO: implement spinner for commands taking a bit longer like operations.


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

    BINDINGS = [
        Binding(
            key="D,d",
            action="toggle_dry_run_mode",
            description="Remove --dry-run flag",
        )
    ]

    CSS_PATH = "gui.tcss"

    def __init__(self, pre_run_data: "PreRunData") -> None:
        self.chezmoi: "Chezmoi"
        self.pre_run_data = pre_run_data
        self.changes_enabled: bool = False
        self.chezmoi_found: bool = self.pre_run_data.chezmoi_found
        self.dev_mode: bool = self.pre_run_data.dev_mode
        self.force_init_screen: bool = self.pre_run_data.force_init_screen

        # Construct the ids for each screen
        self.init_screen_ids = AppIds(CanvasName.init_screen)
        self.install_help_screen_ids = AppIds(CanvasName.install_help_screen)
        self.loading_screen_ids = AppIds(CanvasName.loading_screen)
        self.main_screen_ids = AppIds(CanvasName.main_screen)
        self.op_screen_ids = AppIds(CanvasName.operate_screen)

        # Construct the ids for the tabs
        self.add_tab_ids = AppIds(CanvasName.add_tab)
        self.apply_tab_ids = AppIds(CanvasName.apply_tab)
        self.config_tab_ids = AppIds(CanvasName.config_tab)
        self.help_tab_ids = AppIds(CanvasName.help_tab)
        self.logs_tab_ids = AppIds(CanvasName.logs_tab)
        self.re_add_tab_ids = AppIds(CanvasName.re_add_tab)

        # Track the init screen
        self.init_screen_pushed: bool = False

        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        super().__init__()

    def on_mount(self) -> None:
        self.register_theme(chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"

        self.push_screen(
            LoadingScreen(ids=self.loading_screen_ids),
            callback=self.handle_splash_return_data,
        )

    def push_init_screen(self, return_data: "SplashData"):
        self.init_screen_pushed = True
        self.push_screen(
            InitScreen(ids=self.init_screen_ids, splash_data=return_data),
            callback=self.handle_splash_return_data,
        )

    def handle_splash_return_data(
        self, return_data: "SplashData | None"
    ) -> None:
        if return_data is None:
            self.push_screen(InstallHelp(ids=self.install_help_screen_ids))
            return
        elif (
            self.force_init_screen is True
            or return_data.cat_config.returncode != 0
        ) and self.init_screen_pushed is False:
            self.push_init_screen(return_data=return_data)
            return
        else:
            self.push_main_screen(return_data=return_data)

    def push_main_screen(self, return_data: "SplashData"):
        if return_data.init is None and self.dev_mode is True:
            self.notify(
                "Init screen was pushed but it returned None", severity="error"
            )
        elif (
            return_data.init is not None
            and self.init_screen_pushed is True
            and return_data.init.returncode != 0
        ):
            self.notify(
                "Init screen was pushed but return code was not zero.",
                severity="error",
            )

        dest_dir = return_data.parsed_config.dest_dir
        AddTab.destdir = dest_dir
        ContentsView.destDir = dest_dir
        DiffView.destDir = dest_dir
        GitLogPath.destDir = dest_dir
        MainScreen.destDir = dest_dir
        TreeBase.destDir = dest_dir
        ViewSwitcher.destDir = dest_dir

        OperateInfo.git_autocommit = return_data.parsed_config.git_autocommit
        OperateInfo.git_autopush = return_data.parsed_config.git_autopush

        self.push_screen(
            MainScreen(ids=self.main_screen_ids, splash_data=return_data)
        )

    def action_toggle_dry_run_mode(self) -> None:
        self.changes_enabled = not self.changes_enabled
        reactive_header = self.screen.query_exactly_one(ReactiveHeader)
        reactive_header.changes_enabled = self.changes_enabled

        # TODO: improve this quickly drafted implementation
        try:
            operate_info = self.screen.query_exactly_one(OperateInfo)
            operate_info.write_info_lines()
        except Exception:
            pass

        new_description = (
            "Add --dry-run flag"
            if self.changes_enabled is True
            else "Remove --dry-run flag"
        )

        for key, binding in self._bindings:
            if binding.action == "toggle_dry_run_mode":
                # Create a new binding with the updated description
                updated_binding = dataclasses.replace(
                    binding, description=new_description
                )
                # Update the bindings map
                if key in self._bindings.key_to_bindings:
                    bindings_list = self._bindings.key_to_bindings[key]
                    for i, b in enumerate(bindings_list):
                        if b.action == "toggle_dry_run_mode":
                            bindings_list[i] = updated_binding
                            break
                break
        self.refresh_bindings()


class CustomScrollBarRender(ScrollBarRender):
    # Used to monkey patch the textual ScrollBar.renderer method in ChezmoiGUI
    # __init__

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
