from typing import TYPE_CHECKING

from chezmoi_mousse.gui._chezmoi import Chezmoi
from chezmoi_mousse.gui._id_classes import Id, ScreenIds, Switches, TabIds

__all__ = ["AppType", "Chezmoi", "Id", "ScreenIds", "Switches", "TabIds"]

if TYPE_CHECKING:
    from chezmoi_mousse.gui.app import ChezmoiGUI


class AppType:
    """Type hint for self.app attributes in widgets and screens."""

    if TYPE_CHECKING:
        app: "ChezmoiGUI"
