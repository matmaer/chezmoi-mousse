from pathlib import Path
import chezmoi_mousse.id_typing as id_typing


tcss_file_path: Path = Path("./src/chezmoi_mousse/gui.tcss")


def get_modules_to_test() -> list[Path]:
    all_modules = list(Path("./src/chezmoi_mousse").glob("*.py"))
    excluded_filename = "id_typing.py"
    return [f for f in all_modules if f.name != excluded_filename]


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
