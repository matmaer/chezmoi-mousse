from pathlib import Path
from unittest.mock import patch

import pytest

import chezmoi_mousse.components as chezmoi_components
from chezmoi_mousse.chezmoi import Chezmoi
from chezmoi_mousse.components import StaticDiff


@pytest.fixture
def chezmoi():
    return Chezmoi()


def test_static_diff_instantiation():
    instance = StaticDiff(Path.home(), apply=True)
    assert isinstance(instance, StaticDiff)


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
