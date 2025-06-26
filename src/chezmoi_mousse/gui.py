# Patches the render_bar method to enable a slim horizontal scrollbar

from math import ceil
from pathlib import Path

from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.events import Click
from textual.screen import ModalScreen, Screen
from textual.scrollbar import ScrollBar, ScrollBarRender
from textual.theme import Theme
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

import chezmoi_mousse.theme
from chezmoi_mousse import FLOW
from chezmoi_mousse.containers import ContentSwitcherRight
from chezmoi_mousse.id_typing import (
    CharsEnum,
    CommandLogEntry,
    IdMixin,
    PaneEnum,
    SideStr,
    TabStr,
    ViewStr,
)
from chezmoi_mousse.main_tabs import (
    AddTab,
    ApplyTab,
    CommandLog,
    DoctorTab,
    ReAddTab,
)
from chezmoi_mousse.splash import LoadingScreen
from chezmoi_mousse.widgets import DiffView, GitLogView, PathView


class ModalView(ModalScreen[None], IdMixin):
    BINDINGS = [
        Binding(
            key="escape", action="dismiss", description="close", show=False
        )
    ]

    def __init__(
        self,
        path: Path,
        tab_name: TabStr = TabStr.apply_tab,
        view_name: str = ViewStr.path_view,
    ) -> None:
        IdMixin.__init__(self, tab_name)
        self.tab_name = tab_name
        self.view_name = view_name
        self.path = path
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.view_name == "path_view":
            yield PathView(view_id=self.view_name)
        elif self.view_name == "diff_view":
            yield DiffView(tab_name=self.tab_name, view_id=self.view_name)
        elif self.view_name == "git_log_view":
            yield GitLogView(view_id=self.view_name)

    def on_mount(self) -> None:
        self.add_class("modal-view")
        self.border_subtitle = "double click or escape key to close"

        if self.view_name == ViewStr.path_view:
            self.query_one(f"#{self.view_name}", PathView).path = self.path
        elif self.view_name == ViewStr.diff_view:
            self.query_one(f"#{self.view_name}", DiffView).path = self.path
        elif self.view_name == ViewStr.git_log_view:
            self.query_one(f"#{self.view_name}", GitLogView).path = self.path

        self.border_title = f"{self.path}"

    def on_click(self, event: Click) -> None:
        event.stop()
        if event.chain == 2:
            self.dismiss()


class MainScreen(Screen[None]):

    BINDINGS = [Binding(key="M,m", action="maximize", description="maximize")]

    def compose(self) -> ComposeResult:
        yield Header(icon=CharsEnum.burger.value)
        with TabbedContent():
            with TabPane("Apply", id=PaneEnum.apply.name):
                yield ApplyTab(tab_str=TabStr.apply_tab)
            with TabPane("Re-Add", id=PaneEnum.re_add.name):
                yield ReAddTab(tab_str=TabStr.re_add_tab)
            with TabPane("Add", id=PaneEnum.add.name):
                yield AddTab(tab_str=TabStr.add_tab)
            with TabPane("Doctor", id=PaneEnum.doctor.name):
                yield DoctorTab(tab_str=TabStr.doctor_tab)
            with TabPane("Diagram", id=PaneEnum.diagram.name):
                yield ScrollableContainer(
                    Static(FLOW, id=PaneEnum.diagram.name)
                )
            with TabPane("Log", id=PaneEnum.log.name):
                yield CommandLog(id="cmd_log", highlight=True, max_lines=20000)
        yield Footer()

    def on_mount(self) -> None:
        self.screen.focus()

    def action_maximize(self) -> None:
        active_pane = self.query_one(TabbedContent).active
        # tab id not known upon MainScreen init, so we init it here.
        id_mixin = IdMixin(tab_str=PaneEnum[active_pane].value)

        # Determine what view to show in the modal
        if id_mixin.tab_name in (TabStr.apply_tab, TabStr.re_add_tab):

            content_switcher_right = self.query_one(
                id_mixin.content_switcher_qid(SideStr.right),
                ContentSwitcherRight,
            )
            current_view_id = content_switcher_right.current
            right_switcher_widget = None
            if current_view_id:
                right_switcher_widget = content_switcher_right.get_child_by_id(
                    current_view_id
                )

            view_name = ViewStr.path_view
            path = getattr(right_switcher_widget, "path")

            if current_view_id == id_mixin.view_id(ViewStr.diff_view):
                view_name = ViewStr.diff_view
            elif current_view_id == id_mixin.view_id(ViewStr.git_log_view):
                view_name = ViewStr.git_log_view

            self.app.push_screen(
                ModalView(
                    tab_name=PaneEnum[active_pane].value,
                    view_name=view_name,
                    path=path,
                )
            )
        elif id_mixin.tab_name == TabStr.add_tab:
            self.notify("in add tab")
        elif id_mixin.tab_name == TabStr.doctor_tab:
            self.notify("in doctor tab")
        elif id_mixin.tab_name == TabStr.diagram_tab:
            self.notify("in diagram tab")
        elif id_mixin.tab_name == TabStr.log_tab:
            self.notify("in log tab")


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


class ChezmoiGUI(App[None]):

    CSS_PATH = "gui.tcss"

    SCREENS = {"main_screen": MainScreen}

    def on_mount(self) -> None:
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(chezmoi_mousse.theme.chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        self.push_screen(LoadingScreen(), callback=self.push_main_screen)
        self.watch(self, "theme", self.on_theme_change, init=False)

    def push_main_screen(
        self, splash_command_log: list[CommandLogEntry] | None
    ) -> None:
        CommandLog.splash_command_log = splash_command_log or []
        self.push_screen("main_screen")

    def on_theme_change(self, _: str, new_theme: str) -> None:
        new_theme_object: Theme | None = self.app.get_theme(new_theme)
        assert isinstance(new_theme_object, Theme)
        chezmoi_mousse.theme.vars = (
            new_theme_object.to_color_system().generate()
        )
