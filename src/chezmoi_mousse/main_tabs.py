"""Contains the widgets used to compose the tabs on the main screen of chezmoi-
mousse, except for the Log tab.

Additionally, it contains widgets which are these tabs depend on, if they are
containers.
"""

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
from textual.events import Click
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Collapsible,
    ContentSwitcher,
    DataTable,
    Label,
    Link,
    ListItem,
    ListView,
    Pretty,
    Static,
    Switch,
)

import chezmoi_mousse.theme as theme
from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.components import (
    DiffView,
    ExpandedTree,
    FilteredDirTree,
    FlatTree,
    GitLog,
    ManagedTree,
    PathView,
    TabIdMixin,
)
from chezmoi_mousse.config import filter_data, pw_mgr_info
from chezmoi_mousse.mouse_types import ButtonLabel, FilterName, TabLabel


class TabButton(Button, TabIdMixin):

    def __init__(self, button_label: ButtonLabel, tab: TabLabel) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(
            label=button_label,
            id=self.button_id(button_label),
            classes="tab-button",
        )

    def on_mount(self) -> None:
        self.active_effect_duration = 0
        self.compact = True


class FilterSwitch(HorizontalGroup, TabIdMixin):

    def __init__(
        self, tab: TabLabel, switch_name: FilterName, **kwargs
    ) -> None:
        TabIdMixin.__init__(self, tab)
        self.switch_name: FilterName = switch_name
        self.label = filter_data[self.switch_name].label
        super().__init__(id=self.filter_horizontal_id(switch_name), **kwargs)

    def compose(self) -> ComposeResult:
        yield Switch(id=self.filter_switch_id(self.switch_name))
        yield Label(
            filter_data[self.switch_name].label,
            id=self.filter_label_id(self.switch_name),
            classes="filter-label",
        ).with_tooltip(tooltip=filter_data[self.switch_name].tooltip)


class TreeFilterSlider(VerticalGroup, TabIdMixin):

    def __init__(self, tab: TabLabel, slider_name: str) -> None:
        TabIdMixin.__init__(self, tab)
        self.slider_name = slider_name
        super().__init__(
            id=self.filters_vertical_id(self.tab), classes="filters-vertical"
        )

    def compose(self) -> ComposeResult:
        yield FilterSwitch(
            tab=self.tab,
            switch_name="unchanged",
            classes="filter-horizontal padding-bottom-once",
        )
        yield FilterSwitch(
            tab=self.tab, switch_name="expand_all", classes="filter-horizontal"
        )


class AddFilterSlider(VerticalGroup, TabIdMixin):

    def __init__(self, tab: TabLabel, slider_name: str) -> None:
        TabIdMixin.__init__(self, tab)
        self.slider_name = slider_name
        super().__init__(
            id=self.filters_vertical_id(self.tab), classes="filters-vertical"
        )

    def compose(self) -> ComposeResult:
        yield FilterSwitch(
            tab=self.tab,
            switch_name="unmanaged_dirs",
            classes="filter-horizontal padding-bottom-once",
        )
        yield FilterSwitch(
            tab=self.tab, switch_name="unwanted", classes="filter-horizontal"
        )


class TreeTabFilterSliders(HorizontalGroup, TabIdMixin):

    def __init__(self, tab: TabLabel, **kwargs) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(id=self.filters_vertical_id(self.tab), **kwargs)

    def compose(self) -> ComposeResult:
        yield FilterSwitch(
            tab=self.tab,
            switch_name="unmanaged_dirs",
            classes="filter-horizontal padding-bottom-once",
        )
        yield FilterSwitch(
            tab=self.tab, switch_name="unwanted", classes="filter-horizontal"
        )


