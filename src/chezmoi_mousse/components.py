"""Contains classes used as re-used components by the widgets in mousse.py"""

from collections.abc import Iterable
from pathlib import Path

from rich.text import Text
from textual.lazy import Lazy
from textual.reactive import reactive
from textual.widgets import Collapsible, DirectoryTree, RichLog, Tree

from chezmoi_mousse.chezmoi import chezmoi


class RichDiff(RichLog):

    def __init__(self, file_path: Path, apply: bool) -> None:
        self.file_path = file_path
        self.apply = apply
        super().__init__(auto_scroll=False, wrap=True, max_lines=500)

    def on_mount(self) -> None:
        added = str(self.app.current_theme.success)
        removed = str(self.app.current_theme.error)
        dimmed = f"{self.app.current_theme.foreground} dim"

        # line.strip() does not return a boolean but when used in a conditional statement, the result of `line.strip()` is evaluated as a boolean.
        # An empty string (`""`) evaluates to `False`, while a non-empty string evaluates to `True`.

        diff_output = (
            line
            for line in chezmoi.diff(str(self.file_path), self.apply)
            if line.strip()
            and line[0] in "+- "
            and not line.startswith(("+++", "---"))
        )

        for line in diff_output:
            style = (
                added
                if line.startswith("+")
                else removed if line.startswith("-") else dimmed
            )
            self.write(Text(line, style=style))


class ColorDiff(Collapsible):

    # Chezmoi status command output reference:
    # https://www.chezmoi.io/reference/commands/status/
    status_info = {
        "code name": {
            "space": "No change",
            "A": "Added",
            "D": "Deleted",
            "M": "Modified",
            "R": "Modified Script",
        },
        "re add change": {
            "space": "no changes for repository",
            "A": "add to repository",
            "D": "mark as deleted in repository",
            "M": "modify in repository",
            "R": "not applicable for repository",
        },
        "apply change": {
            "space": "no changes for filesystem",
            "A": "create on filesystem",
            "D": "delete from filesystem",
            "M": "modify on filesystem",
            "R": "modify script on filesystem",
        },
    }

    def __init__(self, apply: bool, file_path: Path, status_code: str) -> None:
        # if true, adds apply status to the list, otherwise "re-add" status
        self.apply = apply
        self.file_path = file_path
        self.status = self.status_info["code name"][status_code]
        dest_dir = Path(chezmoi.dump_config.dict_out["destDir"])  # Cache value
        rel_path = str(self.file_path.relative_to(dest_dir))
        rich_diff = Lazy(RichDiff(self.file_path, self.apply))
        super().__init__(rich_diff)
        self.title = f"{self.status} {rel_path}"


class FilteredAddDirTree(DirectoryTree):

    include_unmanaged_dirs = reactive(False, always_update=True)
    filter_unwanted = reactive(True, always_update=True)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed_dirs = set(chezmoi.managed_d_paths)
        managed_files = set(chezmoi.managed_f_paths)
        dest_dir = Path(chezmoi.dump_config.dict_out["destDir"])  # Cache value

        # Switches: Red - Green (default)
        if not self.include_unmanaged_dirs and self.filter_unwanted:
            return (
                p
                for p in paths
                if (
                    p.is_file()
                    and (p.parent in managed_dirs or p.parent == dest_dir)
                    and not chezmoi.is_unwanted_path(p)
                    and p not in managed_files
                )
                or (
                    p.is_dir()
                    and not chezmoi.is_unwanted_path(p)
                    and p in managed_dirs
                )
            )
        # Switches: Red - Red
        if not self.include_unmanaged_dirs and not self.filter_unwanted:
            return (
                p
                for p in paths
                if (
                    p.is_file()
                    and (p.parent in managed_dirs or p.parent == dest_dir)
                    and p not in managed_files
                )
                or (p.is_dir() and p in managed_dirs)
            )
        # Switches: Green - Green
        if self.include_unmanaged_dirs and self.filter_unwanted:
            return (
                p
                for p in paths
                if p not in managed_files and not chezmoi.is_unwanted_path(p)
            )
        # Switches: Green - Red , this means the following is true:
        # "self.include_unmanaged_dirs and not self.filter_unwanted"
        return (
            p
            for p in paths
            if p.is_dir() or (p.is_file() and p not in managed_files)
        )


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
