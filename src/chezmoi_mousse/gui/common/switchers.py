"""Contains subclassed textual classes shared between the ApplyTab and ReAddTab."""

from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher
from textual.widgets.tree import TreeNode

from chezmoi_mousse import AppType, DirNode, FlatBtnLabel, SubTabLabel, TabName, Tcss

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
        yield TabButtons(self.ids, buttons=(SubTabLabel.tree, SubTabLabel.list))
        with ContentSwitcher(
            id=self.ids.switcher.trees,
            initial=self.ids.tree.managed,
            classes=Tcss.content_switcher_left,
        ):
            yield ManagedTree(self.ids)
            yield ListTree(self.ids)
        yield Button(label=FlatBtnLabel.refresh_tree, classes=Tcss.refresh_button)

    @property
    def dir_nodes(self) -> dict[Path, "DirNode"]:
        if self.ids.canvas_name == TabName.apply:
            return self.app.apply_dir_nodes
        else:
            return self.app.re_add_dir_nodes

    @on(Button.Pressed)
    def switch_view(self, event: Button.Pressed) -> None:
        if event.button.has_class(Tcss.tab_button):
            event.stop()
            view_switcher = self.query_exactly_one(ContentSwitcher)
            if event.button.label == SubTabLabel.tree:
                view_switcher.current = self.ids.tree.managed
            elif event.button.label == SubTabLabel.list:
                view_switcher.current = self.ids.tree.list
            return
        if event.button.has_class(Tcss.refresh_button):
            event.stop()
            managed_tree = self.query_exactly_one(ManagedTree)
            managed_tree.populate_tree()
            list_tree = self.query_exactly_one(ListTree)
            list_tree.populate_tree()

    def get_managed_tree_nodes(self) -> list[TreeNode[Path]]:
        managed_tree = self.query_exactly_one(ManagedTree)
        return managed_tree.get_all_nodes()

    def watch_expand_all(self, expand_all: bool) -> None:
        nodes_before_expand_all_toggle = self.get_managed_tree_nodes()
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
        nodes_before_unchanged_toggle = self.get_managed_tree_nodes()
        list_tree = self.query_exactly_one(ListTree)
        list_tree_nodes = list_tree.get_all_nodes()
        if unchanged is True:
            for x_dir in self.app.tree_x_dirs:
                parent_tree_node = next(
                    (
                        node
                        for node in nodes_before_unchanged_toggle
                        if node.data == x_dir.parent
                    ),
                    None,
                )
                if parent_tree_node is not None:
                    new_x_node = parent_tree_node.add(
                        f"[dim]{x_dir.name}[/]", data=x_dir
                    )
                    if self.expand_all:
                        new_x_node.expand()
                    for x_file in self.dir_nodes[x_dir].x_files_in:
                        new_x_node.add_leaf(f"[dim]{x_file.name}[/]", x_file)
                    parent_tree_node.expand()

            for x_file in self.app.x_files:
                if x_file in [node.data for node in list_tree_nodes]:
                    continue
                rel_path = str(x_file.relative_to(self.app.dest_dir))
                list_tree.root.add_leaf(f"[dim]{rel_path}[/]", x_file)
        elif unchanged is False:
            # remove x_files and x_dirs from managed tree
            for tree_node in nodes_before_unchanged_toggle:
                if (
                    tree_node.data in self.app.x_files
                    or tree_node.data in self.app.tree_x_dirs
                ):
                    try:
                        tree_node.remove()
                    except Exception:
                        pass
            # remove x_files from list tree
            for tree_node in list_tree_nodes:
                if tree_node.data in self.app.x_files:
                    tree_node.remove()


class ViewSwitcher(Container):

    def __init__(self, ids: "AppIds"):
        super().__init__(id=ids.container.right_side)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield TabButtons(
            self.ids,
            buttons=(SubTabLabel.diff, SubTabLabel.contents, SubTabLabel.git_log),
        )
        with ContentSwitcher(initial=self.ids.container.diff):
            yield DiffView(self.ids)
            yield ContentsView(self.ids)
            yield GitLog(self.ids)

    @on(Button.Pressed, Tcss.tab_button.dot_prefix)
    def switch_view(self, event: Button.Pressed) -> None:
        view_switcher = self.query_exactly_one(ContentSwitcher)
        if event.button.label == SubTabLabel.contents:
            view_switcher.current = self.ids.container.contents
        elif event.button.label == SubTabLabel.diff:
            view_switcher.current = self.ids.container.diff
        elif event.button.label == SubTabLabel.git_log:
            view_switcher.current = self.ids.container.git_log
