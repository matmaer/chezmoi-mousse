"""Contains the widgets used to compose the tabs on the main screen of chezmoi-
mousse, except for the Log tab.

Additionally, it contains widgets which are these tabs depend on, if they are
containers.
"""

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
from chezmoi_mousse.mouse_types import TabLabel, ButtonLabel


class TabButton(Vertical):

    def __init__(self, label: ButtonLabel, button_id: str) -> None:
        super().__init__()
        self.button_id = button_id
        self.label = label

    def compose(self) -> ComposeResult:
        yield Button(self.label, id=self.button_id, classes="tab-button")

    def on_mount(self) -> None:
        button = self.query_one(f"#{self.button_id}", Button)
        button.active_effect_duration = 0
        button.compact = True


class TreeTabSwitchers(Horizontal):

    def __init__(self, tab: TabLabel) -> None:
        self.tab: TabLabel = tab
        # button ids
        self.tree_button_id = f"{self.tab}_tree_button"
        self.list_button_id = f"{self.tab}_list_button"
        self.content_button_id = f"{self.tab}_content_button"
        self.diff_button_id = f"{self.tab}_diff_button"
        self.git_log_button_id = f"{self.tab}_git_log_button"
        self.view_buttons_id = f"{self.tab}_view_buttons"
        # button group ids
        self.tree_button_group_id = f"{self.tab}_tree_buttons"
        self.view_button_group_id = f"{self.tab}_view_buttons"

        # content switcher ids
        self.tree_switcher_id = f"{self.tab}_tree_switcher"
        self.view_switcher_id = f"{self.tab}_view_switcher"
        # content switcher content ids
        self.tree_content_id = f"{self.tab}_tree_content"
        self.list_content_id = f"{self.tab}_list_content"
        self.content_content_id = f"{self.tab}_content"
        self.diff_content_id = f"{self.tab}_diff_content"
        self.git_log_content_id = f"{self.tab}_git_log_content"
        # filter switch id
        self.filter_switch_id = f"{self.tab}_unchanged"
        super().__init__()

    def compose(self) -> ComposeResult:
        # Left: Tree/List Switcher
        with Vertical(classes="tab-content-left"):
            with Horizontal(
                id=self.tree_button_group_id, classes="tab-buttons-horizontal"
            ):
                yield TabButton("Tree", self.tree_button_id)
                yield TabButton("List", self.list_button_id)
            with ContentSwitcher(
                initial=self.tree_content_id, id=self.tree_switcher_id
            ):
                yield ManagedTree(
                    id=self.tree_content_id, tab=self.tab, flat_list=False
                )
                yield ManagedTree(
                    id=self.list_content_id, tab=self.tab, flat_list=True
                )
            yield Vertical(
                HorizontalGroup(
                    Switch(id=self.filter_switch_id, classes="filter-switch"),
                    Label(
                        filter_data.unchanged.label, classes="filter-label"
                    ).with_tooltip(tooltip=filter_data.unchanged.tooltip),
                ),
                classes="filter-container",
            )

        # Right: Content/Diff Switcher
        with Vertical(classes="tab-content-right"):
            with Horizontal(
                id=self.view_buttons_id, classes="tab-buttons-horizontal"
            ):
                yield TabButton("Content", self.content_button_id)
                yield TabButton("Diff", self.diff_button_id)
                yield TabButton("Git-Log", self.git_log_button_id)
            with ContentSwitcher(
                initial=self.content_content_id, id=self.view_switcher_id
            ):
                yield PathView(
                    id=self.content_content_id,
                    auto_scroll=False,
                    wrap=False,
                    highlight=True,
                )
                yield DiffView(id=self.diff_content_id)
                yield GitLog(id=self.git_log_content_id)

    def on_mount(self) -> None:

        self.query_one(
            f"#{self.tree_button_group_id}", Horizontal
        ).border_subtitle = chezmoi.dest_dir_str_spaced
        self.query_one(f"#{self.tree_button_id}", Button).add_class(
            "last-clicked"
        )
        # Right
        self.query_one(f"#{self.content_button_id}", Button).add_class(
            "last-clicked"
        )
        self.query_one(
            f"#{self.view_buttons_id}", Horizontal
        ).border_subtitle = " path view "

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        # Tree/List Switch
        if (
            event.button.id == self.tree_button_id
            or event.button.id == self.list_button_id
        ):
            # Remove from both tree and list buttons
            for btn_id in [self.tree_button_id, self.list_button_id]:
                self.query_one(f"#{btn_id}", Button).remove_class(
                    "last-clicked"
                )
            if event.button.id == self.tree_button_id:
                self.query_one(
                    f"#{self.tree_switcher_id}", ContentSwitcher
                ).current = self.tree_content_id
                self.query_one(f"#{self.tree_button_id}", Button).add_class(
                    "last-clicked"
                )
            else:
                self.query_one(
                    f"#{self.tree_switcher_id}", ContentSwitcher
                ).current = self.list_content_id
                self.query_one(f"#{self.list_button_id}", Button).add_class(
                    "last-clicked"
                )
        # Content/Diff/GitLog Switch
        elif (
            event.button.id == self.content_button_id
            or event.button.id == self.diff_button_id
            or event.button.id == self.git_log_button_id
        ):
            # Remove from all right-side buttons
            for btn_id in [
                self.content_button_id,
                self.diff_button_id,
                self.git_log_button_id,
            ]:
                self.query_one(f"#{btn_id}", Button).remove_class(
                    "last-clicked"
                )
            if event.button.id == self.content_button_id:
                self.query_one(
                    f"#{self.view_switcher_id}", ContentSwitcher
                ).current = self.content_content_id
                self.query_one(f"#{self.content_button_id}", Button).add_class(
                    "last-clicked"
                )
            elif event.button.id == self.diff_button_id:
                self.query_one(
                    f"#{self.view_switcher_id}", ContentSwitcher
                ).current = self.diff_content_id
                self.query_one(f"#{self.diff_button_id}", Button).add_class(
                    "last-clicked"
                )
            elif event.button.id == self.git_log_button_id:
                self.query_one(
                    f"#{self.view_switcher_id}", ContentSwitcher
                ).current = self.git_log_content_id
                self.query_one(f"#{self.git_log_button_id}", Button).add_class(
                    "last-clicked"
                )

    def on_tree_node_selected(self, event: ManagedTree.NodeSelected) -> None:
        event.stop()
        assert event.node.data is not None
        self.query_one(
            f"#{self.view_button_group_id}", Horizontal
        ).border_subtitle = (
            f" {event.node.data.path.relative_to(chezmoi.dest_dir)} "
        )
        path_view = self.query_one(f"#{self.content_content_id}", PathView)
        path_view.path = event.node.data.path
        path_view.tab = self.tab
        self.query_one(f"#{self.diff_content_id}", DiffView).diff_spec = (
            event.node.data.path,
            self.tab,
        )
        self.query_one(f"#{self.git_log_content_id}", GitLog).path = (
            event.node.data.path
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.filter_switch_id:
            self.query_one(
                f"#{self.tree_content_id}", ManagedTree
            ).unchanged = event.value


class ApplyTab(Vertical):

    BINDINGS = [
        Binding(
            key="W,w",
            action="apply_path",
            description="chezmoi-apply",
            tooltip="write to dotfiles from your chezmoi repository",
        )
    ]

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

    def compose(self) -> ComposeResult:
        yield TreeTabSwitchers("Re-Add")

    def action_re_add_path(self) -> None:
        self.notify("to implement")


class AddTab(Horizontal):

    BINDINGS = [
        Binding(
            key="A,a",
            action="add_path",
            description="chezmoi-add",
            tooltip="add new file to your chezmoi repository",
        )
    ]

    def __init__(self, **kwargs) -> None:
        self.tab: TabLabel = "Add"
        # the directory tree on the left
        self.add_tree_id = f"{self.tab}_dir_tree"
        # the path view on the right
        self.path_view_id = f"{self.tab}_path_view"
        # vertical container ids to set border titles
        self.tree_container_id = f"{self.tab}_tree_container"
        self.view_container_id = f"{self.tab}_view_container"
        # filter switch ids
        self.unmanaged_dirs_filter_id = f"{self.tab}_unmanaged_dirs_filter"
        self.unwanted_filter_id = f"{self.tab}_unwanted_filter"

        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(classes="tab-content-left"):
            yield ScrollableContainer(
                FilteredDirTree(chezmoi.dest_dir, id=self.add_tree_id),
                id=self.tree_container_id,
                classes="border-path-title",
            )
            yield Vertical(
                HorizontalGroup(
                    Switch(
                        id=self.unmanaged_dirs_filter_id,
                        classes="filter-switch",
                    ),
                    Label(
                        filter_data.unmanaged_dirs.label,
                        classes="filter-label",
                    ).with_tooltip(tooltip=filter_data.unmanaged_dirs.tooltip),
                    classes="padding-bottom-once",
                ),
                HorizontalGroup(
                    Switch(
                        id=self.unwanted_filter_id, classes="filter-switch"
                    ),
                    Label(
                        filter_data.unwanted.label, classes="filter-label"
                    ).with_tooltip(tooltip=filter_data.unwanted.tooltip),
                ),
                classes="filter-container",
            )

        yield Vertical(
            PathView(
                id=self.path_view_id,
                auto_scroll=False,
                wrap=False,
                highlight=True,
            ),
            id=self.view_container_id,
            classes="border-path-title",
        )

    def on_mount(self) -> None:
        filtered_dir_tree = self.query_one(
            f"#{self.add_tree_id}", FilteredDirTree
        )
        filtered_dir_tree.show_root = False
        filtered_dir_tree.guide_depth = 3

        self.query_one(
            f"#{self.tree_container_id}", ScrollableContainer
        ).border_title = chezmoi.dest_dir_str_spaced

        self.query_one(f"#{self.view_container_id}", Vertical).border_title = (
            " path view "
        )

        self.query_one(f"#{self.path_view_id}", PathView).tab = self.tab

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()

        assert event.node.data is not None
        path_view = self.query_one(f"#{self.path_view_id}", PathView)
        path_view.path = event.node.data.path
        path_view.tab = self.tab
        self.query_one(f"#{self.view_container_id}", Vertical).border_title = (
            f" {event.node.data.path} "
        )

    def on_directory_tree_directory_selected(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        assert event.node.data is not None
        path_view = self.query_one(f"#{self.path_view_id}", PathView)
        path_view.path = event.node.data.path
        path_view.tab = self.tab
        self.query_one(f"#{self.view_container_id}", Vertical).border_title = (
            f" {event.node.data.path} "
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(f"#{self.add_tree_id}", FilteredDirTree)
        if event.switch.id == self.unmanaged_dirs_filter_id:
            tree.unmanaged_dirs = event.value
            tree.reload()
        elif event.switch.id == self.unwanted_filter_id:
            tree.unwanted = event.value
            tree.reload()

    def action_add_path(self) -> None:
        dir_tree = self.query_one(f"#{self.add_tree_id}", FilteredDirTree)
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
