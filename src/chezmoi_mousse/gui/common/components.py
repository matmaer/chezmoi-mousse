from __future__ import annotations

from textual.widgets import Label

__all__ = [
    "FlatSectionLabel",
    "InfoLabel",
    "MainSectionLabel",
    "NoShowLabel",
    "SubSectionLabel",
    "WarningLabel",
]


class FlatSectionLabel(Label): ...


class InfoLabel(Label): ...


class MainSectionLabel(Label): ...


class NoShowLabel(FlatSectionLabel): ...


class SubSectionLabel(Label): ...


class WarningLabel(Label): ...
