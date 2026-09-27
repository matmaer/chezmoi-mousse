import ast
from typing import TYPE_CHECKING

from static_tests._ast_nodes import NodeData, NodeDb
from static_tests.conftest import CheckRunner, IssueList

if TYPE_CHECKING:
    from static_tests._ast_nodes import NDSet

type ExportDict = dict[str, set[str]]  # module name mapped to exported strings
type ExportNodeDict = dict[str, NodeData]  # module name mapped to assign node


def _get_defined_exports(node_db: NodeDb) -> tuple[ExportDict, ExportNodeDict]:
    """Finds all `__all__` assignments across modules and extracts exported symbols."""
    defined_exports: ExportDict = {}
    export_nodes: ExportNodeDict = {}

    assign_nodes = node_db.by_type.get(ast.Assign.__name__, set())
    for assign_node in assign_nodes:
        assert isinstance(assign_node.ast_node, ast.Assign)
        targets = assign_node.ast_node.targets

        if (
            len(targets) == 1
            and isinstance(targets[0], ast.Name)
            and targets[0].id == "__all__"
        ):
            names = assign_node.export_names
            if names is not None:
                mod_name = assign_node.module_qualname
                defined_exports[mod_name] = names
                export_nodes[mod_name] = assign_node

    return defined_exports, export_nodes


def get_issues(node_db: NodeDb) -> IssueList:
    issue_list: IssueList = []
    defined_exports, export_nodes = _get_defined_exports(node_db)

    # All known module qualnames, used to detect "from pkg import submodule"
    # imports, which are plain submodule imports and not `__all__` symbols.
    known_modules = {
        next(iter(nodes)).module_qualname for nodes in node_db.by_path.values()
    }

    # Track import relationships across the codebase:
    import_tracker: dict[tuple[str, str], set[str]] = {}
    # (target_module, imported_symbol) -> set of consuming modules
    imported_symbols_by_module: set[tuple[str, str]] = set()

    import_from_nodes: NDSet = node_db.by_type.get(ast.ImportFrom.__name__, set())
    for imp_node in import_from_nodes:
        assert isinstance(imp_node.ast_node, ast.ImportFrom)

        if not imp_node.ast_node.module or not imp_node.ast_node.module.startswith(
            "chezmoi_mousse"
        ):
            continue

        for alias in imp_node.ast_node.names:
            if f"{imp_node.ast_node.module}.{alias.name}" in known_modules:
                continue
            key = (imp_node.ast_node.module, alias.name)
            import_tracker.setdefault(key, set()).add(imp_node.module_qualname)
            imported_symbols_by_module.add((imp_node.module_qualname, alias.name))

    # 1. Flag modules imported from that lack an `__all__` declaration
    modules_imported_from = {src for src, _ in import_tracker}
    for src_module in modules_imported_from:
        if src_module not in defined_exports:
            has_external_consumer = any(
                consumer != src_module
                for (s, _), consumers in import_tracker.items()
                if s == src_module
                for consumer in consumers
            )
            if has_external_consumer:
                issue_list.append(
                    (
                        f"{src_module}",
                        "not available",
                        "not available",
                        (
                            "Module(s) without '__all__' var, but other modules import "
                            "from it"
                        ),
                    )
                )

    # 2. Flag items imported from a module that are missing from its `__all__`
    for (src_module, symbol), consumers in import_tracker.items():
        if (
            consumers - {src_module}
            and src_module in defined_exports
            and symbol not in defined_exports[src_module]
        ):
            issue_list.append(
                (
                    f"{src_module}",
                    f"{symbol}",
                    "not available",
                    ("Symbol(s) imported but not exported in __all__"),
                )
            )

    # 3. Flag unused entries in `__all__` or indirect re-exports
    for src_module, exports in defined_exports.items():
        node = export_nodes[src_module]
        is_init = node.rel_path.endswith("__init__.py")

        for symbol in exports:
            if not is_init and (src_module, symbol) in imported_symbols_by_module:
                issue_list.append(
                    (
                        f"{src_module}",
                        f"{symbol}",
                        f"{node.rel_path}:{node.lineno}",
                        ("Symbol(s) imported and re-exported in __all__"),
                    )
                )
            external_consumers = import_tracker.get((src_module, symbol), set()) - {
                src_module
            }
            if not external_consumers:
                issue_list.append(
                    (
                        f"{src_module}",
                        f"{symbol}",
                        f"{node.rel_path}:{node.lineno}",
                        ("Symbol(s) exported in __all__ but never imported"),
                    )
                )

    return issue_list


def test_import_export(run_check: CheckRunner) -> None:
    run_check(get_issues)
