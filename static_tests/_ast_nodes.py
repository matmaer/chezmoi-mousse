"""This module is executed first by conftest.py"""

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

type NDSet = set[NodeData]
type AllNodesDict = dict[ast.AST, NodeData]
type NodeDataDict = dict[str, NDSet]

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

    _dc_field_name: str | None = None
    _decorator_name: str | None = None
    _enum_member_name: str | None = None
    _export_names: set[str] | None = None
    _function_name: str | None = None
    _target_name: str | None = None
    _is_enum_class: bool | None = None
    _module_qualname: str | None = None

    @property
    def dc_field_name(self) -> str:
        assert isinstance(self.ast_node, ast.AnnAssign)
        assert isinstance(self.ast_node.target, ast.Name)
        if isinstance(self._dc_field_name, str):
            return self._dc_field_name
        self._dc_field_name = self.ast_node.target.id
        return self._dc_field_name

    @property
    def decorator_name(self) -> str | None:
        assert isinstance(
            self.ast_node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        )
        if isinstance(self._decorator_name, str):
            return self._decorator_name

        dec_name = None
        for dec in self.ast_node.decorator_list:
            # Plain decorators
            if isinstance(dec, ast.Name):
                dec_name = dec.id
            elif isinstance(dec, ast.Attribute):
                dec_name = dec.attr
            elif isinstance(dec, ast.Call):
                # Parameterized decorators
                if isinstance(dec.func, ast.Name):
                    dec_name = dec.func.id
                elif isinstance(dec.func, ast.Attribute):
                    dec_name = dec.func.attr
        self._decorator_name = dec_name
        return dec_name

    @property
    def enum_member_name(self) -> str:
        assert isinstance(self.ast_node, ast.Assign)
        target = self.ast_node.targets[0]
        assert isinstance(target, ast.Name)
        if isinstance(self._enum_member_name, str):
            return self._enum_member_name

        self._enum_member_name = target.id
        return self._enum_member_name

    @property
    def export_names(self) -> set[str] | None:
        assert isinstance(self.ast_node, ast.Assign)
        if self._export_names is not None:
            return self._export_names

        val = self.ast_node.value
        names: set[str] = set()

        if isinstance(val, ast.Constant) and isinstance(val.value, str):
            names.add(val.value)
        elif isinstance(val, (ast.List, ast.Tuple, ast.Set)):
            for elt in val.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    names.add(elt.value)

        self._export_names = names
        return names

    @property
    def function_name(self) -> str:
        assert isinstance(self.ast_node, (ast.FunctionDef, ast.AsyncFunctionDef))
        if isinstance(self._function_name, str):
            return self._function_name

        self._function_name = self.ast_node.name
        return self._function_name

    @property
    def is_enum_class(self) -> bool:
        assert isinstance(self.ast_node, ast.ClassDef)
        if self._is_enum_class is not None:
            return self._is_enum_class

        is_enum = False
        for base in self.ast_node.bases:
            if (isinstance(base, ast.Name) and base.id in ("Enum", "StrEnum")) or (
                isinstance(base, ast.Attribute) and base.attr in ("Enum", "StrEnum")
            ):
                is_enum = True
                break

        self._is_enum_class = is_enum
        return is_enum

    @property
    def is_load_context(self) -> bool:
        """Returns True if the AST node is accessed in an ast.Load context."""
        ctx = getattr(self.ast_node, "ctx", None)
        return isinstance(ctx, ast.Load)

    @property
    def is_self_attribute(self) -> bool:
        """Returns True if this node represents an attribute access on `self`
        (e.g. self.foo)."""
        if isinstance(self.ast_node, ast.Attribute):
            value = self.ast_node.value
            return isinstance(value, ast.Name) and value.id == "self"
        return False

    @property
    def target_name(self) -> str | None:
        """Extracts the target identifier string for Assign, AnnAssign, Name,
        or Attribute nodes."""
        if isinstance(self._target_name, str):
            return self._target_name

        name: str | None = None
        node = self.ast_node

        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                name = node.target.id
            elif isinstance(node.target, ast.Attribute):
                name = node.target.attr
        elif isinstance(node, ast.Assign):
            if len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    name = target.id
                elif isinstance(target, ast.Attribute):
                    name = target.attr
        elif isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.Attribute):
            name = node.attr

        self._target_name = name
        return name

    @property
    def is_special_dunder(self) -> bool:
        name = self.function_name
        return name.startswith("__") and name.endswith("__")

    @property
    def is_top_level(self) -> bool:
        """Returns True if the node is defined at the module root level."""
        return self.parent is not None and self.parent.node_type == ast.Module.__name__

    @property
    def module_qualname(self) -> str:
        if isinstance(self._module_qualname, str):
            return self._module_qualname

        rel = self.rel_path.removesuffix(".py").replace("\\", "/")
        if rel == "__init__":
            qualname = "chezmoi_mousse"
        elif rel.endswith("/__init__"):
            qualname = (
                f"chezmoi_mousse.{rel.removesuffix('/__init__').replace('/', '.')}"
            )
        else:
            qualname = f"chezmoi_mousse.{rel.replace('/', '.')}"

        self._module_qualname = qualname
        return qualname


@dataclass
class NodeDb:
    """AST database populated upfront, using lazy cached properties for queries."""

    all_nodes: AllNodesDict = field(default_factory=dict[ast.AST, NodeData])
    by_name: NodeDataDict = field(default_factory=lambda: defaultdict(set))
    by_path: NodeDataDict = field(default_factory=lambda: defaultdict(set))
    by_type: NodeDataDict = field(default_factory=lambda: defaultdict(set))
    nodes_without_name: NDSet = field(default_factory=set[NodeData])

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

    @property
    def textual_imports(self) -> set[str]:
        """Dynamically extracts all imported symbols from textual or its subpackages."""
        imported_names: set[str] = set()
        import_from_nodes = self.by_type.get(ast.ImportFrom.__name__, set())

        for imp_node in import_from_nodes:
            assert isinstance(imp_node.ast_node, ast.ImportFrom)
            mod = imp_node.ast_node.module
            if mod and (mod == "textual" or mod.startswith("textual.")):
                for alias in imp_node.ast_node.names:
                    imported_names.add(alias.name)

        return imported_names

    @property
    def textual_subclass_names(self) -> set[str]:
        """Returns the names of all local classes that inherit from an imported
        Textual class."""
        textual_classes = self.textual_imports
        if not textual_classes:
            return set()

        subclass_names: set[str] = set()
        class_nodes = self.by_type.get(ast.ClassDef.__name__, set())

        for class_node in class_nodes:
            assert isinstance(class_node.ast_node, ast.ClassDef)
            class_name = class_node.ast_node.name

            for base in class_node.ast_node.bases:
                # Match standard bases: class MyWidget(Widget):
                if isinstance(base, ast.Name) and base.id in textual_classes:
                    subclass_names.add(class_name)
                    break
                # Match generic bases: class ManagedTree(Tree[Path]):
                elif isinstance(base, ast.Subscript) and isinstance(
                    base.value, ast.Name
                ):
                    if base.value.id in textual_classes:
                        subclass_names.add(class_name)
                        break
                # Match attribute bases: class MyWidget(widgets.Widget):
                elif isinstance(base, ast.Attribute) and base.attr in textual_classes:
                    subclass_names.add(class_name)
                    break

        return subclass_names


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
