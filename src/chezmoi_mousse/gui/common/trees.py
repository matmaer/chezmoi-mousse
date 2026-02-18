from pathlib import Path

from textual import on
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse import (
    AppIds,
    AppType,
    Chars,
    DirNode,
    StatusCode,
    TabName,
    Tcss,
    TreeName,
)

from .messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg

__all__ = ["ListTree", "ManagedTree"]


class TreeBase(Tree[Path], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    def __init__(self, ids: "AppIds", *, tree_name: TreeName) -> None:
        super().__init__(
            label="root", id=ids.tree_id(tree=tree_name), classes=Tcss.tree_widget
        )
        self.ids = ids
        self.tree_name = tree_name

    def on_mount(self) -> None:
        self.show_root = False
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top)
        self.make_node_colors_dict()

    @property
    def dir_nodes(self) -> dict[Path, DirNode]:
        if self.ids.canvas_name == TabName.apply:
            return self.app.cmd_results.apply_dir_nodes
        else:
            return self.app.cmd_results.re_add_dir_nodes

    def make_node_colors_dict(self) -> None:
        self.node_colors: dict[str, str] = {
            StatusCode.Added: self.app.theme_variables["text-success"],
            StatusCode.Deleted: self.app.theme_variables["text-error"],
            StatusCode.Modified: self.app.theme_variables["text-warning"],
            StatusCode.No_Change: self.app.theme_variables["warning-darken-2"],
            StatusCode.Run: self.app.theme_variables["error"],
            StatusCode.No_Status: self.app.theme_variables["text-secondary"],
        }

    def create_colored_label(self, path: Path) -> str:
        label_text = (
            str(path.relative_to(self.app.cmd_results.dest_dir))
            if self.tree_name == TreeName.list_tree
            else path.name
        )

        # Get status code for the path
        status = StatusCode.No_Status
        for dir_node in self.dir_nodes.values():
            if path in dir_node.status_files_in:
                status = dir_node.status_files_in[path]
                break
        else:
            status = self.dir_nodes[path].dir_status

        # Get color and create styled label
        color = self.node_colors.get(status, self.node_colors[StatusCode.No_Status])
        italic = " italic" if not path.exists() else ""
        return f"[{color}{italic}]{label_text}[/]"

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
            for file_path in dir_node.status_files_in:
                # only add files as leaves, if they were not added already.
                if not any(
                    child.data and child.data == file_path
                    for child in self.root.children
                ):
                    colored_label = self.create_colored_label(file_path)
                    self.root.add_leaf(colored_label, data=file_path)


class ManagedTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(ids, tree_name=TreeName.managed_tree)
        self.expanded_nodes: dict[int, TreeNode[Path]] = {}

    def populate_dest_dir(self) -> None:
        self.expanded_nodes[0] = self.root
        self.root.data = self.app.cmd_results.dest_dir
        dir_node = self.dir_nodes[self.app.cmd_results.dest_dir]
        for dir_path, _ in dir_node.dirs_in_for_tree.items():
            self.root.add(self.create_colored_label(dir_path), data=dir_path)
        for file_path, _ in dir_node.status_files_in.items():
            self.root.add_leaf(self.create_colored_label(file_path), data=file_path)

    @on(Tree.NodeExpanded)
    def handle_node_expanded(self, event: Tree.NodeExpanded[Path]) -> None:
        self.expanded_nodes[event.node.id] = event.node
        self.notify(f"Node collapsed: {event.node.data}")

    @on(Tree.NodeCollapsed)
    def handle_node_collapsed(self, event: Tree.NodeCollapsed[Path]) -> None:
        if event.node.id in self.expanded_nodes:
            del self.expanded_nodes[event.node.id]
