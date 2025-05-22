"""Contains the widgets used to compose the main screen of chezmoi-mousse."""

import os
from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.containers import (
    Container,
    Horizontal,
    ScrollableContainer,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
import re
from chezmoi_mousse.config import unwanted
from collections.abc import Iterable
from textual.content import Content
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Collapsible,
    DataTable,
    DirectoryTree,
    Label,
    Link,
    ListItem,
    ListView,
    Pretty,
    RichLog,
    TabbedContent,
    TabPane,
    Static,
    Switch,
    Tree,
)

from chezmoi_mousse import FLOW
from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.components import (
    FilterSwitch,
    PathView,
    DiffView,
    ManagedTree,
    GitLog,
)

from chezmoi_mousse.components import ConfigDump
from chezmoi_mousse.config import filter_switch_data, pw_mgr_info


class ApplyTab(Horizontal):

    BINDINGS = [
        Binding(
            key="W,w",
            action="apply_path",
            description="write-dotfile",
            tooltip="write to dotfiles from your chezmoi repository",
        )
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="apply_tab_left"):
            yield ManagedTree(
                status_files=chezmoi.status_paths["apply_files"],
                status_dirs=chezmoi.status_paths["apply_dirs"],
                id="apply_tree",
                classes="left-side-tree",
            )
            with VerticalGroup(classes="filter-bar"):
                yield FilterSwitch(
                    switch_id="apply_tab_unchanged",
                    switch_data=filter_switch_data["unchanged"],
                )
        with TabbedContent(id="apply_tabs", classes="path-view-tabs"):
            with TabPane("Content"):
                yield PathView(id="apply_path_view")
            with TabPane("Diff"):
                yield DiffView(id="apply_diff_view")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        event.stop()
        assert event.node.data is not None
        self.query_one("#apply_path_view", PathView).path = (
            event.node.data.path
        )
        self.query_one("#apply_diff_view", DiffView).diff_spec = (
            event.node.data.path,
            "apply",
        )

    @on(TabbedContent.TabActivated)
    def handle_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        print(f"event: {event.pane.id}")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == "apply_tab_unchanged":
            self.query_one("#apply_tree", ManagedTree).unchanged = event.value

    def action_apply_path(self) -> None:
        self.notify("will apply path")


