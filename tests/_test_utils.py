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
