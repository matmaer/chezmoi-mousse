import ast
import inspect
from dataclasses import fields, is_dataclass
from enum import StrEnum
from pathlib import Path
from types import ModuleType
from typing import Any


def get_module_paths(exclude_file_names: list[str] = []) -> list[Path]:
    src_dir = Path("./src/chezmoi_mousse")
    default_excludes = ["__main__.py", "__init__.py"]
    all_excludes = default_excludes + exclude_file_names
    return [f for f in src_dir.glob("*.py") if f.name not in all_excludes]


def get_module_classes(module: ModuleType) -> list[type] | None:
    """Get all class objects defined in a module."""
    classes: list[type] = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        # Only include classes defined in this module (not imported ones)
        if obj.__module__ == module.stem:
            classes.append(obj)
    if not classes:
        return None
    return classes


def get_class_public_members_strings(
    class_object: type,
) -> list[tuple[str, str]]:
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


def get_class_public_member_objects(
    class_object: type,
) -> dict[str, list[Any]] | None:
    """
    Get public member objects of a class, categorized into properties, methods, and attributes.
    Uses AST to parse the class source and identify defined members, then retrieves the objects.
    Includes both annotated and non-annotated attributes, excluding type objects.
    """
    tree = ast.parse(inspect.getsource(class_object))

    class_def = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_def = node
            break

    if not class_def:
        return None

    public_members: set[str] = set()

    for node in class_def.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            public_members.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith(
                    "_"
                ):
                    public_members.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            # Include annotated attributes (with or without assignment)
            if isinstance(
                node.target, ast.Name
            ) and not node.target.id.startswith("_"):
                public_members.add(node.target.id)
        # Check for properties (functions with @property decorator)
        elif (
            isinstance(node, ast.FunctionDef)
            and any(
                (isinstance(d, ast.Name) and d.id == "property")
                or (isinstance(d, ast.Attribute) and d.attr == "property")
                for d in node.decorator_list
            )
            and not node.name.startswith("_")
        ):
            public_members.add(node.name)

    # Retrieve objects and categorize
    result: dict[str, list[Any]] = {
        "property": [],
        "method": [],
        "attribute": [],
    }
    for name in public_members:
        try:
            obj = getattr(class_object, name)
            if isinstance(obj, property):
                result["property"].append(obj)
            elif callable(obj):
                result["method"].append(obj)
            else:
                # Exclude type objects from attributes
                if not isinstance(obj, type):
                    result["attribute"].append(obj)
        except AttributeError:
            pass  # Skip if not accessible

    return result


# def test_class_members_in_use(class_object: type):

#     class_members_dict: dict[str, list[Any]] | None = (
#         get_class_public_member_objects(class_object)
#     )
#     if class_members_dict is None:
#         pytest.skip(f"No members received for {class_object.__name__}")

#     unused_members: dict[str, list[str]] | None = None

#     for py_file in get_module_paths():
#         for key, value_list in class_members_dict:
#             for member in value_list:
#                 # logic to be added
#                 ...

#     if unused_members is not None:
#         for key, values in unused_members:
#             for value in values:
#                 pytest.fail(
#                     f"Class {key}\n{value} is not in use outside of the class."
#                 )


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
        if issubclass(enum_class, StrEnum):
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
