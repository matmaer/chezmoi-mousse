from textual.widgets import Label

__all__ = ["FlatSectionLabel", "MainSectionLabel", "SubSectionLabel"]


class FlatSectionLabel(Label):
    def __init__(self, label_text: str) -> None:
        super().__init__(label_text)


class MainSectionLabel(Label):
    def __init__(self, label_text: str) -> None:
        super().__init__(label_text)


class SubSectionLabel(Label):
    def __init__(self, label_text: str) -> None:
        super().__init__(label_text)
