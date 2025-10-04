import ast
from pathlib import Path


def get_module_paths(
    exclude_paths: list[Path] = [], exclude_id_typing: bool = False
) -> list[Path]:
    src_dir = Path("./src/chezmoi_mousse")
    # the glob method returns an iterator of Path objects
    py_files = [f for f in src_dir.glob("**/*.py")]
    py_files = [
        f for f in py_files if f.name not in ("__init__.py", "__main__.py")
    ]
    if exclude_id_typing:
        # remove all py files in the id_typing directory
        py_files = [f for f in py_files if "id_typing" not in f.parts]
    # exclude any additional specified paths
    py_files = [f for f in py_files if f not in exclude_paths]
    # exclude __init__.py and __main__.py files
    return py_files


def get_module_ast_tree(module_path: Path) -> ast.AST:
    return ast.parse(module_path.read_text())


def get_module_ast_class_defs(module_path: Path) -> list[ast.ClassDef]:
    module_ast_tree = get_module_ast_tree(module_path)
    class_defs: list[ast.ClassDef] = []
    for node in ast.walk(module_ast_tree):
        if isinstance(node, ast.ClassDef):
            class_defs.append(node)
    return class_defs


def get_modules_importing_class(
    class_name: str,
    exclude_paths: list[Path] = [],
    exclude_id_typing: bool = False,
) -> list[Path]:
    modules: list[Path] = []
    for module_path in get_module_paths(
        exclude_paths=exclude_paths + exclude_paths,
        exclude_id_typing=exclude_id_typing,
    ):
        tree = ast.parse(module_path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if class_name in (alias.name for alias in node.names):
                    modules.append(module_path)
    return modules
