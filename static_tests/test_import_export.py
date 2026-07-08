import ast
from pathlib import Path

import pytest


class AllVariableDetector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_module: str = ""

        # Mapping of module_name -> set of exported strings in __all__
        self.defined_all: dict[str, set[str]] = {}
        # Mapping of module_name -> bool indicating if __all__ exists
        self.has_all: dict[str, bool] = {}

        # Tracking explicit imports:
        # (imported_from_module, item_name) -> set of modules that imported it
        self.imports_tracker: dict[tuple[str, str], set[str]] = {}

        # New tracking: set of (module_name, item_name) imported *by* a module
        self.items_imported_by_module: set[tuple[str, str]] = set()

    def visit_Module(self, node: ast.Module) -> None:
        self.has_all[self.current_module] = False

        # Look for __all__ assignment at the top/module level
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        self._process_all_value(self.current_module, stmt.value)
            elif isinstance(stmt, ast.AnnAssign) and (
                isinstance(stmt.target, ast.Name)
                and stmt.target.id == "__all__"
                and stmt.value
            ):
                self._process_all_value(self.current_module, stmt.value)

        self.generic_visit(node)

    def _process_all_value(self, module_name: str, value_node: ast.AST) -> None:
        self.has_all[module_name] = True
        elements: set[str] = set()

        if isinstance(value_node, (ast.Tuple, ast.List)):
            for elt in value_node.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    elements.add(elt.value)
        elif isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
            elements.add(value_node.value)

        self.defined_all[module_name] = elements

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        # Resolve the source module based on absolute vs relative context rules
        if node.level > 0:
            # Handle relative imports (e.g., level=1 -> '.', level=2 -> '..')
            parts = self.current_module.split(".")
            slice_end = -node.level
            base = parts[:slice_end] if slice_end < 0 else parts

            suffix = [node.module] if node.module else []
            absolute_module = ".".join(base + suffix)
        else:
            # Handle the explicit exception: 'from chezmoi_mousse import SomeClass'
            if node.module == "chezmoi_mousse" or (
                node.module and node.module.startswith("chezmoi_mousse.")
            ):
                absolute_module = node.module
            else:
                return

        for alias in node.names:
            if alias.name == "*":
                continue

            key = (absolute_module, alias.name)
            self.imports_tracker.setdefault(key, set()).add(self.current_module)

            # Record that this specific module imported this specific item name
            # (used to check if it's re-exported in __all__)
            self.items_imported_by_module.add((self.current_module, alias.name))

        self.generic_visit(node)


def test_all_variable_usage() -> None:
    detector = AllVariableDetector()
    src_directory = Path(__file__).parent.parent / "src"
    python_files = list(src_directory.rglob("*.py"))

    # Map file paths to package-relative module dotted names
    file_to_module: dict[Path, str] = {}
    for file_path in python_files:
        rel_parts = file_path.relative_to(src_directory).with_suffix("").parts
        if rel_parts[-1] == "__init__":
            module_name = ".".join(rel_parts[:-1])
        else:
            module_name = ".".join(rel_parts)

        if module_name:
            file_to_module[file_path] = module_name

    # Step 1: Scan all files to gather structural definitions and cross-references
    for file_path, module_name in file_to_module.items():
        detector.current_module = module_name
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        detector.visit(tree)

    # Output Buckets
    never_imported_anywhere: list[str] = []
    only_imported_via_init_but_abandoned: list[str] = []
    imported_but_missing_from_all: list[str] = []
    missing_all_variable_entirely: list[str] = []
    imported_items_in_all: list[str] = []  # <--- New bucket

    # Map target modules being queried
    modules_imported_from = {mod for mod, _ in detector.imports_tracker}

    # Module has no __all__ variable but other modules import from it
    for mod, has_all in detector.has_all.items():
        if not has_all and mod in modules_imported_from:
            has_external_consumers = False
            for (imp_mod, _), consumers in detector.imports_tracker.items():
                if imp_mod == mod and (consumers - {mod}):
                    has_external_consumers = True
                    break
            if has_external_consumers:
                missing_all_variable_entirely.append(
                    f"- {mod} has no __all__ but other modules import from it."
                )

    # Core evaluations per tracked import statement
    for (source_mod, item), consumers in detector.imports_tracker.items():
        external_consumers = consumers - {source_mod}
        if not external_consumers:
            continue

        # A module imports from another module, but the entry is missing from __all__
        if source_mod in detector.has_all and detector.has_all[source_mod]:
            exports = detector.defined_all.get(source_mod, set())
            if item not in exports:
                imported_but_missing_from_all.append(
                    f"- {item} is imported from '{source_mod}', but not exported."
                )

        # Entry imported in '__init__.py', but no other module imports it from there.
        if source_mod == "chezmoi_mousse":
            root_consumers = external_consumers
            if not root_consumers:
                only_imported_via_init_but_abandoned.append(f"- {item} not exported")

    # Entry in __all__ evaluations
    for mod, exports in detector.defined_all.items():
        # Determine if this module qualifies as an __init__.py file context
        is_init_file = mod == "chezmoi_mousse" or mod.endswith(".__init__")

        for item in exports:
            # Item in __all__ was imported from elsewhere
            if not is_init_file and (mod, item) in detector.items_imported_by_module:
                imported_items_in_all.append(
                    f"- {item} in {mod} is imported from elsewhere but exported."
                )

            direct_consumers = detector.imports_tracker.get((mod, item), set()) - {mod}

            # If it isn't directly consumed, see if it was grabbed via the root package
            is_used_downstream = False
            if direct_consumers:
                is_used_downstream = True
            else:
                for p_mod in ["chezmoi_mousse", f"{mod}.__init__"]:
                    if detector.imports_tracker.get((p_mod, item), set()) - {p_mod}:
                        is_used_downstream = True
                        break

            if not is_used_downstream:
                never_imported_anywhere.append(f"- {item} in {mod}")

    error_lines: list[str] = []

    if never_imported_anywhere:
        error_lines.append(
            "\nFound entries in __all__ that are never imported anywhere:"
        )
        error_lines.extend(never_imported_anywhere)

    if only_imported_via_init_but_abandoned:
        error_lines.append(
            "\nItems imported in '__init__.py', but never imported from chezmoi_mousse:"
        )
        error_lines.extend(only_imported_via_init_but_abandoned)

    if imported_but_missing_from_all:
        error_lines.append("\nItems imported from a module, but not exported:")
        error_lines.extend(imported_but_missing_from_all)

    if missing_all_variable_entirely:
        error_lines.append(
            "\nModules with no '__all__' variable but other modules import from them:"
        )
        error_lines.extend(missing_all_variable_entirely)

    if imported_items_in_all:
        error_lines.append("\nIndirect imports:")
        error_lines.extend(imported_items_in_all)

    if error_lines:
        pytest.fail("\n".join(error_lines))
