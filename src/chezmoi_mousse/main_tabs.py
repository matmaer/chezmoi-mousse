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
    ScrollableContainer,
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
    FilteredDirTree,
    GitLog,
    ManagedTree,
    PathView,
)
from chezmoi_mousse.config import filter_data, pw_mgr_info
from chezmoi_mousse.mouse_types import (
    ButtonLabel,
    FilterName,
    TabLabel,
    TreeName,
)


class TabIdMixin:
    def __init__(self, tab: TabLabel):
        self.tab: TabLabel = tab

        self.left_content_switcher_id = f"{tab}_left_content_switcher"
        self.right_content_switcher_id = f"{tab}_right_content_switcher"
        self.left_content_switcher_container_id = (
            f"{tab}_left_content_switcher_container"
        )
        self.right_content_switcher_container_id = (
            f"{tab}_right_content_switcher_container"
        )

        # filter switch container id
        self.filters_container_id = f"{tab}_filters_container"
        self.path_view_id = f"{tab}_path_view"
        self.path_view_scrollable_container_id = (
            f"{tab}_path_view_scrollable_container"
        )
        # unique id's for main verticals
        self.tab_left_vertical = f"{tab}_main_left_vertical"
        self.tab_right_vertical = f"{tab}_main_right_vertical"
        # unique id's for tab button horizontals in TreeTabSwitchers
        self.top_left_buttons_container_id = (
            f"{tab}_top_left_buttons_container_id"
        )
        self.top_right_buttons_container_id = (
            f"{tab}_top_right_buttons_container_id"
        )

    def button_id(self, button_label: ButtonLabel) -> str:
        """Generate an id for each TabButton."""
        return f"{self.tab}_button_{button_label}"

    def content_id(self, button_label: ButtonLabel) -> str:
        """Generate an id for each widget inside of the content switcher."""
        return f"{self.tab}_{button_label}_content"

    def filter_container_id(self, filter_name: FilterName) -> str:
        """Generate an id for the filter container."""
        return f"{self.tab}_{filter_name}_filter_container"

    def filter_id(self, filter_name: FilterName) -> str:
        """Generate an id for each filter switch."""
        return f"{self.tab}_{filter_name}_filter"

    def filter_label_id(self, filter_name: FilterName) -> str:
        """Generate an id for each filter label to change style when
        disabled."""
        return f"{self.tab}_{filter_name}_label"

    def tree_container_id(self, tree_name: TreeName) -> str:
        """Generate an id for each tree container."""
        return f"{self.tab}_{tree_name}_container"

    def tree_widget_id(self, tree_name: TreeName) -> str:
        """Generate an id for each Tree or DirectoryTree."""
        return f"{self.tab}_{tree_name}_widget"


class TabButton(Button):

    def __init__(self, button_label: ButtonLabel, button_id: str) -> None:
        self.button_id = button_id
        super().__init__(
            label=button_label, id=button_id, classes="tab-button"
        )
        self.label = button_label

    def on_mount(self) -> None:
        self.active_effect_duration = 0
        self.compact = True


