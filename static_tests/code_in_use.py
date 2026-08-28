import ast
from pathlib import Path

import pytest

# For DebugLog it's normal not all methods are in use.
# CustomScrollBarRender is a monkey patch for the textual ScrollBarRender
EXCLUDE_CLASSES = {"DebugLog", "CustomScrollBarRender"}
# Skip textual related methods
EXCLUDE_METHODS = (
    "action_",
    "check_action",
    "compose",
    "filter_paths",
    "on_",
    "render_line",
    "render_lines",
    "watch_",
)


private_classes: list[str] = []
private_functions: list[str] = []
unused_classes: list[str] = []
unused_functions: list[str] = []


class UnusedMethodDetector:
    def __init__(self) -> None:
        self.current_file: str = ""
        self.current_class: str | None = None
        self.function_depth: int = 0  # Tracks function nesting level

        # Map of (class_name, method_name) -> (file_path, lineno, is_property)
        self.defined_methods: dict[tuple[str, str], tuple[str, int]] = {}

        # Map of (file_path, func_name) -> lineno
        self.defined_module_functions: dict[tuple[str, str], int] = {}

        # Map of (file_path, class_name) -> lineno
        self.defined_module_classes: dict[tuple[str, str], int] = {}

        # Map of method_name -> set of class_names where it is used
        # None represents global/module scope
        self.usages: dict[str, set[str | None]] = {}

        # Map of identifier_name -> set of file paths where it is referenced
        self.file_usages: dict[str, set[str]] = {}

    def visit_class_def(self, node: ast.ClassDef) -> None:
        old_class = self.current_class

        # Track top-level classes defined at module scope
        if self.current_class is None:
            self.defined_module_classes[(self.current_file, node.name)] = node.lineno

        self.current_class = node.name

        # Skip definitions inside excluded classes completely
        if node.name in EXCLUDE_CLASSES:
            self.current_class = old_class
            return

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if item.name.startswith("__") and item.name.endswith("__"):
                    continue  # skip dunders

                if item.name.startswith(EXCLUDE_METHODS):
                    continue

                # Check decorators to see if it's a property or uses an @on decorator
                has_on_decorator = False

                for dec in item.decorator_list:
                    dec_name = None
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
                    if dec_name == "on":
                        has_on_decorator = True

                if has_on_decorator:
                    continue

                self.defined_methods[(node.name, item.name)] = (
                    self.current_file,
                    item.lineno,
                )

        self.current_class = old_class

    def visit_function_def(self, node: ast.FunctionDef) -> None:
        self._handle_function_def(node)

    def visit_async_function_def(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function_def(node)

    def _handle_function_def(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        self.function_depth += 1

        # Track top-level module functions only (outside any class definition)
        if self.current_class is None and not (
            node.name.startswith("__") and node.name.endswith("__")
        ):
            self.defined_module_functions[(self.current_file, node.name)] = node.lineno

        self.function_depth -= 1

    def visit_attribute(self, node: ast.Attribute) -> None:
        # Captures method calls and property access via dot notation
        if self.current_class not in EXCLUDE_CLASSES:
            self.usages.setdefault(node.attr, set()).add(self.current_class)
            self.file_usages.setdefault(node.attr, set()).add(self.current_file)

    def visit_name(self, node: ast.Name) -> None:
        # Captures references to methods/functions/classes passed or referenced by name
        if isinstance(node.ctx, ast.Load) and self.current_class not in EXCLUDE_CLASSES:
            self.usages.setdefault(node.id, set()).add(self.current_class)
            self.file_usages.setdefault(node.id, set()).add(self.current_file)


def _gather_code_in_use_data(module_trees: dict[Path, ast.AST] | None = None) -> None:
    detector = UnusedMethodDetector()

    # Collect definitions and usages across the codebase
    if module_trees is None:
        return
    for _ in module_trees:
        break

    # 1. Check Class Methods
    for (class_name, method_name), (
        file,
        line,
    ) in detector.defined_methods.items():
        method_usages = detector.usages.get(method_name, set())

        if not method_usages:
            # Item is completely unused across the codebase
            info_str = f"{method_name}()  ({file}:{line})"
            unused_functions.append(info_str)
        # Item is in use, check if it's ONLY used inside its own class
        elif method_usages == {class_name} and not method_name.startswith("_"):
            private_functions.append(f"{method_name}()  ({file}:{line})")

    # 2. Check Top-Level Module Functions
    for (file, func_name), line in detector.defined_module_functions.items():
        file_usages = detector.file_usages.get(func_name, set())

        if not file_usages:
            unused_functions.append(f"{func_name}()  ({file}:{line})")
        # Used only inside the module file where it was defined
        elif file_usages == {file} and not func_name.startswith("_"):
            private_functions.append(f"{func_name}()  ({file}:{line})")

    # 3. Check Top-Level Module Classes
    for (file, class_name), line in detector.defined_module_classes.items():
        if class_name in EXCLUDE_CLASSES:
            continue

        file_usages = detector.file_usages.get(class_name, set())

        if not file_usages:
            unused_classes.append(f"{class_name}  ({file}:{line})")
        elif file_usages == {file} and not class_name.startswith("_"):
            private_classes.append(f"{class_name}  ({file}:{line})")


_ = _gather_code_in_use_data()


def test_classes_in_use() -> None:
    if unused_classes:
        lines = sorted(f"{item}" for item in unused_classes)
        pytest.fail("\n".join(lines))


def test_functions_in_use() -> None:
    if unused_functions:
        lines = sorted(f"{item}" for item in unused_functions)
        pytest.fail("\n".join(lines))


def test_private_classes() -> None:
    if private_classes:
        lines = sorted(f"{item}" for item in private_classes)
        pytest.fail("\n".join(lines))


def test_private_functions() -> None:
    if private_functions:
        lines = sorted(f"{item}" for item in private_functions)
        pytest.fail("\n".join(lines))
