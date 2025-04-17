import pytest
from pathlib import Path
from chezmoi_mousse.main_screen import (
    ChezmoiStatus,
    ManagedTree,
    FilteredAddDirTree,
    AddDirTree,
    ChezmoiAdd,
    SlideBar,
    MainScreen,
)


def test_chezmoi_status_instantiation():
    try:
        instance = ChezmoiStatus(apply=True)
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")


def test_managed_tree_instantiation():
    try:
        instance = ManagedTree(apply=True)
    except Exception as e:
        pytest.fail(f"ManagedTree instantiation failed with exception: {e}")


def test_filtered_add_dir_tree_instantiation():
    try:
        instance = FilteredAddDirTree(Path("/some/path"))
    except Exception as e:
        pytest.fail(
            f"FilteredAddDirTree instantiation failed with exception: {e}"
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


def test_main_screen_instantiation():
    try:
        instance = MainScreen()
    except Exception as e:
        pytest.fail(f"MainScreen instantiation failed with exception: {e}")
