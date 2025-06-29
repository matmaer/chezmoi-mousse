"""Shared utilities for test modules."""

from pathlib import Path


def get_python_files() -> list[Path]:
    """Helper function to get Python files from the source directory."""
    src_dir = Path(__file__).parent.parent / "src" / "chezmoi_mousse"
    return [f for f in src_dir.glob("*.py") if not f.name.startswith("__")]


def get_python_files_excluding(excluded_filename: str) -> list[Path]:
    """Get Python files excluding a specific filename."""
    return [f for f in get_python_files() if f.name != excluded_filename]


def get_tcss_file() -> Path:
    """Get the path to the gui.tcss file."""
    return Path(__file__).parent.parent / "src" / "chezmoi_mousse" / "gui.tcss"
