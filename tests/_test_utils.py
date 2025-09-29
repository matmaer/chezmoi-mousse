import ast
import inspect
from dataclasses import fields, is_dataclass
from enum import StrEnum
from pathlib import Path
from types import ModuleType


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
            elif callable(member):  # This catches all callable types
                members.append((name, "method"))
            else:
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


def get_strenum_classes(from_module: ModuleType) -> list[type[StrEnum]]:
    classes: list[type[StrEnum]] = []
    for _, enum_class in inspect.getmembers(from_module, inspect.isclass):
        if (
            issubclass(enum_class, StrEnum)
            and enum_class is not StrEnum  # exclude the StrEnum class itself
            # exclude strings used for filtering DirectoryTree
            and enum_class.__name__ not in ["UnwantedDirs", "UnwantedFiles"]
        ):
            classes.append(enum_class)
    return classes


def get_strenum_member_names(enum_class: type[StrEnum]) -> list[ast.Attribute]:
    attributes: list[ast.Attribute] = []
    class_name = enum_class.__name__
    for member_name in enum_class.__members__.keys():
        attr = ast.Attribute(
            value=ast.Name(id=class_name, ctx=ast.Load()),
            attr=member_name,
            ctx=ast.Load(),
        )
        attributes.append(attr)
    return attributes


def get_ast_call_nodes(py_file: Path) -> list[ast.Call]:
    content = py_file.read_text()
    tree = ast.parse(content, filename=str(py_file))
    call_nodes: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_nodes.append(node)
    return call_nodes


def is_valid_class_expression(node: ast.AST, cls: type) -> bool:
    """
    Recursively validate if the AST node represents a valid dot-accessed expression
    starting from the given class (e.g., cls.add, cls.add.some_var, cls.add.some_method(...)).
    """

    def check_chain(current_obj: object, node: ast.AST) -> object | None:
        if isinstance(node, ast.Name):
            # Must be exactly the class name and match the starting object
            if node.id == cls.__name__ and current_obj is cls:
                return cls
            return None
        elif isinstance(node, ast.Attribute):
            # Recurse on the value to get the object
            obj = check_chain(current_obj, node.value)
            if obj is None:
                return None
            try:
                return getattr(obj, node.attr)  # Return the attribute value
            except AttributeError:
                return None
        elif isinstance(node, ast.Call):
            # For calls, validate the func and return its object
            return check_chain(current_obj, node.func)
        else:
            # Reject other node types (e.g., literals, operators)
            return None

    result = check_chain(cls, node)
    return result is not None


def get_root_class_name(node: ast.AST) -> str | None:
    """
    Get the root class name from an AST expression (e.g., 'Id' from Id.some_attr).
    Returns None if not a valid class-based expression.
    """
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return get_root_class_name(node.value)
    elif isinstance(node, ast.Call):
        return get_root_class_name(node.func)
    return None


def get_dataclasses_from_module(module: ModuleType) -> list[type]:
    dataclass_types: list[type] = []
    for _, cls in inspect.getmembers(module, inspect.isclass):
        if is_dataclass(cls) and cls.__module__ == module.__name__:
            dataclass_types.append(cls)
    return dataclass_types


def get_dataclass_fields(dataclass_type: type) -> list[tuple[str, str]]:
    field_info: list[tuple[str, str]] = []
    for field in fields(dataclass_type):
        field_info.append((field.name, str(field.type)))
    return field_info


def find_dataclass_field_usage(
    py_file: Path, dataclass_name: str, field_name: str
) -> bool:
    content = py_file.read_text()
    tree = ast.parse(content, filename=str(py_file))

    for node in ast.walk(tree):
        # Check for direct attribute access: obj.field_name
        if isinstance(node, ast.Attribute) and node.attr == field_name:
            return True
        # Check for class-level access: ClassName.field_name
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == dataclass_name
            and node.attr == field_name
        ):
            return True
    return False
