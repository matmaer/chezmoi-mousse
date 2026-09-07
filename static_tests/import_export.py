import ast
from typing import TYPE_CHECKING

import pytest
from static_tests._ast_nodes import NodeData, NodeDb

if TYPE_CHECKING:
    from static_tests._ast_nodes import NDSet

type ExportDict = dict[str, set[str]]
type ExportNodeDict = dict[str, NodeData]


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


def get_unused(node_db: NodeDb) -> list[str]:
    defined_exports, export_nodes = _get_defined_exports(node_db)

    # Track import relationships across the codebase:
    # (target_module, imported_symbol) -> set of consuming modules
    import_tracker: dict[tuple[str, str], set[str]] = {}
    imported_symbols_by_module: set[tuple[str, str]] = set()

    import_from_nodes: NDSet = node_db.by_type.get(ast.ImportFrom.__name__, set())
    for imp_node in import_from_nodes:
        assert isinstance(imp_node.ast_node, ast.ImportFrom)
        ast_imp = imp_node.ast_node

        if not ast_imp.module or not ast_imp.module.startswith("chezmoi_mousse"):
            continue

        target_module = ast_imp.module
        consumer_module = imp_node.module_qualname

        for alias in ast_imp.names:
            if alias.name != "*":
                key = (target_module, alias.name)
                import_tracker.setdefault(key, set()).add(consumer_module)
                imported_symbols_by_module.add((consumer_module, alias.name))

    # Output Buckets
    never_imported_anywhere: list[str] = []
    imported_but_missing_from_all: list[str] = []
    missing_all_variable_entirely: list[str] = []
    reexported_indirect_imports: list[str] = []

    # 1. Flag modules imported from that lack an `__all__` declaration
    modules_imported_from = {src for src, _ in import_tracker}
    for src_module in modules_imported_from:
        if src_module not in defined_exports:
            has_external_consumer = any(
                c != src_module
                for (s, _), cons in import_tracker.items()
                if s == src_module
                for c in cons
            )
            if has_external_consumer:
                missing_all_variable_entirely.append(
                    f"{src_module} has no '__all__' variable, but other modules "
                    f"import from it"
                )

    # 2. Flag items imported from a module that are missing from its `__all__`
    for (src_module, symbol), consumers in import_tracker.items():
        if (
            consumers - {src_module}
            and src_module in defined_exports
            and symbol not in defined_exports[src_module]
        ):
            imported_but_missing_from_all.append(
                f"'{symbol}' imported from '{src_module}', not exported in __all__"
            )

    # 3. Flag unused entries in `__all__` or indirect re-exports
    for src_module, exports in defined_exports.items():
        node = export_nodes[src_module]
        is_init = node.rel_path.endswith("__init__.py")

        for symbol in exports:
            if not is_init and (src_module, symbol) in imported_symbols_by_module:
                reexported_indirect_imports.append(
                    f"'{symbol}' in {src_module} ({node.rel_path}:{node.lineno}) "
                    f"is imported from elsewhere but re-exported in __all__"
                )

            external_consumers = import_tracker.get((src_module, symbol), set()) - {
                src_module
            }
            if not external_consumers:
                never_imported_anywhere.append(
                    f"'{symbol}' in {src_module} ({node.rel_path}:{node.lineno})"
                )

    # Build report sections
    sections = [
        (
            "\nFound entries in __all__ that are never imported anywhere:",
            never_imported_anywhere,
        ),
        (
            "\nItems imported from a module, but not exported in __all__:",
            imported_but_missing_from_all,
        ),
        (
            "\nModules with no '__all__' variable, but other modules import from them:",
            missing_all_variable_entirely,
        ),
        ("\nIndirect re-exports in __all__:", reexported_indirect_imports),
    ]

    reports: list[str] = []
    for header, items in sections:
        if items:
            reports.append(header)
            reports.extend(f"- {r}" for r in sorted(items))

    return reports


def test_import_export(node_db: NodeDb) -> None:
    reports = get_unused(node_db)

    if reports:
        msg = f"{len(reports)} import/export issue(s) found:\n" + "\n".join(reports)
        pytest.fail(msg)
