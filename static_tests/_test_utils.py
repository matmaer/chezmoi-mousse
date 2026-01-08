import ast
from pathlib import Path

BASE_DIR = Path("src", "chezmoi_mousse")


def get_module_paths() -> list[Path]:
    py_files = [f for f in BASE_DIR.glob("**/*.py")]
    py_files = [f for f in py_files if f.name not in ("__init__.py", "__main__.py")]
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
    class_name: str, exclude_paths: list[Path] = []
) -> list[Path]:
    modules: list[Path] = []
    for module_path in get_module_paths():
        tree = ast.parse(module_path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if class_name in (alias.name for alias in node.names):
                    modules.append(module_path)
    return modules
