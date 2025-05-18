import pytest

from chezmoi_mousse.mousse import DoctorTab


def test_doctor_instantiation():
    try:
        DoctorTab()
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")
