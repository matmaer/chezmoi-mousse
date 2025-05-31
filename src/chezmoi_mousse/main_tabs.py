"""Contains the widgets used to compose the tabs on the main screen of chezmoi-
mousse, except for the Log tab.

Additionally, it contains widgets which are these tabs depend on, if they are
containers.
"""

from typing import Literal
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    ScrollableContainer,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
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

from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.components import (
    DiffView,
    FilteredDirTree,
    GitLog,
    ManagedTree,
    PathView,
)

from chezmoi_mousse.config import filter_data, pw_mgr_info

# for type hinting/checking
TabName = Literal["Apply", "ReAdd", "Add", "Doctor"]
AreaName = Literal["left_top", "right_top", "right_bottom", "left_bottom"]


def left_min_width() -> int:
    # 7 for the filter switch, 2 for title padding right
    max_filter_width = (
        max(len(f.label) for f in vars(filter_data).values()) + 8 + 2
    )
    return max(len(chezmoi.dest_dir_str_spaced) + 2, max_filter_width)


class TabButton(Vertical):

    def __init__(self, label: str, button_id: str) -> None:
        super().__init__(classes="center-content")
        self.button_id = button_id
        self.label = label

    def compose(self) -> ComposeResult:
        yield Button(self.label, id=self.button_id, classes="tab-button")

    def on_mount(self) -> None:
        button = self.query_one(f"#{self.button_id}", Button)
        button.active_effect_duration = 0
        button.compact = True


class TreeTabSwitchers(Horizontal):

    def __init__(self, tab: str) -> None:
        self.tab = tab
        super().__init__(id=f"{tab}_tab_switchers")

    def compose(self) -> ComposeResult:
        # Left: Tree/List Switcher
        with Vertical(id=f"{self.tab}_left", classes="tab-content-left"):
            with Horizontal(
                id=f"{self.tab}_tree_buttons", classes="tab-buttons-horizontal"
            ):
                yield TabButton("Tree", f"{self.tab}_tree_button")
                yield TabButton("List", f"{self.tab}_list_button")
            with ContentSwitcher(
                initial=f"{self.tab}_tree", id=f"{self.tab}_tree_switcher"
            ):
                yield ManagedTree(
                    id=f"{self.tab}_tree",
                    direction=f"{self.tab}",
                    flat_list=False,
                )
                yield ManagedTree(
                    id=f"{self.tab}_list",
                    direction=f"{self.tab}",
                    flat_list=True,
                )
            yield Vertical(
                HorizontalGroup(
                    Switch(
                        id=f"{self.tab}_tab_unchanged", classes="filter-switch"
                    ),
                    Label(
                        filter_data.unchanged.label, classes="filter-label"
                    ).with_tooltip(tooltip=filter_data.unchanged.tooltip),
                ),
                classes="filter-container",
            )

        # Right: Content/Diff Switcher
        with Vertical(id=f"{self.tab}_right", classes="tab-content-right"):
            with Horizontal(
                id=f"{self.tab}_view_buttons", classes="tab-buttons-horizontal"
            ):
                yield TabButton("Content", f"{self.tab}_content_button")
                yield TabButton("Diff", f"{self.tab}_diff_button")
            with ContentSwitcher(
                initial=f"{self.tab}_content", id=f"{self.tab}_view_switcher"
            ):
                yield PathView(id=f"{self.tab}_content")
                yield DiffView(id=f"{self.tab}_diff")

    def on_mount(self) -> None:
        # Left
        self.query_one(f"#{self.tab}_left", Vertical).styles.min_width = (
            left_min_width()
        )
        self.query_one(
            f"#{self.tab}_tree_buttons", Horizontal
        ).border_subtitle = chezmoi.dest_dir_str_spaced
        self.query_one(f"#{self.tab}_tree_button", Button).add_class(
            "last-clicked"
        )
        # Right
        self.query_one(f"#{self.tab}_content_button", Button).add_class(
            "last-clicked"
        )
        self.query_one(
            f"#{self.tab}_view_buttons", Horizontal
        ).border_subtitle = " path view "

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        # Tree/List Switch
        if event.button.id == f"{self.tab}_tree_button":
            self.query_one(
                f"#{self.tab}_tree_switcher", ContentSwitcher
            ).current = f"{self.tab}_tree"
            self.query_one(f"#{self.tab}_tree_button", Button).add_class(
                "last-clicked"
            )
            self.query_one(f"#{self.tab}_list_button", Button).remove_class(
                "last-clicked"
            )
        elif event.button.id == f"{self.tab}_list_button":
            self.query_one(
                f"#{self.tab}_tree_switcher", ContentSwitcher
            ).current = f"{self.tab}_list"
            self.query_one(f"#{self.tab}_list_button", Button).add_class(
                "last-clicked"
            )
            self.query_one(f"#{self.tab}_tree_button", Button).remove_class(
                "last-clicked"
            )
        # Content/Diff Switch
        elif event.button.id == f"{self.tab}_content_button":
            self.query_one(
                f"#{self.tab}_view_switcher", ContentSwitcher
            ).current = f"{self.tab}_content"
            self.query_one(f"#{self.tab}_content_button", Button).add_class(
                "last-clicked"
            )
            self.query_one(f"#{self.tab}_diff_button", Button).remove_class(
                "last-clicked"
            )
        elif event.button.id == f"{self.tab}_diff_button":
            self.query_one(
                f"#{self.tab}_view_switcher", ContentSwitcher
            ).current = f"{self.tab}_diff"
            self.query_one(f"#{self.tab}_diff_button", Button).add_class(
                "last-clicked"
            )
            self.query_one(f"#{self.tab}_content_button", Button).remove_class(
                "last-clicked"
            )


