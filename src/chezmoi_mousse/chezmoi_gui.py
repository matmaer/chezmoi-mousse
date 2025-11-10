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

from chezmoi_mousse import Chars

from .gui.chezmoi_init import ChezmoiInit
from .gui.install_help import InstallHelp
from .gui.main_screen import MainScreen
from .gui.operate import OperateInfo
from .gui.reach_out import ReachOutScreen
from .gui.reactive_header import ReactiveHeader
from .gui.splash import LoadingScreen
from .gui.tabs.add_tab import AddTab
from .gui.tabs.shared.contents_view import ContentsView
from .gui.tabs.shared.diff_view import DiffView
from .gui.tabs.shared.git_log_view import GitLogView
from .gui.tabs.shared.trees import TreeBase

if TYPE_CHECKING:
    from chezmoi_mousse import Chezmoi, CommandsData, PreRunData

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
        self.changes_enabled = False
        self.chezmoi_found = self.pre_run_data.chezmoi_found
        self.dev_mode = self.pre_run_data.dev_mode
        self.pretend_issue_found = False
        self.pretend_init_needed = False

        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        super().__init__()

    def on_mount(self) -> None:
        self.register_theme(chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"

        self.push_screen(
            LoadingScreen(chezmoi_found=self.chezmoi_found),
            callback=self.handle_splash_return_data,
        )

    def handle_splash_return_data(
        self, return_data: "CommandsData | None"
    ) -> None:
        if return_data is None:
            self.push_screen(InstallHelp())
            return
        # self.pretend_init_needed = True
        if (
            self.pretend_init_needed is True
            or return_data.cat_config.returncode != 0
        ):
            self.push_screen(ChezmoiInit(commands_data=return_data))
            return
        # self.pretend_issue_found = True
        if self.pretend_issue_found is True:
            self.push_screen(ReachOutScreen())
            return

        dest_dir = return_data.parsed_config.dest_dir
        AddTab.destdir = dest_dir
        ContentsView.destDir = dest_dir
        GitLogView.destDir = dest_dir
        DiffView.destDir = dest_dir
        TreeBase.destDir = dest_dir
        MainScreen.destDir = dest_dir

        OperateInfo.git_autocommit = return_data.parsed_config.git_autocommit
        OperateInfo.git_autopush = return_data.parsed_config.git_autopush

        self.push_screen(MainScreen(commands_data=return_data))

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
