from pathlib import Path

tcss_str_enum_name: str = "TcssStr"
type InspectOut = list[tuple[str, object]]


def modules_to_test(exclude_file_names: list[str] = []) -> list[Path]:
    src_dir = Path("./src/chezmoi_mousse")
    return [
        f for f in src_dir.glob("*.py") if f.name not in exclude_file_names
    ]
