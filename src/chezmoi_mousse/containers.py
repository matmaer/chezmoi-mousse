"""Contains classes used as container components in main_tabs.py.

These classes
- inherit from textual containers
- are only reused in the main_tabs.py module
- don't inherit from widgets which are not containers
- only import from chezmoi_mousse config.py and mouse_types.py modules
"""

from textual.app import ComposeResult
from textual.containers import (
    Container,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.widgets import Button, ContentSwitcher, Label, Switch

from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import filter_tooltips
from chezmoi_mousse.id_typing import (
    EventProtocol,
    ComponentStr,
    CornerStr,
    FilterEnum,
    IdMixin,
    TabEnum,
    ButtonEnum,
    SideStr,
)
from chezmoi_mousse.widgets import (
    DiffView,
    ExpandedTree,
    FlatTree,
    GitLog,
    ManagedTree,
    PathView,
)


class EventMixin:

    def on_button_pressed(self: EventProtocol, event: Button.Pressed) -> None:
        # Tree/List Switch
        if event.button.id == self.button_id(ButtonEnum.tree_btn):
            expand_all_switch = self.query_one(
                f"#{self.filter_switch_id(FilterEnum.expand_all)}", Switch
            )
            expand_all_switch.disabled = False
            if expand_all_switch.value:
                self.query_one(
                    f"#{self.content_switcher_id(SideStr.left)}",
                    ContentSwitcher,
                ).current = self.component_id(ComponentStr.expanded_tree)
            else:
                self.query_one(
                    f"#{self.content_switcher_id(SideStr.left)}",
                    ContentSwitcher,
                ).current = self.component_id(ComponentStr.managed_tree)
        elif event.button.id == self.button_id(ButtonEnum.list_btn):
            self.query_one(
                f"#{self.content_switcher_id(SideStr.left)}", ContentSwitcher
            ).current = self.component_id(ComponentStr.flat_tree)
            self.query_one(
                f"#{self.filter_switch_id(FilterEnum.expand_all)}", Switch
            ).disabled = True
        # Contents/Diff/GitLog Switch
        elif event.button.id == self.button_id(ButtonEnum.contents_btn):
            self.query_one(
                f"#{self.content_switcher_id(SideStr.right)}", ContentSwitcher
            ).current = self.component_id(ComponentStr.path_view)
        elif event.button.id == self.button_id(ButtonEnum.diff_btn):
            self.query_one(
                f"#{self.content_switcher_id(SideStr.right)}", ContentSwitcher
            ).current = self.component_id(ComponentStr.diff_view)
        elif event.button.id == self.button_id(ButtonEnum.git_log_btn):
            self.query_one(
                f"#{self.content_switcher_id(SideStr.right)}", ContentSwitcher
            ).current = self.component_id(ComponentStr.git_log)

    def on_tree_node_selected(
        self: EventProtocol, event: ManagedTree.NodeSelected
    ) -> None:
        assert event.node.data is not None
        self.query_one(
            f"#{self.content_switcher_id(SideStr.right)}", Container
        ).border_title = (
            f"{event.node.data.path.relative_to(chezmoi.dest_dir)}"
        )
        self.query_one(
            f"#{self.component_id(ComponentStr.path_view)}", PathView
        ).path = event.node.data.path
        self.query_one(
            f"#{self.component_id(ComponentStr.diff_view)}", DiffView
        ).path = event.node.data.path
        self.query_one(
            f"#{self.component_id(ComponentStr.git_log)}", GitLog
        ).path = event.node.data.path

    def on_switch_changed(self: EventProtocol, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.filter_switch_id(FilterEnum.unchanged):
            self.query_one(
                f"#{self.component_id(ComponentStr.expanded_tree)}",
                ExpandedTree,
            ).unchanged = event.value
            self.query_one(
                f"#{self.component_id(ComponentStr.managed_tree)}", ManagedTree
            ).unchanged = event.value
            self.query_one(
                f"#{self.component_id(ComponentStr.flat_tree)}", FlatTree
            ).unchanged = event.value
        elif event.switch.id == self.filter_switch_id(FilterEnum.expand_all):
            if event.value:
                self.query_one(
                    f"#{self.content_switcher_id(SideStr.left)}",
                    ContentSwitcher,
                ).current = self.component_id(ComponentStr.expanded_tree)
            else:
                self.query_one(
                    f"#{self.content_switcher_id(SideStr.left)}",
                    ContentSwitcher,
                ).current = self.component_id(ComponentStr.managed_tree)


class FilterSlider(VerticalGroup, IdMixin):

    def __init__(
        self, tab_key: TabEnum, filters: tuple[FilterEnum, FilterEnum]
    ) -> None:
        IdMixin.__init__(self, tab_key)
        self.tab_key = tab_key
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
                yield Switch(id=self.filter_switch_id(filter_enum))
                yield Label(
                    filter_enum.value, classes="filter-label"
                ).with_tooltip(tooltip=filter_tooltips[filter_enum.name])


class ButtonsTopLeft(HorizontalGroup, IdMixin):

    def __init__(self, tab_key: TabEnum, **kwargs) -> None:
        IdMixin.__init__(self, tab_key)
        super().__init__(
            id=self.buttons_horizontal_id(CornerStr.top_left),
            classes="tab-buttons-horizontal",
            **kwargs,
        )

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.button_vertical_id(ButtonEnum.tree_btn),
            classes="single-button-vertical",
        ):
            yield Button(
                label=ButtonEnum.tree_btn.value,
                id=self.button_id(ButtonEnum.tree_btn),
                classes="tab-button",
            )
        with Vertical(
            id=self.button_vertical_id(ButtonEnum.list_btn),
            classes="single-button-vertical",
        ):
            yield Button(
                label=ButtonEnum.list_btn.value,
                id=self.button_id(ButtonEnum.list_btn),
                classes="tab-button",
            )

    def on_mount(self) -> None:
        self.query_one(f"#{self.button_id(ButtonEnum.tree_btn)}").add_class(
            "last-clicked"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        lc = "last-clicked"
        if event.button.id == self.button_id(ButtonEnum.tree_btn):
            self.query_one(
                f"#{self.button_id(ButtonEnum.list_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(ButtonEnum.tree_btn)}"
            ).add_class(lc)
        elif event.button.id == self.button_id(ButtonEnum.list_btn):
            self.query_one(
                f"#{self.button_id(ButtonEnum.tree_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(ButtonEnum.list_btn)}"
            ).add_class(lc)


class ButtonsTopRight(HorizontalGroup, IdMixin):
    def __init__(self, tab_key: TabEnum, **kwargs) -> None:
        IdMixin.__init__(self, tab_key)
        super().__init__(
            id=self.buttons_horizontal_id(CornerStr.top_right),
            classes="tab-buttons-horizontal",
            **kwargs,
        )

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.button_vertical_id(ButtonEnum.contents_btn),
            classes="single-button-vertical",
        ):
            yield Button(
                label=ButtonEnum.contents_btn.value,
                id=self.button_id(ButtonEnum.contents_btn),
                classes="tab-button",
            )
        with Vertical(
            id=self.button_vertical_id(ButtonEnum.diff_btn),
            classes="single-button-vertical",
        ):
            yield Button(
                label=ButtonEnum.diff_btn.value,
                id=self.button_id(ButtonEnum.diff_btn),
                classes="tab-button",
            )
        with Vertical(
            id=self.button_vertical_id(ButtonEnum.git_log_btn),
            classes="single-button-vertical",
        ):
            yield Button(
                label=ButtonEnum.git_log_btn.value,
                id=self.button_id(ButtonEnum.git_log_btn),
                classes="tab-button",
            )

    def on_mount(self) -> None:
        self.query_one(
            f"#{self.button_id(ButtonEnum.contents_btn)}"
        ).add_class("last-clicked")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        lc = "last-clicked"
        if event.button.id == self.button_id(ButtonEnum.contents_btn):
            self.query_one(
                f"#{self.button_id(ButtonEnum.diff_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(ButtonEnum.git_log_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(ButtonEnum.contents_btn)}"
            ).add_class(lc)
        elif event.button.id == self.button_id(ButtonEnum.diff_btn):
            self.query_one(
                f"#{self.button_id(ButtonEnum.contents_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(ButtonEnum.git_log_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(ButtonEnum.diff_btn)}"
            ).add_class(lc)
        elif event.button.id == self.button_id(ButtonEnum.git_log_btn):
            self.query_one(
                f"#{self.button_id(ButtonEnum.contents_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(ButtonEnum.diff_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(ButtonEnum.git_log_btn)}"
            ).add_class(lc)


class ContentSwitcherLeft(ContentSwitcher, IdMixin):
    """Reusable ContentSwitcher for the left panel with tree widgets."""

    def __init__(self, tab_key: TabEnum, **kwargs):
        IdMixin.__init__(self, tab_key)
        self.tab_key = tab_key
        super().__init__(
            id=self.content_switcher_id(SideStr.left),
            initial=self.component_id(ComponentStr.managed_tree),
            classes="content-switcher-left top-border-title",
            **kwargs,
        )

    def on_mount(self) -> None:
        self.border_title = chezmoi.dest_dir_str

    def compose(self) -> ComposeResult:
        yield ManagedTree(self.tab_key, classes="tree-widget")
        yield FlatTree(self.tab_key, classes="tree-widget")
        yield ExpandedTree(self.tab_key, classes="tree-widget")


class ContentSwitcherRight(ContentSwitcher, IdMixin):
    """Reusable ContentSwitcher for the right panel with path view widgets."""

    def __init__(self, tab_key: TabEnum, **kwargs):
        IdMixin.__init__(self, tab_key)
        self.tab_key = tab_key
        super().__init__(
            id=self.content_switcher_id(SideStr.right),
            initial=self.component_id(ComponentStr.path_view),
            classes="content-switcher-right top-border-title",
            **kwargs,
        )

    def on_mount(self) -> None:
        self.border_title = chezmoi.dest_dir_str

    def compose(self) -> ComposeResult:
        yield PathView(self.tab_key)
        yield DiffView(self.tab_key)
        yield GitLog(self.tab_key)
