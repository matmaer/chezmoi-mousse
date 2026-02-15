from pathlib import Path

from textual import on
from textual.reactive import reactive
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse import AppIds, AppType, Chars, StatusCode, TabName, Tcss, TreeName

from .messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg

__all__ = ["ListTree", "ManagedTree"]


class TreeBase(Tree[Path], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "AppIds", *, tree_name: TreeName) -> None:
        super().__init__(
            label="root", id=ids.tree_id(tree=tree_name), classes=Tcss.tree_widget
        )
        if ids.canvas_name == TabName.apply:
            self.dir_nodes = self.app.cmd_results.apply_dir_nodes
        else:
            self.dir_nodes = self.app.cmd_results.re_add_dir_nodes
        self.ids = ids

    def on_mount(self) -> None:
        self.show_root = False
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top)
        self.update_node_colors()

    def update_node_colors(self) -> None:
        self.node_colors: dict[str, str] = {
            StatusCode.Added: self.app.theme_variables["text-success"],
            StatusCode.Deleted: self.app.theme_variables["text-error"],
            StatusCode.Modified: self.app.theme_variables["text-warning"],
            StatusCode.No_Change: self.app.theme_variables["warning-darken-2"],
            StatusCode.Run: self.app.theme_variables["error"],
            StatusCode.No_Status: self.app.theme_variables["text-secondary"],
        }

    # def create_label(self, path: Path, tab_name: TabName) -> str:
    #     italic = " italic" if not path.exists() else ""
    #     apply_color = self.node_colors.get(
    #         self.apply_file_status.get(path, StatusCode.No_Status)
    #     )
    #     if tab_name == TabName.apply:
    #         apply_color = self.node_colors.get(
    #             self.apply_file_status.get(path, StatusCode.No_Status)
    #         )
    #         return f"[{apply_color}" f"{italic}]{path.name}[/]"
    #     elif tab_name == TabName.re_add:
    #         re_add_color = self.node_colors.get(
    #             self.re_add_file_status.get(path, StatusCode.No_Status)
    #         )
    #         return f"[{re_add_color}" f"{italic}]{path.name}[/]"
    #     else:
    #         raise ValueError(f"Unhandled tab name: {tab_name}")

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data is None:
            raise ValueError("event.node.data is None in send_node_context")
        if self.ids.canvas_name == TabName.apply:
            self.post_message(CurrentApplyNodeMsg(event.node.data))
        elif self.ids.canvas_name == TabName.re_add:
            self.post_message(CurrentReAddNodeMsg(event.node.data))


class ListTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(ids, tree_name=TreeName.list_tree)

    def populate_dest_dir(self) -> None:
        self.clear()
        for dir_node in self.dir_nodes.values():
            for file_path in dir_node.status_files:
                # only add files as leaves, if they were not added already.
                if not any(
                    child.data and child.data == file_path
                    for child in self.root.children
                ):
                    # show relative path from dest_dir as label
                    relative_path = file_path.relative_to(self.app.cmd_results.dest_dir)
                    self.root.add_leaf(str(relative_path), data=file_path)


class ManagedTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(ids, tree_name=TreeName.managed_tree)

    def populate_dest_dir(self) -> None:
        self.clear()
        nodes: dict[Path, TreeNode[Path]] = {self.app.cmd_results.dest_dir: self.root}
        self.root.data = self.app.cmd_results.dest_dir
        # Sort directories by path depth to ensure parents are added before children
        for dir_path in sorted(self.dir_nodes.keys(), key=lambda p: len(p.parts)):
            dir_node = self.dir_nodes[dir_path]
            if dir_path == self.app.cmd_results.dest_dir:
                # Add files directly under the root
                for file_path, _ in dir_node.status_files.items():
                    self.root.add_leaf(file_path.name, data=file_path)
            else:
                parent_node: TreeNode[Path] = nodes[dir_path.parent]
                new_node = parent_node.add(dir_path.name, data=dir_path)
                nodes[dir_path] = new_node
                # Add files as leaves under this directory
                for file_path, _ in dir_node.status_files.items():
                    new_node.add_leaf(file_path.name, data=file_path)
