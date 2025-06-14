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
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.widgets import Button, ContentSwitcher, Label, Switch


from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.widgets import (
    DiffView,
    ExpandedTree,
    FlatTree,
    GitLog,
    ManagedTree,
    PathView,
    TabButton,
    TabIdMixin,
)

from chezmoi_mousse.config import filter_data
from chezmoi_mousse.type_aliases import FilterName, TabLabel


class FilterSwitch(HorizontalGroup, TabIdMixin):

    def __init__(
        self, tab: TabLabel, *, filter_name: FilterName, **kwargs
    ) -> None:
        TabIdMixin.__init__(self, tab)
        self.filter_name: FilterName = filter_name
        self.label = filter_data[self.filter_name].label
        super().__init__(id=self.filter_horizontal_id(filter_name), **kwargs)

    def compose(self) -> ComposeResult:
        yield Switch(id=self.filter_switch_id(self.filter_name))
        yield Label(
            filter_data[self.filter_name].label,
            id=self.filter_label_id(self.filter_name),
            classes="filter-label",
        ).with_tooltip(tooltip=filter_data[self.filter_name].tooltip)


class TreeFilterSlider(VerticalGroup, TabIdMixin):

    def __init__(self, tab: TabLabel) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(id=self.filter_slider_id, classes="filters-vertical")

    def compose(self) -> ComposeResult:
        yield FilterSwitch(
            self.tab,
            filter_name="unchanged",
            classes="filter-horizontal padding-bottom-once",
        )
        # TODO: fix unchanged filter not working when expand_all is on
        yield FilterSwitch(
            self.tab, filter_name="expand_all", classes="filter-horizontal"
        )


