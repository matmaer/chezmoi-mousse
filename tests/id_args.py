"""Test if no hard coded id's or tcss strings are used."""

import ast
from enum import StrEnum
from pathlib import Path
from types import ModuleType

import pytest
from _test_utils import get_module_paths, get_strenum_member_names

import chezmoi_mousse.id_typing._str_enums as str_enums
from chezmoi_mousse.id_typing import Id


def _get_strenum_classes(from_module: ModuleType) -> list[type[StrEnum]]:
    if from_module.__file__ is None:
        return []
    source = Path(from_module.__file__).read_text()
    tree = ast.parse(source)
    classes: list[type[StrEnum]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if StrEnum is in the bases (assuming direct import)
            if any(
                (isinstance(base, ast.Name) and base.id == "StrEnum")
                for base in node.bases
            ):
                try:
                    cls = getattr(from_module, node.name)
                    if issubclass(cls, StrEnum):
                        classes.append(cls)
                except AttributeError:
                    pass
    return classes


def _get_root_class_name(node: ast.AST) -> str | None:
    """
    Get the root class name from an AST expression (e.g., 'Id' from Id.some_attr).
    Returns None if not a valid class-based expression.
    """
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return _get_root_class_name(node.value)
    elif isinstance(node, ast.Call):
        return _get_root_class_name(node.func)
    return None


def _get_ast_call_nodes(py_file: Path) -> list[ast.Call]:
    content = py_file.read_text()
    tree = ast.parse(content, filename=str(py_file))
    call_nodes: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_nodes.append(node)
    return call_nodes


def _is_valid_class_expression(node: ast.AST, cls: type) -> bool:
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


to_exclude = ["custom_theme.py", "overrides.py"]
strenum_classes = _get_strenum_classes(str_enums)
strenum_members: list[ast.Attribute] = []
for cls in strenum_classes:
    members = get_strenum_member_names(cls)
    strenum_members.extend(members)


@pytest.mark.parametrize(
    "py_file",
    get_module_paths(exclude_file_names=to_exclude),
    ids=lambda py_file: py_file.name,
)
def test_args(py_file: Path):
    # the id= argument is only used in some object.call(), so get call nodes
    call_nodes: list[ast.Call] = _get_ast_call_nodes(py_file)

    invalid_ids: list[str] = []
    for node in call_nodes:
        for keyword in node.keywords:
            if keyword.arg == "id":
                # Check for hardcoded string literal values for id
                if isinstance(keyword.value, ast.Constant) and isinstance(
                    keyword.value.value, str
                ):
                    invalid_ids.append(
                        f"\nHardcoded id: line {keyword.lineno}: {keyword.value.value}"
                    )
                # Check if the value for the id is any attribute from the Id class
                root_name = _get_root_class_name(keyword.value)
                if root_name is not None:
                    if root_name == "LogsEnum":
                        pass
                    elif root_name == "Id":
                        if not _is_valid_class_expression(keyword.value, Id):
                            invalid_ids.append(
                                f"\nInvalid id expression: line {keyword.lineno}: {ast.unparse(keyword.value)} (invalid attribute chain)"
                            )
                    elif (
                        root_name in [cls.__name__ for cls in strenum_classes]
                        or root_name == "self"
                    ):
                        # valid usage of StrEnum member or an id I passed to create an instance (self)
                        pass
                    else:
                        invalid_ids.append(
                            f"\nInvalid class root: line {keyword.lineno}: {ast.unparse(keyword.value)} (does not start with Id)"
                        )
    if invalid_ids:
        pytest.fail("\n" + "\n".join(invalid_ids))
