import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import ContentSwitcher
from textual.widgets.tree import TreeNode

from chezmoi_mousse import CMD, AppType, DirNode, OpBtnEnum, TabLabel, Tcss

from .actionables import OpButton, TabButton, TabButtons
from .contents import ContentsView
from .diffs import DiffView
from .git_log import GitLogView
from .trees import ListTree, ManagedTree

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["TreeSwitcher", "ViewSwitcher"]


class TreeSwitcher(Vertical, AppType):

    unchanged: reactive[bool] = reactive(False)
    expand_all: reactive[bool] = reactive(False)

    def __init__(self, ids: "AppIds"):
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids
        self.old_expanded_nodes: list[TreeNode[Path]] = []

    def compose(self) -> ComposeResult:
        yield TabButtons(self.ids, (TabLabel.tree, TabLabel.list))
        with ContentSwitcher(
            initial=self.ids.tree.managed, classes=Tcss.tree_content_switcher
        ):
            yield ManagedTree(self.ids)
            yield ListTree(self.ids)
        yield OpButton(
            btn_enum=OpBtnEnum.refresh_tree,
            btn_id=self.ids.op_btn.refresh_tree,
            app_ids=self.ids,
        )

    def on_mount(self) -> None:
        refresh_btn = self.query_one(self.ids.op_btn.refresh_tree_q, OpButton)
        refresh_btn.remove_class(Tcss.operate_button)
        refresh_btn.add_class(Tcss.refresh_button)
        self.content_switcher = self.query_exactly_one(ContentSwitcher)

    @property
    def dir_nodes(self) -> dict[Path, "DirNode"]:
        if self.ids.canvas_name == TabLabel.apply:
            return CMD.cache.apply_dir_nodes
        else:
            return CMD.cache.re_add_dir_nodes

    @on(TabButton.Pressed)
    def switch_view(self, event: TabButton.Pressed) -> None:
        if event.button.label == TabLabel.tree:
            self.content_switcher.current = self.ids.tree.managed
        elif event.button.label == TabLabel.list:
            self.content_switcher.current = self.ids.tree.list

    def _get_managed_tree_nodes(self) -> list[TreeNode[Path]]:
        managed_tree = self.query_exactly_one(ManagedTree)
        return managed_tree.get_all_nodes()

    def _populate_x_node(self, tree_node: TreeNode[Path], dir_path: Path) -> None:
        if tree_node.data is None:
            return
        dir_node = CMD.cache.get_dir_node(tree_node.data, self.ids.canvas_name)
        for x_file in CMD.cache.get_x_files_in(dir_path):
            tree_node.add_leaf(f"[dim]{x_file.name}[/]", x_file)

        for x_sub_dir in dir_node.tree_x_dirs_in:
            new_x_node = tree_node.add(f"[dim]{x_sub_dir.name}[/]", data=x_sub_dir)
            if self.expand_all:
                new_x_node.expand()
            self._populate_x_node(new_x_node, x_sub_dir)

    def watch_expand_all(self, expand_all: bool) -> None:
        nodes_before_toggle = self._get_managed_tree_nodes()
        if expand_all is True:
            self.old_expanded_nodes = [
                node for node in nodes_before_toggle if node.is_expanded
            ]
            for node in nodes_before_toggle:
                node.expand()
        else:
            for node in nodes_before_toggle:
                if node not in self.old_expanded_nodes:
                    node.collapse()

    def watch_unchanged(self, unchanged: bool) -> None:
        nodes_before_toggle = self._get_managed_tree_nodes()
        list_tree = self.query_exactly_one(ListTree)
        list_tree_nodes = list_tree.get_all_nodes()
        if unchanged is True:
            for node in nodes_before_toggle:
                # Add unchanged children to nodes already in the tree (the changed ones)
                if node.data in self.dir_nodes:
                    dir_node = CMD.cache.get_dir_node(node.data, self.ids.canvas_name)
                    x_files_in = CMD.cache.get_x_files_in(node.data)
                    # Only populate if there are actual unchanged paths in this
                    # directory
                    if x_files_in or dir_node.tree_x_dirs_in:
                        self._populate_x_node(node, node.data)
                        # Only expand if expand_all is enabled
                        if self.expand_all:
                            node.expand()

            for x_file in CMD.cache.sets.x_files:
                if x_file in [node.data for node in list_tree_nodes]:
                    continue
                rel_path = str(x_file.relative_to(CMD.cache.dest_dir))
                list_tree.root.add_leaf(f"[dim]{rel_path}[/]", x_file)
        elif unchanged is False:
            # remove x_files and x_dirs from managed tree
            for tree_node in nodes_before_toggle:
                if (
                    tree_node.data in CMD.cache.sets.x_files
                    or tree_node.data in CMD.cache.tree_x_dirs
                ):
                    with contextlib.suppress(Exception):
                        tree_node.remove()
            # remove x_files from list tree
            for tree_node in list_tree_nodes:
                if tree_node.data in CMD.cache.sets.x_files:
                    tree_node.remove()


class ViewSwitcher(Vertical):

    def __init__(self, ids: "AppIds"):
        super().__init__(id=ids.container.right_side)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield TabButtons(self.ids, (TabLabel.diff, TabLabel.contents, TabLabel.git_log))
        with ContentSwitcher(initial=self.ids.container.diff):
            yield DiffView(self.ids)
            yield ContentsView(self.ids)
            yield GitLogView(self.ids)

    def on_mount(self) -> None:
        self.view_switcher = self.query_exactly_one(ContentSwitcher)
        self.tab_buttons = self.query_exactly_one(Horizontal)
        self.content_switcher = self.query_exactly_one(ContentSwitcher)

    @on(TabButton.Pressed)
    def switch_view(self, event: TabButton.Pressed) -> None:
        event.stop()
        if event.button.label == TabLabel.contents:
            self.content_switcher.current = self.ids.container.contents
        elif event.button.label == TabLabel.diff:
            self.content_switcher.current = self.ids.container.diff
        elif event.button.label == TabLabel.git_log:
            self.content_switcher.current = self.ids.container.git_log
