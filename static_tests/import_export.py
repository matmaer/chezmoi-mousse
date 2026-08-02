import ast
from pathlib import Path

import pytest

from static_tests._cached_data import MODULE_DIR, ast_parse, get_file_paths


class AllVariableDetector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_module: str = ""
        self.known_modules: set[str] = set()
        self.root_package: str = "chezmoi_mousse"

        # Mapping of module_name -> set of exported strings in __all__
        self.defined_all: dict[str, set[str]] = {}
        # Mapping of module_name -> bool indicating if __all__ exists
        self.has_all: dict[str, bool] = {}

        # Tracking explicit imports:
        # (imported_from_module, item_name) -> set of modules that imported it
        self.imports_tracker: dict[tuple[str, str], set[str]] = {}

        # Set of (module_name, item_name) imported *by* a module
        self.items_imported_by_module: set[tuple[str, str]] = set()

    def _is_known_module_path(self, module_name: str) -> bool:
        """Return True for exact known module names or package prefixes."""
        if module_name in self.known_modules:
            return True

        package_prefix = f"{module_name}."
        return any(known.startswith(package_prefix) for known in self.known_modules)

    def _resolve_non_relative_import(self, module_name: str | None) -> str | None:
        """Resolve non-relative imports into a module path tracked by this test."""
        if not module_name:
            return None

        root_prefix = f"{self.root_package}."
        if module_name.startswith(root_prefix):
            return module_name[len(root_prefix) :]

        current_parts = self.current_module.split(".")
        package_parts = current_parts[:-1]

        # Accept implicit package-style imports by resolving nearest package first.
        # Example: from common.x import Y inside chezmoi_mousse.gui.*
        # becomes chezmoi_mousse.gui.common.x when that module exists.
        incoming_parts = module_name.split(".")
        for end in range(len(package_parts), 0, -1):
            candidate_parts = package_parts[:end] + incoming_parts
            candidate = ".".join(candidate_parts)
            if self._is_known_module_path(candidate):
                return candidate

        # Fallback to root package scope for root-level modules.
        if self._is_known_module_path(module_name):
            return module_name

        return None

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
            absolute_module = self._resolve_non_relative_import(node.module)
            if absolute_module is None:
                return

        for alias in node.names:
            if alias.name == "*":
                continue

            key = (absolute_module, alias.name)
            self.imports_tracker.setdefault(key, set()).add(self.current_module)

            # Record that this specific module imported this specific item name
            # (used to check if it's re-exported in __all__)
            self.items_imported_by_module.add((self.current_module, alias.name))


def test_import_export() -> None:
    detector = AllVariableDetector()

    # Map file paths to package-relative module dotted names
    file_to_module: dict[Path, str] = {}
    for file_path in get_file_paths():
        rel_parts = file_path.relative_to(MODULE_DIR).with_suffix("").parts
        module_name = ".".join(rel_parts)

        if module_name:
            file_to_module[file_path] = module_name

    detector.known_modules = set(file_to_module.values())

    # Scan all files to gather structural definitions and cross-references
    for file_path, module_name in file_to_module.items():
        detector.current_module = module_name
        tree = ast_parse(file_path)
        detector.visit(tree)

    # Output Buckets
    never_imported_anywhere: list[str] = []
    imported_but_missing_from_all: list[str] = []
    missing_all_variable_entirely: list[str] = []
    imported_items_in_all: list[str] = []

    # Map target modules being queried
    modules_imported_from = {mod for mod, _ in detector.imports_tracker}

    # Module has no __all__ variable but other modules import from it
    for mod, has_all in detector.has_all.items():
        if (
            not has_all
            and mod in modules_imported_from
            and any(
                imp_mod == mod and (consumers - {mod})
                for (imp_mod, _), consumers in detector.imports_tracker.items()
            )
        ):
            missing_all_variable_entirely.append(
                f"- {mod} has no __all__ but other modules import from it."
            )

    # Core evaluations per tracked import statement
    for (source_mod, item), consumers in detector.imports_tracker.items():
        external_consumers = consumers - {source_mod}
        if not external_consumers:
            continue

        # A module imports from another module, but the entry is missing from __all__
        if detector.has_all.get(source_mod):
            exports = detector.defined_all.get(source_mod, set())
            if item not in exports:
                imported_but_missing_from_all.append(
                    f"- {item} is imported from '{source_mod}', but not exported."
                )

    # Entry in __all__ evaluations
    for mod, exports in detector.defined_all.items():
        for item in exports:
            # Item in __all__ was imported from elsewhere
            if (mod, item) in detector.items_imported_by_module:
                imported_items_in_all.append(
                    f"- {item} in {mod} is imported from elsewhere but exported."
                )

            direct_consumers = detector.imports_tracker.get((mod, item), set()) - {mod}

            if not direct_consumers:
                never_imported_anywhere.append(f"- {item} in {mod}")

    error_lines: list[str] = []

    if never_imported_anywhere:
        error_lines.append(
            "\nFound entries in __all__ that are never imported anywhere:"
        )
        error_lines.extend(never_imported_anywhere)

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
