from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Vertical
from textual.widgets import Label, Static

from chezmoi_mousse.str_enums import LabelStr, Tcss

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.widget import Widget


__all__ = [
    "FlatSectionLabel",
    "HighlightedStatic",
    "LabeledView",
    "MainSectionLabel",
    "SubSectionLabel",
]


class MainSectionLabel(Label):
    def __init__(self, section_label: str) -> None:
        super().__init__(section_label, classes=Tcss.main_section_label)


class FlatSectionLabel(Label):
    def __init__(self, section_label: str = LabelStr.not_set) -> None:
        super().__init__(section_label, classes=Tcss.flat_section_label)


class SubSectionLabel(Label):
    def __init__(self, section_label: str = LabelStr.not_set) -> None:
        super().__init__(section_label, classes=Tcss.sub_section_label)


class HighlightedStatic(Static): ...


class LabeledView(Vertical):
    """A MainSectionLabel, SubSectionLabel and Static widget for a standard format to
    show information which is manually created by accepting a value for each of the
    3 widgets to display."""

    def __init__(
        self,
        container_id: str,
        main_label: str,
        view_body: Widget | None = None,
        sub_label: str | None = None,
        flat_label: str | None = None,
        classes: str | None = None,
    ) -> None:
        self.main_label = main_label
        self.sub_label = sub_label
        self.flat_label = flat_label
        self.view_body = view_body

        super().__init__(id=container_id, classes=classes)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(self.main_label)
        if self.sub_label:
            yield SubSectionLabel(self.sub_label)
        if self.flat_label:
            yield FlatSectionLabel(self.flat_label)
        if self.view_body is not None:
            yield self.view_body
        else:
            yield Static("nothing to show")