class TreeTabSwitchers(Horizontal, TabIdMixin):

    def __init__(self, tab: TabLabel, **kwargs) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(id=self.tab_left_vertical, classes="tab-content-left"):
            with HorizontalGroup(
                id=self.top_left_buttons_container_id,
                classes="tab-buttons-horizontal",
            ):
                yield Vertical(TabButton("Tree", self.button_id("Tree")))
                yield Vertical(TabButton("List", self.button_id("List")))
            with Container(
                id=self.left_content_switcher_container_id,
                classes="top-border-title-style",
            ):
                with ContentSwitcher(
                    initial=self.content_id("Tree"),
                    id=self.left_content_switcher_id,
                    classes="content-switcher-left",
                ):
                    with ScrollableContainer(
                        id=self.content_id("Tree"),
                        classes="tree-scrollable-container",
                    ):
                        yield ManagedTree(
                            id=self.tree_widget_id("ManagedTree"),
                            tab=self.tab,
                            flat_list=False,
                            classes="tree-widget",
                        )
                    with ScrollableContainer(
                        id=self.content_id("List"),
                        classes="tree-scrollable-container",
                    ):
                        yield ManagedTree(
                            id=self.tree_widget_id("ManTreeList"),
                            tab=self.tab,
                            flat_list=True,
                            classes="tree-widget",
                        )
                with Vertical(
                    id=self.filters_container_id,
                    classes="filter-group-vertical",
                ):
                    yield Horizontal(
                        Switch(
                            id=self.filter_id("unchanged"), classes="filter"
                        ),
                        Label(
                            filter_data.unchanged.label,
                            id=self.filter_label_id("unchanged"),
                            classes="filter filter-label",
                        ).with_tooltip(tooltip=filter_data.unchanged.tooltip),
                        id=self.filter_container_id("unchanged"),
                        classes="filter-horizontal border-top border-bottom height-3",
                    )

        with Vertical(id=self.tab_right_vertical, classes="tab-content-right"):
            with Horizontal(
                id=self.top_right_buttons_container_id,
                classes="tab-buttons-horizontal",
            ):
                yield Vertical(
                    TabButton("Contents", self.button_id("Contents"))
                )
                yield Vertical(TabButton("Diff", self.button_id("Diff")))
                yield Vertical(TabButton("Git-Log", self.button_id("Git-Log")))
            with Container(
                id=self.right_content_switcher_container_id,
                classes="top-border-title-style",
            ):
                with ContentSwitcher(
                    id=self.right_content_switcher_id,
                    initial=self.content_id("Contents"),
                    classes="content-switcher-right",
                ):
                    yield PathView(
                        id=self.content_id("Contents"),
                        auto_scroll=False,
                        wrap=False,
                        highlight=True,
                        classes="widget-right",
                    )
                    yield DiffView(
                        id=self.content_id("Diff"),
                        tab=self.tab,
                        classes="widget-right",
                    )
                    yield GitLog(
                        id=self.content_id("Git-Log"), classes="widget-right"
                    )

    def on_mount(self) -> None:
        self.query_one(
            f"#{self.left_content_switcher_container_id}", Container
        ).border_title = chezmoi.dest_dir_str_spaced
        self.query_one(
            f"#{self.right_content_switcher_container_id}", Container
        ).border_title = " path view "
        self.query_one(f"#{self.button_id('Tree')}", Button).add_class(
            "last-clicked"
        )
        self.query_one(f"#{self.button_id('Contents')}", Button).add_class(
            "last-clicked"
        )

    def update_button_classes(self, button_ids, active_id):
        for btn_id in button_ids:
            self.query_one(f"#{btn_id}", Button).remove_class("last-clicked")
        self.query_one(f"#{active_id}", Button).add_class("last-clicked")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        # Tree/List Switch
        if event.button.id in [self.button_id("Tree"), self.button_id("List")]:
            self.update_button_classes(
                [self.button_id("Tree"), self.button_id("List")],
                event.button.id,
            )
            if event.button.id == self.button_id("Tree"):
                self.query_one(
                    f"#{self.left_content_switcher_id}", ContentSwitcher
                ).current = self.content_id("Tree")
                self.query_one(
                    f"#{self.filter_id('unchanged')}", Switch
                ).disabled = False
            elif event.button.id == self.button_id("List"):
                self.query_one(
                    f"#{self.left_content_switcher_id}", ContentSwitcher
                ).current = self.content_id("List")
                self.query_one(
                    f"#{self.filter_id('unchanged')}", Switch
                ).disabled = True
        # Contents/Diff/GitLog Switch
        elif event.button.id in [
            self.button_id("Contents"),
            self.button_id("Diff"),
            self.button_id("Git-Log"),
        ]:
            # Remove from all right-side buttons
            self.update_button_classes(
                [
                    self.button_id("Contents"),
                    self.button_id("Diff"),
                    self.button_id("Git-Log"),
                ],
                event.button.id,
            )
            if event.button.id == self.button_id("Contents"):
                self.query_one(
                    f"#{self.right_content_switcher_id}", ContentSwitcher
                ).current = self.content_id("Contents")
            elif event.button.id == self.button_id("Diff"):
                self.query_one(
                    f"#{self.right_content_switcher_id}", ContentSwitcher
                ).current = self.content_id("Diff")
            elif event.button.id == self.button_id("Git-Log"):
                self.query_one(
                    f"#{self.right_content_switcher_id}", ContentSwitcher
                ).current = self.content_id("Git-Log")

    def on_tree_node_selected(self, event: ManagedTree.NodeSelected) -> None:
        event.stop()
        assert event.node.data is not None
        self.query_one(
            f"#{self.right_content_switcher_container_id}", Container
        ).border_title = (
            f" {event.node.data.path.relative_to(chezmoi.dest_dir)} "
        )
        path_view = self.query_one(f"#{self.content_id('Contents')}", PathView)
        path_view.path = event.node.data.path
        path_view.tab = self.tab

        self.query_one(f"#{self.content_id('Diff')}", DiffView).path = (
            event.node.data.path
        )

        self.query_one(f"#{self.content_id('Git-Log')}", GitLog).path = (
            event.node.data.path
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.filter_id("unchanged"):
            self.query_one(
                f"#{self.tree_widget_id('ManagedTree')}", ManagedTree
            ).unchanged = event.value


class ApplyTab(Horizontal):

    BINDINGS = [
        Binding(
            key="W,w",
            action="apply_path",
            description="chezmoi-apply",
            tooltip="write to dotfiles from your chezmoi repository",
        )
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield TreeTabSwitchers("Apply")

    def action_apply_path(self) -> None:
        self.notify("to implement")


class ReAddTab(Horizontal):

    BINDINGS = [
        Binding(
            key="A,a",
            action="re_add_path",
            description="chezmoi-re-add",
            tooltip="overwrite chezmoi repository with dotfile on disk",
        )
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield TreeTabSwitchers("Re-Add")

    def action_re_add_path(self) -> None:
        self.notify("to implement")


class AddTab(Horizontal, TabIdMixin):

    BINDINGS = [
        Binding(
            key="A,a",
            action="add_path",
            description="chezmoi-add",
            tooltip="add new file to your chezmoi repository",
        )
    ]

    def __init__(self, **kwargs) -> None:
        TabIdMixin.__init__(self, "Add")
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(id=self.tab_left_vertical, classes="tab-content-left"):
            with Container(
                id=self.left_content_switcher_container_id,
                classes="top-border-title-style",
            ):
                with ScrollableContainer(
                    id=self.tree_container_id("DirTree"),
                    classes="tree-scrollable-container",
                ):
                    yield FilteredDirTree(
                        chezmoi.dest_dir,
                        id=self.tree_widget_id("DirTree"),
                        classes="tree-widget",
                    )
            with Vertical(
                id=self.filters_container_id, classes="filter-group-vertical"
            ):
                yield Horizontal(
                    Switch(
                        id=self.filter_id("unmanaged_dirs"), classes="filter"
                    ),
                    Label(
                        filter_data.unmanaged_dirs.label,
                        id=self.filter_label_id("unmanaged_dirs"),
                        classes="filter filter-label",
                    ).with_tooltip(tooltip=filter_data.unmanaged_dirs.tooltip),
                    id=self.filter_container_id("unmanaged_dirs"),
                    classes="filter-horizontal border-top height-3",
                )
                yield Horizontal(
                    Switch(id=self.filter_id("unwanted"), classes="filter"),
                    Label(
                        filter_data.unwanted.label,
                        id=self.filter_label_id("unwanted"),
                        classes="filter filter-label",
                    ).with_tooltip(tooltip=filter_data.unwanted.tooltip),
                    id=self.filter_container_id("unwanted"),
                    classes="filter-horizontal border-bottom height-2",
                )
        with Vertical(id=self.tab_right_vertical, classes="tab-content-right"):
            with ScrollableContainer(
                id=self.path_view_scrollable_container_id,
                classes="add-tab-path-view-scrollable-container top-border-title-style-right",
            ):
                yield PathView(
                    id=self.path_view_id,
                    auto_scroll=False,
                    wrap=False,
                    highlight=True,
                    classes="widget-right",
                )

    def on_mount(self) -> None:
        filtered_dir_tree = self.query_one(
            f"#{self.tree_widget_id("DirTree")}", FilteredDirTree
        )
        filtered_dir_tree.show_root = False
        filtered_dir_tree.guide_depth = 3

        self.query_one(f"#{self.tab_left_vertical}", Vertical).border_title = (
            chezmoi.dest_dir_str_spaced
        )

        self.query_one(
            f"#{self.path_view_scrollable_container_id}", ScrollableContainer
        ).border_title = " path view "
        self.query_one(f"#{self.path_view_id}", PathView).tab = self.tab

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()

        assert event.node.data is not None
        path_view = self.query_one(f"#{self.path_view_id}", PathView)
        path_view.path = event.node.data.path
        self.query_one(
            f"#{self.tab_right_vertical}", Vertical
        ).border_title = f" {event.node.data.path} "

    def on_directory_tree_directory_selected(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        assert event.node.data is not None
        path_view = self.query_one(f"#{self.path_view_id}", PathView)
        path_view.path = event.node.data.path
        self.query_one(
            f"#{self.tab_right_vertical}", Vertical
        ).border_title = f" {event.node.data.path} "

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(
            f"#{self.tree_widget_id("DirTree")}", FilteredDirTree
        )
        if event.switch.id == self.filter_id("unmanaged_dirs"):
            tree.unmanaged_dirs = event.value
            tree.reload()
        elif event.switch.id == self.filter_id("unwanted"):
            tree.unwanted = event.value
            tree.reload()

    def action_add_path(self) -> None:
        self.notify(f"to_implement: {self.tab} tab action 'add_path'")


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
            yield GitLog()

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
