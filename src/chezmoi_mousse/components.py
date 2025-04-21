"""Contains classes used as re-used components by the widgets in mousse.py"""

from collections.abc import Iterable
from pathlib import Path

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import DirectoryTree, Tree

from chezmoi_mousse.chezmoi import chezmoi


class FilteredAddDirTree(DirectoryTree):

    include_unmanaged_dirs = reactive(False, always_update=True)
    filter_unwanted = reactive(True, always_update=True)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed_dirs = set(chezmoi.managed_d_paths)
        managed_files = set(chezmoi.managed_f_paths)

        # Switches: Red - Green (default)
        if not self.include_unmanaged_dirs and self.filter_unwanted:
            return [
                p
                for p in paths
                if (
                    p.is_file()
                    and (
                        p.parent in managed_dirs
                        or p.parent
                        == Path(chezmoi.dump_config.dict_out["destDir"])
                    )
                    and not chezmoi.is_unwanted_path(p)
                    and p not in managed_files
                )
                or (
                    p.is_dir()
                    and not chezmoi.is_unwanted_path(p)
                    and p in managed_dirs
                )
            ]
        # Switches: Red - Red
        if not self.include_unmanaged_dirs and not self.filter_unwanted:
            return [
                p
                for p in paths
                if (
                    p.is_file()
                    and (
                        p.parent in managed_dirs
                        or p.parent
                        == Path(chezmoi.dump_config.dict_out["destDir"])
                    )
                    and p not in managed_files
                )
                or (p.is_dir() and p in managed_dirs)
            ]
        # Switches: Green - Green
        if self.include_unmanaged_dirs and self.filter_unwanted:
            return [
                p
                for p in paths
                if p not in managed_files and not chezmoi.is_unwanted_path(p)
            ]
        # Switches: Green - Red , this means the following is true:
        # "self.include_unmanaged_dirs and not self.filter_unwanted"
        return [
            p
            for p in paths
            if p.is_dir() or (p.is_file() and p not in managed_files)
        ]


class ManagedTree(Tree):

    def on_mount(self) -> None:

        dest_dir_path = Path(chezmoi.dump_config.dict_out["destDir"])

        def recurse_paths(parent, dir_path):
            if dir_path == dest_dir_path:
                parent = self.root
                self.root.label = str(dir_path)
            else:
                parent = parent.add(dir_path.parts[-1], dir_path)
            files = [
                f for f in chezmoi.managed_f_paths if f.parent == dir_path
            ]
            for file in files:
                parent.add_leaf(str(file.parts[-1]))
            sub_dirs = [
                d for d in chezmoi.managed_d_paths if d.parent == dir_path
            ]
            for sub_dir in sub_dirs:
                recurse_paths(parent, sub_dir)

        recurse_paths(self.root, dest_dir_path)
        self.root.expand()