class TreeTabSwitchers(Horizontal, TabIdMixin):

    def __init__(self, tab: TabLabel, **kwargs) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_vertical_id("Left"), classes="tab-left-vertical"
        ):
            with HorizontalGroup(
                id=self.buttons_horizontal_id("TopLeft"),
                classes="tab-buttons-horizontal",
            ):
                with Vertical(
                    id=self.button_vertical_id("Tree"),
                    classes="single-button-vertical",
                ):
                    yield TabButton(
                        self.tab, button_label="Tree", classes="tab-button"
                    )
                with Vertical(
                    id=self.button_vertical_id("List"),
                    classes="single-button-vertical",
                ):
                    yield TabButton(
                        self.tab, button_label="List", classes="tab-button"
                    )
            with ContentSwitcher(
                id=self.content_switcher_id("Left"),
                initial=self.component_id("ManagedTree"),
                classes="content-switcher-left top-border-title",
            ):
                yield ManagedTree(self.tab, classes="tree-widget")
                yield FlatTree(self.tab, classes="tree-widget")
                yield ExpandedTree(self.tab, classes="tree-widget")

        with Vertical(
            id=self.tab_vertical_id("Right"), classes="tab-right-vertical"
        ):
            with HorizontalGroup(
                id=self.buttons_horizontal_id("TopRight"),
                classes="tab-buttons-horizontal",
            ):
                with Vertical(
                    id=self.button_vertical_id("Contents"),
                    classes="single-button-vertical",
                ):
                    yield TabButton(
                        self.tab, button_label="Contents", classes="tab-button"
                    )
                with Vertical(
                    id=self.button_vertical_id("Diff"),
                    classes="single-button-vertical",
                ):
                    yield TabButton(
                        self.tab, button_label="Diff", classes="tab-button"
                    )
                with Vertical(
                    id=self.button_vertical_id("Git-Log"),
                    classes="single-button-vertical",
                ):
                    yield TabButton(
                        self.tab, button_label="Git-Log", classes="tab-button"
                    )

            with ContentSwitcher(
                id=self.content_switcher_id("Right"),
                initial=self.component_id("PathView"),
                classes="content-switcher-right top-border-title",
            ):
                yield PathView(self.tab, classes="path-view")
                yield DiffView(self.tab, classes="diff-view")
                yield GitLog(self.tab, classes="git-log")

        yield TreeFilterSlider(self.tab)

    def on_mount(self) -> None:
        self.query_one(f"#{self.button_id('Tree')}").add_class("last-clicked")
        self.query_one(
            f"#{self.content_switcher_id('Left')}", ContentSwitcher
        ).border_title = chezmoi.dest_dir_str_spaced
        self.query_one(f"#{self.button_id('Contents')}").add_class(
            "last-clicked"
        )
        self.query_one(
            f"#{self.content_switcher_id('Right')}", ContentSwitcher
        ).border_title = " path view "

    def update_button_classes(self, button_id: str) -> None:
        lc = "last-clicked"
        if button_id == self.button_id("Tree"):
            self.query_one(f"#{self.button_id('List')}").remove_class(lc)
            self.query_one(f"#{self.button_id('Tree')}").add_class(lc)
        elif button_id == self.button_id("List"):
            self.query_one(f"#{self.button_id('Tree')}").remove_class(lc)
            self.query_one(f"#{self.button_id('List')}").add_class(lc)
        elif button_id == self.button_id("Contents"):
            self.query_one(f"#{self.button_id('Diff')}").remove_class(lc)
            self.query_one(f"#{self.button_id('Git-Log')}").remove_class(lc)
            self.query_one(f"#{self.button_id('Contents')}").add_class(lc)
        elif button_id == self.button_id("Diff"):
            self.query_one(f"#{self.button_id('Contents')}").remove_class(lc)
            self.query_one(f"#{self.button_id('Git-Log')}").remove_class(lc)
            self.query_one(f"#{self.button_id('Diff')}").add_class(lc)
        elif button_id == self.button_id("Git-Log"):
            self.query_one(f"#{self.button_id('Contents')}").remove_class(lc)
            self.query_one(f"#{self.button_id('Diff')}").remove_class(lc)
            self.query_one(f"#{self.button_id('Git-Log')}").add_class(lc)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # event.stop()
        assert event.button.id is not None
        # Tree/List Switch
        self.update_button_classes(event.button.id)
        if event.button.id == self.button_id("Tree"):
            self.query_one(
                f"#{self.content_switcher_id('Left')}", ContentSwitcher
            ).current = self.component_id("ManagedTree")
        elif event.button.id == self.button_id("List"):
            self.query_one(
                f"#{self.content_switcher_id('Left')}", ContentSwitcher
            ).current = self.component_id("FlatTree")
        # Contents/Diff/GitLog Switch
        elif event.button.id == self.button_id("Contents"):
            self.query_one(
                f"#{self.content_switcher_id('Right')}", ContentSwitcher
            ).current = self.component_id("PathView")
        elif event.button.id == self.button_id("Diff"):
            self.query_one(
                f"#{self.content_switcher_id('Right')}", ContentSwitcher
            ).current = self.component_id("DiffView")
        elif event.button.id == self.button_id("Git-Log"):
            self.query_one(
                f"#{self.content_switcher_id('Right')}", ContentSwitcher
            ).current = self.component_id("GitLog")

    def on_tree_node_selected(self, event: ManagedTree.NodeSelected) -> None:
        # event.stop()
        assert event.node.data is not None
        self.query_one(
            f"#{self.content_switcher_id('Right')}", Container
        ).border_title = (
            f" {event.node.data.path.relative_to(chezmoi.dest_dir)} "
        )
        self.query_one(f"#{self.component_id('PathView')}", PathView).path = (
            event.node.data.path
        )

        self.query_one(f"#{self.component_id('DiffView')}", DiffView).path = (
            event.node.data.path
        )

        self.query_one(f"#{self.component_id('GitLog')}", GitLog).path = (
            event.node.data.path
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.filter_switch_id("unchanged"):
            self.query_one(
                f"#{self.component_id('ManagedTree')}", ManagedTree
            ).unchanged = event.value
            self.query_one(
                f"#{self.component_id('FlatTree')}", FlatTree
            ).unchanged = event.value
        elif event.switch.id == self.filter_switch_id("expand_all"):
            if event.value:
                self.query_one(
                    f"#{self.content_switcher_id('Left')}", ContentSwitcher
                ).current = self.component_id("ExpandedTree")
            elif not event.value:
                self.query_one(
                    f"#{self.content_switcher_id('Left')}", ContentSwitcher
                ).current = self.component_id("ManagedTree")
