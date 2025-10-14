from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chezmoi_mousse._chezmoi import Chezmoi
    from chezmoi_mousse.gui.app import ChezmoiGUI

__all__ = ["AppType", "PreRunData"]


class AppType:
    """Type hint for self.app attributes in widgets and screens."""

    if TYPE_CHECKING:
        app: "ChezmoiGUI"


@dataclass(slots=True)
class PreRunData:
    chezmoi_instance: "Chezmoi"
    changes_enabled: bool
    chezmoi_found: bool
    dev_mode: bool
