"""Contains the widgets used to compose the main screen of chezmoi-mousse."""

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
    TabButton,
)

from chezmoi_mousse.config import filter_data, pw_mgr_info


def left_min_width() -> int:
    # 7 for the filter switch, 2 for title padding right
    max_filter_width = (
        max(len(f.label) for f in vars(filter_data).values()) + 8 + 2
    )
    return max(len(chezmoi.dest_dir_str_spaced) + 2, max_filter_width)


class TreeTabButtons(Horizontal):

    def __init__(self, kind: str, **kwargs) -> None:
        self.kind = kind
        super().__init__(
            id=f"{self.kind}_tree_buttons",
            classes="tab-buttons-horizontal",
            **kwargs,
        )

    def compose(self) -> ComposeResult:
        yield Vertical(
            TabButton("Tree", id=f"{self.kind}_tree_button"),
            classes="center-content",
        )
        yield Vertical(
            TabButton("List", id=f"{self.kind}_list_button"),
            classes="center-content",
        )


class ViewTabButtons(Horizontal):
    def __init__(self, kind: str, **kwargs) -> None:
        self.kind = kind
        super().__init__(
            id=f"{self.kind}_view_buttons",
            classes="tab-buttons-horizontal",
            **kwargs,
        )

    def compose(self) -> ComposeResult:
        yield Vertical(
            TabButton("Content", id=f"{self.kind}_content_button"),
            classes="center-content",
        )
        yield Vertical(
            TabButton("Diff", id=f"{self.kind}_diff_button"),
            classes="center-content",
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
        with Vertical(id="apply_left", classes="tab-content-left"):
            yield TreeTabButtons("apply")
            with ContentSwitcher(initial="apply_tree", id="apply_switcher"):
                yield ManagedTree(
                    id="apply_tree", direction="apply", flat_list=False
                )
                yield ManagedTree(
                    id="apply_list", direction="apply", flat_list=True
                )
            yield Vertical(
                HorizontalGroup(
                    Switch(id="apply_tab_unchanged", classes="filter-switch"),
                    Label(
                        filter_data.unchanged.label, classes="filter-label"
                    ).with_tooltip(tooltip=filter_data.unchanged.tooltip),
                ),
                classes="filter-container",
            )
        with Vertical(classes="tab-content-right"):
            yield ViewTabButtons("apply")
            with ContentSwitcher(
                initial="apply_content", id="apply_view_switcher"
            ):
                yield PathView(id="apply_content")
                yield DiffView(id="apply_diff")

    def on_mount(self) -> None:
        self.query_one("#apply_left", Vertical).styles.min_width = (
            left_min_width()
        )

        self.query_one("#apply_tree_buttons", Horizontal).border_subtitle = (
            chezmoi.dest_dir_str_spaced
        )

        self.query_one("#apply_view_buttons", Horizontal).border_subtitle = (
            " path view "
        )

        self.query_one("#apply_tree_button", Button).add_class("last-clicked")

        self.query_one("#apply_content_button", Button).add_class(
            "last-clicked"
        )

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "apply_tree_button":
            self.query_one("#apply_switcher", ContentSwitcher).current = (
                "apply_tree"
            )
            self.query_one("#apply_tree_button", Button).add_class(
                "last-clicked"
            )
            self.query_one("#apply_list_button", Button).remove_class(
                "last-clicked"
            )
        elif event.button.id == "apply_list_button":
            self.query_one("#apply_switcher", ContentSwitcher).current = (
                "apply_list"
            )
            self.query_one("#apply_list_button", Button).add_class(
                "last-clicked"
            )
            self.query_one("#apply_tree_button", Button).remove_class(
                "last-clicked"
            )
        elif event.button.id == "apply_content_button":
            self.query_one("#apply_view_switcher", ContentSwitcher).current = (
                "apply_content"
            )
            self.query_one("#apply_content_button", Button).add_class(
                "last-clicked"
            )
            self.query_one("#apply_diff_button", Button).remove_class(
                "last-clicked"
            )
        elif event.button.id == "apply_diff_button":
            self.query_one("#apply_view_switcher", ContentSwitcher).current = (
                "apply_diff"
            )
            self.query_one("#apply_diff_button", Button).add_class(
                "last-clicked"
            )
            self.query_one("#apply_content_button", Button).remove_class(
                "last-clicked"
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
        with Vertical(id="re_add_left", classes="tab-content-left"):
            yield TreeTabButtons("re_add")
            with ContentSwitcher(
                initial="re_add_tree", id="re_add_tree_switcher"
            ):
                yield ManagedTree(
                    id="re_add_tree", direction="re-add", flat_list=False
                )
                yield ManagedTree(
                    id="re_add_list", direction="re-add", flat_list=True
                )
            yield Vertical(
                HorizontalGroup(
                    Switch(id="re_add_tab_unchanged", classes="filter-switch"),
                    Label(
                        filter_data.unchanged.label, classes="filter-label"
                    ).with_tooltip(tooltip=filter_data.unchanged.tooltip),
                ),
                classes="filter-container",
            )
        with Vertical(classes="tab-content-right"):
            yield ViewTabButtons("re_add")
            with ContentSwitcher(
                initial="re_add_content", id="re_add_view_switcher"
            ):
                yield PathView(id="re_add_content")
                yield DiffView(id="re_add_diff")

    def on_mount(self) -> None:
        self.query_one("#re_add_left", Vertical).styles.min_width = (
            left_min_width()
        )

        self.query_one("#re_add_tree_buttons", Horizontal).border_subtitle = (
            chezmoi.dest_dir_str_spaced
        )

        self.query_one("#re_add_view_buttons", Horizontal).border_subtitle = (
            " path view "
        )

        self.query_one("#re_add_tree_button", Button).add_class("last-clicked")

        self.query_one("#re_add_content_button", Button).add_class(
            "last-clicked"
        )

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "re_add_tree_button":
            self.query_one(
                "#re_add_tree_switcher", ContentSwitcher
            ).current = "re_add_tree"
            self.query_one("#re_add_tree_button", Button).add_class(
                "last-clicked"
            )
            self.query_one("#re_add_list_button", Button).remove_class(
                "last-clicked"
            )
        elif event.button.id == "re_add_list_button":
            self.query_one(
                "#re_add_tree_switcher", ContentSwitcher
            ).current = "re_add_list"
            self.query_one("#re_add_list_button", Button).add_class(
                "last-clicked"
            )
            self.query_one("#re_add_tree_button", Button).remove_class(
                "last-clicked"
            )
        elif event.button.id == "re_add_content_button":
            self.query_one(
                "#re_add_view_switcher", ContentSwitcher
            ).current = "re_add_content"
            self.query_one("#re_add_content_button", Button).add_class(
                "last-clicked"
            )
            self.query_one("#re_add_diff_button", Button).remove_class(
                "last-clicked"
            )
        elif event.button.id == "re_add_diff_button":
            self.query_one(
                "#re_add_view_switcher", ContentSwitcher
            ).current = "re_add_diff"
            self.query_one("#re_add_diff_button", Button).add_class(
                "last-clicked"
            )
            self.query_one("#re_add_content_button", Button).remove_class(
                "last-clicked"
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
        with Vertical(id="add_left_vertical", classes="tab-content-left"):
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
            PathView(id="add_path_view", classes="border-path-title"),
            classes="tab-content-right",
        )

    def on_mount(self) -> None:
        filtered_dir_tree = self.query_one("#add_tree", FilteredDirTree)
        filtered_dir_tree.show_root = False
        filtered_dir_tree.guide_depth = 3
        self.query_one(
            "#add_tree_container", ScrollableContainer
        ).border_title = chezmoi.dest_dir_str_spaced

        self.query_one("#add_left_vertical", Vertical).styles.min_width = (
            left_min_width()
        )
        self.query_one("#add_path_view", PathView).tab_id = "add_tab"

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()
        if event.node.data is not None:
            path_view = self.query_one("#add_path_view", PathView)
            path_view.path = event.node.data.path
            path_view.tab_id = "add_tab"

    def on_directory_tree_directory_selected(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        if event.node.data is not None:
            path_view = self.query_one("#add_path_view", PathView)
            path_view.path = event.node.data.path
            path_view.tab_id = "add_tab"

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
