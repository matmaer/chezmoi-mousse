"""Contains classes used as container components in main_tabs.py.

Rules:
- inherit from textual containers or is a ModalScreen
- are only reused in the main_tabs.py module
"""

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button, ContentSwitcher, Label, Switch

from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import filter_tooltips
from chezmoi_mousse.id_typing import (
    ButtonEnum,
    FilterEnum,
    IdMixin,
    Location,
    TabStr,
    TcssStr,
    TreeStr,
    ViewStr,
)
from chezmoi_mousse.widgets import (
    DiffView,
    ExpandedTree,
    FlatTree,
    GitLogView,
    ManagedTree,
    ContentsView,
)


class FilterSlider(VerticalGroup, IdMixin):

    def __init__(
        self, tab_str: TabStr, filters: tuple[FilterEnum, FilterEnum]
    ) -> None:
        IdMixin.__init__(self, tab_str)
        self.tab_str = tab_str
        self.top_filter = filters[0]
        self.bottom_filter = filters[1]
        super().__init__(
            id=self.filter_slider_id, classes=TcssStr.filters_vertical
        )

    def compose(self) -> ComposeResult:
        with HorizontalGroup(
            id=self.filter_horizontal_id(self.top_filter, Location.top),
            classes=(TcssStr.filter_horizontal_top),
        ):
            yield Switch(id=self.switch_id(self.top_filter))
            yield Label(
                self.top_filter.value, classes=TcssStr.filter_label
            ).with_tooltip(tooltip=filter_tooltips[self.top_filter.name])
        with HorizontalGroup(
            id=self.filter_horizontal_id(self.bottom_filter, Location.bottom),
            classes=(TcssStr.filter_horizontal_bottom),
        ):
            yield Switch(id=self.switch_id(self.bottom_filter))
            yield Label(
                self.bottom_filter.value, classes=TcssStr.filter_label
            ).with_tooltip(tooltip=filter_tooltips[self.bottom_filter.name])


class ButtonsHorizontal(HorizontalGroup, IdMixin):

    def __init__(
        self,
        tab_str: TabStr,
        *,
        buttons: tuple[ButtonEnum, ...],
        location: Location,
    ) -> None:
        IdMixin.__init__(self, tab_str)
        super().__init__(
            id=self.buttons_horizontal_id(location),
            classes=TcssStr.tab_buttons_horizontal,
        )
        self.buttons = buttons
        self.button_class: str
        self.location: Location = location
        if self.location == Location.bottom:
            self.button_class = "operate-button"
        else:
            self.button_class = "tab-button"

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(
                id=self.button_vertical_id(button_enum),
                classes=TcssStr.single_button_vertical,
            ):
                yield Button(
                    label=button_enum.value,
                    id=self.button_id(button_enum),
                    classes=self.button_class,
                )

    def on_mount(self) -> None:
        self.query_one(self.button_qid(self.buttons[0])).add_class(
            "last-clicked"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        lc = "last-clicked"
        for button_enum in self.buttons:
            self.query_one(self.button_qid(button_enum)).remove_class(lc)
        event.button.add_class(lc)


class ContentSwitcherLeft(ContentSwitcher, IdMixin):

    def __init__(self, tab_str: TabStr):
        IdMixin.__init__(self, tab_str)
        self.tab_str = tab_str
        super().__init__(
            id=self.content_switcher_id(Location.left),
            initial=self.tree_id(TreeStr.managed_tree),
            classes=f"{TcssStr.content_switcher_left} {TcssStr.top_border_title}",
        )

    def on_mount(self) -> None:
        self.border_title = chezmoi.dest_dir_str

    def compose(self) -> ComposeResult:
        yield ManagedTree(self.tab_str)
        yield FlatTree(self.tab_str)
        yield ExpandedTree(self.tab_str)


class ContentSwitcherRight(ContentSwitcher, IdMixin):
    """Reusable ContentSwitcher for the right panel with path view widgets."""

    def __init__(self, tab_str: TabStr):
        IdMixin.__init__(self, tab_str)
        super().__init__(
            id=self.content_switcher_id(Location.right),
            initial=self.view_id(ViewStr.diff_view),
            classes=f"{TcssStr.content_switcher_right} {TcssStr.top_border_title}",
        )

    def on_mount(self) -> None:
        self.border_title = chezmoi.dest_dir_str

    def compose(self) -> ComposeResult:
        yield DiffView(
            tab_name=self.tab_name, view_id=self.view_id(ViewStr.diff_view)
        )
        yield ContentsView(view_id=self.view_id(ViewStr.contents_view))
        yield GitLogView(view_id=self.view_id(ViewStr.git_log_view))