class TreeTabSwitchers(Horizontal, TabIdMixin):

    def __init__(self, tab: TabLabel, **kwargs) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(id=self.tree_tab_switchers_id(self.tab), **kwargs)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_vertical_id("Left"),
            classes="tab-left-vertical apply-re-add-min-width",
        ):
            with HorizontalGroup(
                id=self.buttons_horizontal_id("TopLeft"),
                classes="tab-buttons-horizontal",
            ):
                yield TabButton("Tree", tab=self.tab)
                yield TabButton("List", tab=self.tab)
            with ContentSwitcher(
                id=self.content_switcher_id("Left"),
                initial=self.component_id("ManagedTree"),
                classes="content-switcher-left top-border-title",
            ):
                yield ManagedTree(tab=self.tab, classes="tree-widget")
                yield FlatTree(tab=self.tab, classes="tree-widget")
                yield ExpandedTree(tab=self.tab, classes="tree-widget")

        with Vertical(
            id=self.tab_vertical_id("Right"), classes="tab-right-vertical"
        ):
            with HorizontalGroup(
                id=self.buttons_horizontal_id("TopRight"),
                classes="tab-buttons-horizontal",
            ):
                yield TabButton("Contents", tab=self.tab)
                yield TabButton("Diff", tab=self.tab)
                yield TabButton("Git-Log", tab=self.tab)

            with ContentSwitcher(
                id=self.content_switcher_id("Right"),
                initial=self.component_id("PathView"),
                classes="content-switcher-right top-border-title",
            ):
                yield PathView(tab=self.tab, classes="path-view")
                yield DiffView(tab=self.tab, classes="diff-view")
                yield GitLog(tab=self.tab, classes="git-log")

        yield TreeFilterSlider(tab=self.tab, slider_name="tree-filters")

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
        event.stop()
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
        event.stop()
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


class ApplyTab(Container, TabIdMixin):

    BINDINGS = [
        Binding(
            key="W,w",
            action="apply_path",
            description="chezmoi-apply",
            tooltip="write to dotfiles from your chezmoi repository",
        ),
        Binding(
            key="F,f",
            action="toggle_filter_slider",
            description="toggle-filters",
            tooltip="toggle filters for this tree in/out of view",
        ),
    ]

    def __init__(self, **kwargs) -> None:
        TabIdMixin.__init__(self, "Apply")
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield TreeTabSwitchers(tab="Apply")

    def action_apply_path(self) -> None:
        self.notify("to implement")

    def action_toggle_filter_slider(self) -> None:
        """Toggle the visibility of the filter slider."""
        self.query_one(
            f"#{self.filters_vertical_id(self.tab)}", VerticalGroup
        ).toggle_class("-visible")


class ReAddTab(Container, TabIdMixin):

    BINDINGS = [
        Binding(key="A,a", action="re_add_path", description="chezmoi-re-add"),
        Binding(
            key="F,f",
            action="toggle_filter_slider",
            description="toggle-filters",
        ),
    ]

    def __init__(self, **kwargs) -> None:
        TabIdMixin.__init__(self, "Re-Add")
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield TreeTabSwitchers(tab="Re-Add")

    def action_re_add_path(self) -> None:
        self.notify("to implement")

    def action_toggle_filter_slider(self) -> None:
        """Toggle the visibility of the filter slider."""
        self.query_one(
            f"#{self.filters_vertical_id(self.tab)}", VerticalGroup
        ).toggle_class("-visible")


