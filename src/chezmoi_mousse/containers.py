"""Contains classes used as container components in main_tabs.py.

Rules:
- inherit from textual containers or is a ModalScreen
- are only reused in the main_tabs.py module
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup, Vertical, VerticalGroup
from textual.events import Click
from textual.screen import ModalScreen
from textual.widgets import Button, ContentSwitcher, Label, Static, Switch

from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import filter_tooltips
from chezmoi_mousse.id_typing import (
    ButtonEnum,
    CornerStr,
    FilterEnum,
    IdMixin,
    SideStr,
    TabEnum,
    TreeStr,
    ViewEnum,
)
from chezmoi_mousse.widgets import (
    DiffView,
    ExpandedTree,
    FlatTree,
    GitLogView,
    ManagedTree,
    PathView,
)


class ModalView(ModalScreen[PathView | DiffView | GitLogView], IdMixin):
    BINDINGS = [
        Binding(
            key="escape", action="dismiss", description="close", show=False
        )
    ]
    # current_path: Path
    current_tab: TabEnum = TabEnum.apply_tab
    current_view: ViewEnum = ViewEnum.path_view
    current_path: Path | None = None

    def __init__(self) -> None:
        self.current_path = chezmoi.dest_dir
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.current_view == ViewEnum.path_view:
            path_view = PathView(
                view_id=f"{self.current_tab}_{self.current_view.name}_modal_view"
            )
            # path_view.path = self.current_path
            yield path_view
        elif self.current_view == ViewEnum.diff_view:
            diff_view = DiffView(
                tab_name=self.current_tab.name,
                view_id=f"{self.current_tab.name}_{self.current_view.name}_modal_view",
            )
            # diff_view.path = self.current_path
            yield diff_view
        elif self.current_view == ViewEnum.git_log_view:
            git_log_view = GitLogView(
                view_id=f"{self.current_tab.name}_{self.current_view.name}_modal_view"
            )
            # git_log_view.path = self.current_path
            yield git_log_view
        return Static("no content to show", id="no-content")

    def on_mount(self) -> None:
        self.add_class("doctor-modal")
        self.border_subtitle = "double click or escape key to close"
        self.border_title = f"{self.current_tab} {self.current_view}"
        # self.content_to_show = self.update_content()

    # def update_content(self):

    def on_click(self, event: Click) -> None:
        event.stop()
        if event.chain == 2:
            self.dismiss()


class FilterSlider(VerticalGroup, IdMixin):

    def __init__(
        self, tab_enum: TabEnum, filters: tuple[FilterEnum, FilterEnum]
    ) -> None:
        IdMixin.__init__(self, tab_enum)
        self.tab_enum = tab_enum
        self.filters = filters
        super().__init__(id=self.filter_slider_id, classes="filters-vertical")

    def compose(self) -> ComposeResult:
        for filter_enum in self.filters:
            with HorizontalGroup(
                id=self.filter_horizontal_id(filter_enum),
                classes=(
                    "filter-horizontal padding-bottom-once"
                    if filter_enum == self.filters[0]
                    else "filter-horizontal"
                ),
            ):
                yield Switch(id=self.switch_id(filter_enum))
                yield Label(
                    filter_enum.value, classes="filter-label"
                ).with_tooltip(tooltip=filter_tooltips[filter_enum.name])


class ButtonsTopLeft(HorizontalGroup, IdMixin):

    def __init__(self, tab_enum: TabEnum) -> None:
        IdMixin.__init__(self, tab_enum)
        super().__init__(
            id=self.buttons_horizontal_id(CornerStr.top_left),
            classes="tab-buttons-horizontal",
        )
        self.buttons = (ButtonEnum.tree_btn, ButtonEnum.list_btn)

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(
                id=self.button_vertical_id(button_enum),
                classes="single-button-vertical",
            ):
                yield Button(
                    label=button_enum.value,
                    id=self.button_id(button_enum),
                    classes="tab-button",
                )

    def on_mount(self) -> None:
        self.query_one(self.button_qid(ButtonEnum.tree_btn)).add_class(
            "last-clicked"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        lc = "last-clicked"
        for button_enum in self.buttons:
            self.query_one(self.button_qid(button_enum)).remove_class(lc)
        event.button.add_class(lc)


class ButtonsTopRight(HorizontalGroup, IdMixin):
    def __init__(self, tab_enum: TabEnum) -> None:
        IdMixin.__init__(self, tab_enum)
        super().__init__(
            id=self.buttons_horizontal_id(CornerStr.top_right),
            classes="tab-buttons-horizontal",
        )
        self.buttons = (
            ButtonEnum.contents_btn,
            ButtonEnum.diff_btn,
            ButtonEnum.git_log_btn,
        )

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(
                id=self.button_vertical_id(button_enum),
                classes="single-button-vertical",
            ):
                yield Button(
                    label=button_enum.value,
                    id=self.button_id(button_enum),
                    classes="tab-button",
                )

    def on_mount(self) -> None:
        self.query_one(self.button_qid(ButtonEnum.contents_btn)).add_class(
            "last-clicked"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        lc = "last-clicked"
        for button_enum in self.buttons:
            self.query_one(self.button_qid(button_enum)).remove_class(lc)
        event.button.add_class(lc)


class ContentSwitcherLeft(ContentSwitcher, IdMixin):
    """Reusable ContentSwitcher for the left panel with tree widgets."""

    def __init__(self, tab_enum: TabEnum):
        IdMixin.__init__(self, tab_enum)
        self.tab_enum = tab_enum
        super().__init__(
            id=self.content_switcher_id(SideStr.left),
            initial=self.tree_id(TreeStr.managed_tree),
            classes="content-switcher-left top-border-title",
        )

    def on_mount(self) -> None:
        self.border_title = chezmoi.dest_dir_str

    def compose(self) -> ComposeResult:
        yield ManagedTree(self.tab_enum)
        yield FlatTree(self.tab_enum)
        yield ExpandedTree(self.tab_enum)


class ContentSwitcherRight(ContentSwitcher, IdMixin):
    """Reusable ContentSwitcher for the right panel with path view widgets."""

    def __init__(self, tab_enum: TabEnum):
        IdMixin.__init__(self, tab_enum)
        self.tab_name = tab_enum.name
        super().__init__(
            id=self.content_switcher_id(SideStr.right),
            initial=self.view_id(ViewEnum.path_view),
            classes="content-switcher-right top-border-title",
        )

    def on_mount(self) -> None:
        self.border_title = chezmoi.dest_dir_str

    def compose(self) -> ComposeResult:
        yield PathView(view_id=self.view_id(ViewEnum.path_view))
        yield DiffView(
            tab_name=self.tab_name, view_id=self.view_id(ViewEnum.diff_view)
        )
        yield GitLogView(view_id=self.view_id(ViewEnum.git_log_view))
