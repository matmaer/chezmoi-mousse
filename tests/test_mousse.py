from pathlib import Path

import pytest

from chezmoi_mousse.mousse import ChezmoiAdd, ChezmoiStatus, DoctorTab


def test_doctor_instantiation():
    try:
        instance = DoctorTab()
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")


def test_chezmoi_status_instantiation():
    try:
        instance = ChezmoiStatus(apply=True)
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")


def test_chezmoi_add_instantiation():
    try:
        instance = ChezmoiAdd(path_to_add=Path("/some/path"))
    except Exception as e:
        pytest.fail(f"ChezmoiAdd instantiation failed with exception: {e}")
