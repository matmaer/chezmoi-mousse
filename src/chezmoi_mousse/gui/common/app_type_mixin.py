from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chezmoi_mousse._textual_app import ChezmoiGUI

__all__ = ["ChezmoiAppType"]


class ChezmoiAppType:
    """Mixin to provide strict type hinting for self.app in Textual widgets/screens
    which works for all type checkers."""

    if TYPE_CHECKING:
        app: "ChezmoiGUI"
