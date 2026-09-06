"""This module is executed first by conftest.py"""

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

type AllNodesDict = dict[ast.AST, NodeData]
type NodeDataDict = dict[str, set[NodeData]]

MODULE_DIR = Path("src", "chezmoi_mousse")

MODULE_TREES: dict[Path, ast.Module] = {
    p: ast.parse(p.read_text(encoding="utf-8")) for p in MODULE_DIR.rglob("*.py")
}


@dataclass(slots=True, kw_only=True, eq=False)
class NodeData:
    """Stores enriched metadata for a single AST node."""

    ast_node: ast.AST
    str_rep: str | None = None
    file_path: Path
    rel_path: str
    node_type: str
    parent: "NodeData | None" = None
    children: list["NodeData"] = field(default_factory=lambda: [])
    depth: int = 0
    lineno: int | None = None
    col_offset: int | None = None

    @property
    def slots_var_elements(self) -> list[str]:
        if not isinstance(self.ast_node, ast.Assign):
            return []
        if isinstance(self.ast_node.value, ast.List):
            slots_elements: list[str] = []
            for elt in self.ast_node.value.elts:
                assert isinstance(elt, ast.Constant)
                assert isinstance(elt.value, str)
                slots_elements.append(elt.value)
            return slots_elements
        else:
            assert isinstance(self.ast_node.value, ast.Constant)
            assert isinstance(self.ast_node.value.value, str)
            return [self.ast_node.value.value]


@dataclass
class NodeDb:
    """AST database populated upfront, using lazy cached properties for queries."""

    all_nodes: AllNodesDict = field(default_factory=dict[ast.AST, NodeData])
    by_name: NodeDataDict = field(default_factory=lambda: defaultdict(set))
    by_path: NodeDataDict = field(default_factory=lambda: defaultdict(set))
    by_type: NodeDataDict = field(default_factory=lambda: defaultdict(set))
    nodes_without_name: set[NodeData] = field(default_factory=set[NodeData])

    def __post_init__(self) -> None:
        for file_path, tree in MODULE_TREES.items():
            indexer = IndexerVisitor(file_path=file_path, all_nodes=self.all_nodes)
            indexer.visit(tree)
        # shortcuts
        for data in self.all_nodes.values():
            if data.str_rep:
                self.by_name[data.str_rep].add(data)
            else:
                self.nodes_without_name.add(data)
            self.by_path[data.rel_path].add(data)
            self.by_type[data.node_type].add(data)


class IndexerVisitor(ast.NodeVisitor):
    """Visitor that indexes every node into all_nodes and maintains parent-child
    edges."""

    def __init__(self, file_path: Path, all_nodes: dict[ast.AST, NodeData]) -> None:
        self.all_nodes = all_nodes
        self.file_path = file_path
        self._parent_stack: list[NodeData] = []

    def _find_str_attrib(self, node: ast.AST) -> str | None:
        result: str | None = None
        target = node.func if isinstance(node, ast.Call) else node
        for attr in ("name", "id", "arg", "attr", "label", "module"):
            if isinstance(str_attr := getattr(target, attr, None), str):
                result = str_attr
        return result

    def generic_visit(self, node: ast.AST) -> None:
        parent = self._parent_stack[-1] if self._parent_stack else None

        node_data = NodeData(
            ast_node=node,
            str_rep=self._find_str_attrib(node),
            file_path=self.file_path.relative_to(MODULE_DIR),
            rel_path=str(self.file_path.relative_to(MODULE_DIR)),
            node_type=type(node).__name__,
            parent=parent,
            depth=len(self._parent_stack),
            lineno=getattr(node, "lineno", None),
            col_offset=getattr(node, "col_offset", None),
        )

        if parent is not None:
            parent.children.append(node_data)

        self.all_nodes[node] = node_data

        self._parent_stack.append(node_data)
        super().generic_visit(node)
        self._parent_stack.pop()
