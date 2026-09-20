from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Label

from chezmoi_mousse import store
from chezmoi_mousse.str_enums import LabelStr, Tcss

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult
    from textual.widget import Widget


__all__ = [
    "FlatSectionLabel",
    "LabeledView",
    "MainSectionLabel",
    "SubSectionLabel",
]


class MainSectionLabel(Label): ...


class FlatSectionLabel(Label): ...


class SubSectionLabel(Label): ...


class LabeledView(Vertical):
    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(
        self,
        view_node: Widget,
        *,
        main_label: str = LabelStr.dest_dir,
        sub_label: str = LabelStr.not_set,
        flat_label: str = LabelStr.not_set,
    ) -> None:
        self.view_node = view_node
        self.main_label = main_label
        self.sub_label = sub_label
        self.flat_label = flat_label

        super().__init__(classes=Tcss.operations_middle)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel()
        yield SubSectionLabel()
        yield FlatSectionLabel()
        yield self.view_node

    def on_mount(self) -> None:
        self.main_section_label = self.query_exactly_one(MainSectionLabel)
        self.sub_section_label = self.query_exactly_one(SubSectionLabel)
        self.flat_section_label = self.query_exactly_one(FlatSectionLabel)

    def _get_main_section_label_string(self, path: Path) -> LabelStr:
        if path == store.cfg.dest_dir:
            return LabelStr.dest_dir
        if path in store.cm_paths.managed_dirs:
            return LabelStr.managed_dir
        if path in store.cm_paths.managed_files:
            return LabelStr.managed_file
        if path in store.cm_paths.status_files:
            return LabelStr.status_file
        if path in store.cm_paths.un_man_dirs:
            return LabelStr.unmanaged_dir
        if path in store.cm_paths.un_man_files:
            return LabelStr.unmanaged_file
        return LabelStr.not_set

    def watch_path(self, path: Path) -> None:
        self.main_section_label.update(self._get_main_section_label_string(path))
        self.sub_section_label.update(str(path))
        self.path_watch_hook(path)

    def path_watch_hook(self, path: Path) -> None:
        pass
