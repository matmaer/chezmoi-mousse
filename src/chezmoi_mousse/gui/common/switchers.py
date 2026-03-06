import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher
from textual.widgets.tree import TreeNode

from chezmoi_mousse import CMD, AppType, DirNode, FlatBtnLabel, TabLabel, Tcss

from .actionables import TabButtons
from .contents import ContentsView
from .diffs import DiffView
from .git_log import GitLog
from .trees import ListTree, ManagedTree

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["TreeSwitcher", "ViewSwitcher"]


class TreeSwitcher(Container, AppType):

    unchanged: reactive[bool] = reactive(False)
    expand_all: reactive[bool] = reactive(False)

    def __init__(self, ids: "AppIds"):
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids
        self.old_expanded_nodes: list[TreeNode[Path]] = []

    def compose(self) -> ComposeResult:
        yield TabButtons(self.ids, buttons=(TabLabel.tree, TabLabel.list))
        with ContentSwitcher(
            initial=self.ids.tree.managed, classes=Tcss.tree_content_switcher
        ):
            yield ManagedTree(self.ids)
            yield ListTree(self.ids)
        yield Button(label=FlatBtnLabel.refresh_tree, classes=Tcss.refresh_button)

    @property
    def dir_nodes(self) -> dict[Path, "DirNode"]:
        if self.ids.canvas_name == TabLabel.apply:
            return CMD.cache.apply_dir_nodes
        else:
            return CMD.cache.re_add_dir_nodes

    @on(Button.Pressed)
    def switch_view(self, event: Button.Pressed) -> None:
        if event.button.has_class(Tcss.tab_button):
            view_switcher = self.query_exactly_one(ContentSwitcher)
            if event.button.label == TabLabel.tree:
                view_switcher.current = self.ids.tree.managed
            elif event.button.label == TabLabel.list:
                view_switcher.current = self.ids.tree.list
            return

    @on(Button.Pressed)
    async def refresh_tree(self, event: Button.Pressed) -> None:
        if event.button.has_class(Tcss.refresh_button):
            event.stop()
            worker = self.app.refresh_cmd_results()
            await worker.wait()
            managed_tree = self.query_exactly_one(ManagedTree)
            managed_tree.populate_tree()
            list_tree = self.query_exactly_one(ListTree)
            list_tree.populate_tree()

    def _get_managed_tree_nodes(self) -> list[TreeNode[Path]]:
        managed_tree = self.query_exactly_one(ManagedTree)
        return managed_tree.get_all_nodes()

    def _populate_x_node(self, tree_node: TreeNode[Path], dir_path: Path) -> None:
        dir_node = self.dir_nodes[dir_path]
        for x_file in dir_node.x_files_in:
            tree_node.add_leaf(f"[dim]{x_file.name}[/]", x_file)

        for x_sub_dir in dir_node.tree_x_dirs_in:
            new_x_node = tree_node.add(f"[dim]{x_sub_dir.name}[/]", data=x_sub_dir)
            if self.expand_all:
                new_x_node.expand()
            self._populate_x_node(new_x_node, x_sub_dir)

    def watch_expand_all(self, expand_all: bool) -> None:
        nodes_before_expand_all_toggle = self._get_managed_tree_nodes()
        if expand_all is True:
            self.old_expanded_nodes = [
                node for node in nodes_before_expand_all_toggle if node.is_expanded
            ]
            for node in nodes_before_expand_all_toggle:
                node.expand()
        else:
            for node in nodes_before_expand_all_toggle:
                if node not in self.old_expanded_nodes:
                    node.collapse()

    def watch_unchanged(self, unchanged: bool) -> None:
        nodes_before_unchanged_toggle = self._get_managed_tree_nodes()
        list_tree = self.query_exactly_one(ListTree)
        list_tree_nodes = list_tree.get_all_nodes()
        if unchanged is True:
            for node in nodes_before_unchanged_toggle:
                # Add unchanged children to nodes already in the tree (the changed ones)
                if node.data in self.dir_nodes:
                    dir_node = self.dir_nodes[node.data]
                    # Only populate if there are actual unchanged paths in this
                    # directory
                    if dir_node.x_files_in or dir_node.tree_x_dirs_in:
                        self._populate_x_node(node, node.data)
                        # Only expand if expand_all is enabled
                        if self.expand_all:
                            node.expand()

            for x_file in CMD.cache.x_files:
                if x_file in [node.data for node in list_tree_nodes]:
                    continue
                rel_path = str(x_file.relative_to(CMD.cache.dest_dir))
                list_tree.root.add_leaf(f"[dim]{rel_path}[/]", x_file)
        elif unchanged is False:
            # remove x_files and x_dirs from managed tree
            for tree_node in nodes_before_unchanged_toggle:
                if (
                    tree_node.data in CMD.cache.x_files
                    or tree_node.data in CMD.cache.tree_x_dirs
                ):
                    with contextlib.suppress(Exception):
                        tree_node.remove()
            # remove x_files from list tree
            for tree_node in list_tree_nodes:
                if tree_node.data in CMD.cache.x_files:
                    tree_node.remove()


class ViewSwitcher(Container):

    def __init__(self, ids: "AppIds"):
        super().__init__(id=ids.container.right_side)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield TabButtons(
            self.ids, buttons=(TabLabel.diff, TabLabel.contents, TabLabel.git_log)
        )
        with ContentSwitcher(initial=self.ids.container.diff):
            yield DiffView(self.ids)
            yield ContentsView(self.ids)
            yield GitLog(self.ids)

    def on_mount(self) -> None:
        self.tab_buttons = self.query_exactly_one(Horizontal)
        self.tab_buttons.border_subtitle = f" {CMD.cache.dest_dir} "

    @on(Button.Pressed)
    def switch_view(self, event: Button.Pressed) -> None:
        if event.button.label not in (
            TabLabel.diff,
            TabLabel.contents,
            TabLabel.git_log,
        ):
            return
        view_switcher = self.query_exactly_one(ContentSwitcher)
        if event.button.label == TabLabel.contents:
            view_switcher.current = self.ids.container.contents
        elif event.button.label == TabLabel.diff:
            view_switcher.current = self.ids.container.diff
        elif event.button.label == TabLabel.git_log:
            view_switcher.current = self.ids.container.git_log
