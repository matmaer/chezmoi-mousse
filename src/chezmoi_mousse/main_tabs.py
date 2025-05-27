"""Contains the widgets used to compose the main screen of chezmoi-mousse."""

import os
from pathlib import Path

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
    TabbedContent,
    TabPane,
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


def left_min_width(add_tab: bool = False) -> int:
    dest_dir_length = len(str(chezmoi.dest_dir)) + 4  # for double padding
    # 8 for the filter switch, 2 for title padding right and the border
    if add_tab:
        max_filter_width = (
            max(len(f.label) for f in vars(filter_data).values()) + 8 + 2
        )
    else:
        max_filter_width = len(filter_data.unchanged.label) + 8 + 2
    return max(dest_dir_length, max_filter_width)


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
        with Vertical(id="apply_left_vertical", classes="tab-content-left"):
            yield Horizontal(
                Vertical(
                    Button("Tree", id="apply_button_tree"),
                    classes="center-content",
                ),
                Vertical(
                    Button("List", id="apply_button_status"),
                    classes="center-content",
                ),
                classes="tree_buttons_horizontal",
                id="apply_tree_buttons_horizontal",
            )
            with ContentSwitcher(initial="apply_tree", id="apply_switcher"):
                yield ManagedTree(id="apply_tree")
                yield Static("List of files with status", id="apply_list")
            yield Vertical(
                HorizontalGroup(
                    Switch(id="apply_tab_unchanged", classes="filter-switch"),
                    Label(
                        filter_data.unchanged.label, classes="filter-label"
                    ).with_tooltip(tooltip=filter_data.unchanged.tooltip),
                ),
                classes="filter-container",
            )
        with TabbedContent(id="apply_view_tabs", classes="tab-content-right"):
            with TabPane("Content", id="apply_content_pane"):
                yield PathView(id="apply_path_view")
            with TabPane("Diff", id="apply_diff_pane"):
                yield DiffView(id="apply_diff_view")

    def on_mount(self) -> None:
        self.query_one("#apply_left_vertical", Vertical).styles.min_width = (
            left_min_width()
        )
        self.query_one(
            "#apply_tree_buttons_horizontal", Horizontal
        ).border_subtitle = f"{chezmoi.dest_dir}{os.sep}"

    def on_tree_node_selected(self, event: ManagedTree.NodeSelected) -> None:
        event.stop()
        assert event.node.data is not None
        self.query_exactly_one(PathView).path = event.node.data.path
        self.query_one("#apply_diff_view", DiffView).diff_spec = (
            event.node.data.path,
            "apply",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "apply_button_tree":
            self.query_one("#apply_switcher", ContentSwitcher).current = (
                "apply_tree"
            )
        elif event.button.id == "apply_button_status":
            self.query_one("#apply_switcher", ContentSwitcher).current = (
                "apply_list"
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
        with Vertical(id="re_add_left_vertical", classes="tab-content-left"):
            yield Horizontal(
                Vertical(
                    Button("Tree", id="re_add_button_tree"),
                    classes="center-content",
                ),
                Vertical(
                    Button("List", id="re_add_button_status"),
                    classes="center-content",
                ),
                classes="tree_buttons_horizontal",
                id="re_add_tree_buttons_horizontal",
            )
            with ContentSwitcher(initial="re_add_tree", id="re_add_switcher"):
                yield ManagedTree(id="re_add_tree")
                yield Static("List of files with status", id="re_add_list")
            yield Vertical(
                HorizontalGroup(
                    Switch(id="re_add_tab_unchanged", classes="filter-switch"),
                    Label(
                        filter_data.unchanged.label, classes="filter-label"
                    ).with_tooltip(tooltip=filter_data.unchanged.tooltip),
                ),
                classes="filter-container",
            )
        with TabbedContent(id="re_add_view_tabs", classes="tab-content-right"):
            with TabPane("Content", id="re_add_content_pane"):
                yield PathView(id="re_add_path_view")
            with TabPane("Diff", id="re_add_diff_pane"):
                yield DiffView(id="re_add_diff_view")

    def on_mount(self) -> None:
        self.query_one("#re_add_left_vertical", Vertical).styles.min_width = (
            left_min_width()
        )
        self.query_one(
            "#re_add_tree_buttons_horizontal", Horizontal
        ).border_subtitle = f"{chezmoi.dest_dir}{os.sep}"

    def on_tree_node_selected(self, event: ManagedTree.NodeSelected) -> None:
        event.stop()
        assert event.node.data is not None
        self.query_exactly_one(PathView).path = event.node.data.path
        self.query_one("#re_add_diff_view", DiffView).diff_spec = (
            event.node.data.path,
            "re-add",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "re_add_button_tree":
            self.query_one("#re_add_switcher", ContentSwitcher).current = (
                "re_add_tree"
            )
        elif event.button.id == "re_add_button_status":
            self.query_one("#re_add_switcher", ContentSwitcher).current = (
                "re_add_list"
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
            PathView(classes="border-path-title"), classes="tab-content-right"
        )

    def on_mount(self) -> None:
        filtered_dir_tree = self.query_one(FilteredDirTree)
        filtered_dir_tree.show_root = False
        filtered_dir_tree.guide_depth = 3
        self.query_one(
            "#add_tree_container", ScrollableContainer
        ).border_title = f"{chezmoi.dest_dir}{os.sep}"

        self.query_one("#add_left_vertical", Vertical).styles.min_width = (
            left_min_width(add_tab=True)
        )

        self.query_exactly_one(PathView).border_title = "Path View"

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()
        if event.node.data is not None:
            self.query_exactly_one(PathView).path = event.node.data.path
            title = f"{event.node.data.path.relative_to(chezmoi.dest_dir)}"
            self.query_exactly_one(PathView).border_title = title

    def on_directory_tree_directory_selected(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        if event.node.data is not None:
            path_view = self.query_exactly_one(PathView)
            path_view.clear()
            title = f"{event.node.data.path.relative_to(chezmoi.dest_dir)}"
            path_view.border_title = title
            managed: bool = event.node.data.path in chezmoi.managed_dir_paths
            if managed:
                path_view.write(f"Managed directory: {event.node.data.path}\n")
            else:
                path_view.write(
                    f"Unmanaged directory: {event.node.data.path}\n"
                )
            unmanaged_files: list[Path] = chezmoi.unmanaged_in_d(
                event.node.data.path
            )
            managed_files: list[Path] = chezmoi.managed_file_paths_in_dir(
                event.node.data.path
            )
            managed_dirs: list[Path] = chezmoi.managed_dir_paths_in_dir(
                event.node.data.path
            )
            if managed_dirs:
                path_view.write("Contains managed sub dirs:")
                for p in managed_dirs:
                    path_view.write(str(p))
            if unmanaged_files:
                path_view.write("Contains unmanaged files:")
                for p in unmanaged_files:
                    path_view.write(str(p))
            if managed_files:
                path_view.write("Contains managed files:")
                for p in managed_files:
                    path_view.write(str(p))

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
            yield Pretty(chezmoi.dump_config.dict_out, id="config_dump_doctor")

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
