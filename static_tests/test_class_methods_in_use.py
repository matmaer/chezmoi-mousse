import ast
from pathlib import Path

import pytest

# For DebugLog it's normal not all methods are in use.
# CustomScrollBarRender is a monkey patch for the textual ScrollBarRender
EXCLUDE_CLASSES = {"DebugLog", "CustomScrollBarRender"}


class UnusedMethodDetector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_file: str = ""
        self.current_class: str | None = None

        # Map of (class_name, method_name) -> (file_path, lineno, is_property)
        self.defined_methods: dict[tuple[str, str], tuple[str, int, bool]] = {}

        # Map of method_name -> set of class_names where it is used
        # None represents global scope
        self.usages: dict[str, set[str | None]] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Skip definitions and tracking inside excluded classes completely
        if node.name in EXCLUDE_CLASSES:
            # We still visit children normally so that any references/usages
            # inside these skipped classes are still caught code-wide
            self.generic_visit(node)
            return

        # Save old class context to support nested classes perfectly
        old_class = self.current_class
        self.current_class = node.name

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

                    # # Parameterized decorators (e.g., @on(OpButton.Pressed))
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

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Captures method calls and property access via dot notation
        # (e.g., self.foo, obj.bar)
        self.usages.setdefault(node.attr, set()).add(self.current_class)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        # Captures references to methods passed directly by name inside the class body
        if isinstance(node.ctx, ast.Load):
            self.usages.setdefault(node.id, set()).add(self.current_class)
        self.generic_visit(node)


def test_class_methods() -> None:
    detector = UnusedMethodDetector()
    src_dir = Path(__file__).parent.parent / "src"
    py_files = list(src_dir.rglob("*.py"))

    # Collect definitions and usages across the codebase
    for file_path in py_files:
        detector.current_file = str(file_path.relative_to(src_dir.parent))
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        detector.visit(tree)

    should_be_private: list[str] = []
    unused_properties: list[str] = []
    unused_functions: list[str] = []

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

    # Build the single combined reporting block
    error_lines: list[str] = []

    if should_be_private:
        error_lines.append("\nFound methods that should be private:")
        error_lines.extend(f"  - {item}" for item in should_be_private)

    if unused_properties:
        error_lines.append("\nFound unused properties:")
        error_lines.extend(f"  - {item}" for item in unused_properties)

    if unused_functions:
        error_lines.append("\nUnused functions:")
        error_lines.extend(f"  - {item}" for item in unused_functions)

    if error_lines:
        pytest.fail("\n".join(error_lines))
