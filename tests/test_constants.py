"""Test if all members from the StrEnum classes in constants.py are in use"""

from enum import StrEnum

import pytest
from _test_utils import (
    find_enum_usage_in_file,
    get_strenum_classes,
    modules_to_test,
)

import chezmoi_mousse.constants as constants


@pytest.mark.parametrize(
    "str_enum_class",
    get_strenum_classes(constants),
    ids=lambda cls: cls.__name__,
)
def test_strenum_members_in_use(str_enum_class: type[StrEnum]):
    enum_class_name = str_enum_class.__name__
    modules = modules_to_test(
        exclude_file_names=[
            "__init__.py",
            "__main__.py",
            "custom_theme.py",
            "constants.py",
        ]
    )

    members_with_unnecessary_value: list[str] = []
    error_messages: list[str] = []
    unused_members: list[str] = []

    for member in str_enum_class:
        member_name = member.name
        found = False
        unnecessary_value_usage = False

        for py_file in modules:
            usage_found, value_unnecessary = find_enum_usage_in_file(
                py_file, enum_class_name, member_name
            )
            if usage_found:
                found = True
            if value_unnecessary:
                unnecessary_value_usage = True

        if not found:
            unused_members.append(member_name)
        elif unnecessary_value_usage:
            members_with_unnecessary_value.append(member_name)

    # Report failures
    if unused_members:
        error_messages.append(
            f"Unused members in {enum_class_name}: {', '.join(unused_members)}"
        )

    if members_with_unnecessary_value:
        error_messages.append(
            f"Members with unnecessary .value attribute in {enum_class_name}: {', '.join(members_with_unnecessary_value)}"
        )

    if error_messages:
        pytest.fail("\n" + "\n".join(error_messages))
