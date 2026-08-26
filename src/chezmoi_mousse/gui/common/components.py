from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.containers import Container, Vertical
from textual.widgets import Label, Static

from chezmoi_mousse.str_enums import InfoKind, SectionLabel

if TYPE_CHECKING:
    from textual.app import ComposeResult

from textual.reactive import reactive

from chezmoi_mousse.str_enums import Tcss

__all__ = [
    "DiffLinesContainer",
    "FlatSectionLabel",
    "HighlightedStatic",
    "InfoVertical",
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


class ViewVertical(Vertical):
    """Container for ."""

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


class InfoVertical(Vertical):
    """A MainSectionLabel, SubSectionLabel and Static widget for a standard format to
    show information which is manually created by accepting a value for each of the
    3 widgets to display."""

    nothing_to_show_map: ClassVar[dict[InfoKind, tuple[str, ...]]] = {
        InfoKind.dest_dir_contents: (
            SectionLabel.dest_dir,
            "",
            "<- click a path with a status to see its diff",
        ),
        InfoKind.contents_view_file: (
            SectionLabel.dest_dir,
            "",
            "<- Click a file path to see its contents",
        ),
    }

    info_kind: reactive[tuple[InfoKind,] | None] = reactive(None, init=False)

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        yield MainSectionLabel()
        yield SubSectionLabel()
        yield InfoStatic()

    def on_mount(self) -> None:
        self.main_label = self.query_exactly_one(MainSectionLabel)
        self.sub_label = self.query_exactly_one(SubSectionLabel)
        self.info_static = self.query_exactly_one(SubSectionLabel)

    def _reset_widgets(self) -> None:
        self.main_label = SectionLabel.not_set
        self.sub_label = SectionLabel.not_set
        self.info_static = SectionLabel.not_set

    def watch_info_kind(self, info_kind: InfoKind | None) -> None:
        if info_kind is None:
            return
