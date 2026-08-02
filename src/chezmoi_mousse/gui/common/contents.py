from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual import getters
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse.cm_command import ReadCmd
from chezmoi_mousse.functions import Commands
from chezmoi_mousse.str_enums import SectionLabel, TabLabel, Tcss

from .actionables import DirContentBtn
from .messages import LogCmdResultMsg

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import AppIds, ChezmoiGui, ManagedTreePaths

__all__ = ["ContentsView"]

OUTPUT_LIMIT = 40


class ContentsView(Container):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    class ContentStr(StrEnum):
        cannot_decode = "Path cannot be decoded as UTF-8:"
        empty_or_only_whitespace = "File is empty or contains only whitespace."
        permission_denied = "Permission denied to read file"
        read_error = "Error reading path"
        truncated = "\n--- File content truncated to"

    show_path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, ids: AppIds) -> None:
        self.app_ids = ids
        super().__init__(id=ids.container.contents)

    @property
    def paths(self) -> ManagedTreePaths:
        return (
            self.app.cmattr.paths.apply_tree_paths
            if self.app_ids.tab_label == TabLabel.apply
            else self.app.cmattr.paths.re_add_tree_paths
        )

    def _create_add_dir_container(self, dir_path: Path) -> ScrollableContainer:
        widgets: list[Static | Label] = []
        if dir_path == self.paths.dest_dir:
            widgets.append(
                Label("Destination directory", classes=Tcss.main_section_label)
            )
            widgets.append(
                Static("<- Click a path to see its contents.", classes=Tcss.added)
            )
        unmanaged_dirs: list[str] = []
        unmanaged_files: list[str] = []

        limited_dirs = False
        limited_files = False

        for root, dirs, _ in os.walk(dir_path):
            root_path = Path(root)

            for name in dirs:
                path = root_path / name
                if path not in self.paths.managed_dirs_map:
                    unmanaged_dirs.append(str(path.relative_to(self.paths.dest_dir)))
                    if len(unmanaged_dirs) >= OUTPUT_LIMIT:
                        limited_dirs = True
                        break
            if limited_dirs:
                break

        for root, _, files in os.walk(dir_path):
            root_path = Path(root)
            for name in files:
                path = root_path / name
                if path not in self.paths.managed_files_map:
                    unmanaged_files.append(str(path.relative_to(self.paths.dest_dir)))
                    if len(unmanaged_files) >= OUTPUT_LIMIT:
                        limited_files = True
                        break
            if limited_files:
                break

        unmanaged_dirs.sort()
        unmanaged_files.sort()

        if unmanaged_dirs:
            widgets.append(
                Label("Contains unmanaged directories", classes=Tcss.sub_section_label)
            )
            widgets.append(Static("\n".join(unmanaged_dirs), classes=Tcss.info))
            if limited_dirs:
                widgets.append(
                    Label(
                        f"Limited output to {OUTPUT_LIMIT} unmanaged directories",
                        classes=Tcss.limited_label,
                    )
                )
        if unmanaged_files:
            widgets.append(
                Label("Contains unmanaged files", classes=Tcss.sub_section_label)
            )
            widgets.append(Static("\n".join(unmanaged_files), classes=Tcss.info))
            if limited_files:
                widgets.append(
                    Label(
                        f"Limited output to {OUTPUT_LIMIT} unmanaged files",
                        classes=Tcss.limited_label,
                    )
                )

        if not unmanaged_dirs and not unmanaged_files:
            widgets.append(Static("No unmanaged paths in this directory."))
        return ScrollableContainer(*widgets)

    def _create_file_container(self, file_path: Path) -> ScrollableContainer:
        widgets: list[Label | Static] = []

        def _handle_exception(
            exception: PermissionError | UnicodeDecodeError | OSError,
        ) -> str:
            if isinstance(exception, PermissionError):
                return f"{ContentsView.ContentStr.permission_denied} for {file_path}"
            elif isinstance(exception, UnicodeDecodeError):
                return f"{ContentsView.ContentStr.cannot_decode} for {file_path}"
            else:
                return f"{ContentsView.ContentStr.read_error} for {file_path}"

        def _read_file(file_path: Path) -> str:
            if not file_path.exists():
                cmd_result = Commands.run_read_cmd(cmd=ReadCmd.cat, path_arg=file_path)
                self.post_message(LogCmdResultMsg(cmd_result))
                return cmd_result.std_out
            try:
                truncate_size: int = 1024 * 1024  # 1Mib
                file_size = file_path.stat().st_size
                with Path.open(file_path, encoding="utf-8") as f:
                    f_contents = f.read(truncate_size)
                if f_contents.strip() == "":
                    return ContentsView.ContentStr.empty_or_only_whitespace
                if file_size > truncate_size:
                    return (
                        f_contents + f"\n--- {ContentsView.ContentStr.truncated} "
                        f"{truncate_size / 1024} KiB ---"
                    )
                else:
                    return f_contents

            except (UnicodeDecodeError, PermissionError, OSError) as e:
                return _handle_exception(e)

        file_contents = _read_file(file_path)
        text_obj = Text(file_contents)
        ReprHighlighter().highlight(text_obj)
        widgets.append(Static(text_obj))
        return ScrollableContainer(*widgets)

    def _create_managed_dir_container(self, dir_path: Path) -> ScrollableContainer:
        widgets: list[Static | Label | DirContentBtn] = []
        widgets.append(Label(str(dir_path), classes=Tcss.sub_section_label))
        widgets.append(
            Static("<- Click a file to see its contents.", classes=Tcss.added)
        )
        if dir_path == self.paths.dest_dir:
            widgets.append(
                Label("Destination directory", classes=Tcss.main_section_label)
            )
        if not self.paths.managed_dirs_map:
            widgets = [
                Label(SectionLabel.paths_with_status, classes=Tcss.main_section_label)
            ]
            widgets.append(
                Static(
                    "No managed paths are in the chezmoi repository, "
                    "switch to the Add tab to add some paths.",
                    classes=Tcss.added,
                )
            )
        elif self.paths.no_status_paths:
            widgets.append(
                Label(SectionLabel.paths_with_status, classes=Tcss.main_section_label)
            )
            widgets.append(
                Static(
                    "No diffs are available because no paths have a status. Toggle "
                    "the 'Show unchanged paths' switch to view all managed paths.",
                    classes=Tcss.info,
                )
            )

        return ScrollableContainer(*widgets)

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        self.remove_children()
        if self.app_ids.tab_label == TabLabel.add and (
            show_path == self.paths.dest_dir or show_path.is_dir()
        ):
            container = self._create_add_dir_container(show_path)
        elif show_path in (self.paths.dest_dir, self.paths.managed_dirs_map):
            container = self._create_managed_dir_container(show_path)
        else:
            container = self._create_file_container(show_path)
        self.mount(container)
        self.current_path = show_path
