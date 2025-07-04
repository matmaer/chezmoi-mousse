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
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.scrollbar import ScrollBar, ScrollBarRender
from textual.theme import Theme
from textual.widget import Widget
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

import chezmoi_mousse.theme
from chezmoi_mousse import FLOW
from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.containers import ContentSwitcherRight
from chezmoi_mousse.id_typing import (
    CharsEnum,
    IdMixin,
    Location,
    PaneEnum,
    TabStr,
    TcssStr,
    ViewStr,
)
from chezmoi_mousse.main_tabs import (
    AddTab,
    ApplyTab,
    DoctorTab,
    LogTab,
    ReAddTab,
)
from chezmoi_mousse.splash import LoadingScreen
from chezmoi_mousse.widgets import ContentsView, DiffView, GitLogView


class MaximizedView(ModalScreen[None], IdMixin):
    BINDINGS = [
        Binding(
            key="escape", action="dismiss", description="close", show=False
        )
    ]

    def __init__(
        self,
        border_title_text: str,
        id_to_maximize: str | None,
        path: Path | None,
        tab_name: TabStr = TabStr.apply_tab,
    ) -> None:
        IdMixin.__init__(self, tab_name)
        self.border_title_text = border_title_text
        self.id_to_maximize = id_to_maximize
        self.path = path
        if self.path is not None:
            if self.path == chezmoi.dest_dir:
                self.border_title_text = f" {chezmoi.dest_dir} "
            else:
                self.border_title_text = (
                    f" {self.path.relative_to(chezmoi.dest_dir)} "
                )
        self.modal_view_id = "modal_view"
        self.modal_view_qid = f"#{self.modal_view_id}"
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.id_to_maximize == self.view_id(ViewStr.contents_view):
            yield ContentsView(view_id=self.modal_view_id)
        elif self.id_to_maximize == self.view_id(ViewStr.diff_view):
            yield DiffView(tab_name=self.tab_name, view_id=self.modal_view_id)
        elif self.id_to_maximize == self.view_id(ViewStr.git_log_view):
            yield GitLogView(view_id=self.modal_view_id)
        elif self.id_to_maximize == PaneEnum.diagram.name:
            yield ScrollableContainer(
                Static(
                    FLOW, id=self.modal_view_id, classes=TcssStr.flow_diagram
                )
            )

    def on_mount(self) -> None:
        self.add_class(TcssStr.modal_view)
        self.border_subtitle = " double click or escape key to close "

        if self.id_to_maximize == self.view_id(ViewStr.contents_view):
            self.query_one(self.modal_view_qid, ContentsView).path = self.path
        elif self.id_to_maximize == self.view_id(ViewStr.diff_view):
            self.query_one(self.modal_view_qid, DiffView).path = self.path
        elif self.id_to_maximize == self.view_id(ViewStr.git_log_view):
            self.query_one(self.modal_view_qid, GitLogView).path = self.path

        self.border_title = self.border_title_text

    def on_click(self, event: Click) -> None:
        event.stop()
        if event.chain == 2:
            self.dismiss()


