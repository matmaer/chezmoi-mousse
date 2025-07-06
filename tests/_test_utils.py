import ast
import pytest
from pathlib import Path
import chezmoi_mousse.id_typing as id_typing


tcss_file_path: Path = Path("./src/chezmoi_mousse/gui.tcss")


def get_modules_to_test() -> list[Path]:
    src_dir = Path("./src/chezmoi_mousse")
    excluded_filename = "id_typing.py"
    return [f for f in src_dir.glob("*.py") if f.name != excluded_filename]


def str_enum_classes_excluding_tcss() -> list[str]:
    return [
        attr_name
        for attr_name in dir(id_typing)
        if attr_name.endswith("Str") and not attr_name.startswith("Tcss")
    ]


def str_enum_tcss_class() -> str:
    return "TcssStr"


def str_enum_tcss_names() -> list[str]:
    return [getattr(id_typing, str_enum_tcss_class())]


def enum_classes() -> list[str]:
    return [
        attr_name for attr_name in dir(id_typing) if attr_name.endswith("Enum")
    ]


def enum_names() -> list[str]:
    return [
        getattr(id_typing, attr_name).name
        for attr_name in enum_classes()
        # if hasattr(getattr(id_typing, attr_name), "name")
    ]


def enum_values() -> list[str]:
    return [
        getattr(id_typing, attr_name).value
        for attr_name in enum_classes()
        if hasattr(getattr(id_typing, attr_name), "value")
    ]


def get_method_calls_from_modules_to_test() -> set[str]:
    all_method_calls: set[str] = set()

    for py_file in get_modules_to_test():
        try:
            content = py_file.read_text()
            tree = ast.parse(content, filename=str(py_file))
            method_calls = {
                node.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Attribute)
                and isinstance(node.ctx, ast.Load)
            }
            all_method_calls.update(method_calls)
        except (SyntaxError, UnicodeDecodeError) as e:
            pytest.fail(f"Error parsing {py_file}: {e}")

    return all_method_calls
