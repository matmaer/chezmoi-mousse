from pathlib import Path


def modules_to_test(exclude_file_names: list[str] = []) -> list[Path]:
    src_dir = Path("./src/chezmoi_mousse")
    return [
        f for f in src_dir.glob("*.py") if f.name not in exclude_file_names
    ]


def get_all_classes_in_module(
    module_name: str, exclude_classes: list[str] = []
) -> list[str]:
    import importlib
    import inspect

    module = importlib.import_module(module_name)
    classes: list[str] = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Only include classes that are actually defined in the chezmoi module
        if obj.__module__ == module.__name__ and name not in exclude_classes:
            classes.append(name)
    return classes


def get_class_public_members(
    class_object: type, class_name: str
) -> list[tuple[str, str]]:
    """Get all public members of a given class."""
    import inspect

    cls = getattr(class_object, class_name)
    members: list[tuple[str, str]] = []

    for name, member in inspect.getmembers(cls):
        if not name.startswith("_"):
            if isinstance(member, property):
                members.append((name, "property"))
            elif inspect.isfunction(member):
                members.append((name, "method"))
            elif not callable(member):
                members.append((name, "attribute"))
    return members
