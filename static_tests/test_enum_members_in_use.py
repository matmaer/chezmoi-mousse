import ast
from pathlib import Path

import pytest

EXCLUDE_ENUMS = {"UnwantedDirs", "UnwantedFileExtensions", "KeyFileNames"}


def is_enum_class(class_def: ast.ClassDef) -> bool:
    # Todo: change the module where these are being used not to use enums.
    if class_def.name in EXCLUDE_ENUMS:
        return False
    for base in class_def.bases:
        if isinstance(base, ast.Name) and base.id in ("Enum", "StrEnum"):
            return True
    return False


class UnusedEnumMemberDetector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_file: str = ""
        # Map of "EnumName.MEMBER_NAME" -> (file_path, lineno)
        self.defined_members: dict[str, tuple[str, int]] = {}
        self.used_member_names: set[str] = set()
        # Track the active Enum class context for internal references
        self.current_enum_class: str | None = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if is_enum_class(node):
            # Gather all defined members
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            member_key = f"{node.name}.{target.id}"
                            self.defined_members[member_key] = (
                                self.current_file,
                                item.lineno,
                            )

            # Set the context before walking the internal body nodes
            old_enum_context = self.current_enum_class
            self.current_enum_class = node.name
            # Walk the body to catch internal ast.Name references
            self.generic_visit(node)
            # Restore the context when leaving the class
            self.current_enum_class = old_enum_context
        else:
            # Not an enum, just walk normally
            self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Catches standard dot-notation usage: Color.RED or status.SUCCESS
        self.used_member_names.add(node.attr)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        # Check if we are iterating directly over an identifier: for x in SomeEnumClass:
        if isinstance(node.iter, ast.Name):
            enum_name = node.iter.id
            self._mark_all_enum_members_used(enum_name)
        self.generic_visit(node)

    def _mark_all_enum_members_used(self, enum_name: str) -> None:
        # Helper to find any keys starting with "EnumName." and register them as used
        prefix = f"{enum_name}."
        for key in self.defined_members:
            if key.startswith(prefix):
                _, member_name = key.split(".")
                self.used_member_names.add(member_name)

    def visit_Name(self, node: ast.Name) -> None:
        # If we are inside an Enum class, check if this Name matches an internal member
        if self.current_enum_class and isinstance(node.ctx, ast.Load):
            internal_key = f"{self.current_enum_class}.{node.id}"
            if internal_key in self.defined_members:
                self.used_member_names.add(node.id)

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        # Catches dynamic string dictionary lookups: Color["RED"]
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            self.used_member_names.add(node.slice.value)
        self.generic_visit(node)


def test_enum_members() -> None:
    detector = UnusedEnumMemberDetector()
    src_directory = Path(__file__).parent.parent / "src"
    python_files = list(src_directory.rglob("*.py"))

    # Collect definitions and usages across the codebase
    for file_path in python_files:
        detector.current_file = str(file_path.relative_to(src_directory.parent))
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        detector.visit(tree)

    # Identify unused members
    unused: list[str] = []
    for member_key, (file, line) in detector.defined_members.items():
        enum_name, member_name = member_key.split(".")

        if member_name not in detector.used_member_names:
            unused.append(f"{member_name} in {enum_name} ({file}:{line})")

    if unused:
        error_message = "\nFound unused Enum members:\n" + "\n".join(unused)
        pytest.fail(error_message)
