from __future__ import annotations

from textual.widgets import Label

__all__ = [
    "FlatSectionLabel",
    "MainSectionLabel",
    "NoShowLabel",
    "SubSectionLabel",
    "WarningLabel",
]


class FlatSectionLabel(Label): ...


class MainSectionLabel(Label): ...


class NoShowLabel(FlatSectionLabel): ...


class SubSectionLabel(Label): ...


class WarningLabel(Label): ...
