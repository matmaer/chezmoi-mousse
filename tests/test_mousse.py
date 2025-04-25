from pathlib import Path

import pytest

from chezmoi_mousse.mousse import (
    AddDirTree,
    ApplyTree,
    ChezmoiAdd,
    ChezmoiStatus,
    DoctorTab,
    ReAddTree,
    SlideBar,
)


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


def test_apply_tree():
    try:
        instance = ApplyTree()
    except Exception as e:
        pytest.fail(
            f"ManagedTree instantiation with apply=True failed with exception: {e}"
        )


def test_re_add_tree():
    try:
        instance = ReAddTree()
    except Exception as e:
        pytest.fail(
            f"ManagedTree instantiation with apply=False failed with exception: {e}"
        )


def test_add_dir_tree_instantiation():
    try:
        instance = AddDirTree()
    except Exception as e:
        pytest.fail(f"AddDirTree instantiation failed with exception: {e}")


def test_chezmoi_add_instantiation():
    try:
        instance = ChezmoiAdd(path_to_add=Path("/some/path"))
    except Exception as e:
        pytest.fail(f"ChezmoiAdd instantiation failed with exception: {e}")


def test_slide_bar_instantiation():
    try:
        instance = SlideBar()
    except Exception as e:
        pytest.fail(f"SlideBar instantiation failed with exception: {e}")
