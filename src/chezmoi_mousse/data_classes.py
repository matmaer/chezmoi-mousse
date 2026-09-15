from __future__ import annotations

from pathlib import Path
from typing import NamedTuple, Self

ChangedPaths = NamedTuple(
    "ChangedPaths",
    [
        ("removed_dirs", list[Path]),
        ("removed_files", list[Path]),
        ("added_files", dict[Path, str]),
        ("added_dirs", dict[Path, str]),
        ("changed_dirs", dict[Path, str]),
        ("changed_files", dict[Path, str]),
        ("top_removed_dirs", list[Path]),
    ],
)

ChezmoiPathSets = NamedTuple(
    "ChezmoiPathSets",
    [
        # dirty space dirs have nested status paths, clean don't
        ("clean_space_dirs", set[Path]),
        ("dirty_space_dirs", set[Path]),
        # Managed paths, including both files and directories
        ("managed_paths", set[Path]),
        ("status_paths", set[Path]),
        ("missing_paths", set[Path]),
        # Paths in the tree which 'chezmoi add' will do something
        ("add_files", set[Path]),
        ("add_dirs", set[Path]),
        ("add_paths", set[Path]),
        # Paths in the tree which 'chezmoi apply' will do something
        ("apply_files", set[Path]),
        ("apply_dirs", set[Path]),
        ("apply_paths", set[Path]),
        # Paths in the tree which 'chezmoi re-add' will do something
        ("re_add_files", set[Path]),
        ("re_add_dirs", set[Path]),
        ("re_add_paths", set[Path]),
    ],
)


class ChezmoiPaths:
    """
    Created after each time we re-run chezmoi managed and chezmoi status for
    directories and files. This class will be initialized in store.cm_paths_legacy after
    each chezmoi WriteCmd, a manual refresh, or at app startup after the SplashScreen.
    """

    def __init__(
        self,
        *,
        managed_dirs: dict[Path, str],
        managed_files: dict[Path, str],
        changes: ChangedPaths,
    ) -> None:

        self.managed_dirs = managed_dirs
        self.managed_files = managed_files
        self.changes = changes

        self.sets: ChezmoiPathSets = self._get_path_sets()

    def _get_path_sets(
        self,
    ) -> ChezmoiPathSets:

        def check_can_add(status: str) -> bool:
            # TODO: check if this condition is correct
            return status[0] == "A" or status[1] == "A"

        def check_can_apply(status: str) -> bool:
            # TODO: handle/support 'R'
            return status[1] != " " and status[1] != "R"

        def check_can_readd(status: str) -> bool:
            return status[0] != " "

        add_files: set[Path] = set()
        apply_files: set[Path] = set()
        re_add_files: set[Path] = set()

        for path, status_pair in self.managed_files.items():
            if check_can_add(status_pair):
                add_files.add(path)
            if check_can_apply(status_pair):
                apply_files.add(path)
            if check_can_readd(status_pair):
                re_add_files.add(path)

        _status_add_dirs: set[Path] = set()
        _status_apply_dirs: set[Path] = set()
        _status_re_add_dirs: set[Path] = set()

        for path, status_pair in self.managed_dirs.items():
            if check_can_add(status_pair):
                _status_add_dirs.add(path)
            if check_can_apply(status_pair):
                _status_apply_dirs.add(path)
            if check_can_readd(status_pair):
                _status_re_add_dirs.add(path)

        # for the dirs without a status, we also need to consider their nested contents

        def has_nested_status_children(dir_path: Path, context: set[Path]) -> bool:
            return any(
                path != dir_path and path.is_relative_to(dir_path) for path in context
            )

        _space_add_dirs: set[Path] = set()
        _space_apply_dirs: set[Path] = set()
        _space_re_add_dirs: set[Path] = set()

        for path in self.managed_dirs.keys() - self.managed_files.keys():
            if has_nested_status_children(path, _status_add_dirs | add_files):
                _space_add_dirs.add(path)
            if has_nested_status_children(path, _status_apply_dirs | apply_files):
                _space_apply_dirs.add(path)
            if has_nested_status_children(path, _status_re_add_dirs | re_add_files):
                _space_re_add_dirs.add(path)

        add_dirs = _status_add_dirs | _space_add_dirs
        apply_dirs = _status_apply_dirs | _space_apply_dirs
        re_add_dirs = _status_re_add_dirs | _space_re_add_dirs

        dirty_space_dirs = _space_add_dirs | _space_apply_dirs | _space_re_add_dirs
        clean_space_dirs = (
            self.managed_dirs.keys() - self.managed_files.keys() - dirty_space_dirs
        )

        managed_paths = self.managed_dirs.keys() | self.managed_files.keys()
        status_paths = self.managed_dirs.keys() | self.managed_files.keys()

        return ChezmoiPathSets(
            # dirty space dirs have nested status paths, clean don't
            clean_space_dirs=clean_space_dirs,
            dirty_space_dirs=dirty_space_dirs,
            # Managed and status paths, including both files and directories
            managed_paths=managed_paths,
            status_paths=managed_paths - status_paths,
            missing_paths={p for p in managed_paths if not p.exists()},
            # Paths in the tree which 'chezmoi add' will do something
            add_dirs=add_dirs,
            add_files=add_files,
            add_paths=add_dirs | add_files,
            # Paths in the tree which 'chezmoi apply' will do something
            apply_dirs=apply_dirs,
            apply_files=apply_files,
            apply_paths=apply_dirs | apply_files,
            # Paths in the tree which 'chezmoi re-add' will do something
            re_add_dirs=re_add_dirs,
            re_add_files=re_add_files,
            re_add_paths=re_add_dirs | re_add_files,
        )

    @classmethod
    def empty(cls) -> Self:
        return cls(
            managed_dirs={},
            managed_files={},
            changes=ChangedPaths(
                removed_dirs=[],
                removed_files=[],
                added_files={},
                added_dirs={},
                changed_dirs={},
                changed_files={},
                top_removed_dirs=[],
            ),
        )
