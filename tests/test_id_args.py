"""Test if no hard coded id's or tcss strings are used."""

import ast
from pathlib import Path

import pytest
from _test_utils import (
    get_ast_call_nodes,
    get_root_class_name,
    get_strenum_classes,
    get_strenum_member_names,
    is_valid_class_expression,
    modules_to_test,
)

import chezmoi_mousse.constants as constants
from chezmoi_mousse.id_typing import Id

# exclude some files not of interest
to_exclude = ["__init__.py", "__main__.py", "custom_theme.py", "overrides.py"]
strenum_classes = get_strenum_classes(constants)
strenum_members: list[ast.Attribute] = []
for cls in strenum_classes:
    members = get_strenum_member_names(cls)
    strenum_members.extend(members)


@pytest.mark.parametrize(
    "py_file",
    modules_to_test(exclude_file_names=to_exclude),
    ids=lambda py_file: py_file.name,
)
def test_ids(py_file: Path):
    # the id= argument is only used in some object.call(), so get call nodes
    call_nodes: list[ast.Call] = get_ast_call_nodes(py_file)

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
                root_name = get_root_class_name(keyword.value)
                if root_name is not None:
                    if root_name == "Id":
                        if not is_valid_class_expression(keyword.value, Id):
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
