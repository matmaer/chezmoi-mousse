import ast
from pathlib import Path


def modules_to_test(exclude_file_names: list[str] = []) -> list[Path]:
    src_dir = Path("./src/chezmoi_mousse")
    return [
        f for f in src_dir.glob("*.py") if f.name not in exclude_file_names
    ]


def get_class_public_members(class_object: type) -> list[tuple[str, str]]:
    import inspect

    members: list[tuple[str, str]] = []
    for name, member in inspect.getmembers(class_object):
        if not name.startswith("_"):
            if isinstance(member, property):
                members.append((name, "property"))
            elif inspect.isfunction(member):
                members.append((name, "method"))
            elif not callable(member):
                members.append((name, "attribute"))
    return members


def find_enum_usage_in_file(
    py_file: Path, enum_class_name: str, member_name: str
) -> tuple[bool, bool]:
    """Find if enum member is used and if .value is unnecessarily used.

    Returns:
        (found_usage, has_unnecessary_value_usage)
    """
    content = py_file.read_text()
    tree = ast.parse(content, filename=str(py_file))

    found_usage = False
    unnecessary_value_usage = False

    for node in ast.walk(tree):
        # Look for Attribute nodes like EnumClass.member
        if isinstance(node, ast.Attribute):
            # Check for EnumClass.member usage
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == enum_class_name
                and node.attr == member_name
            ):
                found_usage = True

            # Check for unnecessary .value usage: EnumClass.member.value
            elif (
                isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == enum_class_name
                and node.value.attr == member_name
                and node.attr == "value"
            ):
                unnecessary_value_usage = True
                found_usage = True  # It's still usage, just bad usage

    return found_usage, unnecessary_value_usage
