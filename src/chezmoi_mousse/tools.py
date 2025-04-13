import ast
import re
from pathlib import Path
import subprocess
from subprocess import TimeoutExpired


def subprocess_run(long_command):
    try:
        return subprocess.run(
            long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,
            text=True,  # returns stdout as str instead of bytes
            timeout=1,
        ).stdout.strip()
    except TimeoutExpired:
        if long_command[-1] == "doctor":
            return "'chezmoi doctor' timed out, the command depends on an internet connection."
        raise


def is_unwanted_path(path: Path) -> bool:
    unwanted_dirs = {
        "__pycache__",
        ".build",
        ".bundle",
        ".cache",
        ".dart_tool",
        ".DS_Store",
        ".git",
        ".ipynb_checkpoints",
        ".mypy_cache",
        ".parcel_cache",
        ".pytest_cache",
        ".Trash",
        ".venv",
        "bin",
        "cache",
        "Cache",
        "CMakeFiles",
        "Crash Reports",
        "DerivedData",
        "go-build",
        "node_modules",
        "Recent",
        "temp",
        "Temp",
        "tmp",
        "trash",
        "Trash",
    }
    unwanted_files = {
        ".bak",
        ".cache",
        ".egg-info",
        ".gz",
        ".lnk",
        ".lock",
        ".log",
        ".pid",
        ".rar",
        ".swp",
        ".tar",
        ".temp",
        ".tgz",
        ".tmp",
        ".zip",
    }

    if path.is_dir() and path.name in unwanted_dirs:
        return True

    regex = r"\.[^.]*$"
    if path.is_file() and bool(re.match(regex, path.name)):
        extension = re.match(regex, path.name)
        if extension in unwanted_files:
            return True

    if not path.is_dir() and not path.is_file():
        # for the time being, only support files and directories
        return True

    return False


def has_sub_dirs(path: Path) -> bool:
    for child in path.iterdir():
        if child.is_dir():
            return True
    return False


def get_file_content(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    if not path.exists():
        raise ValueError(f"File does not exist: {path}")
    with open(path, "rt", encoding="utf-8") as f:
        return f.read()


def string_to_dict(string: str) -> dict:
    try:
        return ast.literal_eval(string)
    except (SyntaxError, ValueError) as error:
        raise ValueError(
            f"Syntax error or invalid value provided: {error}"
        ) from error