class ReAddTab(Horizontal):

    BINDINGS = [
        Binding(
            key="A,a",
            action="re_add_path",
            description="re-add-chezmoi",
            tooltip="overwrite chezmoi repository with your current dotfiles",
        )
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="re_add_tab_left"):
            yield ManagedTree(
                status_files=chezmoi.status_paths["re_add_files"],
                status_dirs=chezmoi.status_paths["re_add_dirs"],
                id="re_add_tree",
                classes="left-side-tree",
            )
            with VerticalGroup(classes="filter-bar"):
                yield FilterSwitch(
                    switch_id="re_add_tab_unchanged",
                    switch_data=filter_switch_data["unchanged"],
                )
        with TabbedContent(id="re_add_tabs", classes="path-view-tabs"):
            with TabPane("Content"):
                yield PathView(id="re_add_path_view")
            with TabPane("Diff"):
                yield DiffView(id="re_add_diff_view")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        event.stop()
        assert event.node.data is not None
        self.query_one("#re_add_path_view", PathView).path = (
            event.node.data.path
        )
        self.query_one("#re_add_diff_view", DiffView).diff_spec = (
            event.node.data.path,
            "re-add",
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == "re_add_tab_unchanged":
            self.query_one("#re_add_tree", ManagedTree).unchanged = event.value

    def action_re_add_path(self) -> None:
        self.notify("will re-add path")


class AddTab(Horizontal):

    BINDINGS = [
        Binding(
            key="A,a",
            action="add_path",
            description="chezmoi-add",
            tooltip="add new file to your chezmoi repository",
        )
    ]

    class FilteredDirTree(DirectoryTree):

        unmanaged_dirs = reactive(False)
        unwanted = reactive(False)

        def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
            managed_dirs = chezmoi.managed_dir_paths
            managed_files = chezmoi.managed_file_paths

            # Switches: Red - Green (default)
            if not self.unmanaged_dirs and not self.unwanted:
                return (
                    p
                    for p in paths
                    if (
                        p.is_file()
                        and (
                            p.parent in managed_dirs
                            or p.parent == chezmoi.dest_dir
                        )
                        and not self.is_unwanted_path(p)
                        and p not in managed_files
                    )
                    or (
                        p.is_dir()
                        and not self.is_unwanted_path(p)
                        and p in managed_dirs
                    )
                )
            # Switches: Green - Red
            elif self.unmanaged_dirs and not self.unwanted:
                return (
                    p
                    for p in paths
                    if p not in managed_files and not self.is_unwanted_path(p)
                )
            # Switches: Red - Green
            elif not self.unmanaged_dirs and self.unwanted:
                return (
                    p
                    for p in paths
                    if (
                        p.is_file()
                        and (
                            p.parent in managed_dirs
                            or p.parent == chezmoi.dest_dir
                        )
                        and p not in managed_files
                    )
                    or (p.is_dir() and p in managed_dirs)
                )
            # Switches: Green - Green, include all unmanaged paths
            elif self.unmanaged_dirs and self.unwanted:
                return (
                    p
                    for p in paths
                    if p.is_dir() or (p.is_file() and p not in managed_files)
                )
            else:
                return paths

        def is_unwanted_path(self, path: Path) -> bool:
            if path.is_dir():
                if path.name in unwanted["dirs"]:
                    return True
            if path.is_file():
                extension = re.match(r"\.[^.]*$", path.name)
                if extension in unwanted["files"]:
                    return True
            return False

    def compose(self) -> ComposeResult:
        with Vertical(id="add_tab_left"):
            yield AddTab.FilteredDirTree(
                chezmoi.dest_dir, id="add_tree", classes="dir-tree"
            )
            with VerticalGroup(classes="filter-bar"):
                yield FilterSwitch(
                    switch_id="add_tab_unmanaged_dirs",
                    switch_data=filter_switch_data["unmanaged_dirs"],
                )
                yield FilterSwitch(
                    switch_id="add_tab_unwanted",
                    switch_data=filter_switch_data["unwanted"],
                )
        with Vertical(id="add_tab_right"):
            yield PathView(id="add_path_view")

    def on_mount(self) -> None:
        self.query_exactly_one(AddTab.FilteredDirTree).show_root = False
        tree_title = Content.from_text(f" {chezmoi.dest_dir}{os.sep} ")

        add_tab_left = self.query_one("#add_tab_left", Vertical)
        add_tab_left.border_title = tree_title
        add_tab_left.styles.min_width = len(tree_title)

        add_tab_right = self.query_one("#add_tab_right", Vertical)
        add_tab_right.border_title = Content.from_text(" Path View ")

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()
        if event.node.data is not None:
            self.query_exactly_one(PathView).path = event.node.data.path
            title = f" {event.node.data.path.relative_to(chezmoi.dest_dir)} "
            self.query_one("#add_tab_right", Vertical).border_title = title

    def on_directory_tree_directory_selected(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        if event.node.data is not None:
            rich_log = self.query_one("#file_preview", RichLog)
            rich_log.clear()
            managed: bool = event.node.data.path in chezmoi.managed_dir_paths
            if managed:
                rich_log.write(f'Managed directory: "{event.node.data.path}"')
            else:
                rich_log.write(
                    f'Unmanaged directory: "{event.node.data.path}"'
                )
            unmanaged_files: list[Path] = chezmoi.unmanaged_in_d(
                event.node.data.path
            )
            if not unmanaged_files:
                rich_log.write("No unmanaged files in this directory.")
            else:
                rich_log.write("Unmanaged files in this directory:")
                for p in unmanaged_files:
                    rich_log.write(f'"{p}"')
                rich_log.write(
                    "Click chezmoi-add or hit A to add it to chezmoi."
                )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one("#add_tree", AddTab.FilteredDirTree)
        if event.switch.id == "add_tab_unmanaged_dirs":
            tree.unmanaged_dirs = event.value
            tree.reload()
        elif event.switch.id == "add_tab_unwanted":
            tree.unwanted = event.value
            tree.reload()

    def action_add_path(self) -> None:
        cursor_node = self.query_one(
            "#add_tree", AddTab.FilteredDirTree
        ).cursor_node
        self.notify(f"will add {cursor_node}")


class DoctorTab(VerticalScroll):

    class ConfigDumpModal(ModalScreen):

        BINDINGS = [
            Binding(
                key="escape", action="dismiss", description="close", show=False
            )
        ]

        def compose(self) -> ComposeResult:
            yield ConfigDump(id="configdump", classes="doctormodals")

        def on_mount(self) -> None:
            self.query_one("#configdump").border_title = (
                "chezmoi dump-config - command output"
            )
            self.query_one("#configdump").border_subtitle = (
                "double click or escape to close"
            )

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

        def on_click(self, event: Click) -> None:
            event.stop()
            if event.chain == 2:
                self.dismiss()

    def compose(self) -> ComposeResult:

        with Horizontal():
            yield DataTable(
                id="doctortable", classes="doctortable", show_cursor=False
            )
        with VerticalGroup(classes="collapsiblegroup"):
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
            yield Collapsible(
                ListView(id="cmdnotfound"), title="Commands Not Found"
            )

    def on_mount(self) -> None:

        styles = {
            "ok": f"{self.app.current_theme.success}",
            "warning": f"{self.app.current_theme.warning}",
            "error": f"{self.app.current_theme.error}",
            "info": f"{self.app.current_theme.foreground}",
        }

        list_view = self.query_one("#cmdnotfound", ListView)
        table = self.query_one("#doctortable", DataTable)
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


class DiagramTab(Container):

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static(FLOW, id="diagram_text")
