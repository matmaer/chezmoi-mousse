import pytest
from pathlib import Path
from chezmoi_mousse.chezmoi import Chezmoi


@pytest.fixture
def chezmoi_instance():
    return Chezmoi()


def test_string_to_dict_valid(chezmoi_instance):
    valid_json = '{"key": "value"}'
    result = chezmoi_instance._string_to_dict(valid_json)
    assert result == {"key": "value"}


def test_string_to_dict_invalid(chezmoi_instance):
    invalid_json = '{"key": value}'
    with pytest.raises(ValueError):
        chezmoi_instance._string_to_dict(invalid_json)


def test_unmanaged_in_d_invalid_dir(chezmoi_instance):
    with pytest.raises(ValueError):
        chezmoi_instance.unmanaged_in_d(Path("/invalid/path"))
