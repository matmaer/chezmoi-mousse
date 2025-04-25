"""Contains classes used as re-used components by the widgets in mousse.py"""

import re
from collections.abc import Iterable
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container
from textual.content import Content
from textual.lazy import Lazy
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Collapsible, DirectoryTree, RichLog, Static, Tree

from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import unwanted_dirs, unwanted_files


def is_reasonable_dotfile(file_path: Path) -> bool:
    if file_path.stat().st_size < 150 * 1024:  # 150 KiB
        try:
            with open(file_path, "rb") as file:
                chunk = file.read(512)
                chars = re.sub(r"\s", "", str(chunk, encoding="utf-8"))
                return chars.isprintable()
        except UnicodeDecodeError:
            return False
    return False


def is_unwanted_path(path: Path) -> bool:
    if path.is_dir():
        if path.name in unwanted_dirs:
            return True
    if path.is_file():
        extension = re.match(r"\.[^.]*$", path.name)
        if extension in unwanted_files:
            return True
    return False


class AutoWarning(Widget):

    def __init__(self) -> None:
        self.auto_warning = ""
        if chezmoi.autocommit_enabled and not chezmoi.autopush_enabled:
            self.auto_warning = '"Auto Commit" is enabled: added file(s) will also be committed.'
        elif chezmoi.autocommit_enabled and chezmoi.autopush_enabled:
            self.auto_warning = '"Auto Commit" and "Auto Push" are enabled: adding file(s) will also be committed and pushed the remote.'
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(
            Content.from_markup(f"[$warning italic]{self.auto_warning}[/]")
        )


class RichFileContent(RichLog):
    """RichLog widget to display the content of a file."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        super().__init__(
            auto_scroll=False, wrap=True, classes="richfilecontent"
        )

    def on_mount(self) -> None:
        if not is_reasonable_dotfile(self.file_path):
            self.write(
                f'File is not a text file or too large for a reasonable "dotfile" : {self.file_path}'
            )
        else:
            with open(self.file_path, "rt", encoding="utf-8") as f:
                self.write(f.read())


class ColoredFileContent(Collapsible):
    """Collapsible widget to display the content of a file."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        rich_file_content = Lazy(RichFileContent(self.file_path))
        super().__init__(rich_file_content, classes="coloredfilecontent")
        self.title = str(self.file_path.relative_to(chezmoi.paths.dest_dir))


class StaticDiff(Container):

    def __init__(self, file_path: Path, apply: bool) -> None:
        self.file_path = file_path
        self.apply = apply
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(id="staticdiff")

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
        colored_lines = []
        for line in diff_output:
            escaped = line.replace("[", "\\[")
            if escaped.startswith("+"):
                colored_lines.append(f"[{added}]{escaped}[/{added}]")
            elif escaped.startswith("-"):
                colored_lines.append(f"[{removed}]{escaped}[/{removed}]")
            else:
                colored_lines.append(f"[{dimmed}]{escaped}[/{dimmed}]")

        text_widget = self.query_one("#staticdiff", Static)
        text_widget.update("\n".join(colored_lines))


class ColoredDiff(Collapsible):

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
        rel_path = str(file_path.relative_to(chezmoi.paths.dest_dir))
        title = f"{self.status_info["code name"][status_code]} {rel_path}"
        colored_diff = StaticDiff(file_path, apply)
        super().__init__(colored_diff, title=title)


class FilteredAddDirTree(DirectoryTree):

    include_unmanaged_dirs = reactive(False, always_update=True)
    filter_unwanted = reactive(True, always_update=True)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed_dirs = chezmoi.paths.managed_dirs
        managed_files = chezmoi.paths.managed_files
        dest_dir = chezmoi.paths.dest_dir

        # Switches: Red - Green (default)
        if not self.include_unmanaged_dirs and self.filter_unwanted:
            return (
                p
                for p in paths
                if (
                    p.is_file()
                    and (p.parent in managed_dirs or p.parent == dest_dir)
                    and not is_unwanted_path(p)
                    and p not in managed_files
                )
                or (
                    p.is_dir()
                    and not is_unwanted_path(p)
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
                if p not in managed_files and not is_unwanted_path(p)
            )
        # Switches: Green - Red , this means the following is true:
        # "self.include_unmanaged_dirs and not self.filter_unwanted"
        return (
            p
            for p in paths
            if p.is_dir() or (p.is_file() and p not in managed_files)
        )


class ManagedTree(Tree):

    def __init__(self, show_existing_only: bool = False, **kwargs) -> None:
        self.show_existing_only = show_existing_only
        super().__init__(**kwargs)

    def on_mount(self) -> None:

        dest_dir_path = chezmoi.paths.dest_dir

        def recurse_paths(parent, dir_path):
            if dir_path == dest_dir_path:
                parent = self.root
                self.root.label = str(dir_path)
            else:
                parent = parent.add(dir_path.parts[-1], dir_path)
            files = [
                f
                for f in chezmoi.paths.managed_files
                if f.parent == dir_path
                and (not self.show_existing_only or f.exists())
            ]
            for file in files:
                parent.add_leaf(str(file.parts[-1]), file)
            sub_dirs = [
                d
                for d in chezmoi.paths.managed_dirs
                if d.parent == dir_path
                and (not self.show_existing_only or d.exists())
            ]
            for sub_dir in sub_dirs:
                recurse_paths(parent, sub_dir)

        recurse_paths(self.root, dest_dir_path)
        self.root.expand()
