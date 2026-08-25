from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Container
from textual.widgets import Label, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

from chezmoi_mousse.str_enums import SectionLabel, Tcss

__all__ = [
    "DiffLinesContainer",
    "FlatSectionLabel",
    "HighlightedStatic",
    "InfoContainer",
    "InfoStatic",
    "MainSectionLabel",
    "SubSectionLabel",
]

# Label subclasses


class MainSectionLabel(Label):
    def __init__(self, section_label: SectionLabel = SectionLabel.not_set) -> None:
        super().__init__(section_label, classes=Tcss.main_section_label)


class FlatSectionLabel(Label):
    def __init__(
        self, section_label: SectionLabel | str = SectionLabel.not_set
    ) -> None:
        super().__init__(section_label, classes=Tcss.flat_section_label)


class SubSectionLabel(Label):
    def __init__(self, section_label: SectionLabel = SectionLabel.not_set) -> None:
        super().__init__(section_label, classes=Tcss.sub_section_label)


# Static subclasses


class DiffLineStatic(Static): ...


class InfoStatic(Static):
    def __init__(self, text: str = "") -> None:
        super().__init__(text, classes=Tcss.info)


class HighlightedStatic(Static): ...


# Container subclasses


class DiffLinesContainer(Container): ...


class InfoContainer(Container):
    def __init__(
        self, main_label: SectionLabel, sub_label: SectionLabel, static_text: str
    ) -> None:
        self.main_label = main_label
        self.sub_label = sub_label
        self.static_text = static_text
        super().__init__()

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(self.main_label)
        yield SubSectionLabel(self.sub_label)
        yield InfoStatic(self.static_text)
