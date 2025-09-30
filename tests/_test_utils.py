import ast
from enum import StrEnum
from pathlib import Path


def get_module_paths(exclude_file_names: list[str] = []) -> list[Path]:
    src_dir = Path("./src/chezmoi_mousse")
    default_excludes = ["__main__.py", "__init__.py"]
    all_excludes = default_excludes + exclude_file_names
    # the glob method returns an iterator of Path objects
    return [f for f in src_dir.glob("*.py") if f.name not in all_excludes]


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
