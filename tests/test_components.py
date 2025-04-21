import pytest
from pathlib import Path

from chezmoi_mousse.components import FilteredAddDirTree, ManagedTree


def test_filtered_add_dir_tree_instantiation():
    try:
        instance = FilteredAddDirTree(Path.home())
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")


def test_managed_tree_instantiation():
    try:
        instance = ManagedTree(label="test_label")
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")
