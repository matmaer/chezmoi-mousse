from __future__ import annotations

from textual.containers import Container
from textual.widgets import Label, Static

from chezmoi_mousse.str_enums import SectionLabel, Tcss

__all__ = [
    "CatConfigStatic",
    "DiffLinesContainer",
    "FlatSectionLabel",
    "HighlightedStatic",
    "InfoStatic",
    "MainSectionLabel",
    "SubSectionLabel",
]

# Label subclasses


class MainSectionLabel(Label):
    def __init__(self, section_label: SectionLabel = SectionLabel.not_set) -> None:
        super().__init__(section_label, classes=Tcss.main_section_label)


class FlatSectionLabel(Label):
    def __init__(self, section_label: SectionLabel = SectionLabel.not_set) -> None:
        super().__init__(section_label, classes=Tcss.flat_section_label)


class SubSectionLabel(Label):
    def __init__(self, section_label: SectionLabel = SectionLabel.not_set) -> None:
        super().__init__(section_label, classes=Tcss.sub_section_label)


# Static subclasses


class CatConfigStatic(Static): ...


class DiffLineStatic(Static): ...


class InfoStatic(Static):
    def __init__(self, text: str = "") -> None:
        super().__init__(text, classes=Tcss.info)


class HighlightedStatic(Static): ...


# Container subclasses


class DiffLinesContainer(Container): ...