class MainScreen(Screen[None]):

    BINDINGS = [
        Binding(key="M,m", action="maximize", description="maximize"),
        Binding(
            key="F,f",
            action="toggle_filter_slider",
            description="toggle-filters",
        ),
    ]

    # reactive var to track the current tab and refresh bindings when changed
    active_pane = reactive("apply", bindings=True)

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
                yield DoctorTab(id=TabStr.doctor_tab.value)
            with TabPane("Diagram", id=PaneEnum.diagram.name):
                yield ScrollableContainer(
                    Static(
                        FLOW,
                        id=PaneEnum.diagram.value,
                        classes=TcssStr.flow_diagram,
                    )
                )
            with TabPane("Log", id=PaneEnum.log.name):
                yield LogTab(
                    id=PaneEnum.log.value, markup=True, max_lines=20000
                )
        yield Footer()

    def on_mount(self) -> None:
        self.query_exactly_one(ApplyTab).focus()

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        self.active_pane = event.tab.id

        # Refresh bindings on the newly activated tab to ensure they reflect current state
        if event.tab.id in ("apply", "re_add"):
            # Get the tab widget and refresh its bindings
            tab_pane = self.query_one(f"#{event.tab.id}", TabPane)
            if tab_pane.children:
                tab_widget = tab_pane.children[0]
                # Focus the tab widget and use call_after_refresh to ensure mounting is complete
                tab_widget.focus()
                if hasattr(tab_widget, "refresh_bindings"):
                    self.call_after_refresh(tab_widget.refresh_bindings)

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:

        active_pane = self.query_one(TabbedContent).active

        if action == "maximize":
            # If no tab is active, return True because ApplyTab will be shown
            if not active_pane:
                return True
            # Once the app is running - guard against empty active_pane
            try:
                id_mixin = IdMixin(tab_str=PaneEnum[active_pane].value)
            except (KeyError, AttributeError):
                return True
            if (
                id_mixin.tab_name == TabStr.doctor_tab
                or id_mixin.tab_name == TabStr.log_tab
            ):
                return None  # show disabled binding
            return True

        elif action == "toggle_filter_slider":

            if not active_pane:
                return True  # Show at startup (apply tab will be active)
            if active_pane in ("apply", "re_add", "add"):
                return True
            else:
                return None  # show disabled binding

        return None  # show disabled binding

    def action_toggle_filter_slider(self) -> None:
        # merely find the corresponding method in the active tab ant call it
        active_pane = self.query_one(TabbedContent).active
        if active_pane in ("apply", "re_add", "add"):
            tab_pane = self.query_one(f"#{active_pane}", TabPane)
            tab_widget = tab_pane.children[0]
            if hasattr(tab_widget, "action_toggle_filter_slider"):
                getattr(tab_widget, "action_toggle_filter_slider")()

    def action_maximize(self) -> None:
        active_pane = self.query_one(TabbedContent).active
        # tab id not known upon MainScreen init, so we init it here.
        id_mixin = IdMixin(tab_str=PaneEnum[active_pane].value)

        # Initialize modal parameters
        tab_name = PaneEnum[active_pane].value
        id_to_maximize: str | None = None
        path_for_maximize: Path | None = None
        border_title_text: str = ""

        if id_mixin.tab_name in (TabStr.apply_tab, TabStr.re_add_tab):
            # Determine what view to show in the modal
            content_switcher_right = self.query_one(
                id_mixin.content_switcher_qid(Location.right),
                ContentSwitcherRight,
            )
            current_view_id: str | None = content_switcher_right.current

            if current_view_id:
                right_switcher_widget: Widget | None = (
                    content_switcher_right.get_child_by_id(current_view_id)
                )
                id_to_maximize = current_view_id
                path_for_maximize = getattr(right_switcher_widget, "path")

        elif id_mixin.tab_name == TabStr.add_tab:
            add_tab_contents_view = self.query_one(
                id_mixin.view_qid(ViewStr.contents_view), ContentsView
            )

            id_to_maximize = add_tab_contents_view.id
            path_for_maximize = getattr(add_tab_contents_view, "path")

        elif id_mixin.tab_name == TabStr.diagram_tab:
            id_to_maximize = PaneEnum.diagram.name
            border_title_text = " chezmoi diagram "

        self.app.push_screen(
            MaximizedView(
                tab_name=tab_name,
                id_to_maximize=id_to_maximize,
                path=path_for_maximize,
                border_title_text=border_title_text,
            )
        )


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

    def push_main_screen(self, splash_log: list[str] | None) -> None:
        LogTab.splash_log = splash_log
        self.push_screen("main_screen")

    def on_theme_change(self, _: str, new_theme: str) -> None:
        new_theme_object: Theme | None = self.app.get_theme(new_theme)
        assert isinstance(new_theme_object, Theme)
        chezmoi_mousse.theme.vars = (
            new_theme_object.to_color_system().generate()
        )
