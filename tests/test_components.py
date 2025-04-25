from pathlib import Path

import pytest

import chezmoi_mousse.components as chezmoi_components
from chezmoi_mousse.chezmoi import Chezmoi
from unittest.mock import patch

from chezmoi_mousse.components import (
    AutoWarning,
    ColoredDiff,
    ColoredFileContent,
    FilteredAddDirTree,
    RichFileContent,
    StaticDiff,
)


@pytest.fixture
def chezmoi():
    return Chezmoi()


@pytest.fixture
def rich_file_content():
    return RichFileContent(Path.home())


def test_rich_file_content_instantiation(rich_file_content):
    assert isinstance(rich_file_content, RichFileContent)


def test_static_diff_instantiation():
    instance = StaticDiff(Path.home(), apply=True)
    assert isinstance(instance, StaticDiff)


def test_colored_diff_instantiation():
    instance = ColoredDiff(file_path=Path.home(), status_code="M", apply=True)
    assert isinstance(instance, ColoredDiff)


def test_colored_file_content_instantiation():
    instance = ColoredFileContent(Path.home())
    assert isinstance(instance, ColoredFileContent)


def test_filtered_add_dir_tree_instantiation():
    try:
        instance = FilteredAddDirTree(Path.home())
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")


def test_is_unwanted_path_false():
    unwanted_path = chezmoi_components.is_unwanted_path(
        path=Path("tests/text_file.txt")
    )
    assert unwanted_path is False


def test_is_unwanted_path_true():
    unwanted_path = chezmoi_components.is_unwanted_path(
        path=Path(f"{Path.home()}/.cache")
    )
    assert unwanted_path is True


def test_is_reasonable_dotfile_false():
    reasonable_dotfile = chezmoi_components.is_reasonable_dotfile(
        file_path=Path("tests/binary_file.png")
    )
    assert reasonable_dotfile is False


def test_is_reasonable_dotfile_true():
    reasonable_dotfile = chezmoi_components.is_reasonable_dotfile(
        file_path=Path("tests/text_file.txt")
    )
    assert reasonable_dotfile is True


@patch("chezmoi_mousse.components.chezmoi")
def test_auto_warning_message_autocommit_enabled(mock_chezmoi):
    mock_chezmoi.autocommit_enabled = True
    mock_chezmoi.autopush_enabled = False
    instance = AutoWarning()
    assert (
        instance.auto_warning
        == '"Auto Commit" is enabled: added file(s) will also be committed.'
    )


@patch("chezmoi_mousse.components.chezmoi")
def test_auto_warning_message_autocommit_and_autopush_enabled(mock_chezmoi):
    mock_chezmoi.autocommit_enabled = True
    mock_chezmoi.autopush_enabled = True
    instance = AutoWarning()
    assert (
        instance.auto_warning
        == '"Auto Commit" and "Auto Push" are enabled: adding file(s) will also be committed and pushed the remote.'
    )


@patch("chezmoi_mousse.components.chezmoi")
def test_auto_warning_message_neither_enabled(mock_chezmoi):
    mock_chezmoi.autocommit_enabled = False
    mock_chezmoi.autopush_enabled = False
    instance = AutoWarning()
    assert instance.auto_warning == ""
