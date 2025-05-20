"""Contains the widgets used to compose the main screen of chezmoi-mousse."""

import os
from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    ScrollableContainer,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
from textual.content import Content
from textual.widgets import (
    Collapsible,
    DataTable,
    Label,
    Link,
    ListItem,
    ListView,
    Pretty,
    Static,
    Switch,
    Tree,
)

from chezmoi_mousse import FLOW
from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.components import (
    FilterSwitch,
    FilteredDirTree,
    PathView,
    PathViewTabs,
    ManagedTree,
)

from chezmoi_mousse.config import filter_switch_data, pw_mgr_info
from chezmoi_mousse.modalscreens import ConfigDump, GitLog, Operate


class ApplyTab(Horizontal):

    BINDINGS = [
        Binding(
            key="F,f",
            action="toggle_filterbar",
            description="filter",
            tooltip="show/hide filter",
        ),
        Binding(
            key="W,w",
            action="apply_path",
            description="write-dotfile",
            tooltip="write to dotfiles from your chezmoi repository",
        ),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield ManagedTree(
                status_files=chezmoi.status_paths["apply_files"],
                status_dirs=chezmoi.status_paths["apply_dirs"],
                id="apply_tree",
                classes="left-side-tree",
            )
        with Vertical():
            yield PathViewTabs(id="apply_path_view", classes="tree-right-side")

    def action_apply_path(self) -> None:
        self.notify("will apply path")

    @on(Tree.NodeSelected)
    def update_preview_path(self, event: Tree.NodeSelected) -> None:
        assert event.node.data is not None
        path_view_tabs = self.query_one("#apply_path_view", PathViewTabs)
        if event.node.data is not None:
            self.query_exactly_one(PathViewTabs).selected_path = (
                event.node.data.path
            )
        if event.node.data.path in chezmoi.status_paths["re_add_files"]:
            path_view_tabs.diff_lines = chezmoi.apply_diff(
                str(event.node.data.path)
            )
        else:
            path_view_tabs.diff_lines = ["no diff available"]

    @on(Switch.Changed)
    def notify_apply_tree(self, event: Switch.Changed) -> None:
        apply_tree = self.query_one("#apply_tree", ManagedTree)
        if event.switch.id == "apply_tab_include_unchanged_files":
            apply_tree.include_unchanged_files = event.value


# class ReAddTab(Horizontal):

#     BINDINGS = [
#         Binding(
#             key="F,f",
#             action="toggle_filterbar",
#             description="filter",
#             tooltip="show or hide filter",
#         ),
#         Binding(
#             key="A,a",
#             action="re_add_path",
#             description="re-add-chezmoi",
#             tooltip="overwrite chezmoi repository with your current dotfiles",
#         ),
#     ]

#     def compose(self) -> ComposeResult:
#         with Vertical():
#             yield TreeHeader(classes="tree-title")
#             yield ManagedTree(
#                 status_files=chezmoi.status_paths["re_add_files"],
#                 status_dirs=chezmoi.status_paths["re_add_dirs"],
#                 id="re_add_tree",
#                 classes="left-side-tree",
#             )
#         yield PathViewTabs(id="re_add_path_view", classes="tree-right-side")

#     def action_re_add_path(self) -> None:
#         self.notify("will re-add path")

#     def on_resize(self) -> None:
#         self.query_one("#re_add_tree", ManagedTree).focus()

#     @on(Tree.NodeSelected)
#     def update_preview_path(self, event: Tree.NodeSelected) -> None:
#         assert event.node.data is not None
#         path_view_tabs = self.query_one("#re_add_path_view", PathViewTabs)
#         if event.node.data is not None:
#             path_view_tabs.selected_path = event.node.data.path
#         if event.node.data.path in chezmoi.status_paths["re_add_files"]:
#             path_view_tabs.diff_lines = chezmoi.re_add_diff(
#                 str(event.node.data.path)
#             )
#         else:
#             path_view_tabs.diff_lines = ["no diff available"]

#     @on(Switch.Changed)
#     def notify_re_add_tree(self, event: Switch.Changed) -> None:
#         if event.switch.id == "re_add_tab_include_unchanged_files":
#             re_add_tree = self.query_one("#re_add_tree", ManagedTree)
#             re_add_tree.include_unchanged_files = event.value


class AddTab(Horizontal):

    BINDINGS = [
        Binding(
            key="A,a",
            action="add_path",
            description="add-chezmoi",
            tooltip="add new file to your chezmoi repository",
        )
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="add_tab_left"):
            yield FilteredDirTree(
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
        self.query_exactly_one(FilteredDirTree).show_root = False
        tree_title = Content.from_text(f" {chezmoi.dest_dir}{os.sep} ")

        add_tab_left = self.query_one("#add_tab_left", Vertical)
        add_tab_left.border_title = tree_title
        add_tab_left.styles.min_width = len(tree_title)

        add_tab_right = self.query_one("#add_tab_right", Vertical)
        add_tab_right.border_title = Content.from_text(" Path View ")

    @on(FilteredDirTree.FileSelected)
    def update_preview_path(self, event: FilteredDirTree.FileSelected) -> None:
        if event.node.data is not None:
            self.query_exactly_one(PathView).path = event.node.data.path
            title = f" {event.node.data.path.relative_to(chezmoi.dest_dir)} "
            self.query_one("#add_tab_right", Vertical).border_title = title

    def action_add_path(self) -> None:
        cursor_node = self.query_one(
            "#filtered_dir_tree", FilteredDirTree
        ).cursor_node
        if cursor_node is not None:
            assert isinstance(cursor_node.data, Path)
            self.app.push_screen(Operate(cursor_node.data.path))

    def on_switch_changed(self, event: Switch.Changed) -> None:
        tree = self.query_one("#add_tree", FilteredDirTree)
        if event.switch.id == "add_tab_unmanaged_dirs":
            tree.unmanaged_dirs = event.value
            tree.reload()
        elif event.switch.id == "add_tab_unwanted":
            tree.unwanted = event.value
            tree.reload()


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

    def action_open_config(self) -> None:
        self.app.push_screen(ConfigDump())

    def action_git_log(self) -> None:
        self.app.push_screen(GitLog())


class DiagramTab(Container):

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static(FLOW, id="diagram_text")
