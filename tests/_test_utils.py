import ast
from enum import StrEnum
from pathlib import Path

import chezmoi_mousse.id_typing._str_enums


def get_module_paths(exclude_paths: list[Path] = []) -> list[Path]:
    src_dir = Path("./src/chezmoi_mousse")
    # the glob method returns an iterator of Path objects
    return [
        f
        for f in src_dir.glob("**/*.py")
        if f.name not in ["__init__.py", "__main__.py"]
        and f.relative_to(src_dir) not in exclude_paths
    ]


def get_module_ast_tree(module_path: Path) -> ast.AST:
    return ast.parse(module_path.read_text())


def get_str_enum_classes() -> list[type[StrEnum]]:
    return [
        cls
        for cls in chezmoi_mousse.id_typing._str_enums.__dict__.values()
        if isinstance(cls, type) and issubclass(cls, StrEnum)
    ]
