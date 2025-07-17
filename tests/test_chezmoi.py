import pytest

from chezmoi_mousse.chezmoi import Chezmoi, ManagedStatus

exclude_files = ["chezmoi.py"]


def _get_chezmoi_public_members() -> list[tuple[str, str]]:
    import inspect

    members: list[tuple[str, str]] = []
    for name, member in inspect.getmembers(Chezmoi):
        if not name.startswith("_"):
            if isinstance(member, property):
                members.append((name, "property"))
            elif inspect.isfunction(member):
                members.append((name, "method"))
            elif not callable(member):
                members.append((name, "attribute"))
    return members


def _get_managed_status_public_members() -> list[tuple[str, str]]:
    import inspect

    members: list[tuple[str, str]] = []
    for name, member in inspect.getmembers(ManagedStatus):
        if not name.startswith("_"):
            if isinstance(member, property):
                members.append((name, "property"))
            elif inspect.isfunction(member):
                members.append((name, "method"))
    return members


@pytest.mark.parametrize(
    "member_name, member_type", _get_chezmoi_public_members()
)
def test_chezmoi_member_in_use(member_name: str, member_type: str):
    import ast

    from _test_utils import modules_to_test

    is_used = False

    for py_file in modules_to_test(exclude_file_names=exclude_files):
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == member_name:
                is_used = True
                break  # Found usage
        if is_used:
            break  # No need to check other files

    if not is_used:
        pytest.fail(f"Not in use: {member_name} {member_type}")


@pytest.mark.parametrize(
    "member_name, member_type", _get_managed_status_public_members()
)
def test_managed_status_member_in_use(member_name: str, member_type: str):
    import ast

    from _test_utils import modules_to_test

    is_used = False

    # Exclude chezmoi.py from the search
    for py_file in modules_to_test(exclude_file_names=exclude_files):
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == member_name:
                is_used = True

        if is_used:
            break  # Found usage, no need to check other files

    if not is_used:
        pytest.fail(
            f"Unused Chezmoi {member_type}: '{member_name}' not in use.\n"
        )
