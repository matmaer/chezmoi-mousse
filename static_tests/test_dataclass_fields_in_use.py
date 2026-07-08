import ast
from pathlib import Path

import pytest


def is_dataclass(class_def: ast.ClassDef) -> bool:
    return any(
        (isinstance(d, ast.Name) and d.id == "dataclass")
        or (isinstance(d, ast.Attribute) and d.attr == "dataclass")
        or (
            isinstance(d, ast.Call)
            and isinstance(d.func, ast.Name)
            and d.func.id == "dataclass"
        )
        for d in class_def.decorator_list
    )


class UnusedFieldDetector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_file: str = ""
        self.current_file_path: Path | None = None
        # Map "ClassName.field_name" to (file_path, lineno)
        self.defined_fields: dict[str, tuple[str, int]] = {}
        self.used_field_names: set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if is_dataclass(node):
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(
                    item.target, ast.Name
                ):
                    field_key = f"{node.name}.{item.target.id}"
                    self.defined_fields[field_key] = (self.current_file, item.lineno)

        # Continue walking the tree to find usages inside this class's methods
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Catches usages like: config.some_value
        self.used_field_names.add(node.attr)
        self.generic_visit(node)

    def visit_keyword(self, node: ast.keyword) -> None:
        # Catches keyword arguments like: LocalConfig(some_value='foo')
        if node.arg:
            self.used_field_names.add(node.arg)
        self.generic_visit(node)


def test_dataclass_fields() -> None:
    # By passing every file tree to the same visitor instance, the visitor can
    # accumulate a global map of your entire project, even though each generic_visit
    # call only ever knows about the single file it is currently walking.

    detector = UnusedFieldDetector()
    src_directory = Path(__file__).parent.parent / "src"
    python_files = list(src_directory.rglob("*.py"))

    # Collect all data across modules
    for file_path in python_files:
        detector.current_file = str(file_path.relative_to(src_directory.parent))
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        detector.visit(tree)

    # Identify unused fields
    unused: list[str] = []
    for field_key, (file, line) in detector.defined_fields.items():
        class_name, field_name = field_key.split(".")

        if field_name not in detector.used_field_names:
            unused.append(f"{field_name} in {class_name} ({file}:{line})")

    if unused:
        error_message = "\nFound unused dataclass fields:\n" + "\n".join(unused)
        pytest.fail(error_message)
