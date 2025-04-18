import pytest
from chezmoi_mousse.doctor import Doctor


def test_doctor_instantiation():
    try:
        instance = Doctor()
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")
