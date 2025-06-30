"""Test to ensure enum values in id_typing.py are actually used in the codebase."""

import re
import sys
from enum import Enum
from pathlib import Path

# Add the source directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import chezmoi_mousse.id_typing as id_typing

from _test_utils import get_modules_to_test


def test_no_unused_enum_values():
    """Verify that all enum values defined in id_typing.py are actually used in the codebase."""
    # Extract enum classes and their members directly
    enum_classes: dict[str, set[str]] = {}
    for attr_name in dir(id_typing):
        attr = getattr(id_typing, attr_name)
        # Check if it's an Enum class (but not the base Enum classes themselves)
        if (
            isinstance(attr, type)
            and issubclass(attr, Enum)
            and attr is not Enum
            and not attr_name.startswith("_")  # Skip private attributes
        ):
            enum_classes[attr_name] = {member.name for member in attr}

    # Get all Python files except id_typing.py itself
    python_files = get_modules_to_test()

    # Track usage for each enum class
    used_values: dict[str, set[str]] = {
        enum_name: set() for enum_name in enum_classes
    }

    # Search for enum usage in Python files
    for py_file in python_files:
        content = py_file.read_text()

        # Look for enum usage patterns
        for enum_name, member_names in enum_classes.items():
            # Pattern 1: EnumName.member_name
            enum_pattern = re.compile(rf"{enum_name}\.(\w+)")
            matches = enum_pattern.findall(content)
            for match in matches:
                if match in member_names:
                    used_values[enum_name].add(match)

            # Pattern 2: Direct string usage of enum values (for StrEnum)
            for member_name in member_names:
                # Check if the member name appears as a string or identifier
                if member_name in content:
                    used_values[enum_name].add(member_name)

    # Find unused enum values
    unused_values: dict[str, set[str]] = {}
    for enum_name, all_members in enum_classes.items():
        unused = all_members - used_values[enum_name]
        if unused:
            unused_values[enum_name] = unused

    # Format error message
    if unused_values:
        error_lines = ["Found unused enum values in id_typing.py:"]
        for enum_name, unused_members in unused_values.items():
            error_lines.append(f"\n{enum_name}:")
            for member in sorted(unused_members):
                error_lines.append(f"  - {member}")
        error_lines.append(
            "\nConsider removing these unused enum values or verify they are actually needed."
        )

        assert False, "\n".join(error_lines)


def test_enum_usage_patterns():
    python_files = get_modules_to_test()
    id_typing_imports = 0
    enum_usage_count = 0

    for py_file in python_files:
        content = py_file.read_text()

        # Count imports from id_typing
        if (
            "from chezmoi_mousse.id_typing import" in content
            or "import chezmoi_mousse.id_typing" in content
        ):
            id_typing_imports += 1

        # Count enum usage by checking each enum class
        for attr_name in dir(id_typing):
            attr = getattr(id_typing, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Enum)
                and attr is not Enum
                and not attr_name.startswith("_")
            ):
                enum_usage_count += content.count(f"{attr_name}.")

    assert id_typing_imports > 0, "No imports from id_typing module found"
    assert (
        enum_usage_count > 10
    ), f"Expected significant enum usage, found only {enum_usage_count} occurrences"


if __name__ == "__main__":
    test_no_unused_enum_values()
    test_enum_usage_patterns()
    print("All enum management tests passed!")
