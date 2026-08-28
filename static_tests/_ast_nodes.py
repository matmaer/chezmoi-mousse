"""This module is executed first by conftest.py"""

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

MODULE_DIR = Path("src", "chezmoi_mousse")

FILE_PATHS: list[Path] = [Path(path_str) for path_str in MODULE_DIR.rglob("*.py")]

MODULE_TREES: dict[Path, ast.Module] = {
    p: ast.parse(p.read_text(encoding="utf-8")) for p in FILE_PATHS
}


@dataclass(slots=True, kw_only=True, eq=False)
class NodeData:
    """Stores enriched metadata for a single AST node."""

    ast_node: ast.AST
    name: str | None = None
    file_path: Path
    rel_path: Path
    node_type: type[ast.AST]
    parent: ast.AST | None = None
    children: list[ast.AST] = field(default_factory=lambda: [])
    depth: int = 0
    lineno: int | None = None
    col_offset: int | None = None

    def get_ancestry(self, node_db: dict[ast.AST, "NodeData"]) -> list[ast.AST]:
        """Returns parent nodes starting from immediate parent up to the root."""
        ancestors: list[ast.AST] = []
        curr = self.parent
        while curr is not None:
            ancestors.append(curr)
            curr = node_db[curr].parent
        return ancestors


@dataclass
class NodeDb:
    """AST database populated upfront, using lazy cached properties for queries."""

    all_nodes: dict[ast.AST, NodeData] = field(default_factory=lambda: {})

    def __post_init__(self) -> None:
        for file_path, tree in MODULE_TREES.items():
            indexer = IndexerVisitor(file_path=file_path, all_nodes=self.all_nodes)
            indexer.visit(tree)

    # --- Lazy Private Properties ---

    @cached_property
    def _nodes_by_type(self) -> dict[type[ast.AST], set[NodeData]]:
        by_type: defaultdict[type[ast.AST], set[NodeData]] = defaultdict(set)
        for node_data in self.all_nodes.values():
            by_type[node_data.node_type].add(node_data)
        return dict(by_type)

    @cached_property
    def _nodes_by_file(self) -> dict[Path, set[NodeData]]:
        by_file: defaultdict[Path, set[NodeData]] = defaultdict(set)
        for node_data in self.all_nodes.values():
            by_file[node_data.file_path].add(node_data)
        return dict(by_file)

    # --- Query Methods ---

    def find_by_type(
        self, node_type: type[ast.AST]
    ) -> dict[type[ast.AST], set[NodeData]]:
        """Returns matching NodeData in a dict keyed by the requested node type.

        The values include nodes of `node_type` and its subclasses.
        """
        matches = {
            node_data
            for registered_type, node_data_set in self._nodes_by_type.items()
            if issubclass(registered_type, node_type)
            for node_data in node_data_set
        }
        return {node_type: matches}

    def is_inside(self, node: ast.AST, parent_type: type[ast.AST]) -> bool:
        info = self.all_nodes.get(node)
        if not info:
            return False
        return any(
            isinstance(ancestor, parent_type)
            for ancestor in info.get_ancestry(self.all_nodes)
        )


class IndexerVisitor(ast.NodeVisitor):
    """Visitor that indexes every node into all_nodes and maintains parent-child
    edges."""

    def __init__(self, file_path: Path, all_nodes: dict[ast.AST, NodeData]) -> None:
        self.all_nodes = all_nodes
        self.file_path = file_path
        self._parent_stack: list[ast.AST] = []

    def _find_str_attrib(self, node: ast.AST) -> str | None:
        result: str | None = None
        target = node.func if isinstance(node, ast.Call) else node
        for attr in ("id", "name", "attr", "arg", "label", "module", "__name__"):
            if isinstance(str_attr := getattr(target, attr, None), str):
                result = str_attr
        return result

    def generic_visit(self, node: ast.AST) -> None:
        parent = self._parent_stack[-1] if self._parent_stack else None

        node_data = NodeData(
            ast_node=node,
            name=self._find_str_attrib(node),
            file_path=self.file_path,
            rel_path=self.file_path.relative_to(MODULE_DIR),
            node_type=type(node),
            parent=parent,
            depth=len(self._parent_stack),
            lineno=getattr(node, "lineno", None),
            col_offset=getattr(node, "col_offset", None),
        )

        if parent in self.all_nodes:
            self.all_nodes[parent].children.append(node)

        self.all_nodes[node] = node_data

        self._parent_stack.append(node)
        super().generic_visit(node)
        self._parent_stack.pop()
