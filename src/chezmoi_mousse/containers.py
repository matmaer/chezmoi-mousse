"""Contains classes used as container components in main_tabs.py.

These classes
- inherit from textual containers
- are only reused in the main_tabs.py module
- don't inherit from widgets which are not containers
- only import from chezmoi_mousse config.py and mouse_types.py modules
"""

from textual.app import ComposeResult
from textual.containers import Container, HorizontalGroup, Vertical
from textual.widgets import Button, ContentSwitcher, Label, Switch

from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import filter_tooltips
from chezmoi_mousse.id_typing import (
    CommonTabEvents,
    Component,
    Corner,
    Filter,
    IdMixin,
    MainTab,
    TabButton,
    TabSide,
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

    def on_button_pressed(
        self: CommonTabEvents, event: Button.Pressed
    ) -> None:
        assert event.button.id is not None
        # Tree/List Switch
        if event.button.id == self.button_id(TabButton.tree_btn):
            expand_all_switch = self.query_one(
                f"#{self.filter_switch_id(Filter.expand_all.name)}", Switch
            )
            expand_all_switch.disabled = False
            if expand_all_switch.value:
                self.query_one(
                    f"#{self.content_switcher_id(TabSide.left)}",
                    ContentSwitcher,
                ).current = self.component_id(Component.expanded_tree)
            else:
                self.query_one(
                    f"#{self.content_switcher_id(TabSide.left)}",
                    ContentSwitcher,
                ).current = self.component_id(Component.managed_tree)
        elif event.button.id == self.button_id(TabButton.list_btn):
            self.query_one(
                f"#{self.content_switcher_id(TabSide.left)}", ContentSwitcher
            ).current = self.component_id(Component.flat_tree)
            self.query_one(
                f"#{self.filter_switch_id(Filter.expand_all.name)}", Switch
            ).disabled = True
        # Contents/Diff/GitLog Switch
        elif event.button.id == self.button_id(TabButton.contents_btn):
            self.query_one(
                f"#{self.content_switcher_id(TabSide.right)}", ContentSwitcher
            ).current = self.component_id(Component.path_view)
        elif event.button.id == self.button_id(TabButton.diff_btn):
            self.query_one(
                f"#{self.content_switcher_id(TabSide.right)}", ContentSwitcher
            ).current = self.component_id(Component.diff_view)
        elif event.button.id == self.button_id(TabButton.git_log_btn):
            self.query_one(
                f"#{self.content_switcher_id(TabSide.right)}", ContentSwitcher
            ).current = self.component_id(Component.git_log)

    def on_tree_node_selected(
        self: CommonTabEvents, event: ManagedTree.NodeSelected
    ) -> None:
        assert event.node.data is not None
        self.query_one(
            f"#{self.content_switcher_id(TabSide.right)}", Container
        ).border_title = (
            f"{event.node.data.path.relative_to(chezmoi.dest_dir)}"
        )
        self.query_one(
            f"#{self.component_id(Component.path_view)}", PathView
        ).path = event.node.data.path
        self.query_one(
            f"#{self.component_id(Component.diff_view)}", DiffView
        ).path = event.node.data.path
        self.query_one(
            f"#{self.component_id(Component.git_log)}", GitLog
        ).path = event.node.data.path

    def on_switch_changed(
        self: CommonTabEvents, event: Switch.Changed
    ) -> None:
        event.stop()
        if event.switch.id == self.filter_switch_id("unchanged"):
            self.query_one(
                f"#{self.component_id(Component.expanded_tree)}", ExpandedTree
            ).unchanged = event.value
            self.query_one(
                f"#{self.component_id(Component.managed_tree)}", ManagedTree
            ).unchanged = event.value
            self.query_one(
                f"#{self.component_id(Component.flat_tree)}", FlatTree
            ).unchanged = event.value
        elif event.switch.id == self.filter_switch_id("expand_all"):
            if event.value:
                self.query_one(
                    f"#{self.content_switcher_id(TabSide.left)}",
                    ContentSwitcher,
                ).current = self.component_id(Component.expanded_tree)
            else:
                self.query_one(
                    f"#{self.content_switcher_id(TabSide.left)}",
                    ContentSwitcher,
                ).current = self.component_id(Component.managed_tree)


class FilterSwitch(HorizontalGroup, IdMixin):

    def __init__(self, tab_key: MainTab, filter: Filter, **kwargs) -> None:
        IdMixin.__init__(self, tab_key)
        self.filter_name = filter.name
        self.filter_label = filter.value
        super().__init__(id=self.filter_horizontal_id(filter.name), **kwargs)

    def compose(self) -> ComposeResult:
        yield Switch(id=self.filter_switch_id(self.filter_name), value=False)
        yield Label(self.filter_label, classes="filter-label").with_tooltip(
            tooltip=filter_tooltips[self.filter_name]
        )


class TabButtonsLeft(HorizontalGroup, IdMixin):

    def __init__(self, tab_key: MainTab, **kwargs) -> None:
        IdMixin.__init__(self, tab_key)
        super().__init__(
            id=self.buttons_horizontal_id(Corner.top_left),
            classes="tab-buttons-horizontal",
            **kwargs,
        )

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.button_vertical_id(TabButton.tree_btn),
            classes="single-button-vertical",
        ):
            yield Button(
                label=TabButton.tree_btn.value,
                id=self.button_id(TabButton.tree_btn),
                classes="tab-button",
            )
        with Vertical(
            id=self.button_vertical_id(TabButton.list_btn),
            classes="single-button-vertical",
        ):
            yield Button(
                label=TabButton.list_btn.value,
                id=self.button_id(TabButton.list_btn),
                classes="tab-button",
            )

    def on_mount(self) -> None:
        self.query_one(f"#{self.button_id(TabButton.tree_btn)}").add_class(
            "last-clicked"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        lc = "last-clicked"
        if event.button.id == self.button_id(TabButton.tree_btn):
            self.query_one(
                f"#{self.button_id(TabButton.list_btn)}"
            ).remove_class(lc)
            self.query_one(f"#{self.button_id(TabButton.tree_btn)}").add_class(
                lc
            )
        elif event.button.id == self.button_id(TabButton.list_btn):
            self.query_one(
                f"#{self.button_id(TabButton.tree_btn)}"
            ).remove_class(lc)
            self.query_one(f"#{self.button_id(TabButton.list_btn)}").add_class(
                lc
            )


class TabButtonsRight(HorizontalGroup, IdMixin):
    def __init__(self, tab_key: MainTab, **kwargs) -> None:
        IdMixin.__init__(self, tab_key)
        super().__init__(
            id=self.buttons_horizontal_id(Corner.top_right),
            classes="tab-buttons-horizontal",
            **kwargs,
        )

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.button_vertical_id(TabButton.contents_btn),
            classes="single-button-vertical",
        ):
            yield Button(
                label=TabButton.contents_btn.value,
                id=self.button_id(TabButton.contents_btn),
                classes="tab-button",
            )
        with Vertical(
            id=self.button_vertical_id(TabButton.diff_btn),
            classes="single-button-vertical",
        ):
            yield Button(
                label=TabButton.diff_btn.value,
                id=self.button_id(TabButton.diff_btn),
                classes="tab-button",
            )
        with Vertical(
            id=self.button_vertical_id(TabButton.git_log_btn),
            classes="single-button-vertical",
        ):
            yield Button(
                label=TabButton.git_log_btn.value,
                id=self.button_id(TabButton.git_log_btn),
                classes="tab-button",
            )

    def on_mount(self) -> None:
        self.query_one(f"#{self.button_id(TabButton.contents_btn)}").add_class(
            "last-clicked"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        lc = "last-clicked"
        if event.button.id == self.button_id(TabButton.contents_btn):
            self.query_one(
                f"#{self.button_id(TabButton.diff_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(TabButton.git_log_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(TabButton.contents_btn)}"
            ).add_class(lc)
        elif event.button.id == self.button_id(TabButton.diff_btn):
            self.query_one(
                f"#{self.button_id(TabButton.contents_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(TabButton.git_log_btn)}"
            ).remove_class(lc)
            self.query_one(f"#{self.button_id(TabButton.diff_btn)}").add_class(
                lc
            )
        elif event.button.id == self.button_id(TabButton.git_log_btn):
            self.query_one(
                f"#{self.button_id(TabButton.contents_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(TabButton.diff_btn)}"
            ).remove_class(lc)
            self.query_one(
                f"#{self.button_id(TabButton.git_log_btn)}"
            ).add_class(lc)


class ContentSwitcherLeft(ContentSwitcher, IdMixin):
    """Reusable ContentSwitcher for the left panel with tree widgets."""

    def __init__(self, tab_key: MainTab, **kwargs):
        IdMixin.__init__(self, tab_key)
        self.tab_key = tab_key
        super().__init__(
            id=self.content_switcher_id(TabSide.left),
            initial=self.component_id(Component.managed_tree),
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

    def __init__(self, tab_key: MainTab, **kwargs):
        IdMixin.__init__(self, tab_key)
        self.tab_key = tab_key
        super().__init__(
            id=self.content_switcher_id(TabSide.right),
            initial=self.component_id(Component.path_view),
            classes="content-switcher-right top-border-title",
            **kwargs,
        )

    def on_mount(self) -> None:
        self.border_title = chezmoi.dest_dir_str

    def compose(self) -> ComposeResult:
        yield PathView(self.tab_key)
        yield DiffView(self.tab_key)
        yield GitLog(self.tab_key)
