from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Label

from chezmoi_mousse.str_enums import Tcss

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
        main_label: str,
        view_node: Widget,
        *,
        sub_label: str | None = None,
        flat_label: str | None = None,
    ) -> None:
        self.view_node = view_node
        self.main_label = main_label
        self.sub_label = sub_label
        self.flat_label = flat_label

        super().__init__(classes=Tcss.operations_middle)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(self.main_label)
        yield SubSectionLabel()
        yield FlatSectionLabel()
        yield self.view_node

    def on_mount(self) -> None:
        self.main_section_label = self.query_exactly_one(MainSectionLabel)
        self.sub_section_label = self.query_exactly_one(SubSectionLabel)
        self.flat_section_label = self.query_exactly_one(FlatSectionLabel)

        if self.sub_label is None:
            self.sub_section_label.display = False
        if self.flat_label is None:
            self.sub_section_label.display = False

    def watch_path(self, path: Path | None) -> None:
        if path is None:
            return
        self.sub_section_label.update(str(path))
        self.path_watch_hook(path)

    def path_watch_hook(self, path: Path) -> None:
        pass
