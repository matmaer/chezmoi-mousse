"""Contains the main GUI application where the App class is being subclassed
and the MainScreen class which is rendered after the LoadingScreen has
completed running each chezmoi command."""

from math import ceil

from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.scrollbar import ScrollBar, ScrollBarRender
from textual.theme import Theme
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

import chezmoi_mousse.theme
from chezmoi_mousse import FLOW
from chezmoi_mousse.config import chars
from chezmoi_mousse.id_typing import MainTab
from chezmoi_mousse.main_tabs import (
    AddTab,
    ApplyTab,
    CommandLog,
    DoctorTab,
    ReAddTab,
)
from chezmoi_mousse.splash import LoadingScreen


class MainScreen(Screen):

    def compose(self) -> ComposeResult:
        yield Header(icon=chars.burger)
        with TabbedContent():
            with TabPane("Apply", id="apply_tab_pane"):
                yield ApplyTab(tab_key=MainTab.apply_tab)
            with TabPane("Re-Add", id="re_add_tab_pane"):
                yield ReAddTab(tab_key=MainTab.re_add_tab)
            with TabPane("Add", id="add_tab_pane"):
                yield AddTab(tab_key=MainTab.add_tab)
            with TabPane("Doctor", id="doctor_tab_pane"):
                yield DoctorTab(id="doctor_tab")
            with TabPane("Diagram", id="diagram_tab_pane"):
                yield ScrollableContainer(Static(FLOW, id="flow_diagram"))
            with TabPane("Log", id="rich_log_tab_pane"):
                yield CommandLog(
                    id="command_log", highlight=True, max_lines=20000
                )
        yield Footer()


class CustomScrollBarRender(ScrollBarRender):
    SLIM_HORIZONTAL_BAR = "▃"

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
            if vertical or cls.SLIM_HORIZONTAL_BAR is None:
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
                        cls.SLIM_HORIZONTAL_BAR * width_thickness,
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


class ChezmoiGUI(App):

    CSS_PATH = "gui.tcss"

    SCREENS = {"main_screen": MainScreen}

    def on_mount(self) -> None:
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(chezmoi_mousse.theme.chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        self.push_screen(LoadingScreen(), self.push_main_screen)
        self.watch(self, "theme", self.on_theme_change, init=False)

    def push_main_screen(self, new_splash_command_log) -> None:
        CommandLog.splash_command_log = new_splash_command_log
        self.push_screen("main_screen")

    def on_theme_change(self, _, new_theme):
        new_theme_object: Theme | None = self.app.get_theme(new_theme)
        assert isinstance(new_theme_object, Theme)
        chezmoi_mousse.theme.vars = (
            new_theme_object.to_color_system().generate()
        )
