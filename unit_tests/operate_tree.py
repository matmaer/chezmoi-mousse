from dataclasses import replace
from pathlib import Path

from chezmoi_mousse.data_types import DirData, NodeData
from chezmoi_mousse.gui.common.operate_tree import OperateTree
from chezmoi_mousse.str_enums import TreeName


def make_tree() -> OperateTree:
    tree = OperateTree(TreeName.managed_sp, "test-tree")
    root_path = Path("/destination")
    root_data = NodeData(
        dir_path=True,
        exists=True,
        managed=True,
        path=root_path,
        source_path=None,
        status=None,
        wanted=None,
        dir_data=replace(DirData.for_file(), dest_dir=True),
    )
    tree.root.data = root_data
    tree.root.expand()
    tree.node_map = {root_path: tree.root}
    for relative_path in ("first", "first/nested", "second"):
        path = root_path / relative_path
        data = replace(root_data, path=path, dir_data=DirData.for_file())
        node = tree.node_map[path.parent].add(path.name, data=data, expand=True)
        tree.node_map[path] = node
    return tree


def test_collapse_bottom_level() -> None:
    tree = make_tree()
    tree.collapse_bottom_level()

    assert tree.root.is_expanded
    assert tree.node_map[Path("/destination/first")].is_expanded
    assert tree.node_map[Path("/destination/second")].is_collapsed
    assert tree.node_map[Path("/destination/first/nested")].is_collapsed

    tree.collapse_bottom_level()
    assert tree.root.is_expanded
    assert tree.node_map[Path("/destination/first")].is_collapsed
    assert tree.node_map[Path("/destination/second")].is_collapsed
    assert tree.node_map[Path("/destination/first/nested")].is_collapsed

    tree.collapse_bottom_level()
    assert tree.root.is_expanded
    assert all(
        node.is_collapsed for node in tree.node_map.values() if node is not tree.root
    )


def test_expand_after_collapse_bottom_level() -> None:
    tree = make_tree()
    tree.collapse_bottom_level()
    tree.collapse_bottom_level()
    tree.expand_top_level()

    assert tree.root.is_expanded
    assert tree.node_map[Path("/destination/first")].is_expanded
    assert tree.node_map[Path("/destination/second")].is_expanded
    assert tree.node_map[Path("/destination/first/nested")].is_collapsed
