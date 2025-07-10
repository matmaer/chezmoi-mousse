import pytest

from chezmoi_mousse.chezmoi import Chezmoi


@pytest.fixture
def chezmoi_instance() -> Chezmoi:
    return Chezmoi()


def _get_chezmoi_public_members() -> list[tuple[str, str]]:
    import inspect

    members: list[tuple[str, str]] = []
    for name, member in inspect.getmembers(Chezmoi):
        if not name.startswith("_"):
            if isinstance(member, property):
                members.append((name, "property"))
            elif inspect.isfunction(member):
                members.append((name, "method"))
    return members


@pytest.mark.parametrize(
    "member_name, member_type", _get_chezmoi_public_members()
)
def test_member_in_use(member_name: str, member_type: str):
    import ast

    from _test_utils import modules_to_test

    is_used = False
    usage_locations: list[str] = []

    # Exclude chezmoi.py from the search
    for py_file in modules_to_test(exclude_file_names=["chezmoi.py"]):
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == member_name:
                is_used = True
                usage_locations.append(f"{py_file.name}:{node.lineno}")

        if is_used:
            break  # Found usage, no need to check other files

    if not is_used:
        pytest.skip(
            f"Unused Chezmoi {member_type}: '{member_name}' is not used in the codebase.\n"
            "If this is intentional for internal use, consider renaming it with a leading underscore."
        )