class AddTab(Horizontal, TabIdMixin):

    BINDINGS = [
        Binding(key="A,a", action="add_path", description="chezmoi-add"),
        Binding(
            key="F,f",
            action="toggle_filter_slider",
            description="toggle-filters",
        ),
    ]

    def __init__(self, **kwargs) -> None:
        TabIdMixin.__init__(self, "Add")
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_vertical_id("Left"),
            classes="tab-left-vertical add-tab-min-width",
        ):
            yield FilteredDirTree(
                chezmoi.dest_dir,
                id=self.component_id("FilteredDirTree"),
                classes="dir-tree-widget top-border-title",
            )

        with Vertical(
            id=self.tab_vertical_id("Right"), classes="tab-right-vertical"
        ):
            yield PathView(tab=self.tab, classes="path-view top-border-title")
        yield AddFilterSlider(tab=self.tab, slider_name="dir-tree-filters")

    def on_mount(self) -> None:
        self.query_one(
            f"#{self.component_id('PathView')}", PathView
        ).border_title = " path view "
        self.query_one(
            f"#{self.component_id('FilteredDirTree')}", FilteredDirTree
        ).border_title = chezmoi.dest_dir_str_spaced

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()

        assert event.node.data is not None
        path_view = self.query_one(
            f"#{self.component_id('PathView')}", PathView
        )
        path_view.path = event.node.data.path
        path_view.border_title = (
            f" {event.node.data.path.relative_to(chezmoi.dest_dir)} "
        )

    def on_directory_tree_directory_selected(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        assert event.node.data is not None
        path_view = self.query_one(
            f"#{self.component_id('PathView')}", PathView
        )
        path_view.path = event.node.data.path
        path_view.border_title = (
            f" {event.node.data.path.relative_to(chezmoi.dest_dir)} "
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(
            f"#{self.component_id('FilteredDirTree')}", FilteredDirTree
        )
        if event.switch.id == self.filter_switch_id("unmanaged_dirs"):
            tree.unmanaged_dirs = event.value
            tree.reload()
        elif event.switch.id == self.filter_switch_id("unwanted"):
            tree.unwanted = event.value
            tree.reload()

    def action_add_path(self) -> None:
        self.notify(f"to_implement: {self.tab} tab action 'add_path'")

    def action_toggle_filter_slider(self) -> None:
        """Toggle the visibility of the filter slider."""
        self.query_one(
            f"#{self.filters_vertical_id(self.tab)}", VerticalGroup
        ).toggle_class("-visible")


class DoctorTab(VerticalScroll):

    BINDINGS = [
        Binding(key="C,c", action="open_config", description="chezmoi-config"),
        Binding(
            key="G,g",
            action="git_log",
            description="show-git-log",
            tooltip="git log from your chezmoi repository",
        ),
    ]

    class ConfigDumpModal(ModalScreen):

        BINDINGS = [
            Binding(
                key="escape", action="dismiss", description="close", show=False
            )
        ]

        def compose(self) -> ComposeResult:
            yield Pretty(chezmoi.dump_config.dict_out)

        def on_mount(self) -> None:
            self.add_class("doctor-modal")
            self.border_title = "chezmoi dump-config - command output"
            self.border_subtitle = "double click or escape to close"

        def on_click(self, event: Click) -> None:
            event.stop()
            if event.chain == 2:
                self.dismiss()

    class GitLogModal(ModalScreen):

        BINDINGS = [
            Binding(
                key="escape", action="dismiss", description="close", show=False
            )
        ]

        def compose(self) -> ComposeResult:
            yield GitLog(tab="Doctor")

        def on_mount(self) -> None:
            self.add_class("doctor-modal")
            self.border_title = "chezmoi git log - command output"
            self.border_subtitle = "double click or escape to close"

        def on_click(self, event: Click) -> None:
            event.stop()
            if event.chain == 2:
                self.dismiss()

    def compose(self) -> ComposeResult:

        with Horizontal():
            yield DataTable(show_cursor=False)
        with VerticalGroup():
            yield Collapsible(
                Pretty(chezmoi.template_data.dict_out),
                title="chezmoi data (template data)",
            )
            yield Collapsible(
                Pretty(chezmoi.cat_config.list_out),
                title="chezmoi cat-config (contents of config-file)",
            )
            yield Collapsible(
                Pretty(chezmoi.ignored.list_out),
                title="chezmoi ignored (git ignore in source-dir)",
            )
            yield Collapsible(ListView(), title="Commands Not Found")

    def on_mount(self) -> None:

        styles = {
            "ok": theme.vars["text-success"],
            "warning": theme.vars["text-warning"],
            "error": theme.vars["text-error"],
            "info": theme.vars["foreground-darken-1"],
        }
        list_view = self.query_exactly_one(ListView)
        table = self.query_exactly_one(DataTable)
        doctor_rows = chezmoi.doctor.list_out
        table.add_columns(*doctor_rows[0].split())

        for line in doctor_rows[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                if row[1] in pw_mgr_info:
                    list_view.append(
                        ListItem(
                            Link(row[1], url=pw_mgr_info[row[1]]["link"]),
                            Static(pw_mgr_info[row[1]]["description"]),
                        )
                    )
                elif row[1] not in pw_mgr_info:
                    list_view.append(
                        ListItem(
                            # color accent as that's how links are styled by default
                            Static(f"[$accent-muted]{row[1]}[/]", markup=True),
                            Label("Not Found in $PATH."),
                        )
                    )
            elif row[0] == "ok" or row[0] == "warning" or row[0] == "error":
                row = [
                    Text(cell_text, style=f"{styles[row[0]]}")
                    for cell_text in row
                ]
                table.add_row(*row)
            elif row[0] == "info" and row[2] == "not set":
                row = [
                    Text(cell_text, style=styles["warning"])
                    for cell_text in row
                ]
                table.add_row(*row)
            else:
                row = [Text(cell_text) for cell_text in row]
                table.add_row(*row)

    def action_open_config(self) -> None:
        self.app.push_screen(DoctorTab.ConfigDumpModal())

    def action_git_log(self) -> None:
        self.app.push_screen(DoctorTab.GitLogModal())