class ApplyTab(Horizontal):

    BINDINGS = [
        Binding(
            key="W,w",
            action="apply_path",
            description="chezmoi-apply",
            tooltip="write to dotfiles from your chezmoi repository",
        )
    ]

    def compose(self) -> ComposeResult:
        yield TreeTabSwitchers("apply")

    def on_tree_node_selected(self, event: ManagedTree.NodeSelected) -> None:
        event.stop()
        assert event.node.data is not None
        self.query_one("#apply_view_buttons", Horizontal).border_subtitle = (
            f" {event.node.data.path.relative_to(chezmoi.dest_dir)} "
        )
        path_view = self.query_one("#apply_content", PathView)
        path_view.path = event.node.data.path
        path_view.tab_id = "apply_tab"
        self.query_one("#apply_diff", DiffView).diff_spec = (
            event.node.data.path,
            "apply",
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == "apply_tab_unchanged":
            self.query_one("#apply_tree", ManagedTree).unchanged = event.value

    def action_apply_path(self) -> None:
        managed_tree = self.query_one("#apply_tree", ManagedTree)
        self.notify(f"will add {managed_tree.cursor_node}")


class ReAddTab(Horizontal):

    BINDINGS = [
        Binding(
            key="A,a",
            action="re_add_path",
            description="chezmoi-re-add",
            tooltip="overwrite chezmoi repository with dotfile on disk",
        )
    ]

    def compose(self) -> ComposeResult:
        yield TreeTabSwitchers("re_add")

    def on_tree_node_selected(self, event: ManagedTree.NodeSelected) -> None:
        event.stop()
        assert event.node.data is not None
        self.query_one("#re_add_view_buttons", Horizontal).border_subtitle = (
            f" {event.node.data.path.relative_to(chezmoi.dest_dir)} "
        )
        path_view = self.query_one("#re_add_content", PathView)
        path_view.path = event.node.data.path
        path_view.tab_id = "re_add_tab"
        self.query_one("#re_add_diff", DiffView).diff_spec = (
            event.node.data.path,
            "re-add",
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == "re_add_tab_unchanged":
            self.query_one("#re_add_tree", ManagedTree).unchanged = event.value

    def action_re_add_path(self) -> None:
        managed_tree = self.query_one("#re_add_tree", ManagedTree)
        self.notify(f"will add {managed_tree.cursor_node}")


class AddTab(Horizontal):

    BINDINGS = [
        Binding(
            key="A,a",
            action="add_path",
            description="chezmoi-add",
            tooltip="add new file to your chezmoi repository",
        )
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="add_tab_left", classes="tab-content-left"):
            yield ScrollableContainer(
                FilteredDirTree(chezmoi.dest_dir, id="add_tree"),
                id="add_tree_container",
                classes="border-path-title",
            )
            yield Vertical(
                HorizontalGroup(
                    Switch(
                        id="add_tab_unmanaged_dirs", classes="filter-switch"
                    ),
                    Label(
                        filter_data.unmanaged_dirs.label,
                        classes="filter-label",
                    ).with_tooltip(tooltip=filter_data.unmanaged_dirs.tooltip),
                    classes="center-content padding-bottom-once",
                ),
                HorizontalGroup(
                    Switch(id="add_tab_unwanted", classes="filter-switch"),
                    Label(
                        filter_data.unwanted.label, classes="filter-label"
                    ).with_tooltip(tooltip=filter_data.unwanted.tooltip),
                    classes="center-content",
                ),
                classes="filter-container",
            )

        yield Vertical(
            PathView(id="add_path_view"),
            id="add_tab_right",
            classes="border-path-title",
        )

    def on_mount(self) -> None:
        filtered_dir_tree = self.query_one("#add_tree", FilteredDirTree)
        filtered_dir_tree.show_root = False
        filtered_dir_tree.guide_depth = 3

        self.query_one("#add_tab_left", Vertical).styles.min_width = (
            left_min_width()
        )
        self.query_one(
            "#add_tree_container", ScrollableContainer
        ).border_title = chezmoi.dest_dir_str_spaced

        self.query_one("#add_tab_right", Vertical).border_title = " path view "

        self.query_one("#add_path_view", PathView).tab_id = "add_tab"

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()

        assert event.node.data is not None
        path_view = self.query_one("#add_path_view", PathView)
        path_view.path = event.node.data.path
        path_view.tab_id = "add_tab"
        self.query_one("#add_tab_right", Vertical).border_title = (
            f" {event.node.data.path} "
        )

    def on_directory_tree_directory_selected(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        assert event.node.data is not None
        path_view = self.query_one("#add_path_view", PathView)
        path_view.path = event.node.data.path
        path_view.tab_id = "add_tab"
        self.query_one("#add_tab_right", Vertical).border_title = (
            f" {event.node.data.path} "
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one("#add_tree", FilteredDirTree)
        if event.switch.id == "add_tab_unmanaged_dirs":
            tree.unmanaged_dirs = event.value
            tree.reload()
        elif event.switch.id == "add_tab_unwanted":
            tree.unwanted = event.value
            tree.reload()

    def action_add_path(self) -> None:
        dir_tree = self.query_one("#add_tree", FilteredDirTree)
        self.notify(f"will add {dir_tree.cursor_node}")


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
            "ok": f"{self.app.current_theme.success}",
            "warning": f"{self.app.current_theme.warning}",
            "error": f"{self.app.current_theme.error}",
            "info": f"{self.app.current_theme.foreground}",
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
                    Text(cell_text, style=f"{self.app.current_theme.warning}")
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
