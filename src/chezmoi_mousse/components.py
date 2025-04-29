"""Contains classes used as re-used components by the widgets in mousse.py"""

import re
from collections.abc import Iterable
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, HorizontalGroup, VerticalGroup
from textual.content import Content
from textual.lazy import Lazy
from textual.reactive import reactive
from textual.widgets import (
    Collapsible,
    DirectoryTree,
    Label,
    RichLog,
    Static,
    Switch,
    Tree,
)

from chezmoi_mousse.chezmoi import chezmoi, dest_dir
from chezmoi_mousse.config import unwanted, status_info


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
        if path.name in unwanted["dirs"]:
            return True
    if path.is_file():
        extension = re.match(r"\.[^.]*$", path.name)
        if extension in unwanted["files"]:
            return True
    return False


class AutoWarning(Container):

    def compose(self) -> ComposeResult:
        yield Static()

    def on_mount(self) -> None:
        auto_warning = ""
        if chezmoi.autocommit_enabled and not chezmoi.autopush_enabled:
            auto_warning = '"Auto Commit" is enabled: added file(s) will also be committed.'
        elif chezmoi.autocommit_enabled and chezmoi.autopush_enabled:
            auto_warning = '"Auto Commit" and "Auto Push" are enabled: adding file(s) will also be committed and pushed the remote.'

        self.query_one(Static).update(
            Content.from_markup(f"[$text-warning italic]{auto_warning}[/]")
        )


class RichFileContent(Static):
    """RichLog widget to display the content of a file."""

    def __init__(self, file_path: Path, **kwargs) -> None:
        self.file_path = file_path
        self.rich_file_content = RichLog(
            auto_scroll=False, wrap=True, highlight=True
        )
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield self.rich_file_content

    def on_mount(self) -> None:
        if not is_reasonable_dotfile(self.file_path):
            self.rich_file_content.write(
                f'File is not a text file or too large for a reasonable "dotfile" : {self.file_path}'
            )
        else:
            with open(self.file_path, "rt", encoding="utf-8") as f:
                self.rich_file_content.write(f.read())


class ColoredFileContent(Collapsible):
    """Collapsible widget to display the content of a file."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        rich_file_content = Lazy(RichFileContent(self.file_path))
        super().__init__(rich_file_content, classes="coloredfilecontent")
        self.title = str(self.file_path.relative_to(dest_dir))


class StaticDiff(Container):

    def __init__(self, file_path: Path, apply: bool) -> None:
        self.file_path = file_path
        self.apply = apply
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static()

    def on_mount(self) -> None:

        diff_output = (
            line.replace("[", "\\[")
            for line in chezmoi.diff(str(self.file_path), self.apply)
            if line.strip()  # filter lines containing only spaces
            and line[0] in "+- "
            and not line.startswith(("+++", "---"))
        )

        colored_lines: list[Content] = []
        for line in diff_output:
            content = Content(line)
            if line.startswith("+"):
                colored_lines.append(content.stylize("$text-error"))
            elif line.startswith("-"):
                colored_lines.append(content.stylize("$text-success"))
            else:
                colored_lines.append(content.stylize("$text-muted"))

        static_diff = self.query_one(Static)
        static_diff.update(Content("\n").join(colored_lines))


class FilteredAddDirTree(DirectoryTree):

    include_unmanaged_dirs = reactive(False, always_update=True)
    filter_unwanted = reactive(True, always_update=True)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed_dirs = chezmoi.managed_dir_paths
        managed_files = chezmoi.managed_file_paths
        self.root.label = f"{dest_dir} (destDir)"

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

        def recurse_paths(parent, dir_path):
            if dir_path == dest_dir:
                parent = self.root
                self.root.label = str(dir_path)
            else:
                parent = parent.add(dir_path.parts[-1], dir_path)
            files = [
                f
                for f in chezmoi.managed_file_paths
                if f.parent == dir_path
                and (not self.show_existing_only or f.exists())
            ]
            for file in files:
                parent.add_leaf(str(file.parts[-1]), file)
            sub_dirs = [
                d
                for d in chezmoi.managed_dir_paths
                if d.parent == dir_path
                and (not self.show_existing_only or d.exists())
            ]
            for sub_dir in sub_dirs:
                recurse_paths(parent, sub_dir)

        recurse_paths(self.root, dest_dir)
        self.root.expand()


class ChezmoiStatus(VerticalGroup):

    def __init__(self, apply: bool) -> None:
        # if true, adds apply status to the list, otherwise "re-add" status
        self.apply = apply
        self.status_items: list[Collapsible] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        yield from self.status_items

    def on_mount(self) -> None:
        # status can be a space so not using str.split() or str.strip()
        status_paths = [
            (adm, Path(line[3:]))
            for line in chezmoi.status_files.list_out
            if (adm := line[1] if self.apply else line[0]) in "ADM"
        ]
        for status_code, file_path in status_paths:
            rel_path = str(file_path.relative_to(dest_dir))
            title = f"{status_info["code name"][status_code]} {rel_path}"
            self.status_items.append(
                Collapsible(StaticDiff(file_path, self.apply), title=title)
            )
        self.refresh(recompose=True)


class SlideBar(VerticalGroup):

    class FilterItem(HorizontalGroup):

        def __init__(
            self,
            switch_label: str,
            switch_tooltip: str,
            switch_id: str,
            initial_state: bool,
        ) -> None:
            self.switch_label = switch_label
            self.switch_tooltip = switch_tooltip
            self.switch_id = switch_id
            self.initial_state = initial_state
            super().__init__(classes="filter-container")

        def compose(self) -> ComposeResult:
            yield Switch(
                value=self.initial_state,
                id=self.switch_id,
                classes="filter-switch",
            )
            yield Label(self.switch_label, classes="filter-label")
            yield Label("(?)", classes="filter-tooltip").with_tooltip(
                tooltip=self.switch_tooltip
            )

    def __init__(self, filters: dict, **kwargs) -> None:
        self.filters = filters
        self.filter_items = []
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield from self.filter_items

    def on_mount(self) -> None:
        for switch_id, items in self.filters.items():
            self.filter_items.append(
                self.FilterItem(
                    switch_label=items["switch_label"],
                    switch_tooltip=items["switch_tooltip"],
                    switch_id=switch_id,
                    initial_state=items["switch_state"],
                )
            )
        self.refresh(recompose=True)
