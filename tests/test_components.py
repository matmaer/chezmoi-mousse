from pathlib import Path

import pytest

import chezmoi_mousse.components as chezmoi_components
from chezmoi_mousse.chezmoi import Chezmoi
from chezmoi_mousse.components import (
    ColoredDiff,
    ColoredFileContent,
    FilteredAddDirTree,
    ManagedTree,
    RichDiff,
    RichFileContent,
)


@pytest.fixture
def chezmoi():
    return Chezmoi()


@pytest.fixture
def rich_file_content():
    return RichFileContent(Path.home())


def test_rich_file_content_instantiation(rich_file_content):
    assert isinstance(rich_file_content, RichFileContent)


def test_rich_diff_instantiation():
    rich_diff = RichDiff(Path.home(), apply=True)
    assert isinstance(rich_diff, RichDiff)


def test_colored_diff_instantiation():
    colored_diff = ColoredDiff(
        file_path=Path.home(), status_code="M", apply=True
    )
    assert isinstance(colored_diff, ColoredDiff)


def test_colored_file_content_instantiation():
    file_content = ColoredFileContent(Path.home())
    assert isinstance(file_content, ColoredFileContent)


def test_filtered_add_dir_tree_instantiation():
    try:
        instance = FilteredAddDirTree(Path.home())
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")


def test_managed_tree_instantiation():
    managed_tree = ManagedTree(label="test_label")
    assert isinstance(managed_tree, list)


def test_is_unwanted_path_false():
    unwanted_path = chezmoi_components.is_unwanted_path(
        path=Path("tests/test.txt")
    )
    assert unwanted_path is False


def test_is_unwanted_path_true():
    unwanted_path = chezmoi_components.is_unwanted_path(
        path=Path(f"{Path.home()}/.cache")
    )
    assert unwanted_path is True


def test_is_reasonable_dotfile_true():
    reasonable_dotfile = chezmoi_components.is_reasonable_dotfile(
        file_path=Path("tests/test.txt")
    )
    assert reasonable_dotfile is True
