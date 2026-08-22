import ast

import pytest

from static_tests._cached_data import MODULE_DIR, ast_parse, get_file_paths

# For DebugLog it's normal not all methods are in use.
# CustomScrollBarRender is a monkey patch for the textual ScrollBarRender
EXCLUDE_CLASSES = {"DebugLog", "CustomScrollBarRender"}


class UnusedMethodDetector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_file: str = ""
        self.current_class: str | None = None
        self.function_depth: int = 0  # Tracks function nesting level

        # Map of (class_name, method_name) -> (file_path, lineno, is_property)
        self.defined_methods: dict[tuple[str, str], tuple[str, int, bool]] = {}

        # Map of (file_path, func_name) -> lineno
        self.defined_module_functions: dict[tuple[str, str], int] = {}

        # Map of method_name -> set of class_names where it is used
        # None represents global/module scope
        self.usages: dict[str, set[str | None]] = {}

        # Map of func_name -> set of file_paths where it is referenced
        self.file_usages: dict[str, set[str]] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old_class = self.current_class
        self.current_class = node.name

        # Skip definitions inside excluded classes completely
        if node.name in EXCLUDE_CLASSES:
            self.current_class = old_class
            return

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if item.name.startswith("__") and item.name.endswith("__"):
                    continue  # skip dunders

                if item.name.startswith(  # Skip textual related methods
                    (
                        "action_",
                        "check_action",
                        "compose",
                        "filter_paths",
                        "on_",
                        "render_line",
                        "render_lines",
                        "watch_",
                    )
                ):
                    continue

                # Check decorators to see if it's a property or uses an @on decorator
                is_property = False
                has_on_decorator = False

                for dec in item.decorator_list:
                    dec_name = None

                    # Plain decorators (e.g., @property, @on)
                    if isinstance(dec, ast.Name):
                        dec_name = dec.id
                    elif isinstance(dec, ast.Attribute):
                        dec_name = dec.attr

                    # Parameterized decorators (e.g., @on(OpButton.Pressed))
                    elif isinstance(dec, ast.Call):
                        if isinstance(dec.func, ast.Name):
                            dec_name = dec.func.id
                        elif isinstance(dec.func, ast.Attribute):
                            dec_name = dec.func.attr

                    # Skip the method if it has any variation of an @on decorator
                    if dec_name == "on":
                        has_on_decorator = True
                        break

                    # Matches @property, @cached_property, etc.
                    if dec_name and "property" in dec_name:
                        is_property = True

                if has_on_decorator:
                    continue

                self.defined_methods[(node.name, item.name)] = (
                    self.current_file,
                    item.lineno,
                    is_property,
                )

        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function_def(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function_def(node)

    def _handle_function_def(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        # Ignore inner nested functions defined inside other functions/methods
        if self.function_depth > 0:
            self.function_depth += 1
            self.generic_visit(node)
            self.function_depth -= 1
            return

        self.function_depth += 1

        # Track top-level module functions only (outside any class definition)
        if self.current_class is None and not (
            node.name.startswith("__") and node.name.endswith("__")
        ):
            self.defined_module_functions[(self.current_file, node.name)] = node.lineno

        self.generic_visit(node)
        self.function_depth -= 1

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Captures method calls and property access via dot notation
        if self.current_class not in EXCLUDE_CLASSES:
            self.usages.setdefault(node.attr, set()).add(self.current_class)
            self.file_usages.setdefault(node.attr, set()).add(self.current_file)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        # Captures references to methods/functions passed directly by name
        if isinstance(node.ctx, ast.Load) and self.current_class not in EXCLUDE_CLASSES:
            self.usages.setdefault(node.id, set()).add(self.current_class)
            self.file_usages.setdefault(node.id, set()).add(self.current_file)
        self.generic_visit(node)


def test_functions_and_methods_in_use() -> None:
    detector = UnusedMethodDetector()

    # Collect definitions and usages across the codebase
    for file_path in get_file_paths():
        detector.current_file = str(file_path.relative_to(MODULE_DIR))
        tree = ast_parse(file_path)
        detector.visit(tree)

    should_be_private: list[str] = []
    unused_properties: list[str] = []
    unused_functions: list[str] = []

    # 1. Check Class Methods
    for (class_name, method_name), (
        file,
        line,
        is_property,
    ) in detector.defined_methods.items():
        method_usages = detector.usages.get(method_name, set())

        if not method_usages:
            # Item is completely unused across the codebase
            info_str = f"{method_name} in {class_name} ({file}:{line})"
            if is_property:
                unused_properties.append(info_str)
            else:
                unused_functions.append(info_str)
        else:
            # Item is in use, check if it's ONLY used inside its own class
            if method_usages == {class_name} and not method_name.startswith("_"):
                should_be_private.append(
                    f"{method_name} in {class_name} ({file}:{line})"
                )

    # 2. Check Top-Level Module Functions
    for (file, func_name), line in detector.defined_module_functions.items():
        file_usages = detector.file_usages.get(func_name, set())

        if not file_usages:
            unused_functions.append(f"{func_name}() in module ({file}:{line})")
        else:
            # Used only inside the module file where it was defined
            if file_usages == {file} and not func_name.startswith("_"):
                should_be_private.append(f"{func_name}() in module ({file}:{line})")

    error_lines: list[str] = []

    if should_be_private:
        error_lines.append("\nFound methods/functions that should be private:")
        error_lines.extend(f"  - {item}" for item in should_be_private)

    if unused_properties:
        error_lines.append("\nFound unused properties:")
        error_lines.extend(f"  - {item}" for item in unused_properties)

    if unused_functions:
        error_lines.append("\nUnused functions/methods:")
        error_lines.extend(f"  - {item}" for item in unused_functions)

    if error_lines:
        pytest.fail("\n".join(error_lines))
