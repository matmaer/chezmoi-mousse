from __future__ import annotations

from typing import TYPE_CHECKING

from textual import work
from textual.containers import ScrollableContainer
from textual.reactive import reactive

from chezmoi_mousse import store, tchezmoi
from chezmoi_mousse.gui.common.components import (
    HighlightedStatic,
    MainSectionLabel,
    SubSectionLabel,
)
from chezmoi_mousse.str_enums import (
    BtnLabel,
    LabelStr,
    PathKind,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.data_classes import StatusPaths
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

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
    def paths(self) -> StatusPaths:
        return (
            store.apply_paths
            if self.app_ids.tab_label == BtnLabel.apply
            else store.re_add_paths
        )

    def _is_dir(self, path: Path) -> bool:
        return path == store.cfg.dest_dir or path in store.managed_dirs or path.is_dir()

    def _set_dir_contents(self, path: Path) -> None:
        # main label
        if path == store.cfg.dest_dir:
            self.main_section_label.update(LabelStr.dest_dir)
        elif path in store.managed_dirs:
            self.main_section_label.update(LabelStr.managed_dir)
        else:
            self.main_section_label.update(LabelStr.unmanaged_dir)
        # sub label
        label = str(path)
        if self.app_ids.tab_label in (BtnLabel.apply, BtnLabel.re_add):
            if not store.managed_dirs | store.managed_files:
                label = LabelStr.no_managed_paths
            elif not store.status_dirs_kind and not store.status_files_kind:
                label = LabelStr.no_status_paths
        self.sub_section_label.update(label)

    @work
    async def _create_file_container(self, path: Path) -> None:
        self.sub_section_label.update(LabelStr.not_set)
        if path in store.managed_files:
            self.main_section_label.update(LabelStr.managed_file)
        else:
            self.main_section_label.update(LabelStr.unmanaged_file)
        if store.managed_files.get(path) is PathKind.EXISTS_FALSE:
            f_content = await tchezmoi.get_highlighted_chezmoi_cat_output(
                self.app, path
            )
            self.highlighted_static.update(f_content)
            self.sub_section_label.update(LabelStr.chezmoi_cat_output)
        else:
            f_content = tchezmoi.get_highlighted_file_contents(path)
            self.highlighted_static.update(f_content)
            self.sub_section_label.update(LabelStr.read_file_output)

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        if self._is_dir(show_path):
            self._set_dir_contents(show_path)
            return
        self._create_file_container(show_path)
