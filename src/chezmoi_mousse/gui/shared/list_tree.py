from typing import TYPE_CHECKING

from rich.text import Text
from textual.reactive import reactive

from chezmoi_mousse import AppType, Canvas, NodeData, TreeName

from .tree_base import TreeBase

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import CanvasIds

__all__ = ["ListTree"]


class ListTree(TreeBase, AppType):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.list_tree)

    def add_files_with_status(self) -> None:
        if self.active_canvas == Canvas.apply:
            status_files = self.app.chezmoi.all_status_files(
                active_canvas=Canvas.apply
            )
        else:
            status_files = self.app.chezmoi.all_status_files(
                active_canvas=Canvas.re_add
            )
        for file_path, status_code in status_files.items():
            node_data: NodeData = self.create_node_data(
                path=file_path, is_leaf=True, status_code=status_code
            )
            if (
                self.active_canvas == Canvas.re_add
                and node_data.found is False
            ):
                continue
            node_label: Text = self.style_label(node_data)
            self.root.add_leaf(label=node_label, data=node_data)

    def add_files_without_status(self) -> None:
        if self.active_canvas == Canvas.apply:
            self.files_without_status: list["Path"] = (
                self.app.chezmoi.apply_files_without_status
            )
        else:
            self.files_without_status: list["Path"] = (
                self.app.chezmoi.re_add_files_without_status
            )
        for file_path in self.files_without_status:
            node_data: NodeData = self.create_node_data(
                path=file_path, is_leaf=True, status_code="X"
            )
            if (
                self.active_canvas == Canvas.re_add
                and node_data.found is False
            ):
                continue
            node_label: Text = self.style_label(node_data)
            self.root.add_leaf(label=node_label, data=node_data)

    def watch_unchanged(self) -> None:
        if self.unchanged:
            self.add_files_without_status()
        else:
            self.remove_files_without_status_in(tree_node=self.root)
