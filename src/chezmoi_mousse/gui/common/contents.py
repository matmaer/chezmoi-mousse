from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.reactive import reactive

from chezmoi_mousse.functions import Commands
from chezmoi_mousse.str_enums import (
    PathKind,
    SectionLabel,
    StaticString,
    TabLabel,
)

from .components import (
    HighlightedStatic,
    MainSectionLabel,
    SubSectionLabel,
)
from .messages import LogCmdResultMsg

if TYPE_CHECKING:
    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import ManagedTreePaths

__all__ = ["ContentsView"]


class ContentsView(ScrollableContainer):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    show_path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, ids: AppIds) -> None:
        self.app_ids = ids
        super().__init__(id=ids.container.contents)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel()
        yield SubSectionLabel()
        yield HighlightedStatic()

    def on_mount(self) -> None:
        self.highlighted_static = self.query_exactly_one(HighlightedStatic)
        self.main_section_label = self.query_exactly_one(MainSectionLabel)
        self.sub_section_label = self.query_exactly_one(SubSectionLabel)

        self.sub_section_label.update()

    @property
    def _managed_paths(self) -> ManagedTreePaths:
        return (
            self.app.cmattr.paths.apply_tree_paths
            if self.app_ids.tab_label == TabLabel.apply
            else self.app.cmattr.paths.re_add_tree_paths
        )

    def _is_dir(self, path: Path) -> bool:
        return (
            path == self.app.cmattr.dest_dir
            or path in self._managed_paths.managed_dirs
            or path.is_dir()
        )

    def _set_dir_contents(self, path: Path) -> None:
        # main label
        if path == self.app.cmattr.dest_dir:
            self.main_section_label.update(SectionLabel.dest_dir)
        elif path in self.app.cmattr.paths.managed_dirs:
            self.main_section_label.update(SectionLabel.managed_dir)
        else:
            self.main_section_label.update(SectionLabel.unmanaged_dir)
        # sub label
        label = str(path)
        if self.app_ids.tab_label in (TabLabel.apply, TabLabel.re_add):
            if self.app.cmattr.paths.no_managed_paths:
                label = SectionLabel.no_managed_paths
            elif self._managed_paths.no_status_paths:
                label = SectionLabel.no_status_paths
        self.sub_section_label.update(label)
        self.highlighted_static.update(StaticString.click_file_for_contents)

    def _create_file_container(self, path: Path) -> None:
        self.sub_section_label.update(SectionLabel.not_set)
        if path in self.app.cmattr.paths.managed_files:
            self.main_section_label.update(SectionLabel.managed_file)
        else:
            self.main_section_label.update(SectionLabel.unmanaged_file)
        if self.app.cmattr.paths.managed_files.get(path) is PathKind.EXISTS_FALSE:
            f_content, cmd_result = Commands.get_highlighted_chezmoi_cat_output(path)
            self.post_message(LogCmdResultMsg([cmd_result]))
            self.highlighted_static.update(f_content)
            self.sub_section_label.update(SectionLabel.chezmoi_cat_output)
        else:
            f_content = Commands.get_highlighted_file_contents(path)
            self.highlighted_static.update(f_content)
            self.sub_section_label.update(SectionLabel.read_file_output)

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        if self._is_dir(show_path):
            self._set_dir_contents(show_path)
            return
        self._create_file_container(show_path)
