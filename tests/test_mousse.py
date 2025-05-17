import pytest

from chezmoi_mousse.mousse import ChezmoiStatus, DoctorTab


def test_doctor_instantiation():
    try:
        DoctorTab()
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")


def test_chezmoi_status_instantiation():
    try:
        ChezmoiStatus(apply=True)
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")
